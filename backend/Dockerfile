# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装编译依赖、中文字体及时区数据
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev fonts-wqy-zenhei tzdata \
    && rm -rf /var/lib/apt/lists/*

# 设置容器默认时区为中国上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建上传目录、日志目录与 SQLite 数据目录（Render Disk 挂载点）
RUN mkdir -p uploads logs /app/data

EXPOSE 5000

# 生产环境使用 Gunicorn；开发环境可覆盖为 python run.py
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "run:app"]
