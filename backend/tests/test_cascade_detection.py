# -*- coding: utf-8 -*-
"""
三步级联检测算法单元测试。

覆盖：
- 安神镇定类 9 种药物各自输入均返回自身为 Step 3 Top 1
- 参照药物不在该类别时报错
- areas 缺少波长时报错
- lambda2 缺失时正确忽略
- 候选为空时返回 candidateCount=0 和空结果
"""

import json
import os

import pytest

from app.model import Drug, DrugCategory


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# 安神镇定类 9 种药物输入数据（与 demo_drugs_full.json / seed_sample_library.sql 一致）
SEDATIVE_INPUTS = {
    "咪达唑仑": {
        "tx": 6.256,
        "lambda1": 227.5,
        "lambda2": None,
        "areas": {"245": 1595667, "250": 1403031, "255": 1138550, "260": 813884},
    },
    "苯巴比妥": {
        "tx": 10.821,
        "lambda1": 222.7,
        "lambda2": None,
        "areas": {"245": 1441107, "250": 983841, "255": 729551, "260": 626377},
    },
    "盐酸氯丙嗪": {
        "tx": 12.988,
        "lambda1": 255.8,
        "lambda2": 308.1,
        "areas": {"245": 3010872, "250": 4040773, "255": 4726452, "260": 3678992},
    },
    "艾司唑仑": {
        "tx": 16.865,
        "lambda1": 225.1,
        "lambda2": None,
        "areas": {"245": 1547526, "250": 1379153, "255": 1032442, "260": 720495},
    },
    "奥沙西泮": {
        "tx": 17.434,
        "lambda1": 228.6,
        "lambda2": 312.9,
        "areas": {"245": 2064921, "250": 1815930, "255": 1540065, "260": 1151876},
    },
    "阿普唑仑": {
        "tx": 17.995,
        "lambda1": 223.9,
        "lambda2": None,
        "areas": {"245": 1177304, "250": 1044196, "255": 805899, "260": 596511},
    },
    "三唑仑": {
        "tx": 19.532,
        "lambda1": 225.1,
        "lambda2": None,
        "areas": {"245": 1568987, "250": 1291095, "255": 951835, "260": 633825},
    },
    "氯硝西泮": {
        "tx": 20.114,
        "lambda1": 220.4,
        "lambda2": 310.5,
        "areas": {"245": 1407669, "250": 1376894, "255": 1313144, "260": 1193772},
    },
    "地西泮": {
        "tx": 24.133,
        "lambda1": 231.0,
        "lambda2": 360.1,
        "areas": {"245": 3087279, "250": 2673562, "255": 2175960, "260": 1720816},
    },
}


THRESHOLDS = {
    "rrtTolerance": 0.03,
    "lambdaTolerance": 2.0,
    "r1Tolerance": 0.1,
    "r2Tolerance": 0.1,
    "r3Tolerance": 0.1,
}


def _login(client):
    resp = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["data"]["token"]


def _import_demo_data(client, headers):
    demo_path = os.path.join(
        PROJECT_ROOT, "..", "samples", "enterprise", "drug_library_comprehensive.json"
    )
    demo_path = os.path.abspath(demo_path)
    with open(demo_path, "rb") as f:
        data = {"file": (f, "drug_library_comprehensive.json")}
        resp = client.post(
            "/api/library/import",
            data=data,
            headers=headers,
            content_type="multipart/form-data",
        )
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()


@pytest.fixture
def auth_headers(client):
    token = _login(client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def imported_sedatives(client, auth_headers):
    """导入示例数据并设置安神镇定类参照药物为盐酸氯丙嗪。"""
    _import_demo_data(client, auth_headers)

    category = DrugCategory.query.filter_by(name="安神镇定类").first()
    reference_drug = Drug.query.filter_by(name="盐酸氯丙嗪").first()
    assert category is not None
    assert reference_drug is not None

    resp = client.put(
        f"/api/library/categories/{category.id}/reference-drug",
        json={"referenceDrugId": reference_drug.id},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.get_json()

    return category, reference_drug


@pytest.mark.parametrize("name,inputs", SEDATIVE_INPUTS.items())
def test_cascade_detect_self_as_top1(client, auth_headers, imported_sedatives, name, inputs):
    """9 种药物各自输入均应返回自身为 Step 3 Top 1，且 score ≈ 1.0。"""
    category, reference_drug = imported_sedatives
    drug = Drug.query.filter_by(name=name).first()
    assert drug is not None, f"药物 {name} 未导入"

    payload = {
        "categoryId": category.id,
        "referenceDrugId": reference_drug.id,
        "tx": inputs["tx"],
        "lambda1": inputs["lambda1"],
        "lambda2": inputs["lambda2"],
        "areas": inputs["areas"],
        "thresholds": THRESHOLDS,
    }

    resp = client.post(
        "/api/detect/cascade",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["code"] == 0, data

    step3 = data["data"]["step3"]
    assert len(step3["results"]) > 0, f"{name}: Step 3 无结果"
    top1 = step3["results"][0]
    assert top1["drugName"] == name, f"{name}: Top1 为 {top1['drugName']}"
    assert top1["score"] == pytest.approx(1.0, abs=1e-6), f"{name}: score={top1['score']}"


def test_cascade_reference_drug_not_in_category(client, auth_headers, imported_sedatives):
    """参照药物不在该类别时应返回参数错误。"""
    category, _reference_drug = imported_sedatives

    # 借用地西泮作为另一个类别的药物不存在；构造一个确定不属于该类别的药物 ID：
    # 找任意非安神镇定类的启用药物
    other_drug = Drug.query.filter(Drug.category_id != category.id, Drug.status == 1).first()
    assert other_drug is not None, "测试需要至少一个其他类别的药物"

    inputs = SEDATIVE_INPUTS["苯巴比妥"]
    payload = {
        "categoryId": category.id,
        "referenceDrugId": other_drug.id,
        "tx": inputs["tx"],
        "lambda1": inputs["lambda1"],
        "lambda2": inputs["lambda2"],
        "areas": inputs["areas"],
        "thresholds": THRESHOLDS,
    }

    resp = client.post(
        "/api/detect/cascade",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 400, resp.get_json()
    data = resp.get_json()
    assert data["code"] == 400
    assert "不属于当前类别" in data["msg"]


def test_cascade_missing_wavelength(client, auth_headers, imported_sedatives):
    """areas 缺少波长时应返回参数错误。"""
    category, reference_drug = imported_sedatives

    payload = {
        "categoryId": category.id,
        "referenceDrugId": reference_drug.id,
        "tx": 10.821,
        "lambda1": 222.7,
        "lambda2": None,
        "areas": {"245": 1441107, "250": 983841, "255": 729551},
        "thresholds": THRESHOLDS,
    }

    resp = client.post(
        "/api/detect/cascade",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 400, resp.get_json()
    data = resp.get_json()
    assert data["code"] == 400
    assert "260" in data["msg"]


def test_cascade_lambda2_ignored_when_absent(client, auth_headers, imported_sedatives):
    """样本 lambda2 缺失但药物有 lambda_max_2 时，应仅比较 lambda1。"""
    category, reference_drug = imported_sedatives

    # 盐酸氯丙嗪有 lambda_max_2=308.1，但请求不提供 lambda2
    inputs = SEDATIVE_INPUTS["盐酸氯丙嗪"].copy()
    inputs["lambda2"] = None
    inputs["areas"] = inputs["areas"].copy()

    payload = {
        "categoryId": category.id,
        "referenceDrugId": reference_drug.id,
        "tx": inputs["tx"],
        "lambda1": inputs["lambda1"],
        "lambda2": None,
        "areas": inputs["areas"],
        "thresholds": THRESHOLDS,
    }

    resp = client.post(
        "/api/detect/cascade",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["code"] == 0, data

    step2 = data["data"]["step2"]
    assert step2["lambda2"] is None
    assert any(c["drugName"] == "盐酸氯丙嗪" for c in step2["candidates"])


def test_cascade_empty_candidates(client, auth_headers, imported_sedatives):
    """使用不可能命中的 tx 时，应返回 candidateCount=0 和空结果。"""
    category, reference_drug = imported_sedatives

    payload = {
        "categoryId": category.id,
        "referenceDrugId": reference_drug.id,
        "tx": 999.999,
        "lambda1": 222.7,
        "lambda2": None,
        "areas": {"245": 1441107, "250": 983841, "255": 729551, "260": 626377},
        "thresholds": THRESHOLDS,
    }

    resp = client.post(
        "/api/detect/cascade",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["code"] == 0, data

    assert data["data"]["step1"]["candidateCount"] == 0
    assert data["data"]["step2"]["candidateCount"] == 0
    assert data["data"]["step3"]["results"] == []


def test_cascade_service_directly(imported_sedatives):
    """直接调用服务函数验证结构。"""
    from app.service.cascade_detection_service import detect_by_cascade

    category, reference_drug = imported_sedatives
    inputs = SEDATIVE_INPUTS["苯巴比妥"]

    result = detect_by_cascade(
        category_id=category.id,
        reference_drug_id=reference_drug.id,
        tx=inputs["tx"],
        lambda1=inputs["lambda1"],
        lambda2=inputs["lambda2"],
        areas=inputs["areas"],
        thresholds=THRESHOLDS,
    )

    assert result["referenceDrug"]["name"] == "盐酸氯丙嗪"
    assert result["step1"]["rrtSample"] == pytest.approx(0.833154, abs=1e-6)
    assert result["step3"]["results"][0]["drugName"] == "苯巴比妥"
    assert result["step3"]["results"][0]["score"] == pytest.approx(1.0, abs=1e-6)
