# -*- coding: utf-8 -*-
"""
统一 JSON 响应工具。

所有 API 接口必须通过本模块返回统一格式：
    {
        "code": 0,
        "msg": "success",
        "data": {}
    }

禁止直接返回裸字符串、布尔值或裸对象。
"""

from typing import Any, Dict, List, Optional

from flask import jsonify


class ResponseCode:
    """响应状态码常量。"""

    SUCCESS = 0
    ERROR = 1
    PARAM_ERROR = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500


def success(
    data: Optional[Any] = None, msg: str = "success", code: int = ResponseCode.SUCCESS
):
    """
    成功响应。

    :param data: 响应数据，可为任意 JSON 可序列化对象
    :param msg: 提示信息
    :param code: 业务状态码，默认 0
    :return: Flask Response 对象
    """
    return jsonify({"code": code, "msg": msg, "data": data if data is not None else {}})


def fail(msg: str = "error", code: int = ResponseCode.ERROR, data: Optional[Any] = None):
    """
    失败响应。

    :param msg: 错误信息
    :param code: 业务错误码
    :param data: 可选的附加数据
    :return: Flask Response 对象
    """
    return jsonify(
        {"code": code, "msg": msg, "data": data if data is not None else {}}
    )


def page(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    msg: str = "success",
):
    """
    分页响应。

    :param items: 当前页数据列表
    :param total: 总记录数
    :param page: 当前页码
    :param page_size: 每页大小
    :param msg: 提示信息
    :return: Flask Response 对象
    """
    return jsonify(
        {
            "code": ResponseCode.SUCCESS,
            "msg": msg,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        }
    )


def build_response(
    data: Optional[Any] = None,
    msg: str = "success",
    code: int = ResponseCode.SUCCESS,
    status_code: int = 200,
):
    """
    构造自定义 HTTP 状态码的响应。

    :param data: 响应数据
    :param msg: 提示信息
    :param code: 业务状态码
    :param status_code: HTTP 状态码
    :return: Flask Response 对象
    """
    resp = jsonify(
        {"code": code, "msg": msg, "data": data if data is not None else {}}
    )
    resp.status_code = status_code
    return resp
