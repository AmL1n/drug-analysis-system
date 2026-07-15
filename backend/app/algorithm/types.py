# -*- coding: utf-8 -*-
"""
算法数据类型定义模块。

使用 dataclass 定义峰、色谱图、光谱、匹配结果等纯数据对象，
供算法模块内部使用，不依赖任何 Web 框架或数据库框架。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


@dataclass
class Chromatogram:
    """
    色谱图数据对象。

    Attributes:
        retention_time: 保留时间数组，单位 min
        intensity: 信号强度数组（如吸光度）
        wavelength: 检测波长，单位 nm，可选
        metadata: 附加元数据
    """

    retention_time: np.ndarray
    intensity: np.ndarray
    wavelength: Optional[float] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """校验数组长度一致。"""
        if self.retention_time.shape != self.intensity.shape:
            raise ValueError("retention_time 与 intensity 长度必须一致")
        if self.retention_time.ndim != 1:
            raise ValueError("retention_time 必须为一维数组")


@dataclass
class Spectrum:
    """
    光谱数据对象（UV 光谱）。

    Attributes:
        wavelength: 波长数组，单位 nm
        absorbance: 吸光度数组
        metadata: 附加元数据
    """

    wavelength: np.ndarray
    absorbance: np.ndarray
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """校验数组长度一致。"""
        if self.wavelength.shape != self.absorbance.shape:
            raise ValueError("wavelength 与 absorbance 长度必须一致")
        if self.wavelength.ndim != 1:
            raise ValueError("wavelength 必须为一维数组")


@dataclass
class Peak:
    """
    峰数据对象。

    Attributes:
        index: 峰序号（从 1 开始）
        retention_time: 保留时间，单位 min
        area: 峰面积
        height: 峰高
        width: 半峰宽
        start_index: 峰起点在原始数组中的索引
        end_index: 峰终点在原始数组中的索引
        wavelength: 检测波长
        metadata: 附加元数据
    """

    index: int
    retention_time: float
    area: float = 0.0
    height: float = 0.0
    width: float = 0.0
    start_index: int = 0
    end_index: int = 0
    wavelength: Optional[float] = None
    relative_retention_time: Optional[float] = None
    area_ratio: Optional[float] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class MatchedPeak:
    """
    峰匹配结果对象。

    Attributes:
        sample_peak: 样本峰
        reference_peak: 对照品峰，可能为空
        rrt_score: 相对保留时间评分
        area_ratio_score: 峰面积比评分
        uv_score: UV 光谱评分
        fusion_score: 融合评分
        delta_rt: 保留时间偏差
        is_matched: 是否判定为匹配
    """

    sample_peak: Peak
    reference_peak: Optional[Peak] = None
    rrt_score: float = 0.0
    area_ratio_score: float = 0.0
    uv_score: float = 0.0
    fusion_score: float = 0.0
    delta_rt: float = 0.0
    delta_area_ratio: float = 0.0
    is_matched: bool = False


@dataclass
class DrugMatchResult:
    """
    药物级匹配结果对象。

    Attributes:
        drug_id: 药物ID（字符串或整数，由调用方决定）
        drug_name: 药物名称
        total_score: 综合评分 0-1
        confidence: 置信度 0-1
        matched_peak_count: 匹配峰数量
        total_peak_count: 药物总峰数
        is_detected: 是否判定为检出
        peak_matches: 峰级匹配明细
        algorithm_details: 算法详细结果
    """

    drug_id: str
    drug_name: str
    total_score: float = 0.0
    confidence: float = 0.0
    matched_peak_count: int = 0
    total_peak_count: int = 0
    is_detected: bool = False
    peak_matches: List[MatchedPeak] = field(default_factory=list)
    algorithm_details: Dict = field(default_factory=dict)


@dataclass
class PeakList:
    """
    标准导入文件解析出的峰列表。

    用于“相对保留时间”或“峰面积”导入文件，
    不包含完整色谱图，只包含已识别的峰信息。
    """

    peaks: List[Peak]
    wavelengths: List[float] = field(default_factory=list)
    # 峰面积导入文件时，每个峰在各波长下的面积
    area_matrix: Dict[float, List[float]] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SpectraTable:
    """
    光谱吸收表解析结果。

    列=样品，行=峰，单元格可能含多个波长（以 '/' 分隔）。
    """

    sample_names: List[str]
    peak_labels: List[str]
    # sample_name -> list of (peak_label, wavelengths)
    data: Dict[str, List[tuple]]
    metadata: Dict = field(default_factory=dict)
