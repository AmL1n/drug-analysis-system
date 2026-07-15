# -*- coding: utf-8 -*-
"""
UV 光谱匹配模块单元测试。
"""

import numpy as np

from app.algorithm.types import Spectrum
from app.algorithm.uv_match import (
    calculate_uv_match_score,
    euclidean_distance,
    normalize_spectrum,
    pearson_correlation,
)


class TestNormalizeSpectrum:
    def test_min_max_range(self):
        abs_val = np.array([1.0, 2.0, 3.0, 4.0])
        normalized = normalize_spectrum(abs_val)
        assert np.isclose(np.min(normalized), 0.0)
        assert np.isclose(np.max(normalized), 1.0)


class TestEuclideanDistance:
    def test_distance(self):
        a = np.array([0.0, 1.0, 0.0])
        b = np.array([1.0, 0.0, 1.0])
        dist = euclidean_distance(a, b)
        assert np.isclose(dist, np.sqrt(3.0))


class TestPearsonCorrelation:
    def test_perfect_correlation(self):
        a = np.array([1.0, 2.0, 3.0, 4.0])
        b = np.array([2.0, 4.0, 6.0, 8.0])
        corr = pearson_correlation(a, b)
        assert np.isclose(corr, 1.0)

    def test_inverse_correlation(self):
        a = np.array([1.0, 2.0, 3.0, 4.0])
        b = np.array([4.0, 3.0, 2.0, 1.0])
        corr = pearson_correlation(a, b)
        assert np.isclose(corr, -1.0)


class TestCalculateUvMatchScore:
    def test_identical_spectrum_euclidean(self):
        wl = np.arange(200, 301, 1.0)
        abs_val = np.sin((wl - 200) / 100 * np.pi)
        sp = Spectrum(wavelength=wl, absorbance=abs_val)
        score = calculate_uv_match_score(sp, sp, method="euclidean")
        assert np.isclose(score, 1.0)

    def test_correlation_method(self):
        wl = np.arange(200, 301, 1.0)
        abs_val = np.sin((wl - 200) / 100 * np.pi)
        sp = Spectrum(wavelength=wl, absorbance=abs_val)
        score = calculate_uv_match_score(sp, sp, method="correlation")
        assert np.isclose(score, 1.0)
