# -*- coding: utf-8 -*-
"""
API 蓝图注册中心。

所有业务接口按模块拆分为独立蓝图，在此统一注册到 /api 前缀下。
"""

from flask import Blueprint

api_bp = Blueprint("api", __name__)

# 导入各子模块蓝图
from .auth import auth_bp  # noqa: E402
from .common import common_bp  # noqa: E402
from .config import config_bp  # noqa: E402
from .detection import detection_bp  # noqa: E402
from .file import file_bp  # noqa: E402
from .library import library_bp  # noqa: E402
from .report import report_bp  # noqa: E402
from .sample import sample_bp  # noqa: E402

# 注册子蓝图到 /api
api_bp.register_blueprint(common_bp, url_prefix="")
api_bp.register_blueprint(auth_bp, url_prefix="")
api_bp.register_blueprint(config_bp, url_prefix="")
api_bp.register_blueprint(file_bp, url_prefix="")
api_bp.register_blueprint(sample_bp, url_prefix="")
api_bp.register_blueprint(detection_bp, url_prefix="")
api_bp.register_blueprint(library_bp, url_prefix="")
api_bp.register_blueprint(report_bp, url_prefix="")

# 后续逐步导入并注册：
# from .user import user_bp
# api_bp.register_blueprint(user_bp, url_prefix="")
# from .log import log_bp
# api_bp.register_blueprint(log_bp, url_prefix="")
