# -*- coding: utf-8 -*-
"""
对照品库相关 API。
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.errors.exceptions import ParamValidationException
from app.service.library_import_service import import_library_from_json
from app.service.library_service import (
    get_drug_detail,
    list_categories,
    list_drugs,
    list_peaks,
    list_spectra,
)
from app.service.log_service import log_operation
from app.utils.pagination import get_pagination_params
from app.utils.response import page, success

library_bp = Blueprint("library", __name__)


@library_bp.route("/library/categories", methods=["GET"])
@jwt_required()
def list_categories_view():
    """获取药物类别列表。"""
    categories = list_categories()
    return success(data=categories)


@library_bp.route("/library/drugs", methods=["GET"])
@jwt_required()
def list_drugs_view():
    """分页获取药物列表。"""
    page_no, page_size = get_pagination_params()
    category_id = request.args.get("categoryId", type=int)
    keyword = request.args.get("keyword")

    result = list_drugs(category_id, keyword, page_no, page_size)
    return page(
        result["items"], result["total"], result["page"], result["page_size"]
    )


@library_bp.route("/library/drugs/<int:drug_id>", methods=["GET"])
@jwt_required()
def get_drug_view(drug_id: int):
    """获取药物详情。"""
    detail = get_drug_detail(drug_id)
    return success(data=detail)


@library_bp.route("/library/peaks", methods=["GET"])
@jwt_required()
def list_peaks_view():
    """分页获取参考峰列表。"""
    page_no, page_size = get_pagination_params()
    drug_id = request.args.get("drugId", type=int)
    category_id = request.args.get("categoryId", type=int)

    result = list_peaks(drug_id, category_id, page_no, page_size)
    return page(
        result["items"], result["total"], result["page"], result["page_size"]
    )


@library_bp.route("/library/spectra", methods=["GET"])
@jwt_required()
def list_spectra_view():
    """分页获取参考光谱列表。"""
    page_no, page_size = get_pagination_params()
    drug_id = request.args.get("drugId", type=int)
    category_id = request.args.get("categoryId", type=int)

    result = list_spectra(drug_id, category_id, page_no, page_size)
    return page(
        result["items"], result["total"], result["page"], result["page_size"]
    )


@library_bp.route("/library/import", methods=["POST"])
@jwt_required()
def import_library_view():
    """
    导入外部药物标准库 JSON 文件到对照品库。

    请求：multipart/form-data
        file: JSON 文件（必填）
        categoryId: 已有类别 ID（可选）
    """
    if "file" not in request.files:
        raise ParamValidationException("缺少文件字段 file")

    file_storage = request.files["file"]
    category_id_raw = request.form.get("categoryId") or None

    category_id = None
    if category_id_raw is not None:
        try:
            category_id = int(category_id_raw)
        except (ValueError, TypeError):
            raise ParamValidationException("categoryId 必须为整数")

    summary = import_library_from_json(file_storage, category_id=category_id)

    log_operation(
        action="导入药物列表",
        module="library",
        target_type="library_import",
        detail={
            "created": summary["created"],
            "updated": summary["updated"],
            "failed": summary["failed"],
            "categoryId": category_id,
        },
    )

    return success(data=summary)
