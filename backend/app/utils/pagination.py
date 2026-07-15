# -*- coding: utf-8 -*-
"""
分页工具模块。
"""

from typing import Tuple

from flask import request

from app.errors.exceptions import ParamValidationException


def get_pagination_params(
    default_page: int = 1, default_page_size: int = 20, max_page_size: int = 100
) -> Tuple[int, int]:
    """
    从请求参数中获取分页信息。

    :param default_page: 默认页码
    :param default_page_size: 默认每页大小
    :param max_page_size: 最大每页大小
    :return: (page, page_size)
    """
    try:
        page = int(request.args.get("page", default_page))
        # 兼容前端常用的 camelCase 传参
        page_size = int(
            request.args.get("page_size") or request.args.get("pageSize", default_page_size)
        )
    except (ValueError, TypeError):
        raise ParamValidationException("分页参数必须是整数")

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = default_page_size
    if page_size > max_page_size:
        page_size = max_page_size

    return page, page_size
