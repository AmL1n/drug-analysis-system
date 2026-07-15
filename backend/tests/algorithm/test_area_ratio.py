# -*- coding: utf-8 -*-
"""
峰面积比匹配模块单元测试。
"""

import numpy as np

from app.algorithm.area_ratio import (
    calculate_area_ratio_similarity,
    match_area_ratios,
    multivariate_normal_probability,
)
from app.algorithm.types import Peak


class TestCalculateAreaRatioSimilarity:
    def test_identical_vectors(self):
        v = np.array([1.0, 0.5, 0.25])
        score = calculate_area_ratio_similarity(v, v, method="relative_error")
        assert np.isclose(score, 1.0)

    def test_different_vectors(self):
        v1 = np.array([1.0, 0.5, 0.25])
        v2 = np.array([1.0, 0.4, 0.3])
        score = calculate_area_ratio_similarity(v1, v2, method="relative_error")
        assert 0.0 < score < 1.0

    def test_cosine_similarity(self):
        v1 = np.array([1.0, 0.5, 0.25])
        v2 = np.array([1.0, 0.5, 0.25])
        score = calculate_area_ratio_similarity(v1, v2, method="cosine")
        assert np.isclose(score, 1.0)


class TestMatchAreaRatios:
    def test_match_similar_peaks(self):
        sample_peaks = [
            Peak(index=1, retention_time=1.0, area_ratio=1.0),
            Peak(index=2, retention_time=2.0, area_ratio=0.5),
        ]
        reference_peaks = [
            Peak(index=1, retention_time=1.05, area_ratio=1.0),
            Peak(index=2, retention_time=2.05, area_ratio=0.52),
        ]
        score = match_area_ratios(sample_peaks, reference_peaks)
        assert 0.8 < score <= 1.0


class TestMultivariateNormalProbability:
    def test_probability_calculation(self):
        sample = np.array([1.0, 0.5])
        mean = np.array([1.0, 0.5])
        cov = np.array([[0.01, 0.0], [0.0, 0.01]])
        prob = multivariate_normal_probability(sample, mean, cov)
        assert prob > 0.0
