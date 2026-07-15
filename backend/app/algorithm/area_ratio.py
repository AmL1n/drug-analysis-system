# -*- coding: utf-8 -*-
"""
峰面积比值匹配模块。

计算样本峰面积比向量与对照品峰面积比向量的相似度。
"""

from typing import List, Optional

import numpy as np
from scipy.stats import multivariate_normal

from .types import MatchedPeak, Peak


def _get_area_ratio_vector(peaks: List[Peak]) -> np.ndarray:
    """
    从峰列表中提取面积比向量。

    :param peaks: 峰列表
    :return: 面积比向量
    """
    ratios = []
    for peak in peaks:
        ratio = peak.area_ratio if peak.area_ratio is not None else 0.0
        ratios.append(float(ratio))
    return np.array(ratios, dtype=float)


def calculate_area_ratio_similarity(
    sample_ratios: np.ndarray,
    reference_ratios: np.ndarray,
    method: str = "relative_error",
) -> float:
    """
    计算两个峰面积比向量的相似度。

    :param sample_ratios: 样本面积比向量
    :param reference_ratios: 对照品面积比向量
    :param method: 计算方法，可选 relative_error / cosine / correlation
    :return: 相似度得分，范围 [0, 1]
    """
    if len(sample_ratios) != len(reference_ratios):
        raise ValueError("样本与对照品的峰数量必须一致")
    if len(sample_ratios) == 0:
        return 0.0

    sample = np.array(sample_ratios, dtype=float)
    reference = np.array(reference_ratios, dtype=float)

    if method == "relative_error":
        # 相对误差，避免除以 0
        denominator = np.maximum(np.abs(reference), 1e-10)
        relative_errors = np.abs(sample - reference) / denominator
        mean_error = np.mean(relative_errors)
        score = max(0.0, 1.0 - mean_error)
        return float(score)

    elif method == "cosine":
        norm_sample = np.linalg.norm(sample)
        norm_reference = np.linalg.norm(reference)
        if norm_sample == 0 or norm_reference == 0:
            return 0.0
        cosine = np.dot(sample, reference) / (norm_sample * norm_reference)
        # 映射到 [0, 1]
        return float((cosine + 1.0) / 2.0)

    elif method == "correlation":
        if np.std(sample) == 0 or np.std(reference) == 0:
            return 0.0
        corr = np.corrcoef(sample, reference)[0, 1]
        return float((corr + 1.0) / 2.0)

    else:
        raise ValueError(f"不支持的相似度计算方法: {method}")


def match_area_ratios(
    sample_peaks: List[Peak],
    reference_peaks: List[Peak],
    method: str = "relative_error",
) -> float:
    """
    计算样本与对照品的峰面积比整体匹配得分。

    先按保留时间对峰进行排序并一一对应，再计算面积比向量相似度。

    :param sample_peaks: 样本峰列表
    :param reference_peaks: 对照品峰列表
    :param method: 相似度计算方法
    :return: 整体匹配得分 [0, 1]
    """
    if not sample_peaks or not reference_peaks:
        return 0.0

    # 按保留时间排序
    sample_sorted = sorted(sample_peaks, key=lambda p: p.retention_time)
    reference_sorted = sorted(reference_peaks, key=lambda p: p.retention_time)

    # 若峰数量不同，取较少的一方，并按顺序配对
    n = min(len(sample_sorted), len(reference_sorted))
    sample_subset = sample_sorted[:n]
    reference_subset = reference_sorted[:n]

    sample_ratios = _get_area_ratio_vector(sample_subset)
    reference_ratios = _get_area_ratio_vector(reference_subset)

    return calculate_area_ratio_similarity(sample_ratios, reference_ratios, method)


def multivariate_normal_probability(
    sample_ratios: np.ndarray,
    mean_vector: np.ndarray,
    cov_matrix: np.ndarray,
) -> float:
    """
    使用多元正态分布计算峰面积比向量的概率。

    :param sample_ratios: 样本面积比向量
    :param mean_vector: 均值向量
    :param cov_matrix: 协方差矩阵
    :return: 概率密度值（未归一化，越大越相似）
    """
    try:
        mvn = multivariate_normal(mean=mean_vector, cov=cov_matrix, allow_singular=True)
        prob = mvn.pdf(sample_ratios)
        return float(prob)
    except Exception:
        return 0.0


def normalize_probability(
    probability: float,
    max_probability: float = 1.0,
) -> float:
    """
    将概率密度值归一化为 [0, 1] 得分。

    :param probability: 概率密度值
    :param max_probability: 用于归一化的最大概率密度值
    :return: 归一化得分
    """
    if max_probability <= 0:
        return 0.0
    score = probability / max_probability
    return float(min(1.0, max(0.0, score)))
