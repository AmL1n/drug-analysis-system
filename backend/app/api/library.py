# -*- coding: utf-8 -*-
"""
对照品库相关 API。
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.errors.exceptions import ParamValidationException
from app.service.library_import_service import import_library_from_json
from app.service.library_service import (
    delete_drug,
    delete_drugs,
    get_category_reference_drug,
    get_drug_detail,
    list_categories,
    list_drugs,
    list_peaks,
    list_reference_drugs,
    list_spectra,
    set_category_reference_drug,
    update_drug_rrt_stats,
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


@library_bp.route("/library/categories/<int:category_id>/reference-drugs", methods=["GET"])
@jwt_required()
def list_reference_drugs_view(category_id: int):
    """获取类别下可作为参照物的药物列表。"""
    drugs = list_reference_drugs(category_id)
    return success(data=drugs, msg="ok")


@library_bp.route("/library/categories/<int:category_id>/reference-drug", methods=["GET"])
@jwt_required()
def get_category_reference_drug_view(category_id: int):
    """获取类别当前默认参照药物。"""
    drug = get_category_reference_drug(category_id)
    return success(data=drug, msg="ok")


@library_bp.route("/library/categories/<int:category_id>/reference-drug", methods=["PUT"])
@jwt_required()
def set_category_reference_drug_view(category_id: int):
    """设置类别默认参照药物。"""
    data = request.get_json(silent=True) or {}
    reference_drug_id = data.get("referenceDrugId")
    if reference_drug_id is None:
        raise ParamValidationException("referenceDrugId 不能为空")
    try:
        reference_drug_id = int(reference_drug_id)
    except (ValueError, TypeError):
        raise ParamValidationException("referenceDrugId 必须为整数")

    result = set_category_reference_drug(category_id, reference_drug_id)
    log_operation(
        action="设置类别参照药物",
        module="library",
        target_type="drug_category",
        target_id=category_id,
        detail=result,
    )
    return success(data=result, msg="ok")


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


@library_bp.route("/library/drugs/<int:drug_id>/train-rrt", methods=["POST"])
@jwt_required()
def train_drug_rrt_view(drug_id: int):
    """
    使用新的 RRT 观测值增量训练药物的 RRT 高斯模型。

    请求体：{"rrt": float}
    """
    data = request.get_json(silent=True) or {}
    rrt = data.get("rrt")
    if rrt is None:
        raise ParamValidationException("rrt 不能为空")
    try:
        rrt = float(rrt)
    except (ValueError, TypeError):
        raise ParamValidationException("rrt 必须为数值")

    stats = update_drug_rrt_stats(drug_id, rrt)
    log_operation(
        action="训练 RRT 模型",
        module="library",
        target_type="drug",
        target_id=drug_id,
        detail={"drugId": drug_id, "rrt": rrt, "stats": stats},
    )
    return success(data=stats, msg="RRT 模型训练成功")


@library_bp.route("/library/drugs/<int:drug_id>", methods=["DELETE"])
@jwt_required()
def delete_drug_view(drug_id: int):
    """删除单个药物。"""
    delete_drug(drug_id)
    log_operation(
        action="删除药物",
        module="library",
        target_type="drug",
        target_id=drug_id,
        detail={"drugId": drug_id},
    )
    return success(msg="删除成功")


@library_bp.route("/library/drugs", methods=["DELETE"])
@jwt_required()
def batch_delete_drugs_view():
    """批量删除药物。

    请求体：{"ids": [1, 2, 3]}
    """
    data = request.get_json(silent=True) or {}
    drug_ids = data.get("ids")
    if not isinstance(drug_ids, list) or not drug_ids:
        raise ParamValidationException("ids 必须是非空数组")

    try:
        drug_ids = [int(did) for did in drug_ids]
    except (ValueError, TypeError):
        raise ParamValidationException("ids 数组元素必须为整数")

    count = delete_drugs(drug_ids)
    log_operation(
        action="批量删除药物",
        module="library",
        target_type="drug",
        detail={"drugIds": drug_ids, "count": count},
    )
    return success(data={"deleted": count}, msg=f"成功删除 {count} 条药物")
