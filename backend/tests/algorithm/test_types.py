# -*- coding: utf-8 -*-
"""
算法数据类型单元测试。
"""

import numpy as np
import pytest

from app.algorithm.types import Chromatogram, Peak, Spectrum


class TestChromatogram:
    def test_create_valid(self):
        rt = np.array([1.0, 2.0, 3.0])
        intensity = np.array([0.1, 0.5, 0.2])
        cg = Chromatogram(retention_time=rt, intensity=intensity, wavelength=254.0)
        assert cg.wavelength == 254.0
        assert len(cg.retention_time) == 3

    def test_length_mismatch_raises(self):
        rt = np.array([1.0, 2.0, 3.0])
        intensity = np.array([0.1, 0.5])
        with pytest.raises(ValueError):
            Chromatogram(retention_time=rt, intensity=intensity)

    def test_ndim_mismatch_raises(self):
        rt = np.array([[1.0, 2.0], [3.0, 4.0]])
        intensity = np.array([0.1, 0.5])
        with pytest.raises(ValueError):
            Chromatogram(retention_time=rt, intensity=intensity)


class TestSpectrum:
    def test_create_valid(self):
        wl = np.array([200.0, 250.0, 300.0])
        abs_val = np.array([0.1, 0.8, 0.3])
        sp = Spectrum(wavelength=wl, absorbance=abs_val)
        assert len(sp.wavelength) == 3

    def test_length_mismatch_raises(self):
        wl = np.array([200.0, 250.0])
        abs_val = np.array([0.1, 0.8, 0.3])
        with pytest.raises(ValueError):
            Spectrum(wavelength=wl, absorbance=abs_val)


class TestPeak:
    def test_create_with_defaults(self):
        peak = Peak(index=1, retention_time=5.234)
        assert peak.area == 0.0
        assert peak.height == 0.0
        assert peak.width == 0.0
