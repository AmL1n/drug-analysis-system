# -*- coding: utf-8 -*-
"""
认证相关 API。
"""

from flask import Blueprint, request
from flask_jwt_extended import get_current_user, jwt_required

from app.errors.exceptions import ParamValidationException
from app.service.auth_service import get_user_profile, login
from app.service.log_service import log_operation
from app.utils.decorators import login_required
from app.utils.response import success

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["POST"])
def login_view():
    """
    用户登录接口。

    请求体：{"username": "admin", "password": "admin123"}
    响应：{"token": "...", "user": {...}}
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        raise ParamValidationException("用户名和密码不能为空")

    result = login(username, password)
    log_operation(
        action="登录",
        module="auth",
        target_type="user",
        target_id=result["user"]["id"],
        detail={"username": result["user"]["username"]},
        user_id=result["user"]["id"],
    )
    return success(data=result)


@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me_view():
    """
    获取当前登录用户信息。
    """
    user = get_current_user()
    profile = get_user_profile(user.id)
    return success(data=profile)
