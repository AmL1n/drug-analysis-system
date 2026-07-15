# -*- coding: utf-8 -*-
"""
预处理模块单元测试。
"""

import numpy as np
import pytest

from app.algorithm.preprocess import (
    min_max_normalize,
    moving_average_smooth,
    polynomial_baseline,
    preprocess_chromatogram,
    savgol_smooth,
    z_score_normalize,
)


class TestPolynomialBaseline:
    def test_removes_linear_baseline(self):
        x = np.linspace(0, 10, 100)
        baseline = 0.5 * x + 1.0
        signal = np.zeros_like(x)
        signal[40:60] = 5.0  # 模拟一个峰
        y = signal + baseline

        corrected = polynomial_baseline(y, degree=1, iterations=5)
        # 校正后基线应接近 0，峰保留
        assert np.mean(corrected[:10]) < 0.5
        assert np.max(corrected) > 3.0

    def test_invalid_degree_raises(self):
        y = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            polynomial_baseline(y, degree=0)


class TestMovingAverageSmooth:
    def test_smooth_preserves_peak(self):
        y = np.zeros(50)
        y[20:30] = 10.0
        smoothed = moving_average_smooth(y, window_size=5)
        assert smoothed.shape == y.shape
        # 平顶峰移动平均后，最大值会形成一个平台，首个最大值索引会前移
        assert np.max(smoothed) == 10.0
        assert 20 <= np.argmax(smoothed) <= 29


class TestSavGolSmooth:
    def test_smooth_shape(self):
        y = np.random.rand(50)
        smoothed = savgol_smooth(y, window_size=11, polyorder=3)
        assert smoothed.shape == y.shape

    def test_invalid_window_raises(self):
        y = np.random.rand(50)
        with pytest.raises(ValueError):
            savgol_smooth(y, window_size=10, polyorder=3)


class TestNormalization:
    def test_min_max_normalize_range(self):
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = min_max_normalize(y)
        assert np.isclose(np.min(normalized), 0.0)
        assert np.isclose(np.max(normalized), 1.0)

    def test_z_score_normalize(self):
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = z_score_normalize(y)
        assert np.isclose(np.mean(normalized), 0.0, atol=1e-10)
        assert np.isclose(np.std(normalized), 1.0, atol=1e-10)


class TestPreprocessPipeline:
    def test_pipeline_runs(self):
        y = np.random.rand(100) + np.linspace(0, 1, 100)
        result = preprocess_chromatogram(
            y,
            baseline_method="polynomial",
            smooth_method="savgol",
            normalize="min_max",
        )
        assert result.shape == y.shape
        assert np.min(result) >= 0.0
        assert np.max(result) <= 1.0
