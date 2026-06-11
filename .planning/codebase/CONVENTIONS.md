# Coding Conventions

**Analysis Date:** 2026-06-11

## Naming Patterns

**Files:**
- Python modules use lowercase with optional underscore separators: `run.py`, `user.py`, `model.py`, `__init__.py`
- HTML templates use lowercase English: `home.html`, `signin.html`, `register.html`, `add.html`, `modify.html`, `result.html`, `detail.html`
- One file breaks the convention: `app/templates/detail示例.html` (mixed CJK + English) — appears to be a reference example, not an active template

**Functions (Python):**
- View functions use camelCase in some places and snake_case in others — inconsistent:
  - camelCase: `registBusiness()` (`app/api/__init__.py:16`), `loginBusiness()` (`app/api/__init__.py:32`)
  - snake_case: `load_user()` (`app/__init__.py:21`)
  - Single-word: `home()`, `login()`, `regist()`, `add()`, `search()`, `detail()`, `modify()`, `logout()`, `reset()`
- SQLAlchemy `__str__` methods return Chinese-formatted strings (e.g. `'用户<id:%s, 姓名:%s>'`, `'词条<title:%s, contet:%s>'`) — see `app/api/model.py:24,39`

**Variables:**
- snake_case: `searchtext`, `fullcontent`, `newTitle`, `newContent`, `entirelytitle`, `nowUser`, `nowTitle`
- Local variables sometimes shadow the `user` module identifier:
  - Inside `registBusiness()`: `user = User(...)` (`app/api/__init__.py:22`) — overwrites the outer `user` Blueprint reference
  - `uesrname` typo at `app/api/__init__.py:20` (variable assigned but never used)

**Types (SQLAlchemy Models):**
- PascalCase class names: `User`, `Lemma`, `Comment` (`app/api/model.py:16,30,45`)
- Table-name attributes are misspelled `__tablenanme__` (should be `__tablename__`) on all three models — see `app/api/model.py:18,32,47`. Because the attribute is misspelled, SQLAlchemy falls back to auto-generated table names (`user`, `lemma`, `comment`) rather than the explicit values.

**Blueprints:**
- `user` Blueprint uses the import name `apple` (`app/route/user.py:8`):
  ```python
  user = Blueprint('apple', __name__)
  ```
  All `url_for()` calls in this project reference `'apple.home'`, `'apple.login'`, etc. This is a known, load-bearing oddity — do not "fix" it without updating every `url_for` callsite.

## Code Style

**Formatting:**
- No formatter configured (no `.prettierrc`, `pyproject.toml`, `setup.cfg`, `.flake8`, `black`/`isort` config present)
- Tabs are used for indentation in some files (visible mixed indentation in `app/__init__.py:22` where `return User.query.get(int(id))` is indented with a tab, and in `app/api/__init__.py:10-13` where Blueprint args are tab-indented)
- Spaces are used elsewhere
- Trailing whitespace and inconsistent blank lines are present throughout

**Linting:**
- No linter configured (no `.pylintrc`, `ruff.toml`, `.flake8`, `mypy.ini`)
- No type hints anywhere in the codebase

**Encoding Header:**
- Every Python file begins with `# coding=utf-8` (line 1): `run.py:1`, `app/__init__.py:1`, `app/api/__init__.py:1`, `app/api/model.py:1`, `app/route/user.py:1`

## Import Organization

**Order observed:**
1. Standard library: `sys`, `datetime`, `random`
2. Third-party Flask ecosystem: `flask`, `flask_login`, `flask_sqlalchemy`
3. Local app modules: `from app.api.model import ...`, `from app.route.user import user`, `from app import app`

**Path Aliases:**
- None — no `sys.path` manipulation beyond the standard package layout
- No `conftest.py` or `setup.py` defining package metadata

**Python 2 Compatibility Boilerplate:**
- `app/api/__init__.py:2-4` and `app/api/model.py:2-4`:
  ```python
  import sys
  reload(sys)             # NameError on Python 3
  sys.setdefaultencoding('utf8')
  ```
  This is a Python 2 idiom. On Python 3 (which the project is implicitly expected to run, given `mysql-python` is a Py2-only package, yet the Flask stack is Py3-compatible), `reload` does not exist in `sys` and this code raises `NameError` on import. Flag this if Python 3 is the target.

## Configuration

**Hardcoded values (anti-pattern — no external config is read by the application):**
- `app.secret_key = '1frMFuWRVPV1'` — `app/__init__.py:10`
- MySQL DSN is hardcoded in **two** places with literal credentials:
  - `app/__init__.py:11`: `"mysql://%s:%s@%s/%s" % ('root', '123456', '127.0.0.1', 'baike')`
  - `app/api/model.py:10`: same string, same credentials
- `config.ini` exists in the repo root but is a **uwsgi** config (`[uwsgi]` section), not an application config. It is not read by any Python code.
- `run.py:5`: `host='0.0.0.0'` is hardcoded; debug mode is hardcoded `True`

**No `.env`, no environment-variable reads, no config file parsing.** If adding new code, secrets and connection strings should NOT be added as new hardcoded literals; the existing pattern should be replaced by an `os.environ`/`.env` read.

## Error Handling

**Strategy: flash + redirect (the only error-handling pattern in the project).**

Examples (`app/api/__init__.py`):
- `registBusiness()` (`:28`): `flash('注册失败！帐号已存在')` then `return redirect(url_for('apple.regist'))`
- `loginBusiness()` (`:39`): `flash('登录失败，请检查账号和密码！')` then `return redirect(url_for('apple.login'))`
- `add()` (`:62`): `flash('添加失败！该词条已存在！')` then `return redirect(url_for('apple.add'))`
- `search()` in `app/route/user.py:36`: `flash('所查词条不存在，工作人员正在努力完整词条库～～')` then redirect home

**Patterns:**
- Chinese user-facing messages via `flash()`
- The flashed message is rendered in templates using `{% with messages = get_flashed_messages() %}` — see `home.html:44-52`, `signin.html:24-32`, `add.html:55-63`, `register.html:22-30`, `detail.html:107-115`
- `try/except` is **not used anywhere** in the application code — database errors, validation errors, and authentication failures all propagate to Flask's default 500 page
- `abort()` is imported in `app/api/__init__.py:6` but never called
- The `modify` endpoint (`app/api/__init__.py:65-73`) has a bug: it reads `request.form.get('newContent')` into **both** `newTitle` and `newContent`, then flashes success without redirecting — an `else` branch is missing and the function returns `None`

## Logging

**Framework:** None. `print()` and the `logging` module are not used.

**Observability:**
- No structured logging
- No request/response logging middleware
- The `reset` endpoint returns `jsonify(error=False)` (`app/api/__init__.py:100`) — this is the only JSON response in the project

## Comments

**When to Comment:**
- Sparse. Most view functions have no docstring or comment.
- A `commen` (comment) endpoint is entirely commented out at `app/api/__init__.py:76-85`
- A `detail1` route is commented out at `app/route/user.py:50-53`
- `app/api/model.py:14`: `#db = SQLAlchemy()` — orphan alternative declaration

**JSDoc/TSDoc:**
- Not used (Python project, no docstrings at all in this codebase)
- No module-level docstrings, no function docstrings, no class docstrings

## Function Design

**Size:** View functions are small (5–15 lines). The `reset` endpoint in `app/api/__init__.py:87-100` is the outlier (~14 lines) and is intentionally a data-seed script.

**Parameters:**
- View functions take no parameters — they read from `request.form`
- Models use explicit keyword constructors: `User(name=..., password=...)` (`app/api/model.py:26`)

**Return Values:**
- Views return either `render_template(...)` or `redirect(url_for(...))` — never raw strings, never JSON (except `reset`)
- On success of mutating endpoints, the pattern is `flash('<success message>')` then `redirect(url_for('apple.home'))`

## Module Design

**Exports:**
- Implicit. `app/__init__.py` exposes a module-level `app` (Flask instance)
- Blueprints are module-level singletons: `user = Blueprint(...)` (`app/route/user.py:7`), `api = Blueprint(...)` (`app/api/__init__.py:10`)

**Barrel Files:**
- `app/api/__init__.py` and `app/route/__init__.py` are used as package markers. `app/route/__init__.py` is empty (0 bytes).
- `app/api/__init__.py` doubles as the API blueprint definition file — the Blueprint is defined and all routes are registered in the same file. The `model.py` module is imported by it.
- The `app.api.model` module is unusual: it constructs its own `Flask(__name__)` and `SQLAlchemy(app)` at import time (`app/api/model.py:9-11`) — **in addition** to the app instance in `app/__init__.py`. The same DB URI is duplicated, and two `Flask` instances exist when `app.api.model` is imported. This is a load-bearing quirk; do not reorganize casually.

## Templates (HTML/Jinja2)

**Layout convention:**
- `<html lang="zh-cn">` is used in every template
- `<meta charset="utf-8">` declared in `<head>` of every template
- Each template hand-rolls the same nav bar — see `home.html:26-39`, `add.html:25-39`, `result.html:22-35`, `detail.html:25-39`, `modify.html:25-39`. The navbar is **not** factored into a base template (`{% extends %}` / `{% include %}`). No `base.html` exists.
- Flashed messages use the same block in every template:
  ```jinja
  {% with messages = get_flashed_messages() %}
  {% if messages %}
  <ul class=flashes>
      {% for message in messages %}
      <li class="error">{{ message }}</li>
      {% endfor %}
  </ul>
  {% endif %}
  {% endwith %}
  ```
- Static asset paths are relative (`../static/stylesheets/...`, `../static/javascripts/...`) — they assume a one-segment URL depth. This breaks when a route is nested deeper (e.g., any future blueprint with a `url_prefix`).
- jQuery 1.11.3 and Bootstrap JS are loaded at the bottom of every template; `wangEditor.min.js` is loaded on `add.html` and `detail.html` and `modify.html` for the rich-text editor.

## Summary of Prescriptive Guidance for New Code

- **Add a new view:** pick a blueprint (`app/api/__init__.py` for actions, `app/route/user.py` for page renders) and add a `@blueprint.route('/<path>', methods=[...])` decorator. Use the same `flash()` + `redirect()` style for user feedback.
- **Add a new model:** place it in `app/api/model.py` (or a new sibling module) inheriting `db.Model`. Use the existing constructor pattern: `def __init__(self, name=None, password=None):`. Add a `__str__` returning a Chinese-formatted string.
- **Add a new template:** place it under `app/templates/`, copy the nav block from `home.html:26-39` and the flash block, and use `<html lang="zh-cn">` + `<meta charset="utf-8">`.
- **Naming:** keep blueprint endpoint names matching the function (e.g., a route handler `home()` uses `url_for('apple.home')` because the Blueprint is `'apple'`).
- **Configuration:** do not add new hardcoded credentials or DSNs — read from environment variables and refactor the two existing literal-credential sites to use the same source.
- **Encoding header:** continue to include `# coding=utf-8` on line 1 of every Python file to match the existing convention (even though Python 3 source files do not require it).
- **Avoid the `reload(sys)` pattern** in any new module — it is broken on Python 3 and only exists in two files already; new code should not propagate it.

---

*Convention analysis: 2026-06-11*
