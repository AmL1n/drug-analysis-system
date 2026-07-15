# 企业版安神镇定类示例数据

本目录提供与「三步级联检测」配套的对照品库和测试样本。

## 文件说明

| 文件 | 说明 |
|---|---|
| `drug_library_sedatives.json` | 安神镇定类 9 种对照品库，含保留时间、相对保留时间、最大吸收波长、峰面积常数 |
| `cascade_test_all_9.json` | 9 种药物的级联检测输入参数，用于验证 `/api/detect/cascade` |
| `chromatogram_sedatives.csv` | 模拟色谱图，包含 9 个峰，可用于文件上传自动检测模式 |

## 级联检测参数示例（苯巴比妥）

```json
{
  "categoryId": 1,
  "referenceDrugId": 37,
  "tx": 10.821,
  "lambda1": 222.7,
  "lambda2": null,
  "areas": {
    "245": 1441107,
    "250": 983841,
    "255": 729551,
    "260": 626377
  },
  "thresholds": {
    "rrtTolerance": 0.03,
    "lambdaTolerance": 2.0,
    "r1Tolerance": 0.1,
    "r2Tolerance": 0.1,
    "r3Tolerance": 0.1
  }
}
```

## 使用步骤

1. 登录系统后进入「对照品库」
2. 导入 `drug_library_sedatives.json`
3. 进入「检测分析」→「级联检测 / 手动录入」
4. 选择「安神镇定类」，参照药物选择「盐酸氯丙嗪」
5. 输入 `cascade_test_all_9.json` 中任意一组参数，Step 3 Top 1 应为对应药物
