# -*- coding: utf-8 -*-
"""
检测相关 API。
"""

from flask import Blueprint, request
from flask_jwt_extended import get_current_user, jwt_required

from app.dao.detection_dao import DetectionResultDAO
from app.dao.library_dao import DrugDAO, ReferencePeakDAO
from app.errors.exceptions import NotFoundException, ParamValidationException
from app.model import User
from app.service.detection_service import (
    create_batch_task,
    detect_single_sample,
    get_task_progress,
)
from app.service.log_service import log_operation
from app.utils.response import success

detection_bp = Blueprint("detection", __name__)


@detection_bp.route("/detect", methods=["POST"])
@jwt_required()
def detect_view():
    """
    单样本检测。

    请求体：{
        "sampleId": 1,
        "modelType": "fusion",
        "topN": 10,
        "confidenceThreshold": 0.7
    }
    """
    data = request.get_json(silent=True) or {}
    sample_id = data.get("sampleId")
    if not sample_id:
        raise ParamValidationException("sampleId 不能为空")

    model_type = data.get("modelType", "fusion")
    top_n = data.get("topN", 10)
    threshold = data.get("confidenceThreshold", 0.7)
    rrt_tolerance = data.get("rrtTolerance", 0.02)
    uv_distance_threshold = data.get("uvDistanceThreshold", 0.15)
    area_ratio_method = data.get("areaRatioMethod", "relative_error")

    if not isinstance(top_n, int) or top_n < 1:
        raise ParamValidationException("topN 必须是大于等于 1 的整数")
    for name, value in (
        ("confidenceThreshold", threshold),
        ("rrtTolerance", rrt_tolerance),
        ("uvDistanceThreshold", uv_distance_threshold),
    ):
        if not isinstance(value, (int, float)) or value < 0 or value > 1:
            raise ParamValidationException(f"{name} 必须在 [0, 1] 范围内")
    if area_ratio_method not in ("relative_error", "cosine", "correlation"):
        raise ParamValidationException("areaRatioMethod 必须是 relative_error / cosine / correlation 之一")

    report = detect_single_sample(
        sample_id=sample_id,
        model_type=model_type,
        top_n=top_n,
        confidence_threshold=threshold,
        rrt_tolerance=rrt_tolerance,
        uv_distance_threshold=uv_distance_threshold,
        area_ratio_method=area_ratio_method,
    )

    log_operation(
        action="执行单样本检测",
        module="detection",
        target_type="sample",
        target_id=sample_id,
        detail={
            "modelType": model_type,
            "topN": top_n,
            "confidenceThreshold": threshold,
        },
    )

    return success(data=report)


@detection_bp.route("/detect/batch", methods=["POST"])
@jwt_required()
def detect_batch_view():
    """
    批量检测任务创建。

    请求体：{
        "sampleIds": [1, 2, 3],
        "name": "批量任务名称"
    }
    """
    data = request.get_json(silent=True) or {}
    sample_ids = data.get("sampleIds", [])
    name = data.get("name")

    if not sample_ids or not isinstance(sample_ids, list):
        raise ParamValidationException("sampleIds 必须是数组且不为空")

    user = get_current_user()
    operator_id = user.id if isinstance(user, User) else None

    task = create_batch_task(sample_ids, operator_id, name)

    log_operation(
        action="创建批量检测任务",
        module="detection",
        target_type="task",
        target_id=task.id,
        detail={
            "taskNo": task.task_no,
            "name": task.name,
            "sampleIds": sample_ids,
        },
    )

    return success(
        data={
            "id": task.id,
            "taskNo": task.task_no,
            "name": task.name,
            "status": task.status,
            "totalSamples": task.total_samples,
        }
    )


@detection_bp.route("/detect/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task_view(task_id: int):
    """获取任务进度。"""
    progress = get_task_progress(task_id)
    if progress is None:
        raise NotFoundException("任务不存在")

    return success(data=progress)


@detection_bp.route("/detect/results/<int:sample_id>", methods=["GET"])
@jwt_required()
def get_detection_results_view(sample_id: int):
    """获取样本的检测结果明细，含参考峰叠加数据。"""
    results = DetectionResultDAO.get_by_sample_id(sample_id)

    items = []
    for r in results:
        drug = DrugDAO.get_by_id(r.drug_id)
        ref_peaks = ReferencePeakDAO.get_by_drug_id(r.drug_id) if drug else []
        items.append(
            {
                "drugId": r.drug_id,
                "drugName": drug.name if drug else None,
                "totalScore": float(r.total_score) if r.total_score else 0.0,
                "confidence": float(r.confidence) if r.confidence else 0.0,
                "isDetected": r.is_detected,
                "matchedPeakCount": r.matched_peak_count,
                "totalPeakCount": r.total_peak_count,
                "algorithmDetails": r.algorithm_details or {},
                "referencePeaks": [
                    {
                        "peakIndex": p.peak_index,
                        "retentionTime": float(p.retention_time),
                        "relativeRetentionTime": (
                            float(p.relative_retention_time)
                            if p.relative_retention_time is not None
                            else None
                        ),
                        "areaRatio": float(p.area_ratio) if p.area_ratio is not None else None,
                        "wavelength": float(p.wavelength) if p.wavelength is not None else None,
                        "height": float(p.height) if p.height is not None else None,
                        "width": float(p.width) if p.width is not None else None,
                        "isMainPeak": bool(p.is_main_peak),
                    }
                    for p in ref_peaks
                ],
                "createdAt": r.created_at.isoformat(),
            }
        )

    return success(data=items)
