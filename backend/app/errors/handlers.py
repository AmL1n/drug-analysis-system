# -*- coding: utf-8 -*-
"""
全局错误处理器。

将所有异常统一包装为 JSON 响应格式。
"""

from flask import Flask, Response
from werkzeug.exceptions import HTTPException

from app.utils.response import ResponseCode, fail

from .exceptions import BusinessException


def register_handlers(app: Flask) -> None:
    """注册全局错误处理器。"""

    @app.errorhandler(BusinessException)
    def handle_business_exception(exc: BusinessException) -> Response:
        """处理业务异常。"""
        app.logger.warning("业务异常: %s", exc.msg)
        resp = fail(msg=exc.msg, code=exc.code)
        resp.status_code = exc.http_status
        return resp

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException) -> Response:
        """处理 HTTP 异常（如 404、405、500 等）。"""
        app.logger.warning("HTTP 异常: %s %s", exc.code, exc.description)
        resp = fail(msg=exc.description, code=exc.code)
        resp.status_code = exc.code
        return resp

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception) -> Response:
        """兜底异常处理器。"""
        app.logger.exception("未捕获异常: %s", exc)
        resp = fail(
            msg="服务器内部错误", code=ResponseCode.SERVER_ERROR
        )
        resp.status_code = 500
        return resp
