# 网页端药物检测系统算法分析与迁移设计

> 角色：Agent 3 — 算法分析与迁移  
> 目标：把原桌面端（tkinter）HPLC-DAD 药物检测系统的核心算法迁移到 Vue 3 + Flask + MySQL 网页端，重点补充**多药物批量检测**与**峰值图对比**所需的聚合计算逻辑。

---

## 1. 原始资料梳理

| 资料 | 关键结论 |
|---|---|
| `Drug_check/UI.py` / `trailing_funcion.py` | 原系统仅做了最简单的单峰匹配：`tx/ts` 与库中相对保留时间差值在 `[-0.001, 0.001]` 之间即命中。 |
| `贝叶斯决策算法与函数详解.docx` | 三种检测方式：①相对保留时间用**一元正态分布贝叶斯**；②峰面积比值用**多元正态分布贝叶斯**（3 维比值向量 + 3×3 协方差）；③紫外吸收光谱用**欧氏距离阈值法**。 |
| `数据库六种表结构.xlsx` | 六类表：相对保留时间参数/原始表、峰面积参数/原始表、紫外光谱参数/原始表、药物类别表、检测结果表。 |
| `对照品数据库20220402.xlsx` | 安神类示例：相对保留时间以盐酸氯丙嗪为参照；峰面积比值按 `R1=A245/A250`、`R2=A255/A250`、`R3=A260/A250` 计算；紫外光谱记录 `Lambda 最大1/2`。 |
| `导入文件标准说明.docx` | 文件名即实验编号；RRT 每 txt 1 组；峰面积每 txt 4 组（按波长递增）；光谱 xlsx 每列 1 组，多波峰用 `/` 分隔。 |
| `基于hplc-dad...说明书.docx` | 功能流程：预处理 → RRT 初筛 → 峰面积二次确认 → 紫外光谱高准确度确认 → 日志/结果导出。 |

---

## 2. 算法核心解析

### 2.1 相对保留时间检测（一元正态贝叶斯）

对某个药物类别 `C` 中的第 `k` 种药物，设其相对保留时间训练样本为 `Xk = {x1, x2, …, xN}`。

1. 计算模型参数（预训练或迭代更新）：

```
μk  = mean(Xk)
σk² = var(Xk)
```

2. 对待检峰，已知参照物保留时间 `ts`，样本保留时间 `tx`，得相对保留时间：

```
r = tx / ts
```

3. 类条件概率密度（一元正态）：

```
p(r | class=k) = (1 / sqrt(2π·σk²)) · exp( -(r-μk)² / (2·σk²) )
```

4. 各类先验概率相等：

```
P(k) = 1 / K    （K 为类别 C 中药物总数）
```

5. 后验概率：

```
P(k | r) = p(r | k) · P(k) / Σj[p(r | j) · P(j)]
```

6. 决策：保留 `P(k|r) ≥ θ_rrt` 的候选药物。

> 兼容原桌面端的快速兜底：若 `|r - μk| ≤ 0.001` 可直接标为“高置信命中”。

---

### 2.2 峰面积比值检测（多元正态贝叶斯）

对类别 `C` 的每种药物，库中保存 4 个波长下的峰面积。先转换为 3 维比值向量（以第 2 个波长为分母）：

```
给定原始面积 A = [A1, A2, A3, A4]

x = [A1/A2, A3/A2, A4/A2]
```

> 波长到分母索引可在 `drug_categories.wavelengths` 中配置，本系统默认按“第 2 个波长”作为基准。

对第 `k` 种药物：

```
μk      = E[x]          （3 维均值向量）
Σk      = Cov(x)        （3×3 协方差矩阵）
d       = 3
p(x|k)  = (2π)^(-d/2) · |Σk|^(-1/2) · exp( -1/2 · (x-μk)ᵀ · Σk⁻¹ · (x-μk) )
P(k|x)  同上贝叶斯公式
```

决策：保留 `P(k|x) ≥ θ_area` 的候选。

---

### 2.3 紫外吸收光谱检测（欧氏距离阈值）

库中记录每种药物的紫外吸收峰波长向量：

```
λk = [λk1, λk2, …, λkm]
```

待检峰解析出波长向量 `λ = [λ1, λ2, …, λm]`（多波峰用 `/` 分隔后排序）。

```
d(λ, λk) = sqrt( Σi(λi - λki)² )
```

决策：

```
if d(λ, λk) ≤ θ_uv:
    score_uv(k) = 1    （命中）
else:
    score_uv(k) = 0
```

> 紫外光谱在原系统中被描述为“准确度最高”，因此作为强证据使用。

---

### 2.4 模型参数迭代更新（`proc`）

当新增一组实验数据时，按类别/药物增量更新参数，避免全量重训。

#### 2.4.1 相对保留时间

```
N'  = N + 1
μ'  = (N·μ + x) / (N + 1)
σ'² = (N/(N+1))·σ² + (N/(N+1)²)·(x - μ)²
```

#### 2.4.2 峰面积比值（多元）

```
N'   = N + 1
μ'   = (N·μ + x) / (N + 1)
Σ'   = (N/(N+1))·Σ + (N/(N+1)²)·(x - μ)(x - μ)ᵀ
```

#### 2.4.3 紫外吸收光谱

```
N'  = N + 1
μ'  = (N·μ + x) / (N + 1)
```

紫外模型不维护协方差，仅维护均值向量用于距离比对。

---

## 3. 数据模型设计

为支持上述算法，数据库至少包含以下表。完整 DDL 见 `backend/sql/schema.sql`。

| 表名 | 用途 |
|---|---|
| `drug_categories` | 药物类别、默认参照物、峰面积检测波长列表 |
| `reference_drugs` | 对照品库：每种药物的保留时间、紫外波长、峰面积比值等 |
| `rrt_model_params` | 相对保留时间贝叶斯模型参数（N, μ, variance） |
| `peak_area_model_params` | 峰面积比值多元正态模型参数（N, μ, Σ） |
| `uv_spectrum_model_params` | 紫外光谱模型参数（N, μ 波长向量） |
| `raw_retention_times` | 导入的相对保留时间原始实验数据 |
| `raw_peak_areas` | 导入的峰面积原始实验数据 |
| `raw_uv_spectra` | 导入的紫外光谱原始实验数据 |
| `detection_tasks` | 批量检测任务批次 |
| `detection_results` | 每峰、每药物的检测结果与置信度 |
| `detection_peak_matches` | 峰值图对比：样品峰与候选对照品峰的匹配明细 |

---

## 4. 算法详细设计

### 4.1 输入数据结构

```python
class Peak:
    peak_index: int           # 峰序号
    rt: float | None          # 保留时间 tx
    areas: list[float]        # 各波长峰面积，长度 = len(category.wavelengths)
    lambda_maxima: list[float] # 紫外吸收峰波长，可能为空

class Sample:
    sample_id: str            # 实验编号，通常来自文件名
    category_id: int          # 药物类别
    reference_rt: float       # 参照物保留时间 ts
    peaks: list[Peak]
```

### 4.2 单峰检测流程

```
单峰检测(peak, category_id, reference_rt, params):
    1. 若 reference_rt 为空，取 drug_categories.reference_drug_id 对应 reference_drugs.retention_time
    2. r = peak.rt / reference_rt
    3. score_rrt = classify_rrt(r, category_id)
    4. score_area = classify_peak_area(peak.areas, category_id)
    5. score_uv  = classify_uv(peak.lambda_maxima, category_id)
    6. 对类别中每种药物 k:
           final_score = combine(score_rrt[k], score_area[k], score_uv[k], weights)
           若 final_score ≥ θ_overall 且至少有一种可用模态得分 ≥ 各自阈值:
               将该药物加入候选列表
    7. 返回候选列表（含各项分数、结论）
```

#### 组合规则（默认）

```
weights = {rrt: 0.25, area: 0.35, uv: 0.40}

若某模态缺失，其权重置 0，其余归一化。
final_score = Σ(weight_i · score_i) / Σ(weight_i)
```

> UV 权重最高，因为它准确；峰面积次之；RRT 只做初筛。

#### 兼容原系统的“严格交集”模式

```
结论 = 命中，当且仅当：
  (rrt 命中) 且 (area 命中) 且 (uv 未提供 或 uv 命中)
```

前端可让用户选择“严格模式 / 加权模式”。

### 4.3 多药物批量检测流程

```
批量检测(batch_upload):
    1. 解析上传文件，生成 list[Sample]
    2. 创建 detection_tasks 记录
    3. 对每个 Sample:
         对 Sample 中每个 Peak:
             candidates = 单峰检测(peak, sample.category_id, sample.reference_rt)
             将 candidates 写入 detection_results（含 score_rrt / score_area / score_uv / final_score）
    4. 汇总报告:
         - 每个 sample 检测到的药物列表
         - 每种药物的最高置信度
         - 未命中/疑似命中/确认命中分类
    5. 返回 task_id 与汇总结果
```

#### 汇总规则

- **确认命中**：同一药物在 RRT、峰面积、紫外三个模态中至少两个命中，或加权最终分 `≥ 0.8`。
- **疑似命中**：仅一个模态命中，或 `0.5 ≤ final_score < 0.8`。
- **未命中**：无候选药物。

### 4.4 峰值图对比聚合计算

#### 4.4.1 保留时间分布直方图

用途：把一批样品中所有峰的保留时间与对照品期望保留时间对比。

```
聚合_RRT_直方图(sample_list, category_id, bin_width=0.2):
    ref_drugs = 查询 reference_drugs 中 category_id 下所有药物
    series_ref = []
    对每种药物 d:
        expected_abs_rt = d.relative_retention_time * reference_rt
        series_ref.append({drug: d.name, rt: expected_abs_rt})

    sample_peaks = [p.rt for s in sample_list for p in s.peaks if p.rt]
    bins = floor(min_rt / bin_width) .. ceil(max_rt / bin_width)
    counts = 统计每个 bin 内 sample_peaks 数量

    返回 {bins, counts, reference_lines: series_ref}
```

#### 4.4.2 紫外/峰面积光谱对比曲线

用途：对某个疑似药物，把样品峰的平均光谱与对照品光谱叠加展示。

```
聚合_光谱对比(sample_peaks, drug_name, category_id):
    ref = 查询 reference_drugs (drug_name, category_id)
    ref_wavelengths = category.wavelengths
    ref_intensity = ref.peak_area_raw 或从 peak_area_ratios 反推为相对强度

    target_peaks = sample_peaks 中 final_score ≥ θ 且包含 drug_name 的峰
    avg_intensity = 对 target_peaks 的 areas 按每个波长求平均
    individual = 每个峰的光谱曲线（用于透明度叠加）

    返回 {
        wavelengths: ref_wavelengths,
        reference: ref_intensity,
        sample_avg: avg_intensity,
        sample_curves: individual
    }
```

#### 4.4.3 概率柱状图

```
聚合_概率图(detection_results, top_n=5):
    按 (sample_id, peak_index) 分组
    取每个峰置信度最高的 top_n 种药物
    返回 ECharts 所需的 category/series 结构
```

---

## 5. 伪代码

以下伪代码可直接作为 Flask Service / `backend/app/algorithm.py` 的骨架。

### 5.1 导入文件解析

```python
def parse_rrt_txt(file_path: str) -> Sample:
    """相对保留时间 txt：文件名 = sample_id，每行 '(index, tx)'。"""
    sample_id = basename_noext(file_path)
    peaks = []
    with open(file_path, encoding='gbk') as f:   # 原样本为 GBK
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            idx, tx = line.split(',')
            peaks.append(Peak(peak_index=int(idx), rt=float(tx), areas=[], lambda_maxima=[]))
    return Sample(sample_id=sample_id, peaks=peaks)


def parse_peak_area_txt(file_path: str, category_wavelengths: list) -> Sample:
    """峰面积 txt：包含 4 个波长段，每段按波长递增顺序。"""
    sample_id = basename_noext(file_path)
    peak_areas = defaultdict(lambda: [0.0] * len(category_wavelengths))
    section_idx = -1
    with open(file_path, encoding='gbk') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if 'PDA' in line:          # 遇到波长标识，进入下一段
                section_idx += 1
                continue
            if line.startswith('#') or line.startswith('('):
                continue
            parts = line.split(',')
            if len(parts) >= 2 and parts[0].isdigit():
                pidx = int(parts[0])
                area = float(parts[1])
                if 0 <= section_idx < len(category_wavelengths):
                    peak_areas[pidx][section_idx] = area
    peaks = [Peak(peak_index=i, rt=None, areas=a, lambda_maxima=[])
             for i, a in sorted(peak_areas.items())]
    return Sample(sample_id=sample_id, peaks=peaks)


def parse_uv_xlsx(file_path: str) -> list[Sample]:
    """紫外 xlsx：第二列起每列一个 sample，每行一个峰，多波长用 '/' 分隔。"""
    samples = []
    ws = load_workbook(file_path).active
    header = [cell.value for cell in ws[1]]
    for col_idx in range(1, ws.max_column):
        sample_id = header[col_idx]
        peaks = []
        for row_idx in range(2, ws.max_row + 1):
            cell = ws.cell(row=row_idx, column=col_idx + 1).value
            if not cell:
                continue
            lambdas = [float(x.strip()) for x in str(cell).split('/') if x.strip()]
            peaks.append(Peak(peak_index=row_idx - 1, rt=None, areas=[], lambda_maxima=lambdas))
        samples.append(Sample(sample_id=sample_id, peaks=peaks))
    return samples
```

### 5.2 三个核心分类器

```python
import numpy as np
from scipy.stats import multivariate_normal

def classify_rrt(r: float, category_id: int) -> dict[str, float]:
    rows = db.query("""
        SELECT d.name, p.mean, p.variance
        FROM rrt_model_params p
        JOIN reference_drugs d ON p.drug_id = d.id
        WHERE d.category_id = %s
    """, category_id)
    likelihoods = {}
    for drug, mu, var in rows:
        var = max(var, 1e-12)
        likelihoods[drug] = np.exp(-(r - mu) ** 2 / (2 * var)) / np.sqrt(2 * np.pi * var)
    total = sum(likelihoods.values())
    return {k: v / total for k, v in likelihoods.items()} if total > 0 else {}


def classify_peak_area(areas: list[float], category_id: int) -> dict[str, float]:
    if len(areas) < 4:
        return {}
    base = areas[1] if areas[1] != 0 else 1e-9
    x = np.array([areas[0] / base, areas[2] / base, areas[3] / base])

    rows = db.query("""
        SELECT d.name, p.mean_vector, p.covariance_matrix
        FROM peak_area_model_params p
        JOIN reference_drugs d ON p.drug_id = d.id
        WHERE d.category_id = %s
    """, category_id)
    likelihoods = {}
    for drug, mean_vector, covariance_matrix in rows:
        mu = np.array(json.loads(mean_vector), dtype=float)
        sigma = rebuild_symmetric_matrix(json.loads(covariance_matrix))  # 6 个元素 -> 3x3
        try:
            likelihoods[drug] = multivariate_normal.pdf(x, mean=mu, cov=sigma, allow_singular=True)
        except Exception:
            likelihoods[drug] = 0.0
    total = sum(likelihoods.values())
    return {k: v / total for k, v in likelihoods.items()} if total > 0 else {}


def classify_uv(lambdas: list[float], category_id: int) -> dict[str, float]:
    if not lambdas:
        return {}
    x = np.array(sorted(lambdas))
    rows = db.query("""
        SELECT d.name, p.lambda_max_1, p.lambda_max_2
        FROM uv_spectrum_model_params p
        JOIN reference_drugs d ON p.drug_id = d.id
        WHERE d.category_id = %s
    """, category_id)
    scores = {}
    for drug, lm1, lm2 in rows:
        mu = np.array([v for v in (lm1, lm2) if v is not None], dtype=float)
        if len(mu) == 0 or len(mu) != len(x):
            scores[drug] = 0.0
            continue
        dist = np.linalg.norm(x - mu)
        scores[drug] = 1.0 if dist <= theta_uv else 0.0
    return scores
```

### 5.3 单峰组合与批量检测

```python
DEFAULT_WEIGHTS = {'rrt': 0.25, 'area': 0.35, 'uv': 0.40}

def combine_scores(score_rrt, score_area, score_uv, weights=DEFAULT_WEIGHTS):
    vals, w = [], []
    if score_rrt is not None:
        vals.append(score_rrt); w.append(weights['rrt'])
    if score_area is not None:
        vals.append(score_area); w.append(weights['area'])
    if score_uv is not None:
        vals.append(score_uv); w.append(weights['uv'])
    if not vals:
        return 0.0
    return sum(v * wt for v, wt in zip(vals, w)) / sum(w)


def detect_peak(peak: Peak, category_id: int, reference_rt: float,
                theta_rrt=0.6, theta_area=0.6, theta_uv=2.0, theta_overall=0.5):
    if reference_rt is None or reference_rt <= 0:
        raise ValueError("参照物保留时间无效")

    r = peak.rt / reference_rt if peak.rt else None
    scores_rrt = classify_rrt(r, category_id) if r is not None else {}
    scores_area = classify_peak_area(peak.areas, category_id) if peak.areas else {}
    scores_uv = classify_uv(peak.lambda_maxima, category_id) if peak.lambda_maxima else {}

    drugs = set(scores_rrt) | set(scores_area) | set(scores_uv)
    results = []
    for drug in drugs:
        s_rrt = scores_rrt.get(drug)
        s_area = scores_area.get(drug)
        s_uv = scores_uv.get(drug)
        final = combine_scores(s_rrt, s_area, s_uv)

        passed = (final >= theta_overall) and \
                 ((s_rrt is not None and s_rrt >= theta_rrt) or
                  (s_area is not None and s_area >= theta_area) or
                  (s_uv is not None and s_uv == 1.0))
        if passed:
            results.append({
                'drug': drug,
                'score_rrt': s_rrt,
                'score_area': s_area,
                'score_uv': s_uv,
                'final_score': final,
                'conclusion': 'confirmed' if final >= 0.8 else 'suspect'
            })
    return sorted(results, key=lambda x: x['final_score'], reverse=True)


def batch_detect(samples: list[Sample]) -> dict:
    task_id = db.insert_detection_task()
    summary = defaultdict(lambda: {'max_score': 0.0, 'peaks': []})
    for sample in samples:
        for peak in sample.peaks:
            candidates = detect_peak(peak, sample.category_id, sample.reference_rt)
            for c in candidates:
                db.insert_result(task_id, sample.sample_id, peak.peak_index, c)
                s = summary[c['drug']]
                s['max_score'] = max(s['max_score'], c['final_score'])
                s['peaks'].append({'sample': sample.sample_id, 'peak': peak.peak_index})
    return {'task_id': task_id, 'summary': dict(summary)}
```

### 5.4 峰值图聚合

```python
def aggregate_rt_histogram(samples: list[Sample], category_id: int, reference_rt: float,
                           bin_width: float = 0.2):
    drugs = db.query_reference_drugs(category_id)
    ref_lines = [{'drug': d.name,
                  'rt': d.relative_retention_time * reference_rt} for d in drugs]

    values = [p.rt for s in samples for p in s.peaks if p.rt]
    mn, mx = min(values), max(values)
    bins = np.arange(floor(mn / bin_width) * bin_width,
                     ceil(mx / bin_width) * bin_width + bin_width,
                     bin_width)
    counts, _ = np.histogram(values, bins=bins)
    return {'bins': bins.tolist(), 'counts': counts.tolist(), 'reference_lines': ref_lines}


def aggregate_spectrum_overlay(drug_name: str, category_id: int,
                               sample_peaks: list[Peak], theta: float = 0.5):
    cat = db.query_category(category_id)
    ref = db.query_reference_drugs(drug_name, category_id)
    ref_intensity = ref.peak_area_raw or [1.0] * len(cat.wavelengths)

    target = [p for p in sample_peaks if p.areas and peak_has_drug(p, drug_name, theta)]
    if not target:
        return None

    avg = np.mean([p.areas for p in target], axis=0).tolist()
    individual = [p.areas for p in target]
    return {
        'wavelengths': cat.wavelengths,
        'reference': ref_intensity,
        'sample_avg': avg,
        'sample_curves': individual
    }


def aggregate_probability_chart(results: list[dict], top_n: int = 5):
    """results: detection_results 行列表。"""
    grouped = defaultdict(list)
    for r in results:
        key = (r['sample_id'], r['peak_index'])
        grouped[key].append(r)
    series = []
    for key, rows in grouped.items():
        rows = sorted(rows, key=lambda x: x['final_score'], reverse=True)[:top_n]
        series.append({
            'sample': key[0], 'peak': key[1],
            'drugs': [r['drug_name'] for r in rows],
            'scores': [float(r['final_score']) for r in rows]
        })
    return series
```

### 5.5 模型参数迭代更新

```python
def update_rrt_model(drug_id: int, x: float):
    row = db.query_one("""
        SELECT sample_count, mean, variance FROM rrt_model_params WHERE drug_id = %s
    """, drug_id)
    N, mu, var = row['sample_count'], row['mean'], row['variance']
    Np = N + 1
    mu_p = (N * mu + x) / Np
    var_p = (N / Np) * var + (N / (Np ** 2)) * ((x - mu) ** 2)
    db.execute("""
        UPDATE rrt_model_params
        SET sample_count=%s, mean=%s, variance=%s, std_dev=SQRT(%s)
        WHERE drug_id=%s
    """, Np, mu_p, var_p, var_p, drug_id)


def update_peak_area_model(drug_id: int, x: np.ndarray):
    row = db.query_one("""
        SELECT sample_count, mean_vector, covariance_matrix
        FROM peak_area_model_params WHERE drug_id = %s
    """, drug_id)
    N, mu, sigma = row['sample_count'], np.array(json.loads(row['mean_vector'])), np.array(json.loads(row['covariance_matrix']))
    Np = N + 1
    mu_p = (N * mu + x) / Np
    diff = (x - mu).reshape(-1, 1)
    sigma_p = (N / Np) * sigma + (N / (Np ** 2)) * (diff @ diff.T)
    db.execute("""
        UPDATE peak_area_model_params
        SET sample_count=%s, mean_vector=%s, covariance_matrix=%s
        WHERE drug_id=%s
    """, Np, json.dumps(mu_p.tolist()), json.dumps(sigma_p.tolist()), drug_id)


def update_uv_model(drug_id: int, x: np.ndarray):
    row = db.query_one("""
        SELECT sample_count, lambda_max_1, lambda_max_2
        FROM uv_spectrum_model_params WHERE drug_id = %s
    """, drug_id)
    N = row['sample_count']
    mu = np.array([v for v in (row['lambda_max_1'], row['lambda_max_2']) if v is not None])
    Np = N + 1
    mu_p = (N * mu + x) / Np
    lm1, lm2 = (mu_p.tolist() + [None, None])[:2]
    db.execute("""
        UPDATE uv_spectrum_model_params
        SET sample_count=%s, lambda_max_1=%s, lambda_max_2=%s
        WHERE drug_id=%s
    """, Np, lm1, lm2, drug_id)
```

---

## 6. Flask 接口规划（算法侧）

| 接口 | 输入 | 输出 | 说明 |
|---|---|---|---|
| `POST /api/detect/single` | `{category_id, reference_rt, peaks: [...]}` | 单峰候选列表 | 单样品即时检测 |
| `POST /api/detect/tasks` | `multipart/form-data` 文件列表 + category_id | `task_id`、汇总报告 | 多药物批量检测入口 |
| `GET /api/detect/tasks/{id}` | task_id | 完整结果 | 查询批次 |
| `GET /api/charts/rt_histogram` | task_id, bin_width? | bins / counts / ref_lines | 保留时间对比 |
| `GET /api/charts/spectrum_overlay` | task_id, drug_name | wavelengths / ref / sample_avg / curves | 峰面积/光谱叠加 |
| `GET /api/charts/probability` | task_id | 每峰 topN 概率 | 概率柱状图 |
| `POST /api/models/update` | `{data_type, category_id, experiment_id}` | success/fail | 触发 `proc` 迭代更新 |

---

## 7. 阈值与超参数

| 参数 | 默认值 | 可调方式 | 说明 |
|---|---|---|---|
| `θ_rrt` | 0.60 | 按类别配置 | RRT 后验概率阈值 |
| `θ_area` | 0.60 | 按类别配置 | 峰面积后验概率阈值 |
| `θ_uv` | 2.0 nm | 按类别配置 | 紫外欧氏距离阈值 |
| `θ_overall` | 0.50 | 全局 | 加权最终分阈值 |
| RRT 兜底容差 | 0.001 | 全局 | 兼容原桌面版 |
| 组合权重 | `rrt:0.25, area:0.35, uv:0.40` | 全局 | 加权模式 |

建议前端提供“参数设定”页面，保存到 `system_settings` 表。

---

## 8. 单元测试思路

### 8.1 解析层测试

- 分别用 GBK 编码的 RRT txt、峰面积 txt、紫外 xlsx 作为输入，断言解析出的 `Peak` 数量、字段类型正确。
- 测试空文件、缺波长段、面积为零、多波峰 `/` 分隔等异常输入。

### 8.2 分类器测试

- **RRT 分类器**：构造一个类别含 3 种药物，参数已知；输入 `r = μk`，断言该药物后验概率接近 1.0。
- **峰面积分类器**：构造已知的 `mu`、`Σ`；输入 `x = mu`，断言对应药物后验概率最高。
- **UV 分类器**：构造参考波长 `[220.4, 310.5]`；输入 `[220.4, 310.5]`，断言命中；输入 `[200.0, 300.0]` 大于阈值，断言未命中。

### 8.3 组合逻辑测试

- RRT 命中、area 命中、UV 命中 → 最终结论 `confirmed`。
- 仅 RRT 命中 → `suspect`。
- 全部缺失 → 空结果。

### 8.4 批量检测测试

- 上传 2 个文件、共 5 个峰，验证 `detection_tasks` 与 `detection_results` 写入行数正确。
- 验证汇总报告中每种药物的 `max_score` 取的是最高值。

### 8.5 聚合图表测试

- 直方图 bin 边界、reference line 位置是否正确。
- 光谱对比中 `sample_avg` 是否等于目标峰面积的均值。

### 8.6 模型更新测试

- 对已知模型增加一个新样本，用解析公式手算 `μ'`、`σ²'`，与函数输出比对。

---

## 9. 性能与精度考虑

1. **矩阵求逆稳定**：`multivariate_normal.pdf` 内部处理；若协方差接近奇异，可加入极小正则项 `Σ + εI`。
2. **批量大文件**：峰面积 txt 可能很长，解析应使用流式读取，避免一次性加载大列表。
3. **重复峰过滤**：同一样品中保留时间非常接近的峰（< 0.05 min）可视为同一个峰，避免重复报告。
4. **UV 维度不一致**：当样品峰与参考库波长数量不一致时，默认判为不匹配；可在配置中开启“最近邻匹配”作为实验功能。
5. **模型参数冷启动**：若某药物模型 `N=0`，应fallback到 `reference_drugs` 中的静态对照品库数据（μ=reference 值，variance 取类别平均或一个缺省小值）。

---

## 10. 遗留问题与待确认事项

1. **公式图像缺失**：`贝叶斯决策算法与函数详解.docx` 中的公式为 WMF 图片，已按常规统计学习理论还原。若实际实现与原 WMF 公式有出入，需要核对后修正第 2 节公式。
2. **峰面积比值分母**：本设计默认以“第 2 个波长”作为分母（与安神类示例一致）。若其他类别分母不同，请在 `drug_categories` 中增加 `denominator_index` 字段。
3. **UV 距离阈值单位**：`θ_uv` 默认 2.0 nm，需与实验人员确认仪器波长精度。
4. **组合模式选择**：提供了“加权模式”和“严格交集模式”，最终采用哪种需产品/业务确认。
5. **导入文件编码**：样本文件为 GBK，网页上传文件可能为 UTF-8，解析时应优先尝试 UTF-8，失败再回退 GBK。
6. **药物类别与参照物**：部分类别在 `数据库六种表结构.xlsx` 中未填写标准参照物，需要补充完整。
7. **模型迭代触发时机**：`proc` 是在每次导入后立即触发，还是由管理员手动触发？建议提供“导入并更新模型”和“仅导入不更新”两个按钮。
