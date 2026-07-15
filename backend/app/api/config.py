# -*- coding: utf-8 -*-
"""
系统配置相关 API。
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.errors.exceptions import ParamValidationException
from app.service.config_service import get_config_value, set_config_value
from app.service.log_service import log_operation
from app.utils.response import success

config_bp = Blueprint("config", __name__)


@config_bp.route("/system/configs/<string:key>", methods=["GET"])
@jwt_required()
def get_config_view(key: str):
    """按 key 获取系统配置值。"""
    value = get_config_value(key)
    return success(data={"key": key, "value": value}, msg="ok")


@config_bp.route("/system/configs/<string:key>", methods=["PUT"])
@jwt_required()
def set_config_view(key: str):
    """按 key 设置系统配置值。"""
    data = request.get_json(silent=True) or {}
    value = data.get("value")
    if value is None:
        raise ParamValidationException("value 不能为空")

    result = set_config_value(key, value, description=data.get("description"))
    log_operation(
        action="更新系统配置",
        module="system",
        target_type="system_config",
        target_id=key,
        detail=result,
    )
    return success(data=result, msg="ok")
