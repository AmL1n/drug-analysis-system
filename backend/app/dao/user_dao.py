# -*- coding: utf-8 -*-
"""
用户 DAO。
"""

from datetime import datetime
from typing import List, Optional

from app.model import Role, User, db


class UserDAO:
    """用户数据访问对象。"""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        return User.query.filter_by(username=username).first()

    @staticmethod
    def create(
        username: str,
        password_hash: str,
        real_name: Optional[str] = None,
        email: Optional[str] = None,
        operator_no: Optional[str] = None,
        roles: List[Role] = None,
    ) -> User:
        if not operator_no:
            operator_no = UserDAO._generate_operator_no()
        user = User(
            username=username,
            password_hash=password_hash,
            real_name=real_name,
            email=email,
            operator_no=operator_no,
        )
        if roles:
            user.roles.extend(roles)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def _generate_operator_no() -> str:
        """生成唯一个人工号，格式 OP-XXXXXX。"""
        count = User.query.count()
        while True:
            count += 1
            candidate = f"OP-{count:06d}"
            if User.query.filter_by(operator_no=candidate).first() is None:
                return candidate

    @staticmethod
    def update_last_login(user: User) -> None:
        user.last_login_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def list_users(page: int, page_size: int):
        return User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )


class RoleDAO:
    """角色数据访问对象。"""

    @staticmethod
    def get_by_name(name: str) -> Optional[Role]:
        return Role.query.filter_by(name=name).first()

    @staticmethod
    def get_by_names(names: List[str]) -> List[Role]:
        if not names:
            return []
        return Role.query.filter(Role.name.in_(names)).all()
