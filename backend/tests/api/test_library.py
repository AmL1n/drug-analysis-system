# -*- coding: utf-8 -*-
"""
对照品库相关 API 测试。
"""

import io
import json

import pytest

from app.model import (
    Drug,
    DrugAreaConstant,
    DrugCategory,
    ReferencePeak,
    ReferenceSpectrum,
)


@pytest.fixture
def auth_headers(client):
    """获取已登录用户的 Authorization 请求头。"""
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 0
    token = data["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_import_library_drugs_success(client, auth_headers, app):
    """测试 /library/import 能正确导入药物、主峰、峰面积常数和光谱。"""
    payload = {
        "rt": [
            {
                "no": 1,
                "name": "  测试药物  ",
                "rt": "5.123",
                "ref_rt": 10.0,
                "rrt": 0.5123,
                "lambda1": "245.0",
                "lambda2": "/",
            }
        ],
        "area": [
            {
                "no": 1,
                "name": "测试药物",
                "a245": "100",
                "a250": "200",
                "r1": 0.5,
                "a255": "300",
                "r2": 1.5,
                "a260": "400",
                "r3": 2.0,
            }
        ],
    }

    data = {
        "file": (io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")), "test_library.json"),
    }

    resp = client.post(
        "/api/library/import",
        data=data,
        headers=auth_headers,
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    result = resp.get_json()
    assert result["code"] == 0, result.get("msg")

    summary = result["data"]
    assert summary["created"] == 1
    assert summary["updated"] == 0
    assert summary["failed"] == []

    with app.app_context():
        category = DrugCategory.query.filter_by(name="导入药物").first()
        assert category is not None

        drug = Drug.query.filter_by(name="测试药物").first()
        assert drug is not None
        assert drug.category_id == category.id
        assert drug.peak_count == 1

        peak = ReferencePeak.query.filter_by(drug_id=drug.id).first()
        assert peak is not None
        assert peak.peak_index == 1
        assert float(peak.retention_time) == pytest.approx(5.123)
        assert float(peak.relative_retention_time) == pytest.approx(0.5123)
        assert peak.is_main_peak is True
        assert float(peak.wavelength) == pytest.approx(245.0)

        constants = DrugAreaConstant.query.filter_by(drug_id=drug.id).all()
        assert len(constants) == 4
        wl_areas = {float(c.wavelength): float(c.area) for c in constants}
        assert wl_areas[245.0] == pytest.approx(100.0)
        assert wl_areas[250.0] == pytest.approx(200.0)
        assert wl_areas[255.0] == pytest.approx(300.0)
        assert wl_areas[260.0] == pytest.approx(400.0)

        spectra = ReferenceSpectrum.query.filter_by(drug_id=drug.id).all()
        assert len(spectra) == 1
        assert float(spectra[0].wavelength) == pytest.approx(245.0)
        assert float(spectra[0].absorbance) == pytest.approx(100.0)
