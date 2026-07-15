# 药物检测系统数据库设计说明

## 1. 设计目标

将原桌面端（Python + tkinter + 阿里云 MySQL）的 **基于 HPLC-DAD 方法的数字对照品库快速筛查系统** 改造为网页端（Vue 3 + Flask + MySQL）。本设计在保留原系统"六种表结构"核心业务语义的基础上，针对以下需求进行扩展：

- 支持 **多药物批量检测**（`detection_tasks` + `detection_results`）。
- 支持 **峰值图对比**（`detection_peak_matches`）。
- 保留原系统的三种检测模型：相对保留时间、峰面积比值、紫外吸收光谱。
- 保留用户登录、数据导入（txt/xlsx）、数据库管理、日志生成等功能。

## 2. 原始资料关键信息摘要

| 资料 | 关键内容 |
|------|----------|
| `数据库六种表结构.xlsx` | 原系统包含：相对保留时间参数、峰面积参数、紫外吸收光谱参数、药物类别、保留时间原始数据、峰面积原始数据、紫外吸收原始数据、检测记录/结论、待定物质检测等逻辑表。 |
| `对照品数据库20220402.xlsx` | 当前仅提供 **安神镇定类 9 种** 对照品：咪达唑仑、苯巴比妥、盐酸氯丙嗪（参照物）、艾司唑仑、奥沙西泮、阿普唑仑、三唑仑、氯硝西泮、地西泮。含相对保留时间、Lambda 最大吸收、多波长峰面积及比值 R1/R2/R3。 |
| `导入文件标准说明.docx` | 文件名即试验编号；保留时间 txt 每组 1 个文件；峰面积 txt 每组 4 个波长数据；光谱吸收 xlsx 每列一组试验，多峰用 `/` 分隔。 |
| `贝叶斯决策算法与函数详解.docx` | 相对保留时间用单变量正态分布（μ, σ²）；峰面积用多维正态分布（μ 向量、Σ 协方差矩阵）；紫外吸收用波长距离/阈值法；模型参数随新样本迭代更新。 |
| `基于hplc-dad...说明书.docx` | 系统包含 8 类样品、96 种化学药物；药物类别编码为 1-8；检测流程包含参照物确定、相对保留时间、峰面积、紫外吸收光谱、日志生成。 |
| 源码 `Drug_check/` | 源码中出现表名 `hold_time`、`relative_retention_time_yslbq`、`medicine_name`，验证了保留时间、相对保留时间、药物名称是原数据库核心表。 |

## 3. 数据库选型与约定

- **数据库**：MySQL 8.0（与原系统"阿里云数据库 8.0"一致）。
- **数据库名**：`drug_check`。
- **字符集**：`utf8mb4_unicode_ci`，支持中文及特殊符号。
- **存储引擎**：`InnoDB`，支持事务与外键。
- **时间字段**：统一使用 `created_at` / `updated_at`。
- **可变维度数据**：使用 `JSON` 类型存储波长列表、峰面积向量、协方差矩阵等，避免频繁改表。
- **幂等性**：脚本使用 `CREATE TABLE IF NOT EXISTS` 与 `INSERT ... ON DUPLICATE KEY UPDATE`，可重复执行。
- **软删除**：本系统数据具有追溯价值，不采用软删除；通过 `status` 字段控制停用/启用。

## 4. ER 图（文字描述）

```
users ─┬─ raw_experiments ─┬─ raw_retention_times
       │                   ├─ raw_peak_areas
       │                   └─ raw_uv_spectra
       ├─ detection_tasks ─┬─ detection_results ─┬─ detection_peak_matches
       │                   │                     └─ reference_drugs
       └─ operation_logs

drug_categories ←── reference_drugs
       │                  ↑
       │                  ├── rrt_model_params
       │                  ├── peak_area_model_params
       │                  └── uv_spectrum_model_params
       └──────────────────┘

system_configs
```

## 5. 表结构说明

### 5.1 用户与权限

#### `users` 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT UNSIGNED PK | 用户ID |
| `username` | VARCHAR(64) UNIQUE | 登录账号 |
| `password_hash` | VARCHAR(255) | 密码哈希（bcrypt） |
| `real_name` | VARCHAR(64) | 真实姓名 |
| `role` | ENUM | `admin` 管理员 / `operator` 操作员 |
| `status` | TINYINT | 0-禁用，1-启用 |
| `last_login_at` | DATETIME | 最后登录时间 |

### 5.2 对照品与模型参数（对应原六种表结构）

#### `drug_categories` 药物类别表

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | VARCHAR(32) UNIQUE | 类别编码，与原系统一致：1-8 |
| `name` | VARCHAR(64) | 类别名称 |
| `reference_drug_id` | INT UNSIGNED FK | 默认标准参照物 |
| `wavelengths` | JSON | 该类检测波长列表，如 `[245,250,255,260]` |

#### `reference_drugs` 对照品标准药物表

| 字段 | 类型 | 说明 |
|------|------|------|
| `category_id` | INT UNSIGNED FK | 所属类别 |
| `name` | VARCHAR(128) | 药物中文名 |
| `name_en` | VARCHAR(128) | 药物英文名 |
| `cas_no` | VARCHAR(64) | CAS 号 |
| `is_reference` | TINYINT | 是否为参照物 |

#### `rrt_model_params` 相对保留时间模型参数表

对应原"相对保留时间表"，存储贝叶斯模型参数。

| 字段 | 类型 | 说明 |
|------|------|------|
| `drug_id` | INT UNSIGNED FK | 药物 |
| `sample_count` | INT UNSIGNED | 训练样本数 N |
| `mean` | DOUBLE | 数学期望 μ |
| `variance` | DOUBLE | 方差 σ² |
| `std_dev` | DOUBLE | 标准差 σ |

#### `peak_area_model_params` 峰面积比值模型参数表

对应原"峰面积表"，存储多维正态分布参数。

| 字段 | 类型 | 说明 |
|------|------|------|
| `drug_id` | INT UNSIGNED FK | 药物 |
| `sample_count` | INT UNSIGNED | 训练样本数 N |
| `wavelengths` | JSON | 波长列表 |
| `mean_vector` | JSON | 期望比值向量 μ |
| `covariance_matrix` | JSON | 协方差矩阵 Σ |

#### `uv_spectrum_model_params` 紫外吸收光谱模型参数表

对应原"紫外吸收光谱表"。

| 字段 | 类型 | 说明 |
|------|------|------|
| `drug_id` | INT UNSIGNED FK | 药物 |
| `sample_count` | INT UNSIGNED | 训练样本数 N |
| `peak_count` | INT UNSIGNED | 色谱峰个数 |
| `lambda_max_1` / `lambda_max_2` | DOUBLE | 最大吸收波长 |
| `absorption_data` | JSON | 吸收数据，如 `{A245,A250,R1,A255,R2,A260,R3}` |

### 5.3 原始实验数据（对应原三种 xxx_data 库）

#### `raw_experiments` 原始实验记录表

| 字段 | 类型 | 说明 |
|------|------|------|
| `experiment_no` | VARCHAR(64) UNIQUE | 实验编号（文件名） |
| `category_id` | INT UNSIGNED FK | 药物类别 |
| `reference_drug_id` | INT UNSIGNED FK | 选用的参照物 |
| `reference_retention_time` | DOUBLE | 参照物保留时间 ts |
| `operator_id` | INT UNSIGNED FK | 操作人 |
| `sample_location` | VARCHAR(128) | 采样地点 |
| `file_name` / `file_path` | VARCHAR | 原始文件信息 |

#### `raw_retention_times` 原始保留时间数据表

| 字段 | 类型 | 说明 |
|------|------|------|
| `experiment_id` | INT UNSIGNED FK | 实验 |
| `peak_index` | INT UNSIGNED | 峰序号 |
| `retention_time` | DOUBLE | 保留时间 tx |
| `relative_retention_time` | DOUBLE | 相对保留时间 tx/ts |

#### `raw_peak_areas` 原始峰面积数据表

| 字段 | 类型 | 说明 |
|------|------|------|
| `experiment_id` | INT UNSIGNED FK | 实验 |
| `peak_index` | INT UNSIGNED | 峰序号 |
| `wavelength` | INT UNSIGNED | 波长 nm |
| `area` | DOUBLE | 峰面积 |

#### `raw_uv_spectra` 原始紫外吸收光谱数据表

| 字段 | 类型 | 说明 |
|------|------|------|
| `experiment_id` | INT UNSIGNED FK | 实验 |
| `sample_no` | VARCHAR(64) | 样品编号（xlsx 列头） |
| `peak_index` | INT UNSIGNED | 峰序号 |
| `lambda_values` | JSON | 最大吸收波长数组，多峰存列表 |

### 5.4 批量检测与结果（新增与扩展）

#### `detection_tasks` 检测任务表

支持多药物批量检测，一次任务可包含多个样品。

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_no` | VARCHAR(64) UNIQUE | 任务编号 |
| `name` | VARCHAR(128) | 任务名称 |
| `category_id` | INT UNSIGNED FK | 检测类别 |
| `reference_drug_id` | INT UNSIGNED FK | 参照物 |
| `reference_retention_time` | DOUBLE | 参照保留时间 |
| `operator_id` | INT UNSIGNED FK | 创建人 |
| `status` | TINYINT | 0-待检测，1-检测中，2-完成，3-失败 |
| `threshold_rrt` | DOUBLE | RRT 概率阈值，默认 0.6 |
| `threshold_peak_area` | DOUBLE | 峰面积概率阈值，默认 0.6 |
| `threshold_uv` | DOUBLE | UV 距离阈值，默认 2.0 nm |

#### `detection_results` 检测结果表

对应原"待定物质检测/结论"表。

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | INT UNSIGNED FK | 所属任务 |
| `sample_no` | VARCHAR(64) | 样品编号 |
| `peak_index` | INT UNSIGNED | 峰序号 |
| `detected_drug_id` | INT UNSIGNED FK | 检出的药物 |
| `detection_method` | ENUM | `rrt` / `peak_area` / `uv_spectrum` / `combined` |
| `confidence` | DOUBLE | 置信度/后验概率 |
| `conclusion` | VARCHAR(255) | 结论文本 |
| `is_positive` | TINYINT | 是否阳性 |

#### `detection_peak_matches` 检测峰值匹配明细表

专门支持峰值图对比功能。

| 字段 | 类型 | 说明 |
|------|------|------|
| `result_id` | INT UNSIGNED FK | 关联检测结果 |
| `peak_index` | INT UNSIGNED | 样品峰序号 |
| `sample_peak_rt` | DOUBLE | 样品峰保留时间 |
| `ref_drug_id` | INT UNSIGNED FK | 比对的对照品 |
| `ref_peak_rt` | DOUBLE | 对照品保留时间 |
| `similarity_score` | DOUBLE | 相似度得分 |
| `matched_wavelengths` | JSON | 匹配到的波长及面积对比 |

### 5.5 配置与日志

#### `system_configs` 系统配置表

| 字段 | 类型 | 说明 |
|------|------|------|
| `config_key` | VARCHAR(100) UNIQUE | 配置键 |
| `config_value` | TEXT | 配置值 |
| `description` | VARCHAR(255) | 说明 |

#### `operation_logs` 操作日志表

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | INT UNSIGNED FK | 操作用户 |
| `action` | VARCHAR(100) | 操作类型 |
| `target_type` | VARCHAR(64) | 操作对象类型 |
| `target_id` | VARCHAR(64) | 操作对象 id |
| `detail` | TEXT | 详情 |
| `ip_address` | VARCHAR(64) | IP 地址 |

## 6. 与原六种表结构的对应关系

| 原表/区域 | 新表 | 说明 |
|-----------|------|------|
| 药物类别 | `drug_categories` | 新增 `reference_drug_id`、`wavelengths` |
| 药物名称/对照品 | `reference_drugs` | 新增英文名、CAS、是否参照物 |
| 相对保留时间表 | `rrt_model_params` | 单变量正态参数 |
| 峰面积表 | `peak_area_model_params` | 多维正态参数，JSON 存储向量/矩阵 |
| 紫外吸收光谱表 | `uv_spectrum_model_params` | JSON 存储多波长数据 |
| 保留时间原始数据 | `raw_retention_times` | 按峰拆行，便于查询与绘图 |
| 峰面积原始数据 | `raw_peak_areas` | 按峰+波长拆行 |
| 光谱吸收原始数据 | `raw_uv_spectra` | JSON 存储多吸收峰 |
| 检测记录/结论 | `detection_tasks` + `detection_results` | 拆分为任务与结果 |
| 待定物质检测 | `detection_results` | 每条记录对应一个样品峰 |

## 7. 新增需求实现

### 7.1 多药物批量检测

- 通过 `detection_tasks` 表组织一次检测任务。
- 一个任务关联一个药物类别和参照物，可包含多个样品（`sample_no`）。
- `detection_results` 按 `task_id + sample_no + peak_index` 唯一标识每个样品每个峰的检测结果。

### 7.2 峰值图对比

- `detection_peak_matches` 记录样品峰与候选对照品峰的匹配关系。
- `sample_peak_rt` 与 `ref_peak_rt` 用于在同一坐标系下绘制保留时间对比图。
- `matched_wavelengths` 可存储各波长下的峰面积对比，用于多波长峰面积比值图。

## 8. 种子数据说明

`backend/sql/schema.sql` 已包含以下种子数据：

1. 一个管理员账号（默认密码 `admin123`，部署前建议修改）。
2. 8 个药物类别（编码 1-8，与原系统一致）。
3. 安神镇定类 9 种对照品药物（来自 `对照品数据库20220402.xlsx`）。
4. 盐酸氯丙嗪设为安神镇定类默认参照物。
5. 9 种药物的相对保留时间模型参数（单样本，方差为 0，需后续训练数据更新）。
6. 9 种药物的峰面积比值初始参数（`mean_vector` 来自对照品数据库中的 R1/R2/R3，`covariance_matrix` 为空，需后续训练拟合）。
7. 9 种药物的紫外吸收光谱完整初始参数（`lambda_max` + `absorption_data`）。
8. 默认阈值配置：RRT/峰面积/UV 阈值及组合权重 `weight_rrt` / `weight_peak_area` / `weight_uv`。

**注意**：
- 峰面积模型参数目前仅有单样本均值，协方差矩阵为空。需在实际使用中通过导入多批次训练数据后，由算法模块拟合并写入 `covariance_matrix`。
- 其他 7 类药物（减肥类、降糖类等）的对照品及模型参数待补充。

## 9. 使用说明

### 9.1 创建数据库

```sql
CREATE DATABASE drug_check DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE drug_check;
SOURCE backend/sql/schema.sql;
```

### 9.2 后端连接配置（Flask 示例）

```python
SQLALCHEMY_DATABASE_URI = (
    "mysql+pymysql://user:password@localhost:3306/drug_check?charset=utf8mb4"
)
```

### 9.3 关键查询示例

**查询某类别下所有对照品及其相对保留时间参数：**

```sql
SELECT d.name, p.mean, p.std_dev
FROM reference_drugs d
JOIN rrt_model_params p ON d.id = p.drug_id
JOIN drug_categories c ON d.category_id = c.id
WHERE c.code = '1';
```

**查询某检测任务的所有阳性结果：**

```sql
SELECT r.sample_no, r.peak_index, d.name AS detected_drug, r.confidence, r.conclusion
FROM detection_results r
LEFT JOIN reference_drugs d ON r.detected_drug_id = d.id
WHERE r.task_id = 1 AND r.is_positive = 1;
```

**查询峰值图对比数据：**

```sql
SELECT m.peak_index, m.sample_peak_rt, rd.name AS ref_drug, m.ref_peak_rt, m.similarity_score
FROM detection_peak_matches m
JOIN reference_drugs rd ON m.ref_drug_id = rd.id
WHERE m.result_id = 1;
```

## 10. 遗留问题与待确认事项

1. **本地 MySQL 无法登录**：当前环境能检测到 127.0.0.1:3306 运行 MySQL，但未知 root 密码，因此 `schema.sql` 尚未实际执行验证。请提供可用账号密码后在测试库执行。
2. **管理员默认密码**：种子数据中管理员密码为 `admin123` 的 bcrypt 哈希，部署前务必修改为强密码。
3. **峰面积协方差矩阵缺失**：当前资料只有单组峰面积数据，无法计算协方差矩阵。建议后续通过批量训练数据导入后由算法模块自动拟合。
4. **其他 7 类药物数据缺失**：当前 `对照品数据库20220402.xlsx` 仅含安神镇定类 9 种药物。减肥类、降糖类等 7 类共 96 种药物需补充导入。
5. **数据库重置功能**：当前设计通过 `operation_logs` 记录操作，未单独建立 `db_snapshots` 表。若需实现说明书中的"数据库重置/回滚"，建议增加快照表或采用数据库级备份（如 mysqldump + 文件路径记录）。
6. **峰值图数据粒度**：`detection_peak_matches` 设计为"峰-候选药物"级别，若需更细粒度的"点-点"色谱图对比（如每个保留时间点的吸光度），可能需要额外增加时序数据表或文件存储方案。
