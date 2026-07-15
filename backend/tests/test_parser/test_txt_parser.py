# -*- coding: utf-8 -*-
"""
TXT 解析器单元测试。
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.parser.base import ParseError
from app.parser.txt_parser import TxtParser


class TestTxtParser:
    @pytest.fixture
    def parser(self):
        return TxtParser()

    def test_parse_with_header(self, parser):
        content = "Retention Time\tIntensity\n1.0\t10.0\n2.0\t20.0\n3.0\t15.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
            assert np.allclose(cg.retention_time, [1.0, 2.0, 3.0])
            assert np.allclose(cg.intensity, [10.0, 20.0, 15.0])
        finally:
            Path(path).unlink()

    def test_parse_without_header(self, parser):
        content = "1.0 10.0\n2.0 20.0\n3.0 15.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
        finally:
            Path(path).unlink()

    def test_parse_with_comments(self, parser):
        content = "# Instrument: Agilent\n# Date: 2024-01-01\nTime,Intensity\n1.0,10.0\n2.0,20.0\n3.0,15.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
            assert np.allclose(cg.intensity, [10.0, 20.0, 15.0])
        finally:
            Path(path).unlink()

    def test_parse_empty_file_raises(self, parser):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            path = f.name

        try:
            with pytest.raises(ParseError):
                parser.parse(path)
        finally:
            Path(path).unlink()
