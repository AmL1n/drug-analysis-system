# -*- coding: utf-8 -*-
"""
对照品库服务模块。
"""

import math
from decimal import Decimal
from typing import List, Optional

from app.dao.library_dao import (
    DrugAreaConstantDAO,
    DrugCategoryDAO,
    DrugDAO,
    ReferencePeakDAO,
    ReferenceSpectrumDAO,
)
from app.errors.exceptions import NotFoundException, ParamValidationException
from app.model import Drug, DrugCategory, ReferencePeak, db


def _serialize_decimal(value):
    return float(value) if value is not None else None


def list_categories() -> List[dict]:
    """获取所有药物类别。"""
    categories = DrugCategoryDAO.list_all()
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "code": cat.code,
            "description": cat.description,
            "wavelengths": cat.wavelengths or [],
            "referenceDrugId": cat.reference_drug_id,
            "referenceDrugName": cat.reference_drug.name if cat.reference_drug else None,
            "sortOrder": cat.sort_order,
        }
        for cat in categories
    ]


def list_drugs(
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """分页获取药物列表。"""
    pagination = DrugDAO.list_drugs(category_id, keyword, page, page_size)

    items = [
        {
            "id": drug.id,
            "categoryId": drug.category_id,
            "name": drug.name,
            "cas": drug.cas,
            "molecularFormula": drug.molecular_formula,
            "description": drug.description,
            "peakCount": drug.peak_count,
            "status": drug.status,
        }
        for drug in pagination.items
    ]

    return {
        "items": items,
        "total": pagination.total,
        "page": page,
        "page_size": page_size,
    }


def list_peaks(
    drug_id: Optional[int] = None,
    category_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """分页获取参考峰列表。"""
    pagination = ReferencePeakDAO.list_peaks(drug_id, category_id, page, page_size)

    items = [
        {
            "id": peak.id,
            "drugId": peak.drug_id,
            "drugName": peak.drug.name if peak.drug else None,
            "peakIndex": peak.peak_index,
            "retentionTime": _serialize_decimal(peak.retention_time),
            "relativeRetentionTime": _serialize_decimal(peak.relative_retention_time),
            "areaRatio": _serialize_decimal(peak.area_ratio),
            "wavelength": _serialize_decimal(peak.wavelength),
            "isMainPeak": peak.is_main_peak,
        }
        for peak in pagination.items
    ]

    return {
        "items": items,
        "total": pagination.total,
        "page": page,
        "page_size": page_size,
    }


def list_spectra(
    drug_id: Optional[int] = None,
    category_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """分页获取参考光谱列表。"""
    pagination = ReferenceSpectrumDAO.list_spectra(drug_id, category_id, page, page_size)

    items = [
        {
            "id": spectrum.id,
            "drugId": spectrum.drug_id,
            "drugName": spectrum.drug.name if spectrum.drug else None,
            "wavelength": _serialize_decimal(spectrum.wavelength),
            "absorbance": _serialize_decimal(spectrum.absorbance),
            "isMax": spectrum.is_max,
        }
        for spectrum in pagination.items
    ]

    return {
        "items": items,
        "total": pagination.total,
        "page": page,
        "page_size": page_size,
    }


def get_drug_detail(drug_id: int) -> dict:
    """获取药物详情，包括峰库、光谱库和峰面积常数。"""
    drug = DrugDAO.get_by_id(drug_id)
    if drug is None:
        raise NotFoundException("药物不存在")

    peaks = ReferencePeakDAO.get_by_drug_id(drug_id)
    spectra = ReferenceSpectrumDAO.get_by_drug_id(drug_id)
    area_constants = DrugAreaConstantDAO.get_by_drug_id(drug_id)

    return {
        "id": drug.id,
        "categoryId": drug.category_id,
        "name": drug.name,
        "cas": drug.cas,
        "molecularFormula": drug.molecular_formula,
        "description": drug.description,
        "peakCount": drug.peak_count,
        "status": drug.status,
        "lambdaMax1": _serialize_decimal(drug.lambda_max_1),
        "lambdaMax2": _serialize_decimal(drug.lambda_max_2),
        "peaks": [
            {
                "id": p.id,
                "peakIndex": p.peak_index,
                "retentionTime": _serialize_decimal(p.retention_time),
                "relativeRetentionTime": _serialize_decimal(p.relative_retention_time),
                "areaRatio": _serialize_decimal(p.area_ratio),
                "wavelength": _serialize_decimal(p.wavelength),
                "isMainPeak": p.is_main_peak,
            }
            for p in peaks
        ],
        "spectra": [
            {
                "id": s.id,
                "wavelength": _serialize_decimal(s.wavelength),
                "absorbance": _serialize_decimal(s.absorbance),
                "isMax": s.is_max,
            }
            for s in spectra
        ],
        "areaConstants": [
            {
                "id": ac.id,
                "wavelength": _serialize_decimal(ac.wavelength),
                "area": _serialize_decimal(ac.area),
                "ratioTo250": _serialize_decimal(ac.ratio_to_250),
            }
            for ac in area_constants
        ],
    }


def delete_drug(drug_id: int) -> None:
    """删除单个药物。"""
    drug = DrugDAO.get_by_id(drug_id)
    if drug is None:
        raise NotFoundException("药物不存在")
    DrugDAO.delete(drug)


def delete_drugs(drug_ids: List[int]) -> int:
    """批量删除药物，返回删除数量。"""
    return DrugDAO.delete_by_ids(drug_ids)


def list_reference_drugs(category_id: int) -> List[dict]:
    """获取指定类别下可作为参照物的药物列表（启用且存在参考峰）。"""
    category = db.session.get(DrugCategory, category_id)
    if category is None:
        raise NotFoundException("药物类别不存在")

    drugs = (
        Drug.query.filter_by(category_id=category_id, status=1)
        .join(ReferencePeak, ReferencePeak.drug_id == Drug.id)
        .order_by(Drug.name)
        .all()
    )

    return [
        {
            "id": drug.id,
            "name": drug.name,
            "retentionTime": _serialize_decimal(
                ReferencePeak.query.filter_by(drug_id=drug.id)
                .order_by(ReferencePeak.peak_index)
                .first()
                .retention_time
            ),
        }
        for drug in drugs
    ]


def get_category_reference_drug(category_id: int) -> Optional[dict]:
    """获取指定类别当前默认参照药物。"""
    category = db.session.get(DrugCategory, category_id)
    if category is None:
        raise NotFoundException("药物类别不存在")

    drug = category.reference_drug
    if drug is None:
        return None

    return {
        "id": drug.id,
        "name": drug.name,
        "retentionTime": _serialize_decimal(
            ReferencePeak.query.filter_by(drug_id=drug.id)
            .order_by(ReferencePeak.peak_index)
            .first()
            .retention_time
        ),
    }


def set_category_reference_drug(category_id: int, reference_drug_id: int) -> dict:
    """设置指定类别的默认参照药物。"""
    category = db.session.get(DrugCategory, category_id)
    if category is None:
        raise NotFoundException("药物类别不存在")

    drug = db.session.get(Drug, reference_drug_id)
    if drug is None:
        raise NotFoundException("参照药物不存在")
    if drug.category_id != category_id:
        raise ParamValidationException("参照药物不属于当前类别")
    if drug.status != 1:
        raise ParamValidationException("参照药物已被禁用")
    if not ReferencePeak.query.filter_by(drug_id=drug.id).first():
        raise ParamValidationException("参照药物缺少参考峰信息")

    category.reference_drug_id = drug.id
    db.session.commit()

    return {
        "id": category.id,
        "referenceDrugId": category.reference_drug_id,
        "referenceDrugName": drug.name,
    }


def get_drug_rrt_stats(drug_id: int) -> Optional[dict]:
    """获取药物的增量 RRT 学习统计量。"""
    drug = DrugDAO.get_by_id(drug_id)
    if drug is None:
        raise NotFoundException("药物不存在")

    return {
        "n": drug.rrt_training_count or 0,
        "mean": float(drug.rrt_mean) if drug.rrt_mean is not None else None,
        "std": float(drug.rrt_std) if drug.rrt_std is not None else None,
    }


def init_drug_rrt_stats_from_reference_peaks(drug_id: int) -> None:
    """
    从参考峰初始化药物的 RRT 学习统计量。

    取该药物第一个参考峰的相对保留时间作为初始均值；若不存在相对保留时间，
    则使用保留时间。初始标准差设为 1.0，训练计数 N=1。
    """
    drug = DrugDAO.get_by_id(drug_id)
    if drug is None:
        raise NotFoundException("药物不存在")

    peaks = ReferencePeakDAO.get_by_drug_id(drug_id)
    if not peaks:
        return

    peak = peaks[0]
    if peak.relative_retention_time is not None:
        mean = Decimal(str(peak.relative_retention_time))
    elif peak.retention_time is not None:
        mean = Decimal(str(peak.retention_time))
    else:
        return

    drug.rrt_training_count = 1
    drug.rrt_mean = mean
    drug.rrt_std = Decimal("1.0")
    db.session.commit()


def update_drug_rrt_stats(drug_id: int, rrt_value: float) -> dict:
    """
    使用新的 RRT 样本增量更新药物的高斯统计量。

    更新公式（Welford 等价形式）：
        N = N + 1
        μ_new = (N * μ_old + x) / (N + 1)
        σ²_new = (1/(N+1)) * [x² + N * (σ²_old + μ_old²)] - μ_new²
        σ_new = sqrt(σ²_new)

    :param drug_id: 药物 ID
    :param rrt_value: 新的 RRT 观测值
    :return: 更新后的统计量
    """
    drug = DrugDAO.get_by_id(drug_id)
    if drug is None:
        raise NotFoundException("药物不存在")

    x = Decimal(str(rrt_value))

    n_old = drug.rrt_training_count or 0
    mu_old = drug.rrt_mean
    std_old = drug.rrt_std

    if n_old <= 0 or mu_old is None or std_old is None:
        # 尚未初始化时，先执行单样本初始化
        init_drug_rrt_stats_from_reference_peaks(drug_id)
        n_old = drug.rrt_training_count or 0
        mu_old = drug.rrt_mean
        std_old = drug.rrt_std

    if n_old <= 0 or mu_old is None or std_old is None:
        # 没有参考峰，无法学习
        raise ParamValidationException("药物缺少参考峰，无法训练 RRT")

    n_old_dec = Decimal(n_old)
    n_new = n_old + 1

    mu_new = (n_old_dec * mu_old + x) / n_new
    variance_new = (
        (x ** 2 + n_old_dec * (std_old ** 2 + mu_old ** 2)) / n_new
    ) - mu_new ** 2

    # 避免浮点/Decimal 精度导致的极小负数
    variance_new = max(variance_new, Decimal("0"))
    std_new = Decimal(str(math.sqrt(float(variance_new))))

    drug.rrt_training_count = n_new
    drug.rrt_mean = mu_new
    drug.rrt_std = std_new
    db.session.commit()

    return {
        "n": int(n_new),
        "mean": float(mu_new),
        "std": float(std_new),
    }
