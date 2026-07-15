# -*- coding: utf-8 -*-
"""
pytest 测试配置。

提供测试用的 Flask app 和数据库会话夹具。
"""

import os
import tempfile

import pytest

# 先注入测试数据库地址，再导入应用，确保 config.py 读取到 SQLite 配置
os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.model import db


@pytest.fixture(scope="session")
def app():
    """创建测试用 Flask 应用实例。"""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    os.environ["TEST_DATABASE_URL"] = f"sqlite:///{db_path}"
    test_app = create_app("testing")
    test_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    test_app.config["TESTING"] = True

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()

    os.unlink(db_path)


@pytest.fixture
def client(app):
    """创建测试客户端。"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建 CLI 测试 runner。"""
    return app.test_cli_runner()
