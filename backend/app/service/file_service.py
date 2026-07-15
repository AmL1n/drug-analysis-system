# -*- coding: utf-8 -*-
"""
文件服务模块。

处理文件上传、保存、解析等逻辑。
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import current_app
from werkzeug.utils import secure_filename

from app.dao.file_dao import UploadedFileDAO
from app.errors.exceptions import ParamValidationException
from app.model import UploadedFile
from app.parser.factory import ParserFactory
from app.algorithm.types import Chromatogram


ALLOWED_EXTENSIONS = {"txt", "csv", "xlsx", "xls", "json"}


def _allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许。"""
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext in ALLOWED_EXTENSIONS


def _generate_storage_name(original_name: str) -> str:
    """生成唯一存储文件名。"""
    ext = Path(original_name).suffix
    unique_id = uuid.uuid4().hex[:16]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{unique_id}{ext}"


def save_uploaded_file(
    file_storage, uploader_id: Optional[int]
) -> UploadedFile:
    """
    保存上传文件到服务器并记录到数据库。

    :param file_storage: Flask FileStorage 对象
    :param uploader_id: 上传人ID
    :return: 文件记录
    """
    if not file_storage or not file_storage.filename:
        raise ParamValidationException("未选择文件")

    original_name = secure_filename(file_storage.filename)
    if not _allowed_file(original_name):
        raise ParamValidationException(
            f"不支持的文件格式，仅支持：{', '.join(ALLOWED_EXTENSIONS)}"
        )

    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    storage_name = _generate_storage_name(original_name)
    storage_path = os.path.join(upload_folder, storage_name)

    # 保存文件到磁盘
    file_storage.save(storage_path)

    # 记录到数据库
    file_size = os.path.getsize(storage_path)
    file_type = file_storage.content_type

    return UploadedFileDAO.create(
        original_name=original_name,
        storage_path=storage_path,
        file_size=file_size,
        file_type=file_type,
        uploader_id=uploader_id,
    )


def parse_file_to_chromatogram(file_record: UploadedFile) -> Chromatogram:
    """
    解析上传文件为 Chromatogram。

    若文件为标准导入格式（峰列表/光谱表），则抛出业务异常提示用户。

    :param file_record: 上传文件记录
    :return: 色谱图对象
    """
    result = ParserFactory.parse(file_record.storage_path)
    if not isinstance(result, Chromatogram):
        from app.errors.exceptions import ParamValidationException

        raise ParamValidationException(
            "该文件为标准导入格式，请在样本导入功能中使用；检测分析需上传完整色谱图（CSV/TXT/Excel）"
        )
    return result
