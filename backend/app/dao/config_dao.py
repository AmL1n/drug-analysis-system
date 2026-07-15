# -*- coding: utf-8 -*-
"""
系统配置数据访问对象。
"""

from typing import Optional

from app.model import SystemConfig


class SystemConfigDAO:
    """system_configs 表数据访问。"""

    @staticmethod
    def get_by_key(key: str) -> Optional[SystemConfig]:
        return SystemConfig.query.filter_by(config_key=key).first()

    @staticmethod
    def get_value(key: str, default=None):
        cfg = SystemConfigDAO.get_by_key(key)
        if cfg is None:
            return default
        return cfg.config_value

    @staticmethod
    def set_value(key: str, value, description: Optional[str] = None) -> SystemConfig:
        cfg = SystemConfigDAO.get_by_key(key)
        if cfg is None:
            cfg = SystemConfig(config_key=key, config_value=value, description=description)
            from app.model import db

            db.session.add(cfg)
        else:
            cfg.config_value = value
            if description is not None:
                cfg.description = description
        from app.model import db

        db.session.commit()
        return cfg
