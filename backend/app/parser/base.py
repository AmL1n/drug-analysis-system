# -*- coding: utf-8 -*-
"""
解析器抽象基类与异常定义。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

import numpy as np

from app.algorithm.types import Chromatogram
from app.errors.exceptions import BusinessException
from app.utils.response import ResponseCode


class ParseError(BusinessException):
    """文件解析异常（按业务异常处理，返回 400 而非 500）。"""

    def __init__(self, message: str, file_path: Union[str, Path] = None):
        super().__init__(
            msg=message,
            code=ResponseCode.PARAM_ERROR,
            http_status=400,
        )
        self.message = message
        self.file_path = file_path

    def __str__(self) -> str:
        if self.file_path:
            return f"ParseError [{self.file_path}]: {self.message}"
        return f"ParseError: {self.message}"


class BaseParser(ABC):
    """
    文件解析器抽象基类。

    所有具体解析器必须继承此类并实现 parse 方法。
    """

    # 支持的文件扩展名（小写）
    supported_extensions: set = set()

    # 可识别的仪器品牌
    supported_brands: list = []

    @abstractmethod
    def parse(self, file_path: Union[str, Path]) -> Chromatogram:
        """
        解析文件并返回 Chromatogram 对象。

        :param file_path: 文件路径
        :return: 色谱图对象
        :raises ParseError: 解析失败时抛出
        """
        raise NotImplementedError

    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """
        判断当前解析器是否能处理该文件。

        默认按文件扩展名判断，子类可重写以支持内容探测。

        :param file_path: 文件路径
        :return: 是否支持
        """
        path = Path(file_path)
        return path.suffix.lower().lstrip(".") in self.supported_extensions

    def _validate_file_exists(self, file_path: Union[str, Path]) -> Path:
        """校验文件是否存在。"""
        path = Path(file_path)
        if not path.exists():
            raise ParseError(f"文件不存在: {path}", file_path=path)
        if not path.is_file():
            raise ParseError(f"路径不是文件: {path}", file_path=path)
        return path

    def _build_chromatogram(
        self,
        retention_time: np.ndarray,
        intensity: np.ndarray,
        wavelength: float = None,
        metadata: dict = None,
    ) -> Chromatogram:
        """
        构造 Chromatogram 对象，并进行基础校验。

        :param retention_time: 保留时间数组
        :param intensity: 信号强度数组
        :param wavelength: 检测波长
        :param metadata: 元数据
        :return: 色谱图对象
        """
        rt = np.array(retention_time, dtype=float)
        intens = np.array(intensity, dtype=float)

        if len(rt) == 0 or len(intens) == 0:
            raise ParseError("保留时间或强度数据为空")
        if len(rt) != len(intens):
            raise ParseError("保留时间与强度数据长度不一致")
        if len(rt) < 3:
            raise ParseError("有效数据点过少，无法构成色谱图")

        return Chromatogram(
            retention_time=rt,
            intensity=intens,
            wavelength=wavelength,
            metadata=metadata or {},
        )
