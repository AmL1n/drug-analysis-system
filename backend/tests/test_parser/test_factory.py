# -*- coding: utf-8 -*-
"""
解析器工厂单元测试。
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.parser.base import ParseError
from app.parser.csv_parser import CsvParser
from app.parser.excel_parser import ExcelParser
from app.parser.factory import ParserFactory
from app.parser.txt_parser import TxtParser


class TestParserFactory:
    def test_get_parser_by_extension(self):
        assert isinstance(ParserFactory.get_parser("test.csv"), CsvParser)
        assert isinstance(ParserFactory.get_parser("test.txt"), TxtParser)
        assert isinstance(ParserFactory.get_parser("test.xlsx"), ExcelParser)
        assert isinstance(ParserFactory.get_parser("test.xls"), ExcelParser)

    def test_unsupported_extension_raises(self):
        with pytest.raises(ParseError):
            ParserFactory.get_parser("test.pdf")

    def test_parse_csv(self):
        content = "Time,Intensity\n1.0,10.0\n2.0,20.0\n3.0,15.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            cg = ParserFactory.parse(path)
            assert len(cg.retention_time) == 3
            assert np.allclose(cg.intensity, [10.0, 20.0, 15.0])
        finally:
            Path(path).unlink()

    def test_supported_extensions(self):
        extensions = ParserFactory.supported_extensions()
        assert "csv" in extensions
        assert "txt" in extensions
        assert "xlsx" in extensions
