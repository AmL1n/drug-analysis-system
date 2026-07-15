# -*- coding: utf-8 -*-
"""
模型融合模块单元测试。
"""

import numpy as np
import pytest

from app.algorithm.fusion import (
    DEFAULT_MODEL_WEIGHTS,
    calculate_confidence,
    normalize_scores,
    validate_weights,
    weighted_fusion,
)


class TestValidateWeights:
    def test_valid_weights(self):
        validate_weights(DEFAULT_MODEL_WEIGHTS)

    def test_invalid_sum_raises(self):
        with pytest.raises(ValueError):
            validate_weights({"a": 0.5, "b": 0.5, "c": 0.5})

    def test_negative_weight_raises(self):
        with pytest.raises(ValueError):
            validate_weights({"a": -0.5, "b": 1.5})


class TestWeightedFusion:
    def test_single_model(self):
        scores = {"rrt": 0.8}
        weights = {"rrt": 1.0}
        result = weighted_fusion(scores, weights)
        assert np.isclose(result, 0.8)

    def test_multiple_models(self):
        scores = {"rrt": 1.0, "area_ratio": 0.5, "uv": 0.0}
        weights = {"rrt": 0.5, "area_ratio": 0.3, "uv": 0.2}
        result = weighted_fusion(scores, weights)
        expected = 1.0 * 0.5 + 0.5 * 0.3 + 0.0 * 0.2
        assert np.isclose(result, expected)


class TestNormalizeScores:
    def test_min_max_normalize(self):
        scores = {"a": 0.2, "b": 0.5, "c": 0.8}
        normalized = normalize_scores(scores, method="min_max")
        assert np.isclose(normalized["a"], 0.0)
        assert np.isclose(normalized["c"], 1.0)


class TestCalculateConfidence:
    def test_high_consistency(self):
        scores = {"a": 0.8, "b": 0.82, "c": 0.81}
        confidence = calculate_confidence(0.81, scores)
        assert confidence > 0.8
