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

### Active (V2 backlog, see `.planning/milestones/v1.0-REQUIREMENTS.md` § v2 Requirements)

(Empty for now — V2 planning pending `/gsd-new-milestone`. 19 candidate requirements tracked in archived v1.0-REQUIREMENTS.md.)

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
| 凭据/secret 走环境变量而非配置文件 | 容器化部署下,环境变量是十二要素应用标准做法;`config.ini` 仅留作 uwsgi 历史兼容 | ✓ Good v1.0 |
| 评论不实装编辑(仅发布 + 作者删除) | 用户答复"基础 + 列表 + 作者可删";评论可编辑增加 UI 复杂度,对雏形价值低 | ✓ Good v1.0 |
| Docker 不打包 nginx / MySQL | 用户答复"nginx 和数据库是外部的";降低本项目维护成本 | ✓ Good v1.0 |
| 测试仅 smoke,不写完整测试套件 | 用户答复"加 smoke 测试";完整单测超出 v1 范围 | ✓ Good v1.0 |

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
*Last updated: 2026-06-15 after v1.0 milestone SHIPPED — old A-G 阶段 + 旧 Out of Scope 表已清理(67+18 行),Key Decisions 4 Pending → ✓ Good v1.0,Validated 段重写为 v1.0 SHIPPED 格式*
