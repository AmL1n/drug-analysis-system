# -*- coding: utf-8 -*-
"""
CSV 文件解析器。

支持通用 CSV 格式，自动识别分隔符、保留时间列和强度列。
"""

import csv
from pathlib import Path
from typing import Union

import numpy as np

from app.algorithm.types import Chromatogram

from .base import BaseParser, ParseError


# 保留时间列可能的名称（不区分大小写）
TIME_COLUMN_NAMES = [
    "time",
    "rt",
    "retention time",
    "retention_time",
    "min",
    "minutes",
    "t",
]

# 强度列可能的名称（不区分大小写）
INTENSITY_COLUMN_NAMES = [
    "intensity",
    "absorbance",
    "abs",
    "signal",
    "response",
    "area",
    "height",
    "mv",
    "mau",
]


class CsvParser(BaseParser):
    """CSV 解析器。"""

    supported_extensions = {"csv"}
    supported_brands = ["generic", "agilent", "waters"]

    def parse(self, file_path: Union[str, Path]) -> Chromatogram:
        """
        解析 CSV 文件。

        :param file_path: CSV 文件路径
        :return: 色谱图对象
        """
        path = self._validate_file_exists(file_path)

        try:
            delimiter = self._detect_delimiter(path)
            headers, rows = self._read_csv(path, delimiter)

            if headers:
                rt, intensity, wavelength = self._parse_with_headers(headers, rows)
            else:
                rt, intensity = self._parse_without_headers(rows)
                wavelength = None

            return self._build_chromatogram(
                rt,
                intensity,
                wavelength=wavelength,
                metadata={"source_file": str(path), "parser": "CsvParser"},
            )
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"CSV 解析失败: {e}", file_path=path)

    def _detect_delimiter(self, path: Path) -> str:
        """自动检测 CSV 分隔符。"""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()

        # 优先尝试常见分隔符
        delimiters = [",", "\t", ";", " "]
        counts = {d: first_line.count(d) for d in delimiters}
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else ","

    def _read_csv(
        self, path: Path, delimiter: str
    ) -> tuple:
        """
        读取 CSV 文件。

        :return: (headers, rows) 如果第一行是数字则 headers 为 None
        """
        rows = []
        headers = None

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f, delimiter=delimiter)
            for i, row in enumerate(reader):
                if not row or all(cell.strip() == "" for cell in row):
                    continue

                # 尝试将第一行解析为表头
                if i == 0:
                    try:
                        [float(cell) for cell in row if cell.strip()]
                        # 第一行全是数字，没有表头
                        numeric_row = [float(cell) for cell in row if cell.strip()]
                        rows.append(numeric_row)
                    except ValueError:
                        headers = [cell.strip().lower() for cell in row]
                    continue

                try:
                    numeric_row = [float(cell) for cell in row if cell.strip()]
                    if numeric_row:
                        rows.append(numeric_row)
                except ValueError:
                    # 跳过非数字行（如注释、元数据）
                    continue

        return headers, rows

    def _parse_with_headers(
        self, headers: list, rows: list
    ) -> tuple:
        """根据表头解析保留时间和强度列。"""
        time_idx = self._find_column_index(headers, TIME_COLUMN_NAMES)
        intensity_idx = self._find_column_index(headers, INTENSITY_COLUMN_NAMES)

        if time_idx is None or intensity_idx is None:
            # 未找到匹配列名，默认使用前两列
            if len(headers) >= 2:
                time_idx, intensity_idx = 0, 1
            else:
                raise ParseError("CSV 文件列数不足")

        rt = np.array([row[time_idx] for row in rows if len(row) > max(time_idx, intensity_idx)])
        intensity = np.array([row[intensity_idx] for row in rows if len(row) > max(time_idx, intensity_idx)])

        wavelength = self._detect_wavelength(headers)
        return rt, intensity, wavelength

    def _parse_without_headers(self, rows: list) -> tuple:
        """无表头时，默认第一列为保留时间，第二列为强度。"""
        if not rows or len(rows[0]) < 2:
            raise ParseError("CSV 数据至少需要两列（保留时间和强度）")

        rt = np.array([row[0] for row in rows])
        intensity = np.array([row[1] for row in rows])
        return rt, intensity

    def _find_column_index(self, headers: list, candidates: list) -> Union[int, None]:
        """在表头中查找候选列名对应的索引。"""
        for candidate in candidates:
            for idx, header in enumerate(headers):
                if candidate in header or header in candidate:
                    return idx
        return None

    def _detect_wavelength(self, headers: list) -> Union[float, None]:
        """尝试从表头中检测波长信息。"""
        for header in headers:
            # 匹配形如 "254 nm", "254nm", "wavelength 254" 等
            import re

            match = re.search(r"(\d+(?:\.\d+)?)\s*nm", header, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
