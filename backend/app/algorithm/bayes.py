# -*- coding: utf-8 -*-
"""
贝叶斯概率融合模块。

基于多个特征（RRT、峰面积比、UV 等）计算药物检出的后验概率。

假设各特征条件独立，使用朴素贝叶斯方法：
    P(drug | features) ∝ P(drug) * Π P(feature_i | drug)
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from .types import MatchedPeak


def sigmoid_transform(value: float, steepness: float = 10.0) -> float:
    """
    使用 sigmoid 将得分映射为概率-like 值。

    :param value: 输入值，范围 [0, 1]
    :param steepness: 陡峭程度
    :return: 映射后的值
    """
    value = max(0.0, min(1.0, value))
    return float(1.0 / (1.0 + np.exp(-steepness * (value - 0.5))))


def calculate_likelihood(
    score: float,
    true_mean: float = 0.8,
    true_std: float = 0.15,
    false_mean: float = 0.2,
    false_std: float = 0.15,
) -> Tuple[float, float]:
    """
    计算某特征在“是目标药物”和“不是目标药物”两类下的似然。

    使用高斯分布近似似然。

    :param score: 特征得分 [0, 1]
    :param true_mean: 真实阳性时的分布均值
    :param true_std: 真实阳性时的分布标准差
    :param false_mean: 真实阴性时的分布均值
    :param false_std: 真实阴性时的分布标准差
    :return: (P(score | drug=True), P(score | drug=False))
    """
    likelihood_true = np.exp(-0.5 * ((score - true_mean) / true_std) ** 2)
    likelihood_false = np.exp(-0.5 * ((score - false_mean) / false_std) ** 2)
    return float(likelihood_true), float(likelihood_false)


def naive_bayes_fusion(
    scores: Dict[str, float],
    prior: float = 0.5,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    朴素贝叶斯融合多个特征得分。

    :param scores: 特征得分字典，如 {"rrt": 0.9, "area_ratio": 0.8, "uv": 0.85}
    :param prior: 先验概率 P(drug)
    :param weights: 各特征权重，默认等权重
    :return: 后验概率 P(drug | features)，范围 [0, 1]
    """
    if not scores:
        return prior

    if weights is None:
        weights = {key: 1.0 for key in scores}

    # 确保所有特征都有权重
    for key in scores:
        if key not in weights:
            weights[key] = 1.0

    log_likelihood_true = 0.0
    log_likelihood_false = 0.0

    for feature, score in scores.items():
        weight = weights.get(feature, 1.0)
        score = max(0.0, min(1.0, score))
        like_true, like_false = calculate_likelihood(score)

        # 避免 log(0)
        like_true = max(like_true, 1e-10)
        like_false = max(like_false, 1e-10)

        log_likelihood_true += weight * np.log(like_true)
        log_likelihood_false += weight * np.log(like_false)

    # 计算后验概率
    numerator = prior * np.exp(log_likelihood_true)
    denominator = numerator + (1.0 - prior) * np.exp(log_likelihood_false)

    if denominator == 0:
        return 0.0

    posterior = numerator / denominator
    return float(posterior)


def bayes_from_matches(
    matches: List[MatchedPeak],
    prior: float = 0.5,
    feature_weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    从峰匹配结果中提取特征得分，使用贝叶斯融合计算药物级概率。

    :param matches: 峰匹配结果列表
    :param prior: 先验概率
    :param feature_weights: 特征权重
    :return: 后验概率
    """
    if not matches:
        return 0.0

    # 取所有匹配峰的平均分作为药物级特征得分
    avg_rrt = np.mean([m.rrt_score for m in matches])
    avg_area = np.mean([m.area_ratio_score for m in matches])
    avg_uv = np.mean([m.uv_score for m in matches])

    scores = {
        "rrt": avg_rrt,
        "area_ratio": avg_area,
        "uv": avg_uv,
    }

    return naive_bayes_fusion(scores, prior=prior, weights=feature_weights)
