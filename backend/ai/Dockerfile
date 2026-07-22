# GoFit AI Center - 生产镜像
FROM python:3.11-slim

WORKDIR /app

# 安装 ffmpeg（视频处理依赖）和 ffprobe
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# 复制应用代码
COPY app ./app

# 非 root 用户运行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8100

# 生产环境启动
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
