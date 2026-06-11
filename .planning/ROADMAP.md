# Roadmap: 互动百科 产品化升级

**Defined:** 2026-06-11
**Granularity:** coarse (3-5 phases, 1-3 plans each)
**Mode:** mvp — each phase delivers an end-to-end user capability
**Parallel:** true — independent plans within a phase may run simultaneously
**Core Value:** 一个陌生开发者能根据 README 启动 Docker 容器、注册账号、创建词条、发布评论、并以管理员身份看到完整端到端流程。

## Phases

- [ ] **Phase 1: Foundation (Python 3 + Bug Fixes)** — 让现有 Flask 应用在 Python 3.11+ 上无 bug 跑通,代码本体零隐患
- [ ] **Phase 2: Security & Auth Hardening** — 用户系统从硬编码/明文升级到环境变量 + 密码哈希 + CSRF + admin 角色,登录流程仍可端到端走通
- [ ] **Phase 3: Comment System** — 实装评论发布/列表/作者删除/管理员删除,详情页拥有完整的评论交互
- [ ] **Phase 4: Frontend Modernization & Product Features** — 模板全面重设计 + 引入 HTMX/Pico.css/新编辑器 + wiki 链接 + 最后编辑时间 + 浏览数 + 相关词条
- [ ] **Phase 5: Docker Deployment, Tests & Acceptance** — Docker 镜像 + 容器初始化 + 完整 README + pytest smoke 测试,第三方可独立端到端验收

## Phase Details

### Phase 1: Foundation (Python 3 + Bug Fixes)

**Goal**: The existing Flask app runs cleanly on Python 3.11+ with all known runtime bugs and code smells eliminated — nothing else changes.

**Mode:** mvp

**Depends on**: Nothing (first phase)

**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04

**Success Criteria** (what must be TRUE):
1. Application starts via `python run.py` on Python 3.11+ and the home page loads without 500 errors
2. A registered user can register, log in, create a lemma, search, open detail, edit, and modify returns with a redirect (no 500/blank page) — the original `/api/modify` bug is gone
3. The `/user/detail` page renders a real lemma (not a `BaseQuery`); viewing a missing lemma shows a friendly 404 page
4. `requirements.txt` installs cleanly from a fresh venv on Python 3.11+ using `mysqlclient` (no `mysql-python`); `reload(sys)` and `sys.setdefaultencoding` are removed
5. `app/api/model.py` no longer creates a duplicate `Flask(__name__)`; all three models have correct `__tablename__`

**Plans**: 2 plans
- Plan 1.1: Python 3 迁移 + 依赖替换 (INFRA-01, INFRA-02)
- Plan 1.2: 代码本体 bug 修复 + 重复 Flask 实例清理 (INFRA-03, INFRA-04)

---

### Phase 2: Security & Auth Hardening

**Goal**: The auth surface is production-grade — credentials live in env vars, passwords are hashed, CSRF is enforced, and an admin role exists for moderation. All existing user-facing auth flows still work end-to-end.

**Mode:** mvp

**Depends on**: Phase 1

**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, ROLE-01, ROLE-02, ROLE-03, INFRA-05, INFRA-06, INFRA-09

**Success Criteria** (what must be TRUE):
1. MySQL connection string and Flask `secret_key` are read from environment variables; no credentials appear in source
2. Registering a user stores a hashed password (never plaintext); logging in validates against the hash
3. All POST forms (regist / login / add / modify) reject submissions without a valid CSRF token
4. The default seeded user `a` is upgraded to admin; a `flask promote-admin <username>` CLI command flips `is_admin` on an existing user
5. A logged-in admin sees "管理员操作" controls on lemma detail pages and can delete any lemma via `/api/admin/lemma/<id>/delete`; a non-admin attempting the same call gets 403
6. Missing pages and unhandled exceptions render a unified friendly Jinja error page (no Flask debug traceback leaks in production)

**Plans**: 3 plans
- Plan 2.1: 凭据/secret 走环境变量 + 密码哈希 (AUTH-01, AUTH-02, AUTH-05, INFRA-09)
- Plan 2.2: CSRF 保护 + 统一错误页 + `/api/reset` 守卫 (AUTH-03, AUTH-04, INFRA-05, INFRA-06)
- Plan 2.3: admin 角色 + 管理员删除接口 (AUTH-06, ROLE-01, ROLE-02, ROLE-03)

---

### Phase 3: Comment System

**Goal**: Comments are a fully functional, end-to-end user-facing feature on every lemma detail page — post, list, author delete, admin delete — backed by a clean schema and access control.

**Mode:** mvp

**Depends on**: Phase 2

**Requirements**: COMMENT-01, COMMENT-02, COMMENT-03, COMMENT-04, COMMENT-05, COMMENT-06, COMMENT-07

**Success Criteria** (what must be TRUE):
1. A logged-in user can post a comment on a lemma detail page via `POST /api/comment`; the new comment appears in the list without a full-page reload
2. An anonymous user sees no comment form on the detail page; an anonymous `POST /api/comment` returns 401/403
3. The detail page lists all comments for that lemma in reverse chronological order (newest first)
4. The comment author sees a "删除" button on each of their own comments; clicking it (with confirmation) hard-deletes the comment and it disappears from the list
5. A non-author attempting `POST /api/comment/<id>/delete` directly gets 403; an admin can delete any comment via the same endpoint
6. The `Comment` table has a `user_id` foreign key to `User.id`; renaming a username does not orphan historical comments (comments still display the *current* username at read time, while `user_id` is the durable link)

**Plans**: 2 plans
- Plan 3.1: Comment 数据模型重构 + 发布/列表接口 (COMMENT-01, COMMENT-02, COMMENT-03, COMMENT-06)
- Plan 3.2: 作者删除 + 管理员删除 + 模板集成 (COMMENT-04, COMMENT-05, COMMENT-07)

---

### Phase 4: Frontend Modernization & Product Features

**Goal**: The web UI is a coherent, modern, accessible surface — jQuery and Bootstrap 3 are gone, Pico.css + HTMX are in, all seven templates are redesigned, and lemma pages show last-edited timestamp, view count, wiki links, and related lemmas.

**Mode:** mvp

**Depends on**: Phase 3

**Requirements**: FRONT-01, FRONT-02, FRONT-03, FRONT-04, FRONT-05, FRONT-06, LEMMA-01, LEMMA-02, LEMMA-03, LEMMA-04, LEMMA-05, LEMMA-06, LEMMA-07, LEMMA-08

**Success Criteria** (what must be TRUE):
1. No jQuery or Bootstrap 3 CSS/JS is loaded on any template; the legacy `jquery.min.js` asset is deleted
2. Pico.css provides base styling; HTMX is loaded and used for at least one partial-update flow (search-as-you-type or comment posting)
3. The rich-text editor in `add.html` and `modify.html` is replaced with a modern editor (Quill / EasyMDE / Tiptap — chosen at plan time)
4. All seven templates (home / signin / register / add / modify / result / detail) share a consistent visual language with semantic HTML, visible focus states, and accessible color contrast
5. Lemma detail page shows title, content, "最后编辑于 YYYY-MM-DD HH:MM by <username>", view count, comments, and "相关词条" section
6. Lemma content with `[[词条名]]` renders as a link to that lemma's detail page; a non-existent target renders as a red dashed link with a "(创建此词条)" affordance
7. The "相关词条" section lists lemmas whose content contains `[[本词条标题]]` (backlinks), and the view counter increments atomically on each detail GET

**Plans**: 3 plans
- Plan 4.1: 前端栈替换 (jQuery 移除 + Pico.css + HTMX + 现代编辑器) (FRONT-01, FRONT-02, FRONT-03, FRONT-04)
- Plan 4.2: 七模板重设计 + 可访问性 (FRONT-05)
- Plan 4.3: 词条产品特性 (updated_at / view_count / wiki 链接 / 相关词条) (FRONT-06, LEMMA-01..08)

---

### Phase 5: Docker Deployment, Tests & Acceptance

**Goal**: A third party can clone the repo, follow only the README, build the Docker image, point it at an external MySQL, put it behind an external nginx reverse proxy, and complete the full end-to-end smoke flow in a browser — passing automated pytest smoke tests along the way.

**Mode:** mvp

**Depends on**: Phase 4

**Requirements**: INFRA-07, INFRA-08, INFRA-10, INFRA-11, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05

**Success Criteria** (what must be TRUE):
1. `Dockerfile` (multi-stage, `python:3.11-slim`) builds a runnable image that starts the app via gunicorn on port 8000
2. Container entrypoint runs `flask init-db` (idempotent) on first start, then starts gunicorn; `/api/reset` is not present in the running image
3. All runtime configuration comes from env vars (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `FLASK_SECRET`); no defaults fall back to `root`/`123456`
4. `.dockerignore` keeps the build context under 50 MB (excludes `.venv/`, `.git/`, `__pycache__/`, `*.pyc`, etc.)
5. `pytest` + `pytest-flask` are installed; `tests/test_smoke.py` runs an end-to-end flow in a single test: register → login → create lemma → search → open detail → edit lemma → post comment → delete own comment, asserting each step
6. `tests/test_admin.py` verifies: admin can delete any lemma and any comment; a non-admin attempting the same gets 403
7. `make test` (or `pytest`) passes locally on a fresh venv; README documents how to run
8. README's "Production deploy" section contains full third-party-followable steps: build image, `docker run -e DB_HOST=… -e …`, place behind external nginx reverse proxy, point at external MySQL — and the smoke flow can be completed in a browser after following only these steps

**Plans**: 2 plans
- Plan 5.1: Docker 化 (Dockerfile + entrypoint + env vars + .dockerignore) (INFRA-07, INFRA-08, INFRA-09, INFRA-11)
- Plan 5.2: pytest smoke 测试 + README 验收文档 (INFRA-10, TEST-01..05)

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation (Python 3 + Bug Fixes) | 0/2 | Not started | - |
| 2. Security & Auth Hardening | 0/3 | Not started | - |
| 3. Comment System | 0/2 | Not started | - |
| 4. Frontend Modernization & Product Features | 0/3 | Not started | - |
| 5. Docker Deployment, Tests & Acceptance | 0/2 | Not started | - |

---

*Roadmap defined: 2026-06-11*
*Last updated: 2026-06-11 after brownfield project initialization*
