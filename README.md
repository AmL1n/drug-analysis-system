# HPLC-DAD 药物非法添加筛查系统

基于 Vue 3 + Flask 的网页版中药/西药非法添加药物检测平台，支持多药物同时检测、峰值图对比与报告导出。

## 技术栈

- **前端**：Vue 3 + Vite + TypeScript + Pinia + Element Plus + ECharts
- **后端**：Python 3.9 + Flask + Flask-SQLAlchemy + Flask-JWT-Extended
- **数据库**：开发环境 SQLite，生产环境 MySQL 8.0+
- **部署**：Docker + Docker Compose

## 目录结构

```
.
├── backend/              # Flask 后端
│   ├── app/              # 应用代码
│   ├── sql/              # 数据库脚本
│   ├── tests/            # 测试
│   ├── uploads/          # 上传文件
│   └── Dockerfile
├── frontend/             # Vue 前端
│   ├── src/              # 源码
│   ├── dist/             # 构建产物
│   ├── Dockerfile
│   └── nginx.conf
├── samples/              # 示例数据
├── docker-compose.yml
├── .env.example
└── README.md
```

## 快速开始

### 1. 克隆与初始化

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 2. 环境变量

复制项目根目录 `.env.example` 为 `.env`，并按需修改：

```bash
cp .env.example .env
```

开发环境默认使用 SQLite：

```env
DATABASE_URL=sqlite:///backend/drug_check_dev.db
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-bytes
SECRET_KEY=your-secret-key
```

### 3. 启动开发服务

```bash
# 后端（端口 5000）
cd backend
export DATABASE_URL=sqlite:///backend/drug_check_dev.db
python run.py

# 前端（端口 5173）
cd frontend
npm run dev
```

默认账号：`admin / admin123` 或 `operator / admin123`。

### 4. 导入示例对照品库

启动后端后，示例类别会自动创建。执行 SQL 脚本导入安神镇定类 9 种对照品：

```bash
cd backend
sqlite3 drug_check_dev.db < sql/seed_sample_library.sql
```

## 样本数据

`samples/` 目录下提供以下示例文件：

| 文件 | 说明 |
|------|------|
| `sample_chromatogram.csv` / `.xlsx` | 完整色谱图，可用于检测分析 |
| `sample_retention_time.txt` | 标准保留时间导入格式 |
| `sample_peak_area.txt` | 标准峰面积导入格式（4 组波长） |
| `sample_spectra.xlsx` | 标准光谱吸收表 |

## 检测流程

1. 登录系统
2. 进入“检测分析”页
3. 上传色谱图文件（CSV / TXT / Excel）
4. 系统自动识别峰、匹配对照品库
5. 查看 Top 候选药物、峰值图对比
6. 下载 PDF / Excel 报告

## Docker 部署

```bash
# 复制并修改环境变量
cp .env.example .env

# 构建并启动
docker-compose up -d --build
```

- 前端：http://localhost:5173
- 后端：http://localhost:5000

生产环境请务必修改 `.env` 中的 `JWT_SECRET_KEY` 和 `SECRET_KEY`。

## 测试

```bash
cd backend
pytest tests -q
```

## Render 部署（测试）

项目已包含 `render.yaml`，可一键部署两个服务：

1. **推送到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "init"
   git remote add origin https://github.com/AmL1n/drug-analysis-system.git
   git push -u origin main
   ```

2. **在 Render 创建 Blueprint**
   - 登录 [Render Dashboard](https://dashboard.render.com/blueprints)
   - 点击 **New Blueprint Instance**
   - 选择 `AmL1n/drug-analysis-system` 仓库
   - Render 会自动读取 `render.yaml` 并创建：
     - `drug-analysis-backend`（Docker Web Service）
     - `drug-analysis-frontend`（Static Site）

3. **更新前端 API 地址**
   - 后端部署完成后，Render 会给你一个 URL，例如 `https://drug-analysis-backend-xxx.onrender.com`
   - 修改 `render.yaml` 中 `VITE_API_BASE_URL` 的值：
     ```yaml
     - key: VITE_API_BASE_URL
       value: https://drug-analysis-backend-xxx.onrender.com/api
     ```
   - 重新 push 到 GitHub，Render 会自动重新构建前端。

4. **生产环境注意事项**
   - `JWT_SECRET_KEY` / `SECRET_KEY` 建议手动替换为随机字符串，而不是使用自动生成的值。
   - SQLite 随容器存在，Render 每次重新部署后数据会丢失。若要保留数据，请在 Render 中为后端服务开启 **Disk**（`render.yaml` 已预留 1GB）。
   - 测试阶段免费实例会在一段时间无请求后休眠，首次访问可能需要 30 秒左右冷启动。

## 安全提示

- 生产环境必须设置强随机密钥
- CORS 来源应限制为前端域名
- 文件上传限制在 `txt/csv/xlsx/xls`，单文件不超过 50MB
- 建议使用 Nginx / HTTPS 反向代理
