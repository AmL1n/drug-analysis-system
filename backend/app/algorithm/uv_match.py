# -*- coding: utf-8 -*-
"""
UV 光谱匹配模块。

计算样本光谱与对照品光谱的相似度，支持欧氏距离和皮尔逊相关系数。
"""

from typing import List, Optional, Tuple

import numpy as np
from scipy.interpolate import interp1d

from .types import Spectrum


def resample_spectrum(
    spectrum: Spectrum,
    target_wavelengths: np.ndarray,
    kind: str = "linear",
) -> np.ndarray:
    """
    将光谱重采样到目标波长点。

    :param spectrum: 光谱对象
    :param target_wavelengths: 目标波长数组
    :param kind: 插值方法，默认 linear
    :return: 重采样后的吸光度数组
    """
    if len(spectrum.wavelength) < 2:
        raise ValueError("光谱波长点数量不足，无法插值")

    wavelengths = np.array(spectrum.wavelength, dtype=float)
    absorbance = np.array(spectrum.absorbance, dtype=float)

    # 限制在原始波长范围内
    min_wl, max_wl = np.min(wavelengths), np.max(wavelengths)
    valid_mask = (target_wavelengths >= min_wl) & (target_wavelengths <= max_wl)
    valid_wavelengths = target_wavelengths[valid_mask]

    if len(valid_wavelengths) == 0:
        raise ValueError("目标波长范围与光谱波长范围无交集")

    f = interp1d(wavelengths, absorbance, kind=kind, fill_value="extrapolate")
    return f(valid_wavelengths)


def normalize_spectrum(absorbance: np.ndarray, method: str = "min_max") -> np.ndarray:
    """
    对光谱吸光度进行归一化。

    :param absorbance: 吸光度数组
    :param method: 归一化方法，min_max 或 vector
    :return: 归一化后的吸光度数组
    """
    arr = np.array(absorbance, dtype=float)

    if method == "min_max":
        min_val = np.min(arr)
        max_val = np.max(arr)
        if np.isclose(max_val, min_val):
            return np.zeros_like(arr)
        return (arr - min_val) / (max_val - min_val)

    elif method == "vector":
        norm = np.linalg.norm(arr)
        if norm == 0:
            return arr
        return arr / norm

    else:
        raise ValueError(f"不支持的归一化方法: {method}")


def euclidean_distance(
    sample_abs: np.ndarray,
    reference_abs: np.ndarray,
) -> float:
    """
    计算两个光谱吸光度向量的欧氏距离。

    :param sample_abs: 样本吸光度
    :param reference_abs: 对照品吸光度
    :return: 欧氏距离
    """
    return float(np.linalg.norm(sample_abs - reference_abs))


def pearson_correlation(
    sample_abs: np.ndarray,
    reference_abs: np.ndarray,
) -> float:
    """
    计算两个光谱吸光度向量的皮尔逊相关系数。

    :param sample_abs: 样本吸光度
    :param reference_abs: 对照品吸光度
    :return: 相关系数，范围 [-1, 1]
    """
    if len(sample_abs) != len(reference_abs):
        raise ValueError("两个光谱长度必须一致")

    s = np.array(sample_abs, dtype=float)
    r = np.array(reference_abs, dtype=float)

    if np.std(s) == 0 or np.std(r) == 0:
        return 0.0

    corr = np.corrcoef(s, r)[0, 1]
    return float(corr)


def calculate_uv_match_score(
    sample_spectrum: Spectrum,
    reference_spectrum: Spectrum,
    method: str = "euclidean",
    distance_threshold: float = 0.15,
    normalize: bool = True,
) -> float:
    """
    计算样本光谱与对照品光谱的匹配得分。

    :param sample_spectrum: 样本光谱
    :param reference_spectrum: 对照品光谱
    :param method: 匹配方法，euclidean 或 correlation
    :param distance_threshold: 欧氏距离阈值，超过该值得分为 0
    :param normalize: 是否先对光谱进行 min_max 归一化
    :return: 匹配得分，范围 [0, 1]
    """
    # 统一波长网格：取两者波长范围的交集，按步长 1nm 插值
    sample_wl = np.array(sample_spectrum.wavelength, dtype=float)
    ref_wl = np.array(reference_spectrum.wavelength, dtype=float)

    min_wl = max(np.min(sample_wl), np.min(ref_wl))
    max_wl = min(np.max(sample_wl), np.max(ref_wl))

    if min_wl >= max_wl:
        return 0.0

    target_wavelengths = np.arange(min_wl, max_wl + 1.0, 1.0)

    sample_abs = resample_spectrum(sample_spectrum, target_wavelengths)
    reference_abs = resample_spectrum(reference_spectrum, target_wavelengths)

    if normalize:
        sample_abs = normalize_spectrum(sample_abs, method="min_max")
        reference_abs = normalize_spectrum(reference_abs, method="min_max")

    if method == "euclidean":
        distance = euclidean_distance(sample_abs, reference_abs)
        # 将距离映射为得分：距离为 0 得 1，超过阈值得 0
        score = max(0.0, 1.0 - distance / distance_threshold)
        return float(score)

    elif method == "correlation":
        corr = pearson_correlation(sample_abs, reference_abs)
        # 相关系数映射到 [0, 1]
        return float((corr + 1.0) / 2.0)

    else:
        raise ValueError(f"不支持的 UV 匹配方法: {method}")


def find_best_uv_match(
    sample_spectrum: Spectrum,
    reference_spectra: List[Spectrum],
    method: str = "euclidean",
    distance_threshold: float = 0.15,
) -> Tuple[Optional[Spectrum], float]:
    """
    在多个对照品光谱中寻找最佳匹配。

    :param sample_spectrum: 样本光谱
    :param reference_spectra: 对照品光谱列表
    :param method: 匹配方法
    :param distance_threshold: 距离阈值
    :return: (最佳匹配光谱, 得分)
    """
    best_spectrum: Optional[Spectrum] = None
    best_score = 0.0

    for ref_spectrum in reference_spectra:
        score = calculate_uv_match_score(
            sample_spectrum, ref_spectrum, method, distance_threshold
        )
        if score > best_score:
            best_score = score
            best_spectrum = ref_spectrum

    return best_spectrum, best_score
