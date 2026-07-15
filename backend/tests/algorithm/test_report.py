# -*- coding: utf-8 -*-
"""
报告生成模块单元测试。
"""

from app.algorithm.report import build_detection_report, build_batch_report
from app.algorithm.types import DrugMatchResult, MatchedPeak, Peak


class TestBuildDetectionReport:
    def test_report_structure(self):
        sample_peak = Peak(index=1, retention_time=5.0)
        ref_peak = Peak(index=1, retention_time=5.0)
        match = MatchedPeak(
            sample_peak=sample_peak,
            reference_peak=ref_peak,
            rrt_score=0.95,
            area_ratio_score=0.9,
            uv_score=0.92,
            fusion_score=0.93,
            is_matched=True,
        )
        result = DrugMatchResult(
            drug_id="1",
            drug_name="西地那非",
            total_score=0.95,
            confidence=0.93,
            matched_peak_count=1,
            total_peak_count=1,
            is_detected=True,
            peak_matches=[match],
        )

        report = build_detection_report(
            sample_no="S001",
            sample_name="测试样品",
            results=[result],
        )

        assert report["report_type"] == "detection"
        assert report["sample_no"] == "S001"
        assert report["summary"]["detected_count"] == 1
        assert len(report["summary"]["top_drugs"]) == 1
        assert report["summary"]["top_drugs"][0]["drug_name"] == "西地那非"

    def test_detected_only_filter(self):
        detected = DrugMatchResult(
            drug_id="1", drug_name="A", total_score=0.9, is_detected=True
        )
        not_detected = DrugMatchResult(
            drug_id="2", drug_name="B", total_score=0.3, is_detected=False
        )
        report = build_detection_report(
            sample_no="S002", sample_name=None, results=[detected, not_detected]
        )
        assert len(report["summary"]["top_drugs"]) == 1

    def test_top_n_limit(self):
        results = [
            DrugMatchResult(
                drug_id=str(i), drug_name=f"D{i}", total_score=0.9 - i * 0.1, is_detected=True
            )
            for i in range(5)
        ]
        report = build_detection_report(
            sample_no="S003", sample_name=None, results=results, top_n=3
        )
        assert len(report["summary"]["top_drugs"]) == 3


class TestBuildBatchReport:
    def test_batch_report(self):
        sample_reports = [
            {
                "summary": {"detected_count": 2},
            },
            {
                "summary": {"detected_count": 1},
            },
        ]
        report = build_batch_report("T001", sample_reports)
        assert report["report_type"] == "batch"
        assert report["task_no"] == "T001"
        assert report["summary"]["total_samples"] == 2
        assert report["summary"]["total_detected"] == 3
