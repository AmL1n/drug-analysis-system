# -*- coding: utf-8 -*-
"""
SQLAlchemy 模型初始化模块。

所有数据库模型通过 db 实例注册，避免循环引用。
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# 命名约定：便于后续迁移工具（如 Alembic）使用
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# 创建 SQLAlchemy 实例，命名约定保证外键名稳定
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))

# 导入所有模型，确保在 create_all 时注册
# 注意：模型文件内部只依赖 db.Model，不依赖 Flask app
from .user import User, Role, UserRole  # noqa: E402,F401
from .library import (  # noqa: E402,F401
    DrugCategory,
    Drug,
    DrugAreaConstant,
    ReferencePeak,
    ReferenceSpectrum,
    ModelParam,
)
from .sample import UploadedFile, Sample, SamplePeak, SampleSpectrum  # noqa: E402,F401
from .detection import (  # noqa: E402,F401
    DetectionTask,
    TaskSample,
    DetectionResult,
    DetectionPeakMatch,
    ChromatogramComparison,
)
from .system import SystemConfig, OperationLog  # noqa: E402,F401
