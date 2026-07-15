# -*- coding: utf-8 -*-
"""
文件上传与样本相关模型。
"""

from datetime import datetime

from . import db


class SampleChromatogram(db.Model):
    """样本原始色谱图数据表（解决 Render 等无持久盘环境文件丢失问题）。"""

    __tablename__ = "sample_chromatograms"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="样本ID",
    )
    time_json = db.Column(db.Text, nullable=False, comment="保留时间数组(JSON)")
    intensity_json = db.Column(db.Text, nullable=False, comment="强度数组(JSON)")
    wavelength = db.Column(db.Numeric(8, 2), default=None, comment="检测波长(nm)")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    sample = db.relationship("Sample", backref=db.backref("chromatogram", uselist=False))

    __table_args__ = (
        db.Index("idx_sample_chromatograms_sample_id", "sample_id"),
    )

    def __repr__(self) -> str:
        return f"<SampleChromatogram sample={self.sample_id}>"


class UploadedFile(db.Model):
    """上传文件记录表"""

    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    original_name = db.Column(
        db.String(255), nullable=False, comment="原始文件名"
    )
    storage_path = db.Column(
        db.String(500), nullable=False, comment="服务器存储路径"
    )
    file_size = db.Column(db.Integer, default=None, comment="文件大小(字节)")
    file_type = db.Column(db.String(50), default=None, comment="文件MIME类型")
    uploader_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        comment="上传人ID",
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    uploader = db.relationship("User", backref="uploaded_files")
    samples = db.relationship(
        "Sample", back_populates="uploaded_file", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<UploadedFile {self.original_name}>"


class Sample(db.Model):
    """检测样本表"""

    __tablename__ = "samples"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    sample_no = db.Column(
        db.String(100), unique=True, nullable=False, comment="样品编号"
    )
    sample_name = db.Column(db.String(255), default=None, comment="样品名称")
    operator_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        comment="操作员ID",
    )
    file_id = db.Column(
        db.Integer,
        db.ForeignKey("uploaded_files.id", ondelete="SET NULL"),
        default=None,
        comment="关联上传文件ID",
    )
    instrument_brand = db.Column(
        db.String(50), default=None, comment="仪器品牌"
    )
    detect_time = db.Column(db.DateTime, default=None, comment="检测时间")
    status = db.Column(
        db.String(20),
        default="pending",
        comment="状态：pending/running/success/failed",
    )
    remark = db.Column(db.Text, default=None, comment="备注")
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
    operator = db.relationship("User", backref="samples")
    uploaded_file = db.relationship("UploadedFile", back_populates="samples")
    peaks = db.relationship(
        "SamplePeak",
        back_populates="sample",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    spectra = db.relationship(
        "SampleSpectrum",
        back_populates="sample",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    detection_results = db.relationship(
        "DetectionResult",
        back_populates="sample",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    task_samples = db.relationship(
        "TaskSample", back_populates="sample", lazy="dynamic"
    )
    comparisons = db.relationship(
        "ChromatogramComparison",
        back_populates="sample",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Sample {self.sample_no}>"


class SamplePeak(db.Model):
    """样本峰表：每个峰一条记录。"""

    __tablename__ = "sample_peaks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
        comment="样本ID",
    )
    peak_index = db.Column(db.Integer, nullable=False, comment="峰序号")
    retention_time = db.Column(
        db.Numeric(10, 4), nullable=False, comment="保留时间(min)"
    )
    area = db.Column(db.Numeric(15, 4), default=None, comment="峰面积")
    height = db.Column(db.Numeric(15, 4), default=None, comment="峰高")
    width = db.Column(db.Numeric(10, 4), default=None, comment="半峰宽")
    wavelength = db.Column(
        db.Numeric(8, 2), default=None, comment="检测波长(nm)"
    )
    relative_retention_time = db.Column(
        db.Numeric(10, 4), default=None, comment="相对保留时间"
    )
    area_ratio = db.Column(
        db.Numeric(10, 6), default=None, comment="峰面积比值"
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    sample = db.relationship("Sample", back_populates="peaks")
    matches = db.relationship(
        "DetectionPeakMatch",
        back_populates="sample_peak",
        lazy="dynamic",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "sample_id", "peak_index", name="uk_sample_peaks_sample_peak"
        ),
        db.Index("idx_sample_peaks_sample_id", "sample_id"),
        db.Index("idx_sample_peaks_retention_time", "retention_time"),
    )

    def __repr__(self) -> str:
        return f"<SamplePeak sample={self.sample_id} index={self.peak_index}>"


class SampleSpectrum(db.Model):
    """样本原始DAD光谱数据表。"""

    __tablename__ = "sample_spectra"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
        comment="样本ID",
    )
    retention_time = db.Column(
        db.Numeric(10, 4), nullable=False, comment="保留时间(min)"
    )
    wavelength = db.Column(
        db.Numeric(8, 2), nullable=False, comment="波长(nm)"
    )
    absorbance = db.Column(
        db.Numeric(15, 6), nullable=False, comment="吸光度"
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    sample = db.relationship("Sample", back_populates="spectra")

    __table_args__ = (
        db.Index("idx_sample_spectra_sample_rt", "sample_id", "retention_time"),
        db.Index("idx_sample_spectra_sample_wl", "sample_id", "wavelength"),
    )

    def __repr__(self) -> str:
        return f"<SampleSpectrum sample={self.sample_id} rt={self.retention_time}>"
