# -*- coding: utf-8 -*-
"""
峰检测模块单元测试。
"""

import numpy as np

from app.algorithm.peak_detect import (
    calculate_area_ratios,
    calculate_relative_retention_times,
    detect_peaks,
)
from app.algorithm.types import Chromatogram, Peak


class TestDetectPeaks:
    def test_detect_single_peak(self):
        rt = np.linspace(0, 10, 1000)
        intensity = np.exp(-0.5 * ((rt - 5.0) / 0.2) ** 2) * 100
        cg = Chromatogram(retention_time=rt, intensity=intensity)

        peaks = detect_peaks(cg, min_height=5.0, min_distance=10)
        assert len(peaks) == 1
        assert abs(peaks[0].retention_time - 5.0) < 0.05
        assert peaks[0].height > 90.0
        assert peaks[0].area > 0.0
        assert peaks[0].width > 0.0

    def test_detect_multiple_peaks(self):
        rt = np.linspace(0, 20, 2000)
        intensity = (
            np.exp(-0.5 * ((rt - 5.0) / 0.2) ** 2) * 100
            + np.exp(-0.5 * ((rt - 12.0) / 0.3) ** 2) * 80
            + np.exp(-0.5 * ((rt - 16.0) / 0.25) ** 2) * 60
        )
        cg = Chromatogram(retention_time=rt, intensity=intensity)

        peaks = detect_peaks(cg, min_height=5.0, min_distance=50)
        assert len(peaks) == 3
        assert peaks[0].retention_time < peaks[1].retention_time < peaks[2].retention_time

    def test_no_peak_when_signal_low(self):
        rt = np.linspace(0, 10, 100)
        intensity = np.ones(100) * 0.1
        cg = Chromatogram(retention_time=rt, intensity=intensity)

        peaks = detect_peaks(cg, min_height=1.0)
        assert len(peaks) == 0


class TestCalculateAreaRatios:
    def test_area_ratios_normalized_to_main(self):
        peaks = [
            Peak(index=1, retention_time=1.0, area=100.0),
            Peak(index=2, retention_time=2.0, area=50.0),
            Peak(index=3, retention_time=3.0, area=25.0),
        ]
        result = calculate_area_ratios(peaks)
        assert result[0].area_ratio == 1.0
        assert result[1].area_ratio == 0.5
        assert result[2].area_ratio == 0.25


class TestCalculateRelativeRetentionTimes:
    def test_relative_retention_times(self):
        peaks = [
            Peak(index=1, retention_time=2.0),
            Peak(index=2, retention_time=4.0),
            Peak(index=3, retention_time=6.0),
        ]
        result = calculate_relative_retention_times(peaks, reference_rt=2.0)
        assert result[0].relative_retention_time == 1.0
        assert result[1].relative_retention_time == 2.0
        assert result[2].relative_retention_time == 3.0
