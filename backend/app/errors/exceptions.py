# -*- coding: utf-8 -*-
"""
业务异常定义。
"""

from app.utils.response import ResponseCode


class BusinessException(Exception):
    """
    业务异常。

    用于 Service 层抛出可预期的业务错误，如参数校验失败、资源不存在等。
    """

    def __init__(
        self,
        msg: str = "业务处理失败",
        code: int = ResponseCode.ERROR,
        http_status: int = 200,
    ):
        super().__init__(msg)
        self.msg = msg
        self.code = code
        self.http_status = http_status

    def __str__(self) -> str:
        return f"BusinessException(code={self.code}, msg={self.msg})"


class NotFoundException(BusinessException):
    """资源不存在异常。"""

    def __init__(self, msg: str = "资源不存在"):
        super().__init__(msg=msg, code=ResponseCode.NOT_FOUND, http_status=404)


class ParamValidationException(BusinessException):
    """参数校验异常。"""

    def __init__(self, msg: str = "参数校验失败"):
        super().__init__(msg=msg, code=ResponseCode.PARAM_ERROR, http_status=400)


class UnauthorizedException(BusinessException):
    """未授权异常。"""

    def __init__(self, msg: str = "未登录或登录已过期"):
        super().__init__(msg=msg, code=ResponseCode.UNAUTHORIZED, http_status=401)


class ForbiddenException(BusinessException):
    """无权限异常。"""

    def __init__(self, msg: str = "无权访问"):
        super().__init__(msg=msg, code=ResponseCode.FORBIDDEN, http_status=403)
