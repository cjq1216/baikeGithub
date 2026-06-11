# Phase 2: Security & Auth Hardening - Context

**Gathered:** 2026-06-11
**Status:** Ready for planning

## Phase Boundary

把当前 Flask Wiki 的 auth 表面从"2017 课堂作业基线"升级到"产品可演示"的安全基线:**凭据走环境变量、密码哈希存储、全站 CSRF 保护、`is_admin` 角色 + 管理员删除接口、统一错误页**。其它能力(评论、wiki 链接、前端现代化、Docker 部署)属于 Phase 3/4/5,本阶段不引入。

不动模板整体视觉(归 Phase 4);不动评论模型(归 Phase 3);不动 Docker 镜像(归 Phase 5,只提前预留 `flask init-db` CLI 入口给 Phase 5 的 entrypoint 调)。

## Implementation Decisions

### 1. 密码存储

- **D-01:** Hash 算法 — 使用 `werkzeug.security.generate_password_hash` / `check_password_hash` (默认 pbkdf2:sha256, 600k 迭代)。零新依赖。
- **D-02:** 字段改造 — `User.password` 扩为 `db.String(255)` (pbkdf2 默认产出 150+ 字节)。采用 **drop_all + create_all + 重灌种子** 方式重塑表(不引入 Alembic / Flask-Migrate)。生产部署期间需运行 `flask init-db` 完成初始化。
- **D-03:** 登录失败提示 — 统一 flash "账号或密码错误",**不**区分"用户不存在"与"密码错误"(防账号枚举)。
- **D-04:** 输入校验 — 后端校验用户名 + 密码长度 6-30 字符,同名账号直接 302 + flash "注册失败!帐号已存在",不引入强密码策略(留 v2)。

### 2. 凭据与 secret_key

- **D-05:** 必读 env 变量 — `FLASK_SECRET`、`DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`。`DB_*` 任一缺失 → `RuntimeError` 启动失败(无静默默认值,无回退到硬编码)。
- **D-06:** `FLASK_SECRET` 缺失行为 — dev 友好:启动时 `os.urandom(32)` 生成临时密钥,默认写入 `instance/.flask_secret` (Flask instance 约定目录)。可被 `FLASK_SECRET_FILE` env 覆盖(不暴露给用户设,只内部可指定)。README 必须提醒**生产必须传 `-e FLASK_SECRET=...`**,避免容器重启 / 重新 build 后密钥轮换导致全员登出。
- **D-07:** DB URI 拼装 — 用 `sqlalchemy.engine.url.URL` + `urllib.parse.quote_plus` 拼 `mysql+mysqlclient://user:quote(password)@host:port/db`,适应密码含 `@` / 特殊字符场景。**不再用 `mysql://%s:%s@...` % 字符串**(那是 Phase 1 前的硬编码写法)。
- **D-08:** 默认种子账号 — 保留 `a` / `a`,在 reset 时用 `generate_password_hash('a')` 存哈希,并设 `is_admin=True`。其它种子词条 7 条保持不变。

### 3. CSRF 保护

- **D-09:** 选型 — 加依赖 `Flask-WTF`(其依赖 `WTForms` 会作为传递依赖装入,但我们只使用 CSRF 部分,不引入 WTForms 表单类)。
- **D-10:** 接入方式 — `app.__init__` 中 `CSRFProtect(app)` 启用全局 POST 验证;在 5 个表单模板 (`register.html` / `signin.html` / `add.html` / `modify.html` / `result.html` 中的搜索表单) 添加 `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`。
- **D-11:** 失败反馈 — 验证失败时由 Flask-WTF 默认抛 400,需在 `app.errorhandler(400)` 中改为 **302 回原页 + flash "会话已过期,请重试"**。
- **D-12:** AJAX/header 验证 — Phase 2 **不**暴露 `X-CSRFToken` header 入口、不在 base 模板印 `<meta name="csrf-token">`。Phase 4 引入 HTMX 时再补。

### 4. /api/reset 收口

- **D-13:** 双重入口 — **同时**保留 `GET /api/reset` 路由(开发体验) + 新增 `flask init-db` CLI(容器初始化走这条)。
- **D-14:** 路由守卫 — `app.debug=False` 时 `/api/reset` 返回 `abort(404)`。README 必须明示"生产部署设 `FLASK_DEBUG=0`"或"使用 gunicorn 启动(自动 `debug=False`)"。
- **D-15:** 重置语义 — `drop_all()` → `create_all()` → 灌 7 条种子词条 + admin 账号 `a`/`a`(hash 化,`is_admin=True`)。逻辑抽到模块函数 `init_db()`(在 `app/api/model.py` 或新文件 `app/cli.py`),路由和 CLI 都调用同一函数。
- **D-16:** CLI 注册 — 在 `app/__init__.py` 用 `@app.cli.command("init-db")` 注册(也可用 `flask --app run init-db` 调用)。`flask init-db` 与现有 `flask run` 同级命令空间,不需要额外建 Click group。

### 5. 错误页

- **D-17:** 范围 — 实现 `errorhandler(404)` + `errorhandler(500)` + `errorhandler(403)`,统一渲染 `app/templates/error.html`(从 base 模板继承,显示状态码 + 简短说明 + 返回首页链接)。
- **D-18:** 生产安全 — 关闭 `app.debug`,错误页不再暴露 traceback;traceback 仍写 stderr / 日志(Flask 默认行为)。
- **D-19:** Phase 2 范围边界 — `400` 错误专门服务 CSRF 失败场景(见 D-11);`401` 当前未直接使用(Flask-Login 自带 `login_manager.unauthorized()` 跳转登录页),不在 Phase 2 改 login_view 行为。

### 6. 管理员删除接口

- **D-20:** 路径选择 — 新建 `/api/admin/lemma/<int:lemma_id>/delete` (POST) 走独立 admin 蓝图(`app/api/admin.py`)。**不**复用 `/api/lemma/<id>/delete`(留作 v2 / 通用删除)。失败返回 403 走 D-17 错误页。
- **D-21:** 权限校验 — 自定义装饰器 `@admin_required`,内含 `@login_required` + `current_user.is_admin` 校验,非 admin 返回 `abort(403)`。
- **D-22:** 详情页入口 — 在 `app/templates/detail.html` 顶部加条件渲染块 `{% if current_user.is_authenticated and current_user.is_admin %}...删除按钮...{% endif %}`。模板当前为旧 jQuery/Bootstrap 3 风格,本阶段 **只**加这块条件块,不动整体样式。
- **D-23:** `User` 模型扩展 — `is_admin: db.Column(db.Boolean, default=False)`。**不**改 `UserMixin` 来源(它本就提供 `is_authenticated` 等)。

### 7. CLI 工具

- **D-24:** `flask promote-admin <username>` — 走 `@app.cli.command("promote-admin")`,接收位置参数,找到用户后设 `is_admin=True` 并 commit;找不到则 `print` 错误并 `sys.exit(1)`。
- **D-25:** `flask init-db` — 复用 `init_db()` 模块函数(见 D-15)。

### Claude's Discretion

- **CD-01:** `werkzeug.security` 默认迭代次数随版本升级(2.3+ 默认 600k)。本项目保持默认值,不手动传 `pbkdf2:sha256:600000` 参数 — 这样未来 Werkzeug 升级会自动跟上安全基线。
- **CD-02:** `instance/.flask_secret` 文件权限 — 写文件时不手动 `os.chmod`,由创建时的 umask 决定。README 可建议生产用 `chmod 600`,但不强制。
- **CD-03:** 错误页 `error.html` 是否继承 base 模板 — Phase 2 没有 base 模板(7 个模板各自独立),所以 `error.html` 写成自包含 HTML(与 `signin.html` / `register.html` 同等简单),不复用任何 layout。Phase 4 引入 base 后再统一重构。

## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### 项目元信息
- `.planning/PROJECT.md` — 项目核心价值、v1 范围、Out of Scope 排除清单
- `.planning/REQUIREMENTS.md` — v1 46 条需求,Phase 2 对应 AUTH-01..06 / ROLE-01..03 / INFRA-05,06,09
- `.planning/ROADMAP.md` § Phase 2 — 阶段目标 + 成功标准 6 条 + 计划 2.1/2.2/2.3 拆分
- `.planning/STATE.md` — Phase 1 已完成、累计上下文、Discovered Constraints(尤其 INFRA-09 必须在 Phase 2 完成、COMMENT-06 在 Phase 3 之前规划)

### 既有代码 / 决策溯源
- `.planning/phases/01-foundation-python-3-bug-fixes/01-VERIFICATION.md` — Phase 1 8/8 must-haves 全部 verified,为本阶段提供"无遗留 bug"的代码基线
- `app/__init__.py` — 现状 Flask 实例化、secret_key 硬编码、MySQL URI 拼字符串(本阶段要改的目标)
- `app/api/__init__.py` — 现状所有 POST 路由无 CSRF、`reset` 路由无守卫(本阶段要改的目标)
- `app/api/model.py` — 现状 `User.password = String(40)` 无 is_admin、`Comment.user_name` 仍为字符串(本阶段扩展 User,Comment 留 Phase 3)
- `app/route/user.py` — 蓝图名 `apple`(url_prefix `/user`),跨蓝图跳转用 `apple.<endpoint>` / `api.<endpoint>`,**不要**写 `user.<endpoint>`
- `app/templates/register.html` (以及 `signin.html` / `add.html` / `modify.html` / `result.html` / `detail.html` / `home.html`) — 现有 5 个 POST 表单需加 hidden `csrf_token`
- `requirements.txt` — 现状 4 行,本阶段加 `Flask-WTF>=1.2,<2.0`

### 锁定决策(非文档,来自本对话讨论)
- 凭据 / secret_key / CSRF / reset / admin 五大块决策见上文 D-01..D-25,无歧义可执行。

## Existing Code Insights

### Reusable Assets
- `werkzeug.security.generate_password_hash` / `check_password_hash` — 已随 Flask 安装,无需新依赖
- `flask_login.UserMixin` — 已混入 `User`,`is_authenticated` 即可用,无需自实现
- `flask_login.login_user` / `logout_user` / `login_required` — 已用,继续复用
- `flash` / `get_flashed_messages` — 现有错误反馈链路,继续复用
- `db.create_all()` / `db.drop_all()` — Phase 1 已确认在 Python 3.11 + mysqlclient 上工作正常,直接复用
- `db.session.commit()` 事务边界 — 现有风格显式 commit,继续

### Established Patterns
- **Blueprint 命名约定**: `apple` (页面) + `api` (表单提交)。本阶段新增 admin 蓝图应命名为 `admin`(Blueprint name 与 url_prefix `/api/admin` 一致),`url_for` 跨蓝图用 `api.<endpoint>` / `admin.<endpoint>`。
- **`url_for` 跳转**: 现有 `redirect(url_for('apple.home'))` / `'apple.login'` 风格保持不变。
- **错误反馈**: 现状是 `flash` + 重定向(非 JSON 响应),Phase 2 维持这种 HTML 优先的风格,不改 API 形态。
- **种子灌库**: `/api/reset` 内的 `db.session.add(...)` 链已建立,新 `init_db()` 函数直接抽离这段代码,路由和 CLI 都调它。
- **隐式 flask app context**: `@app.cli.command` 装饰器自带 app context,无需 `with app.app_context()` 包裹。

### Integration Points
- `app/__init__.py` — 改 secret_key 加载逻辑 + 加 SQLAlchemy `URL` 拼装 + 加 `CSRFProtect` + 注册 admin 蓝图 + 注册 `init-db` / `promote-admin` CLI
- `app/api/model.py` — 改 `User.password` 长度 255 + 加 `is_admin` 字段
- `app/api/__init__.py` — 改 `reset` 路由(加守卫)+ 改 `regist` / `login`(hash + 校验)+ 抽 `init_db()` 函数
- `app/api/admin.py` — **新文件**,admin 蓝图 + 装饰器 `admin_required` + 路由 `POST /api/admin/lemma/<int:id>/delete`
- `app/route/user.py` — 不动
- `app/templates/*.html` — 5 个表单加 hidden csrf_token + detail.html 顶部加 admin 按钮 + **新** `app/templates/error.html`
- `requirements.txt` — 加 `Flask-WTF>=1.2,<2.0`
- `.dockerignore` — 加 `instance/`(避免 `.flask_secret` 进镜像)
- `README.md` (在 Phase 5 改) — 本阶段只需在 dev 说明里补一句"生产 FLASK_SECRET 必须传"

## Specific Ideas

- **想法 A:** `werkzeug.security` 2.3+ 默认 `pbkdf2:sha256:600000` 迭代,在 Python 3.11 上一次 hash 约 250ms,一次验证约 250ms — 性能可接受,无需手动指定迭代次数。
- **想法 B:** `instance/.flask_secret` 容器内重 build 会丢,但**仅影响已签发 session 的失效**;用户重新登录即可。Phase 5 docker entrypoint 可加 `chmod 600 instance/.flask_secret`。
- **想法 C:** 错误页 `error.html` 写自包含 HTML(暂不引入 base 模板),与现有 `signin.html` 风格相近即可。Phase 4 再统一样式。
- **想法 D:** `flask promote-admin` 是排错/迁移用 CLI,不暴露 HTTP 接口;操作需 SSH 到服务器或 `docker exec` 进去,本身已隐含信任。

## Deferred Ideas

### 邮件 / 找回密码 / OAuth / 2FA
- 邮件验证、密码重置、第三方登录、TOTP — PROJECT.md 显式 Out of Scope,本阶段不讨论,留 v2。

### 评论与 admin 删除评论
- 评论模型、评论 admin 删除 — Phase 3 处理。Phase 2 只建 `admin` 蓝图 + `admin_required` 装饰器骨架,删评论接口留 Phase 3。

### 模板整体重设计
- 模板视觉、HTMX、Pico.css、wangEditor 替换 — Phase 4。本阶段只加最小必要改动(CSRF token 字段 + admin 按钮 + error.html)。

### Docker 部署 / 端到端 README
- `Dockerfile`、entrypoint 调 `flask init-db`、README 生产部署段 — Phase 5。本阶段产出 `init-db` CLI 给 Phase 5 调。

### 限流 / 登录失败锁定
- 暴力破解防护、登录失败计数器、IP 封禁 — v2 (V2-AUTH-03/04/05 同性质)。

### Session 有效期 / 滑动续期
- `PERMANENT_SESSION_LIFETIME`、remember-me 策略 — 本项目 demo 性质,Phase 2 维持 Flask-Login 默认(浏览器关闭即失效)。v2 再细化。

---

*Phase: 02-Security & Auth Hardening*
*Context gathered: 2026-06-11*
