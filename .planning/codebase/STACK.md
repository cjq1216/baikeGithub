# Technology Stack

**Analysis Date:** 2026-06-11

## Languages

**Primary:**
- Python 2.7.18 (`C:\Python27`) - Backend application runtime; locked via `.venv/pyvenv.cfg` (`version_info = 2.7.18.final.0`).
  - Source files: `app/__init__.py`, `app/api/__init__.py`, `app/api/model.py`, `app/route/__init__.py`, `app/route/user.py`, `run.py`.

**Secondary:**
- HTML5 + Jinja2 templates - Server-rendered UI markup (`app/templates/*.html`).
- JavaScript (jQuery 1.11.3, Bootstrap 3 JS, wangEditor 2.x) - Client-side interactivity in `app/static/javascripts/`.
- CSS / LESS - Bootstrap 3, wangEditor styles, custom project styles under `app/static/stylesheets/`.

## Runtime

**Environment:**
- Python 2.7.18 (CPython) - Confirmed by `.venv/pyvenv.cfg` (`base-prefix = C:\Python27`).
- virtualenv 20.13.0 (project tooling; bootstrapped against Python 2.7).
- Werkzeug dev server (via `app.run()`) for local development (`run.py` line 5).

**Package Manager:**
- pip - Installed inside `.venv/` (`pip-20.3.4.dist-info` present).
- Lockfile: Not detected - `requirements.txt` exists at repo root but contains only unversioned package names; no `pip freeze` snapshot, no `Pipfile.lock`, no `poetry.lock`.

## Frameworks

**Core:**
- Flask (unversioned in `requirements.txt`) - Web framework. App object constructed in `app/__init__.py` line 9 (`app = Flask(__name__)`), blueprints registered at lines 17-18 (`/user` and `/api`).
- Flask-Login (unversioned) - Session/auth. `LoginManager` wired in `app/__init__.py` lines 13-15; `login_view = '.login'`; `@login_required` used on `app/api/__init__.py` lines 43, 49, 66 and `app/route/user.py` lines 25, 46.
- Flask-SQLAlchemy (unversioned) - ORM. `SQLAlchemy` instantiated in `app/api/model.py` line 11; `db.init_app(app)` in `app/__init__.py` line 12.

**Testing:**
- Not detected - No test framework, no `tests/` directory, no `pytest.ini`/`tox.ini`.

**Build/Dev:**
- uWSGI - Production WSGI server. Configured in `config.ini` (`[uwsgi]` section, `socket = 127.0.0.1:2002`, `wsgi-file = run.py`, `callable = app`). Note: the uwsgi stanza is the only content of `config.ini`; this file is the deployment config, not a Flask config.
- Bootstrap 3.x (frontend CSS/JS framework) - Served from `app/static/stylesheets/bootstrap.min.css` and `app/static/javascripts/bootstrap.min.js`.
- wangEditor 2.x (rich text editor) - Served from `app/static/javascripts/wangEditor/wangEditor.min.js` and `app/static/stylesheets/wangEditor/wangEditor.min.css`. Instantiated in `app/templates/add.html` line 84, `app/templates/detail.html` line 136, `app/templates/modify.html` line 87.

## Key Dependencies

**Critical (from `requirements.txt`):**
- `flask` - Web framework foundation.
- `flask_login` - User session and `@login_required` enforcement.
- `flask_SQLAlchemy` - ORM and `db.session`/`db.Model` API used in every model.
- `mysql-python` - MySQL C-extension driver for Python 2 (a.k.a. `MySQLdb`). No fallback driver (`PyMySQL`, `mysqlclient`) declared.

**Infrastructure:**
- MySQL 5.7.16 (per `baike.sql` dump header) - Target database. Connection string is hard-coded in two places:
  - `app/__init__.py` line 11: `mysql://root:123456@127.0.0.1/baike`.
  - `app/api/model.py` line 10: `mysql://root:123456@127.0.0.1/baike`.
  - Driver scheme `mysql://` matches `MySQLdb` only; SQLAlchemy 1.x accepts this without `mysql+pymysql://`.

## Configuration

**Environment:**
- No `.env` files present; no environment-variable based config.
- `app.secret_key` is hard-coded to `'1frMFuWRVPV1'` (`app/__init__.py` line 10).
- MySQL credentials (`root` / `123456` / `127.0.0.1` / db `baike`) are hard-coded literals in the two connection strings above.
- `config.ini` is a uWSGI deployment config only; it does NOT configure Flask.

**Build:**
- `requirements.txt` - Declares runtime Python deps (unpinned).
- `config.ini` - uWSGI deployment stanza (socket bind, chdir, wsgi-file, callable, processes=1, threads=1).
- `run.py` - Dev launcher: `app.run(debug=True, host='0.0.0.0')`.

## Platform Requirements

**Development:**
- Python 2.7.x (currently 2.7.18) on Windows (`C:\Python27` is the base interpreter).
- MySQL 5.7 reachable at `127.0.0.1:3306` with database `baike` and root password `123456`.
- Optional: `virtualenv` to recreate `.venv/` (matches README.md deployment instructions).

**Production:**
- uWSGI host bound to `127.0.0.1:2002` (per `config.ini`); an upstream HTTP server is implied but not declared.
- `chdir = /Users/chujunqi/work/python/baike/` in `config.ini` is a macOS-style absolute path from the original developer environment - it WILL NOT match this repo's location (`D:\work\baike`) and must be edited before any uWSGI deploy.

## Frontend Asset Inventory

- `app/static/stylesheets/bootstrap.min.css` + `bootstrap-theme.min.css` - Bootstrap 3.
- `app/static/stylesheets/mycss/*.css` - Project-specific styles (`blog.css`, `cover.css`, `detail.css`, `modify.css`, `result.css`, `signin.css`, `style.css`).
- `app/static/stylesheets/wangEditor/wangEditor.min.css` (+ `.less` source) - Editor styles.
- `app/static/stylesheets/fonts/icomoon.{eot,svg,ttf,woff}` - Icon font.
- `app/static/javascripts/jquery-1.11.3.min.js` - jQuery 1.11.3.
- `app/static/javascripts/bootstrap.min.js`, `docs.min.js`, `bootstrap.js`, `npm.js` - Bootstrap 3 JS bundle.
- `app/static/javascripts/wangEditor/wangEditor.min.js` (+ dev `wangEditor.js` and bundled `lib/jquery-1.10.2.min.js`, `lib/jquery-2.2.1.js`) - Rich text editor.

## Templates

- `app/templates/home.html` - Landing/search page (search form posts to `/user/search`).
- `app/templates/signin.html` - Login form (posts to `/api/login`).
- `app/templates/register.html` - Registration form (posts to `/api/regist`).
- `app/templates/add.html` - New lemma entry (wangEditor bound to `#content0`; posts to `/api/add`).
- `app/templates/modify.html` - Modify lemma (wangEditor bound to `#content0`).
- `app/templates/detail.html` - Lemma detail + comment surface (wangEditor bound to `#content1`; comment modal posts to `/api/commen`).
- `app/templates/result.html` - Search results list (each result is a form posting to `/user/detail`).
- `app/templates/detail示例.html` - Sample/template variant of `detail.html` (not wired into routes).

---

*Stack analysis: 2026-06-11*