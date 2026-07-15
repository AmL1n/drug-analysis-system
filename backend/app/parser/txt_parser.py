# -*- coding: utf-8 -*-
"""
TXT 文件解析器。

支持常见仪器导出的 TXT 格式，如 Agilent、Waters、Shimadzu。
自动识别表头、分隔符和列位置。
"""

import re
from pathlib import Path
from typing import Union

import numpy as np

from app.algorithm.types import Chromatogram

from .base import BaseParser, ParseError
from .csv_parser import INTENSITY_COLUMN_NAMES, TIME_COLUMN_NAMES


class TxtParser(BaseParser):
    """TXT 解析器。"""

    supported_extensions = {"txt"}
    supported_brands = ["generic", "agilent", "waters", "shimadzu"]

    def parse(self, file_path: Union[str, Path]) -> Chromatogram:
        """
        解析 TXT 文件。

        :param file_path: TXT 文件路径
        :return: 色谱图对象
        """
        path = self._validate_file_exists(file_path)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            if not lines:
                raise ParseError("TXT 文件为空", file_path=path)

            headers, data_lines = self._split_header_and_data(lines)
            delimiter = self._detect_delimiter(data_lines)

            if headers:
                headers_lower = [h.strip().lower() for h in headers]
                rt, intensity, wavelength = self._parse_with_headers(
                    headers_lower, data_lines, delimiter
                )
            else:
                rt, intensity, wavelength = self._parse_without_headers(
                    data_lines, delimiter
                )

            return self._build_chromatogram(
                rt,
                intensity,
                wavelength=wavelength,
                metadata={"source_file": str(path), "parser": "TxtParser"},
            )
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"TXT 解析失败: {e}", file_path=path)

    def _split_header_and_data(self, lines: list) -> tuple:
        """
        将文件内容分为表头行和数据行。

        表头行通常包含非纯数字内容，数据行每行都可解析为两个及以上数字。
        """
        headers = None
        data_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # 对当前行进行分隔符检测，避免将带空格的表头错误拆分
            delimiter = self._detect_delimiter_from_line(stripped)
            parts = self._split_line(stripped, delimiter)
            try:
                numeric_parts = [float(p) for p in parts]
                # 如果一行有两个及以上数字，则认为是数据开始
                if len(numeric_parts) >= 2:
                    data_start = i
                    break
            except ValueError:
                # 不是数字行，可能是表头
                headers = parts
                data_start = i + 1
                continue

        data_lines = [line.strip() for line in lines[data_start:] if line.strip()]
        return headers, data_lines

    def _detect_delimiter_from_line(self, line: str) -> str:
        """从单行中检测最可能的分隔符。"""
        delimiters = ["\t", ",", ";"]
        counts = {d: line.count(d) for d in delimiters}
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else None

    def _detect_delimiter(self, data_lines: list) -> str:
        """根据数据行检测分隔符。"""
        if not data_lines:
            return "\t"

        delimiters = ["\t", ",", ";", " "]
        counts = {d: 0 for d in delimiters}

        for line in data_lines[:5]:
            for d in delimiters:
                counts[d] += line.count(d)

        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else "\t"

    def _split_line(self, line: str, delimiter: str = None) -> list:
        """按分隔符拆分一行，并过滤空值。"""
        if delimiter:
            parts = line.split(delimiter)
        else:
            parts = re.split(r"[\t,;\s]+", line)
        return [p.strip() for p in parts if p.strip()]

    def _parse_with_headers(
        self, headers: list, data_lines: list, delimiter: str
    ) -> tuple:
        """根据表头解析数据。"""
        time_idx = self._find_column_index(headers, TIME_COLUMN_NAMES)
        intensity_idx = self._find_column_index(headers, INTENSITY_COLUMN_NAMES)

        if time_idx is None or intensity_idx is None:
            if len(headers) >= 2:
                time_idx, intensity_idx = 0, 1
            else:
                raise ParseError("TXT 文件列数不足")

        rt = []
        intensity = []
        for line in data_lines:
            parts = self._split_line(line, delimiter)
            if len(parts) <= max(time_idx, intensity_idx):
                continue
            try:
                rt.append(float(parts[time_idx]))
                intensity.append(float(parts[intensity_idx]))
            except ValueError:
                continue

        if not rt:
            raise ParseError("未解析到有效数据")

        wavelength = self._detect_wavelength_from_headers(headers)
        return np.array(rt), np.array(intensity), wavelength

    def _parse_without_headers(
        self, data_lines: list, delimiter: str
    ) -> tuple:
        """无表头时默认前两列分别为保留时间和强度。"""
        rt = []
        intensity = []

        for line in data_lines:
            parts = self._split_line(line, delimiter)
            if len(parts) < 2:
                continue
            try:
                rt.append(float(parts[0]))
                intensity.append(float(parts[1]))
            except ValueError:
                continue

        if not rt:
            raise ParseError("未解析到有效数据")

        return np.array(rt), np.array(intensity), None

    def _find_column_index(self, headers: list, candidates: list) -> Union[int, None]:
        """在表头中查找候选列名对应的索引。"""
        for candidate in candidates:
            for idx, header in enumerate(headers):
                if candidate in header or header in candidate:
                    return idx
        return None

    def _detect_wavelength_from_headers(self, headers: list) -> Union[float, None]:
        """尝试从表头中检测波长。"""
        for header in headers:
            match = re.search(r"(\d+(?:\.\d+)?)\s*nm", header, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
