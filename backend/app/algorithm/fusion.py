# -*- coding: utf-8 -*-
"""
多模型融合模块。

将 RRT、峰面积比、UV、贝叶斯、SVM 等多个模型的得分，
按可配置权重融合为最终综合评分。
"""

from typing import Dict, List, Optional

import numpy as np


DEFAULT_MODEL_WEIGHTS = {
    "rrt": 0.35,
    "area_ratio": 0.25,
    "uv": 0.20,
    "bayes": 0.10,
    "svm": 0.10,
}


def validate_weights(weights: Dict[str, float]) -> None:
    """
    校验权重是否合法。

    :param weights: 模型权重字典
    :raises ValueError: 权重不合法时抛出
    """
    if not weights:
        raise ValueError("权重不能为空")

    total = sum(weights.values())
    if not np.isclose(total, 1.0, atol=1e-6):
        raise ValueError(f"权重之和必须等于 1，当前为 {total}")

    for key, value in weights.items():
        if value < 0:
            raise ValueError(f"模型 {key} 的权重不能为负数")


def weighted_fusion(
    scores: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    加权融合多个模型得分。

    :param scores: 模型得分字典，如 {"rrt": 0.9, "area_ratio": 0.8}
    :param weights: 模型权重字典，默认使用 DEFAULT_MODEL_WEIGHTS
    :return: 融合后的综合评分 [0, 1]
    """
    if weights is None:
        weights = DEFAULT_MODEL_WEIGHTS.copy()

    validate_weights(weights)

    # 只计算同时存在的模型
    common_keys = set(scores.keys()) & set(weights.keys())
    if not common_keys:
        return 0.0

    total_weight = sum(weights[k] for k in common_keys)
    if total_weight == 0:
        return 0.0

    fused_score = 0.0
    for key in common_keys:
        score = max(0.0, min(1.0, scores[key]))
        fused_score += weights[key] * score

    # 归一化到 [0, 1]
    return float(fused_score / total_weight)


def normalize_scores(
    scores: Dict[str, float],
    method: str = "min_max",
) -> Dict[str, float]:
    """
    对多个模型得分进行归一化。

    :param scores: 模型得分字典
    :param method: 归一化方法，min_max 或 softmax
    :return: 归一化后的得分字典
    """
    if not scores:
        return scores

    values = np.array(list(scores.values()), dtype=float)

    if method == "min_max":
        min_val = np.min(values)
        max_val = np.max(values)
        if np.isclose(max_val, min_val):
            normalized = np.zeros_like(values)
        else:
            normalized = (values - min_val) / (max_val - min_val)

    elif method == "softmax":
        exp_values = np.exp(values - np.max(values))
        normalized = exp_values / np.sum(exp_values)

    else:
        raise ValueError(f"不支持的归一化方法: {method}")

    return {key: float(normalized[i]) for i, key in enumerate(scores.keys())}


def calculate_confidence(
    fused_score: float,
    individual_scores: Dict[str, float],
) -> float:
    """
    根据融合得分和个体得分的一致性计算置信度。

    一致性越高，置信度越高。

    :param fused_score: 融合得分
    :param individual_scores: 个体模型得分
    :return: 置信度 [0, 1]
    """
    if not individual_scores:
        return fused_score

    values = np.array(list(individual_scores.values()), dtype=float)
    std = np.std(values)

    # 标准差越小，一致性越高，置信度越高
    consistency = max(0.0, 1.0 - std)
    confidence = 0.7 * fused_score + 0.3 * consistency

    return float(min(1.0, max(0.0, confidence)))
