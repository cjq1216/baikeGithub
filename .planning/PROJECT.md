# 互动百科 (Hudong Baike) — 产品化升级

## What This Is

一个 Flask + MySQL 互动百科的现代化升级项目,基于 2017 年软工大作业(641 宿舍)的 Python 2 时代代码,经 v1.0 升级后已成为"可部署演示的产品雏形"。v1.0 涵盖了 Python 3 迁移、bug 修复、安全加固、评论系统、前端现代化、Docker 化与 smoke 测试;陌生开发者 clone 仓库后,凭 README 即可拉起 Docker 容器、注册账号、创建词条、发布评论、并以管理员身份看到完整端到端流程。

## Core Value

**一个陌生开发者能根据 README 启动 Docker 容器、注册账号、创建词条、发布评论、并以管理员身份看到完整端到端流程。**v1.0 已达成,v2 应在此基础上扩展。

## Current State (after v1.0 SHIPPED 2026-06-12)

- **5 phases, 12 plans, 46/46 v1 requirements complete**
- 3 pytest tests passing(端到端 smoke + admin 双向权限)
- 8/8 ROADMAP SUCCESS criteria verified
- Verifier verdict: PASS (high confidence)
- Code: ~813 Python + ~467 templates LOC
- 4 acknowledged deviations, all acceptable(no docker daemon / Makefile Windows / conftest engine hack / LegacyAPIWarning)
- See `.planning/milestones/v1.0-ROADMAP.md` for full archive
- See `.planning/milestones/v1.0-REQUIREMENTS.md` for requirements traceability

## Requirements

### Validated (v1.0 — SHIPPED 2026-06-12)

**Authentication & Authorization**(AUTH-01..06, INFRA-09)
- ✓ User can register with username + password (hashed, never plaintext) — v1.0
- ✓ User can log in and stay logged in across browser refresh — v1.0
- ✓ User can log out from any page — v1.0
- ✓ All forms require a valid CSRF token — v1.0
- ✓ MySQL credentials and Flask secret_key come from env vars — v1.0
- ✓ User has `is_admin` boolean; `flask promote-admin <username>` CLI — v1.0

**User Roles**(ROLE-01..03)
- ✓ Admin can delete any lemma — v1.0
- ✓ Admin can delete any comment — v1.0
- ✓ Non-admin users see no admin-only controls — v1.0

**Lemma Core Content**(LEMMA-01..08)
- ✓ Logged-in user can create a lemma (title + rich-text content) — v1.0
- ✓ Logged-in user can edit an existing lemma — v1.0
- ✓ Logged-in user can search lemmas by partial title match — v1.0
- ✓ User can view lemma detail page(title/content/timestamp/views/comments/backlinks) — v1.0
- ✓ Detail page view increments view counter atomically(no race) — v1.0
- ✓ Detail page shows "最后编辑于 YYYY-MM-DD HH:MM by <username>" — v1.0
- ✓ Lemma content supports `[[词条名]]` wiki-link syntax — v1.0
- ✓ Detail page shows "相关词条" (backlinks) section — v1.0

**Comments**(COMMENT-01..07)
- ✓ Logged-in user can post a comment via POST /api/comment — v1.0
- ✓ Comment form hidden for anonymous; anonymous POSTs rejected — v1.0
- ✓ Comments listed in reverse chronological order — v1.0
- ✓ Author sees "删除" button on own comments — v1.0
- ✓ Non-authors see no delete button; non-author POST returns 403 — v1.0
- ✓ Comment has user_id FK to User (no orphan on rename) — v1.0
- ✓ Comment deletion is hard-delete — v1.0

**Frontend Modernization**(FRONT-01..06)
- ✓ No jQuery in templates or assets — v1.0
- ✓ HTMX (latest stable) used for partial updates — v1.0
- ✓ Bootstrap 3 removed; Pico.css provides base styling — v1.0
- ✓ wangEditor 2.x replaced with Quill 2.x (local vendor) — v1.0
- ✓ All 7 templates redesigned for visual consistency + accessibility — v1.0
- ✓ Wiki-link parsing at write-time (bleach) + render-time (Jinja filter) — v1.0

**Infrastructure**(INFRA-01..11)
- ✓ App runs on Python 3.11+; no reload(sys) — v1.0
- ✓ mysql-python replaced with mysqlclient — v1.0
- ✓ Single Flask app construction site in app/__init__.py — v1.0
- ✓ __tablename__ typo fixed in all 3 models — v1.0
- ✓ /api/reset guarded in production; `flask init-db` CLI exposed — v1.0
- ✓ Unified 404/500 error pages — v1.0
- ✓ Dockerfile multi-stage python:3.11-slim + gunicorn :8000 — v1.0
- ✓ Container entrypoint: flask init-db --if-empty (idempotent) + gunicorn — v1.0
- ✓ All runtime config from env vars (DB_HOST/PORT/USER/PASSWORD/NAME + FLASK_SECRET) — v1.0
- ✓ README "Production deploy" section with full third-party-followable steps — v1.0
- ✓ .dockerignore keeps build context < 50MB — v1.0

**Tests & Acceptance**(TEST-01..05)
- ✓ pytest + pytest-flask installed; tests/ directory exists — v1.0
- ✓ test_smoke.py runs end-to-end single test (9 steps, each asserted) — v1.0
- ✓ test_admin.py verifies admin delete + non-admin 403 — v1.0
- ✓ make test / pytest passes on fresh venv; README documents how — v1.0
- ✓ Third-party can clone + docker run + nginx reverse proxy + smoke flow — v1.0

### Active (V2 backlog, see `.planning/REQUIREMENTS.md` § v2 Requirements if created)

(Empty for now — V2 planning pending `/gsd-new-milestone`)

### Out of Scope (reaffirmed v1.0)

| Feature | Reason | Status |
|---------|--------|--------|
| OAuth / 第三方登录 | 用户名+密码 + admin 标志已满足产品雏形 | ✓ Maintained v1.0 |
| 2FA / TOTP | 课堂作业环境不需要 | ✓ Maintained v1.0 |
| 邮件验证 / 找回密码 | 需要 SMTP 凭据,产品雏形不引入外部依赖 | ✓ Maintained v1.0 |
| 实时聊天 / WebSocket | 与"词条 + 评论"核心场景无关 | ✓ Maintained v1.0 |
| 词条版本历史 / diff | 复杂,需要新表和 UI | ✓ Maintained v1.0 |
| 全文搜索 (Elasticsearch) | SQL LIKE 对小数据集够用 | ✓ Maintained v1.0 |
| K8s 部署 / Helm chart | 假设生产用外部编排 | ✓ Maintained v1.0 |
| CI/CD pipeline | smoke 测试本地 make test 跑过即可 | ✓ Maintained v1.0 |
| 移动端 App / PWA | 响应式 Web 已足够 | ✓ Maintained v1.0 |
| 多语言 i18n | 单一中文界面 | ✓ Maintained v1.0 |
| React/Vue 等 SPA | 与"无重前端"诉求冲突 | ✓ Maintained v1.0 |
| 编辑者 / 版主等中间角色 | v1 只用 regular + admin 二元角色 | ✓ Maintained v1.0 |
| 词条保护 / 锁定 | 任何登录用户都可编辑(管理员可删除兜底) | ✓ Maintained v1.0 |

## Next Milestone Goals (V2 candidates)

V2 候选需求已在 `.planning/REQUIREMENTS.md` § v2 Requirements 中跟踪(19 条:V2-AUTH-01..04 / V2-CONTENT-01..04 / V2-COMMENT-01..02 / V2-OPS-01..03 / V2-FRONT-01..03 / V2-AUTH-05 / V2-OPS-04)。V2 milestone 启动前需 `/gsd-new-milestone` 走 questioning → research → requirements → roadmap 流程。

**特别推荐 V2 优先项**:
1. **V2-OPS-01** GitHub Actions CI(smoke tests 自动跑) — 解决"dev 端无 docker daemon,实际验证需 CI" 的痛点
2. **V2-OPS-04** `/healthz` endpoint + Docker HEALTHCHECK — 解决"运维通过 gunicorn 启动日志判断就绪" 的人肉操作
3. **V2-AUTH-01** Email 验证 — 提升用户信任
4. **V2-CONTENT-01** Lemma revision history + diff viewer — 知识库型产品的强需求
5. **V2-FRONT-03** Real-time updates via SSE/WebSocket — 让评论/浏览数实时刷新

### Active

(本次升级的 v1 范围)

#### 阶段 A: 修 bug + Python 3 迁移(代码本体)

- [ ] **A-01**: 修复 `/api/modify` 提交后无 return/redirect 的 500/空白页 bug
- [ ] **A-02**: 修复 `/user/detail` 返回 `BaseQuery` 而非结果列表的隐患(加 `.all()` + None 守卫)
- [ ] **A-03**: 修复 `__tablenanme__` typo,改为 `__tablename__` (三处:`app/api/model.py:18,32,47`)
- [ ] **A-04**: 移除 `app/api/model.py:9-11` 重复创建的 `Flask(__name__)` 实例,改用统一的 `db.init_app(app)` 模式
- [ ] **A-05**: `/api/reset` 加上 `if not app.debug: abort(404)` 保护,或改为 CLI 命令
- [ ] **A-06**: 迁移到 Python 3:删除 `reload(sys)` 和 `sys.setdefaultencoding('utf8')`(`app/__init__.py` 顶部)
- [ ] **A-07**: `mysql-python` 替换为 `mysqlclient`(`requirements.txt` + 重新生成 venv)
- [ ] **A-08**: 验证整个注册/登录/词条 CRUD/搜索流程在 Python 3.11+ 上完整跑通

#### 阶段 B: 评论功能实装

- [ ] **B-01**: 解除 `app/api/__init__.py:76-85` `/api/commen` 路由注释,实装 `POST` 发布评论接口
- [ ] **B-02**: 详情页 `detail.html` 展示该词条下全部评论(按时间倒序)
- [ ] **B-03**: `detail.html` 提供评论发布表单(仅登录用户可见,无内容时 disabled)
- [ ] **B-04**: 评论作者可删除自己的评论(加作者校验,他人的评论不显示删除按钮 / 接口校验 user_name)
- [ ] **B-05**: 评论模型 `Comment.user_name` 建立外键到 `User.name` (或加 `user_id` 列,避免 username 改名后历史评论失主)
- [ ] **B-06**: 评论删除采用软删除或硬删除 — 决策待定(本项目用硬删除 + 审计日志)

#### 阶段 C: 安全 / 质量重构

- [ ] **C-01**: MySQL 凭据从代码硬编码改为读 `config.ini` / 环境变量
- [ ] **C-02**: `secret_key` 从硬编码改为启动时从环境变量生成(或首次启动随机生成并写入 `.flask_secret`)
- [ ] **C-03**: 密码存储从明文改为 `werkzeug.security.generate_password_hash` + `check_password_hash`
- [ ] **C-04**: 全站表单启用 CSRF 保护(Flask-WTF 或手工 CSRF token)
- [ ] **C-05**: `User` 表增加 `is_admin: Boolean = False` 字段,提供 `flask promote-admin <username>` CLI 命令
- [ ] **C-06**: 管理员可删除任意词条 / 评论(`/api/admin/...` 接口 + 详情页"管理员操作"区)
- [ ] **C-07**: 全局错误处理:404 / 500 统一返回友好的 Jinja 错误页

#### 阶段 D: 现代化前端

- [ ] **D-01**: 移除 jQuery 1.11,改为 HTMX(交互)+ Alpine.js(局部状态)
- [ ] **D-02**: 移除 Bootstrap 3,改为 Pico.css(或同类无 class CSS 框架)
- [ ] **D-03**: 替换 wangEditor 2.x 为现代轻量富文本(候选:Quill / EasyMDE / Tiptap;按体积/中文友好度决断)
- [ ] **D-04**: 重新设计 home / detail / search / add / modify / login / register 模板,统一视觉与可访问性
- [ ] **D-05**: 实现词条详情页中的 `[[词条名]]` → 详情页链接的 wiki 链接解析(后端 + 前端双重处理)

#### 阶段 E: 产品特性增强

- [ ] **E-01**: `Lemma` 表增加 `updated_at: DateTime` 字段,详情页显示"最后编辑于 YYYY-MM-DD HH:MM"
- [ ] **E-02**: `Lemma` 表增加 `view_count: Integer = 0` 字段,详情页 GET 时 `+1`,详情页显示浏览数
- [ ] **E-03**: wiki 链接语法:词条内容中 `[[标题]]` 渲染为到对应词条详情页的链接,目标不存在时显示为红色虚线 + "(创建此词条)" 引导
- [ ] **E-04**: 词条详情页底部增加"相关词条"区,显示通过 wiki 链接引用了本词条的其他词条(基于反向 link 解析)

#### 阶段 F: Docker 部署

- [ ] **F-01**: 编写生产 `Dockerfile` (python:3.11-slim 基础 + gunicorn 启动)
- [ ] **F-02**: 镜像内 `entrypoint.sh` 在首次启动时自动 `flask init-db`(不再暴露 `/api/reset`)
- [ ] **F-03**: 配置通过环境变量注入:`DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` / `FLASK_SECRET`
- [ ] **F-04**: 不打包 nginx / MySQL;只发布 Flask 应用镜像,假设基础设施已有(README 说明)
- [ ] **F-05**: README 包含"外部 nginx + 外部 MySQL 下,如何 docker run + 反代 + 数据库初始化"完整步骤
- [ ] **F-06**: 提供 `.dockerignore`,镜像构建上下文控制在 < 50 MB

#### 阶段 G: 测试与验收

- [ ] **G-01**: 加 `pytest` + `pytest-flask` 测试基础设施
- [ ] **G-02**: 编写 smoke 测试:`tests/test_smoke.py` 覆盖以下端到端流程
  - 注册新用户 → 登录 → 创建词条 → 搜索命中 → 进入详情 → 修改词条 → 发布评论 → 删除自己的评论
  - 管理员登录 → 删除任意词条 / 评论
- [ ] **G-03**: 提供 `make test` / `make smoke` 命令,README 列出验证步骤
- [ ] **G-04**: 验证 Docker 镜像在干净的外部 MySQL + nginx 反代下,根据 README 可被第三方拉起并演示

### Out of Scope

显式排除(本 v1 不做),记录理由防止范围漂移:

| 排除项 | 理由 |
|--------|------|
| OAuth / 第三方登录 (Google/GitHub) | 用户名+密码 + admin 标志已满足产品雏形,集成 OAuth 增加配置面 |
| 2FA / TOTP | 课堂作业环境不需要,可作为 v2 |
| 邮件验证 / 找回密码 | 需要 SMTP 凭据,产品雏形阶段不引入外部依赖 |
| 实时聊天 / WebSocket | 与"词条 + 评论"核心场景无关 |
| 词条版本历史 / diff | 复杂,需要新表和 UI,v2 再做 |
| 全文搜索 (Elasticsearch/Meilisearch) | SQL `LIKE` 对小数据集够用,引入 ES 显著增加运维成本 |
| K8s 部署 / Helm chart | 假设生产用外部编排,本项目只交付单 Flask 容器 |
| CI/CD pipeline | smoke 测试本地 `make test` 跑过即可,无外部 CI 集成 |
| 移动端 App / PWA | 响应式 Web 已足够 |
| 多语言 i18n | 单一中文界面 |
| React/Vue 等 SPA 框架 | 与"无重前端"的诉求冲突,HTMX + Pico.css 满足动态交互 |
| 编辑者 / 版主等中间角色 | v1 只用 regular + admin 二元角色 |
| 词条保护 / 锁定 | 任何登录用户都可编辑(管理员可回滚/删除兜底) |

## Context

### 现有代码基线(从 `.planning/codebase/` 推断)

- **STACK**: Python 2.7.18 + Flask(unversioned) + Flask-Login + Flask-SQLAlchemy + mysql-python;前端 jQuery 1.11 + Bootstrap 3 + wangEditor 2.x;uwsgi 部署(`config.ini`)
- **ARCHITECTURE**: 两个 Blueprint — `apple`(`app/route/user.py`,页面渲染) + `api`(`app/api/__init__.py`,表单提交);SQLAlchemy 模型在 `app/api/model.py`
- **CONCERNS**: 5 个明确的 bug + 安全/质量债务,详细见 `.planning/codebase/CONCERNS.md`

### 项目目标语境

- 原始场景是软件架构课程大作业,代码可读性是教学目标之一;升级过程中保留原作者意图(蓝图命名 `apple` 不改),但代码风格需对齐 Python 3 + 现代 Web 实践
- 部署环境假设已有外部 nginx + 外部 MySQL(从用户答复:"nginx和数据库是外部的"),本项目只交付 Flask 应用容器
- 验收目标是"另一个人能根据 README 启动并演示",不是生产级 SLA(无 SLA,无 SLO,无监控)

### 已知上下游依赖

- 数据库:MySQL 5.7+(SQL 方言假设,使用 SQLAlchemy 抽象层减少耦合)
- 反向代理:任何兼容 HTTP/1.1 的(nginx 默认行为)
- 容器运行时:任何 OCI 兼容(Docker / Podman / containerd)

## Constraints

- **Tech stack**: 必须保留 Flask + SQLAlchemy 栈(用户原始选择),不引入 Django/FastAPI
- **Python**: v1 必须跑在 Python 3.11+(用户原始是 Python 2.7)
- **MySQL**: 外部数据库,本项目不打包不维护
- **Frontend**: 必须避免 jQuery 和 Bootstrap 3(用户答复"现代化前端"),不引入 React/Vue SPA
- **Deployment**: 单 Flask 容器,nginx + MySQL 由外部提供
- **Tests**: pytest smoke 测试,无 CI 强制要求
- **Compatibility**: 浏览器需支持 HTMX(Chrome/Firefox/Safari/Edge 最新两个大版本)
- **Documentation**: README 必须包含完整"从零启动"步骤

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 保留 Flask 而非换栈 | 升级目标不是重写,是把现有功能做扎实;换框架会让"修复 5 个 bug"变成"重写整个项目" | ✓ Good v1.0 |
| 二元角色(regular + admin) 而非三角色 | 实际场景(同学/作业环境)只需要"普通用户 + 管理员",编辑者角色增加复杂度但价值有限 | ✓ Good v1.0 |
| HTMX + Pico.css 而非 React | "现代化前端"的诉求是"摆脱 jQuery + Bootstrap 3",不一定要走 SPA;HTMX 是 server-rendered 模式下的最自然选择 | ✓ Good v1.0 |
| 词条间 wiki 链接采用 `[[标题]]` 语法 | Wikipedia / MediaWiki 既成事实,用户已熟悉,后端正则解析成本低 | ✓ Good v1.0 |
| 凭据/secret 走环境变量而非配置文件 | 容器化部署下,环境变量是十二要素应用标准做法;`config.ini` 仅留作 uwsgi 历史兼容 | — Pending |
| 评论不实装编辑(仅发布 + 作者删除) | 用户答复"基础 + 列表 + 作者可删";评论可编辑增加 UI 复杂度,对雏形价值低 | — Pending |
| Docker 不打包 nginx / MySQL | 用户答复"nginx 和数据库是外部的";降低本项目维护成本 | — Pending |
| 测试仅 smoke,不写完整测试套件 | 用户答复"加 smoke 测试";完整单测超出 v1 范围 | — Pending |

---

## Evolution

本文件在阶段转换和里程碑边界时会演进。

**每次阶段转换后(经由 `/gsd-transition`)**:
1. 需求被验证为已完成?→ 移入 `Validated`,记录阶段号
2. 需求被验证为不需要?→ 移入 `Out of Scope`,记录原因
3. 涌现新需求?→ 加入 `Active`
4. 关键决策需要记录?→ 加入 `Key Decisions`
5. "What This Is" 仍然准确?→ 漂移则更新

**每次里程碑后(经由 `/gsd-complete-milestone`)**:
1. 全面审阅所有章节
2. Core Value 仍是最高优先级?→ 否则需要 pivot
3. 审计 Out of Scope — 排除理由仍然成立?
4. 用当前状态更新 Context

---
*Last updated: 2026-06-11 after brownfield project initialization*
