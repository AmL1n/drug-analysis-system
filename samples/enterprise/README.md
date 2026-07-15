# 企业版示例数据（合成测试数据）

> ⚠️ **声明**：本目录下除安神镇定类 9 种药物外，其余药品保留时间、紫外吸收波长、峰面积常数均为**合成测试数据**，仅用于验证系统检测流程，不作为真实药典或法定检测依据。

## 文件说明

| 文件 | 说明 |
|---|---|
| `drug_library_comprehensive.json` | **全面对照品库**，含 6 个类别共 34 种药物（安神镇定类 9 种为真实参考数据，其余为合成数据） |
| `cascade_test_samples.json` | **级联检测手动录入样例**，含 7 组跨类别测试数据 |
| `chromatogram_phenobarbital.csv` | **苯巴比妥**单峰色谱图，用于文件上传自动检测 |
| `chromatogram_chlorpromazine.csv` | **盐酸氯丙嗪**单峰色谱图，用于文件上传自动检测 |
| `chromatogram_diazepam.csv` | **地西泮**单峰色谱图，用于文件上传自动检测 |
| `chromatogram_metformin.csv` | **二甲双胍**单峰色谱图，用于文件上传自动检测 |
| `chromatogram_sibutramine.csv` | **西布曲明**单峰色谱图，用于文件上传自动检测 |
| `chromatogram_sedatives.csv` | **安神镇定类混合**色谱图样本，含 9 个峰 |
| `chromatogram_mixed.csv` | **跨类别混合**色谱图样本，含 5 个峰（5 个类别各 1 个） |

## 药物类别与数量

| 类别 | 数量 | 参照药物 |
|---|---|---|
| 安神镇定类 | 9 | 盐酸氯丙嗪 |
| 减肥类 | 5 | 西布曲明 |
| 降糖类 | 5 | 格列本脲 |
| 降压类 | 5 | 硝苯地平 |
| 降脂类 | 5 | 辛伐他汀 |
| 抗感冒类 | 5 | 对乙酰氨基酚 |
| **合计** | **34** | — |

## 使用步骤

### 1. 导入对照品库

1. 登录系统
2. 进入「对照品库」
3. 拖拽或点击选择 `drug_library_comprehensive.json`
4. 点击「导入药物列表」
5. 等待导入完成

### 2. 级联检测手动录入

1. 进入「检测分析」→「级联检测 / 手动录入」
2. 选择药物类别和参照药物
3. 从 `cascade_test_samples.json` 中复制对应参数
4. 输入 tx、λ1/λ2、A245/A250/A255/A260
5. 点击「开始级联检测」

**示例：苯巴比妥**

```json
{
  "category": "安神镇定类",
  "referenceDrug": "盐酸氯丙嗪",
  "tx": 10.821,
  "lambda1": 222.7,
  "lambda2": null,
  "areas": {
    "245": 1441107,
    "250": 983841,
    "255": 729551,
    "260": 626377
  }
}
```

### 3. 文件上传自动检测

1. 进入「检测分析」→「文件上传检测」
2. 上传 `chromatogram_phenobarbital.csv`、`chromatogram_chlorpromazine.csv` 等单峰色谱图
3. 置信度阈值保持默认 **0.7** 即可看到检出结果
4. 查看自动识别结果

| 测试文件 | 期望检出 |
|---|---|
| `chromatogram_phenobarbital.csv` | 苯巴比妥 |
| `chromatogram_chlorpromazine.csv` | 盐酸氯丙嗪 |
| `chromatogram_diazepam.csv` | 地西泮 |
| `chromatogram_metformin.csv` | 二甲双胍 |
| `chromatogram_sibutramine.csv` | 西布曲明 |
| `chromatogram_mixed.csv` | 盐酸氯丙嗪（混合样排名第一） |
| `chromatogram_sedatives.csv` | 地西泮（混合样排名第一，阈值 0.7 可能未检出，可降至 0.5 查看） |

> 注意：当前文件上传检测仍使用旧版融合模型，对单峰、干净色谱图检出效果最好。多峰混合样本可能出现排名第一但置信度略低于 0.7 的情况，此时可手动降低阈值或改用「级联检测 / 手动录入」进行 SOP 级判定。
