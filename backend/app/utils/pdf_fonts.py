# -*- coding: utf-8 -*-
"""
PDF 中文字体注册辅助模块。

用于在生成 PDF 时尝试注册系统自带的中文字体，避免中文显示为方框。
"""

import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# Windows 常见中文字体候选，按优先级排序
_FONT_CANDIDATES = [
    ("SimHei", "C:/Windows/Fonts/simhei.ttf", None),
    ("MicrosoftYaHei", "C:/Windows/Fonts/msyh.ttc", 0),
    ("SimSun", "C:/Windows/Fonts/simsun.ttc", 0),
]


def register_chinese_font():
    """
    尝试注册系统自带的中文字体。

    :return: 注册成功后的字体名称；如果都不可用则返回 'Helvetica' 作为兜底。
    """
    for font_name, font_path, subfont_index in _FONT_CANDIDATES:
        if not os.path.isfile(font_path):
            continue
        try:
            kwargs = {}
            if subfont_index is not None:
                kwargs["subfontIndex"] = subfont_index
            pdfmetrics.registerFont(TTFont(font_name, font_path, **kwargs))
            return font_name
        except Exception:
            # 注册失败时尝试下一个候选字体
            continue
    return "Helvetica"
