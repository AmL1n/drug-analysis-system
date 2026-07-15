# -*- coding: utf-8 -*-
"""
检测任务与结果 DAO。
"""

from typing import List, Optional

from app.model import DetectionResult, DetectionTask, TaskSample, db


class DetectionTaskDAO:
    """检测任务 DAO。"""

    @staticmethod
    def get_by_id(task_id: int) -> Optional[DetectionTask]:
        return db.session.get(DetectionTask, task_id)

    @staticmethod
    def get_by_task_no(task_no: str) -> Optional[DetectionTask]:
        return DetectionTask.query.filter_by(task_no=task_no).first()

    @staticmethod
    def create(
        task_no: str,
        name: Optional[str],
        operator_id: Optional[int],
        total_samples: int,
        params: dict,
    ) -> DetectionTask:
        task = DetectionTask(
            task_no=task_no,
            name=name,
            operator_id=operator_id,
            total_samples=total_samples,
            params=params,
        )
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def update_status(
        task: DetectionTask,
        status: str,
        completed: Optional[int] = None,
        failed: Optional[int] = None,
    ) -> None:
        task.status = status
        if completed is not None:
            task.completed_samples = completed
        if failed is not None:
            task.failed_samples = failed
        db.session.commit()

    @staticmethod
    def list_tasks(operator_id: Optional[int], page: int, page_size: int):
        query = DetectionTask.query
        if operator_id is not None:
            query = query.filter_by(operator_id=operator_id)
        return query.order_by(DetectionTask.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )


class TaskSampleDAO:
    """任务样本关联 DAO。"""

    @staticmethod
    def create(task_id: int, sample_id: int) -> TaskSample:
        ts = TaskSample(task_id=task_id, sample_id=sample_id)
        db.session.add(ts)
        db.session.commit()
        return ts

    @staticmethod
    def update_status(ts: TaskSample, status: str, result_summary: Optional[dict]) -> None:
        ts.status = status
        if result_summary is not None:
            ts.result_summary = result_summary
        db.session.commit()


class DetectionResultDAO:
    """检测结果 DAO。"""

    @staticmethod
    def get_by_id(result_id: int) -> Optional[DetectionResult]:
        return db.session.get(DetectionResult, result_id)

    @staticmethod
    def get_by_sample_and_task(
        sample_id: int, task_id: Optional[int]
    ) -> List[DetectionResult]:
        query = DetectionResult.query.filter_by(sample_id=sample_id)
        if task_id is not None:
            query = query.filter_by(task_id=task_id)
        return query.order_by(DetectionResult.total_score.desc()).all()

    @staticmethod
    def create(
        sample_id: int,
        task_id: Optional[int],
        drug_id: int,
        model_type: str,
        total_score: float,
        confidence: float,
        matched_peak_count: int,
        total_peak_count: int,
        is_detected: bool,
        algorithm_details: dict,
    ) -> DetectionResult:
        result = DetectionResult(
            sample_id=sample_id,
            task_id=task_id,
            drug_id=drug_id,
            model_type=model_type,
            total_score=total_score,
            confidence=confidence,
            matched_peak_count=matched_peak_count,
            total_peak_count=total_peak_count,
            is_detected=is_detected,
            algorithm_details=algorithm_details,
        )
        db.session.add(result)
        db.session.commit()
        return result

    @staticmethod
    def delete_by_sample(sample_id: int) -> None:
        DetectionResult.query.filter_by(sample_id=sample_id).delete()
        db.session.commit()

    @staticmethod
    def get_by_sample_id(sample_id: int) -> List[DetectionResult]:
        """获取某个样本的所有检测结果，按综合评分降序。"""
        return (
            DetectionResult.query.filter_by(sample_id=sample_id)
            .order_by(DetectionResult.total_score.desc())
            .all()
        )
