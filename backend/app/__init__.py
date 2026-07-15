# -*- coding: utf-8 -*-
"""
Flask 应用工厂模块。

使用应用工厂模式创建 Flask 实例，便于测试和多环境部署。
"""

import os

from flask import Flask, jsonify
from sqlalchemy import inspect, text
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import config_map
from .model import db
from .utils.logger import configure_logging

# 初始化扩展（不绑定具体 app）
jwt = JWTManager()


def create_app(config_name: str = "development") -> Flask:
    """
    创建 Flask 应用实例。

    :param config_name: 配置环境名称，可选 development/testing/production
    :return: Flask 应用实例
    """
    app = Flask(__name__)

    # 加载配置
    config_class = config_map.get(config_name, config_map["development"])
    app.config.from_object(config_class)

    # 生产环境安全基线检查
    if config_name == "production":
        _check_production_secrets(app)

    # 确保上传目录和日志目录存在
    _ensure_directories(app)

    # 配置日志
    configure_logging(app)

    # 注册扩展
    db.init_app(app)
    jwt.init_app(app)

    # 配置 JWT 用户加载
    _setup_jwt_loaders(app)

    # 跨域支持（开发环境开启，生产环境按需要限制来源）
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    if cors_origins == ["*"] or cors_origins == "*":
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    else:
        CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # 注册蓝图
    _register_blueprints(app)

    # 注册错误处理
    _register_error_handlers(app)

    # 根路径提示，方便浏览器访问时确认服务已启动
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "drug-check-backend",
            "version": "0.1.0",
            "api_base": "/api",
            "health": "/api/common/health",
        })

    # 创建所有数据库表（仅开发/测试环境方便使用；生产环境建议用 Flask-Migrate）
    with app.app_context():
        db.create_all()
        _migrate_operator_no()
        _init_seed_data()

    return app


def _check_production_secrets(app: Flask) -> None:
    """生产环境强制检查密钥强度。"""
    jwt_key = app.config.get("JWT_SECRET_KEY", "")
    secret_key = app.config.get("SECRET_KEY", "")
    if not jwt_key or len(jwt_key) < 32:
        raise RuntimeError(
            "生产环境必须设置至少 32 字节的 JWT_SECRET_KEY 环境变量"
        )
    if not secret_key or len(secret_key) < 16:
        raise RuntimeError(
            "生产环境必须设置至少 16 字节的 SECRET_KEY 环境变量"
        )


def _ensure_directories(app: Flask) -> None:
    """确保上传目录、日志目录与 SQLite 数据目录存在。"""
    import sqlite3

    print(f"[DEBUG] cwd={os.getcwd()}, FLASK_ENV={app.config.get('ENV')}")
    print(f"[DEBUG] SQLALCHEMY_DATABASE_URI={app.config.get('SQLALCHEMY_DATABASE_URI')}")

    upload_folder = app.config.get("UPLOAD_FOLDER")
    log_dir = app.config.get("LOG_DIR")
    for directory in (upload_folder, log_dir):
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    # 若为 SQLite，确保数据库文件所在目录存在（容器/Render 无挂载时也能自创建）
    database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if database_uri and database_uri.startswith("sqlite:///"):
        db_path = database_uri[len("sqlite:///"):]
        if db_path and not db_path.startswith(":"):
            db_dir = os.path.dirname(os.path.abspath(db_path))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            print(f"[DEBUG] db_dir={db_dir}, exists={os.path.exists(db_dir)}, writable={os.access(db_dir, os.W_OK)}")
            # 直接用 sqlite3 测试能否创建/打开文件
            try:
                conn = sqlite3.connect(db_path)
                conn.execute("SELECT 1")
                conn.close()
                print(f"[DEBUG] sqlite3 test connect OK: {db_path}")
            except Exception as e:
                print(f"[DEBUG] sqlite3 test connect FAILED: {db_path}, error={e}")


def _setup_jwt_loaders(app: Flask) -> None:
    """配置 JWT 用户加载与错误处理。"""
    from app.model import User
    from app.utils.response import ResponseCode, build_response

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """根据 JWT identity 加载用户对象。"""
        identity = jwt_data["sub"]
        try:
            user_id = int(identity)
            return User.query.get(user_id)
        except (ValueError, TypeError):
            return None

    @jwt.unauthorized_loader
    def unauthorized_callback(reason: str):
        """请求未携带 Token。"""
        return build_response(
            msg=reason or "缺少认证信息",
            code=ResponseCode.UNAUTHORIZED,
            status_code=401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(reason: str):
        """Token 格式错误或签名验证失败。"""
        return build_response(
            msg="登录已过期或Token无效，请重新登录",
            code=ResponseCode.UNAUTHORIZED,
            status_code=401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        """Token 已过期。"""
        return build_response(
            msg="登录已过期，请重新登录",
            code=ResponseCode.UNAUTHORIZED,
            status_code=401,
        )

    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(_jwt_header, _jwt_payload):
        """Token 校验失败。"""
        return build_response(
            msg="登录已过期或Token无效，请重新登录",
            code=ResponseCode.UNAUTHORIZED,
            status_code=401,
        )


def _init_seed_data() -> None:
    """
    初始化种子数据。

    仅在角色表为空时执行，避免重复插入。
    """
    from app.model import DrugCategory, Role, User, db
    from app.utils.security import hash_password

    # 初始化角色
    if not Role.query.first():
        admin_role = Role(name="admin", description="系统管理员")
        operator_role = Role(name="operator", description="操作员")
        db.session.add_all([admin_role, operator_role])
        db.session.commit()

    # 初始化管理员用户
    if not User.query.filter_by(username="admin").first():
        admin_role = Role.query.filter_by(name="admin").first()
        operator_role = Role.query.filter_by(name="operator").first()

        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            real_name="系统管理员",
            email="admin@example.com",
            operator_no="OP-000001",
            is_active=True,
        )
        operator_user = User(
            username="operator",
            password_hash=hash_password("admin123"),
            real_name="操作员",
            email="operator@example.com",
            operator_no="OP-000002",
            is_active=True,
        )

        if admin_role:
            admin_user.roles.append(admin_role)
        if operator_role:
            operator_user.roles.append(operator_role)

        db.session.add_all([admin_user, operator_user])
        db.session.commit()

    # 初始化药物类别（与《数据库六种表结构》对齐）
    if not DrugCategory.query.first():
        categories = [
            DrugCategory(name="安神镇定类", code=1, description="镇静催眠类药物", wavelengths=[245, 250, 255, 260], sort_order=1),
            DrugCategory(name="减肥类", code=2, description="减肥类药物", wavelengths=[245, 248, 250, 254], sort_order=2),
            DrugCategory(name="降糖类", code=3, description="降糖类药物", wavelengths=[], sort_order=3),
            DrugCategory(name="降压类", code=4, description="降压类药物", wavelengths=[], sort_order=4),
            DrugCategory(name="降脂类", code=5, description="降脂类药物", wavelengths=[], sort_order=5),
            DrugCategory(name="抗感冒类", code=6, description="抗感冒类药物", wavelengths=[], sort_order=6),
            DrugCategory(name="消肿止痛抗风湿类", code=7, description="消肿止痛抗风湿类药物", wavelengths=[], sort_order=7),
            DrugCategory(name="止咳平喘类", code=8, description="止咳平喘类药物", wavelengths=[], sort_order=8),
        ]
        db.session.add_all(categories)
        db.session.commit()


def _migrate_operator_no() -> None:
    """
    兼容性迁移：为已存在的用户表添加 operator_no 列并补填数据。

    由于本地开发使用 SQLite 且未启用 Flask-Migrate，在模型新增字段后需要
    通过此函数自动 ALTER TABLE，避免删除现有数据。
    """
    from app.model import User

    try:
        inspector = inspect(db.engine)
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "operator_no" not in columns:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN operator_no VARCHAR(50)")
            )
            db.session.commit()

        # 为所有没有工号的已有用户补填唯一工号
        users_without_no = User.query.filter(
            (User.operator_no == None) | (User.operator_no == "")
        ).all()
        if users_without_no:
            existing = {
                u.operator_no for u in User.query.filter(User.operator_no != None).all()
            }
            counter = len(existing)
            for user in users_without_no:
                counter += 1
                while f"OP-{counter:06d}" in existing:
                    counter += 1
                user.operator_no = f"OP-{counter:06d}"
                existing.add(user.operator_no)
            db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def _register_blueprints(app: Flask) -> None:
    """注册业务蓝图。"""
    from .api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")


def _register_error_handlers(app: Flask) -> None:
    """注册全局错误处理器。"""
    from .errors.handlers import register_handlers

    register_handlers(app)
