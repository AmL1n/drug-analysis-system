# -*- coding: utf-8 -*-
"""
操作日志服务。

为各业务模块提供统一的操作日志记录入口。
"""

from typing import Any, Dict, Optional

from flask import has_request_context, request
from flask_jwt_extended import get_current_user

from app.model import OperationLog, User, db


def log_operation(
    action: str,
    module: str,
    target_type: Optional[str] = None,
    target_id: Optional[Any] = None,
    detail: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
) -> None:
    """
    记录一条操作日志。

    :param action: 操作动作，如 "登录"、"上传文件"、"执行检测"
    :param module: 所属模块，如 "auth"、"file"、"detection"
    :param target_type: 目标类型，如 "user"、"sample"、"report"
    :param target_id: 目标ID（会自动转为字符串）
    :param detail: 操作详情字典
    :param user_id: 指定用户ID；未指定时尝试从当前 JWT 用户获取
    """
    if user_id is None:
        try:
            current_user = get_current_user()
            if isinstance(current_user, User):
                user_id = current_user.id
        except Exception:
            pass

    ip_address = None
    user_agent = None
    if has_request_context():
        ip_address = request.remote_addr
        # 优先取反向代理后的真实 IP
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip() or ip_address
        user_agent = request.user_agent.string if request.user_agent else None

    log = OperationLog(
        user_id=user_id,
        action=action,
        module=module,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        detail=detail or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(log)
    db.session.commit()
