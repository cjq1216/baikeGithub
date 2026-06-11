# External Integrations

**Analysis Date:** 2026-06-11

## APIs & External Services

**Third-party HTTP APIs:**
- None detected - No outbound HTTP client (`requests`, `urllib`, `httpx`) is imported anywhere in `app/`. The app makes no calls to external services.

**Rich-text editor (browser-side library, not a network service):**
- wangEditor 2.x - Loaded as a static asset from `app/static/javascripts/wangEditor/wangEditor.min.js`. Initialized in `app/templates/add.html:84`, `app/templates/detail.html:136`, `app/templates/modify.html:87` via `new wangEditor('<textarea-id>').create()`. No network calls.

## Data Storage

**Databases:**
- MySQL 5.7.16 (per `baike.sql` dump header `Distrib 5.7.16, for Linux (x86_64)`)
  - Connection: hard-coded URI in two locations:
    - `app/__init__.py:11` - `mysql://root:123456@127.0.0.1/baike`
    - `app/api/model.py:10` - identical URI (duplicate)
  - Client: SQLAlchemy via Flask-SQLAlchemy, models in `app/api/model.py` (`User`, `Lemma`, `Comment`).
  - Driver: `MySQLdb` (Python 2 C-extension), per `requirements.txt` entry `mysql-python`. SQLAlchemy URI scheme `mysql://` resolves to `MySQLdb` with no fallback.
  - Schema dump: `baike.sql` (3 tables - `user`, `lemma`, `comment` - all `ENGINE=InnoDB DEFAULT CHARSET=utf8`).

**File Storage:**
- None - No S3/GCS/Azure Blob usage; no file upload endpoints observed. Static assets are committed to `app/static/` and served by Flask itself.

**Caching:**
- None - No `flask-caching`, no Redis, no Memcached imports.

## Authentication & Identity

**Auth Provider:**
- Custom session auth via Flask-Login (no third-party identity provider).
  - Implementation:
    - `LoginManager` initialized in `app/__init__.py:13-15` with `login_view = '.login'` and `login_message` default.
    - User loader at `app/__init__.py:20-22` (`load_user(id)` queries `User` by primary key).
    - Models implement `UserMixin` (`app/api/model.py:16`).
    - Login endpoint `app/api/__init__.py:31-40` (`/api/login`, POST).
    - Registration endpoint `app/api/__init__.py:15-29` (`/api/regist`, POST) - auto-logs in the user after creating the `User` row.
    - Logout endpoint `app/api/__init__.py:42-46` (`/api/logout`, GET).
  - Password storage: plaintext in `User.password` (`db.Column(db.String(40))`). Hashed/equal length matching the column width (40 chars) suggests intent to use SHA-1 hex digests, but no hashing logic is present in `app/api/__init__.py:registBusiness` or `loginBusiness` - the raw form value is stored and compared directly.
  - Session secret: hard-coded in `app/__init__.py:10` (`app.secret_key = '1frMFuWRVPV1'`).

**CSRF:**
- Not enabled - No `flask_wtf.csrf.CSRFProtect` import, no CSRF tokens in any template form.

## Monitoring & Observability

**Error Tracking:**
- None - No Sentry/Rollbar/Bugsnag integration. Flask's default unhandled-exception page is used (or `debug=True` traceback in dev via `run.py`).

**Logs:**
- No logging framework in use - `app/__init__.py`, `app/api/__init__.py`, `app/api/model.py`, `app/route/user.py` contain no `import logging`. Output is via Flask's `flash()` messages and `print()` (none observed in app code).

## CI/CD & Deployment

**Hosting:**
- Local/on-prem only - No cloud provider config (no `Dockerfile`, no `.dockerignore`, no `Procfile`, no `app.yaml`, no Kubernetes manifests).
- WSGI entrypoint: `run.py` exports `app` from `app/__init__.py:9`. `config.ini` declares `wsgi-file = run.py` and `callable = app` for uWSGI.
- Socket bind (uWSGI): `127.0.0.1:2002` (`config.ini` line 3).
- `chdir` in `config.ini` points to the original developer's macOS path (`/Users/chujunqi/work/python/baike/`, line 5) and must be updated for any new environment.

**CI Pipeline:**
- None - No `.github/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `azure-pipelines.yml`, no `.travis.yml`.

## Environment Configuration

**Required env vars:**
- None - The app reads no environment variables. All config (DB URI, secret key) is hard-coded.

**Secrets location:**
- Hard-coded literals in source:
  - DB password `123456`: `app/__init__.py:11`, `app/api/model.py:10`.
  - Flask `secret_key` `'1frMFuWRVPV1'`: `app/__init__.py:10`.
- No `.env` file, no secrets manager, no vault integration.

## Webhooks & Callbacks

**Incoming:**
- None - All routes are user-facing HTML/POST endpoints under `/user/*` and `/api/*`. No webhook receiver pattern (no signature verification, no public `/webhook/*` endpoint).

**Outgoing:**
- None - The app does not call any external webhooks or callbacks. `flash()` is used for in-app user feedback, not for outbound notifications.

## Database Schema (from `baike.sql`)

- `user` (`id`, `name VARCHAR(30) UNIQUE`, `password VARCHAR(40)`) - InnoDB.
- `lemma` (`id`, `title VARCHAR(40)`, `content TEXT`) - InnoDB.
- `comment` (`id`, `user_name VARCHAR(30)`, `lemma_id INT`, `content VARCHAR(320)`, `time DATETIME`, FK `lemma_id` -> `lemma.id`) - InnoDB.

ORM mapping notes:
- `app/api/model.py` declares `__tablenanme__` (typo - `nanme` instead of `tablename`) on all three models (`User`, `Lemma`, `Comment`). This means SQLAlchemy falls back to default class-name based table naming (`user`, `lemma`, `comment`) which still matches the SQL dump, so the typo is silently harmless.

---

*Integration audit: 2026-06-11*