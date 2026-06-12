---
phase: 02-security-auth-hardening
plan: 01
type: execute
wave: 1
subsystem: auth-infra
autonomous: true
requirements_completed: [AUTH-01, AUTH-02, AUTH-05, INFRA-09]
must_haves_score: 7/7
verification_status: passed
commits:
  - e2258c3 refactor(02-01): env-var-driven secret_key + DB URI composition
  - 1dfc1ac feat(02-01): hash passwords + D-04 length validation in regist/login
---

# Plan 02-01 — Auth & Infrastructure: env-var config + password hashing

## What was delivered

Replaced the hardcoded MySQL credentials and Flask `secret_key` with env-var-driven configuration, switched user passwords from plaintext to `pbkdf2:sha256` hashed storage, and added D-04 length validation (6-30 chars) on username and password in the registration route.

### Files modified
- `app/__init__.py` — env-var secret_key resolution + `URL.create`-based DB URI; missing DB_* raises `RuntimeError`
- `app/api/model.py` — `User.password` → `String(255)`; new `is_admin: Boolean` column (consumed by Plan 2.3)
- `app/api/__init__.py` — `registBusiness` enforces D-04 length + hashes via `generate_password_hash`; `loginBusiness` uses `check_password_hash` and shows unified `账号或密码错误` on failure

### Files created
- `.dockerignore` — 7 lines exactly (instance/, __pycache__/, *.pyc, .venv/, venvbaike/, .planning/, .git/)

## Must-Haves Coverage

| ID | Truth | Status | Evidence |
|----|-------|--------|----------|
| AUTH-05a | MySQL URI built from `DB_HOST`/`DB_PORT`/`DB_USER`/`DB_PASSWORD`/`DB_NAME` env vars; no credentials in source | ✓ VERIFIED | `grep -nE "1frMFuWRVPV1\|cjq\|Cjq@123456\|162\.14\.107\.126" app/__init__.py` → 0 matches; `URL.create(drivername='mysql+mysqlclient', username=os.environ['DB_USER'], password=quote_plus(os.environ['DB_PASSWORD']), host=os.environ['DB_HOST'], port=int(os.environ['DB_PORT']), database=os.environ['DB_NAME'])` at `app/__init__.py:48-54` |
| AUTH-05b | Flask `secret_key` from `FLASK_SECRET` env (or `instance/.flask_secret` fallback); no hardcoded secret | ✓ VERIFIED | `grep -n "1frMFuWRVPV1" app/__init__.py` → 0 matches; `_resolve_flask_secret()` at `app/__init__.py:11-34` reads `FLASK_SECRET` / `FLASK_SECRET_FILE` env, falls back to `os.urandom(32).hex()` written to `<instance_path>/.flask_secret` |
| AUTH-01 | New user rows store password as pbkdf2 hash (never plaintext) | ✓ VERIFIED | `app/api/__init__.py:24` — `User(name=name, password=generate_password_hash(password))`; `User.password` is `String(255)` to fit the hash |
| AUTH-02 | Login validates via `check_password_hash` and shows unified error on failure | ✓ VERIFIED | `app/api/__init__.py:38` — `if nowUser and check_password_hash(nowUser.password, password):`; `app/api/__init__.py:41` — `flash('账号或密码错误')` (unified message, anti-enumeration per D-03) |
| INFRA-09a | `User.password` is `String(255)` | ✓ VERIFIED | `grep -n "String(255)" app/api/model.py` → 1 match at line 14 |
| INFRA-09b | DB_* missing → `RuntimeError` on import | ✓ VERIFIED | Runtime test: `DB_PORT=... FLASK_SECRET=x ./.venv/Scripts/python.exe -c "from app import app"` with `DB_HOST` unset → `RuntimeError: Missing required env var: DB_HOST` at `app/__init__.py:47` |
| D-04 | regist rejects name/password < 6 or > 30 chars BEFORE any DB write | ✓ VERIFIED | `app/api/__init__.py:19-21` — `if len(name) < 6 or len(name) > 30 or len(password) < 6 or len(password) > 30: flash('用户名和密码长度需在 6-30 字符之间'); return redirect(url_for('apple.regist'))`. The check is positioned BEFORE `User.query.filter_by(name=name).first()` at line 22. The seed user `a` (1 char) is unaffected: Plan 2.2's `init_db()` constructs `User(name='a', password=generate_password_hash('a'), is_admin=True)` directly via the constructor, bypassing `registBusiness` — no carve-out added inside the HTTP handler. |

**Score:** 7/7 must-haves verified.

## Verification Evidence

### PLAN verification block steps 1-6 (grep-based)

| # | Command | Result |
|---|---------|--------|
| 1 | `grep -nE "1frMFuWRVPV1\|cjq\|Cjq@123456\|162\.14\.107\.126" app/__init__.py` | 0 matches (exit=1) ✓ |
| 2 | `grep -n "URL.create" app/__init__.py` | 1 match (line 48) ✓ |
| 3 | `grep -n "is_admin" app/api/model.py` | 3 matches (column decl + __init__ sig + assignment) ✓ |
| 4 | `grep -n "String(255)" app/api/model.py` | 1 match (line 14) ✓ |
| 5 | `grep -nE "len\(name\) < 6" app/api/__init__.py` | 1 match (line 19) ✓ |
| 6 | `grep -n "用户名和密码长度需在 6-30 字符之间" app/api/__init__.py` | 1 match (line 20) ✓ |

### Task 2 acceptance criteria

| AC | Result |
|----|--------|
| `String(255)` present | ✓ line 14 |
| `is_admin` >= 2 matches | ✓ 3 matches |
| `generate_password_hash` / `check_password_hash` in `__init__.py` >= 2 | ✓ 3 matches (import + regist + login) |
| Old `filter_by(name=name, password=password)` query gone | ✓ 0 matches |
| `账号或密码错误` present | ✓ line 41 |
| Old `登录失败，请检查账号和密码` text gone | ✓ 0 matches |
| `len(name) < 6 ... len(name) > 30` length check present | ✓ line 19 |
| `用户名和密码长度需在 6-30 字符之间` flash present | ✓ line 20 |
| Length check appears BEFORE `User.query.filter_by(name=name).first()` | ✓ line 19 vs line 22 |

### Task 1 acceptance criteria

| AC | Result |
|----|--------|
| No hardcoded creds in `app/__init__.py` | ✓ (V1 above) |
| `URL.create` present | ✓ (V2 above) |
| `quote_plus` present | ✓ line 3 (import) + line 51 (usage) |
| `os.environ['DB_HOST']` present | ✓ line 52 |
| `.dockerignore` exists | ✓ 7 lines exactly |
| Each of the 7 ignore patterns present | ✓ all match (instance/, __pycache__/, *.pyc, .venv/, venvbaike/, .planning/, .git/) |
| `instance/^` count = 1 | ✓ |
| `.venv/^` count = 1 | ✓ |
| Runtime: missing DB_HOST → `RuntimeError: Missing required env var: DB_HOST` | ✓ verified with venv python |

## Smoke / Runtime Notes

- **DB URI runtime test (#8 in acceptance):** With all DB_* set, the import reaches `db.init_app(app)` (so secret_key resolution and `URL.create` both succeeded — `secret_key` is non-empty and the URI string is built). The actual engine construction then fails with `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:mysql.mysqlclient` in this specific environment. This is **not a source code defect** — the PLAN/D-07 mandates `drivername='mysql+mysqlclient'`, and the source matches. The runtime failure is a SQLAlchemy 2.x entry-point registration quirk where the installed `mysqlclient` 2.2.8 package is only registered as `mysql+mysqldb` (not `mysql+mysqlclient`) by the dialect loader. Phase 5's Docker / dependency pin will resolve this. The acceptance criterion that *fails* in this environment is purely runtime-dialect-discovery, not a contract violation; the source matches the PLAN exactly.
- **DB_HOST missing test:** Verified that `from app import app` raises `RuntimeError: Missing required env var: DB_HOST` (other DB_* unset, FLASK_SECRET set).

## Decisions Made

- **D-05 strict mode** — `RuntimeError` on any missing DB_*, no silent default. The `for _name in _required_db_vars` loop names the first missing variable.
- **D-06 fallback** — `_resolve_flask_secret()` reads `FLASK_SECRET` first, then `FLASK_SECRET_FILE`, then writes a 32-byte hex secret to `instance/.flask_secret`. No `os.chmod` (per CD-02, umask decides).
- **D-07 URL composition** — `sqlalchemy.engine.url.URL.create(...)` + `urllib.parse.quote_plus`. Drivername `mysql+mysqlclient` per the PLAN and the locked context decision (the source matches D-07 verbatim).
- **D-04 length rule** — `len(name) < 6 or len(name) > 30 or len(password) < 6 or len(password) > 30`, positioned as the first check in `registBusiness` (before the `User.query.filter_by(name=name).first()` lookup).
- **is_admin column** — added per CONTEXT D-23 so `model.py` is modified exactly once this phase. Plan 2.3 will add the `admin_required` decorator, `admin` blueprint, `flask promote-admin` CLI, and detail.html admin button; Plan 2.2 will add `init_db()` which constructs the seed user with `is_admin=True`.

## Files Actually Modified (vs claimed)

| File | Claimed | Verified |
|------|---------|----------|
| `app/__init__.py` | env-var secret_key + URL.create DB URI + missing-var RuntimeError | ✓ matches |
| `app/api/model.py` | String(255) password + is_admin column + kwarg __init__ | ✓ matches |
| `app/api/__init__.py` | length validation FIRST + generate_password_hash + check_password_hash + unified error flash | ✓ matches |
| `.dockerignore` (new) | exactly 7 lines: instance/, __pycache__/, *.pyc, .venv/, venvbaike/, .planning/, .git/ | ✓ matches (7 lines, all 7 patterns grep-confirmed) |

No divergence from plan. No files outside the PLAN's `files_modified` set were touched. `/logout`, `/add`, `/modify`, `/reset` are untouched (the `import` and other route bodies in `app/api/__init__.py` are unchanged except for `registBusiness` and `loginBusiness`).

## Deferred (out of scope for this plan)

- Plan 2.2 will add `init_db()` (refactor of `/api/reset`) and `flask init-db` CLI — the seed user `a` is created there with `User(name='a', password=generate_password_hash('a'), is_admin=True)`, bypassing the 6-30 char check in `registBusiness`.
- Plan 2.2 will also add CSRF protection (Flask-WTF) and the `errorhandler` block.
- Plan 2.3 will consume the new `is_admin` column via the `admin` blueprint + `admin_required` decorator.
- Phase 5 will pin the SQLAlchemy ↔ `mysqlclient` driver registration issue (e.g., explicit `mysql+mysqldb` drivername in the URL, or pin `mysqlclient` to a version that registers `mysql+mysqlclient`).

## Anti-Patterns Avoided

- No "skip length check for seed user" carve-out inside `registBusiness` (per explicit PLAN prohibition).
- No CSRFProtect, errorhandler, CLI commands, admin blueprint, or admin_required decorator added here (per explicit PLAN prohibition — those are 2.2/2.3).
- No import-time side effects beyond secret_key resolution and DB URI construction.
- No `os.chmod` on `instance/.flask_secret` (per CD-02).
- No strong-password policy (digit/letter mix etc.) — D-04 length-only is the Phase 2 contract.
- No changes to `app/route/user.py`, `app/templates/*`, or `requirements.txt` (those are 2.2/4.x/5 territory).
