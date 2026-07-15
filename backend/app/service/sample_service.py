# -*- coding: utf-8 -*-
"""
样本服务模块。
"""

from datetime import datetime
from typing import List, Optional

import numpy as np

from app.algorithm.peak_detect import calculate_area_ratios, calculate_relative_retention_times, detect_peaks
from app.algorithm.preprocess import preprocess_chromatogram
from app.algorithm.types import Chromatogram, Peak
from app.model import SamplePeak
from app.dao.sample_dao import SampleDAO
from app.errors.exceptions import NotFoundException, ParamValidationException
from app.model import Sample
from app.service.file_service import parse_file_to_chromatogram
from app.utils.security import generate_sample_no


def create_sample(
    sample_name: Optional[str],
    file_record_id: int,
    operator_id: int,
    instrument_brand: Optional[str] = None,
    detect_time: Optional[datetime] = None,
) -> Sample:
    """
    创建样本并执行峰识别。

    :param sample_name: 样品名称
    :param file_record_id: 上传文件记录ID
    :param operator_id: 操作员ID
    :param instrument_brand: 仪器品牌
    :param detect_time: 检测时间
    :return: 样本对象
    """
    from app.dao.file_dao import UploadedFileDAO

    file_record = UploadedFileDAO.get_by_id(file_record_id)
    if file_record is None:
        raise NotFoundException("上传文件记录不存在")

    sample_no = generate_sample_no()
    while SampleDAO.get_by_sample_no(sample_no):
        sample_no = generate_sample_no()

    sample = SampleDAO.create(
        sample_no=sample_no,
        sample_name=sample_name or sample_no,
        operator_id=operator_id,
        file_id=file_record_id,
        instrument_brand=instrument_brand,
        detect_time=detect_time,
    )

    # 解析并识别峰
    chromatogram = parse_file_to_chromatogram(file_record)
    peaks = _detect_sample_peaks(chromatogram)

    # 保存峰到数据库
    sample_peaks = [_peak_to_sample_peak(peak) for peak in peaks]
    SampleDAO.add_peaks(sample.id, sample_peaks)

    # 持久化原始色谱图，避免无持久盘环境（如 Render free tier）文件丢失后无法绘图
    SampleDAO.set_chromatogram(
        sample.id,
        time_list=chromatogram.retention_time.tolist()
        if hasattr(chromatogram.retention_time, "tolist")
        else list(chromatogram.retention_time),
        intensity_list=chromatogram.intensity.tolist()
        if hasattr(chromatogram.intensity, "tolist")
        else list(chromatogram.intensity),
        wavelength=chromatogram.wavelength,
    )

    # 更新样本状态为待检测
    SampleDAO.update_status(sample, "pending")

    return sample


def _detect_sample_peaks(chromatogram: Chromatogram) -> List[Peak]:
    """对色谱图进行预处理和峰检测。"""
    processed = preprocess_chromatogram(
        chromatogram.intensity,
        baseline_method="polynomial",
        smooth_method="savgol",
        normalize="none",
    )
    cg = Chromatogram(
        retention_time=chromatogram.retention_time,
        intensity=processed,
        wavelength=chromatogram.wavelength,
        metadata=chromatogram.metadata,
    )

    peaks = detect_peaks(cg, min_height=None, min_distance=5)
    peaks = calculate_area_ratios(peaks)

    # 以第一个峰为参考计算相对保留时间
    if peaks:
        reference_rt = peaks[0].retention_time
        peaks = calculate_relative_retention_times(peaks, reference_rt)

    return peaks


def _peak_to_sample_peak(peak: Peak) -> SamplePeak:
    """将算法 Peak 对象转为数据库 SamplePeak 对象。"""
    return SamplePeak(
        peak_index=peak.index,
        retention_time=peak.retention_time,
        area=peak.area,
        height=peak.height,
        width=peak.width,
        wavelength=peak.wavelength,
        relative_retention_time=peak.relative_retention_time,
        area_ratio=peak.area_ratio,
    )


def get_sample_detail(sample_id: int) -> Optional[Sample]:
    """获取样本详情。"""
    sample = SampleDAO.get_by_id(sample_id)
    if sample is None:
        raise NotFoundException("样本不存在")
    return sample


def list_samples(
    operator_id: Optional[int], status: Optional[str], page: int, page_size: int
):
    """分页查询样本列表。"""
    return SampleDAO.list_samples(operator_id, status, page, page_size)
