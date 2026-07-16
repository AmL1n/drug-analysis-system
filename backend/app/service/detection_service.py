# -*- coding: utf-8 -*-
"""
检测服务模块。

实现单样本检测与多药物批量匹配的核心流程。
"""

from datetime import datetime
from typing import List, Optional

from app.algorithm.area_ratio import match_area_ratios
from app.algorithm.bayes import bayes_from_matches
from app.algorithm.fusion import calculate_confidence, weighted_fusion
from app.algorithm.report import build_detection_report
from app.algorithm.retention import (
    match_peaks_by_retention_time,
    match_peaks_by_retention_time_with_stats,
)
from app.service.library_service import get_drug_rrt_stats
from app.algorithm.types import DrugMatchResult, MatchedPeak, Peak, Spectrum
from app.algorithm.uv_match import calculate_uv_match_score
from app.dao.detection_dao import DetectionResultDAO, DetectionTaskDAO, TaskSampleDAO
from app.dao.library_dao import DrugDAO, ReferencePeakDAO, ReferenceSpectrumDAO
from app.dao.sample_dao import SampleDAO, SamplePeakDAO
from app.errors.exceptions import NotFoundException, ParamValidationException
from app.model import DetectionResult, DetectionTask, ReferencePeak, Sample, SamplePeak
from app.utils.security import generate_task_no


DEFAULT_TOP_N = 10
DETECTION_THRESHOLD = 0.7


def detect_single_sample(
    sample_id: int,
    model_type: str = "fusion",
    top_n: int = DEFAULT_TOP_N,
    confidence_threshold: float = DETECTION_THRESHOLD,
    rrt_tolerance: float = 0.02,
    uv_distance_threshold: float = 0.15,
    area_ratio_method: str = "relative_error",
) -> dict:
    """
    对单个样本执行多药物检测。

    :param sample_id: 样本ID
    :param model_type: 模型类型
    :param top_n: 返回前 N 个候选
    :param confidence_threshold: 检出判定阈值
    :param rrt_tolerance: 保留时间匹配容差
    :param uv_distance_threshold: UV 光谱距离阈值
    :param area_ratio_method: 峰面积比相似度计算方法
    :return: 检测报告字典
    """
    sample = SampleDAO.get_by_id(sample_id)
    if sample is None:
        raise NotFoundException("样本不存在")

    SampleDAO.update_status(sample, "running")

    try:
        # 清除旧结果
        DetectionResultDAO.delete_by_sample(sample_id)

        # 获取样本峰并转换为算法对象
        sample_peaks = [_to_peak(p) for p in SamplePeakDAO.get_by_sample_id(sample_id)]
        if not sample_peaks:
            raise ParamValidationException("样本未识别到有效峰")

        # 获取全部活性药物
        drugs = DrugDAO.list_all_active()

        results = []
        for drug in drugs:
            ref_peaks = [_to_peak(p) for p in ReferencePeakDAO.get_by_drug_id(drug.id)]
            if not ref_peaks:
                continue

            drug_result = _match_drug(
                sample_peaks,
                ref_peaks,
                drug.id,
                drug.name,
                model_type,
                rrt_tolerance=rrt_tolerance,
                uv_distance_threshold=uv_distance_threshold,
                area_ratio_method=area_ratio_method,
            )
            drug_result.is_detected = drug_result.confidence >= confidence_threshold

            # 保存结果
            _save_detection_result(sample_id, None, drug_result)
            results.append(drug_result)

        # 按综合评分排序
        results.sort(key=lambda r: r.total_score, reverse=True)

        # 若用户未指定检测时间，则以实际检测完成时间为准
        if sample.detect_time is None:
            sample.detect_time = datetime.utcnow()

        SampleDAO.update_status(sample, "success")

        report = build_detection_report(
            sample_no=sample.sample_no,
            sample_name=sample.sample_name,
            results=results,
            detected_only=False,
            top_n=top_n,
        )
        report["detect_time"] = (sample.detect_time or sample.created_at).isoformat()
        return report

    except Exception as exc:
        SampleDAO.update_status(sample, "failed")
        raise exc


def create_batch_task(
    sample_ids: List[int], operator_id: Optional[int], name: Optional[str] = None
) -> DetectionTask:
    """
    创建批量检测任务。

    :param sample_ids: 样本ID列表
    :param operator_id: 操作员ID
    :param name: 任务名称
    :return: 任务对象
    """
    if not sample_ids:
        raise ParamValidationException("样本ID列表不能为空")

    task_no = generate_task_no()
    while DetectionTaskDAO.get_by_task_no(task_no):
        task_no = generate_task_no()

    task = DetectionTaskDAO.create(
        task_no=task_no,
        name=name or f"批量检测任务-{task_no}",
        operator_id=operator_id,
        total_samples=len(sample_ids),
        params={},
    )

    for sample_id in sample_ids:
        TaskSampleDAO.create(task.id, sample_id)

    return task


def _match_drug(
    sample_peaks: List[Peak],
    reference_peaks: List[Peak],
    drug_id: int,
    drug_name: str,
    model_type: str,
    rrt_tolerance: float = 0.02,
    uv_distance_threshold: float = 0.15,
    area_ratio_method: str = "relative_error",
) -> DrugMatchResult:
    """将样本峰与单个药物进行匹配。"""
    # 1. RRT 匹配：若药物已学习到有效的 RRT 统计量，则使用增量高斯模型
    stats = get_drug_rrt_stats(drug_id)
    if stats and stats["n"] > 0 and stats["std"] is not None and stats["std"] > 0:
        rrt_matches = match_peaks_by_retention_time_with_stats(
            sample_peaks,
            reference_peaks,
            rrt_mean=stats["mean"],
            rrt_std=stats["std"],
            tolerance=rrt_tolerance,
        )
    else:
        rrt_matches = match_peaks_by_retention_time(
            sample_peaks, reference_peaks, tolerance=rrt_tolerance
        )

    # 2. 峰面积比匹配
    area_score = match_area_ratios(sample_peaks, reference_peaks, method=area_ratio_method)

    # 3. UV 匹配（简化：使用主峰光谱）
    uv_score = _match_uv_spectrum(drug_id, sample_peaks, uv_distance_threshold)

    # 4. 计算每个峰的融合得分
    for match in rrt_matches:
        match.area_ratio_score = area_score
        match.uv_score = uv_score
        scores = {
            "rrt": match.rrt_score,
            "area_ratio": match.area_ratio_score,
            "uv": match.uv_score,
        }
        match.fusion_score = weighted_fusion(scores)
        # 单峰匹配判定保留 RRT 主导的结果，避免全局 area/UV 分数淹没保留时间信号

    # 5. 贝叶斯融合
    bayes_score = bayes_from_matches(rrt_matches, prior=0.5)

    # 6. 综合评分
    fusion_scores = {
        "rrt": _average_score(rrt_matches, "rrt_score"),
        "area_ratio": area_score,
        "uv": uv_score,
        "bayes": bayes_score,
    }
    total_score = weighted_fusion(fusion_scores)
    confidence = calculate_confidence(total_score, fusion_scores)

    matched_count = sum(1 for m in rrt_matches if m.is_matched)

    return DrugMatchResult(
        drug_id=str(drug_id),
        drug_name=drug_name,
        total_score=total_score,
        confidence=confidence,
        matched_peak_count=matched_count,
        total_peak_count=len(reference_peaks),
        peak_matches=rrt_matches,
        algorithm_details={
            "fusion_scores": fusion_scores,
            "model_type": model_type,
        },
    )


def _match_uv_spectrum(
    drug_id: int, sample_peaks: List[Peak], distance_threshold: float = 0.15
) -> float:
    """简化 UV 光谱匹配。"""
    ref_spectra = ReferenceSpectrumDAO.get_by_drug_id(drug_id)
    if not ref_spectra or not sample_peaks:
        return 0.0

    import numpy as np

    # 构建对照品光谱对象
    ref_wavelengths = np.array([float(sp.wavelength) for sp in ref_spectra])
    ref_absorbance = np.array([float(sp.absorbance) for sp in ref_spectra])
    from app.algorithm.types import Spectrum

    ref_spectrum = Spectrum(wavelength=ref_wavelengths, absorbance=ref_absorbance)

    # 使用样本中面积最大的峰构建简化光谱（实际应使用 DAD 原始光谱）
    main_peak = max(sample_peaks, key=lambda p: p.area)
    sample_spectrum = Spectrum(
        wavelength=ref_wavelengths,
        absorbance=np.array([float(main_peak.height) * 0.1] * len(ref_wavelengths)),
    )

    return calculate_uv_match_score(
        sample_spectrum,
        ref_spectrum,
        method="correlation",
        distance_threshold=distance_threshold,
    )


def _average_score(matches: List[MatchedPeak], attr: str) -> float:
    """计算匹配列表中某属性的平均值。"""
    if not matches:
        return 0.0
    return sum(getattr(m, attr) or 0.0 for m in matches) / len(matches)


def _save_detection_result(
    sample_id: int,
    task_id: Optional[int],
    result: DrugMatchResult,
) -> DetectionResult:
    """保存检测结果到数据库。"""
    return DetectionResultDAO.create(
        sample_id=sample_id,
        task_id=task_id,
        drug_id=int(result.drug_id),
        model_type=result.algorithm_details.get("model_type", "fusion"),
        total_score=result.total_score,
        confidence=result.confidence,
        matched_peak_count=result.matched_peak_count,
        total_peak_count=result.total_peak_count,
        is_detected=result.is_detected,
        algorithm_details=result.algorithm_details,
    )


def get_task_progress(task_id: int) -> Optional[dict]:
    """获取任务进度。"""
    task = DetectionTaskDAO.get_by_id(task_id)
    if task is None:
        return None

    return {
        "id": task.id,
        "taskNo": task.task_no,
        "name": task.name,
        "status": task.status,
        "totalSamples": task.total_samples,
        "completedSamples": task.completed_samples,
        "failedSamples": task.failed_samples,
        "progress": task.progress,
    }


def _to_peak(obj) -> Peak:
    """将数据库峰对象转换为算法 Peak 对象，数值统一转为 float。"""
    def _f(value):
        return float(value) if value is not None else None

    if isinstance(obj, SamplePeak):
        return Peak(
            index=obj.peak_index,
            retention_time=_f(obj.retention_time) or 0.0,
            area=_f(obj.area) or 0.0,
            height=_f(obj.height) or 0.0,
            width=_f(obj.width) or 0.0,
            wavelength=_f(obj.wavelength),
            relative_retention_time=_f(obj.relative_retention_time),
            area_ratio=_f(obj.area_ratio),
        )

    if isinstance(obj, ReferencePeak):
        return Peak(
            index=obj.peak_index,
            retention_time=_f(obj.retention_time) or 0.0,
            area=0.0,
            height=_f(obj.height) or 0.0,
            width=_f(obj.width) or 0.0,
            wavelength=_f(obj.wavelength),
            relative_retention_time=_f(obj.relative_retention_time),
            area_ratio=_f(obj.area_ratio),
        )

    raise TypeError(f"不支持的峰对象类型: {type(obj)}")
