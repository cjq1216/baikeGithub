---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Phase 3 complete
last_updated: "2026-06-12T10:35:00.000Z"
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 12
  completed_plans: 7
  percent: 58
---

# State: 互动百科 产品化升级

**Initialized:** 2026-06-11
**Project type:** brownfield upgrade (Flask + MySQL Wiki, 2017 课堂作业 → product-shape MVP)
**Core value:** 一个陌生开发者能根据 README 启动 Docker 容器、注册账号、创建词条、发布评论、并以管理员身份看到完整端到端流程。

## Project Reference

**Stack**: Python 3.11+ / Flask / SQLAlchemy / Flask-Login / MySQL (外部) / HTMX + Pico.css (前端) / gunicorn (容器内) / nginx (外部) / Docker (单 Flask 容器)
**Mode**: mvp — each phase delivers a runnable, demonstrable user capability
**Granularity**: coarse — 5 phases, 12 plans total
**Parallel**: true — independent plans within a phase may run in parallel

## Current Position

Phase: 3
**Phase**: 3 — Comment System
**Status**: ✅ Complete (Plans 3.1 + 3.2 delivered, all 7 SUCCESS criteria statically verified)
**Progress bar**: `[██████████░░░░░░░░░░]` 3/5 phases complete (7/12 plans done)
**Next action**: `/gsd-execute-phase 4` — Frontend Modernization & Product Features

## Performance Metrics

| Metric | Value |
|--------|-------|
| Total phases | 5 |
| Total plans | 12 |
| Phases complete | 3 (Phase 1, 2, 3) |
| Plans complete | 7 (1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2) |
| Avg plans/phase | 2.4 |
| v1 requirements | 46 |
| Mapped requirements | 46 |
| Coverage | 100% ✓ |

## Accumulated Context

### Key Decisions (from PROJECT.md, pending validation)

- 保留 Flask 而非换栈 — 升级目标不是重写
- 二元角色 (regular + admin)
- HTMX + Pico.css 而非 React
- 词条间 wiki 链接采用 `[[标题]]` 语法
- 凭据/secret 走环境变量
- 评论不实装编辑 (仅发布 + 作者删除)
- Docker 不打包 nginx / MySQL
- 测试仅 smoke, 不写完整测试套件

### Architectural Notes (from CLAUDE.md, codebase baseline)

- 蓝图命名约定: `apple` (页面渲染, app/route/user.py) + `api` (表单提交, app/api/__init__.py)
- `url_for` 跨蓝图跳转: `apple.<endpoint>` 或 `api.<endpoint>`, 永远不要写 `user.<endpoint>`
- MySQL 凭据在 `app/__init__.py:11` 是单一来源 — model.py 里的硬编码无效
- 默认账号: `a` / `a`
- 重置数据库: 浏览器访问 `/api/reset` (开发模式);容器内改为 `flask init-db`

### Discovered Constraints

- INFRA-09 (env vars) 必须在 Phase 2 完成 (登录依赖 secret_key + DB URI)
- COMMENT-06 (user_id FK) 必须在 Phase 3 之前规划, 因为 Phase 2 引入了 `is_admin` 等 User 字段扩展
- Phase 4 的 wiki 链接 (LEMMA-07) 同时需要后端正则解析 + 模板渲染, FRONT-06 与 LEMMA-07 强耦合 → 合并入 Phase 4 Plan 4.3
- Phase 5 的 README 必须包含"端到端 smoke flow 步骤", 这是验收标准

### TODOs

(none yet — populated by /gsd-plan-phase and /gsd-execute-phase)

### Blockers

(none)

## Phase Summary

| # | Phase | Plans | Requirements | Status |
|---|-------|-------|--------------|--------|
| 1 | Foundation (Python 3 + Bug Fixes) | 2 | INFRA-01..04 | ✅ Complete |
| 2 | Security & Auth Hardening | 3 | AUTH-01..06, ROLE-01..03, INFRA-05, INFRA-06, INFRA-09 | ✅ Complete |
| 3 | Comment System | 2 | COMMENT-01..07, ROLE-02 | ✅ Complete (2026-06-12) |
| 4 | Frontend Modernization & Product Features | 3 | FRONT-01..06, LEMMA-01..08 | Not started |
| 5 | Docker Deployment, Tests & Acceptance | 2 | INFRA-07, INFRA-08, INFRA-10, INFRA-11, TEST-01..05 | Not started |

## Phase 3 Delivery

**Commits** (6 atomic, sequential):
- `945128b` — feat(03-01/T1): comment schema refactor with user_id FK + cascade
- `9a2499c` — feat(03-01/T2): implement POST /api/comment with login + validation
- `fba131e` — feat(03-01/T3): implement author-only POST /api/comment/<id>/delete
- `fd6605e` — feat(03-01/T4): /user/detail queries comments ordered by time desc
- `59b4148` — feat(03-02/T1): add admin POST /api/admin/comment/<id>/delete route
- `bb3991b` — feat(03-02/T2): detail.html — inline comment form, delete buttons, author/time fields

**SUCCESS criteria coverage** (statically verified, see `.planning/phases/03-comment-system/03-VERIFICATION.md`):
- SC-1 登录用户发布评论 → `/api/comment` POST route (9a2499c) ✅
- SC-2 匿名用户不渲染发布 form + 匿名 POST 403 → `{% if current_user.is_authenticated %}` 包裹 (bb3991b) + `@login_required` (9a2499c) ✅
- SC-3 评论按 time DESC 倒序 → `Comment.time.desc()` (fd6605e) ✅
- SC-4 作者删除按钮 + confirm → `url_for('api.delete_comment')` + `onsubmit` confirm (bb3991b) ✅
- SC-5 admin 删除按钮 + 非作者 403 → `url_for('admin.delete_comment')` + `@admin_required` (59b4148, bb3991b) + `comment.user_id != current_user.id` (fba131e) ✅
- SC-6 评论作者字段名随 User.name 变化 → `comment.author.name` 走 `backref=backref('author', lazy='joined')` (945128b, bb3991b) ✅
- SC-7 硬删除 → `db.session.delete + commit` 双端点 (fba131e, 59b4148) ✅

**Deferred to Phase 5 verification** (needs live MySQL + Flask process):
- V3-V7 of Plan 3.1 + V2-V8 of Plan 3.2 (curl / browser end-to-end)

## Session Continuity

- Last session: 2026-06-12 — Phase 3 executed, both plans committed, all 7 SCs statically verified
- Next action: `/gsd-execute-phase 4` (Frontend Modernization & Product Features)
- Resume point: Phase 4 — HTMX + Pico.css migration, wiki links, view_count, related lemmas
