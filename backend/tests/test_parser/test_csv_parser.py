# -*- coding: utf-8 -*-
"""
CSV 解析器单元测试。
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.parser.csv_parser import CsvParser
from app.parser.base import ParseError


class TestCsvParser:
    @pytest.fixture
    def parser(self):
        return CsvParser()

    def test_parse_with_headers(self, parser):
        content = "Time,Intensity\n1.0,10.0\n2.0,20.0\n3.0,15.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
            assert np.allclose(cg.retention_time, [1.0, 2.0, 3.0])
            assert np.allclose(cg.intensity, [10.0, 20.0, 15.0])
        finally:
            Path(path).unlink()

    def test_parse_without_headers(self, parser):
        content = "1.0,10.0\n2.0,20.0\n3.0,15.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
            assert np.allclose(cg.retention_time, [1.0, 2.0, 3.0])
        finally:
            Path(path).unlink()

    def test_parse_tab_delimited(self, parser):
        content = "Time\tIntensity\n1.0\t10.0\n2.0\t20.0\n3.0\t15.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
        finally:
            Path(path).unlink()

    def test_parse_wavelength_header(self, parser):
        content = "Time,Absorbance 254nm\n1.0,10.0\n2.0,20.0\n3.0,15.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            cg = parser.parse(path)
            assert cg.wavelength == 254.0
            assert len(cg.retention_time) == 3
        finally:
            Path(path).unlink()

    def test_parse_empty_file_raises(self, parser):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            path = f.name

        try:
            with pytest.raises(ParseError):
                parser.parse(path)
        finally:
            Path(path).unlink()
