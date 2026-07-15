# -*- coding: utf-8 -*-
"""
三步级联检测服务。

针对企业版 HPLC-DAD 药物检测系统，实现：
1. 相对保留时间（RRT）初筛
2. 紫外最大吸收波长（lambda max）复筛
3. 峰面积常数比值最终定性
"""

from typing import Dict, List, Optional

from app.dao.library_dao import DrugAreaConstantDAO
from app.errors.exceptions import NotFoundException, ParamValidationException
from app.model import Drug, DrugCategory, ReferencePeak, db


DEFAULT_THRESHOLDS = {
    "rrtTolerance": 0.03,
    "lambdaTolerance": 2.0,
    "r1Tolerance": 0.1,
    "r2Tolerance": 0.1,
    "r3Tolerance": 0.1,
}

_REQUIRED_AREA_WAVELENGTHS = ["245", "250", "255", "260"]


def _to_float(value) -> Optional[float]:
    return float(value) if value is not None else None


def _get_main_peak(drug_id: int) -> Optional[ReferencePeak]:
    """获取药物的主峰（is_main_peak=True 或 peak_index=1）。"""
    peak = (
        ReferencePeak.query.filter_by(drug_id=drug_id, is_main_peak=True)
        .order_by(ReferencePeak.peak_index)
        .first()
    )
    if peak is None:
        peak = (
            ReferencePeak.query.filter_by(drug_id=drug_id)
            .order_by(ReferencePeak.peak_index)
            .first()
        )
    return peak


def _get_or_build_rrt(drug: Drug, reference_rt: float) -> Optional[float]:
    """获取药物的相对保留时间；若未记录则使用 retention_time / ts 计算。"""
    peak = _get_main_peak(drug.id)
    if peak is None:
        return None

    if peak.relative_retention_time is not None:
        return float(peak.relative_retention_time)

    if reference_rt and reference_rt > 0 and peak.retention_time is not None:
        return float(peak.retention_time) / reference_rt

    return None


def _validate_inputs(
    category_id: int,
    reference_drug_id: int,
    tx: float,
    lambda1: Optional[float],
    areas: Dict[str, float],
    thresholds: Dict[str, float],
) -> Dict[str, float]:
    """校验输入参数并返回补齐默认值的阈值字典。"""
    if category_id is None:
        raise ParamValidationException("categoryId 不能为空")
    if reference_drug_id is None:
        raise ParamValidationException("referenceDrugId 不能为空")

    category = db.session.get(DrugCategory, category_id)
    if category is None:
        raise NotFoundException("药物类别不存在")

    reference_drug = db.session.get(Drug, reference_drug_id)
    if reference_drug is None:
        raise NotFoundException("参照药物不存在")
    if reference_drug.category_id != category_id:
        raise ParamValidationException("参照药物不属于当前类别")
    if reference_drug.status != 1:
        raise ParamValidationException("参照药物已被禁用")

    if not isinstance(tx, (int, float)) or tx <= 0:
        raise ParamValidationException("tx 必须是大于 0 的数值")

    if lambda1 is not None and not isinstance(lambda1, (int, float)):
        raise ParamValidationException("lambda1 必须是数值或 null")

    if not isinstance(areas, dict):
        raise ParamValidationException("areas 必须是对象")

    for wl in _REQUIRED_AREA_WAVELENGTHS:
        value = areas.get(wl)
        if value is None:
            raise ParamValidationException(f"areas 缺少 {wl}nm 波长数据")
        if not isinstance(value, (int, float)) or value <= 0:
            raise ParamValidationException(f"areas[{wl}] 必须是大于 0 的数值")

    result_thresholds = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        for key in DEFAULT_THRESHOLDS:
            value = thresholds.get(key)
            if value is not None:
                if not isinstance(value, (int, float)) or value <= 0:
                    raise ParamValidationException(f"thresholds.{key} 必须是大于 0 的数值")
                result_thresholds[key] = float(value)

    return result_thresholds


def detect_by_cascade(
    category_id: int,
    reference_drug_id: int,
    tx: float,
    lambda1: Optional[float],
    lambda2: Optional[float],
    areas: Dict[str, float],
    thresholds: Dict[str, float],
    operator_id: Optional[int] = None,
    top_n: int = 10,
) -> dict:
    """
    执行三步级联检测。

    :param category_id: 药物类别 ID
    :param reference_drug_id: 参照药物 ID
    :param tx: 样本主峰保留时间
    :param lambda1: 样本最大吸收波长 1
    :param lambda2: 样本最大吸收波长 2（可为 None）
    :param areas: 各波长下峰面积，键为 "245"/"250"/"255"/"260"
    :param thresholds: 各级容差，缺失时使用默认值
    :param operator_id: 操作员 ID（预留）
    :param top_n: Step 3 返回前 N 个结果
    :return: 级联检测结果字典
    """
    effective_thresholds = _validate_inputs(
        category_id, reference_drug_id, tx, lambda1, areas, thresholds
    )

    reference_drug = db.session.get(Drug, reference_drug_id)
    reference_peak = _get_main_peak(reference_drug_id)
    if reference_peak is None or reference_peak.retention_time is None:
        raise ParamValidationException("参照药物缺少有效主峰保留时间")

    ts = float(reference_peak.retention_time)
    rrt_sample = tx / ts

    # Step 1: RRT 初筛
    rrt_tolerance = effective_thresholds["rrtTolerance"]
    step1_candidates: List[Dict] = []

    category_drugs = (
        Drug.query.filter_by(category_id=category_id, status=1)
        .order_by(Drug.name)
        .all()
    )

    for drug in category_drugs:
        rrt_db = _get_or_build_rrt(drug, ts)
        if rrt_db is None:
            continue

        delta = abs(rrt_db - rrt_sample)
        if delta <= rrt_tolerance:
            step1_candidates.append(
                {
                    "drug": drug,
                    "rrtDb": round(rrt_db, 6),
                    "delta": round(delta, 6),
                }
            )

    step1_candidates.sort(key=lambda x: x["delta"])

    # Step 2: lambda max 复筛
    lambda_tolerance = effective_thresholds["lambdaTolerance"]
    step2_candidates: List[Dict] = []

    if lambda1 is not None:
        for candidate in step1_candidates:
            drug = candidate["drug"]
            lambda_max_1 = _to_float(drug.lambda_max_1)

            if lambda_max_1 is None:
                continue

            if abs(lambda1 - lambda_max_1) > lambda_tolerance:
                continue

            # 若药物有 lambda_max_2 且样本提供了 lambda2，则也必须满足
            lambda_max_2 = _to_float(drug.lambda_max_2)
            if lambda_max_2 is not None and lambda2 is not None:
                if abs(lambda2 - lambda_max_2) > lambda_tolerance:
                    continue

            step2_candidates.append(candidate)
    else:
        # lambda1 缺失时无法执行波长筛选，全部通过
        step2_candidates = step1_candidates.copy()

    # Step 3: 峰面积常数最终定性
    r1 = areas["245"] / areas["250"]
    r2 = areas["255"] / areas["250"]
    r3 = areas["260"] / areas["250"]

    r1_tolerance = effective_thresholds["r1Tolerance"]
    r2_tolerance = effective_thresholds["r2Tolerance"]
    r3_tolerance = effective_thresholds["r3Tolerance"]

    step3_results: List[Dict] = []

    for candidate in step2_candidates:
        drug = candidate["drug"]
        constants = {
            float(c.wavelength): float(c.area)
            for c in DrugAreaConstantDAO.get_by_drug_id(drug.id)
        }

        if not all(wl in constants for wl in (245.0, 250.0, 255.0, 260.0)):
            continue

        r1_db = constants[245.0] / constants[250.0]
        r2_db = constants[255.0] / constants[250.0]
        r3_db = constants[260.0] / constants[250.0]

        delta_r1 = abs(r1 - r1_db)
        delta_r2 = abs(r2 - r2_db)
        delta_r3 = abs(r3 - r3_db)

        score1 = 1.0 - min(1.0, delta_r1 / r1_tolerance)
        score2 = 1.0 - min(1.0, delta_r2 / r2_tolerance)
        score3 = 1.0 - min(1.0, delta_r3 / r3_tolerance)
        final_score = (score1 + score2 + score3) / 3.0

        step3_results.append(
            {
                "drugId": drug.id,
                "drugName": drug.name,
                "r1Db": round(r1_db, 6),
                "r2Db": round(r2_db, 6),
                "r3Db": round(r3_db, 6),
                "deltaR1": round(delta_r1, 6),
                "deltaR2": round(delta_r2, 6),
                "deltaR3": round(delta_r3, 6),
                "score": round(final_score, 6),
            }
        )

    step3_results.sort(key=lambda x: x["score"], reverse=True)
    top_results = step3_results[:top_n]

    return {
        "referenceDrug": {
            "id": reference_drug.id,
            "name": reference_drug.name,
            "retentionTime": round(ts, 3),
        },
        "step1": {
            "rrtSample": round(rrt_sample, 6),
            "tolerance": rrt_tolerance,
            "candidateCount": len(step1_candidates),
            "candidates": [
                {
                    "drugId": c["drug"].id,
                    "drugName": c["drug"].name,
                    "rrtDb": c["rrtDb"],
                    "delta": c["delta"],
                }
                for c in step1_candidates
            ],
        },
        "step2": {
            "lambda1": lambda1,
            "lambda2": lambda2,
            "tolerance": lambda_tolerance,
            "candidateCount": len(step2_candidates),
            "candidates": [
                {
                    "drugId": c["drug"].id,
                    "drugName": c["drug"].name,
                    "rrtDb": c["rrtDb"],
                    "delta": c["delta"],
                }
                for c in step2_candidates
            ],
        },
        "step3": {
            "r1": round(r1, 6),
            "r2": round(r2, 6),
            "r3": round(r3, 6),
            "results": top_results,
        },
    }
