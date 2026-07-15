# -*- coding: utf-8 -*-
"""
文件上传相关 API。
"""

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_current_user, jwt_required
from werkzeug.utils import secure_filename

from app.errors.exceptions import ParamValidationException
from app.model import User
from app.service.file_service import save_uploaded_file
from app.service.log_service import log_operation
from app.utils.response import success

file_bp = Blueprint("file", __name__)


@file_bp.route("/files/upload", methods=["POST"])
@jwt_required()
def upload_file():
    """
    上传仪器数据文件。

    表单字段：file
    响应：文件记录信息
    """
    if "file" not in request.files:
        raise ParamValidationException("未找到文件字段")

    file_storage = request.files["file"]
    if not file_storage or not file_storage.filename:
        raise ParamValidationException("未选择文件")

    # 校验文件大小
    file_storage.seek(0, 2)  # 移动到文件末尾
    file_size = file_storage.tell()
    file_storage.seek(0)  # 重置

    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 50 * 1024 * 1024)
    if file_size > max_size:
        raise ParamValidationException(f"文件大小超过限制 {max_size // 1024 // 1024}MB")

    # 获取当前用户
    user = get_current_user()
    uploader_id = user.id if isinstance(user, User) else None

    file_record = save_uploaded_file(file_storage, uploader_id)

    log_operation(
        action="上传文件",
        module="file",
        target_type="uploaded_file",
        target_id=file_record.id,
        detail={
            "originalName": file_record.original_name,
            "fileSize": file_record.file_size,
        },
    )

    return success(
        data={
            "id": file_record.id,
            "originalName": file_record.original_name,
            "fileSize": file_record.file_size,
            "fileType": file_record.file_type,
            "createdAt": file_record.created_at.isoformat(),
        }
    )
