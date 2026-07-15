# -*- coding: utf-8 -*-
"""
Excel 文件解析器。

支持以下常见格式：
1. 两列：Time + Intensity
2. 多列：Time + 多个波长下的吸光度
3. 仪器导出格式：带表头的多行数据
"""

from pathlib import Path
from typing import Union

import numpy as np
import openpyxl

from app.algorithm.types import Chromatogram

from .base import BaseParser, ParseError
from .csv_parser import INTENSITY_COLUMN_NAMES, TIME_COLUMN_NAMES


class ExcelParser(BaseParser):
    """Excel 解析器。"""

    supported_extensions = {"xlsx", "xls"}
    supported_brands = ["generic"]

    def parse(self, file_path: Union[str, Path]) -> Chromatogram:
        """
        解析 Excel 文件。

        :param file_path: Excel 文件路径
        :return: 色谱图对象
        """
        path = self._validate_file_exists(file_path)

        wb = None
        try:
            wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
            ws = wb.active

            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                raise ParseError("Excel 文件为空", file_path=path)

            headers, data_rows = self._split_header_and_data(rows)

            if headers:
                rt, intensity, wavelength = self._parse_with_headers(
                    headers, data_rows
                )
            else:
                rt, intensity, wavelength = self._parse_without_headers(data_rows)

            return self._build_chromatogram(
                rt,
                intensity,
                wavelength=wavelength,
                metadata={"source_file": str(path), "parser": "ExcelParser"},
            )
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Excel 解析失败: {e}", file_path=path)
        finally:
            if wb is not None:
                wb.close()

    def _split_header_and_data(self, rows: list) -> tuple:
        """区分表头和数据。"""
        headers = None
        data_start = 0

        for i, row in enumerate(rows):
            if not row or all(cell is None or str(cell).strip() == "" for cell in row):
                continue

            # 尝试将行解析为数字
            numeric_cells = []
            for cell in row:
                if cell is None or str(cell).strip() == "":
                    continue
                try:
                    numeric_cells.append(float(cell))
                except (ValueError, TypeError):
                    break

            # 如果整行都能转为数字且至少有两列，则视为数据行
            if len(numeric_cells) >= 2 and len(numeric_cells) == len(
                [c for c in row if c is not None and str(c).strip() != ""]
            ):
                data_start = i
                break
            else:
                headers = [str(cell).strip().lower() if cell else "" for cell in row]
                data_start = i + 1

        data_rows = rows[data_start:]
        return headers, data_rows

    def _parse_with_headers(
        self, headers: list, data_rows: list
    ) -> tuple:
        """根据表头解析保留时间和强度。"""
        time_idx = self._find_column_index(headers, TIME_COLUMN_NAMES)

        # 如果有多个波长列，默认取第一个非时间列作为强度
        if time_idx is None:
            time_idx = 0

        intensity_idx = self._find_column_index(headers, INTENSITY_COLUMN_NAMES)
        if intensity_idx is None:
            # 取时间列之后的第一个有效列
            for idx, header in enumerate(headers):
                if idx != time_idx and header:
                    intensity_idx = idx
                    break

        if intensity_idx is None:
            raise ParseError("Excel 文件未找到强度列")

        rt = []
        intensity = []
        for row in data_rows:
            if len(row) <= max(time_idx, intensity_idx):
                continue
            try:
                rt.append(float(row[time_idx]))
                intensity.append(float(row[intensity_idx]))
            except (ValueError, TypeError):
                continue

        if not rt:
            raise ParseError("未解析到有效数据")

        wavelength = self._detect_wavelength_from_headers(headers)
        return np.array(rt), np.array(intensity), wavelength

    def _parse_without_headers(self, data_rows: list) -> tuple:
        """无表头时默认前两列分别为保留时间和强度。"""
        rt = []
        intensity = []

        for row in data_rows:
            clean_row = [cell for cell in row if cell is not None and str(cell).strip() != ""]
            if len(clean_row) < 2:
                continue
            try:
                rt.append(float(clean_row[0]))
                intensity.append(float(clean_row[1]))
            except (ValueError, TypeError):
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
        import re

        for header in headers:
            match = re.search(r"(\d+(?:\.\d+)?)\s*nm", header, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
