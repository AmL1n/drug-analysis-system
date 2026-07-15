# -*- coding: utf-8 -*-
"""
标准导入文件 TXT 解析器。

支持《导入文件标准说明》中的两种 txt 格式：
1. 相对保留时间导入文件：每个 txt 仅包含 1 组试验数据，列为 (序号, 保留时间)。
2. 峰面积导入文件：每个 txt 包含 4 组试验数据，按波长递增排列。

文件编码通常为 GBK/GB2312。
"""

import re
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np

from app.algorithm.types import Peak, PeakList

from .base import BaseParser, ParseError


# 相对保留时间文件表头关键字
RETENTION_TIME_HEADER = "保留时间"
# 峰面积文件表头关键字
PEAK_AREA_HEADER = "面积"
# 通道描述中的波长提取正则
WAVELENGTH_RE = re.compile(r"PDA\s+(\d+(?:\.\d+)?)", re.IGNORECASE)


class StandardTxtParser(BaseParser):
    """标准 TXT 导入文件解析器。"""

    supported_extensions = {"txt"}
    supported_brands = ["standard"]

    def parse(self, file_path: Union[str, Path]) -> PeakList:
        """
        解析标准 TXT 文件。

        :param file_path: TXT 文件路径
        :return: PeakList 对象
        """
        path = self._validate_file_exists(file_path)

        # 尝试常见中文编码
        content = self._read_text(path)
        lines = [line.rstrip("\n\r") for line in content.splitlines()]

        if not lines:
            raise ParseError("文件内容为空", file_path=path)

        first_line = lines[0]
        if RETENTION_TIME_HEADER in first_line:
            return self._parse_retention_time(lines, path)
        if PEAK_AREA_HEADER in first_line:
            return self._parse_peak_area(lines, path)

        raise ParseError(
            "无法识别的标准 TXT 格式，表头应包含“保留时间”或“面积”",
            file_path=path,
        )

    def _read_text(self, path: Path) -> str:
        """按 GBK / UTF-8 顺序读取文本内容。"""
        for encoding in ("gbk", "gb2312", "utf-8"):
            try:
                with open(path, "r", encoding=encoding, errors="strict") as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ParseError("无法识别文件编码，请使用 GBK 或 UTF-8", file_path=path)

    def _parse_retention_time(
        self, lines: List[str], path: Path
    ) -> PeakList:
        """解析相对保留时间导入文件。"""
        peaks: List[Peak] = []
        data_started = False

        for line in lines:
            # 以 #,# 作为数据起始标记
            if line.strip() == "#, #" or line.strip() == "#,#":
                data_started = True
                continue
            if not data_started:
                continue
            cells = [c.strip() for c in line.split(",")]
            if len(cells) < 2:
                continue
            try:
                index = int(cells[0])
                rt = float(cells[1])
            except (ValueError, IndexError):
                continue
            peaks.append(
                Peak(
                    index=index,
                    retention_time=rt,
                    area=0.0,
                    height=0.0,
                    width=0.0,
                )
            )

        if not peaks:
            raise ParseError("未解析到有效保留时间数据", file_path=path)

        return PeakList(
            peaks=peaks,
            metadata={"source_file": str(path), "parser": "StandardTxtParser", "type": "retention_time"},
        )

    def _parse_peak_area(
        self, lines: List[str], path: Path
    ) -> PeakList:
        """解析峰面积导入文件（4 组波长）。"""
        wavelengths: List[float] = []
        area_matrix: dict = {}
        current_wl: float = None
        current_areas: List[float] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # 检测波长头，例如：: 2998 ,PDA 245.0 , (2998 (190-400) ,)
            # 注意跳过表头中的波长描述，只认以 ':' 开头的数据块标记
            match = WAVELENGTH_RE.search(stripped)
            if match and stripped.startswith(":"):
                current_wl = float(match.group(1))
                wavelengths.append(current_wl)
                current_areas = []
                area_matrix[current_wl] = current_areas
                continue

            # 数据起始标记
            if stripped == "#, #" or stripped == "#,#":
                continue

            cells = [c.strip() for c in line.split(",")]
            if len(cells) < 2:
                continue
            try:
                _ = int(cells[0])
                area = float(cells[1])
            except (ValueError, IndexError):
                continue
            if current_wl is not None:
                current_areas.append(area)

        if not wavelengths or not area_matrix:
            raise ParseError("未解析到有效峰面积数据", file_path=path)

        # 构建简化 Peak 列表，保留时间以索引占位
        peaks = []
        base_len = len(area_matrix[wavelengths[0]])
        for idx in range(1, base_len + 1):
            peaks.append(
                Peak(
                    index=idx,
                    retention_time=float(idx),
                    area=area_matrix[wavelengths[0]][idx - 1],
                    height=0.0,
                    width=0.0,
                )
            )

        return PeakList(
            peaks=peaks,
            wavelengths=wavelengths,
            area_matrix=area_matrix,
            metadata={"source_file": str(path), "parser": "StandardTxtParser", "type": "peak_area"},
        )
