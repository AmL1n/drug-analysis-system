# -*- coding: utf-8 -*-
"""
算法模块包。

本包包含 HPLC-DAD 药物筛查的全部核心算法，遵循以下规范：
- 输入输出为 Python 对象或 numpy 数组
- 不依赖 Flask、SQLAlchemy、文件路径、HTTP 请求
- 每个模块可独立运行和单元测试
"""

from .types import Chromatogram, DrugMatchResult, MatchedPeak, Peak, Spectrum

__all__ = [
    "Chromatogram",
    "Peak",
    "Spectrum",
    "MatchedPeak",
    "DrugMatchResult",
]
