# Requirements: 互动百科 产品化升级

**Defined:** 2026-06-11
**Core Value:** 一个陌生开发者能根据 README 启动 Docker 容器、注册账号、创建词条、发布评论、并以管理员身份看到完整端到端流程。

## v1 Requirements

按功能域组织。每条对应一次可观察的端到端行为。

### Authentication & Authorization

- [ ] **AUTH-01**: User can register with username + password (password is stored hashed, never plaintext)
- [ ] **AUTH-02**: User can log in with username + password and stay logged in across browser refresh
- [ ] **AUTH-03**: User can log out from any page
- [ ] **AUTH-04**: All forms require a valid CSRF token; submissions without one are rejected
- [ ] **AUTH-05**: MySQL connection credentials and Flask `secret_key` come from environment variables, not from source code
- [ ] **AUTH-06**: `User` table has an `is_admin` boolean field; a `flask promote-admin <username>` CLI command flips it

### User Roles

- [ ] **ROLE-01**: Admin can delete any lemma from the detail page
- [ ] **ROLE-02**: Admin can delete any comment from the detail page
- [ ] **ROLE-03**: Non-admin users see no admin-only controls; admin controls are visible only to admins

### Lemma (Core Content)

- [ ] **LEMMA-01**: Logged-in user can create a lemma with a title and rich-text content
- [ ] **LEMMA-02**: Logged-in user can edit an existing lemma from its detail page; submission persists and redirects to the home page (no 500/blank-page error)
- [ ] **LEMMA-03**: Logged-in user can search lemmas by partial title match; results are listed with title and snippet
- [ ] **LEMMA-04**: User can view a lemma detail page showing title, content, last-edited timestamp, view count, comments, and related/backlinks
- [ ] **LEMMA-05**: The detail page view increments the lemma's view counter atomically (no race condition lost-update)
- [ ] **LEMMA-06**: The detail page shows "最后编辑于 YYYY-MM-DD HH:MM by <username>" based on the lemma's `updated_at` field
- [ ] **LEMMA-07**: Lemma content supports `[[词条名]]` wiki-link syntax; on render, it becomes a link to that lemma's detail page; non-existent targets render as a red dashed link with "(创建此词条)" affordance
- [ ] **LEMMA-08**: The detail page shows a "相关词条" (related lemmas) section listing lemmas whose content contains `[[本词条标题]]`

### Comments

- [ ] **COMMENT-01**: Logged-in user can post a comment on a lemma detail page via a `POST /api/comment` endpoint
- [ ] **COMMENT-02**: Comment form is hidden / disabled for anonymous users; anonymous POSTs are rejected
- [ ] **COMMENT-03**: Lemma detail page lists all comments in reverse chronological order (newest first)
- [ ] **COMMENT-04**: Comment author sees a "删除" button on their own comments; clicking it removes the comment after confirmation
- [ ] **COMMENT-05**: Non-authors see no delete button; a direct `POST /api/comment/<id>/delete` from a non-author returns 403
- [ ] **COMMENT-06**: `Comment` table has a foreign key to `User` (via `user_id` integer column) so renames of username don't orphan historical comments
- [ ] **COMMENT-07**: Comment deletion is hard-delete; deleted comments no longer appear in lists

### Frontend Modernization

- [ ] **FRONT-01**: No jQuery is used anywhere in templates or static assets; legacy `app/static/javascripts/jquery.min.js` is removed
- [ ] **FRONT-02**: HTMX (latest stable) is loaded and used for partial page updates (search-as-you-type, comment posting, etc.)
- [ ] **FRONT-03**: Bootstrap 3 CSS/JS is removed; Pico.css (or equivalent classless CSS framework) provides base styling
- [ ] **FRONT-04**: wangEditor 2.x is replaced with a modern rich-text editor (Quill / EasyMDE / Tiptap — final choice made at planning time)
- [ ] **FRONT-05**: All seven templates (home / signin / register / add / modify / result / detail) are redesigned for visual consistency and basic accessibility (semantic HTML, color contrast, focus states)
- [ ] **FRONT-06**: Wiki-link `[[标题]]` parsing happens both at write-time (server sanitization) and at render-time (template link generation)

### Infrastructure & Quality

- [ ] **INFRA-01**: Application runs on Python 3.11+; no `reload(sys)` / `sys.setdefaultencoding` calls remain
- [ ] **INFRA-02**: `mysql-python` (MySQLdb) is replaced with `mysqlclient`; `requirements.txt` is updated and the venv can be re-built from scratch
- [ ] **INFRA-03**: `app/api/model.py` no longer creates a duplicate `Flask(__name__)` instance; only `app/__init__.py` constructs the app
- [ ] **INFRA-04**: The `__tablenanme__` typo is fixed in all three models (`User`, `Lemma`, `Comment`); table names are explicit
- [ ] **INFRA-05**: `/api/reset` is no longer exposed in production; it is either guarded by `if not app.debug: abort(404)` or replaced with a `flask init-db` CLI command
- [ ] **INFRA-06**: A single 404 handler and a single 500 handler render a unified Jinja error page (no default Flask debug page in production)
- [ ] **INFRA-07**: A `Dockerfile` (multi-stage, `python:3.11-slim` base) builds a runnable image that starts the app via gunicorn on port 8000
- [ ] **INFRA-08**: Container entrypoint runs `flask init-db` (idempotent) on first start, then starts gunicorn; the public `/api/reset` URL is removed from the running image
- [ ] **INFRA-09**: All runtime configuration is read from env vars: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `FLASK_SECRET`; no defaults fall back to `root`/`123456`
- [ ] **INFRA-10**: README contains a "Production deploy" section: build image, `docker run -e DB_HOST=… -e …`, place behind an external nginx reverse proxy, point at an external MySQL — full steps a third party can follow
- [ ] **INFRA-11**: `.dockerignore` keeps build context under 50 MB (excludes `.venv/`, `.git/`, `__pycache__/`, `*.pyc`, etc.)

### Tests & Acceptance

- [ ] **TEST-01**: `pytest` + `pytest-flask` are installed; a `tests/` directory exists with at least a smoke test file
- [ ] **TEST-02**: `tests/test_smoke.py` runs an end-to-end flow in a single test: register → login → create lemma → search → open detail → edit lemma → post comment → delete own comment, asserting each step
- [ ] **TEST-03**: `tests/test_admin.py` (or extension of test_smoke) verifies: admin can delete any lemma and any comment; non-admin attempting same gets 403
- [ ] **TEST-04**: `make test` (or `pytest` invocation) passes locally on a fresh venv; README documents how to run
- [ ] **TEST-05**: A third party, starting from a clean checkout and following only README, can `docker run` the image against a fresh external MySQL + external nginx reverse proxy, complete the smoke flow in a browser, and see all v1 features work

## v2 Requirements

Deferred to a future milestone. Tracked but not in current roadmap.

- **V2-AUTH-01**: Email verification flow
- **V2-AUTH-02**: Password reset via email
- **V2-AUTH-03**: OAuth / third-party login (Google / GitHub)
- **V2-AUTH-04**: 2FA / TOTP
- **V2-CONTENT-01**: Lemma revision history with diff viewer
- **V2-CONTENT-02**: Full-text search (Elasticsearch / Meilisearch)
- **V2-CONTENT-03**: Lemma protection / lock
- **V2-CONTENT-04**: Editor / moderator role
- **V2-COMMENT-01**: Comment editing (not just deletion)
- **V2-COMMENT-02**: Comment threading / replies
- **V2-OPS-01**: GitHub Actions CI for smoke tests
- **V2-OPS-02**: K8s manifests / Helm chart
- **V2-OPS-03**: Application monitoring (Prometheus / OpenTelemetry)
- **V2-FRONT-01**: Internationalization (i18n)
- **V2-FRONT-02**: Mobile app / PWA
- **V2-FRONT-03**: Real-time updates via SSE / WebSocket

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| OAuth / 第三方登录 | 用户名+密码 + admin 标志已满足产品雏形,集成 OAuth 增加配置面 |
| 2FA / TOTP | 课堂作业环境不需要 |
| 邮件验证 / 找回密码 | 需要 SMTP 凭据,产品雏形不引入外部依赖 |
| 实时聊天 / WebSocket | 与"词条 + 评论"核心场景无关 |
| 词条版本历史 / diff | 复杂,需要新表和 UI |
| 全文搜索 (Elasticsearch) | SQL `LIKE` 对小数据集够用,引入 ES 显著增加运维成本 |
| K8s 部署 / Helm chart | 假设生产用外部编排,本项目只交付单 Flask 容器 |
| CI/CD pipeline | smoke 测试本地 `make test` 跑过即可 |
| 移动端 App / PWA | 响应式 Web 已足够 |
| 多语言 i18n | 单一中文界面 |
| React/Vue 等 SPA | 与"无重前端"诉求冲突 |
| 编辑者 / 版主等中间角色 | v1 只用 regular + admin 二元角色 |
| 词条保护 / 锁定 | 任何登录用户都可编辑,管理员可删除兜底 |

## Traceability

由 roadmapper 在路线图创建时填充。当前为空 — 路线图阶段会决定每个 requirement 属于哪个 phase。

| Requirement | Phase | Status |
|-------------|-------|--------|
| (待 roadmap 填充) | | |

**Coverage:**
- v1 requirements: 41 total
- Mapped to phases: 0
- Unmapped: 41 ⚠️ (待 roadmap 完成)

---
*Requirements defined: 2026-06-11*
*Last updated: 2026-06-11 after brownfield project initialization*
