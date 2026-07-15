# -*- coding: utf-8 -*-
"""
应用配置模块。

支持 development / testing / production 三种环境。
"""

import os
from datetime import timedelta


class BaseConfig:
    """基础配置，所有环境共用。"""

    # Flask 基础
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "dev-secret-key-change-in-production-immediately"
    )

    # JWT 配置（生产环境必须通过环境变量设置至少 32 字节密钥）
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "jwt-dev-secret-key-must-be-at-least-32-bytes-long"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "120"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # 数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # 文件上传配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "uploads")
    )
    ALLOWED_EXTENSIONS = {"txt", "csv", "xlsx", "xls"}

    # 日志配置
    LOG_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "logs")
    )
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # 分页默认值
    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(BaseConfig):
    """开发环境配置。"""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/drug_check?charset=utf8mb4",
    )
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"


class TestingConfig(BaseConfig):
    """测试环境配置。"""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/drug_check_test?charset=utf8mb4",
    )
    WTF_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


class ProductionConfig(BaseConfig):
    """生产环境配置。"""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@localhost:3306/drug_check?charset=utf8mb4",
    )
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")

    # CORS 来源限制（默认只允许前端开发域名，生产环境请通过环境变量配置）
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    def __init__(self):
        # 生产环境强制从环境变量读取密钥，避免使用默认弱密钥
        jwt_key = os.getenv("JWT_SECRET_KEY")
        secret_key = os.getenv("SECRET_KEY")
        if not jwt_key or len(jwt_key) < 32:
            raise ValueError(
                "生产环境必须设置至少 32 字节的 JWT_SECRET_KEY 环境变量"
            )
        if not secret_key or len(secret_key) < 16:
            raise ValueError(
                "生产环境必须设置至少 16 字节的 SECRET_KEY 环境变量"
            )


# 配置映射，供应用工厂使用
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
