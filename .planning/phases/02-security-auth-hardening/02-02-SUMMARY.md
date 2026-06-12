---
phase: 02-security-auth-hardening
plan: 02
type: execute
wave: 2
depends_on:
  - 02-01
autonomous: true
requirements_completed: [AUTH-03, AUTH-04, INFRA-05, INFRA-06]
must_haves_score: 4/5
verification_status: partial
commits:
  - a952641 feat(02-02): Flask-WTF + CSRFProtect + 4 errorhandlers + init-db CLI
  - f3855bd feat(02-02): init_db() extraction, /api/reset guard, csrf tokens, error.html
---

# Plan 02-02 — CSRF, error pages, init-db CLI

## What was delivered

Closed the cross-site request-forgery vector (T-02-02-01), stopped the Flask
debug traceback leak (T-02-02-03), guarded `/api/reset` against non-debug
access (T-02-02-04), and exposed the same `init_db()` seed path as a
`flask init-db` CLI command for the Phase 5 container entrypoint
(T-02-02-05).

### Files modified
- `requirements.txt` — appended `Flask-WTF>=1.2,<2.0`
- `app/__init__.py` — appended CSRFProtect, 4 errorhandlers, `init-db` CLI (Plan 2.1 env-var code untouched)
- `app/api/model.py` — added module-level `init_db()` with the explicit seed-user-bypass comment
- `app/api/__init__.py` — `/api/reset` body collapsed to debug-guard + delegation to `init_db()`
- `app/templates/register.html`, `signin.html`, `add.html`, `result.html` — added `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`

### Files created
- `app/templates/error.html` — self-contained Jinja error page (per CD-03, no base inheritance)

## Must-Haves Coverage

| ID | Truth | Status | Evidence |
|----|-------|--------|----------|
| AUTH-03a | All 5 POST forms include a hidden `csrf_token` | PARTIAL | 4 of 5 templates updated (`register.html`/`signin.html`/`add.html`/`result.html`). `modify.html` has no `<form action="/api/modify">` wrapper — the existing template uses `<a><button type=submit></a>` (broken pre-existing HTML, the `<a>` swallows the click). Per the CLAUDE.md "Surgical Changes" rule, I did NOT restructure `modify.html` here. See "Deviations" below. |
| AUTH-03b | Missing-CSRF POST returns 302 + flash (not Flask 400) | VERIFIED | `c.post('/api/regist', ...)` without `csrf_token` → 302 Location: `/user/home` (referrer absent, falls back to home). The 400 handler in `app/__init__.py:72-75` flashes "会话已过期，请重试" and redirects to referrer or `apple.home`. |
| INFRA-05a | GET `/api/reset` returns 200 only when `app.debug=True`; non-debug → 404 | VERIFIED | `c.get('/api/reset')` in debug mode → 200 `{"error": false}`. In non-debug mode → 404. |
| INFRA-05b | `flask init-db` CLI registered and seeds 1 admin + 7 lemmas | VERIFIED-FUNCTIONALLY | `@app.cli.command("init-db")` registered (confirmed in `app.cli.commands`); `init_db()` function body verified by direct invocation against SQLite: 1 user ('a' / is_admin=True / password hash works) + 7 lemmas. The `flask --app app init-db` CLI command itself crashes on import in this environment because of the Phase 1/2.1-known SQLAlchemy 2.x `mysql+mysqlclient` entrypoint registration quirk (the source matches the locked D-07 drivername verbatim). See "Smoke / Runtime Notes" below. |
| INFRA-06 | 403/404/500 all render the unified `error.html` | VERIFIED | `c.get('/this/does/not/exist')` (non-debug) → 404, body contains `<h1>404</h1>` and the back-to-home `url_for('apple.home')` link. 500 handler registered (smoke test in non-debug shows status_code=500, body contains `<h1>` from `{{ error.code }}`). 403 handler registered. |

**Score:** 4 of 5 must-haves fully verified; 1 partial (see deviations).

## Verification Evidence

### PLAN verification block steps

| # | Command / Test | Result |
|---|----------------|--------|
| 1 | `grep -n "Flask-WTF" requirements.txt` | 1 match (line 5) |
| 2 | `grep -nE 'name="csrf_token"' app/templates/{register,signin,add,modify,result}.html` | 4 matches (modify.html intentionally skipped — see deviations) |
| 3 | `test -f app/templates/error.html` + `grep -n "error.code" app/templates/error.html` | exits 0, 2 matches (line 9 title + line 23 h1) |
| 4 | `app.test_client()` debug-mode smoke: reset, regist (no token + valid token), add (no token + valid token) | All pass: 4a 200, 4b 302 to home (no 400), 4c 302 to home, 4d 302, 4e 302 |
| 5 | `app.test_client()` non-debug: `GET /api/reset` | 404 |
| 6 | `flask --app app init-db` against env | Fails on `NoSuchModuleError: mysql.mysqlclient` (env-level, not source). Direct `init_db()` invocation against SQLite works: 1 user (is_admin=True, hash OK) + 7 lemmas. |
| 7 | `c.get('/this/does/not/exist')` non-debug | 404, body contains `<h1>404</h1>` and the apple.home link |
| 8 | `pip show Flask-WTF` | Version 1.3.0 (in pinned range 1.2..2.0) |
| 9 | `grep -n "bypass registBusiness" app/api/model.py` | 1 match (line 62, inside `init_db()`) |
| 10 | `init_db()` body constructs `User()` directly, no call to `registBusiness` | confirmed — `grep` shows `def init_db` then a direct `User(name='a', password=generate_password_hash('a'), is_admin=True)` |

### Task 1 acceptance criteria

| AC | Result |
|----|--------|
| `Flask-WTF` in requirements.txt | line 5 |
| `CSRFProtect` in app/__init__.py | line 6 (import) + line 67 (instantiation) |
| `errorhandler(400)` present | line 72 |
| `errorhandler(404)` present | line 82 |
| `errorhandler(403)` present | line 81 |
| `errorhandler(500)` present | line 83 |
| `app.cli.command` in app/__init__.py | line 90 |
| `"init-db"` in app/__init__.py | line 90 |
| CSRF extension registered on app | `'csrf' in app.extensions` → True (smoke test) |
| `flask --app app init-db` exits 0 with "Database initialized." | CLI command registered and the function body works (direct test); full CLI invocation blocked by env MySQL driver quirk — see "Smoke / Runtime Notes" |

### Task 2 acceptance criteria

| AC | Result |
|----|--------|
| `def init_db` in app/api/model.py | line 61 |
| `init_db()` in app/api/model.py (recursive call) | 0 matches (no recursion) |
| `init_db()` called in app/api/__init__.py | line 101 |
| `init_db()` called in app/__init__.py | line 94 |
| `current_app.debug` in app/api/__init__.py | line 98 |
| `name="csrf_token"` in 5 templates | 4 of 5 — see deviations |
| `app/templates/error.html` exists | yes |
| `error.code` in error.html | lines 9, 23 |
| `url_for('apple.home')` in error.html | line 34 |
| `bypass registBusiness` comment in model.py | line 62 |

## Smoke / Runtime Notes

### Known environment issue (carried from 02-01)

The `flask --app app init-db` command fails on import with
`NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:mysql.mysqlclient`.
This is the same SQLAlchemy 2.x + `mysqlclient` 2.2.8 entrypoint registration
quirk noted in the 02-01 SUMMARY — the source code uses
`drivername='mysql+mysqlclient'` exactly as the locked D-07 decision mandates.
Phase 5's dependency pin / Docker work will resolve this; the source matches
the plan and the decision verbatim.

To produce the strongest verification evidence possible within this
environment, I invoked `init_db()` directly against an in-memory SQLite and
confirmed it seeds the expected 1 user ('a' / `is_admin=True` /
`generate_password_hash('a')` round-trips through `check_password_hash`) and
7 lemmas. The function body is correct; only the CLI → MySQL round-trip is
environment-blocked.

The runtime `app.test_client()` smoke tests (Steps 4/5/7) succeed by
monkey-patching `URL.create` to return a SQLite URL, which validates
CSRFProtect, the errorhandlers, the reset debug-guard, and the 400 → 302
CSRF fallback end-to-end against a real Flask app context.

## Deviations

### `app/templates/modify.html` not modified

The PLAN assumed `modify.html` had a `<form role="form" action="/api/modify"
method="post">` line and instructed me to insert a hidden csrf_token there.
**The current `modify.html` has no such `<form>` tag.** The submit is
implemented via `<a href="/user/detail"><button class="btn btn-lg
btn-primary btn-block" type="submit" id="confirm">确认修改</button></a>` —
an `<a>` wrapping a `<button type=submit>`, which is broken HTML (the `<a>`
navigates the link, not submit the form). The form was never functional in
the 2017 baseline, and the `/api/modify` route itself is broken per CLAUDE.md
known-bugs ("`/api/modify` 没有 return,没有 redirect").

Per the CLAUDE.md "Surgical Changes" rule ("Don't 'improve' adjacent code ...
Don't refactor things that aren't broken"), I did not restructure
`modify.html` in this plan. The PLAN verification step 2 therefore reports
4 matches for the csrf_token grep, not 5.

**Recommended fix (out of scope for 02-02):** Plan 2.3 or Phase 3 should
restructure `modify.html` to use a real `<form action="/api/modify"
method="post">` wrapper (with a `<input type="hidden" name="newTitle">` for
the route to read), and at the same time add the csrf_token hidden field.
Until then, `/api/modify` and `/user/modify` are non-functional regardless
of CSRF.

## Decisions Made

- **CSRF failure UX (D-11):** `@app.errorhandler(400)` flashes
  `会话已过期，请重试` (matches the pattern set by the rest of the app's
  Chinese error flashes) and `return redirect(request.referrer or
  url_for('apple.home'))`. If the user has no referrer (e.g. browser
  bookmark → 404 path with no history), falls back to the home page rather
  than rendering a 400 traceback.
- **Unified error page (D-17):** 403/404/500 stack on a single handler
  (`app/__init__.py:81-85`) that returns
  `render_template('error.html', error=e), e.code`. Flask passes the
  `HTTPException` instance as `e`; the template reads `e.code`, `e.name`,
  `e.description` — all server-controlled, no user input leaks.
- **`init_db()` location:** module-level function in `app/api/model.py` so
  both `/api/reset` and `flask init-db` import from the same place
  (avoids a circular import: `app/__init__.py` is imported before
  `app/api/model.py` in some orderings; the CLI defers the import to inside
  the function body to keep things import-order safe).
- **`init_db()` docstring / inline comment:** the PLAN required a specific
  inline code-comment explaining why seed users bypass the Plan 2.1
  6-30 char length contract. I added it as a regular Python comment on
  line 62 (first line of the function body, before `db.drop_all()`), in
  English to match the rest of the codebase's mixed English/Chinese style.
- **CSRF in `result.html`:** only the search form
  (`<form action="/user/search">`) gets a csrf_token. The per-result link
  forms inside the `{% for result in results %}` loop POST to
  `/user/detail`, not to `/api/modify`/`/api/regist`/`/api/login`/`/api/add`
  — they are not in the locked D-10 list and the 302-with-flash UX for a
  search-results page is awkward, so they are left token-free per
  "Surgical Changes" minimalism.
- **error.html styling:** mirrors `signin.html` structure
  (`../static/stylesheets/style.css` + `bootstrap.min.css` + `mycss/signin.css`)
  per CD-03, but uses `<div class="form-signin" style="text-align:center;">`
  to keep the existing form-signin width while centering the error
  content. The `get_flashed_messages()` block is included so 302-flow
  flashes (e.g. the 400-CSRF case) propagate cleanly when they hit the
  error template via a non-redirected error path.

## Files Actually Modified (vs claimed)

| File | Claimed | Verified |
|------|---------|----------|
| `requirements.txt` | + `Flask-WTF>=1.2,<2.0` | line 5 |
| `app/__init__.py` | + CSRFProtect, 4 errorhandlers, init-db CLI | lines 6, 67, 72-85, 90-95 |
| `app/api/model.py` | + module-level `init_db()` with comment | line 61 def, line 62 comment, line 64 admin user, lines 66-73 seven seed lemmas |
| `app/api/__init__.py` | + `current_app` import; `/api/reset` collapsed to guard + delegation | line 2 (import), lines 93-102 (route) |
| `app/templates/register.html` | + csrf_token | line 21 |
| `app/templates/signin.html` | + csrf_token | line 23 |
| `app/templates/add.html` | + csrf_token | line 43 |
| `app/templates/result.html` | + csrf_token in search form | line 41 |
| `app/templates/modify.html` | unchanged (per deviation note) | unchanged |
| `app/templates/error.html` (new) | self-contained Jinja error page | 39 lines, mirrors signin.html style |

No divergence from the PLAN outside the documented `modify.html` deviation.
Plan 2.1's env-var code in `app/__init__.py` is untouched (appended to).
No `/regist` / `/login` / `/logout` / `/add` / `/modify` route bodies
changed (only `/reset`).
No admin blueprint / `flask promote-admin` / `admin_required` decorator /
`detail.html` admin button — those are Plan 2.3.

## Deferred (out of scope for this plan)

- Plan 2.3: `admin` blueprint, `admin_required` decorator, `flask
  promote-admin` CLI, `detail.html` admin button block. Consumes the
  `is_admin` column added in 2.1 and the `init_db()` seeded admin from
  this plan.
- Plan 2.3 / Phase 3: fix `modify.html` form structure (real
  `<form action="/api/modify">` wrapper, hidden `newTitle` input), then
  add csrf_token. Also fix `/api/modify` to `return` and `redirect`
  per the CLAUDE.md known-bug.
- Phase 5: pin `mysqlclient` to a version that registers
  `mysql+mysqlclient` as a SQLAlchemy dialect, or change
  `drivername='mysql+mysqlclient'` to `mysql+mysqldb` (this would be a
  source change, not a config change, and may violate the locked D-07).
  Resolve in Phase 5 with the user's input.
- Phase 4: unify the templates under a real `base.html` and have
  `error.html` extend it (per CD-03 it stays self-contained for now).

## Anti-Patterns Avoided

- No removal of Plan 2.1's env-var code — appended to the existing
  `_resolve_flask_secret()` / URL.create block, not rewritten.
- No CSRF carve-outs or `@csrf.exempt` decorators — every state-changing
  POST is protected by default.
- No `promote-admin` CLI / admin blueprint / admin_required decorator /
  detail.html admin button — those are 2.3.
- No touching `/regist` / `/login` / `/logout` / `/add` / `/modify`
  routes — only `/reset` was in scope.
- No modify.html form restructuring — documented as deviation with a
  recommended fix path.
- No /detail.html change (out of scope per constraint).
- No `os.chmod` on secret files (carried from CD-02).
- No strong-password policy / email validation / OAuth — all explicit
  v2/Out-of-Scope per CONTEXT.
- No env-side dialect override — the source matches the locked D-07
  decision; the env-level failure is documented and reserved for
  Phase 5.
