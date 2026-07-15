# -*- coding: utf-8 -*-
"""
相对保留时间（RRT）匹配模块。

通过比较样本峰与对照品峰的相对保留时间，计算匹配得分。
"""

from typing import List, Optional, Tuple

import numpy as np

from .types import MatchedPeak, Peak


def calculate_rrt_score(
    sample_rt: float,
    reference_rt: float,
    tolerance: float = 0.02,
) -> float:
    """
    计算单个保留时间的匹配得分。

    采用高斯衰减函数：偏差为 0 时得分为 1，偏差达到 tolerance 时得分约为 0.6，
    偏差越大得分越低。

    :param sample_rt: 样本保留时间
    :param reference_rt: 对照品保留时间
    :param tolerance: 容差阈值
    :return: 匹配得分，范围 [0, 1]
    """
    if tolerance <= 0:
        raise ValueError("容差必须大于 0")

    delta = abs(sample_rt - reference_rt)
    # 高斯衰减：score = exp(-0.5 * (delta / tolerance)^2)
    score = np.exp(-0.5 * (delta / tolerance) ** 2)
    return float(score)


def match_peaks_by_retention_time(
    sample_peaks: List[Peak],
    reference_peaks: List[Peak],
    tolerance: float = 0.02,
) -> List[MatchedPeak]:
    """
    按相对保留时间对样本峰与对照品峰进行匹配。

    对每个对照品峰，在样本峰中寻找保留时间最接近的峰作为候选。

    :param sample_peaks: 样本峰列表
    :param reference_peaks: 对照品峰列表
    :param tolerance: 保留时间容差
    :return: 匹配结果列表
    """
    matches: List[MatchedPeak] = []

    for ref_peak in reference_peaks:
        best_sample_peak: Optional[Peak] = None
        best_score = 0.0
        best_delta = 0.0

        for sample_peak in sample_peaks:
            score = calculate_rrt_score(
                sample_peak.retention_time, ref_peak.retention_time, tolerance
            )
            delta = abs(sample_peak.retention_time - ref_peak.retention_time)

            if score > best_score:
                best_score = score
                best_sample_peak = sample_peak
                best_delta = delta

        match = MatchedPeak(
            sample_peak=best_sample_peak if best_sample_peak else Peak(index=0, retention_time=0.0),
            reference_peak=ref_peak,
            rrt_score=best_score,
            delta_rt=best_delta,
            is_matched=best_score >= 0.6,
        )
        matches.append(match)

    return matches


def match_peaks_by_relative_retention_time(
    sample_peaks: List[Peak],
    reference_peaks: List[Peak],
    tolerance: float = 0.02,
) -> List[MatchedPeak]:
    """
    按相对保留时间（RRT）对样本峰与对照品峰进行匹配。

    要求样本峰和对照品峰均已计算 relative_retention_time。

    :param sample_peaks: 样本峰列表
    :param reference_peaks: 对照品峰列表
    :param tolerance: RRT 容差
    :return: 匹配结果列表
    """
    matches: List[MatchedPeak] = []

    for ref_peak in reference_peaks:
        if ref_peak.relative_retention_time is None:
            continue

        best_sample_peak: Optional[Peak] = None
        best_score = 0.0
        best_delta = 0.0

        for sample_peak in sample_peaks:
            if sample_peak.relative_retention_time is None:
                continue

            score = calculate_rrt_score(
                float(sample_peak.relative_retention_time),
                float(ref_peak.relative_retention_time),
                tolerance,
            )
            delta = abs(
                float(sample_peak.relative_retention_time)
                - float(ref_peak.relative_retention_time)
            )

            if score > best_score:
                best_score = score
                best_sample_peak = sample_peak
                best_delta = delta

        match = MatchedPeak(
            sample_peak=best_sample_peak if best_sample_peak else Peak(index=0, retention_time=0.0),
            reference_peak=ref_peak,
            rrt_score=best_score,
            delta_rt=best_delta,
            is_matched=best_score >= 0.6,
        )
        matches.append(match)

    return matches


def detect_internal_standard(
    sample_peaks: List[Peak],
    reference_rt: float,
    tolerance: float = 0.02,
) -> Optional[Peak]:
    """
    根据保留时间识别内标物峰。

    :param sample_peaks: 样本峰列表
    :param reference_rt: 内标物参考保留时间
    :param tolerance: 容差
    :return: 最可能的内标物峰，未找到返回 None
    """
    best_peak: Optional[Peak] = None
    best_score = 0.0

    for peak in sample_peaks:
        score = calculate_rrt_score(peak.retention_time, reference_rt, tolerance)
        if score > best_score:
            best_score = score
            best_peak = peak

    if best_score >= 0.8:
        return best_peak
    return None
