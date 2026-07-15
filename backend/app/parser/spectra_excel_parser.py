# -*- coding: utf-8 -*-
"""
光谱吸收表 Excel 解析器。

解析《导入文件标准说明》中的 .xlsx/.xls 光谱吸收表：
- 第一列为“峰的最大吸收值”，行标题为峰 1、峰 2 ...
- 从第二列起，每一列为一个样品；第一行为样品名称。
- 单元格中可能包含多个最大吸收波长，以 '/' 分隔。
"""

from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd

from app.algorithm.types import SpectraTable

from .base import BaseParser, ParseError


class SpectraExcelParser(BaseParser):
    """光谱吸收表 Excel 解析器。"""

    supported_extensions = {"xlsx", "xls"}
    supported_brands = ["standard"]

    def parse(self, file_path: Union[str, Path]) -> SpectraTable:
        """
        解析光谱吸收表 Excel 文件。

        :param file_path: Excel 文件路径
        :return: SpectraTable 对象
        """
        path = self._validate_file_exists(file_path)

        try:
            df = pd.read_excel(path, header=None)
        except Exception as e:
            raise ParseError(f"Excel 读取失败: {e}", file_path=path)

        if df.empty or df.shape[1] < 2:
            raise ParseError("Excel 数据为空或列数不足", file_path=path)

        # 第一行：列标题，第二列起为样品名称
        sample_names = [str(v).strip() for v in df.iloc[0, 1:].tolist() if pd.notna(v)]
        if not sample_names:
            raise ParseError("未找到样品名称", file_path=path)

        # 第一列：行标题，从第二行起为峰标签
        peak_labels = []
        data_rows = []
        for i in range(1, len(df)):
            label = df.iloc[i, 0]
            if pd.isna(label):
                continue
            peak_labels.append(str(label).strip())
            data_rows.append(df.iloc[i, 1:].tolist())

        if not peak_labels:
            raise ParseError("未找到峰标签", file_path=path)

        data: dict = {}
        for col_idx, sample_name in enumerate(sample_names):
            sample_data = []
            for row_idx, label in enumerate(peak_labels):
                cell = data_rows[row_idx][col_idx] if col_idx < len(data_rows[row_idx]) else None
                wavelengths = self._parse_cell(cell)
                sample_data.append((label, wavelengths))
            data[sample_name] = sample_data

        return SpectraTable(
            sample_names=sample_names,
            peak_labels=peak_labels,
            data=data,
            metadata={"source_file": str(path), "parser": "SpectraExcelParser"},
        )

    def _parse_cell(self, value) -> list:
        """解析单元格中的波长，支持 '/' 分隔。"""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return []
        text = str(value).strip()
        if not text or text in ("/", "／", "-"):
            return []
        # 替换全角斜杠
        text = text.replace("／", "/")
        waves = []
        for part in text.split("/"):
            part = part.strip()
            if not part:
                continue
            try:
                waves.append(float(part))
            except ValueError:
                continue
        return waves
