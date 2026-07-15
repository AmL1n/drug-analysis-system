# -*- coding: utf-8 -*-
"""
安全工具模块。

提供密码哈希、校验和 JWT Token 生成/解析辅助函数。
"""

from datetime import datetime, timedelta
from typing import Optional

from flask_jwt_extended import create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """使用 Werkzeug 生成密码哈希。"""
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码与哈希是否匹配。"""
    return check_password_hash(password_hash, password)


def create_jwt_token(identity: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌。

    :param identity: 用户标识（通常为用户名或用户ID）
    :param expires_delta: 过期时间
    :return: JWT 字符串
    """
    return create_access_token(identity=identity, expires_delta=expires_delta)


def get_current_user_identity() -> Optional[str]:
    """获取当前 JWT 中的用户标识。"""
    try:
        return get_jwt_identity()
    except Exception:
        return None


def generate_sample_no() -> str:
    """
    生成样品编号。

    格式：S + 年月日时分秒 + 3位随机数
    """
    import random

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"S{now}{rand}"


def generate_task_no() -> str:
    """
    生成任务编号。

    格式：T + 年月日时分秒 + 3位随机数
    """
    import random

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"T{now}{rand}"
