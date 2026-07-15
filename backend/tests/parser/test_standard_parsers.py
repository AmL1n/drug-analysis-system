# -*- coding: utf-8 -*-
"""
标准导入文件解析器测试。
"""

import os

import pytest

from app.algorithm.types import PeakList, SpectraTable
from app.parser.factory import ParserFactory
from app.parser.spectra_excel_parser import SpectraExcelParser
from app.parser.standard_txt_parser import StandardTxtParser


def test_parse_retention_time_txt(tmp_path):
    """测试相对保留时间 TXT 解析。"""
    file_path = tmp_path / "rt.txt"
    file_path.write_text(
        "保留时间,分钟\n(,）\n#,#\n1,6.256\n2,10.821\n3,12.988\n",
        encoding="gbk",
    )

    result = ParserFactory.parse(str(file_path))
    assert isinstance(result, PeakList)
    assert len(result.peaks) == 3
    assert result.peaks[0].retention_time == pytest.approx(6.256)
    assert result.peaks[1].retention_time == pytest.approx(10.821)


def test_parse_peak_area_txt(tmp_path):
    """测试峰面积 TXT 解析。"""
    file_path = tmp_path / "area.txt"
    lines = [
        "进样,样品名称,示例,混梯,样品瓶,采集日期,面积,处理通道说明,2998 PDA 245.0 纳米 (2998 (190-400) 纳米)",
        "1, ,10",
        "2, 2024/01/01 10:00:00 ,CST",
        ": 2998 ,PDA 245.0 , (2998 (190-400) ,)",
        "#,#",
        "1,100000",
        "2,200000",
        ": 2998 ,PDA 250.0 , (2998 (190-400) ,)",
        "#,#",
        "1,110000",
        "2,210000",
    ]
    file_path.write_text("\n".join(lines), encoding="gbk")

    result = ParserFactory.parse(str(file_path))
    assert isinstance(result, PeakList)
    assert result.wavelengths == [245.0, 250.0]
    assert len(result.peaks) == 2
    assert result.area_matrix[245.0] == [100000.0, 200000.0]
    assert result.area_matrix[250.0] == [110000.0, 210000.0]


def test_parse_spectra_excel(tmp_path):
    """测试光谱吸收表 Excel 解析。"""
    from openpyxl import Workbook

    file_path = tmp_path / "spectra.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["峰的最大吸收值", "样品1", "样品2"])
    ws.append(["峰1", "230/290", "232/288"])
    ws.append(["峰2", "220", "225/310"])
    wb.save(str(file_path))

    result = ParserFactory.parse(str(file_path))
    assert isinstance(result, SpectraTable)
    assert result.sample_names == ["样品1", "样品2"]
    assert result.peak_labels == ["峰1", "峰2"]
    assert result.data["样品1"][0] == ("峰1", [230.0, 290.0])
    assert result.data["样品2"][1] == ("峰2", [225.0, 310.0])


def test_standard_parser_invalid_format(tmp_path):
    """测试无法识别的 TXT 会抛出异常。"""
    file_path = tmp_path / "unknown.txt"
    file_path.write_text("未知内容\n1,2\n", encoding="utf-8")

    with pytest.raises(Exception):
        StandardTxtParser().parse(str(file_path))


def test_factory_fallback_to_chromatogram_csv(tmp_path):
    """测试普通色谱图 CSV 仍走原有解析器。"""
    file_path = tmp_path / "chrom.csv"
    file_path.write_text(
        "time,absorbance\n1.0,10\n2.0,20\n3.0,15\n", encoding="utf-8"
    )

    result = ParserFactory.parse(str(file_path))
    assert not isinstance(result, PeakList)
    assert not isinstance(result, SpectraTable)
    assert hasattr(result, "retention_time")
