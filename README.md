# 互动百科 (baike)

一个 Flask + MySQL 的小型互动百科。v1 产品化升级目标:第三方按本文档即可拉起
Docker 容器、注册账号、创建词条、发布评论、admin 端到端走一遍。

## 项目简介

- 5 个 POST 接口(注册/登录/登出/加词条/改词条)+ 3 个评论端点 + 2 个 admin 端点
- 持久层:MySQL(外部,容器假定已就绪)
- 前端:Pico.css + HTMX + Quill 富文本(CDN 加载)
- 测试:pytest 端到端 smoke + admin 权限测试
- 部署:`python:3.11-slim` 多阶段 Docker 镜像 + gunicorn (2 workers / 4 threads) + ProxyFix 适配 nginx

## 本地开发

```bash
# 1. 准备 MySQL(假定 root@localhost:3306 / 库名 baike 已建好)
# 2. 准备虚拟环境
python -m venv venvbaike
source venvbaike/bin/activate     # Windows: venvbaike\Scripts\activate
pip install -r requirements.txt

# 3. .env.dev 是模板,clone 后已经存在且默认指向 localhost:3306
#    改值直接编辑 .env.dev 重启 python run.py 即可
#    APP_ENV 默认 'dev',无需 export

# 4. 初始化 DB
flask init-db   # 强制重建 + 灌 admin 'a'/'a' + 7 条种子词条

# 5. 启动
python run.py   # 监听 5000 端口
```

浏览器打开 http://127.0.0.1:5000/ → 注册 / 登录 / 加词条。

## 生产部署(Docker)

### 前置条件

- Docker 20.10+
- MySQL 5.7+ / 8.0 实例可达(外部基础设施,本项目不打包 MySQL)
- nginx 反代(外部基础设施,本项目不打包 nginx)

### 配置文件

| 文件 | 用途 | 是否进 git |
|------|------|---|
| `.env.dev` | 本地开发默认值(localhost + root + 空密码) | ✅ 模板 |
| `.env.prod` | 生产配置模板(空值待填) | ✅ 模板 |
| `.env.prod.local` | 生产实际配置(从 `.env.prod` 复制,填真实值) | ❌ `.gitignore` |

### 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `APP_ENV` | 加载哪个 `.env` 文件,可取 `dev` / `prod` / `staging` | `dev` |
| `DB_HOST` | MySQL 主机 | `.env.dev` = `localhost` |
| `DB_PORT` | MySQL 端口 | `.env.dev` = `3306` |
| `DB_USER` | MySQL 用户 | `.env.dev` = `root` |
| `DB_PASSWORD` | MySQL 密码 | `.env.dev` = 空 |
| `DB_NAME` | MySQL 库名 | `.env.dev` = `baike` |
| `FLASK_SECRET` | Flask session 签名密钥(`APP_ENV=prod` 必传) | dev 走 `instance/.flask_secret` 兜底 |

**优先级**:`docker run --env-file` 注入的 env > `.env` 文件值。这是 `python-dotenv` 默认 `override=False` 的语义,容器场景下 env_file 始终是权威源。

### 启动

```bash
# 1. 准备生产配置(从模板复制一份填真实值,不要 commit)
cp .env.prod .env.prod.local
vim .env.prod.local
#   必填两行:DB_PASSWORD=... / FLASK_SECRET=$(openssl rand -hex 32)

# 2a. 用 docker compose(直接用 env_file 字段)
cp docker-compose.example.yml docker-compose.yml
docker compose build          # 首次或代码变更后
docker compose up -d

# 2b. 或:不用 compose,直接 docker run
docker load -i baike-latest.tar
docker run -d --name baike -p 8000:8000 \
  --env-file .env.prod.local \
  --restart unless-stopped \
  baike:latest

# 3. (首次)admin 已是 'a'/'a' 默认可用
#    后续新增用户转 admin:docker compose exec baike flask promote-admin <username>

# 4. 验证
curl http://localhost:8000/user/home
docker compose logs -f baike
```

**进阶:`FLASK_SECRET_FILE` 路径支持**

`app/__init__.py` 的 `_resolve_flask_secret()` 还支持从文件读取,适合 K8s `secretKeyRef` 或 Docker `secrets:` 挂载场景:

```bash
# Docker secrets 方式
docker run -e FLASK_SECRET_FILE=/run/secrets/flask_secret ...

# K8s Secret 挂载方式
env:
  - name: FLASK_SECRET_FILE
    value: /var/run/secrets/baike/flask_secret
volumeMounts:
  - name: flask-secret
    mountPath: /var/run/secrets/baike
```

优先级:`FLASK_SECRET` env > `FLASK_SECRET_FILE` 文件 > `instance/.flask_secret` 持久化(容器内未挂卷,重启会丢)。

### nginx 反代示例

```nginx
server {
    listen 80;
    server_name baike.example.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

完整 nginx 主配置(events / http / upstream blocks)由运维侧负责,本项目仅给 server 块。

## 测试(pytest)

```bash
make test      # 跑全部:smoke + admin
make smoke     # 只跑 9 步端到端
```

SQLite in-memory,无需 MySQL 容器;每个测试函数独立 DB 状态。

## 验收清单(smoke flow for third-party verification)

第三方 fresh checkout + docker compose up -d 后,在浏览器走完以下 9 步:

1. 打开 http://baike.example.com/ → 看到首页 + 已有 7 条种子词条
2. 注册新账号(用户名 ≥ 6 字符 / 密码 ≥ 6 字符)→ 302 → 首页 + 导航栏右上角显示用户名
3. 登出 → 重新登录(同账号)→ 302 → 首页
4. 进入「写词条」→ 填 title + Quill 富文本(含 `[[wiki 链接]]` 语法)→ 提交 → 302 → 首页
5. 搜索刚加的词条(首页搜索框)→ 看到列表
6. 打开词条详情页 → 看到内容 + `[[wiki 链接]]` 渲染为蓝链接 / 红虚线(若目标不存在)+ 浏览数 + 1
7. 点「修改」→ Quill 预填 + 改内容 + 提交 → 302 → 首页
8. 词条详情页底部评论框发评论 → 看到评论显示在列表顶部
9. 登出 / 重新登录 admin(`a`/`a`)→ 进任一词条详情页 → 看到「删除词条」按钮 + 点「删除」该词条下所有评论一并消失

走完 9 步无 FAIL = v1 验收通过。

## 已知限制 / FAQ

1. **本项目不打包 MySQL**:`docker-compose.example.yml` 仅含 baike app;MySQL / nginx 假定由外部基础设施提供。
2. **`FLASK_SECRET` 生产必传**:`instance/.flask_secret` 兜底机制在容器里**未挂卷**,容器重启会重新 `os.urandom(32)`,全员 session 立即失效。生产必须把 `FLASK_SECRET=$(openssl rand -hex 32)` 写进 `.env.prod.local`,或用 `FLASK_SECRET_FILE` 挂载 secret 文件。
3. **容器重启数据保留**:entrypoint 走 `flask init-db --if-empty`,已有数据时秒返(不 drop)。要强制重灌:`docker compose exec baike flask init-db`(不带 flag)。
4. **HTMX / Pico.css 走 jsdelivr CDN**:浏览器需能访问 `cdn.jsdelivr.net`;内网部署请把这两份资产 vendor 到 `app/static/`。
5. **`.env` 文件加载规则**:`APP_ENV` 决定加载 `.env.dev` / `.env.prod` / `.env.staging` 哪个文件,默认 `dev`。`docker run --env-file` 注入的变量优先于文件值(`python-dotenv` 默认 `override=False`)。`.env.prod.local` 含真实密码,已在 `.gitignore` 保护;`.env.dev` / `.env.prod` 是模板,正常进 git。
