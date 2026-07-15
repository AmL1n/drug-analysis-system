# -*- coding: utf-8 -*-
"""
文件解析模块包。

提供统一入口 ParserFactory，根据文件类型和仪器厂商自动选择解析器，
将 TXT/CSV/Excel 文件解析为算法层可识别的 Chromatogram 对象。

本模块不依赖 Flask、数据库、HTTP 请求，可独立运行和测试。
"""

from .base import BaseParser, ParseError
from .csv_parser import CsvParser
from .excel_parser import ExcelParser
from .factory import ParserFactory
from .txt_parser import TxtParser

__all__ = [
    "BaseParser",
    "ParseError",
    "CsvParser",
    "ExcelParser",
    "TxtParser",
    "ParserFactory",
]
