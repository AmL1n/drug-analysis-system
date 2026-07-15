# -*- coding: utf-8 -*-
"""
对照品库服务模块。
"""

from typing import List, Optional

from app.dao.library_dao import (
    DrugAreaConstantDAO,
    DrugCategoryDAO,
    DrugDAO,
    ReferencePeakDAO,
    ReferenceSpectrumDAO,
)
from app.errors.exceptions import NotFoundException


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


def delete_drug(drug_id: int) -> None:
    """删除单个药物。"""
    drug = DrugDAO.get_by_id(drug_id)
    if drug is None:
        raise NotFoundException("药物不存在")
    DrugDAO.delete(drug)


def delete_drugs(drug_ids: List[int]) -> int:
    """批量删除药物，返回删除数量。"""
    return DrugDAO.delete_by_ids(drug_ids)

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
