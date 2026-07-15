# -*- coding: utf-8 -*-
"""
系统配置与操作日志模型。
"""

from datetime import datetime

from . import db


class SystemConfig(db.Model):
    """系统配置表"""

    __tablename__ = "system_configs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    config_key = db.Column(
        db.String(100), unique=True, nullable=False, comment="配置键"
    )
    config_value = db.Column(db.JSON, nullable=False, comment="配置值")
    description = db.Column(db.Text, default=None, comment="配置说明")
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<SystemConfig {self.config_key}>"

    @classmethod
    def get_value(cls, key: str, default=None):
        """按 key 获取配置值。"""
        cfg = cls.query.filter_by(config_key=key).first()
        if cfg is None:
            return default
        return cfg.config_value


class OperationLog(db.Model):
    """操作日志表"""

    __tablename__ = "operation_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        comment="用户ID",
    )
    action = db.Column(db.String(100), nullable=False, comment="操作动作")
    module = db.Column(db.String(50), default=None, comment="所属模块")
    target_type = db.Column(db.String(50), default=None, comment="目标类型")
    target_id = db.Column(db.String(100), default=None, comment="目标ID")
    detail = db.Column(db.JSON, default=None, comment="操作详情")
    ip_address = db.Column(db.String(50), default=None, comment="IP地址")
    user_agent = db.Column(db.String(255), default=None, comment="浏览器UA")
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    user = db.relationship("User", backref="operation_logs")

    __table_args__ = (
        db.Index("idx_operation_logs_user_id", "user_id"),
        db.Index("idx_operation_logs_action", "action"),
        db.Index("idx_operation_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<OperationLog {self.action}>"
