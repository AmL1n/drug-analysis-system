# -*- coding: utf-8 -*-
"""
用户与权限相关模型。
"""

from datetime import datetime

from . import db


class User(db.Model):
    """用户表"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    username = db.Column(
        db.String(50), unique=True, nullable=False, comment="登录用户名"
    )
    password_hash = db.Column(
        db.String(255), nullable=False, comment="bcrypt 加密后的密码"
    )
    real_name = db.Column(db.String(50), default=None, comment="真实姓名")
    email = db.Column(db.String(100), default=None, comment="邮箱")
    operator_no = db.Column(
        db.String(50), unique=True, nullable=True, comment="个人工号/操作员编号"
    )
    is_active = db.Column(db.Boolean, default=True, comment="是否启用")
    last_login_at = db.Column(db.DateTime, default=None, comment="最后登录时间")
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    # 关系
    roles = db.relationship(
        "Role", secondary="user_roles", back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def has_role(self, role_name: str) -> bool:
        """判断用户是否拥有指定角色。"""
        return any(role.name == role_name for role in self.roles)


class Role(db.Model):
    """角色表"""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    name = db.Column(
        db.String(50), unique=True, nullable=False, comment="角色名称"
    )
    description = db.Column(db.String(255), default=None, comment="角色描述")
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    users = db.relationship(
        "User", secondary="user_roles", back_populates="roles"
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class UserRole(db.Model):
    """用户角色关联表"""

    __tablename__ = "user_roles"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID",
    )
    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="角色ID",
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    def __repr__(self) -> str:
        return f"<UserRole user={self.user_id} role={self.role_id}>"
