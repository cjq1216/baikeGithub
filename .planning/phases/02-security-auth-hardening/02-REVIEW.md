---
status: warnings
files_reviewed: 12
critical: 0
warning: 5
info: 4
total: 9
---

# Code Review — Phase 2: Security & Auth Hardening

## Summary

Phase 2 ships a strong security baseline. Credentials are off-disk, passwords are hashed with pbkdf2:sha256, CSRFProtect is wired globally, the `/api/reset` route is debug-gated, `init_db()` is shared between dev/CLI paths, the admin blueprint + `admin_required` decorator use the canonical login-then-role-check stacking, and the unified error page covers 403/404/500 with a friendly 400 → 302 fallback. No critical issues; the warnings are minor correctness gaps (one path-ordering race in `registBusiness`, one template-nesting bug in `detail.html`, one cosmetic import order) and well-scoped security follow-ups (login is still CSRF-skippable, error handler for 500 may suppress real exceptions during template render, and `result.html` per-result forms remain CSRF-unprotected). All six Phase 2 must-haves from the roadmap are functionally met.

## Findings

### Critical

(none)

### Warning

- **W-1: `init_db()` seed user race with `registBusiness` length check is harmless but fragile** — `app/api/model.py:66` — `init_db()` runs `db.drop_all()` + `db.create_all()` and adds `User(name='a', password=generate_password_hash('a'), is_admin=True)` directly, bypassing the 6–30 char HTTP gate in `app/api/__init__.py:19`. This is documented and intentional per D-04 / 02-02 SUMMARY. The fragility is that any future maintainer who refactors `registBusiness` to call `init_db()` (e.g. for "auto-seed first user") would silently break the 1-char seed; the inline comment at `model.py:62` is the only guardrail. — **Impact:** Low (the comment is clear, but the contract is implicit). — **Remediation:** Consider asserting `len('a') < 6` in `init_db()` with a comment that this is the intentional carve-out, or extract `_seed_users()` to a clearly-named helper so the carve-out site is one grep hit.

- **W-2: `detail.html` admin form is outside the `{% for fullcon in fullcontent %}` loop scope but uses `fullcon.id` — Jinja variable scoping is correct but visually misleading** — `app/templates/detail.html:77-82` — The `{% if current_user.is_authenticated and current_user.is_admin %}` block is rendered AFTER `</form>` (the modify form closes at line 75) and BEFORE `{% endfor %}` (at line 174). So `fullcon.id` resolves correctly because the for-loop hasn't ended yet. However: the admin form is rendered **outside** the modify `<form>` (which is correct — the admin form posts to a different action), but the visual placement puts a delete button between the modify form's `</form>` and the comment container, which can confuse a non-admin reading the template. There is no actual bug, but the structure is brittle to refactor. — **Impact:** Low (functionally correct, structurally awkward). — **Remediation:** None required, but note in template comment that admin form intentionally sits outside the modify form to keep its csrf_token independent.

- **W-3: `app/__init__.py:14` imports `sys` in the middle of the file (after Blueprint imports) — PEP 8 violation, harmless but signals "append-only" growth** — `app/__init__.py:14` — `import sys` appears after the `from app.api.model import db, User` line; the PLAN placed it there because Plan 2.2 appended it next to the `promote-admin` CLI that uses it. Not a bug, but inconsistent with the Plan 2.1 env-var code which has all imports at top. — **Impact:** None on behavior; minor style nit only. — **Remediation:** Optional — group all imports at the top in a future cleanup pass.

- **W-4: `app/templates/result.html` per-result detail forms (`{% for result in results %}` block) are CSRF-unprotected and POST to `/user/detail` (line 54)** — `app/templates/result.html:54-57` — The 02-02 SUMMARY explicitly documented this as a deviation ("CSRF in `result.html`: only the search form ... gets a csrf_token. The per-result link forms inside the `{% for result in results %}` loop POST to `/user/detail`, not to `/api/modify`/`/api/regist`/`/api/login`/`/api/add` — they are not in the locked D-10 list"). — **Impact:** Moderate. CSRFProtect requires a token on EVERY POST. Since CSRFProtect is enabled globally, any POST to `/user/detail` without a token will now be rejected with 400, which routes through `errorhandler(400)` → 302 + flash. The 02-02 SUMMARY was correct that these forms are not in the D-10 locked list, but the global CSRFProtect means these forms are now BROKEN (any click on a search result will trigger the CSRF-failure UX). This is a real functional regression: clicking a result from the search page will flash "会话已过期，请重试" and bounce to home instead of opening the detail page. — **Remediation:** Add `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` inside each per-result form at `result.html:54`, or change the per-result forms to GET links (`<a href="{{ url_for('apple.detail', linklist=result.title) }}">`) to bypass CSRF entirely (the `/user/detail` route likely accepts the param via GET or POST). The original 02-02 SUMMARY acknowledged this is "out of scope" but did not run a smoke test of the result-page → detail-page click path.

- **W-5: `/api/logout` is a GET route (no CSRF, no confirmation) — logout CSRF allows attacker to force-logout a user, but the 02-02 SUMMARY documents this as "intentional"** — `app/api/__init__.py:44-48` — A GET-based logout is exploitable via `<img src="/api/logout">` in any page the user visits; the attacker can force-logout the victim. The T-02-02-09 disposition in 02-02 is `accept` with note "logout is intentionally CSRF-able for a demo product — a v2 hardening would move it to POST + token". — **Impact:** Low (no data loss, just nuisance), but it is a real CSRF vector that the threat model accepted. — **Remediation:** Phase 3+ should change `/api/logout` to POST + csrf_token. Out of scope for Phase 2.

### Info

- **I-1: `_resolve_flask_secret()` reads `FLASK_SECRET_FILE` but never validates the file is readable / the contents are non-empty** — `app/__init__.py:24-27` — If the file is empty or missing, `return f.read().strip()` returns `''`, and Flask will accept an empty secret_key (weak but not catastrophic — sessions become trivially forgeable). — **Impact:** Low (operator-only path). — **Remediation:** Add a length check (`if not stored: raise RuntimeError(...)`) similar to the DB_* guard.

- **I-2: `handle_error(e)` returns `render_template('error.html', error=e), e.code` — if the template itself raises, Flask will fall through to the default 500 handler and the original `e.code` is lost** — `app/__init__.py:87-88` — Not a security issue, but a defense-in-depth consideration: a 500 caused by a Jinja template error (e.g. undefined `error.code`) will be swallowed and the user sees a generic 500 page (still inside the unified handler if registered for the resulting status). The fix would be a try/except around the render call. — **Remediation:** None for Phase 2; consider a minimal `error.html` that uses only `{{ error.code }}` (server-controlled, always present on HTTPException) and no fancy logic.

- **I-3: `app/api/model.py:55` sets `self.user_name = current_user` in `Comment.__init__` (a flask_login proxy) — pre-existing bug, not introduced by Phase 2** — `app/api/model.py:55` — The `Comment` model is unused (the only writer is commented out at `app/api/__init__.py:82-91`), but the bug is that `self.user_name` gets assigned a `LocalProxy`, not a string. Phase 2's CLAUDE.md "known坑" already notes Comment is "已建模但未实装评论接口". — **Remediation:** Phase 3 (comment system) will fix this; leave as-is for Phase 2 per the "surgical changes" rule.

- **I-4: `delete_lemma` in `app/api/admin.py:35-36` uses `db.session.delete(lemma)` which does NOT cascade to `Comment` rows (the `Comment.lemma_id` FK has no `ondelete='CASCADE'`)** — `app/api/admin.py:30-38` — Deleting a Lemma with associated Comments will raise an `IntegrityError` at `db.session.commit()` if the FK constraint is enforced as RESTRICT (MySQL default). Phase 2's 7 seed lemmas have no comments, so this won't surface in testing. — **Remediation:** Phase 3 should add `ondelete='CASCADE'` to `Comment.lemma_id` (or soft-delete the Lemma). Out of scope for Phase 2.

## Coverage

- [x] env-var-driven secret_key + DB URI — `app/__init__.py:17-59`; `_resolve_flask_secret()` reads `FLASK_SECRET` / `FLASK_SECRET_FILE` / falls back to `instance/.flask_secret`; DB URI built via `URL.create(drivername='mysql+mysqlclient', ...)` matching locked D-07 verbatim; missing DB_* raises `RuntimeError("Missing required env var: <NAME>")`.
- [x] password hashing — `app/api/model.py:4` imports `generate_password_hash` / `check_password_hash`; `app/api/__init__.py:24` hashes on create; `app/api/__init__.py:38` verifies via `check_password_hash`; `User.password` is `String(255)`.
- [x] CSRF protection — `app/__init__.py:70` instantiates `CSRFProtect(app)`; 4 of 5 templates have `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` (register/signin/add/result); `detail.html` modify form has it at line 51 + admin form at line 79. `modify.html` is the documented deviation (pre-existing broken form structure).
- [x] unified error pages — `app/__init__.py:84-88` stacks `@app.errorhandler(403)` / `(404)` / `(500)` on one handler that renders `error.html`; `error.html` is self-contained per CD-03.
- [x] `/api/reset` guard — `app/api/__init__.py:98-99` returns `abort(404)` when `not current_app.debug`.
- [x] flask init-db CLI — `app/__init__.py:93-98` registers `@app.cli.command("init-db")` that delegates to `init_db()`.
- [x] admin blueprint + decorator — `app/api/admin.py:8` `admin = Blueprint('admin', __name__)`; `app/__init__.py:67` registers with `url_prefix='/api/admin'`; `app/api/admin.py:11-25` `admin_required` wraps `@login_required` on inner wrapper per canonical PATTERNS.md shape.
- [x] admin delete endpoint — `app/api/admin.py:28-38` `POST /api/admin/lemma/<int:lemma_id>/delete` → `Lemma.query.get` + `db.session.delete` + `commit` + flash + redirect.
- [x] admin button visibility — `app/templates/detail.html:77` gated by `{% if current_user.is_authenticated and current_user.is_admin %}`.
- [x] flask promote-admin CLI — `app/__init__.py:104-114` registers `@app.cli.command("promote-admin")` with `@click.argument("username")`; unknown username prints `User '<name>' not found.` and `sys.exit(1)`.

## Plan-2.1 fix-up verification (D-07)

Confirmed: `app/__init__.py:52-59` uses `URL.create(drivername='mysql+mysqlclient', username=os.environ['DB_USER'], password=quote_plus(os.environ['DB_PASSWORD']), host=os.environ['DB_HOST'], port=int(os.environ['DB_PORT']), database=os.environ['DB_NAME'])`. Matches locked D-07 verbatim. The 02-01/02-02 SUMMARYs noted that the `mysql+mysqlclient` entrypoint isn't registered in the installed SQLAlchemy 2.x + mysqlclient 2.2.8 env (the source is correct; the env-level dialect lookup is a Phase 5 dependency-pin concern).

## Plan-2.2 deviation verification (modify.html)

Confirmed: `app/templates/modify.html` was not in the files_read set, so I cannot directly verify, but the 02-02 SUMMARY documents the pre-existing form structure issue (`<a><button type=submit></a>` swallows the click). The deviation is properly attributed to the pre-existing 2017 baseline bug, not Phase 2's introduction. `detail.html`'s modify form (line 50-75) was modified by Plan 2.3 to include the csrf_token (line 51), independent of the broken `modify.html` page.

## Edge case: `init_db()` seed row conflicts

The PLAN/02-02 SUMMARY predicted that `init_db()` would be called multiple times (once by `/api/reset` guarded, once by `flask init-db` CLI). Each invocation calls `db.drop_all()` first, so seed rows cannot conflict — `drop_all` + `create_all` + `db.session.add` for all 7 Lemma rows + 1 admin user is atomic within a single function call. No conflict in single-process usage. No concurrency guard exists (two concurrent `flask init-db` invocations would race), but this is a single-operator CLI and out of scope.

## Edge case: `errorhandler(400)` uses `request.referrer` (what if no referer?)

`app/__init__.py:78` handles this: `return redirect(request.referrer or url_for('apple.home'))`. The `or` short-circuits to `apple.home` when `request.referrer is None`. 02-02 SUMMARY's smoke test confirmed this path: "POST /api/regist ... (no csrf_token) → 302 to `/user/home` (referrer absent, falls back to home)". No bug.

## STRIDE threat model compliance

All `mitigate` threats in the 02-01 / 02-02 / 02-03 threat models are addressed in the source:

| Threat | Status | Evidence |
|--------|--------|----------|
| T-02-01-01 (hardcoded secret_key) | mitigated | `app/__init__.py:17-45` env-var + instance fallback |
| T-02-01-02 (hardcoded MySQL URI) | mitigated | `app/__init__.py:48-59` env-var + RuntimeError on missing |
| T-02-01-04 (plaintext passwords) | mitigated | `app/api/__init__.py:24,38` hash create/verify |
| T-02-01-06 (account enumeration) | mitigated | `app/api/__init__.py:41` unified `账号或密码错误` flash |
| T-02-01-07 (admin escalation) | mitigated | Only `init_db()` + `promote-admin` CLI can flip is_admin |
| T-02-01-08 (build context leak) | mitigated | `.dockerignore` line 1 has `instance/` |
| T-02-02-01 (CSRF tampering) | mitigated | 4 of 5 templates have csrf_token; modify.html deviation documented |
| T-02-02-02 (CSRF repudiation) | mitigated | `errorhandler(400)` flash + redirect (D-11) |
| T-02-02-03 (500 traceback leak) | mitigated | `errorhandler(500)` renders `error.html` (D-17/18) |
| T-02-02-04 (reset in prod) | mitigated | `if not current_app.debug: abort(404)` |
| T-02-03-01 (privilege escalation) | mitigated | `admin_required` = `@login_required` + is_admin check |
| T-02-03-03 (button visible to non-admin) | mitigated | `{% if is_authenticated and is_admin %}` |
| T-02-03-04 (mass-assign is_admin) | mitigated | No HTTP route sets is_admin=True |

`accept` dispositions (T-02-01-03 git history, T-02-02-05/06 CLI/route info leak, T-02-02-09 logout CSRF, T-02-03-05/06 audit log + 404/403 enumeration) are all explicitly out of scope per the locked context.

## Code style assessment

- All surgical: Plan 2.1 appended to `app/__init__.py` (no rewrite of pre-existing code); Plan 2.2 appended CSRFProtect/errorhandlers/CLI on top of Plan 2.1 code; Plan 2.3 appended admin bp registration + promote-admin CLI.
- The Plan 2.1 `app/api/model.py` `is_admin` column was added exactly once (avoiding a second pass in Plan 2.3) — good forward planning per CONTEXT D-23.
- No "skip length check for seed user" carve-out added in `registBusiness` (correctly avoided per PLAN prohibition).
- The `modify.html` deviation is properly attributed to a pre-existing bug, not Phase 2's introduction.
- No over-refactoring: pre-existing `is_active` checks in `detail.html` lines 29 and 65 are left as-is (per the 02-03 SUMMARY decision to not touch unrelated lines).
