# -*- coding: utf-8 -*-
"""
贝叶斯融合模块单元测试。
"""

import numpy as np

from app.algorithm.bayes import (
    bayes_from_matches,
    calculate_likelihood,
    naive_bayes_fusion,
)
from app.algorithm.types import MatchedPeak, Peak


class TestCalculateLikelihood:
    def test_high_score_likely_true(self):
        like_true, like_false = calculate_likelihood(0.9)
        assert like_true > like_false

    def test_low_score_likely_false(self):
        like_true, like_false = calculate_likelihood(0.1)
        assert like_false > like_true


class TestNaiveBayesFusion:
    def test_high_scores_give_high_posterior(self):
        scores = {"rrt": 0.95, "area_ratio": 0.9, "uv": 0.92}
        posterior = naive_bayes_fusion(scores, prior=0.5)
        assert posterior > 0.8

    def test_low_scores_give_low_posterior(self):
        scores = {"rrt": 0.1, "area_ratio": 0.1, "uv": 0.1}
        posterior = naive_bayes_fusion(scores, prior=0.5)
        assert posterior < 0.2

    def test_empty_scores_return_prior(self):
        posterior = naive_bayes_fusion({}, prior=0.5)
        assert np.isclose(posterior, 0.5)


class TestBayesFromMatches:
    def test_from_matches(self):
        sample_peak = Peak(index=1, retention_time=5.0)
        ref_peak = Peak(index=1, retention_time=5.0)
        matches = [
            MatchedPeak(
                sample_peak=sample_peak,
                reference_peak=ref_peak,
                rrt_score=0.95,
                area_ratio_score=0.9,
                uv_score=0.92,
            )
        ]
        posterior = bayes_from_matches(matches, prior=0.5)
        assert posterior > 0.5
