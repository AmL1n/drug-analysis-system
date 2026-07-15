# -*- coding: utf-8 -*-
"""
Excel 解析器单元测试。
"""

import tempfile
from pathlib import Path

import numpy as np
import openpyxl
import pytest

from app.parser.base import ParseError
from app.parser.excel_parser import ExcelParser


class TestExcelParser:
    @pytest.fixture
    def parser(self):
        return ExcelParser()

    def _create_excel(self, data):
        """创建临时 Excel 文件。"""
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in data:
            ws.append(row)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = f.name
        wb.save(path)
        wb.close()
        return path

    def test_parse_with_headers(self, parser):
        path = self._create_excel([
            ["Time", "Intensity"],
            [1.0, 10.0],
            [2.0, 20.0],
            [3.0, 15.0],
        ])

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
            assert np.allclose(cg.retention_time, [1.0, 2.0, 3.0])
            assert np.allclose(cg.intensity, [10.0, 20.0, 15.0])
        finally:
            Path(path).unlink()

    def test_parse_without_headers(self, parser):
        path = self._create_excel([
            [1.0, 10.0],
            [2.0, 20.0],
            [3.0, 15.0],
        ])

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
        finally:
            Path(path).unlink()

    def test_parse_multi_wavelength(self, parser):
        path = self._create_excel([
            ["Time", "254nm", "280nm"],
            [1.0, 10.0, 12.0],
            [2.0, 20.0, 22.0],
            [3.0, 15.0, 17.0],
        ])

        try:
            cg = parser.parse(path)
            assert len(cg.retention_time) == 3
            assert cg.wavelength == 254.0
        finally:
            Path(path).unlink()

    def test_parse_empty_file_raises(self, parser):
        path = self._create_excel([])

        try:
            with pytest.raises(ParseError):
                parser.parse(path)
        finally:
            Path(path).unlink()
