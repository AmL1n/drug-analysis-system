# -*- coding: utf-8 -*-
"""
装饰器工具模块。

提供 RBAC 权限控制装饰器。
"""

from functools import wraps
from typing import Callable, List

from flask_jwt_extended import get_current_user, verify_jwt_in_request

from app.errors.exceptions import ForbiddenException, UnauthorizedException
from app.model import User


def login_required(fn: Callable) -> Callable:
    """要求登录的装饰器（JWT 校验）。"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as exc:
            raise UnauthorizedException(f"登录校验失败: {exc}")
        return fn(*args, **kwargs)

    return wrapper


def role_required(allowed_roles: List[str]) -> Callable:
    """
    要求用户拥有指定角色的装饰器。

    :param allowed_roles: 允许访问的角色名称列表
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as exc:
                raise UnauthorizedException(f"登录校验失败: {exc}")

            user = get_current_user()
            if not isinstance(user, User):
                raise UnauthorizedException("无法获取当前用户信息")

            user_roles = {role.name for role in user.roles}
            if not user_roles.intersection(set(allowed_roles)):
                raise ForbiddenException("无权访问该资源")

            return fn(*args, **kwargs)

        return wrapper

    return decorator
