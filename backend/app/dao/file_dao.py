# -*- coding: utf-8 -*-
"""
上传文件 DAO。
"""

from typing import Optional

from app.model import UploadedFile, db


class UploadedFileDAO:
    """上传文件数据访问对象。"""

    @staticmethod
    def get_by_id(file_id: int) -> Optional[UploadedFile]:
        return db.session.get(UploadedFile, file_id)

    @staticmethod
    def create(
        original_name: str,
        storage_path: str,
        file_size: int,
        file_type: Optional[str],
        uploader_id: Optional[int],
    ) -> UploadedFile:
        file_record = UploadedFile(
            original_name=original_name,
            storage_path=storage_path,
            file_size=file_size,
            file_type=file_type,
            uploader_id=uploader_id,
        )
        db.session.add(file_record)
        db.session.commit()
        return file_record

    @staticmethod
    def list_by_uploader(uploader_id: int, page: int, page_size: int):
        return UploadedFile.query.filter_by(uploader_id=uploader_id).order_by(
            UploadedFile.created_at.desc()
        ).paginate(page=page, per_page=page_size, error_out=False)
