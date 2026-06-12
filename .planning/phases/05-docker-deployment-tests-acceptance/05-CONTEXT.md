# Phase 5: Docker Deployment, Tests & Acceptance - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

## Phase Boundary

把已通过 Phase 1-4 的 Flask Wiki 应用打成可由第三方独立验收的产品交付物:**多阶段 Dockerfile (python:3.11-slim) + 幂等 entrypoint (检表行数判断首次启动) + 内联 Python 重试 30s 等待 MySQL + sh 脚本 + gunicorn (workers=2, threads=4, ProxyFix 适配 nginx) + .dockerignore (< 50MB) + pytest+pytest-flask (SQLite in-memory) + test_smoke.py + test_admin.py + README.md (简洁、面向资深运维) + docker-compose.example.yml (仅 app service) + nginx server snippet + 内嵌 TEST-05 手工验收清单**.

不动:Phase 1-4 全部已锁定决策直接 carry-forward(`init_db()` 模块函数、`flask init-db` / `flask promote-admin` CLI、env vars 配置、Flask-WTF CSRF、HTMX 4 个局部刷新流、Quill 编辑器、wiki 链接渲染、Comment 模型、admin 蓝图)。Phase 5 不重构任何已交付代码,只新增 deployment + test 层。

## Implementation Decisions

### 1. Docker entrypoint 启动协议(本阶段核心讨论)

- **D-75:** **init-db 走"检表行数 + --if-empty"幂等模式**。Phase 2 D-15 的 `init_db()` 函数签名扩展为 `init_db(if_empty: bool = False)`,内部:
  ```python
  if if_empty:
      try:
          if User.query.count() > 0:
              return  # 已初始化,跳过
      except Exception:
          pass  # 表不存在,继续走 drop+create+seed
  db.drop_all()
  db.create_all()
  # ... seed users/lemmas
  ```
  CLI 加 `--if-empty` flag:`@app.cli.command("init-db")` + `@click.option('--if-empty', is_flag=True)`。entrypoint 调 `flask init-db --if-empty`;运维如需强制重灌走 `docker exec ... flask init-db`(不带 flag)。**容器重启不清生产数据**,首次启动自动初始化。

- **D-76:** **MySQL 启动等待:内联 Python 重试 30s**。entrypoint.sh 拉起前先执行:
  ```python
  python -c "
  import os, socket, sys, time
  host, port = os.environ['DB_HOST'], int(os.environ.get('DB_PORT', 3306))
  for _ in range(30):
      try:
          with socket.create_connection((host, port), timeout=1):
              sys.exit(0)
      except OSError:
          time.sleep(1)
  sys.exit(1)
  "
  ```
  零外部依赖(stdlib socket),超时 exit 1 让 docker `--restart` 自动重试。**不**引入 `wait-for-it.sh` 第三方脚本。

- **D-77:** **entrypoint 脚本走 sh + root 用户(最简)**。`entrypoint.sh` 内容:
  ```sh
  #!/bin/sh
  set -e
  python -c "..."  # D-76 wait-for-mysql
  flask init-db --if-empty  # D-75
  exec gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 30 \
       --access-logfile - --error-logfile - run:app
  ```
  Dockerfile **不**加 `USER appuser`(demo + 外部 nginx 反代已隔离),`sh` 兼容 python:3.11-slim 默认 shell(无需 apt-get install bash,镜像小 12MB)。`exec` 让 gunicorn 作为 PID 1,SIGTERM 正常转发。

### 2. README 部署文档形态与深度(本阶段核心讨论)

- **D-78:** **README 面向"资深运维"读者**。假定读者熟悉 Docker、有 MySQL 实例、会配 nginx。文档篇幅 ~150 行。**不**逐条解释 env vars 含义,**不**给手把手 docker desktop 截图,**不**列长串故障排查 FAQ。给:env 变量速查表 + 1 个 docker run 完整命令示例 + 1 个 nginx server 块 snippet + smoke 验收清单。

- **D-79:** **TEST-05 验收清单全进 README.md**。不拆 `docs/ACCEPTANCE.md` 或 `docs/DEPLOY.md`。README 结构:
  ```
  # 互动百科 (baike)
  ## 项目简介
  ## 本地开发
  ## 生产部署 (Docker)
    ### 前置条件
    ### 环境变量
    ### 启动
    ### nginx 反代示例
  ## 测试 (pytest)
  ## 验收清单 (smoke flow for third-party verification)
  ## 已知限制 / FAQ (3-5 条)
  ```
  单一入口,降低读者认知负担。

- **D-80:** **docker-compose.example.yml 仅含 app service + env(不含 MySQL)**。compose 示例:
  ```yaml
  services:
    baike:
      image: baike:latest
      ports: ["8000:8000"]
      environment:
        DB_HOST: db.internal
        DB_PORT: "3306"
        DB_USER: baike_user
        DB_PASSWORD: ${DB_PASSWORD}
        DB_NAME: baike
        FLASK_SECRET: ${FLASK_SECRET}
      restart: always
  ```
  README 明示:"compose 示例仅展示 app 启动方式,**MySQL 与 nginx 假定由外部基础设施提供**"。**不**写包含 mysql:8.0 service 的 example(避免读者误以为本项目打包 MySQL)。nginx 配置以 ~30 行 server 块 snippet 直接放 README 章节内,不拆 nginx.conf.example 文件。

### 3. Dockerfile 构建策略(基于 Phase 5 ROADMAP locked + Phase 2 carry-forward)

- **D-81:** **多阶段 Dockerfile**:
  - **builder stage**(`python:3.11-slim AS builder`):安装 `build-essential` + `pkg-config` + `default-libmysqlclient-dev`(mysqlclient C extension 编译依赖)+ `pip install --user --no-cache-dir -r requirements.txt`
  - **runtime stage**(`python:3.11-slim`):仅 `apt-get install -y --no-install-recommends libmariadb3`(运行时 MySQL client 库,约 8MB)+ `COPY --from=builder /root/.local /root/.local` + `COPY app/ run.py entrypoint.sh ./`
  - 最终镜像目标 < 200MB(slim base ~120MB + Python 包 ~60MB)

- **D-82:** **WORKDIR /app + ENV PATH 包含 /root/.local/bin**(pip --user 安装的 flask/gunicorn 在该路径)。

- **D-83:** **CMD ["./entrypoint.sh"]**;不直接 `CMD ["gunicorn", ...]`(entrypoint 需要先 wait-for-mysql + init-db)。

### 4. gunicorn 配置(Claude's Discretion 默认)

- **CD-21:** gunicorn 命令行(D-77 内嵌):
  ```
  gunicorn --bind 0.0.0.0:8000 \
           --workers 2 --threads 4 --timeout 30 \
           --access-logfile - --error-logfile - \
           run:app
  ```
  workers=2 适合 demo/小流量,threads=4 处理 I/O 阻塞;timeout=30 兜底慢查询。

- **CD-22:** **启用 ProxyFix 中间件**。在 `app/__init__.py` Flask app 创建后(secret_key 与 db.init_app 之后)添加:
  ```python
  from werkzeug.middleware.proxy_fix import ProxyFix
  app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
  ```
  nginx 反代下 `url_for(_external=True)` 生成正确 https URL,日志 / `request.remote_addr` 显示真实客户端 IP。**仅信任 1 层代理**(本项目部署假设外部 nginx 直接到 baike app,无 CDN/LB 多层)。

- **CD-23:** **不**新增 `/healthz` 端点。运维通过 gunicorn 启动日志(`Listening at: http://0.0.0.0:8000`)判断就绪。Phase 5 demo 性质不引入主动健康检查协议。

- **CD-24:** **日志走 stdout**(`--access-logfile -` `--error-logfile -`),Docker 标准收集方式。无需挂载日志卷。

### 5. .dockerignore(基于 ROADMAP < 50MB cap)

- **D-84:** `.dockerignore` 内容:
  ```
  .git
  .gitignore
  .gitattributes
  .venv
  venvbaike
  __pycache__
  *.pyc
  *.pyo
  .idea
  .vscode
  .claude
  .planning
  .pytest_cache
  tests/
  instance/.flask_secret
  *.md
  !README.md
  baike.sql
  config.ini
  ```
  关键决策:
  - **`.planning/` 不进镜像**(GSD 规划文档,部署不需要)
  - **`tests/` 不进镜像**(测试在本地 / CI 跑,运行时不需要)
  - **`instance/.flask_secret` 不进镜像**(D-06 dev 临时密钥;生产必传 `-e FLASK_SECRET`)
  - **保留 README.md**(`docker inspect` / 用户可能 mount 进容器查看)
  - **`baike.sql` / `config.ini` 不进镜像**(uwsgi 历史 + 原始 SQL dump,Phase 5 部署不用)

### 6. pytest 测试环境(Claude's Discretion 默认)

- **CD-25:** **DB 后端:SQLite in-memory**。`conftest.py` 注入:
  ```python
  app.config.update(
      TESTING=True,
      WTF_CSRF_ENABLED=False,
      SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
  )
  ```
  优点:无需 MySQL container、每个测试函数 ~50ms 启动、CI / 本地 fresh venv 即可跑;局限:MySQL-specific SQL(本项目无)不被覆盖。Phase 5 smoke 性质足够。

- **CD-26:** **当前 app 是 module-level 实例(非 factory)**。`conftest.py` 直接 `from app import app, db` 并通过 `app.config.update(...)` 改 config;**不**引入 application factory 重构(超出 Phase 5 范围)。fixture 设计:
  ```python
  @pytest.fixture
  def client():
      from app import app, db
      app.config.update(TESTING=True, WTF_CSRF_ENABLED=False,
                        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
      with app.app_context():
          db.drop_all(); db.create_all()
          init_db(if_empty=False)  # seed
          with app.test_client() as c:
              yield c
          db.session.remove(); db.drop_all()
  ```

- **CD-27:** **CSRF 在测试中关闭**(`WTF_CSRF_ENABLED=False`),专注端到端业务流程。CSRF 集成测试**不**做(由 Phase 2 D-09 Flask-WTF 默认行为兜底)。

- **CD-28:** **`tests/test_admin.py` 与 `tests/test_smoke.py` 分离**(ROADMAP SUCCESS 6 推荐)。`test_smoke.py` 覆盖普通用户端到端(注册→登录→词条 CRUD→评论→自删评论);`test_admin.py` 覆盖 admin 删 lemma + 删 comment + 非 admin 403。共享 conftest.py fixture。

- **CD-29:** **HTMX 请求路径不在 smoke 测试中显式覆盖**(Phase 4 D-46/D-73 HX-Request 分支)。Smoke 测试走整页 302 redirect 路径(`/api/comment` POST 不带 HX-Request header,返回 302),与 Phase 3 既定向后兼容行为一致。HTMX 行为留 Phase 5 README 手工验收清单确认。

### 7. TEST-02 / TEST-03 测试流程具体步骤

- **D-85:** `tests/test_smoke.py::test_full_user_flow` 单测覆盖:
  1. `POST /api/regist` 注册 `testuser` / `testpass123` → assert 302 + 用户存在 + 密码哈希存储
  2. `POST /api/login` 同账号 → assert 302 → home + session cookie 设
  3. `POST /api/add` `title="测试词条"` + `content="测试内容 [[词条 A]]"` → assert 302 + Lemma 存在
  4. `GET /user/search?q=测试` → assert 200 + 结果含"测试词条"
  5. `GET /user/detail?title=测试词条` → assert 200 + content 含 `<a href` (wiki 链接渲染)+ view_count 从 0 变 1
  6. `POST /api/modify` `newTitle="测试词条" newContent="改后"` → assert 302 + Lemma.content 更新
  7. `POST /api/comment` `lemma_id=1 content="测试评论"` → assert 302 + Comment 存在
  8. `POST /api/comment/<id>/delete`(作者本人)→ assert 302 + Comment 不存在
  9. `POST /api/logout` → assert 302 + session 清

- **D-86:** `tests/test_admin.py::test_admin_can_delete_any` 覆盖:
  1. 用 `init_db()` 灌的 admin `a`/`a` 登录
  2. 普通用户 `bob` 创建 lemma + comment
  3. admin 登录后 `POST /api/admin/lemma/<id>/delete` → assert 302 + lemma 被删 + 级联 comments 被删
  4. `POST /api/admin/comment/<id>/delete` 单独路径覆盖(用 bob 新建 comment)
  
  `tests/test_admin.py::test_non_admin_forbidden` 覆盖:
  1. 普通用户 `bob` 登录
  2. `POST /api/admin/lemma/<id>/delete` → assert 403
  3. `POST /api/admin/comment/<id>/delete` → assert 403

- **CD-30:** `make test` 走 `pytest -v tests/`;`make smoke` 走 `pytest -v tests/test_smoke.py`(允许只跑 smoke)。Makefile 单行 target 即可,**不**引入复杂的 test category(unit/integration 区分对 Phase 5 demo 性质无价值)。

### 8. requirements.txt 增量

- **D-87:** Phase 5 新增依赖:
  ```
  gunicorn>=21.0,<22.0   # 生产 WSGI server
  pytest>=8.0,<9.0       # 测试框架
  pytest-flask>=1.3,<2.0 # Flask 测试辅助
  ```
  **不**新增:`pytest-cov`(覆盖率工具,超出 smoke 范围)、`wait-for-it`(D-76 用 stdlib socket 替代)、`gunicorn-paste`(无需 paste 配置)、`docker-compose` Python 库(compose 是 CLI 不是依赖)。

### 9. ProxyFix 集成时机

- **D-88:** `ProxyFix` 在 `app/__init__.py` 中**条件启用**:
  ```python
  if os.environ.get('FLASK_BEHIND_PROXY', '').lower() == 'true':
      app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
  ```
  默认**关闭**(本地 dev `python run.py` 不需要);Dockerfile `ENV FLASK_BEHIND_PROXY=true`,容器内自动启用。避免 dev 模式下 `request.remote_addr` 永远显示 127.0.0.1 的伪 X-Forwarded-For 攻击面。

### Claude's Discretion(汇总)

- **CD-31:** Dockerfile base image 锁版本 — `python:3.11-slim`(ROADMAP locked),不锁 patch 版本(`3.11.X-slim`);如需复现可挑当时最新稳定 tag,planner 决定。
- **CD-32:** Makefile target 命名 — `make test` / `make smoke` / `make docker-build` / `make docker-run`(后两条仅为方便,不强制)。
- **CD-33:** entrypoint.sh 可执行权限 — Dockerfile 中 `RUN chmod +x entrypoint.sh`(避免 Windows checkout 后丢失 +x 位)。
- **CD-34:** gunicorn `--reload` flag 在生产**关闭**(默认即关);仅本地 dev 用 `python run.py debug=True`。
- **CD-35:** pytest conftest.py 位置 — `tests/conftest.py`(Flask 社区惯例;**不**放 `tests/__init__.py` + module-level fixture)。
- **CD-36:** `flask init-db --if-empty` 决策落地 — Phase 2 D-15 的 init_db() 改签名,Phase 5 实施时 verify D-15 既有调用方(`/api/reset` 路由 + `flask init-db` CLI)不传 `if_empty=False` 即可保持向后兼容。
- **CD-37:** Dockerfile **不**安装 `vim` / `curl` 等调试工具;运维通过 `docker exec ... sh` + Python stdlib 排障。镜像小 ~5MB。
- **CD-38:** README "已知限制 / FAQ" 章节内容 — 列举:① 镜像不打包 MySQL/nginx 假定外部基础设施;② FLASK_SECRET 必传生产;③ 容器重启不清数据(D-75 if-empty);④ HTMX 局部刷新需浏览器加载 CDN(Phase 4 D-53)。
- **CD-39:** docker-compose.example.yml 用 `${VAR}` 占位(读取 `.env` 或 export 环境)— README 提示 `.env` 文件创建方式,**不**在 example 中写死示例密码。
- **CD-40:** TEST-05 验收清单**不**机械化(无 BDD framework),纯人类可执行的 markdown 列表 + 每条期望结果;Phase 5 demo 验收性质。

## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### 项目元信息
- `.planning/PROJECT.md` — 项目核心价值"陌生开发者根据 README 启动并演示全部功能"(Phase 5 直接对应);Out of Scope 的 K8s/CI/CD/监控/OAuth 排除清单(Phase 5 不要漂移)
- `.planning/REQUIREMENTS.md` — v1 46 条需求,Phase 5 对应 INFRA-07, INFRA-08, INFRA-10, INFRA-11, TEST-01..05(共 9 条);特别留意 INFRA-10 README "Production deploy" 段 + TEST-05 端到端
- `.planning/ROADMAP.md` § Phase 5 — 阶段目标 + 8 条 SUCCESS 标准 + 计划 5.1/5.2 拆分
- `.planning/STATE.md` — Phase 1/2/3/4 已完成累计上下文 + Discovered Constraints("Phase 5 的 README 必须包含端到端 smoke flow 步骤")

### Phase 1-4 已锁定决策(本阶段直接 carry-forward)
- `.planning/phases/01-foundation-python-3-bug-fixes/01-VERIFICATION.md` — Python 3.11+ + mysqlclient 基线已 verified
- `.planning/phases/02-security-auth-hardening/02-CONTEXT.md` — D-01..D-25 全部生效
  - **D-05, D-06, D-07**:必读 env vars 清单 + FLASK_SECRET fallback + DB URI quote_plus 拼装 → Phase 5 docker-compose env 直接复用
  - **D-13, D-14, D-15, D-16, D-25**:`init_db()` 模块函数 + `flask init-db` CLI 注册(`@app.cli.command("init-db")`)→ Phase 5 D-75 在此基础上加 `--if-empty` flag
  - **D-22, D-23**:`@admin_required` 装饰器 + `User.is_admin` 字段 → Phase 5 test_admin.py 覆盖
  - **D-24**:`flask promote-admin <username>` CLI → README 中说明"首次部署后用 docker exec 提升 admin"
- `.planning/phases/03-comment-system/03-CONTEXT.md` — D-26..D-41 全部生效
  - **D-26**:`Comment.user_id FK` + `backref('author', lazy='joined')` → smoke 测试 author 字段查询路径
  - **D-31, D-32, D-41**:作者删除 / admin 删除评论端点 → test_smoke / test_admin 覆盖
- `.planning/phases/04-frontend-modernization-product-features/04-CONTEXT.md` — D-42..D-74 全部生效
  - **D-46, D-73**:HTMX 评论发布 HX-Request 分支(Phase 5 smoke 测试**不**覆盖此路径,CD-29)
  - **D-53**:Pico.css + HTMX 走 jsdelivr CDN(README 需提示"需要外网访问 jsdelivr",CD-38 已记录)
  - **D-61, D-65**:Lemma `updated_at` + `view_count` + `/user/detail` GET 化 → smoke 测试 step 5 验证

### 既有代码 / 改造目标
- `app/__init__.py` — Flask app 工厂入口,Phase 5 需添加 ProxyFix 条件启用(D-88)
- `app/api/model.py` — `init_db()` 函数加 `if_empty` 参数(D-75 / CD-36)
- `app/api/__init__.py` — 含 `@app.cli.command("init-db")` CLI 注册,Phase 5 需扩展 click option `--if-empty`
- `app/route/user.py` — smoke 测试中 `/user/detail` 走 GET(Phase 4 D-65 已改);测试 step 5 验证 view_count 增长
- `app/api/admin.py` — admin 蓝图 + `@admin_required` 已就绪(Phase 2 D-20..D-22 + Phase 3 D-41)→ test_admin.py 调用
- `requirements.txt` — 当前 7 行(Flask / Flask-Login / Flask-SQLAlchemy / mysqlclient / PyMySQL / Flask-WTF / bleach),Phase 5 新增 3 行(D-87:gunicorn + pytest + pytest-flask)
- `instance/` 目录 — Phase 2 D-06 用于 `.flask_secret`;Phase 5 `.dockerignore` 排除该文件(D-84)
- `app/static/` — Phase 4 已清理 jQuery/Bootstrap/wangEditor;Phase 5 Dockerfile COPY 时整 static 进镜像即可(无需额外清单)
- `run.py` — gunicorn 启动入口 `run:app`(D-77),不改 run.py

### 新建文件清单
- `Dockerfile` — 新建,多阶段 builder + runtime(D-81/82/83)
- `entrypoint.sh` — 新建,sh 脚本,wait-for-mysql + init-db --if-empty + exec gunicorn(D-77)
- `.dockerignore` — 新建,排除 .planning/.git/tests/...(D-84)
- `docker-compose.example.yml` — 新建,仅含 app service(D-80)
- `tests/conftest.py` — 新建,SQLite in-memory fixture(CD-25/26)
- `tests/test_smoke.py` — 新建,端到端流程单测(D-85)
- `tests/test_admin.py` — 新建,admin 删除 + 非 admin 403(D-86)
- `Makefile` — 新建,`make test` / `make smoke` / `make docker-build` / `make docker-run`(CD-30/32)
- `README.md` — **重写**(现状是 2017 年原 README,Phase 5 改写为生产部署 + 验收文档,D-78/79)

### 测试与文档
- `tests/` 目录 — 本阶段新建(此前不存在,见 `.planning/codebase/TESTING.md`)
- `README.md` 验收清单 — 内嵌 TEST-05 第三方手工验收 smoke flow(D-79)

## Existing Code Insights

### Reusable Assets
- **`init_db()` 模块函数**(Phase 2 D-15)— 复用,Phase 5 仅加 `if_empty: bool = False` 参数
- **`flask init-db` CLI**(Phase 2 D-16/D-25)— 复用,Phase 5 加 `--if-empty` flag
- **`flask promote-admin <username>` CLI**(Phase 2 D-24)— 复用,README 说明用法
- **Flask-WTF CSRF**(Phase 2 D-09..D-12)— 测试中 `WTF_CSRF_ENABLED=False` 关闭(CD-27)
- **统一错误页**(Phase 2 D-17..D-19,Phase 4 CD-12 改 Pico.css 风格)— 复用,smoke 测试中可 assert 404 页面
- **`admin` 蓝图 + `@admin_required`**(Phase 2 D-20..D-22)— test_admin.py 直接调用
- **`User.is_admin`**(Phase 2 D-23)— admin 测试 fixture 用 `init_db()` 灌的 `a` 账号(已 is_admin=True)
- **`Comment` 模型 + cascade 删除**(Phase 3 D-26..D-33)— test_admin 测试 admin 删 lemma 级联删评论
- **HTMX 4 个局部刷新流**(Phase 4 D-45..D-48)— smoke 测试**不**覆盖 HX-Request 分支(CD-29)
- **Pico.css + HTMX CDN 加载**(Phase 4 D-53)— README 添加"需要外网访问 jsdelivr"提示(CD-38)
- **Quill 本地 vendor**(Phase 4 D-54)— Dockerfile COPY static/ 即包含,无额外步骤
- **bleach HTML 过滤**(Phase 4 D-44)— smoke 测试 step 3 创建 lemma 时验证(隐式)

### Established Patterns
- **Blueprint 命名约定**:`apple` (页面) + `api` (表单提交) + `admin`(Phase 2)— Phase 5 不引入新蓝图
- **`url_for` 跳转**:smoke 测试中可用 `client.post(url_for('api.regist'))` 而非硬编码 URL
- **错误反馈**:`flash` + redirect 风格(非 JSON)— smoke 测试 assert response.status_code == 302 + follow_redirects=True 后查 flash 内容
- **`db.drop_all()` + `db.create_all()` + 灌种子**(Phase 2 D-15)— Phase 5 D-75 在此模式上加 `--if-empty` 守卫
- **隐式 flask app context**:`@app.cli.command` 装饰器自带 app context(Phase 2 D-16)— Phase 5 entrypoint 中 `flask init-db` 自动获取 context
- **module-level Flask 实例**(非 factory)— Phase 5 test fixture 接管 `from app import app` 直接 `app.config.update()`,**不**引入 factory 重构(超出范围)

### Integration Points
- `app/__init__.py` — 添加 ProxyFix 条件启用块(~5 行,D-88)
- `app/api/model.py` 或 `app/api/__init__.py`(init_db 实际位置)— 函数签名加 `if_empty=False` 参数 + 内部 User.query.count() 守卫(D-75)
- `app/api/__init__.py` 的 `flask init-db` CLI — 加 `@click.option('--if-empty', is_flag=True)` 装饰器
- `requirements.txt` — 加 `gunicorn` / `pytest` / `pytest-flask` 3 行(D-87)
- 新增根目录文件:`Dockerfile` / `entrypoint.sh` / `.dockerignore` / `docker-compose.example.yml` / `Makefile`
- 新增 `tests/` 目录:`conftest.py` / `test_smoke.py` / `test_admin.py`
- **重写** `README.md`(现状是 2017 年原文,Phase 5 整篇更新)

## Specific Ideas

- **想法 A:** entrypoint sh 脚本里 wait-for-mysql 的 Python heredoc 注入 env 变量时,引号嵌套小心 — 推荐用 `python -c "$(cat <<'EOF' ... EOF)"` 形式或单独 `entrypoint_check.py` 文件(更易调试)。Planner 决定。
- **想法 B:** Dockerfile multi-stage 的 `COPY --from=builder /root/.local /root/.local` 依赖 pip --user;如改用 venv 拷贝,路径变为 `/opt/venv`。两者等价,选 pip --user 因更轻量。
- **想法 C:** `tests/conftest.py` fixture scope 用 `function`(每个测试函数独立 DB 状态),而非 `session`(共享 DB)。Phase 5 测试数量少(2-3 个 test functions),function scope 简洁可靠。
- **想法 D:** `make test` 在 fresh venv 跑前需 `pip install -e .` 还是 `pip install -r requirements.txt`?本项目无 `setup.py`,直接 `pip install -r requirements.txt` 即可。tests/ 目录 PYTHONPATH 由 `pytest` 自动处理(认 `app/` 在 cwd)。
- **想法 E:** README 中 `docker run` 示例命令推荐 `\` 换行多行展示(可读),而非单行长串。运维 copy-paste 友好。
- **想法 F:** ProxyFix 启用条件可改为"always on, 但仅 trust 1 层"— 简化判断,本地 dev 也无副作用(因为 `python run.py` 不经任何代理,X-Forwarded-* 头不存在,ProxyFix 回退到原 remote_addr)。如 planner 选此方案,D-88 简化为无条件 ProxyFix。
- **想法 G:** `tests/test_smoke.py` 单测体很长(9 步),拆为多个 test function(每步一个测试)还是单个 `test_full_user_flow`?**单个 test function** 更贴近 TEST-02 "single test" 措辞 + 端到端语义;拆分会丢失"流程连续性"价值。
- **想法 H:** `make docker-build` 标签策略 — `baike:latest` + `baike:$(git rev-parse --short HEAD)`,二者 alias,demo 性质。CI/CD 不在 Phase 5 范围(V2-OPS-01)。

## Deferred Ideas

### CI/CD pipeline (V2-OPS-01)
- GitHub Actions 自动跑 smoke / 自动 build & push 镜像 — 留 v2。Phase 5 仅本地 `make test` + 手工 `docker build`。

### K8s / Helm chart (V2-OPS-02)
- Kubernetes manifests / Helm chart — 留 v2。Phase 5 只交付单 Flask 容器,假设外部编排。

### 监控 / OpenTelemetry (V2-OPS-03)
- Prometheus metrics / OTel trace / 应用监控 — 留 v2。Phase 5 仅 stdout 日志。

### healthcheck 端点
- `/healthz` / `/readyz` 端点 + Docker `HEALTHCHECK` 指令 — 留 v2。Phase 5 demo 性质,运维通过 gunicorn 启动日志判断(CD-23)。

### pytest 覆盖率工具 (pytest-cov)
- coverage report / .coveragerc — 留 v2。Phase 5 smoke 性质,无覆盖率指标。

### MySQL 容器集成测试
- 用 `pytest-docker` 在测试中拉起真实 MySQL container — 留 v2。Phase 5 CD-25 SQLite in-memory 性能 + 简单性优先。

### Application Factory 模式重构
- `app/__init__.py` 改为 `create_app()` factory 函数 — 留 v2。Phase 5 CD-26 直接 import module-level instance,不引入大改。

### 多环境 config (development / staging / production)
- Flask `app.config.from_object('config.ProductionConfig')` 多 class config — 留 v2。Phase 5 全走 env vars(Phase 2 D-05),无 config class 分层。

### 容器镜像签名 / 漏洞扫描
- cosign / trivy scan — 留 v2。Phase 5 demo 不引入。

### nginx 配置完整文件
- 完整 `nginx.conf.example`(含 events / http / upstream blocks)— Phase 5 D-80 仅给 server snippet,假设运维有完整 nginx 主配置。

### docker-compose 含 MySQL service
- compose 里集成 mysql:8.0 + named volume + healthcheck — Phase 5 D-80 显式排除("不打包 MySQL")。

### CSRF token 集成测试
- 测试中模拟真实 CSRF 流程 — Phase 5 CD-27 关闭 CSRF。Flask-WTF 自身行为由 Phase 2 已 verify。

### HTMX 路径 smoke 测试
- 测试 `HX-Request` header 触发的局部刷新分支(Phase 4 D-46/D-73)— Phase 5 CD-29 留手工验收。

### Docker Buildx 多架构镜像
- arm64 + amd64 multi-arch build — 留 v2。Phase 5 假设 amd64。

### Volume / 持久化最佳实践
- `instance/` 卷挂载策略 / .flask_secret 跨重启持久化 — Phase 5 D-06 README 提示"生产传 FLASK_SECRET";.flask_secret 不挂载,容器重启即新生成。

---

*Phase: 05-Docker Deployment, Tests & Acceptance*
*Context gathered: 2026-06-12*
