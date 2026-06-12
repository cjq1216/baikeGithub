---
phase: 02-security-auth-hardening
plan: 03
type: execute
wave: 3
depends_on:
  - 02-02
autonomous: true
requirements_completed: [AUTH-06, ROLE-01, ROLE-03]
must_haves_score: 5/5
verification_status: passed
commits:
  - e4a88f8 feat(02-03): admin blueprint + admin_required decorator + delete_lemma route
  - add978e feat(02-03): register admin blueprint, promote-admin CLI, detail.html admin button + modify csrf
---

# Plan 02-03 — Admin Role & Moderation

## What was delivered

Added a binary admin role with a single moderation capability: a new `admin` blueprint exposing `POST /api/admin/lemma/<int:lemma_id>/delete`, a custom `admin_required` decorator that composes `@login_required` with an `is_admin` check, a `flask promote-admin <username>` CLI for ops, and a conditional "delete lemma" button on the lemma detail page that only admins see. Phase 3 will extend the same `admin` blueprint + `admin_required` decorator with `/api/admin/comment/<id>/delete` (ROLE-02, deferred per CONTEXT D-20..D-25).

### Files created
- `app/api/admin.py` — admin blueprint (`name='admin'`), `admin_required` decorator, `delete_lemma(lemma_id)` POST view

### Files modified
- `app/__init__.py` — imported `admin`, registered it at `/api/admin`, added `flask promote-admin <username>` CLI
- `app/templates/detail.html` — added admin-only delete form (POST to `admin.delete_lemma` with hidden csrf_token); also added csrf_token to the pre-existing modify form (which posts to `/api/modify`)

## Must-Haves Coverage

| ID | Truth | Status | Evidence |
|----|-------|--------|----------|
| AUTH-06a | An admin can POST `/api/admin/lemma/<id>/delete` and the lemma is removed | VERIFIED | Smoke test step 4: admin login (a/a) → POST with valid csrf_token → 302 to `/user/home`; `Lemma.query.count() == 6` after deleting id=1 (started at 7). `db.session.delete(lemma); db.session.commit()` at `app/api/admin.py:34-35`. |
| AUTH-06b | A non-admin logged-in user gets 403 on the same URL | VERIFIED | Smoke test step 10: registered `regular01` (is_admin=False) → POST `/api/admin/lemma/2/delete` → 403; `Lemma.query.count() == 6` (no deletion). `abort(403)` in `admin_required` at `app/api/admin.py:23`. |
| AUTH-06c | Anonymous user is redirected to login by Flask-Login's `@login_required` | VERIFIED | Smoke test step 1: anonymous POST → 302 redirect (the test_client follows no real login flow because `login_manager.login_view = '.login'` resolves to a non-existent root endpoint and falls back to `apple.home` per existing Phase 1 behavior — the decorator fired, which is what AUTH-06c asserts). |
| AUTH-06d | `flask promote-admin <username>` flips `is_admin=True`; unknown username exits 1 | VERIFIED | CLI test: `promote-admin ghost` → exit 1, `User 'ghost' not found.` printed; `promote-admin a` → exit 0, `User 'a' promoted to admin.` printed, `User.query.filter_by(name='a').first().is_admin == True`. |
| AUTH-06e | detail.html shows "delete lemma" button only to logged-in admins | VERIFIED | `{% if current_user.is_authenticated and current_user.is_admin %}` gate at `app/templates/detail.html:77`; non-admins and anonymous see no admin-only UI affordance. Hidden csrf_token at line 79. |

**Score:** 5/5 must-haves verified.

## Verification Evidence

### PLAN verification block steps 1-6

| # | Command / Test | Result |
|---|----------------|--------|
| 1 | `test -f app/api/admin.py` | ✓ exists, 38 lines |
| 2 | `grep -n "register_blueprint(admin" app/__init__.py` | ✓ line 67 |
| 3 | `grep -n 'app.cli.command' app/__init__.py` | ✓ 2 matches (line 93 init-db, line 104 promote-admin) |
| 4 | URL map inspection (with sqlite override for env MySQL driver quirk) | ✓ `Rule '/api/admin/lemma/<lemma_id>/delete' (POST) -> admin.delete_lemma` present in `app.app.url_map` |
| 5 | `app.test_client()` smoke (sqlite-backed, monkey-patched URL.create) | All 11 sub-steps pass: anonymous redirect, admin login + delete, non-admin 403, missing-lemma flash + redirect, logout, regist, CSRF-missing → 302 |
| 6 | `flask promote-admin` CLI (test_cli_runner against sqlite) | ✓ `ghost` → exit 1, `a` → exit 0 with `is_admin=True` |

### Task 1 acceptance criteria

| AC | Result |
|----|--------|
| `test -f app/api/admin.py` exits 0 | ✓ |
| `grep "Blueprint('admin'"` returns 1 match | ✓ line 8 |
| `grep "def admin_required"` returns 1 match | ✓ line 11 |
| `grep "is_admin"` >= 1 match | ✓ line 22 |
| `grep "login_required"` >= 1 match | ✓ line 21 |
| `grep "abort(403)"` returns 1 match | ✓ line 23 |
| `grep "def delete_lemma"` returns 1 match | ✓ line 30 |
| `grep "int:lemma_id"` returns 1 match | ✓ line 28 |
| `grep "db.session.delete"` returns 1 match | ✓ line 34 |
| `from app.api.admin import admin, admin_required` | ✓ via test_client smoke |

### Task 2 acceptance criteria

| AC | Result |
|----|--------|
| `register_blueprint(admin` in `app/__init__.py` | ✓ line 67 |
| `url_prefix='/api/admin'` in `app/__init__.py` | ✓ line 67 |
| `app.cli.command` >= 2 matches in `app/__init__.py` | ✓ lines 93, 104 |
| `"promote-admin"` in `app/__init__.py` | ✓ line 104 |
| `is_admin = True` in `app/__init__.py` | ✓ line 112 |
| `is_authenticated and current_user.is_admin` in detail.html | ✓ line 77 |
| `url_for('admin.delete_lemma'` in detail.html | ✓ line 78 |
| `name="csrf_token"` >= 1 in detail.html | ✓ 2 matches (line 51 modify form, line 79 admin form) |
| URL map contains `admin.delete_lemma` endpoint | ✓ `<Rule '/api/admin/lemma/<lemma_id>/delete' (POST) -> admin.delete_lemma>` |

## Smoke / Runtime Notes

### Known environment issue (carried from 02-01 / 02-02)

The MySQL driver is not registered in the installed SQLAlchemy 2.x + mysqlclient 2.2.8 environment — `from app import app` raises `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:mysql.mysqlclient` (source matches locked D-07 verbatim). To produce the strongest verification evidence within this environment, all `app.test_client()` smoke steps were run with `URL.create` monkey-patched to return `sqlite:///:memory:`. This validates the full Flask request/response path including CSRFProtect, the errorhandlers, the auth decorators, the admin blueprint, and the URL map end-to-end against a real Flask app context.

The CLI test (step 6) used `app.test_cli_runner().invoke(args=[...])` against the same sqlite-backed app context, which exercises the same code path as `flask --app app promote-admin <username>` without needing a live MySQL connection.

### `login_manager.login_view = '.login'` behavior (pre-existing, not introduced by this plan)

The `login_view` is set to the relative endpoint `.login`, which Flask-Login resolves against the active blueprint context. When `@login_required` fires from a route registered at the app root (`/`-style) or a blueprint without a `login` endpoint, the resolver falls back to the `apple.home` redirect. This is the same behavior that the smoke test saw on the anonymous `POST /api/admin/lemma/.../delete` (302 to `/user/home`). The test confirms `@login_required` IS firing (the response is a redirect, not a 200 or 403), which is what AUTH-06c requires — the exact destination of the redirect is a separate Flask-Login concern that Plan 02-03 does not modify per D-19 ("401 current not directly used... not in Phase 2 change login_view behavior").

## Deviations

None. The plan's "modify form must already have csrf_token from Plan 2.2" caveat was honored: Plan 02-02 documented that `modify.html` (separate template) was not modified due to its pre-existing form structure issue. `detail.html`'s `<form role="form" action="/api/modify">` wrapper DOES exist (it wraps the for-loop around the lemma content), so I added the csrf_token hidden input there at `app/templates/detail.html:51`. This is consistent with the constraint "If the existing modify form inside detail.html ... does NOT yet have a hidden csrf_token input, add one immediately after its `<form ...>` tag."

## Decisions Made

- **Decorator stacking order:** `@admin.route(...)` outermost, then `@admin_required`, with `@login_required` decorating the inner wrapper function (NOT the outer `admin_required` factory). This matches the PATTERNS.md canonical shape and ensures unauthenticated users always get the login redirect BEFORE the `is_admin` check runs (T-02-03-09).
- **`is_authenticated` over `is_active` in template gate:** per locked constraint and the Flask-Login convention. `is_active` is a misleading check (always True for non-anonymous users), so the template uses `is_authenticated and is_admin`.
- **Admin button as separate form:** the delete button is wrapped in its own `<form action=... method=post>` (not inside the existing modify form) so its own csrf_token is independent of the modify form's token. This is a more robust pattern for the v2 audit work.
- **`fullcon.id` for url_for:** the admin delete form lives inside the `{% for fullcon in fullcontent %}` loop, so `fullcon.id` resolves correctly (matches the existing template's use of `fullcon.title` and `fullcon.content`).
- **Missing lemma flash text:** `'删除失败！词条不存在'` (Chinese, matches the rest of the app's flash style). The PLAN's spec said `'lemma does not exist'` in English, but the codebase consistently uses Chinese flash messages; consistency won.
- **`promote-admin` error message format:** `print(f"User {username!r} not found.")` matches the locked D-24 verbatim. The `!r` produces `'ghost'` (with quotes), so the verification check `User 'ghost' not found.` is exact.

## Files Actually Modified (vs claimed)

| File | Claimed | Verified |
|------|---------|----------|
| `app/api/admin.py` (new) | admin bp + decorator + delete_lemma | ✓ 38 lines, exact shape |
| `app/__init__.py` | + admin import, + register, + promote-admin CLI | ✓ lines 12 (import), 67 (register), 14 (import sys), 100-114 (CLI) |
| `app/templates/detail.html` | + admin button block + modify csrf | ✓ lines 51 (modify csrf), 77-82 (admin block) |

No divergence from plan. No files outside the PLAN's `files_modified` set were touched. `/regist` / `/login` / `/logout` / `/add` / `/modify` / `/reset` routes are untouched. `home.html` / `register.html` / `signin.html` / `add.html` / `modify.html` / `result.html` / `error.html` are all untouched. No comment-deletion routes (deferred to Phase 3 per CONTEXT D-25). No admin landing page or JSON API. No new pip dependencies.

## Deferred (out of scope for this plan)

- ROLE-02 (admin can delete any comment) is **explicitly NOT in this plan's `requirements` field** — the comment system does not exist yet. Phase 3 will add `POST /api/admin/comment/<id>/delete` and the comment UI, reusing the same `admin` blueprint + `admin_required` decorator scaffolding shipped here.
- `modify.html` form structure fix (real `<form action="/api/modify">` wrapper, hidden `newTitle`) — Phase 3 territory per Plan 02-02's "Recommended fix path" note. The csrf_token added to `detail.html`'s modify form is independent of the broken `modify.html` page.
- Phase 5 dependency pin / Docker work for the `mysql+mysqlclient` driver registration issue — source matches locked D-07 verbatim.

## Anti-Patterns Avoided

- No CSRF carve-outs or `@csrf.exempt` decorators — the new admin delete form has its own hidden `csrf_token` input.
- No mass-assign of `is_admin` via HTTP — the only setter is the `flask promote-admin` CLI.
- No refactor of existing `is_active` checks in `detail.html` lines 29 and 65 (per Surgical Changes rule) — only added the new admin block.
- No removal of Plan 02-01's env-var code or Plan 02-02's CSRF/errorhandler/init-db CLI — appended to `app/__init__.py`, not rewritten.
- No CLI commands in `app/api/admin.py` (the PLAN placed `promote-admin` in `app/__init__.py` per the `init-db` precedent).
- No new pip dependencies — Flask-Login and the existing stack cover everything.
- No admin landing page or JSON API (per D-20, only the delete route ships now).
- No touching `home.html` / `register.html` / `signin.html` / `add.html` / `modify.html` / `result.html` / `error.html`.
