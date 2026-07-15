# -*- coding: utf-8 -*-
"""
解析器工厂。

根据文件扩展名和内容自动选择合适的解析器。
"""

from pathlib import Path
from typing import Type, Union

from app.algorithm.types import Chromatogram, PeakList, SpectraTable

from .base import BaseParser, ParseError
from .csv_parser import CsvParser
from .excel_parser import ExcelParser
from .spectra_excel_parser import SpectraExcelParser
from .standard_txt_parser import StandardTxtParser
from .txt_parser import TxtParser


ParseResult = Union[Chromatogram, PeakList, SpectraTable]


class ParserFactory:
    """
    文件解析器工厂。

    提供统一的文件解析入口，屏蔽不同格式的解析细节。
    """

    # 扩展名到默认解析器类的映射
    _parsers: dict = {
        "txt": TxtParser,
        "csv": CsvParser,
        "xlsx": ExcelParser,
        "xls": ExcelParser,
    }

    @classmethod
    def register_parser(cls, extension: str, parser_class: Type[BaseParser]) -> None:
        """
        注册新的解析器。

        :param extension: 文件扩展名（不含点）
        :param parser_class: 解析器类
        """
        cls._parsers[extension.lower()] = parser_class

    @classmethod
    def get_parser(cls, file_path: Union[str, Path]) -> BaseParser:
        """
        根据文件路径获取合适的解析器实例。

        对 txt 和 xlsx/xls 会先读取内容进行格式探测。

        :param file_path: 文件路径
        :return: 解析器实例
        :raises ParseError: 找不到对应解析器时抛出
        """
        path = Path(file_path)
        extension = path.suffix.lower().lstrip(".")

        parser_class = cls._detect_parser_class(path, extension)
        if parser_class is None:
            raise ParseError(
                f"不支持的文件格式: .{extension}，支持的格式：{list(cls._parsers.keys())}",
                file_path=path,
            )

        return parser_class()

    @classmethod
    def parse(cls, file_path: Union[str, Path]) -> ParseResult:
        """
        解析文件并返回对应的数据对象。

        :param file_path: 文件路径
        :return: Chromatogram / PeakList / SpectraTable
        """
        parser = cls.get_parser(file_path)
        return parser.parse(file_path)

    @classmethod
    def supported_extensions(cls) -> list:
        """返回所有支持的文件扩展名。"""
        return list(cls._parsers.keys())

    @classmethod
    def _detect_parser_class(cls, path: Path, extension: str) -> Type[BaseParser]:
        """根据扩展名和内容探测解析器类。"""
        if extension == "txt":
            return cls._detect_txt_parser(path) or cls._parsers.get("txt")

        if extension in ("xlsx", "xls"):
            return cls._detect_excel_parser(path) or cls._parsers.get(extension)

        return cls._parsers.get(extension)

    @classmethod
    def _detect_txt_parser(cls, path: Path):
        """探测是否为标准导入 TXT 格式。"""
        for encoding in ("gbk", "gb2312", "utf-8"):
            try:
                with open(path, "r", encoding=encoding, errors="strict") as f:
                    first_lines = [f.readline() for _ in range(3)]
                text = "".join(first_lines)
                if "保留时间" in text or "面积" in text:
                    return StandardTxtParser
            except (UnicodeDecodeError, UnicodeError, FileNotFoundError):
                continue
        return None

    @classmethod
    def _detect_excel_parser(cls, path: Path):
        """探测是否为光谱吸收表 Excel 格式。"""
        try:
            import pandas as pd

            df = pd.read_excel(path, header=None, nrows=3)
            if df.empty or df.shape[1] < 2:
                return None
            header_text = " ".join(str(v) for v in df.iloc[0].tolist() if pd.notna(v))
            if "最大吸收" in header_text or "峰的最大吸收值" in header_text:
                return SpectraExcelParser
        except Exception:
            return None
        return None
