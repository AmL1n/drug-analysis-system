# -*- coding: utf-8 -*-
"""
对照品库 DAO。
"""

from typing import List, Optional

from app.model import (
    Drug,
    DrugAreaConstant,
    DrugCategory,
    ReferencePeak,
    ReferenceSpectrum,
    db,
)


class DrugCategoryDAO:
    """药物类别 DAO。"""

    @staticmethod
    def list_all() -> List[DrugCategory]:
        return DrugCategory.query.order_by(DrugCategory.sort_order).all()


class DrugDAO:
    """药物 DAO。"""

    @staticmethod
    def get_by_id(drug_id: int) -> Optional[Drug]:
        return db.session.get(Drug, drug_id)

    @staticmethod
    def list_drugs(
        category_id: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        query = Drug.query
        if category_id is not None:
            query = query.filter_by(category_id=category_id)
        if keyword:
            query = query.filter(Drug.name.ilike(f"%{keyword}%"))
        return query.order_by(Drug.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )

    @staticmethod
    def list_all_active() -> List[Drug]:
        return Drug.query.filter_by(status=1).order_by(Drug.name).all()

    @staticmethod
    def delete(drug: Drug) -> None:
        """删除药物及其关联的峰、光谱、峰面积常数。"""
        # 级联删除关联数据
        ReferencePeak.query.filter_by(drug_id=drug.id).delete()
        ReferenceSpectrum.query.filter_by(drug_id=drug.id).delete()
        DrugAreaConstant.query.filter_by(drug_id=drug.id).delete()
        db.session.delete(drug)
        db.session.commit()

    @staticmethod
    def delete_by_ids(drug_ids: List[int]) -> int:
        """批量删除药物及其关联数据，返回删除数量。"""
        if not drug_ids:
            return 0
        # 先删除关联数据
        ReferencePeak.query.filter(ReferencePeak.drug_id.in_(drug_ids)).delete(
            synchronize_session=False
        )
        ReferenceSpectrum.query.filter(ReferenceSpectrum.drug_id.in_(drug_ids)).delete(
            synchronize_session=False
        )
        DrugAreaConstant.query.filter(DrugAreaConstant.drug_id.in_(drug_ids)).delete(
            synchronize_session=False
        )
        # 再删除药物
        count = Drug.query.filter(Drug.id.in_(drug_ids)).delete(synchronize_session=False)
        db.session.commit()
        return count


class ReferencePeakDAO:
    """峰库 DAO。"""

    @staticmethod
    def get_by_drug_id(drug_id: int) -> List[ReferencePeak]:
        return ReferencePeak.query.filter_by(drug_id=drug_id).order_by(
            ReferencePeak.retention_time
        ).all()

    @staticmethod
    def list_peaks(
        drug_id: Optional[int] = None,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        query = ReferencePeak.query.join(Drug, ReferencePeak.drug_id == Drug.id)
        if drug_id is not None:
            query = query.filter(ReferencePeak.drug_id == drug_id)
        if category_id is not None:
            query = query.filter(Drug.category_id == category_id)
        return query.order_by(ReferencePeak.drug_id, ReferencePeak.peak_index).paginate(
            page=page, per_page=page_size, error_out=False
        )


class ReferenceSpectrumDAO:
    """光谱库 DAO。"""

    @staticmethod
    def get_by_drug_id(drug_id: int) -> List[ReferenceSpectrum]:
        return ReferenceSpectrum.query.filter_by(drug_id=drug_id).order_by(
            ReferenceSpectrum.wavelength
        ).all()

    @staticmethod
    def list_spectra(
        drug_id: Optional[int] = None,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        query = ReferenceSpectrum.query.join(Drug, ReferenceSpectrum.drug_id == Drug.id)
        if drug_id is not None:
            query = query.filter(ReferenceSpectrum.drug_id == drug_id)
        if category_id is not None:
            query = query.filter(Drug.category_id == category_id)
        return query.order_by(ReferenceSpectrum.drug_id, ReferenceSpectrum.wavelength).paginate(
            page=page, per_page=page_size, error_out=False
        )


class DrugAreaConstantDAO:
    """峰面积常数 DAO。"""

    @staticmethod
    def get_by_drug_id(drug_id: int) -> List[DrugAreaConstant]:
        return DrugAreaConstant.query.filter_by(drug_id=drug_id).order_by(
            DrugAreaConstant.wavelength
        ).all()
