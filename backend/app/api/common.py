# -*- coding: utf-8 -*-
"""
公共接口蓝图。

提供健康检查、系统时间等基础接口。
"""

from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.model import Drug, DetectionResult, OperationLog, Sample, User
from app.utils.pagination import get_pagination_params
from app.utils.response import page, success

common_bp = Blueprint("common", __name__)


@common_bp.route("/common/stats", methods=["GET"])
def get_stats():
    """
    仪表盘统计数据接口。

    返回待检测样本数、已完成检测数、启用对照品药物数以及今日检测报告数。
    """
    pending = Sample.query.filter(Sample.status.in_(["pending", "running"])).count()
    completed = Sample.query.filter(Sample.status == "success").count()
    drugs = Drug.query.filter(Drug.status == 1).count()

    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    reports = DetectionResult.query.filter(
        DetectionResult.created_at >= start_of_day
    ).count()

    return success(
        data={
            "pending": pending,
            "completed": completed,
            "drugs": drugs,
            "reports": reports,
        }
    )


@common_bp.route("/common/logs", methods=["GET"])
@jwt_required()
def list_logs_view():
    """
    操作日志列表。

    支持分页，返回操作人、操作、模块、目标、详情、IP、UA、时间。
    """
    page_no, page_size = get_pagination_params()

    pagination = (
        OperationLog.query.order_by(OperationLog.created_at.desc())
        .paginate(page=page_no, per_page=page_size, error_out=False)
    )

    items = []
    for log in pagination.items:
        user = log.user
        items.append(
            {
                "id": log.id,
                "operator": user.real_name or user.username or "未知用户" if user else "未知用户",
                "operatorNo": user.operator_no if user else None,
                "action": log.action,
                "module": log.module,
                "targetType": log.target_type,
                "targetId": log.target_id,
                "detail": log.detail or {},
                "ipAddress": log.ip_address,
                "userAgent": log.user_agent,
                "createdAt": log.created_at.isoformat(),
            }
        )

    return page(items, pagination.total, page_no, page_size)


@common_bp.route("/common/health", methods=["GET"])
def health_check():
    """
    健康检查接口。

    返回服务器当前状态和时间戳，用于前端判断后端是否可用。
    """
    return success(
        data={
            "status": "ok",
            "service": "drug-check-backend",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@common_bp.route("/ping", methods=["GET"])
def ping():
    """
    简单连通性测试接口。
    """
    return success(data="pong")
