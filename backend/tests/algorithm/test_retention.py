# -*- coding: utf-8 -*-
"""
RRT 匹配模块单元测试。
"""

import numpy as np

from app.algorithm.peak_detect import calculate_relative_retention_times
from app.algorithm.retention import (
    calculate_rrt_score,
    detect_internal_standard,
    match_peaks_by_retention_time,
)
from app.algorithm.types import Peak


class TestCalculateRrtScore:
    def test_exact_match(self):
        score = calculate_rrt_score(5.0, 5.0, tolerance=0.02)
        assert np.isclose(score, 1.0)

    def test_large_difference(self):
        score = calculate_rrt_score(5.0, 6.0, tolerance=0.02)
        assert score < 0.1

    def test_at_tolerance(self):
        score = calculate_rrt_score(5.0, 5.02, tolerance=0.02)
        assert 0.5 < score < 1.0


class TestMatchPeaksByRetentionTime:
    def test_match_closest_peak(self):
        sample_peaks = [
            Peak(index=1, retention_time=5.0),
            Peak(index=2, retention_time=8.0),
        ]
        reference_peaks = [
            Peak(index=1, retention_time=5.02),
            Peak(index=2, retention_time=12.0),
        ]
        matches = match_peaks_by_retention_time(
            sample_peaks, reference_peaks, tolerance=0.05
        )
        assert len(matches) == 2
        assert matches[0].sample_peak.retention_time == 5.0
        assert matches[0].is_matched is True
        assert matches[1].is_matched is False


class TestDetectInternalStandard:
    def test_find_internal_standard(self):
        peaks = [
            Peak(index=1, retention_time=5.0),
            Peak(index=2, retention_time=8.0),
            Peak(index=3, retention_time=12.0),
        ]
        std = detect_internal_standard(peaks, reference_rt=8.01, tolerance=0.05)
        assert std is not None
        assert std.retention_time == 8.0

    def test_not_found(self):
        peaks = [Peak(index=1, retention_time=5.0)]
        std = detect_internal_standard(peaks, reference_rt=10.0, tolerance=0.05)
        assert std is None
