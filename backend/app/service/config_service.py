# -*- coding: utf-8 -*-
"""
系统配置服务模块。
"""

from typing import Optional

from app.dao.config_dao import SystemConfigDAO


CONFIG_KEY_CASCADE_THRESHOLDS = "cascade_thresholds"


def get_config_value(key: str) -> Optional[dict]:
    """按 key 获取系统配置值。"""
    return SystemConfigDAO.get_value(key)


def set_config_value(key: str, value: dict, description: Optional[str] = None) -> dict:
    """设置系统配置值。"""
    cfg = SystemConfigDAO.set_value(key, value, description)
    return {
        "key": cfg.config_key,
        "value": cfg.config_value,
        "description": cfg.description,
    }
