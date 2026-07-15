# 企业版示例数据（合成测试数据）

> ⚠️ **声明**：本目录下所有药品保留时间、紫外吸收波长、峰面积常数均为**合成测试数据**，仅用于验证系统检测流程，不作为真实药典或法定检测依据。

本目录提供与「三步级联检测」配套的对照品库和测试样本。

## 文件说明

### 对照品库

| 文件 | 说明 |
|---|---|
| `drug_library_sedatives.json` | 安神镇定类 9 种药物（基于用户提供的真实参考数据） |
| `drug_library_enterprise.json` | 企业版多类别合成库，含 6 个类别共 39 种药物 |

### 级联检测输入样本

| 文件 | 说明 |
|---|---|
| `cascade_test_all_9.json` | 安神镇定类 9 种药物的级联检测输入参数 |
| `cascade_test_enterprise.json` | 企业版 6 个类别共 39 种药物的级联检测输入参数 |

### 色谱图样本（文件上传自动检测模式）

| 文件 | 说明 |
|---|---|
| `chromatogram_sedatives.csv` | 安神镇定类 9 个峰的模拟色谱图 |
| `chromatogram_weight_loss.csv` | 减肥类 6 个峰的模拟色谱图 |
| `chromatogram_diabetes.csv` | 降糖类 6 个峰的模拟色谱图 |
| `chromatogram_mixed.csv` | 混合 12 个峰（每个类别 2 个）的模拟色谱图 |

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
2. 导入 `drug_library_sedatives.json` 或 `drug_library_enterprise.json`
3. 进入「检测分析」→「级联检测 / 手动录入」
4. 选择药物类别和参照药物
5. 输入级联检测参数，查看 Step 1/2/3 结果

## 关于文件上传自动检测

目前「文件上传检测」标签页仍使用旧版融合模型（不是三步级联），因此对企业版多峰色谱图可能给出较低的综合评分。如需文件上传也按级联 SOP 判定，请联系开发团队扩展该功能。
