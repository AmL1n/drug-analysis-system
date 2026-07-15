# -*- coding: utf-8 -*-
"""
峰检测模块。

基于 scipy.signal.find_peaks 实现色谱峰识别，并计算：
- 保留时间
- 峰面积（梯形法）
- 峰高
- 半峰宽
- 峰起点/终点索引
"""

from typing import List, Optional, Tuple

import numpy as np
from scipy.signal import find_peaks

from .types import Chromatogram, Peak


def _estimate_peak_bounds(
    y: np.ndarray, peak_index: int, rel_height: float = 0.5
) -> Tuple[int, int]:
    """
    估计峰的左右边界。

    从峰顶向两侧下降，找到信号首次低于相对高度的位置作为边界。

    :param y: 信号数组
    :param peak_index: 峰顶索引
    :param rel_height: 相对高度，默认 0.5（半高处）
    :return: (左边界索引, 右边界索引)
    """
    peak_height = y[peak_index]
    if peak_height <= 0:
        return peak_index, peak_index

    threshold = peak_height * rel_height

    # 向左搜索
    left = peak_index
    while left > 0 and y[left] > threshold:
        left -= 1

    # 向右搜索
    right = peak_index
    while right < len(y) - 1 and y[right] > threshold:
        right += 1

    return left, right


def _calculate_peak_width(
    rt: np.ndarray,
    y: np.ndarray,
    peak_index: int,
    left_index: int,
    right_index: int,
    rel_height: float = 0.5,
) -> float:
    """
    计算半峰宽。

    在峰边界内，找到半高处左右两侧对应的保留时间差。

    :param rt: 保留时间数组
    :param y: 信号数组
    :param peak_index: 峰顶索引
    :param left_index: 左边界索引
    :param right_index: 右边界索引
    :param rel_height: 相对高度，默认 0.5
    :return: 半峰宽，单位与 rt 一致
    """
    peak_height = y[peak_index]
    if peak_height <= 0:
        return 0.0

    threshold = peak_height * rel_height
    window_y = y[left_index : right_index + 1]
    window_rt = rt[left_index : right_index + 1]

    # 线性插值找到半高处的左右保留时间
    left_rt = _interpolate_x_at_y(window_rt, window_y, threshold, direction="left")
    right_rt = _interpolate_x_at_y(window_rt, window_y, threshold, direction="right")

    return float(right_rt - left_rt)


def _interpolate_x_at_y(
    x: np.ndarray, y: np.ndarray, target_y: float, direction: str = "left"
) -> float:
    """
    线性插值找到 y = target_y 对应的 x 值。

    :param x: x 数组
    :param y: y 数组
    :param target_y: 目标 y 值
    :param direction: 搜索方向，left 从峰顶向左，right 从峰顶向右
    :return: 插值得到的 x 值
    """
    peak_idx = np.argmax(y)

    if direction == "left":
        for i in range(peak_idx, 0, -1):
            if y[i] >= target_y >= y[i - 1]:
                if np.isclose(y[i], y[i - 1]):
                    return float(x[i])
                ratio = (target_y - y[i - 1]) / (y[i] - y[i - 1])
                return float(x[i - 1] + ratio * (x[i] - x[i - 1]))
        return float(x[0])

    # direction == "right"
    for i in range(peak_idx, len(y) - 1):
        if y[i] >= target_y >= y[i + 1]:
            if np.isclose(y[i], y[i + 1]):
                return float(x[i])
            ratio = (target_y - y[i + 1]) / (y[i] - y[i + 1])
            return float(x[i + 1] + ratio * (x[i] - x[i + 1]))
    return float(x[-1])


def detect_peaks(
    chromatogram: Chromatogram,
    min_height: Optional[float] = None,
    min_distance: int = 5,
    min_prominence: Optional[float] = None,
    width_bounds: Optional[Tuple[float, float]] = None,
    rel_height: float = 0.5,
    baseline_corrected: bool = True,
) -> List[Peak]:
    """
    从色谱图中检测峰。

    :param chromatogram: 色谱图对象
    :param min_height: 最小峰高，None 时自动取信号最大值的 5%
    :param min_distance: 峰之间的最小索引距离
    :param min_prominence: 最小 prominence，None 时自动取信号最大值的 1%
    :param width_bounds: 峰宽范围 (min_width, max_width)，单位同 retention_time
    :param rel_height: 计算峰宽时使用的相对高度
    :param baseline_corrected: 色谱图是否已完成基线校正
    :return: 按保留时间排序的 Peak 对象列表
    """
    rt = chromatogram.retention_time
    y = chromatogram.intensity.astype(float)

    if len(rt) != len(y):
        raise ValueError("保留时间与信号强度长度不一致")
    if len(y) < 3:
        raise ValueError("信号数据点过少，无法检测峰")

    y_max = np.max(y)
    if y_max <= 0:
        return []

    if min_height is None:
        min_height = y_max * 0.05
    if min_prominence is None:
        min_prominence = y_max * 0.01

    # 构造 find_peaks 参数
    find_kwargs = {
        "height": min_height,
        "distance": min_distance,
        "prominence": min_prominence,
    }
    if width_bounds is not None:
        find_kwargs["width"] = width_bounds

    peak_indices, properties = find_peaks(y, **find_kwargs)

    peaks: List[Peak] = []
    for idx, peak_idx in enumerate(peak_indices, start=1):
        left_idx, right_idx = _estimate_peak_bounds(y, peak_idx, rel_height=rel_height)

        # 计算峰面积（梯形法）
        area = float(np.trapz(y[left_idx : right_idx + 1], rt[left_idx : right_idx + 1]))
        height = float(y[peak_idx])
        retention_time = float(rt[peak_idx])

        # 计算半峰宽
        fwhm = _calculate_peak_width(
            rt, y, peak_idx, left_idx, right_idx, rel_height=0.5
        )

        peak = Peak(
            index=idx,
            retention_time=retention_time,
            area=area,
            height=height,
            width=fwhm,
            start_index=int(left_idx),
            end_index=int(right_idx),
            wavelength=chromatogram.wavelength,
            metadata={
                "prominence": float(properties["prominences"][idx - 1]),
                "baseline_corrected": baseline_corrected,
            },
        )
        peaks.append(peak)

    # 按保留时间排序
    peaks.sort(key=lambda p: p.retention_time)

    # 重新编号
    for i, peak in enumerate(peaks, start=1):
        peak.index = i

    return peaks


def calculate_area_ratios(peaks: List[Peak]) -> List[Peak]:
    """
    计算峰面积比值。

    以最大峰面积为基准（或指定主峰），将每个峰的面积归一化为相对比值。

    :param peaks: Peak 对象列表
    :return: 更新 area_ratio 后的 Peak 对象列表
    """
    if not peaks:
        return peaks

    # 查找主峰：优先使用 is_main_peak 标记，否则使用面积最大者
    main_peak = None
    for peak in peaks:
        if peak.metadata.get("is_main_peak"):
            main_peak = peak
            break

    if main_peak is None:
        main_peak = max(peaks, key=lambda p: p.area)

    main_area = main_peak.area
    if main_area <= 0:
        return peaks

    for peak in peaks:
        peak.area_ratio = float(peak.area / main_area)
        if peak == main_peak:
            peak.area_ratio = 1.0

    return peaks


def calculate_relative_retention_times(
    peaks: List[Peak], reference_rt: Optional[float] = None
) -> List[Peak]:
    """
    计算相对保留时间。

    :param peaks: Peak 对象列表
    :param reference_rt: 参考保留时间，None 时使用第一个峰
    :return: 更新 relative_retention_time 后的 Peak 对象列表
    """
    if not peaks:
        return peaks

    if reference_rt is None:
        reference_rt = peaks[0].retention_time

    if reference_rt <= 0:
        raise ValueError("参考保留时间必须大于 0")

    for peak in peaks:
        peak.relative_retention_time = float(peak.retention_time / reference_rt)

    return peaks
