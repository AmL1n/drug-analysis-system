# -*- coding: utf-8 -*-
"""
相对保留时间（RRT）匹配模块。

通过比较样本峰与对照品峰的相对保留时间，计算匹配得分。
"""

from typing import List, Optional, Tuple

import numpy as np

from .types import MatchedPeak, Peak


MIN_RRT_STD = 0.01


def calculate_rrt_score_with_stats(
    sample_rt: float,
    reference_rt: float,
    rrt_mean: Optional[float],
    rrt_std: Optional[float],
    tolerance: float = 0.02,
) -> float:
    """
    使用增量学习得到的高斯 RRT 分布计算匹配得分。

    当已学习到有效的 RRT 统计量（N > 0，std > 0）时，将样本保留时间按
    参照药物保留时间归一化得到样本 RRT x，再与 learned distribution 比较：
        score = exp(-0.5 * ((x - μ) / max(σ, min_std)) ^ 2)
    结果天然落在 [0, 1]。

    若统计量无效，则回退到基于绝对保留时间的高斯衰减得分。

    :param sample_rt: 样本峰保留时间
    :param reference_rt: 参照药物保留时间（用于计算样本 RRT）
    :param rrt_mean: 学习得到的 RRT 均值 μ
    :param rrt_std: 学习得到的 RRT 标准差 σ
    :param tolerance: 统计量无效时的回退容差
    :return: 匹配得分，范围 [0, 1]
    """
    if tolerance <= 0:
        raise ValueError("容差必须大于 0")

    if (
        rrt_mean is not None
        and rrt_std is not None
        and rrt_std > 0
        and reference_rt is not None
        and reference_rt > 0
    ):
        x = sample_rt / reference_rt
        sigma = max(rrt_std, MIN_RRT_STD)
        return float(np.exp(-0.5 * ((x - rrt_mean) / sigma) ** 2))

    return calculate_rrt_score(sample_rt, reference_rt, tolerance)


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


def match_peaks_by_retention_time_with_stats(
    sample_peaks: List[Peak],
    reference_peaks: List[Peak],
    rrt_mean: float,
    rrt_std: float,
    tolerance: float = 0.02,
) -> List[MatchedPeak]:
    """
    基于增量学习得到的 RRT 高斯分布对样本峰与对照品峰进行匹配。

    对每个对照品峰，利用其相对保留时间反推参照药物保留时间，
    再将各样本峰保留时间归一化为样本 RRT，与 learned μ、σ 比较得分，
    取最高分的样本峰作为匹配结果。

    当某个对照品峰缺少相对保留时间或统计量无效时，回退到绝对保留时间匹配。

    :param sample_peaks: 样本峰列表
    :param reference_peaks: 对照品峰列表
    :param rrt_mean: 学习得到的 RRT 均值 μ
    :param rrt_std: 学习得到的 RRT 标准差 σ
    :param tolerance: 回退匹配时的容差
    :return: 匹配结果列表
    """
    matches: List[MatchedPeak] = []

    for ref_peak in reference_peaks:
        reference_drug_rt: Optional[float] = None
        if (
            ref_peak.relative_retention_time is not None
            and ref_peak.relative_retention_time > 0
            and ref_peak.retention_time is not None
            and ref_peak.retention_time > 0
        ):
            reference_drug_rt = (
                ref_peak.retention_time / ref_peak.relative_retention_time
            )

        best_sample_peak: Optional[Peak] = None
        best_score = 0.0
        best_delta = 0.0

        if reference_drug_rt is not None:
            for sample_peak in sample_peaks:
                if sample_peak.retention_time is None or sample_peak.retention_time <= 0:
                    continue

                score = calculate_rrt_score_with_stats(
                    sample_peak.retention_time,
                    reference_drug_rt,
                    rrt_mean,
                    rrt_std,
                    tolerance,
                )
                x = sample_peak.retention_time / reference_drug_rt
                delta = abs(x - rrt_mean)

                if score > best_score:
                    best_score = score
                    best_sample_peak = sample_peak
                    best_delta = delta
        else:
            # 无法推导参照药物保留时间时回退到绝对保留时间匹配
            for sample_peak in sample_peaks:
                score = calculate_rrt_score(
                    sample_peak.retention_time,
                    ref_peak.retention_time,
                    tolerance,
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
