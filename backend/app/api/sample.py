# -*- coding: utf-8 -*-
"""
样本相关 API。
"""

from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import get_current_user, jwt_required

from app.errors.exceptions import NotFoundException, ParamValidationException
from app.model import Sample, User
from app.service.file_service import parse_file_to_chromatogram
from app.service.log_service import log_operation
from app.service.sample_service import create_sample, get_sample_detail, list_samples
from app.utils.pagination import get_pagination_params
from app.utils.response import page, success

sample_bp = Blueprint("sample", __name__)


@sample_bp.route("/samples", methods=["POST"])
@jwt_required()
def create_sample_view():
    """
    创建样本。

    请求体：{
        "sampleName": "样品名称",
        "fileId": 1,
        "instrumentBrand": "Agilent",
        "detectTime": "2024-01-01 10:00:00"
    }
    """
    data = request.get_json(silent=True) or {}
    sample_name = data.get("sampleName")
    file_id = data.get("fileId")
    instrument_brand = data.get("instrumentBrand")
    detect_time_str = data.get("detectTime")

    if not file_id:
        raise ParamValidationException("fileId 不能为空")

    detect_time = None
    if detect_time_str:
        try:
            detect_time = datetime.strptime(detect_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ParamValidationException("detectTime 格式错误，应为 YYYY-MM-DD HH:MM:SS")

    user = get_current_user()
    operator_id = user.id if isinstance(user, User) else None

    sample = create_sample(
        sample_name=sample_name,
        file_record_id=file_id,
        operator_id=operator_id,
        instrument_brand=instrument_brand,
        detect_time=detect_time,
    )

    log_operation(
        action="创建样本",
        module="sample",
        target_type="sample",
        target_id=sample.id,
        detail={
            "sampleNo": sample.sample_no,
            "sampleName": sample.sample_name,
            "instrumentBrand": instrument_brand,
        },
    )

    return success(
        data={
            "id": sample.id,
            "sampleNo": sample.sample_no,
            "sampleName": sample.sample_name,
            "status": sample.status,
            "createdAt": sample.created_at.isoformat(),
        }
    )


@sample_bp.route("/samples", methods=["GET"])
@jwt_required()
def list_samples_view():
    """分页查询样本列表。"""
    page_no, page_size = get_pagination_params()
    status = request.args.get("status")

    user = get_current_user()
    operator_id = user.id if isinstance(user, User) else None

    pagination = list_samples(operator_id, status, page_no, page_size)

    items = [
        {
            "id": s.id,
            "sampleNo": s.sample_no,
            "sampleName": s.sample_name,
            "status": s.status,
            "instrumentBrand": s.instrument_brand,
            "detectTime": s.detect_time.isoformat() if s.detect_time else None,
            "createdAt": s.created_at.isoformat(),
        }
        for s in pagination.items
    ]

    return page(items, pagination.total, page_no, page_size)


@sample_bp.route("/samples/<int:sample_id>", methods=["GET"])
@jwt_required()
def get_sample_view(sample_id: int):
    """获取样本详情。"""
    sample = get_sample_detail(sample_id)
    peaks = [
        {
            "id": p.id,
            "peakIndex": p.peak_index,
            "retentionTime": float(p.retention_time),
            "area": float(p.area) if p.area else None,
            "height": float(p.height) if p.height else None,
            "areaRatio": float(p.area_ratio) if p.area_ratio is not None else None,
            "relativeRetentionTime": (
                float(p.relative_retention_time)
                if p.relative_retention_time is not None
                else None
            ),
        }
        for p in sample.peaks
    ]

    return success(
        data={
            "id": sample.id,
            "sampleNo": sample.sample_no,
            "sampleName": sample.sample_name,
            "status": sample.status,
            "instrumentBrand": sample.instrument_brand,
            "detectTime": sample.detect_time.isoformat() if sample.detect_time else None,
            "peaks": peaks,
            "createdAt": sample.created_at.isoformat(),
        }
    )


@sample_bp.route("/samples/<int:sample_id>/chromatogram", methods=["GET"])
@jwt_required()
def get_sample_chromatogram_view(sample_id: int):
    """
    获取样本原始色谱图数据，用于前端绘制峰图。

    返回：{
        "time": [],
        "intensity": [],
        "peaks": []
    }
    """
    sample = Sample.query.get(sample_id)
    if sample is None:
        raise NotFoundException("样本不存在")

    if sample.file_id is None:
        raise NotFoundException("样本未关联原始文件")

    from app.dao.file_dao import UploadedFileDAO

    file_record = UploadedFileDAO.get_by_id(sample.file_id)
    if file_record is None:
        raise NotFoundException("原始文件不存在")

    chromatogram = parse_file_to_chromatogram(file_record)

    peaks = [
        {
            "peakIndex": p.peak_index,
            "retentionTime": float(p.retention_time),
            "area": float(p.area) if p.area else None,
            "height": float(p.height) if p.height else None,
        }
        for p in sample.peaks
    ]

    return success(
        data={
            "time": chromatogram.retention_time.tolist(),
            "intensity": chromatogram.intensity.tolist(),
            "wavelength": chromatogram.wavelength,
            "peaks": peaks,
        }
    )
