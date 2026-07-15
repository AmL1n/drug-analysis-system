# -*- coding: utf-8 -*-
"""
样本 DAO。
"""

from datetime import datetime
from typing import List, Optional

from app.model import Sample, SampleChromatogram, SamplePeak, SampleSpectrum, db
import json


class SampleDAO:
    """样本数据访问对象。"""

    @staticmethod
    def get_by_id(sample_id: int) -> Optional[Sample]:
        return db.session.get(Sample, sample_id)

    @staticmethod
    def get_by_sample_no(sample_no: str) -> Optional[Sample]:
        return Sample.query.filter_by(sample_no=sample_no).first()

    @staticmethod
    def create(
        sample_no: str,
        sample_name: Optional[str],
        operator_id: Optional[int],
        file_id: Optional[int],
        instrument_brand: Optional[str],
        detect_time: Optional[datetime],
        remark: Optional[str] = None,
    ) -> Sample:
        sample = Sample(
            sample_no=sample_no,
            sample_name=sample_name,
            operator_id=operator_id,
            file_id=file_id,
            instrument_brand=instrument_brand,
            detect_time=detect_time,
            remark=remark,
        )
        db.session.add(sample)
        db.session.commit()
        return sample

    @staticmethod
    def update_status(sample: Sample, status: str) -> None:
        sample.status = status
        db.session.commit()

    @staticmethod
    def list_samples(
        operator_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        query = Sample.query
        if operator_id is not None:
            query = query.filter_by(operator_id=operator_id)
        if status is not None:
            query = query.filter_by(status=status)
        return query.order_by(Sample.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )

    @staticmethod
    def add_peaks(sample_id: int, peaks: List[SamplePeak]) -> None:
        for peak in peaks:
            peak.sample_id = sample_id
            db.session.add(peak)
        db.session.commit()

    @staticmethod
    def add_spectra(sample_id: int, spectra: List[SampleSpectrum]) -> None:
        for sp in spectra:
            sp.sample_id = sample_id
            db.session.add(sp)
        db.session.commit()

    @staticmethod
    def set_chromatogram(
        sample_id: int,
        time_list: list,
        intensity_list: list,
        wavelength: Optional[float] = None,
    ) -> SampleChromatogram:
        existing = SampleChromatogram.query.filter_by(sample_id=sample_id).first()
        if existing:
            existing.time_json = json.dumps(time_list)
            existing.intensity_json = json.dumps(intensity_list)
            existing.wavelength = wavelength
        else:
            existing = SampleChromatogram(
                sample_id=sample_id,
                time_json=json.dumps(time_list),
                intensity_json=json.dumps(intensity_list),
                wavelength=wavelength,
            )
            db.session.add(existing)
        db.session.commit()
        return existing

    @staticmethod
    def get_chromatogram(sample_id: int) -> Optional[SampleChromatogram]:
        return SampleChromatogram.query.filter_by(sample_id=sample_id).first()


class SamplePeakDAO:
    """样本峰 DAO。"""

    @staticmethod
    def get_by_sample_id(sample_id: int) -> List[SamplePeak]:
        return SamplePeak.query.filter_by(sample_id=sample_id).order_by(
            SamplePeak.retention_time
        ).all()
