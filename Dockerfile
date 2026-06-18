# 全部依赖都是纯 Python wheel(greenlet 走 manylinux 预编译),单阶段即可
# D-81: python:3.11-slim 基镜像,不锁 patch 版本(CD-31)
FROM python:3.11-slim
# CD-37: 不装 vim / curl / wget 等调试工具,镜像更小
# PYTHONUNBUFFERED=1 让 stdout 日志不被缓冲(CD-24,Docker 日志收集)
# FLASK_BEHIND_PROXY=true 让容器内 ProxyFix 自动启用(D-88)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_BEHIND_PROXY=true

WORKDIR /app

# 先单 COPY requirements.txt 利用 Docker 层缓存(只装依赖,不变就不重装)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
