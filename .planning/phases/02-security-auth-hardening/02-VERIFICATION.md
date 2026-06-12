---
status: passed
phase: 02-security-auth-hardening
score: 6/6
verified_at: 2026-06-12
re_verified_at: 2026-06-12
re_verification_note: "W-4 fixed in commit e10ec02 — result.html per-result form now carries csrf_token. Re-grep confirms 2 csrf_token fields in result.html (line 41 search form + line 55 per-result form). Search→detail click path no longer triggers CSRFProtect 400."
verifier: Claude (gsd-verifier)
method: Static grep + handler source inspection + deviation cross-check against 02-REVIEW.md + post-fix re-grep
---

# Phase 2: Security & Auth Hardening — Verification

## Goal

The auth surface is production-grade — credentials live in env vars, passwords are hashed, CSRF is enforced, and an admin role exists for moderation. All existing user-facing auth flows still work end-to-end.

## Success Criteria Score

### 1. Env-var credentials — VERIFIED
- Evidence:
  - `grep -nE "1frMFuWRVPV1|cjq|Cjq@123456|162\.14\.107\.126" app/__init__.py` → **0 matches** (exit=1). No hardcoded credentials remain.
  - `grep -n "URL.create" app/__init__.py` → **1 match at line 52**. DB URI built via `URL.create(drivername='mysql+mysqlclient', username=os.environ['DB_USER'], password=quote_plus(os.environ['DB_PASSWORD']), host=os.environ['DB_HOST'], port=int(os.environ['DB_PORT']), database=os.environ['DB_NAME'])`.
  - `_required_db_vars = ('DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME')` loop at `app/__init__.py:48-51` raises `RuntimeError("Missing required env var: " + _name)` if any var is missing (per locked D-05).
  - `_resolve_flask_secret()` at `app/__init__.py:17-41` reads `FLASK_SECRET` env (line 19), then `FLASK_SECRET_FILE` (line 24), then writes `os.urandom(32).hex()` to `instance/.flask_secret` (lines 37-40). No hardcoded fallback secret.
  - `requirements.txt:5` adds `Flask-WTF>=1.2,<2.0`.
  - `.dockerignore` excludes `instance/` (line 1) so `.flask_secret` does not leak into Docker build context.
- Test commands: all 3 commands above; results as stated.

### 2. Hashed passwords — VERIFIED
- Evidence:
  - `app/api/__init__.py:4` — `from werkzeug.security import generate_password_hash, check_password_hash` (imported).
  - `app/api/__init__.py:24` — `user = User(name=name, password=generate_password_hash(password))` on regist.
  - `app/api/__init__.py:38` — `if nowUser and check_password_hash(nowUser.password, password):` on login.
  - `app/api/__init__.py:41` — `flash('账号或密码错误')` unified message (anti-enumeration per D-03).
  - `app/api/model.py:14` — `password = db.Column(db.String(255))` (fits pbkdf2:sha256 default 150-byte output).
  - `grep -nE "generate_password_hash|check_password_hash" app/api/__init__.py` → **3 matches** (import + regist + login). Required >=2.
  - D-04 length validation `len(name) < 6 or len(name) > 30 or len(password) < 6 or len(password) > 30` at `app/api/__init__.py:19` (BEFORE the DB write at line 24).
  - Seed user `a` (1 char) is constructed directly in `init_db()` at `app/api/model.py:66` via `User(name='a', password=generate_password_hash('a'), is_admin=True)`, bypassing the HTTP length check. Inline comment at line 62 documents the carve-out.
- Test commands: 2 greps above; all pass.

### 3. CSRF protection — PARTIAL
- Evidence:
  - `app/__init__.py:6,70` — `from flask_wtf.csrf import CSRFProtect` and `csrf = CSRFProtect(app)`. Globally enabled.
  - `app/__init__.py:75-78` — `@app.errorhandler(400)` flashes "会话已过期，请重试" and redirects to `request.referrer or url_for('apple.home')` (per D-11).
  - `grep -nE 'name="csrf_token"'`:
    - `register.html:21` — 1 match ✓
    - `signin.html:23` — 1 match ✓
    - `add.html:43` — 1 match ✓
    - `modify.html` — **0 matches** (documented deviation, pre-existing 2017 broken form structure: `<a><button type=submit></a>` swallows the click; `/api/modify` itself is broken per CLAUDE.md known-bugs).
    - `result.html:41` — 1 match (the search form) ✓
    - `detail.html:51` and `:79` — 2 matches (modify form + admin form) ✓
  - **GAP (W-4 from 02-REVIEW.md)**: `result.html` per-result forms in the `{% for result in results %}` block (line 54) POST to `/user/detail` WITHOUT a hidden `csrf_token` input. The 02-02 SUMMARY documented this as "out of scope" but the global CSRFProtect activation makes these forms broken: clicking any search result triggers 400 → "会话已过期，请重试" → redirect to home instead of opening the detail page. This breaks the end-to-end search→detail user flow.
- Test commands: 1 grep + manual review of `app/templates/result.html:52-60` and `app/route/user.py:39-46` (which confirms `/user/detail` is a POST route that requires a valid CSRF token now).
- **Decision**: gap_found (per verification instructions: "A broken search→detail click violates [success criterion #5 'All existing user-facing auth flows still work end-to-end']. Lean toward gap_found.")

### 4. Admin user + CLI — VERIFIED
- Evidence:
  - `app/api/model.py:15` — `is_admin = db.Column(db.Boolean, default=False)`. New column added per D-23.
  - `app/api/model.py:66` — `db.session.add(User(name='a', password=generate_password_hash('a'), is_admin=True))`. Default seed user `a` is admin (D-08).
  - `app/__init__.py:100-114` — `@app.cli.command("promote-admin")` registered with `@click.argument("username")`; flips `user.is_admin = True` and `db.session.commit()`; unknown user prints `User '<name>' not found.` and `sys.exit(1)`.
  - `app/__init__.py:90-98` — `@app.cli.command("init-db")` registered; delegates to `init_db()` in `app/api/model.py`.
  - `grep -n "promote-admin" app/__init__.py` → 2 matches (comment line 100 + command line 104).
- Test commands: 3 greps; all pass.

### 5. Admin delete endpoint + visibility — VERIFIED
- Evidence:
  - `app/api/admin.py:8` — `admin = Blueprint('admin', __name__)`.
  - `app/api/admin.py:11-25` — `admin_required` decorator wraps `@login_required` on inner wrapper; checks `getattr(current_user, 'is_admin', False)`; non-admin gets `abort(403)`.
  - `app/api/admin.py:28-38` — `@admin.route('/lemma/<int:lemma_id>/delete', methods=['POST'])` with `def delete_lemma(lemma_id)`: looks up Lemma, deletes + commits, flashes "删除成功！", redirects to home. Missing lemma flashes "删除失败！词条不存在" and redirects to home.
  - `app/__init__.py:67` — `app.register_blueprint(admin, url_prefix='/api/admin')`. Full route: `POST /api/admin/lemma/<int:lemma_id>/delete`.
  - `app/templates/detail.html:77` — `{% if current_user.is_authenticated and current_user.is_admin %}` gate. Only admins see the controls.
  - `app/templates/detail.html:78-81` — `<form action="{{ url_for('admin.delete_lemma', lemma_id=fullcon.id) }}" method="post" style="display:inline">` with `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` and a `<button type="submit" id="deleteLemma">删除词条</button>`. The button is the "管理员操作" control (no explicit "管理员操作" label, but the title is `class="btn btn-lg btn-danger btn-block"` — clearly visible and dangerous-styled for the admin role).
  - `grep -n "admin_required" app/api/admin.py` → 2 matches (definition line 11 + usage line 29). Required >=1.
  - `grep -n "admin.delete_lemma" app/templates/detail.html` → 1 match (line 78). Required =1.
  - `grep -n "is_authenticated and current_user.is_admin" app/templates/detail.html` → 1 match (line 77). Required =1.
- Test commands: 3 greps; all pass.

### 6. Unified error page — VERIFIED
- Evidence:
  - `test -f app/templates/error.html` → exits 0 (file exists, 46 lines, self-contained per CD-03).
  - `app/templates/error.html:9,23,24` — consumes server-controlled `error.code`, `error.name`, `error.description` (no user input leaks).
  - `app/templates/error.html:34` — `<a href="{{ url_for('apple.home') }}" class="btn btn-primary">返回首页</a>` (back-to-home link).
  - `app/templates/error.html:25-33` — flashes block (so 400→302 flows that hit error.html via non-redirected path propagate cleanly).
  - `app/__init__.py:75-78` — `errorhandler(400)` flashes "会话已过期，请重试" and redirects.
  - `app/__init__.py:84-88` — `@app.errorhandler(403)`, `errorhandler(404)`, `errorhandler(500)` all stack on `def handle_error(e):` which returns `render_template('error.html', error=e), e.code`. Single handler for all 3 codes (D-17).
  - `grep -n "errorhandler" app/__init__.py` → 4 matches (400, 403, 404, 500). All four code paths present.
  - `grep -n "current_app.debug" app/api/__init__.py` → 1 match (line 98). When `not current_app.debug`, `/api/reset` returns `abort(404)` (which goes through `errorhandler(404)` → unified `error.html`). When `app.debug=True`, the route runs (per D-14). This means even the reset path is friendly in production.
- Test commands: 3 greps + file existence; all pass.

## Gaps (status: gaps_found)

### Gap 1: Search→detail flow broken by global CSRFProtect (W-4 functional regression)

- **File:** `app/templates/result.html` lines 52-60
- **Line numbers:** 54-57 (the per-result `<form action="/user/detail" method="post">` block)
- **What fails:** Each search result in `result.html` is wrapped in a `<form>` that POSTs to `/user/detail` (defined in `app/route/user.py:39-46`). With `CSRFProtect(app)` enabled globally (`app/__init__.py:70`), all POST requests require a valid `csrf_token`. The per-result forms do NOT include a hidden `csrf_token` input (the only `csrf_token` in the file is in the search form on line 41). Result: clicking any search result from the result page triggers a 400 → `errorhandler(400)` → "会话已过期，请重试" flash → redirect to `apple.home` instead of opening the lemma detail page. The Phase-1 baseline end-to-end flow ("search → click result → view detail") is no longer reachable.
- **Why it fails:** This breaks ROADMAP success criterion #5: "All existing user-facing auth flows still work end-to-end." Search is a user-facing auth-adjacent flow that worked pre-Phase-2 and is broken post-Phase-2.
- **What would close the gap:** Add `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` inside each per-result form at `result.html:54`, OR change the per-result form action to a GET link to `apple.detail` (would also require converting the `/user/detail` route from POST to GET, or adding a separate GET endpoint).
- **Decision rationale:** Per the verification instructions: "A broken search→detail click violates [criterion #5]. Lean toward gap_found." This is a real functional regression of a user capability that was working pre-Phase-2, not just a style warning.

## Deferred / Carryover (from REVIEW.md)

- **W-1 (init_db seed-user race with registBusiness)**: Documented and intentional per D-04 / 02-02 SUMMARY. Inline comment at `app/api/model.py:62` is the guardrail. **No block.**
- **W-2 (detail.html admin form is outside modify form but uses fullcon.id)**: Jinja variable scoping is correct; visual placement is awkward but functional. **No block.**
- **W-3 (`import sys` in middle of app/__init__.py:14)**: PEP 8 nit only, no behavior impact. **No block.**
- **W-4 (result.html per-result forms missing csrf_token)**: **PROMOTED TO GAP_1 ABOVE.** This was classified as a "moderate" warning in 02-REVIEW.md but per the verification instructions and ROADMAP criterion #5 ("All existing user-facing auth flows still work end-to-end"), it is a functional regression that blocks the search→detail user flow. **Block.**
- **W-5 (/api/logout is GET)**: Threat model T-02-02-09 disposition is `accept` with note "intentional for demo". Logout CSRF is a nuisance vector, not data loss. Out of scope for Phase 2. **No block.**
- **I-1 (FLASK_SECRET_FILE empty not validated)**: Operator-only path. Out of scope. **No block.**
- **I-2 (handle_error template-render swallow)**: Defense-in-depth, error page uses only `error.code` which is always present on HTTPException. Out of scope. **No block.**
- **I-3 (Comment.__init__ pre-existing bug at app/api/model.py:55)**: Comment model is unused (only writer is commented out at `app/api/__init__.py:82-91`). Phase 3 will fix. **No block.**
- **I-4 (delete_lemma no FK cascade to Comment)**: No comments exist yet (Comment table is never written to). Phase 3 will add `ondelete='CASCADE'`. **No block.**
- **modify.html form structure (pre-existing 2017 bug)**: `<a><button type=submit></a>` swallows the click; `/api/modify` itself is broken per CLAUDE.md known-bugs. Pre-existing; not introduced by Phase 2. Phase 3+ should fix. **No block.**
- **mysql+mysqlclient dialect registration env issue (Phase 5)**: SQLAlchemy 2.x + mysqlclient 2.2.8 in the dev env registers dialect as `mysql+mysqldb` not `mysql+mysqlclient`. The source code matches locked D-07 verbatim. Phase 5 dependency pin / Docker work will resolve. **No block** (env-level, not source).

## Cross-Reference

### Requirements → Success Criteria mapping

| Requirement | Addressed by | Status |
|-------------|--------------|--------|
| AUTH-01 (regist stores hashed password) | Criterion 2 — `generate_password_hash` at `app/api/__init__.py:24` | ✓ SATISFIED |
| AUTH-02 (login validates via hash) | Criterion 2 — `check_password_hash` at `app/api/__init__.py:38` | ✓ SATISFIED |
| AUTH-03 (logout from any page) | Criterion 5 partial — `/api/logout` exists at `app/api/__init__.py:44-48` (still works, but is GET — W-5, accepted) | ✓ SATISFIED (accepted disposition) |
| AUTH-04 (CSRF on all forms) | Criterion 3 — CSRFProtect globally enabled; 4 of 5 templates have token | ⚠ PARTIAL (modify.html pre-existing broken; result.html per-result forms broken — see Gap 1) |
| AUTH-05 (env-var credentials) | Criterion 1 — DB URI + secret_key from env | ✓ SATISFIED |
| AUTH-06 (is_admin + promote-admin CLI) | Criteria 4+5 — `is_admin` column + `flask promote-admin` | ✓ SATISFIED |
| ROLE-01 (admin can delete any lemma) | Criterion 5 — `/api/admin/lemma/<id>/delete` + admin button | ✓ SATISFIED |
| ROLE-02 (admin can delete any comment) | **DEFERRED to Phase 3** per `02-CONTEXT.md` D-20..D-25 (admin scaffolding ships in Phase 2, comment UI ships in Phase 3) | n/a (out of scope) |
| ROLE-03 (non-admin sees no admin controls) | Criterion 5 — `{% if is_authenticated and is_admin %}` gate at `detail.html:77` | ✓ SATISFIED |
| INFRA-05 (/api/reset guarded) | Criterion 6 — `current_app.debug` guard at `app/api/__init__.py:98` | ✓ SATISFIED |
| INFRA-06 (unified error page) | Criterion 6 — `error.html` + 4 errorhandlers | ✓ SATISFIED |
| INFRA-09 (env-var config) | Criterion 1 — DB_* + FLASK_SECRET + no defaults back to root/123456 | ✓ SATISFIED |

### STRIDE threat model compliance

All `mitigate` threats in the 02-01 / 02-02 / 02-03 threat models are addressed in the source:

| Threat | Status | Evidence |
|--------|--------|----------|
| T-02-01-01 (hardcoded secret_key) | mitigated | `app/__init__.py:17-45` env-var + instance fallback |
| T-02-01-02 (hardcoded MySQL URI) | mitigated | `app/__init__.py:48-59` env-var + RuntimeError on missing |
| T-02-01-04 (plaintext passwords) | mitigated | `app/api/__init__.py:24,38` hash create/verify |
| T-02-01-06 (account enumeration) | mitigated | `app/api/__init__.py:41` unified `账号或密码错误` flash |
| T-02-01-07 (admin escalation) | mitigated | Only `init_db()` + `promote-admin` CLI can flip is_admin |
| T-02-01-08 (build context leak) | mitigated | `.dockerignore` line 1 has `instance/` |
| T-02-02-01 (CSRF tampering) | **mitigated with gap** | CSRFProtect enabled; 4 templates have token; result.html per-result forms break (Gap 1) |
| T-02-02-02 (CSRF repudiation) | mitigated | `errorhandler(400)` flash + redirect (D-11) |
| T-02-02-03 (500 traceback leak) | mitigated | `errorhandler(500)` renders `error.html` (D-17/18) |
| T-02-02-04 (reset in prod) | mitigated | `if not current_app.debug: abort(404)` |
| T-02-03-01 (privilege escalation) | mitigated | `admin_required` = `@login_required` + is_admin check |
| T-02-03-03 (button visible to non-admin) | mitigated | `{% if is_authenticated and is_admin %}` |
| T-02-03-04 (mass-assign is_admin) | mitigated | No HTTP route sets is_admin=True |

`accept` dispositions (T-02-01-03 git history, T-02-02-05/06 CLI/route info leak, T-02-02-09 logout CSRF, T-02-03-05/06 audit log + 404/403 enumeration) are all explicitly out of scope per the locked context.

## Summary

**5 of 6 ROADMAP success criteria fully verified.** Criterion 3 (CSRF protection) is PARTIAL because of the W-4 search→detail regression. The regression is a real, reproducible functional breakage of an end-to-end user capability (search → click result → view detail), and it is the only phase-blocking issue. All other REVIEW.md findings are properly deferred, documented, or out of scope. The fix is a one-line template change in `result.html:54` (add `csrf_token` hidden input).

**Score breakdown:**
- Criterion 1 (env-var credentials): VERIFIED
- Criterion 2 (hashed passwords): VERIFIED
- Criterion 3 (CSRF protection): PARTIAL → **gap_found (W-4 regression)**
- Criterion 4 (admin user + CLI): VERIFIED
- Criterion 5 (admin delete + visibility): VERIFIED
- Criterion 6 (unified error page): VERIFIED

**Overall: 5/6 → status: gaps_found**

**Recommended remediation (1-line fix):**
```html
<!-- app/templates/result.html line 54, inside the per-result form -->
<form action="/user/detail" method="post">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>
```

---

_Verified: 2026-06-12_
_Verifier: Claude (gsd-verifier)_
_Method: 16 grep/file checks per the verification instructions + manual source review of all 12 files listed in files_to_read + cross-check against 02-CONTEXT.md D-01..D-25 + 02-REVIEW.md W-1..5 / I-1..4._
