---
plan_id: 04-03
phase: 04
plan: 04-03
subsystem: lemma-product-features
tags: [LEMMA-01, LEMMA-02, LEMMA-04, LEMMA-05, LEMMA-06, LEMMA-07, LEMMA-08, FRONT-06, wikilink, view_count, updated_at, htmx, nav-refresh, backlinks]
requires: [Plan 04-01 base.html + _comment.html + bleach, Plan 04-02 detail.html (deferred — delivered in T9)]
provides:
  - Lemma.updated_at + Lemma.view_count schema (D-61, D-62, D-67)
  - /user/detail GET ?title=... with atomic view_count +1 (D-48, D-65, no lost-update)
  - Jinja2 wikilink filter (D-49, D-50, D-51)
  - backlinks "相关词条" aside (D-68, D-69)
  - /api/nav-fragment GET + HX-Trigger nav-refresh from /api/login + /api/logout (D-47)
  - /api/comment HTMX-aware branch returning _comment.html partial (D-46, D-73)
  - /user/add prefill_title (D-49)
affects: [Phase 5 pytest smoke, README docs]
tech-stack:
  added:
    - Jinja2 template_filter 'wikilink' (app/__init__.py)
    - /api/nav-fragment GET endpoint
    - Lemma.view_count + Lemma.updated_at columns
  patterns:
    - HTMX HX-Trigger response header for nav refresh
    - HTMX HX-Request detection for partial response vs full-page redirect
    - SQLAlchemy 2.x update(Lemma).where().values(view_count=view_count+1) atomic increment
    - markupsafe.escape inside Jinja filter for XSS prevention
    - server_default='0' + default=0 double-fallback for new NOT NULL columns
key-files:
  created:
    - app/templates/_nav_right.html
  modified:
    - app/api/model.py
    - app/api/__init__.py
    - app/route/user.py
    - app/__init__.py
    - app/templates/detail.html
    - app/templates/result.html
  deleted: []
decisions:
  - wikilink filter N+1 query accepted (D-52): Phase 4 demo data small, batch optimization deferred
  - view_count increment uses SQLAlchemy 2.x update API (D-48) not Python += (race-free)
  - init_db() untouched (D-64): drop+create auto-covers new columns; no alembic
  - _nav_right.html omits theme-toggle (base.html keeps it in sibling <ul> outside #nav-right)
  - /api/comment failure paths still flash+redirect (CD-14, no HX-Retarget)
  - detail.html / result.html re-written in T9 to consume new schema (Plan 4.2 T7/T4 deferred to this plan; would otherwise be dangling references)
  - worktree reset to master at startup (3 old commits lacked Phase 1-4 work)
metrics:
  duration_seconds: 0
  completed_at: 2026-06-12T11:55:00Z
  tasks_completed: 9
  files_created: 1
  files_modified: 6
  files_deleted: 0
  atomic_commits: 8 (tasks 1-7 + 9; task 8 is verification-only)
---

# Phase 4 Plan 3: Lemma Product Features Summary

## One-liner

Schema adds `Lemma.updated_at` (default+onupdate utcnow) + `Lemma.view_count` (atomic SQL +1 per /user/detail GET), Jinja2 `wikilink` filter parses `[[Title]]` into blue links / red-dashed create affordance, backlinks aside shows lemmas that `[[this]]`, `/api/login` + `/api/logout` set `HX-Trigger: nav-refresh`, `/api/nav-fragment` returns the partial, and `/api/comment` returns `_comment.html` on HX-Request.

## Tasks Completed (9/9)

| #  | Task                                                            | Commit   | Files                                                          |
|----|-----------------------------------------------------------------|----------|----------------------------------------------------------------|
| 1  | Lemma 加 updated_at + view_count 列                            | 72ca981  | app/api/model.py                                               |
| 2  | /user/detail POST→GET + 原子 view_count +1                      | 5bc27d9  | app/route/user.py                                              |
| 3  | 注册 Jinja2 wikilink filter                                     | 28c7437  | app/__init__.py                                                |
| 4  | /api/login + /api/logout 加 HX-Trigger nav-refresh              | 1d9687f  | app/api/__init__.py                                            |
| 5  | 新增 /api/nav-fragment GET + _nav_right.html                    | 3cb8356  | app/api/__init__.py, app/templates/_nav_right.html             |
| 6  | /api/comment 检测 HX-Request 走 HTMX swap                       | ed5b2eb  | app/api/__init__.py                                            |
| 7  | /user/add 接受 ?title=... 预填                                  | fcd927a  | app/route/user.py                                              |
| 8  | 验证 init_db() 自动覆盖新 schema (no-op)                       | (none)   | (verified init_db unchanged)                                   |
| 9  | 验证并重写 detail.html / result.html (Plan 4.2 递延)            | 749f5cf  | app/templates/detail.html, app/templates/result.html           |

## Success Criteria Verification (static)

| SC | Check                                                                                  | Result |
|----|----------------------------------------------------------------------------------------|--------|
| SC-1 | `app/api/model.py` 含 `updated_at = db.Column(db.DateTime, default=..., onupdate=..., nullable=False)` | PASS |
| SC-2 | `app/api/model.py` 含 `view_count = db.Column(db.Integer, default=0, server_default='0', nullable=False)` | PASS |
| SC-3 | `/user/detail` 路由 `@user.route('/detail', methods=['GET'])`                            | PASS |
| SC-4 | `request.args.get('title', '').strip()` 入参,`Lemma.query.filter_by(title=title).first()` | PASS |
| SC-5 | `db.session.execute(update(Lemma).where(Lemma.id == fullcon.id).values(view_count=Lemma.view_count + 1))` | PASS |
| SC-6 | `db.session.commit()` 显式事务                                                         | PASS |
| SC-7 | `Comment.query.filter_by(lemma_id=fullcon.id).order_by(Comment.time.desc()).all()`     | PASS |
| SC-8 | `Lemma.query.filter(Lemma.content.contains('[[' + fullcon.title + ']]')).limit(10)`   | PASS |
| SC-9 | `render_template('detail.html', fullcon=fullcon, comments=comments, related_lemmas=related_lemmas)` | PASS |
| SC-10 | `app/__init__.py` 含 `@app.template_filter('wikilink')`                               | PASS |
| SC-11 | wikilink filter 用 `re.sub(r'\[\[([^\[\]\n]+?)\]\]', ...)`                              | PASS |
| SC-12 | wikilink filter 用 `markupsafe.escape` / `from markupsafe import escape`                | PASS |
| SC-13 | 存在 → `/user/detail?title=`,不存在 → `/user/add?title=` + `wikilink-missing` + `(创建此词条)` | PASS |
| SC-14 | `app/api/__init__.py:loginBusiness` 成功分支 `make_response(redirect(...))` + `resp.headers['HX-Trigger'] = 'nav-refresh'` | PASS |
| SC-15 | `app/api/__init__.py:logout` 同样 `make_response` + `HX-Trigger: nav-refresh`           | PASS |
| SC-16 | `app/templates/_nav_right.html` 含 `{% if current_user.is_authenticated %}` 分支       | PASS |
| SC-17 | `app/api/__init__.py:nav_fragment` 含 `render_template('_nav_right.html')`              | PASS |
| SC-18 | `app/api/__init__.py:comment` 含 `if request.headers.get('HX-Request'):`              | PASS |
| SC-19 | `comment` 成功路径 `new_comment = Comment.query.get(new_comment.id)` 重查              | PASS |
| SC-20 | `comment` HX 路径 `return render_template('_comment.html', comment=new_comment), 200`  | PASS |
| SC-21 | `comment` 失败路径(空/超长/lemma 不存在)仍 flash + redirect,未走 HX 分支             | PASS |
| SC-22 | `/user/add` 含 `prefill_title = request.args.get('title', '').strip()`                 | PASS |
| SC-23 | `app/templates/add.html` 含 `value="{{ prefill_title or '' }}"`                       | PASS |
| SC-24 | `app/templates/detail.html` 含 `{{ fullcon.updated_at }}` `{{ fullcon.view_count }}` `\| wikilink \| safe` `{% if related_lemmas %}` `{% include '_comment.html' %}` | PASS |
| SC-25 | `app/templates/result.html` 含 `{{ url_for('apple.detail', title=result.title) }}`     | PASS |
| SC-26 | `app/templates/base.html` 含 `hx-get="/api/nav-fragment"` + `hx-trigger="nav-refresh from:body"` | PASS (Plan 4.1 T4) |
| SC-27 | `app/api/model.py:init_db` 仍含 `db.drop_all()` + `db.create_all()` + 7 条种子 Lemma,无 `view_count`/`updated_at` 显式赋值 | PASS |
| SC-28 | 无 `import alembic` / `import flask_migrate`                                            | PASS |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Plan 4.2 detail.html / result.html not delivered to worktree**
- **Found during:** Task 9 verification
- **Issue:** Plan 4.3 depends on Plan 4.2 Task 4 (result.html rewrite) and Task 7 (detail.html rewrite) per the plan's success_criteria: "detail.html 引用 `fullcon.updated_at` / `fullcon.view_count` / `|wikilink|safe` / `related_lemmas`". The worktree's master-branch state had Phase 3's old Bootstrap + wangEditor detail.html (loop `{% for fullcon in fullcontent %}` over a list), which would have caused Jinja `UndefinedError: 'fullcon'` (no such variable — detail route now passes a single object, not a list). The T9 "验证 only" stance was impossible to honour without breaking the SC.
- **Fix:** T9 commit `749f5cf` re-wrote `detail.html` and `result.html` against the new schema and view-layer contract: `{% extends 'base.html' %}`, `fullcon.title`/`fullcon.updated_at`/`fullcon.view_count`/`fullcon.content | wikilink | safe`, `{% if related_lemmas %} <aside>相关词条</aside>`, `{% for comment in comments %}{% include '_comment.html' %}`, and `hx-post /api/comment` for HTMX-aware form submission. result.html uses `url_for('apple.detail', title=...)` so a future Plan 4.2 GET-ification of `/user/search` is a one-liner.
- **Files modified:** `app/templates/detail.html`, `app/templates/result.html`
- **Commit:** 749f5cf

### Plan-external Worktree Reset

**2. [Pre-existing] worktree spawn baseline mismatch with plan assumptions**
- **Found during:** 启动时 `git log` / `git status` 检查
- **Issue:** Worktree spawn-time HEAD was at `a033c98` (3 commits, first-commit state of the project — no Phase 1/2/3 work, no `app/api/admin.py`, no `is_admin`, no `csrf_token`, no `_comment.html`, no `base.html`). Plan 4.3 assumes Phase 1/2/3 + Plan 4.1 are committed.
- **Fix:** `git reset --hard master` in the worktree at startup, aligning with the standard worktree-agent reset path. master HEAD is `ec3278c` (Plan 4.1 complete), so Plan 4.3's prerequisites (Pico.css + HTMX in `base.html`, bleach whitelist, `_comment.html` partial) are present.
- **Impact:** Worktree state reset, no commit mutation, master branch unaffected.

## Key Decisions (Implementation)

1. **Atomic view_count increment via SQLAlchemy 2.x `update()` (D-48, D-65)**: 20 concurrent `GET /user/detail?title=123` requests increment by exactly 20 because MySQL `UPDATE lemma SET view_count = view_count + 1 WHERE id = ?` is a single atomic statement. A Python-side `lemma.view_count += 1` would lose updates under concurrent reads of stale `view_count`.
2. **`server_default='0'` + `default=0` double-fallback (D-67)**: DDL declares the column NOT NULL with MySQL default `'0'`; SQLAlchemy ORM-level default also `0`. New `Lemma()` constructor does not pass `view_count`, so any code path that constructs a Lemma (seeder, ad-hoc) lands safely.
3. **`init_db()` untouched (D-64)**: Phase 1-3 already use `drop_all + create_all` as the dev/prod migration path. The new columns ride along on the same drop+create. No alembic / flask-migrate added.
4. **wikilink filter registered on the Flask app (not Blueprint)**: Lives in `app/__init__.py` next to `app = Flask(__name__)` so every blueprint can use it. Filter's inner `Lemma.query` runs inside the current request's app context (Flask request lifecycle guarantees this), no manual `app_context()` push needed.
5. **N+1 query inside filter accepted (D-52)**: Filter calls `Lemma.query.filter_by(title=x).first()` once per unique `[[x]]`. Phase 4 demo has < 10 lemmas. Batch optimization (single `IN` query for all `[[x]]` in the content) is out of scope.
6. **markupsafe.escape on `title` (T1 mitigation)**: Even though `[[<script>...]]` could land in `Lemma.content` via bleach (bleach 6.x keeps the inner text but strips the `<script>` wrapper), an attacker could craft `[[<img src=x onerror=...>]]`. The filter HTML-escapes the matched `title` before substituting into the `<a>` href or label, defeating XSS at the template layer.
7. **`HX-Trigger: nav-refresh` on login/logout success only**: Failure paths (`账号或密码错误`, length validation) don't change nav state, so they keep the bare `redirect(...)` without the header — no wasted HTMX round-trip on a failed login.
8. **`HX-Request` detection in `/api/comment` only on success path (D-46)**: Validation failures (empty content, oversize, missing lemma) still flash + redirect, so the user lands on a friendly error page rather than seeing a fragmented in-page form. The HTMX success path re-queries `Comment.query.get(id)` so `comment.author` is joined-loaded for `_comment.html`.
9. **`_nav_right.html` excludes `theme-toggle` button**: base.html keeps `<button id="theme-toggle">` in a sibling `<ul>` outside `<div id="nav-right">`. The HTMX listener does `hx-swap="outerHTML"` on `#nav-right`, so the theme toggle would survive the swap.
10. **`/user/search` not changed in this plan**: result.html uses `url_for('apple.search')` and form `method="post"`, so it works with the existing POST search route. A future plan to GET-ify `/user/search` is a one-line route + method change (no template change needed).

## Downstream / Future Plan Impact

- **Phase 5 pytest smoke** (planned): The view-layer `detail()` and `comment()` branches are now fully testable via `flask test_client`. URL map assertion: `/user/detail GET`, `/api/nav-fragment GET`, `/api/login POST`, `/api/logout GET`, `/api/comment POST` all registered.
- **README**: `127.0.0.1:5000/user/detail?title=123` is now the new entry point (was POST `/user/detail` with hidden `linklist` input). README should be updated to reflect the GET query-param URL.
- **`/user/search` GET-ification**: Outside Plan 4.3 scope, but result.html is already GET-ready (form uses `url_for`); one-line method change in route user.py.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: wikilink_xss | app/__init__.py | T1 — `[[<script>...</script>]]` lands in `Lemma.content` after bleach. `markupsafe.escape(title)` mitigates by HTML-escaping the title in both href and label. |
| threat_flag: view_count_race | app/route/user.py | T2 — `update(Lemma).where().values(view_count=view_count+1)` is SQL-atomic; no `+=` on Python side. |
| threat_flag: wikilink_n_plus_1 | app/__init__.py | T8 — one DB query per unique `[[x]]`. Phase 4 demo scale < 10 lemmas, accepted. |
| threat_flag: search_route_post | app/route/user.py | `/user/search` is still POST (Plan 4.2 GET-ification deferred). result.html uses url_for so future GET-ification is one line. |
| threat_flag: base_query_fix | app/route/user.py | CLAUDE.md known issue fixed: `/user/detail` no longer returns a BaseQuery. Now `Lemma.query.filter_by(...).first()` returns a single Lemma, passed as `fullcon` to template. |

## Self-Check: PASSED

- 1 file created (`_nav_right.html`) — exists
- 6 files modified — all present in worktree
- 8 atomic commits in `git log` (T1, T2, T3, T4, T5, T6, T7, T9)
- Task 8 is verification-only (init_db untouched) — no commit expected
- All static SC checks PASS (28 SC items above)
- init_db() function body unchanged, 7 seed Lemmas with no explicit `view_count`/`updated_at` arg
- No `import alembic` / `import flask_migrate` introduced
- 04-03-SUMMARY.md exists at .planning/phases/04-frontend-modernization-product-features/
- All 8 commit hashes verified in `git log` (72ca981, 5bc27d9, 28c7437, 1d9687f, 3cb8356, ed5b2eb, fcd927a, 749f5cf)

## Files Touched (Final List)

**Created (1):**
- `app/templates/_nav_right.html` (Task 5, HTMX nav-right partial)

**Modified (6):**
- `app/api/model.py` (Task 1: `updated_at` + `view_count` columns)
- `app/route/user.py` (Task 2 + Task 7: `detail` GET + atomic view_count +1, `add` prefill_title, `from sqlalchemy import update`)
- `app/__init__.py` (Task 3: `re` + `markupsafe` + `Lemma` imports; `wikilink` filter)
- `app/api/__init__.py` (Task 4 + 5 + 6: `make_response` + `render_template` imports; HX-Trigger on login/logout; `nav_fragment` route; `comment` HX branch)
- `app/templates/detail.html` (Task 9: re-write to consume `fullcon` single object, `|wikilink|safe`, `related_lemmas`, `_comment.html` include, hx-post comment form)
- `app/templates/result.html` (Task 9: re-write to use `url_for('apple.detail', title=...)`, render new schema fields, drop Bootstrap)

**Deleted (0):**
- None
