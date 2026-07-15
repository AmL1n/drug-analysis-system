# -*- coding: utf-8 -*-
"""
对照品库相关模型：药物类别、药物、峰库、光谱库、模型参数、峰面积常数。

字段设计参考：
- 《导入文件标准说明》
- 《数据库六种表结构.xlsx》
- 《对照品数据库20220402.xlsx》
"""

from datetime import datetime

from . import db


class DrugCategory(db.Model):
    """药物类别表"""

    __tablename__ = "drug_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    name = db.Column(
        db.String(100), unique=True, nullable=False, comment="类别名称"
    )
    code = db.Column(db.Integer, unique=True, nullable=False, comment="类别编码")
    description = db.Column(db.Text, default=None, comment="类别描述")
    # 检测波长数组，如 [245, 250, 255, 260]
    wavelengths = db.Column(db.JSON, default=list, comment="检测波长(nm)列表")
    # 标准参照物，用于计算相对保留时间
    reference_drug_id = db.Column(
        db.Integer,
        db.ForeignKey("drugs.id", ondelete="SET NULL"),
        default=None,
        comment="标准参照物ID",
    )
    sort_order = db.Column(db.Integer, default=0, comment="排序号")
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    drugs = db.relationship(
        "Drug", back_populates="category", lazy="dynamic",
        foreign_keys="Drug.category_id",
    )
    reference_drug = db.relationship(
        "Drug",
        foreign_keys=[reference_drug_id],
        post_update=True,
    )

    def __repr__(self) -> str:
        return f"<DrugCategory {self.name}>"


class Drug(db.Model):
    """药物基本信息表"""

    __tablename__ = "drugs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("drug_categories.id", ondelete="SET NULL"),
        default=None,
        comment="药物类别ID",
    )
    name = db.Column(db.String(255), nullable=False, comment="药物名称")
    cas = db.Column(db.String(50), default=None, comment="CAS号")
    molecular_formula = db.Column(db.String(100), default=None, comment="分子式")
    description = db.Column(db.Text, default=None, comment="药物描述")
    # 色谱峰个数
    peak_count = db.Column(db.Integer, default=0, comment="色谱峰个数")
    status = db.Column(db.SmallInteger, default=1, comment="状态：0禁用 1启用")
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
    category = db.relationship(
        "DrugCategory",
        back_populates="drugs",
        foreign_keys=[category_id],
    )
    peaks = db.relationship(
        "ReferencePeak",
        back_populates="drug",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    spectra = db.relationship(
        "ReferenceSpectrum",
        back_populates="drug",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    area_constants = db.relationship(
        "DrugAreaConstant",
        back_populates="drug",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    model_params = db.relationship(
        "ModelParam",
        back_populates="drug",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Drug {self.name}>"


class ReferencePeak(db.Model):
    """峰库：每种药物的每个峰一条记录。"""

    __tablename__ = "reference_peaks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    drug_id = db.Column(
        db.Integer,
        db.ForeignKey("drugs.id", ondelete="CASCADE"),
        nullable=False,
        comment="药物ID",
    )
    peak_index = db.Column(db.Integer, nullable=False, comment="峰序号")
    retention_time = db.Column(
        db.Numeric(10, 4), nullable=False, comment="保留时间(min)"
    )
    relative_retention_time = db.Column(
        db.Numeric(10, 4), default=None, comment="相对保留时间"
    )
    area_ratio = db.Column(
        db.Numeric(10, 6), default=None, comment="峰面积比值"
    )
    wavelength = db.Column(
        db.Numeric(8, 2), default=None, comment="检测波长(nm)"
    )
    height = db.Column(db.Numeric(15, 4), default=None, comment="峰高")
    width = db.Column(db.Numeric(10, 4), default=None, comment="半峰宽")
    is_main_peak = db.Column(
        db.Boolean, default=False, comment="是否主峰"
    )
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
    drug = db.relationship("Drug", back_populates="peaks")

    # 联合唯一约束
    __table_args__ = (
        db.UniqueConstraint("drug_id", "peak_index", name="uk_reference_peaks_drug_peak"),
        db.Index("idx_reference_peaks_drug_id", "drug_id"),
    )

    def __repr__(self) -> str:
        return f"<ReferencePeak drug={self.drug_id} index={self.peak_index}>"


class ReferenceSpectrum(db.Model):
    """光谱库：每种药物的最大吸收波长记录。"""

    __tablename__ = "reference_spectra"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    drug_id = db.Column(
        db.Integer,
        db.ForeignKey("drugs.id", ondelete="CASCADE"),
        nullable=False,
        comment="药物ID",
    )
    wavelength = db.Column(
        db.Numeric(8, 2), nullable=False, comment="波长(nm)"
    )
    absorbance = db.Column(
        db.Numeric(15, 6), nullable=False, comment="吸光度"
    )
    is_max = db.Column(
        db.Boolean, default=False, comment="是否为最大吸收波长"
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="创建时间"
    )

    # 关系
    drug = db.relationship("Drug", back_populates="spectra")

    __table_args__ = (
        db.UniqueConstraint(
            "drug_id", "wavelength", name="uk_reference_spectra_drug_wavelength"
        ),
        db.Index("idx_reference_spectra_drug_id", "drug_id"),
    )

    def __repr__(self) -> str:
        return f"<ReferenceSpectrum drug={self.drug_id} wl={self.wavelength}>"


class DrugAreaConstant(db.Model):
    """
    峰面积常数表。

    按《对照品数据库》记录每种药物在 245/250/255/260 nm 等波长下的峰面积常数，
    以及相对于 250 nm 的比值。
    """

    __tablename__ = "drug_area_constants"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    drug_id = db.Column(
        db.Integer,
        db.ForeignKey("drugs.id", ondelete="CASCADE"),
        nullable=False,
        comment="药物ID",
    )
    wavelength = db.Column(
        db.Numeric(8, 2), nullable=False, comment="波长(nm)"
    )
    area = db.Column(
        db.Numeric(15, 4), nullable=False, comment="峰面积常数"
    )
    ratio_to_250 = db.Column(
        db.Numeric(10, 6), default=None, comment="与250nm面积的比值"
    )
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
    drug = db.relationship("Drug", back_populates="area_constants")

    __table_args__ = (
        db.UniqueConstraint(
            "drug_id", "wavelength", name="uk_drug_area_constants_drug_wavelength"
        ),
        db.Index("idx_drug_area_constants_drug_id", "drug_id"),
    )

    def __repr__(self) -> str:
        return f"<DrugAreaConstant drug={self.drug_id} wl={self.wavelength}>"


class ModelParam(db.Model):
    """模型参数表：按药物+模型类型存储 JSON 参数。"""

    __tablename__ = "model_params"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="主键")
    drug_id = db.Column(
        db.Integer,
        db.ForeignKey("drugs.id", ondelete="CASCADE"),
        nullable=False,
        comment="药物ID",
    )
    model_type = db.Column(
        db.String(50), nullable=False, comment="模型类型：rrt/area_ratio/uv/bayes/svm"
    )
    param_name = db.Column(db.String(100), nullable=False, comment="参数名称")
    param_value = db.Column(db.JSON, nullable=False, comment="参数值")
    description = db.Column(db.Text, default=None, comment="参数说明")
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
    drug = db.relationship("Drug", back_populates="model_params")

    __table_args__ = (
        db.Index("idx_model_params_drug_id", "drug_id"),
        db.Index("idx_model_params_model_type", "model_type"),
    )

    def __repr__(self) -> str:
        return f"<ModelParam drug={self.drug_id} type={self.model_type}>"
