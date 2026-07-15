# -*- coding: utf-8 -*-
"""
企业版 HPLC-DAD 药物检测系统 —— 级联检测端到端验证脚本。

验证完整流程：
1. 登录获取 JWT token
2. 导入 samples/demo_data/demo_drugs_full.json
3. 获取安神镇定类默认参照药物
4. 调用 POST /api/detect/cascade 对 9 种安神镇定类药物分别检测
5. 验证每种药物都是自身 Top 1

运行方式：
    # 先启动后端服务
    cd backend
    source .venv/Scripts/activate  # Windows
    set -a && source ../.env && set +a
    python run.py

    # 再执行本脚本
    cd backend
    python scripts/e2e_cascade_test.py
"""

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlencode


BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:5000")
API_PREFIX = "/api"
DEMO_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "samples", "demo_data", "demo_drugs_full.json")
)

# 安神镇定类 9 种药物输入数据（与 demo_drugs_full.json 一致）
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


class ApiError(Exception):
    """API 调用异常。"""

    def __init__(self, message, status=None, body=None):
        super().__init__(message)
        self.status = status
        self.body = body


def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + API_PREFIX + path


def _request(method: str, path: str, *, json_data=None, headers=None, form_data=None):
    """发起 HTTP 请求并返回解析后的 JSON。"""
    req_headers = dict(headers or {})
    data = None

    if json_data is not None:
        data = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    elif form_data is not None:
        data, content_type = form_data
        req_headers.setdefault("Content-Type", content_type)

    req = urllib.request.Request(
        _url(path),
        data=data,
        headers=req_headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        raise ApiError(f"HTTP {exc.code}: {exc.reason}", status=exc.code, body=parsed) from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"无法连接到后端服务: {exc.reason}") from exc


def _encode_multipart(fields, files):
    """构造 multipart/form-data 请求体（支持二进制文件）。"""
    boundary = "----E2ECascadeBoundary"
    body_parts = []

    for key, value in fields.items():
        body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
        body_parts.append(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8")
        )
        body_parts.append(f"{value}\r\n".encode("utf-8"))

    for key, file_path in files.items():
        filename = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "application/octet-stream"
        with open(file_path, "rb") as f:
            file_content = f.read()
        body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
        body_parts.append(
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
            .encode("utf-8")
        )
        body_parts.append(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        body_parts.append(file_content)
        body_parts.append(b"\r\n")

    body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(body_parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def login() -> str:
    """登录并返回 JWT token。"""
    status, resp = _request(
        "POST",
        "/auth/login",
        json_data={"username": "admin", "password": "admin123"},
    )
    if status != 200 or resp.get("code") != 0:
        raise ApiError(f"登录失败: {resp}", status=status, body=resp)
    return resp["data"]["token"]


def import_demo_library(token: str) -> dict:
    """导入示例对照品库。"""
    if not os.path.exists(DEMO_FILE):
        raise ApiError(f"示例文件不存在: {DEMO_FILE}")

    body, content_type = _encode_multipart({}, {"file": DEMO_FILE})
    status, resp = _request(
        "POST",
        "/library/import",
        headers={"Authorization": f"Bearer {token}"},
        form_data=(body, content_type),
    )
    if status != 200 or resp.get("code") != 0:
        raise ApiError(f"导入失败: {resp}", status=status, body=resp)
    return resp["data"]


def get_sedative_category(token: str) -> dict:
    """获取安神镇定类类别信息。"""
    status, resp = _request(
        "GET",
        "/library/categories",
        headers={"Authorization": f"Bearer {token}"},
    )
    if status != 200 or resp.get("code") != 0:
        raise ApiError(f"获取类别失败: {resp}", status=status, body=resp)

    category = next(
        (c for c in resp["data"] if c["name"] == "安神镇定类"),
        None,
    )
    if category is None:
        raise ApiError("未找到安神镇定类类别")
    return category


def get_reference_drug(token: str, category_id: int) -> dict:
    """获取安神镇定类的默认参照药物（盐酸氯丙嗪）。"""
    status, resp = _request(
        "GET",
        f"/library/categories/{category_id}/reference-drugs",
        headers={"Authorization": f"Bearer {token}"},
    )
    if status != 200 or resp.get("code") != 0:
        raise ApiError(f"获取参照药物失败: {resp}", status=status, body=resp)

    reference_drug = next(
        (d for d in resp["data"] if d["name"] == "盐酸氯丙嗪"),
        None,
    )
    if reference_drug is None:
        raise ApiError("未找到参照药物盐酸氯丙嗪")
    return reference_drug


def set_default_reference_drug(token: str, category_id: int, reference_drug_id: int) -> None:
    """设置类别默认参照药物。"""
    status, resp = _request(
        "PUT",
        f"/library/categories/{category_id}/reference-drug",
        headers={"Authorization": f"Bearer {token}"},
        json_data={"referenceDrugId": reference_drug_id},
    )
    if status != 200 or resp.get("code") != 0:
        raise ApiError(f"设置默认参照药物失败: {resp}", status=status, body=resp)


def detect_cascade(token: str, category_id: int, reference_drug_id: int, inputs: dict) -> dict:
    """调用级联检测接口。"""
    payload = {
        "categoryId": category_id,
        "referenceDrugId": reference_drug_id,
        "tx": inputs["tx"],
        "lambda1": inputs["lambda1"],
        "lambda2": inputs["lambda2"],
        "areas": inputs["areas"],
        "thresholds": THRESHOLDS,
    }
    status, resp = _request(
        "POST",
        "/detect/cascade",
        headers={"Authorization": f"Bearer {token}"},
        json_data=payload,
    )
    if status != 200 or resp.get("code") != 0:
        raise ApiError(f"级联检测失败: {resp}", status=status, body=resp)
    return resp["data"]


def main():
    print(f"端到端验证目标: {BASE_URL}")

    try:
        token = login()
        print("登录成功，获取 token")

        import_summary = import_demo_library(token)
        print(f"导入示例库成功: created={import_summary.get('created', 0)}, updated={import_summary.get('updated', 0)}, failed={import_summary.get('failed', 0)}")

        category = get_sedative_category(token)
        print(f"安神镇定类 category_id={category['id']}")

        reference_drug = get_reference_drug(token, category["id"])
        print(f"默认参照药物: {reference_drug['name']} (id={reference_drug['id']})")
        set_default_reference_drug(token, category["id"], reference_drug["id"])

        errors = []
        for name, inputs in SEDATIVE_INPUTS.items():
            result = detect_cascade(token, category["id"], reference_drug["id"], inputs)
            step1_count = result["step1"]["candidateCount"]
            step2_count = result["step2"]["candidateCount"]
            step3_results = result["step3"]["results"]

            if not step3_results:
                errors.append(f"{name}: Step 3 无结果")
                print(f"{name}: Step1={step1_count} Step2={step2_count} Step3=无结果 ❌")
                continue

            top1 = step3_results[0]
            if top1["drugName"] != name:
                errors.append(f"{name}: Top1 为 {top1['drugName']}，期望 {name}")
            if abs(top1["score"] - 1.0) > 1e-6:
                errors.append(f"{name}: score={top1['score']:.6f}，期望 1.0")

            ok = top1["drugName"] == name and abs(top1["score"] - 1.0) <= 1e-6
            status_icon = "PASS" if ok else "FAIL"
            print(
                f"{name}: Step1={step1_count} Step2={step2_count} "
                f"Top1={top1['drugName']} score={top1['score']:.6f} [{status_icon}]"
            )

        if errors:
            print("\n级联检测端到端验证失败:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)

        print("\n[OK] 9 种安神镇定类药物级联检测端到端验证通过，各自返回自身为 Top 1")

    except ApiError as exc:
        print(f"\n端到端验证异常: {exc}")
        if exc.body:
            print("响应体:", json.dumps(exc.body, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
