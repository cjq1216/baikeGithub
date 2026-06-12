# ---- builder stage: 装 mysqlclient C 扩展 + 全量 Python 依赖 ----
# D-81: python:3.11-slim 基镜像,不锁 patch 版本(CD-31)
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# pip --user 安装到 /root/.local,runtime stage 拷贝该路径(D-82)
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- runtime stage: 仅运行时依赖 + 应用代码 ----
FROM python:3.11-slim
# CD-37: 不装 vim / curl / wget 等调试工具,镜像更小
# libmariadb3 是 mysqlclient 运行时所需的动态库(~8MB)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# D-82: pip --user bin 路径在 /root/.local/bin
# PYTHONUNBUFFERED=1 让 stdout 日志不被缓冲(CD-24,Docker 日志收集)
# FLASK_BEHIND_PROXY=true 让容器内 ProxyFix 自动启用(D-88)
ENV PATH=/root/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_BEHIND_PROXY=true

WORKDIR /app

# 从 builder stage 拷贝已编译的 Python 依赖(mysqlclient C 扩展等)
COPY --from=builder /root/.local /root/.local
# 应用代码 + 入口脚本
COPY app/ ./app/
COPY run.py entrypoint.sh ./
# CD-33: 兜底加可执行位(Windows checkout 可能丢失 +x)
RUN chmod +x entrypoint.sh

# CD-21: gunicorn 监听 8000
EXPOSE 8000

# D-83: 走 entrypoint.sh(需先 wait-for-mysql + init-db)
# ENTRYPOINT + CMD 用 exec 形式(不是 ["./entrypoint.sh", "arg"])
CMD ["./entrypoint.sh"]
