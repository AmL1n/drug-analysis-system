# -*- coding: utf-8 -*-
"""
Flask 应用启动入口。

使用方式：
    python run.py
    FLASK_ENV=development python run.py
"""

import os

from app import create_app

# 默认使用 development 配置，可通过环境变量覆盖
config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    debug = app.config.get("DEBUG", True)
    app.run(host=host, port=port, debug=debug)
