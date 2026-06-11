# Phase 2: Security & Auth Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-11
**Phase:** 02-Security & Auth Hardening
**Areas discussed:** 密码 hash 选型, secret_key 加载策略, CSRF 选型, /api/reset 收口方式

---

## 密码 hash 选型

| Option | Description | Selected |
|--------|-------------|----------|
| werkzeug pbkdf2 (推荐) | Flask 同包的 generate_password_hash / check_password_hash,默认 pbkdf2:sha256(600k 迭代)。零新依赖,6 位迭代的 pbkdf2 已超 bcrypt 中档强度。 | ✓ |
| bcrypt | 行业老牌。加 bcrypt 依赖 (~100k LOC C ext),登陆时会明显变慢 (0.3s+)。调整成本一般。 | |
| argon2 (argon2-cffi) | OWASP 推荐首选。需加 argon2-cffi + cffi,需要 C 编译器(在 python:3.11-slim Docker 里多装一步)。强度最高但环境依赖重。 | |

**User's choice:** werkzeug pbkdf2 (推荐)
**Notes:** 零依赖 + 与 Flask 同源,简化部署。Phase 2 决定不引入新 hash 库。

### Follow-up Q1: User 表 password 字段需改造,选什么方案?

| Option | Description | Selected |
|--------|-------------|----------|
| 扩 String(255) + 兼容明文回退 | User.password 扩为 String(255),加检测逻辑(hash 格式 → check_password_hash,否则明文回退)。 | |
| 直接现数据库 drop_all + 重灌 (项目周期短) | Phase 1 未对现有 schema 做迁移, 跳上 Flask-Migrate 为这一列加 migration 过度;由 2.1 plan 负责 db drop_all+重灌 + 只重新种子 admin 账号。 | ✓ |
| 加 Flask-Migrate 逐列迁移 (重量级) | 加 Alembic 包装。为一个 String 长度变更引一个 migration 框架。 | |

**User's choice:** 直接现数据库 drop_all + 重灌 (项目周期短)
**Notes:** 课堂作业背景,生产数据无价值,drop_all 干净利落。Alembic 杀鸡用牛刀。

### Follow-up Q2: 登录失败提示?

| Option | Description | Selected |
|--------|-------------|----------|
| 统一提示 "账号或密码错误" | 不区分"账号不存在"和"密码错误",防账号枚举。 | ✓ |
| 区分 "用户不存在" / "密码错误" | UX 友好但会泄露账号是否存在。 | |

**User's choice:** 统一提示 "账号或密码错误"
**Notes:** 标准做法,与现有 flash 风格一致。

### Follow-up Q3: 密码验证接口设计?

| Option | Description | Selected |
|--------|-------------|----------|
| 后端验证 长度 6-30, 同名拒增 | 长度 6-30 字符(兼容中文用户名),后端必验。强密码策略留 v2。 | ✓ |
| min(6), 仅需"后端有验证" | 最小变动。 | |
| 强密码策略 (v1 提前动) | 后端正则 + 前端实时强度提示。偏重。 | |

**User's choice:** 后端验证 长度 6-30, 同名拒增
**Notes:** 中等强度,与 2017 课堂作业原始风格接近(只多了一层长度校验),不引入复杂度。

---

## secret_key 加载策略

| Option | Description | Selected |
|--------|-------------|----------|
| env 缺失则启动失败 (推荐生产路径) | FLASK_SECRET 未设 → 启动错。坏处:docker run 需 -e 必传。 | |
| env 缺失时随机生成并写文件 (dev 友好) | os.urandom(32) 生成临时密钥, 写入 .flask_secret 文件。下次启动会读取。 | ✓ |
| app.debug 下随机, 生产下 env 必传 | 仅 app.debug=True 时随机生成。 | |

**User's choice:** env 缺失时随机生成并写文件 (dev 友好)
**Notes:** 降低本地开发摩擦。README 提醒"生产必须传 FLASK_SECRET"。

### Follow-up Q1: 启动时随机生成的 key 写到哪?

| Option | Description | Selected |
|--------|-------------|----------|
| 默认写 ./instance/.flask_secret (项目内) | Flask 约定 instance 目录。容器内重起 / 重新打镜像会丢。 | ✓ |
| 默认写 $HOME/.baike_secret (用户主目录) | docker run -v 挂主机卷能跨重启,但需 README 明示。 | |
| 必须读 FLASK_SECRET_FILE env, 缺失仅随机生成不落盘 | 重启丢,会登出所有用户。 | |

**User's choice:** 默认写 ./instance/.flask_secret (项目内)
**Notes:** 与 Flask 惯例对齐。Phase 5 写 Dockerfile 时需在 .dockerignore 排除 `instance/`,避免密钥进镜像。

### Follow-up Q2: DB 凭据 env 变量缺失时?

| Option | Description | Selected |
|--------|-------------|----------|
| env 缺失则启动失败 (推荐) | DB_HOST / DB_USER 等任一缺失 → raise RuntimeError 启动失败。 | ✓ |
| env 缺失则启动失败 + 友好错误信息 | 不提供默认值,不静默连 localhost。 | |
| env 缺失则回退 原硬编码值 (与 INFRA-09 冲突) | 不推荐。 | |

**User's choice:** env 缺失则启动失败 (推荐)
**Notes:** 与 INFRA-09 一致,杜绝明文凭据二次泄露。

### Follow-up Q3: DB 凭据 URI 是否加 quote 编码?

| Option | Description | Selected |
|--------|-------------|----------|
| SQLAlchemy URL 对象 + quote_plus (推荐) | sqlalchemy.engine.url.URL + urllib.parse.quote_plus。适应含 @ / 特殊字符密码。 | ✓ |
| 原始 %s 拼字符串 (与现状一致) | 偏小改动,但与"产品基线"目标有差距。 | |
| 改用 mysql+pymysql 驱动 | 不推荐,需重装依赖。 | |

**User's choice:** SQLAlchemy URL 对象 + quote_plus
**Notes:** 标准做法,与 SQLAlchemy 官方推荐一致。

### Follow-up Q4: 默认账号 `a` 的种子数据?

| Option | Description | Selected |
|--------|-------------|----------|
| 保留 a/a 默认账号 + 升级为 admin (推荐) | reset 时哈希存储密码, admin 标志在 reset 中设为 True。 | ✓ |
| 默认账号哈希 + 升级为 admin + 提示改密 | 多一层提示,UX 更友好。 | |
| 默认账号不设为 admin, admin 需单独设 | 第一个用户需用 flask promote-admin 手动升。 | |

**User's choice:** 保留 a/a 默认账号 + 升级为 admin
**Notes:** demo 友好 — 用户用默认账号登录就能看到 admin 视图。README 提醒"生产改密"。

---

## CSRF 选型

| Option | Description | Selected |
|--------|-------------|----------|
| Flask-WTF (推荐) | 一键启用 + Jinja 隐式 token 字段。多一个依赖,与 Phase 4 重设计兼容。 | ✓ |
| itsdangerous 手写 CSRF token | 零新依赖,需在 5 个表单里手写 hidden input + server 端验签。 | |
| 不启用 CSRF (与 INFRA-04 冲突) | 依赖 HTTPS + SameSite cookie。HTTP demo 不推荐。 | |

**User's choice:** Flask-WTF
**Notes:** 行业标准,一行启用,文档完备。

### Follow-up Q1: Flask-WTF 怎么接入?

| Option | Description | Selected |
|--------|-------------|----------|
| CSRFProtect(app) + 每个表单加 hidden csrf_token | 启用全局 POST 验证 + 在 5 个表单模板手写 hidden input。 | ✓ |
| FlaskForm 重构表单 | 将所有表单重写为 FlaskForm 类,接近 Phase 4 重设计。 | |
| 仅变动模板, 不重构后端 | 模板加 token,后端读 request.form.get('csrf_token') 验证。Flask-WTF 默认自动验证,改模板即可。 | |

**User's choice:** CSRFProtect(app) + 每个表单加 hidden csrf_token
**Notes:** Flask-WTF 默认从 form/header 读 csrf_token,改模板后路由无需变。

### Follow-up Q2: 是否提供 AJAX/HTTP 头部 CSRF 验证?

| Option | Description | Selected |
|--------|-------------|----------|
| HTML 表单 only, 暂不提供 X-CSRFToken (推荐) | Phase 2 只覆盖 HTML 表单;HTMX/JSON API 入口是 Phase 4。 | ✓ |
| 额外暴露 X-CSRFToken header 验证 (为 Phase 4 准备) | 模板印 csrf_token meta 标签,HTMX 可从 meta 读。 | |

**User's choice:** HTML 表单 only, 暂不提供 X-CSRFToken
**Notes:** Phase 4 引入 HTMX 时再补。避免 Phase 2 范围漂移。

### Follow-up Q3: CSRF 验证失败怎么返?

| Option | Description | Selected |
|--------|-------------|----------|
| CSRF 验证失败: 302 回原页 + flash (推荐) | "Session 已过期, 请重试"的 flash。 | ✓ |
| CSRF 验证失败: 纯 JSON 400 错误 | 适合 API 服务,与现有 HTML 风格不一致。 | |
| 静默丢弃 POST | 不推荐。 | |

**User's choice:** CSRF 验证失败: 302 回原页 + flash
**Notes:** 与现有 flash 风格一致。需在 `app.errorhandler(400)` 中改默认行为。

---

## /api/reset 收口方式

| Option | Description | Selected |
|--------|-------------|----------|
| 改为 flask init-db CLI (推荐) | 删 /api/reset 路由,实现 flask init-db CLI。 | |
| 保留 /api/reset 路由 + app.debug 守卫 | 加 if not app.debug: abort(404)。 | |
| 同时保留 路由 + 补 CLI (谁先调用谁) | 两者都保留,公开 URL 在生产被干死,CLI 总是可调用。 | ✓ |

**User's choice:** 同时保留 路由 + 补 CLI
**Notes:** 兼顾开发体验(demo URL 一键重置)+ 容器初始化(Phase 5 调 CLI)。

### Follow-up Q1: /api/reset 生产守卫?

| Option | Description | Selected |
|--------|-------------|----------|
| 仅 app.debug 守卫 (推荐) | if not app.debug: abort(404)。README 提醒"生产部署必须设 debug=False"。 | ✓ |
| 加 环境变量 守卫 | 加 ALLOW_DB_RESET=true env 检查。 | |
| 不加 守卫 | 不推荐。 | |

**User's choice:** 仅 app.debug 守卫
**Notes:** gunicorn 启动自动 debug=False,守卫生效;README 明示即可。

### Follow-up Q2: 种子 data 行为?

| Option | Description | Selected |
|--------|-------------|----------|
| 先 drop_all 再 create_all + 灌种子 (推荐) | 保留现有 db.drop_all() + db.create_all() + 重灌 7 个示例词条 + 默认账号。 | ✓ |
| 仅 create_all (不抹) 增量补充种子 | 与 "reset" 语义不符。 | |
| 加 alembic 迁移 (重量级) | 与已选 drop_all 冲突。 | |

**User's choice:** 先 drop_all 再 create_all + 灌种子
**Notes:** 与现有 reset 路由行为完全一致,无行为漂移。

---

## Claude's Discretion

- **CD-01:** pbkdf2 迭代次数不手动指定,跟随 werkzeug.security 默认值升级(2.3+ 默认 600k)
- **CD-02:** `instance/.flask_secret` 不手动 chmod,创建时由 umask 决定
- **CD-03:** `error.html` 自包含 HTML,不引入 base 模板(Phase 2 范围内最小化改动)

## Deferred Ideas

- **邮件验证 / 找回密码 / OAuth / 2FA** — PROJECT.md Out of Scope,v2 再议
- **评论与 admin 删除评论** — Phase 3 处理
- **模板整体重设计 / HTMX / Pico.css / wangEditor 替换** — Phase 4
- **Docker 镜像 / README 端到端** — Phase 5(本阶段产出 `init-db` CLI 给 Phase 5 用)
- **限流 / 登录失败锁定** — v2
- **Session 有效期 / 滑动续期** — v2(Phase 2 保持 Flask-Login 默认)
