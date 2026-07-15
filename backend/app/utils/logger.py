# -*- coding: utf-8 -*-
"""
日志配置模块。

为 Flask 应用配置控制台日志和按大小切分的文件日志。
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from flask import Flask


def configure_logging(app: Flask, log_dir: Optional[str] = None) -> None:
    """
    配置 Flask 应用日志。

    :param app: Flask 应用实例
    :param log_dir: 日志目录，默认使用 app.config['LOG_DIR']
    """
    if log_dir is None:
        log_dir = app.config.get("LOG_DIR", os.path.join(os.getcwd(), "logs"))

    os.makedirs(log_dir, exist_ok=True)

    log_level = app.config.get("LOG_LEVEL", "INFO")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 清除默认 handler，避免重复输出
    app.logger.handlers.clear()
    app.logger.setLevel(log_level)

    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    # 文件 handler（按文件大小切分，单个 10MB，保留 10 个备份）
    log_file = os.path.join(log_dir, "drug_check.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    app.logger.info("日志配置完成，日志目录: %s", log_dir)
