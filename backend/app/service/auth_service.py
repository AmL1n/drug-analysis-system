# -*- coding: utf-8 -*-
"""
认证服务模块。
"""

from datetime import timedelta
from typing import Optional

from app.dao.user_dao import UserDAO
from app.errors.exceptions import ParamValidationException, UnauthorizedException
from app.model import User
from app.utils.security import create_jwt_token, verify_password


def login(username: str, password: str) -> dict:
    """
    用户登录。

    :param username: 用户名
    :param password: 密码
    :return: 包含用户信息和 Token 的字典
    """
    if not username or not password:
        raise ParamValidationException("用户名和密码不能为空")

    user = UserDAO.get_by_username(username)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedException("用户名或密码错误")

    if not user.is_active:
        raise UnauthorizedException("用户已被禁用")

    UserDAO.update_last_login(user)

    token = create_jwt_token(
        identity=str(user.id), expires_delta=timedelta(hours=2)
    )

    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "realName": user.real_name,
            "email": user.email,
            "operatorNo": user.operator_no,
            "roles": [role.name for role in user.roles],
        },
    }


def get_user_profile(user_id: int) -> Optional[dict]:
    """
    获取用户信息。

    :param user_id: 用户ID
    :return: 用户信息字典
    """
    user = UserDAO.get_by_id(user_id)
    if user is None:
        return None

    return {
        "id": user.id,
        "username": user.username,
        "realName": user.real_name,
        "email": user.email,
        "operatorNo": user.operator_no,
        "roles": [role.name for role in user.roles],
        "lastLoginAt": (
            user.last_login_at.isoformat() if user.last_login_at else None
        ),
    }
