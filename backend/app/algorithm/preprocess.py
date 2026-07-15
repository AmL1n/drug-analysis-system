# -*- coding: utf-8 -*-
"""
数据预处理模块。

提供色谱图和光谱数据的预处理函数：
- 基线校正（多项式拟合）
- 去噪（Savitzky-Golay 滤波）
- 平滑（移动平均）
- 归一化（最大最小归一化 / Z-Score）

所有函数输入输出均为 numpy.ndarray，不依赖任何外部框架。
"""

from typing import Literal, Optional

import numpy as np
from scipy.signal import savgol_filter


def polynomial_baseline(
    y: np.ndarray, degree: int = 3, iterations: int = 10
) -> np.ndarray:
    """
    多项式拟合基线校正。

    通过迭代拟合多项式基线并从原始信号中减去，适用于缓变基线。

    :param y: 原始信号数组
    :param degree: 多项式阶数，默认 3
    :param iterations: 迭代次数，默认 10
    :return: 基线校正后的信号数组
    """
    if y.ndim != 1:
        raise ValueError("输入信号必须为一维数组")
    if degree < 1:
        raise ValueError("多项式阶数必须大于等于 1")

    x = np.arange(len(y), dtype=float)
    corrected = y.astype(float).copy()

    for _ in range(iterations):
        # 对当前信号拟合多项式
        coeffs = np.polyfit(x, corrected, degree)
        baseline = np.polyval(coeffs, x)

        # 仅保留低于拟合基线的点（这些点更可能属于基线）
        mask = corrected <= baseline
        if not np.any(mask):
            break

        # 用基线点重新拟合
        coeffs = np.polyfit(x[mask], corrected[mask], degree)
        baseline = np.polyval(coeffs, x)

        # 从原始信号中减去基线，得到校正结果
        corrected = y - baseline

    return corrected


def median_baseline(
    y: np.ndarray, window_size: int = 51
) -> np.ndarray:
    """
    中值滤波基线估计与校正。

    使用滑动窗口中值估计基线，适用于噪声较大但基线变化较慢的信号。

    :param y: 原始信号数组
    :param window_size: 滑动窗口大小，必须为奇数
    :return: 基线校正后的信号数组
    """
    if y.ndim != 1:
        raise ValueError("输入信号必须为一维数组")
    if window_size % 2 == 0:
        raise ValueError("窗口大小必须为奇数")

    baseline = np.zeros_like(y, dtype=float)
    half = window_size // 2

    for i in range(len(y)):
        left = max(0, i - half)
        right = min(len(y), i + half + 1)
        baseline[i] = np.median(y[left:right])

    # 对基线再做轻微平滑，避免突变
    baseline = moving_average_smooth(baseline, window_size=min(11, window_size))

    return y - baseline


def moving_average_smooth(
    y: np.ndarray, window_size: int = 5
) -> np.ndarray:
    """
    移动平均平滑。

    :param y: 原始信号数组
    :param window_size: 窗口大小
    :return: 平滑后的信号数组
    """
    if y.ndim != 1:
        raise ValueError("输入信号必须为一维数组")
    if window_size < 2:
        return y.copy()

    kernel = np.ones(window_size) / window_size
    smoothed = np.convolve(y, kernel, mode="same")

    # 边界处理：避免卷积导致的边界衰减
    half = window_size // 2
    smoothed[:half] = y[:half]
    smoothed[-half:] = y[-half:]

    return smoothed


def savgol_smooth(
    y: np.ndarray, window_size: int = 11, polyorder: int = 3
) -> np.ndarray:
    """
    Savitzky-Golay 平滑滤波。

    在平滑的同时较好地保留峰形，适合色谱信号。

    :param y: 原始信号数组
    :param window_size: 窗口大小，必须为奇数且大于 polyorder
    :param polyorder: 多项式阶数
    :return: 平滑后的信号数组
    """
    if y.ndim != 1:
        raise ValueError("输入信号必须为一维数组")
    if window_size % 2 == 0:
        raise ValueError("窗口大小必须为奇数")
    if window_size <= polyorder:
        raise ValueError("窗口大小必须大于多项式阶数")

    return savgol_filter(y, window_length=window_size, polyorder=polyorder)


def min_max_normalize(y: np.ndarray) -> np.ndarray:
    """
    最大最小归一化。

    将信号缩放到 [0, 1] 区间。

    :param y: 原始信号数组
    :return: 归一化后的信号数组
    """
    if y.ndim != 1:
        raise ValueError("输入信号必须为一维数组")

    y_min = np.min(y)
    y_max = np.max(y)
    if np.isclose(y_max, y_min):
        return np.zeros_like(y, dtype=float)

    return (y - y_min) / (y_max - y_min)


def z_score_normalize(y: np.ndarray) -> np.ndarray:
    """
    Z-Score 标准化。

    :param y: 原始信号数组
    :return: 标准化后的信号数组
    """
    if y.ndim != 1:
        raise ValueError("输入信号必须为一维数组")

    mean = np.mean(y)
    std = np.std(y)
    if np.isclose(std, 0):
        return np.zeros_like(y, dtype=float)

    return (y - mean) / std


def preprocess_chromatogram(
    y: np.ndarray,
    baseline_method: Optional[Literal["polynomial", "median", "none"]] = "polynomial",
    smooth_method: Optional[Literal["savgol", "moving_average", "none"]] = "savgol",
    normalize: Optional[Literal["min_max", "z_score", "none"]] = "none",
    baseline_degree: int = 3,
    baseline_iterations: int = 10,
    smooth_window: int = 11,
    smooth_polyorder: int = 3,
) -> np.ndarray:
    """
    色谱图预处理流水线。

    按顺序执行：基线校正 → 平滑 → 归一化。

    :param y: 原始信号数组
    :param baseline_method: 基线校正方法
    :param smooth_method: 平滑方法
    :param normalize: 归一化方法
    :param baseline_degree: 多项式基线阶数
    :param baseline_iterations: 基线校正迭代次数
    :param smooth_window: 平滑窗口大小
    :param smooth_polyorder: Savitzky-Golay 多项式阶数
    :return: 预处理后的信号数组
    """
    result = y.astype(float).copy()

    # 根据数据长度动态调整平滑窗口，避免窗口大于数据长度
    effective_window = min(smooth_window, len(result))
    if effective_window % 2 == 0:
        effective_window = max(1, effective_window - 1)

    # 1. 基线校正
    if baseline_method == "polynomial":
        result = polynomial_baseline(result, degree=baseline_degree, iterations=baseline_iterations)
    elif baseline_method == "median":
        result = median_baseline(result, window_size=effective_window)

    # 2. 平滑
    if smooth_method == "savgol":
        result = savgol_smooth(result, window_size=effective_window, polyorder=smooth_polyorder)
    elif smooth_method == "moving_average":
        result = moving_average_smooth(result, window_size=effective_window)

    # 3. 归一化
    if normalize == "min_max":
        result = min_max_normalize(result)
    elif normalize == "z_score":
        result = z_score_normalize(result)

    return result
