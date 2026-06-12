#!/bin/sh
# D-76: 内联 Python wait-for-mysql,30s 重试,零外部依赖(stdlib socket)。
# MySQL 未在 30s 内可连接则 exit 1,让 docker --restart 策略自动重试容器。
set -e
python -c "
import os, socket, sys, time
host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', '3306'))
deadline = time.time() + 30
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=1):
            sys.exit(0)
    except OSError:
        time.sleep(1)
sys.stderr.write('MySQL %s:%s not reachable within 30s\n' % (host, port))
sys.exit(1)
"

# D-75: 幂等初始化(已有数据则秒返,避免容器重启清空生产数据)
flask init-db --if-empty

# D-77: exec 让 gunicorn 收 PID 1,SIGTERM 正常转发;日志走 stdout 给 Docker 收集
# CD-21: workers=2 threads=4 timeout=30 适合 demo / 小流量
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 30 \
     --access-logfile - --error-logfile - \
     run:app
