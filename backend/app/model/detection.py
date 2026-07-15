# -*- coding: utf-8 -*-
"""
检测任务、结果、峰级匹配明细、峰值图对比相关模型。
"""

from datetime import datetime

from . import db


class DetectionTask(db.Model):
    """批量检测任务表"""

    __tablename__ = "detection_tasks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    task_no = db.Column(
        db.String(100), unique=True, nullable=False, comment="任务编号"
    )
    name = db.Column(db.String(255), default=None, comment="任务名称")
    operator_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        comment="创建人ID",
    )
    status = db.Column(
        db.String(20),
        default="pending",
        comment="状态：pending/running/success/failed/partial",
    )
    total_samples = db.Column(db.Integer, default=0, comment="样本总数")
    completed_samples = db.Column(db.Integer, default=0, comment="已完成数")
    failed_samples = db.Column(db.Integer, default=0, comment="失败数")
    params = db.Column(db.JSON, default=None, comment="检测参数")
    started_at = db.Column(db.DateTime, default=None, comment="开始时间")
    finished_at = db.Column(db.DateTime, default=None, comment="完成时间")
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    # 关系
    operator = db.relationship("User", backref="detection_tasks")
    task_samples = db.relationship(
        "TaskSample",
        back_populates="task",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    results = db.relationship(
        "DetectionResult",
        back_populates="task",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DetectionTask {self.task_no}>"

    @property
    def progress(self) -> float:
        """计算任务进度百分比。"""
        if self.total_samples <= 0:
            return 0.0
        return round((self.completed_samples / self.total_samples) * 100, 2)


class TaskSample(db.Model):
    """任务与样本关联表"""

    __tablename__ = "task_samples"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    task_id = db.Column(
        db.Integer,
        db.ForeignKey("detection_tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID",
    )
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
        comment="样本ID",
    )
    status = db.Column(
        db.String(20),
        default="pending",
        comment="状态：pending/running/success/failed",
    )
    result_summary = db.Column(db.JSON, default=None, comment="结果摘要")
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    # 关系
    task = db.relationship("DetectionTask", back_populates="task_samples")
    sample = db.relationship("Sample", back_populates="task_samples")

    __table_args__ = (
        db.UniqueConstraint(
            "task_id", "sample_id", name="uk_task_samples_task_sample"
        ),
        db.Index("idx_task_samples_task_id", "task_id"),
        db.Index("idx_task_samples_sample_id", "sample_id"),
    )

    def __repr__(self) -> str:
        return f"<TaskSample task={self.task_id} sample={self.sample_id}>"


class DetectionResult(db.Model):
    """检测结果表：样本 vs 药物的综合评分。"""

    __tablename__ = "detection_results"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
        comment="样本ID",
    )
    task_id = db.Column(
        db.Integer,
        db.ForeignKey("detection_tasks.id", ondelete="CASCADE"),
        default=None,
        comment="所属任务ID，单样本检测为空",
    )
    drug_id = db.Column(
        db.Integer,
        db.ForeignKey("drugs.id", ondelete="CASCADE"),
        nullable=False,
        comment="药物ID",
    )
    model_type = db.Column(
        db.String(20),
        default="fusion",
        comment="模型类型：rrt/area_ratio/uv/bayes/svm/fusion",
    )
    total_score = db.Column(
        db.Numeric(6, 4), default=None, comment="综合评分 0-1"
    )
    confidence = db.Column(
        db.Numeric(6, 4), default=None, comment="置信度 0-1"
    )
    matched_peak_count = db.Column(db.Integer, default=0, comment="匹配峰数量")
    total_peak_count = db.Column(db.Integer, default=0, comment="药物总峰数")
    is_detected = db.Column(
        db.Boolean, default=False, comment="是否判定为检出"
    )
    algorithm_details = db.Column(db.JSON, default=None, comment="算法详细结果")
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    # 关系
    sample = db.relationship("Sample", back_populates="detection_results")
    task = db.relationship("DetectionTask", back_populates="results")
    drug = db.relationship("Drug")
    peak_matches = db.relationship(
        "DetectionPeakMatch",
        back_populates="result",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "sample_id",
            "task_id",
            "drug_id",
            "model_type",
            name="uk_detection_results_sample_drug_model",
        ),
        db.Index("idx_detection_results_sample_id", "sample_id"),
        db.Index("idx_detection_results_task_id", "task_id"),
        db.Index("idx_detection_results_drug_id", "drug_id"),
        db.Index("idx_detection_results_score", "total_score"),
    )

    def __repr__(self) -> str:
        return f"<DetectionResult sample={self.sample_id} drug={self.drug_id}>"


class DetectionPeakMatch(db.Model):
    """检测峰级匹配明细表"""

    __tablename__ = "detection_peak_matches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    result_id = db.Column(
        db.Integer,
        db.ForeignKey("detection_results.id", ondelete="CASCADE"),
        nullable=False,
        comment="检测结果ID",
    )
    sample_peak_id = db.Column(
        db.Integer,
        db.ForeignKey("sample_peaks.id", ondelete="SET NULL"),
        default=None,
        comment="样本峰ID",
    )
    reference_peak_id = db.Column(
        db.Integer,
        db.ForeignKey("reference_peaks.id", ondelete="SET NULL"),
        default=None,
        comment="对照品峰ID",
    )
    rrt_score = db.Column(
        db.Numeric(6, 4), default=None, comment="RRT模型评分"
    )
    area_ratio_score = db.Column(
        db.Numeric(6, 4), default=None, comment="峰面积比模型评分"
    )
    uv_score = db.Column(
        db.Numeric(6, 4), default=None, comment="UV模型评分"
    )
    fusion_score = db.Column(
        db.Numeric(6, 4), default=None, comment="融合评分"
    )
    delta_rt = db.Column(
        db.Numeric(10, 4), default=None, comment="保留时间偏差"
    )
    delta_area_ratio = db.Column(
        db.Numeric(10, 6), default=None, comment="峰面积比偏差"
    )
    is_matched = db.Column(
        db.Boolean, default=False, comment="是否匹配"
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    result = db.relationship("DetectionResult", back_populates="peak_matches")
    sample_peak = db.relationship("SamplePeak", back_populates="matches")
    reference_peak = db.relationship("ReferencePeak")

    __table_args__ = (
        db.Index("idx_detection_peak_matches_result_id", "result_id"),
        db.Index("idx_detection_peak_matches_sample_peak_id", "sample_peak_id"),
        db.Index("idx_detection_peak_matches_ref_peak_id", "reference_peak_id"),
    )

    def __repr__(self) -> str:
        return f"<DetectionPeakMatch result={self.result_id}>"


class ChromatogramComparison(db.Model):
    """峰值图对比记录表"""

    __tablename__ = "chromatogram_comparisons"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
        comment="样本ID",
    )
    drug_id = db.Column(
        db.Integer,
        db.ForeignKey("drugs.id", ondelete="CASCADE"),
        nullable=False,
        comment="对照药物ID",
    )
    comparison_params = db.Column(db.JSON, default=None, comment="对比参数")
    comparison_result = db.Column(
        db.JSON, default=None, comment="对比结果：峰位配准、差异等"
    )
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        comment="创建人ID",
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    sample = db.relationship("Sample", back_populates="comparisons")
    drug = db.relationship("Drug")
    creator = db.relationship("User")

    __table_args__ = (
        db.Index("idx_chromatogram_comparisons_sample_id", "sample_id"),
        db.Index("idx_chromatogram_comparisons_drug_id", "drug_id"),
    )

    def __repr__(self) -> str:
        return f"<ChromatogramComparison sample={self.sample_id} drug={self.drug_id}>"
