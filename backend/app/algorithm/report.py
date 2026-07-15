# -*- coding: utf-8 -*-
"""
检测报告生成模块。

将算法输出结果转换为结构化的报告数据，供后端 Service 层进一步渲染为
PDF / Word / Excel。

本模块不直接操作文件，只生成 Python 字典对象。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .types import DrugMatchResult, MatchedPeak


def build_peak_match_detail(match: MatchedPeak) -> Dict[str, Any]:
    """
    构建单个峰匹配的详细结果字典。

    :param match: 峰匹配结果
    :return: 结构化字典
    """
    sample_peak = match.sample_peak
    reference_peak = match.reference_peak

    return {
        "is_matched": match.is_matched,
        "sample_peak": {
            "index": sample_peak.index,
            "retention_time": float(sample_peak.retention_time),
            "area": float(sample_peak.area) if sample_peak.area else None,
            "height": float(sample_peak.height) if sample_peak.height else None,
            "area_ratio": float(sample_peak.area_ratio) if sample_peak.area_ratio is not None else None,
            "relative_retention_time": (
                float(sample_peak.relative_retention_time)
                if sample_peak.relative_retention_time is not None
                else None
            ),
        },
        "reference_peak": {
            "index": reference_peak.index if reference_peak else None,
            "retention_time": float(reference_peak.retention_time) if reference_peak else None,
            "area_ratio": float(reference_peak.area_ratio) if reference_peak and reference_peak.area_ratio is not None else None,
            "relative_retention_time": (
                float(reference_peak.relative_retention_time)
                if reference_peak and reference_peak.relative_retention_time is not None
                else None
            ),
        },
        "scores": {
            "rrt": float(match.rrt_score),
            "area_ratio": float(match.area_ratio_score),
            "uv": float(match.uv_score),
            "fusion": float(match.fusion_score),
        },
        "delta": {
            "rt": float(match.delta_rt),
            "area_ratio": float(match.delta_area_ratio),
        },
    }


def build_drug_match_summary(result: DrugMatchResult) -> Dict[str, Any]:
    """
    构建单个药物匹配结果的摘要。

    :param result: 药物匹配结果
    :return: 结构化字典
    """
    return {
        "drug_id": result.drug_id,
        "drug_name": result.drug_name,
        "total_score": float(result.total_score),
        "confidence": float(result.confidence),
        "matched_peak_count": result.matched_peak_count,
        "total_peak_count": result.total_peak_count,
        "is_detected": result.is_detected,
        "match_rate": (
            result.matched_peak_count / result.total_peak_count
            if result.total_peak_count > 0
            else 0.0
        ),
    }


def build_detection_report(
    sample_no: str,
    sample_name: Optional[str],
    results: List[DrugMatchResult],
    detected_only: bool = True,
    top_n: Optional[int] = None,
) -> Dict[str, Any]:
    """
    构建检测报告。

    :param sample_no: 样品编号
    :param sample_name: 样品名称
    :param results: 药物匹配结果列表
    :param detected_only: 是否只包含判定为检出的药物
    :param top_n: 只返回前 N 个结果，None 表示全部
    :return: 结构化报告字典
    """
    # 按综合评分降序排序
    sorted_results = sorted(
        results, key=lambda r: r.total_score, reverse=True
    )

    if detected_only:
        sorted_results = [r for r in sorted_results if r.is_detected]

    if top_n is not None:
        sorted_results = sorted_results[:top_n]

    drug_summaries = [build_drug_match_summary(r) for r in sorted_results]
    detailed_results = []
    for result in sorted_results:
        detailed_results.append(
            {
                "drug_id": result.drug_id,
                "drug_name": result.drug_name,
                "summary": build_drug_match_summary(result),
                "peak_matches": [
                    build_peak_match_detail(m) for m in result.peak_matches
                ],
                "algorithm_details": result.algorithm_details,
            }
        )

    return {
        "report_type": "detection",
        "sample_no": sample_no,
        "sample_name": sample_name,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_candidates": len(results),
            "detected_count": len([r for r in results if r.is_detected]),
            "top_drugs": drug_summaries,
        },
        "details": detailed_results,
    }


def build_batch_report(
    task_no: str,
    sample_reports: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    构建批量检测汇总报告。

    :param task_no: 任务编号
    :param sample_reports: 各样本检测报告列表
    :return: 结构化批量报告字典
    """
    total_detected = sum(
        report["summary"]["detected_count"] for report in sample_reports
    )

    return {
        "report_type": "batch",
        "task_no": task_no,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_samples": len(sample_reports),
            "total_detected": total_detected,
        },
        "samples": sample_reports,
    }
