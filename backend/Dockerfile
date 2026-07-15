# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装编译依赖（部分包需要）
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建上传目录与日志目录
RUN mkdir -p uploads logs

EXPOSE 5000

# 生产环境使用 Gunicorn；开发环境可覆盖为 python run.py
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "run:app"]
