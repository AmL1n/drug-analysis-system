# -*- coding: utf-8 -*-
"""
对照品库药物列表导入服务。

支持 docs/reference_db_extracted.json 格式，将外部药物标准库导入为
药物、参考峰、峰面积常数和光谱数据，用于后续匹配。
"""

import json
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from app.errors.exceptions import ParamValidationException
from app.model import (
    Drug,
    DrugAreaConstant,
    DrugCategory,
    ReferencePeak,
    ReferenceSpectrum,
    db,
)

_AREA_WAVELENGTHS = [245, 250, 255, 260]


def _to_decimal(value: Any, allow_none: bool = False) -> Optional[Decimal]:
    """将值转换为 Decimal，失败时返回默认值或抛出异常。"""
    if value is None:
        if allow_none:
            return None
        raise ValueError("数值为空")
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"无法解析数值 {value!r}: {exc}")


def _safe_str(value: Any) -> Optional[str]:
    """安全地将值转为非空字符串，空值返回 None。"""
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _parse_wavelength(value: Any) -> Optional[Decimal]:
    """解析波长：'/'、'／' 或空表示无。"""
    if value is None:
        return None
    text = str(value).strip()
    if text in ("", "/", "／"):
        return None
    return _to_decimal(text)


def _get_or_create_category(
    category_id: Optional[int] = None,
    category_name: Optional[str] = None,
) -> DrugCategory:
    """获取导入目标类别；未指定时使用默认类别"导入药物"。

    支持按 ID、按名称查找或自动创建新类别。
    """
    if category_id is not None:
        category = db.session.get(DrugCategory, category_id)
        if category is None:
            raise ParamValidationException("指定的药物类别不存在")
        return category

    if category_name:
        category = DrugCategory.query.filter_by(name=category_name).first()
        if category is not None:
            return category
        # 按名称自动创建新类别
        max_code = db.session.query(db.func.max(DrugCategory.code)).scalar() or 0
        code = max(max_code + 1, 900)
        category = DrugCategory(
            name=category_name,
            code=code,
            description=f"{category_name}导入类别",
            wavelengths=[245, 250, 255, 260],
            sort_order=code,
        )
        db.session.add(category)
        db.session.flush()
        return category

    category = DrugCategory.query.filter_by(name="导入药物").first()
    if category is not None:
        return category

    max_code = db.session.query(db.func.max(DrugCategory.code)).scalar() or 0
    code = max(max_code + 1, 900)
    category = DrugCategory(
        name="导入药物",
        code=code,
        description="药物列表导入默认类别",
        wavelengths=[245, 250, 255, 260],
        sort_order=code,
    )
    db.session.add(category)
    db.session.flush()
    return category


def _build_area_constants(
    area_record: Dict[str, Any], drug_id: int
) -> List[DrugAreaConstant]:
    """根据 area 记录构建 245/250/255/260 nm 峰面积常数。"""
    constants: List[DrugAreaConstant] = []
    base_250: Optional[Decimal] = None

    for wl in _AREA_WAVELENGTHS:
        raw = area_record.get(f"a{wl}")
        area = _to_decimal(raw, allow_none=True)
        if area is None:
            continue
        if wl == 250:
            base_250 = area
        constants.append((wl, area))

    results = []
    for wl, area in constants:
        ratio = None
        if base_250 is not None and base_250 != 0:
            ratio = area / base_250
        results.append(
            DrugAreaConstant(
                drug_id=drug_id,
                wavelength=Decimal(wl),
                area=area,
                ratio_to_250=ratio,
            )
        )
    return results


def _build_spectra(
    rt_record: Dict[str, Any],
    area_constants: List[DrugAreaConstant],
    drug_id: int,
) -> List[ReferenceSpectrum]:
    """为 lambda1/lambda2 中有效波长创建光谱记录。"""
    if not area_constants:
        return []

    wavelengths: List[tuple[str, Decimal]] = []
    for key in ("lambda1", "lambda2"):
        wl = _parse_wavelength(rt_record.get(key))
        if wl is not None:
            wavelengths.append((key, wl))

    if not wavelengths:
        return []

    candidates = [
        (float(const.wavelength), const.area) for const in area_constants
    ]

    spectra = []
    seen: set = set()
    for key, wl in wavelengths:
        if wl in seen:
            continue
        seen.add(wl)
        wl_float = float(wl)
        closest = min(candidates, key=lambda item: abs(item[0] - wl_float))
        spectra.append(
            ReferenceSpectrum(
                drug_id=drug_id,
                wavelength=wl,
                absorbance=closest[1],
                is_max=(key == "lambda1"),
            )
        )
    return spectra


def import_library_from_json(
    file_storage, category_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    从上传的 JSON 文件导入药物列表到对照品库。

    :param file_storage: Flask FileStorage 对象
    :param category_id: 目标类别 ID，None 时使用默认类别
    :return: 导入摘要 {created, updated, failed}
    """
    try:
        content = file_storage.stream.read().decode("utf-8")
        data = json.loads(content)
    except (AttributeError, UnicodeDecodeError) as exc:
        raise ParamValidationException(f"文件读取失败：{exc}") from exc
    except json.JSONDecodeError as exc:
        raise ParamValidationException(f"JSON 解析失败：{exc}") from exc

    if not isinstance(data, dict):
        raise ParamValidationException("JSON 根对象必须是对象")

    rt_list = data.get("rt")
    area_list = data.get("area")
    if not isinstance(rt_list, list) or not isinstance(area_list, list):
        raise ParamValidationException("JSON 必须包含 rt 和 area 数组")

    area_map: Dict[str, Dict[str, Any]] = {}
    for record in area_list:
        if not isinstance(record, dict):
            continue
        name = str(record.get("name", "")).strip()
        if name:
            area_map[name] = record

    created = 0
    updated = 0
    failed: List[Dict[str, str]] = []
    processed_names: set = set()

    try:
        for record in rt_list:
            drug_name = ""
            try:
                if not isinstance(record, dict):
                    raise ValueError("rt 记录必须是对象")

                drug_name = str(record.get("name", "")).strip()
                if not drug_name:
                    raise ValueError("药物名称为空")

                if drug_name in processed_names:
                    continue

                area_record = area_map.get(drug_name)

                retention_time = _to_decimal(record.get("rt"))
                relative_retention_time = _to_decimal(
                    record.get("rrt"), allow_none=True
                )

                # 优先按药物记录中的 category 字段决定类别；否则使用传入的 category_id
                record_category_name = str(record.get("category", "")).strip() or None
                drug_category = _get_or_create_category(
                    category_id=category_id if not record_category_name else None,
                    category_name=record_category_name,
                )

                drug = Drug.query.filter_by(name=drug_name).first()
                is_new = drug is None

                if is_new:
                    drug = Drug(
                        name=drug_name,
                        category_id=drug_category.id,
                        peak_count=1,
                        status=1,
                    )
                    db.session.add(drug)
                else:
                    ReferencePeak.query.filter_by(drug_id=drug.id).delete()
                    ReferenceSpectrum.query.filter_by(drug_id=drug.id).delete()
                    DrugAreaConstant.query.filter_by(drug_id=drug.id).delete()
                    drug.category_id = drug_category.id
                    drug.peak_count = 1

                # 补充 CAS、分子式、说明、最大吸收波长等元数据
                drug.cas = _safe_str(record.get("cas")) or drug.cas
                drug.molecular_formula = (
                    _safe_str(record.get("molecular_formula"))
                    or drug.molecular_formula
                )
                drug.description = (
                    _safe_str(record.get("description")) or drug.description
                )
                drug.lambda_max_1 = _parse_wavelength(record.get("lambda1"))
                drug.lambda_max_2 = _parse_wavelength(record.get("lambda2"))

                db.session.flush()

                peak = ReferencePeak(
                    drug_id=drug.id,
                    peak_index=1,
                    retention_time=retention_time,
                    relative_retention_time=relative_retention_time,
                    area_ratio=Decimal("1.0"),
                    wavelength=_parse_wavelength(record.get("lambda1")),
                    is_main_peak=True,
                )
                db.session.add(peak)

                # area 数据可选：缺失时仅跳过级联判定相关数据，不影响药物和主峰导入
                if area_record is not None:
                    area_constants = _build_area_constants(area_record, drug.id)
                    for const in area_constants:
                        db.session.add(const)

                    spectra = _build_spectra(record, area_constants, drug.id)
                    for sp in spectra:
                        db.session.add(sp)

                if is_new:
                    created += 1
                else:
                    updated += 1

                processed_names.add(drug_name)
            except Exception as exc:  # noqa: BLE001
                failed.append({"name": drug_name, "reason": str(exc)})

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {"created": created, "updated": updated, "failed": failed}
