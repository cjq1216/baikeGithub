<!-- refreshed: 2026-06-11 -->
# Architecture

**Analysis Date:** 2026-06-11

## System Overview

```text
┌────────────────────────────────────────────────────────────────┐
│                       Browser (Client)                          │
│  Jinja2 templates rendered with Bootstrap + wangEditor + jQuery │
│  Forms POST to /user/* (rendering) and /api/* (mutations)      │
└──────────────────────────────┬─────────────────────────────────┘
                               │ HTTP (POST/GET)
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                  Flask App (`run.py` -> `app/__init__.py`)      │
│  - `app` factory-less singleton created at import time          │
│  - Secret key, MySQL URI, LoginManager wired here               │
│  - Two blueprints registered: `user` -> /user, `api` -> /api   │
│  - One top-level route: `/` -> home()                           │
└──────────────┬──────────────────────────────────┬──────────────┘
               │                                  │
               ▼                                  ▼
┌──────────────────────────────────┐  ┌──────────────────────────────┐
│  `user` Blueprint (apple)        │  │  `api` Blueprint              │
│  `app/route/user.py`             │  │  `app/api/__init__.py`        │
│  url_prefix='/user'              │  │  url_prefix='/api'            │
│  Responsibilities:               │  │  Responsibilities:            │
│   - GET page rendering           │  │   - POST form mutations       │
│   - POST search/detail           │  │   - auth: login/logout/regist │
│   - login_required on add/modify │  │   - CRUD: add/modify/reset    │
│   - redirect on success/failure  │  │   - db.session.add/merge     │
└──────────────┬───────────────────┘  └──────────────┬───────────────┘
               │                                     │
               └─────────────┬───────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────────────┐
│              SQLAlchemy Models (`app/api/model.py`)             │
│  - db = SQLAlchemy(app) bound at import time                   │
│  - User (Flask-Login UserMixin)                                │
│  - Lemma (title, content, comments relationship)               │
│  - Comment (user_name, lemma_id FK, content, time)             │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│              MySQL 5.7 database `baike` (localhost)            │
│  tables: user, lemma, comment                                  │
│  connection: mysql://root:123456@127.0.0.1/baike               │
└────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `run.py` | Entrypoint; creates `app = Flask(__name__)` indirectly via `app/__init__.py`; runs dev server | `D:/work/baike/run.py` |
| `app/__init__.py` | App factory wiring: secret key, SQLALCHEMY_DATABASE_URI, LoginManager, blueprint registration, `/` route, `user_loader` | `D:/work/baike/app/__init__.py` |
| `app.api` Blueprint (`api`) | POST form-submission handlers: regist/login/logout/add/modify; also `reset` for seeding | `D:/work/baike/app/api/__init__.py` |
| `app.api.model` | SQLAlchemy instance + `User`, `Lemma`, `Comment` model classes | `D:/work/baike/app/api/model.py` |
| `app.route.user` Blueprint (`user` variable, name `apple`) | GET page rendering + POST search/detail; redirects back into `api` for mutations | `D:/work/baike/app/route/user.py` |
| `app/templates/*.html` | Jinja2 templates (home, signin, register, add, modify, result, detail); embed forms posting to `/api/*` and `/user/*` | `D:/work/baike/app/templates/` |
| `app/static/stylesheets/` | Bootstrap CSS + custom `mycss/*.css` per page + wangEditor CSS | `D:/work/baike/app/static/stylesheets/` |
| `app/static/javascripts/` | jQuery, Bootstrap JS, wangEditor JS used inline by templates | `D:/work/baike/app/static/javascripts/` |
| `config.ini` | uWSGI deployment config (process/threads, socket, chdir) | `D:/work/baike/config.ini` |
| `baike.sql` | Reference MySQL schema dump (user, lemma, comment) | `D:/work/baike/baike.sql` |

## Pattern Overview

**Overall:** Modular Flask Blueprint split (page-rendering vs. mutation), with an Eager-Initialization App Singleton and an SQLAlchemy bound at module import time. Two-layer separation: `route/` returns rendered pages and search results, `api/` accepts form submissions and mutates state.

**Key Characteristics:**
- Two Blueprints with disjoint URL prefixes: `user` (mounted at `/user`) and `api` (mounted at `/api`).
- The `user` Blueprint Python variable is named `user` but its registered Blueprint NAME is `'apple'`; this name is what `url_for('apple.<endpoint>')` uses throughout the codebase (see `app/api/__init__.py:26,29,38,40,46,60,63`).
- `db = SQLAlchemy(app)` is created inside `app/api/model.py` and re-bound with `db.init_app(app)` in `app/__init__.py`.
- No service layer; controllers (view functions) talk directly to SQLAlchemy models and `db.session`.
- Page templates POST form actions to `/api/*` for mutations (login, regist, add, modify) and to `/user/*` for read flows (search, detail). This means mutations bypass the `user` blueprint entirely.
- Authentication is cookie/session-based via Flask-Login (`login_user` / `logout_user`); `login_required` guards `add`, `modify`, and `logout`.

## Layers

**Page-Rendering Layer (`app/route/user.py`):**
- Purpose: Render Jinja2 templates and respond to search/detail POSTs.
- Location: `D:/work/baike/app/route/user.py`
- Contains: Flask view functions bound to `user` blueprint (named `apple`); direct `Lemma.query` usage; `flash` + `redirect` on failure.
- Depends on: `app.api.model` (User, Lemma, Comment, db), Flask-Login `login_required`/`current_user`.
- Used by: Templates linking to `/user/home`, `/user/login`, `/user/regist`, `/user/add`, `/user/modify`, `/user/search`, `/user/detail`.

**Mutation/API Layer (`app/api/__init__.py`):**
- Purpose: Accept form submissions, mutate DB, redirect to a page route on success/failure.
- Location: `D:/work/baike/app/api/__init__.py`
- Contains: `registBusiness`, `loginBusiness`, `logout`, `add`, `modify`, `reset` view functions bound to `api` blueprint.
- Depends on: `app.api.model` (User, Lemma, Comment, db), Flask-Login `login_user`/`logout_user`/`login_required`.
- Used by: Templates posting forms with `action="/api/regist"`, `/api/login`, `/api/logout`, `/api/add`, `/api/modify`. Note: `modify.html` and `detail.html` still POST to `/api/modify` even though `/user/modify` exists.

**Model Layer (`app/api/model.py`):**
- Purpose: SQLAlchemy ORM models + a singleton `db` instance bound to a throwaway `Flask(__name__)` inside this module.
- Location: `D:/work/baike/app/api/model.py`
- Contains: `db = SQLAlchemy(app)` (where `app` is a local Flask created in the module), `User`, `Lemma`, `Comment` classes.
- Depends on: `flask_sqlalchemy`, `flask_login.UserMixin`.
- Used by: `app/__init__.py` (imports `db, User` and calls `db.init_app(app)`), and view functions in both blueprints.

**Template Layer (`app/templates/*.html`):**
- Purpose: Server-rendered HTML with Bootstrap + wangEditor + jQuery; forms wire to `/user/*` and `/api/*` URLs.
- Location: `D:/work/baike/app/templates/`
- Contains: `home.html`, `signin.html`, `register.html`, `add.html`, `modify.html`, `result.html`, `detail.html` (plus `detail示例.html` which is a reference/sample and not referenced by any route).
- Depends on: `current_user` (Flask-Login proxy) for nav state; flashed messages from `flash()` calls in `user.py` and `api/__init__.py`.

**Static Asset Layer (`app/static/`):**
- Purpose: Frontend libraries and page-specific CSS.
- Location: `D:/work/baike/app/static/`
- Contains: `stylesheets/` (Bootstrap, `mycss/*.css` per page, wangEditor CSS, `fonts/`), `javascripts/` (jQuery, Bootstrap, wangEditor, plus unused `wangEditor/lib/jquery-1.10.2.min.js` and `jquery-2.2.1.js`).

## Data Flow

### Primary Request Path - Search & View Lemma

1. Browser GETs `/` -> `home()` view in `app/__init__.py:24-26` -> renders `home.html` (search form posts to `/user/search`).
2. User submits search -> POST `/user/search` -> `search()` view in `app/route/user.py:29-37` -> reads `searchtext` form field -> `Lemma.query.filter(Lemma.title.like("%"+searchtext+"%")).all()`.
3. If results: render `result.html` with `results` list. Each result is a form that POSTs to `/user/detail` with hidden input `linklist=result.title`.
4. User clicks a result title -> POST `/user/detail` -> `detail()` view in `app/route/user.py:39-43` -> reads `linklist` -> `Lemma.query.filter_by(title=entirelytitle)` (NOTE: returns a Query, not a list, passed to template as `fullcontent`) -> renders `detail.html`.

### Primary Request Path - Add Lemma

1. Logged-in user GETs `/user/add` -> `add()` view in `app/route/user.py:24-27` (login_required) -> renders `add.html`.
2. `add.html` form `action="/api/add"` POSTs `title` and `content` (content is the wangEditor HTML body).
3. POST `/api/add` -> `add()` view in `app/api/__init__.py:48-63` (login_required) -> checks for duplicate `title` -> creates `Lemma(title, content)` -> `db.session.add` + `commit` -> `flash('添加成功！')` -> redirect to `url_for('apple.home')` -> `/user/home`.
4. On duplicate: `flash('添加失败！该词条已存在！')` -> redirect to `url_for('apple.add')` -> `/user/add`.

### Primary Request Path - Modify Lemma

1. User in `detail.html` clicks `#modify` button -> JS enables wangEditor, shows confirm/cancel.
2. User submits -> form POSTs to `/api/modify` with `newTitle` and `newContent`.
3. POST `/api/modify` -> `modify()` view in `app/api/__init__.py:65-73` (login_required) -> constructs `Lemma(title=newTitle, content=newContent)` -> `db.session.merge(lemma)` -> `commit` -> `flash('修改成功！')`.
4. BUG: The view function never returns an HTTP response on success; Flask will raise `TypeError`. The form action also submits from `detail.html`, but the template uses `newContent` for BOTH `newTitle` and `newContent` (single field) - see `app/templates/detail.html:50` and `app/api/__init__.py:68-69`. The standalone `/user/modify` route renders `modify.html`, which is a separate flow that POSTs nowhere useful.

### Primary Request Path - Authentication

- Register: GET `/user/regist` -> `register.html` -> POST `/api/regist` -> `registBusiness()` in `app/api/__init__.py:15-29` -> on success `login_user` + redirect to `apple.home`; on existing username flash + redirect to `apple.regist`.
- Login: GET `/user/login` -> `signin.html` -> POST `/api/login` -> `loginBusiness()` in `app/api/__init__.py:31-40` -> success: `login_user` + redirect to `apple.home`; failure: flash + redirect to `apple.login`.
- Logout: GET `/api/logout` -> `logout()` in `app/api/__init__.py:42-46` (login_required) -> `logout_user` + redirect to `apple.home`.

### Primary Request Path - Reset (Seeding)

- GET `/api/reset` -> `reset()` in `app/api/__init__.py:87-100` -> `db.drop_all()` + `db.create_all()` -> seeds one `User('a','a')` and several `Lemma` rows with hardcoded HTML content -> `jsonify(error=False)`. This is the bootstrap endpoint documented in `README.md`.

**State Management:**
- Server-side session via Flask session cookie (`app.secret_key` set in `app/__init__.py:10`).
- User identity persisted via Flask-Login (cookie + `user_loader` callback in `app/__init__.py:20-22` which re-queries `User.query.get(int(id))`).
- Flash messages used for cross-redirect messaging (errors and success notices).
- No client-side state beyond the standard form inputs; wangEditor state lives in the DOM only.

## Key Abstractions

**Blueprint (Flask):**
- Purpose: Modular grouping of routes; each blueprint has its own URL prefix and name.
- Examples:
  - `api` blueprint at `app/api/__init__.py:10-13` (name=`api`, prefix=`/api` from registration in `app/__init__.py:18`).
  - `user` blueprint at `app/route/user.py:7-10` (Python variable=`user`, registered name=`apple`, prefix=`/user` from registration in `app/__init__.py:17`).
- Pattern: Use `url_for('apple.<endpoint>')` to refer to routes in the `user` blueprint (see `app/api/__init__.py` redirects and `app/route/user.py:37`).

**SQLAlchemy Model:**
- Purpose: ORM entity mapped to a MySQL table.
- Examples: `User`, `Lemma`, `Comment` in `app/api/model.py:16-63`.
- Pattern: Each model declares columns, a `__init__` accepting keyword args, and a `__str__` for debugging. Note: typo `__tablenanme__` instead of `__tablename__` on all three classes (declared attribute is ignored; SQLAlchemy falls back to default class-name-to-table mapping).

**Flask-Login UserMixin:**
- Purpose: Adds `is_authenticated`, `is_active`, `is_anonymous`, `get_id()` to a `User` so `login_user` / `current_user` work.
- Examples: `User(db.Model, UserMixin)` in `app/api/model.py:16`.

## Entry Points

**`run.py`:**
- Location: `D:/work/baike/run.py`
- Triggers: `python run.py` for development; `uwsgi` reads `config.ini` and invokes `run:app` for production.
- Responsibilities: Imports the `app` singleton from `app/__init__.py` and calls `app.run(debug=True, host='0.0.0.0')`.

**`/` top-level route:**
- Location: `D:/work/baike/app/__init__.py:24-26`
- Triggers: Browser GET to `/`.
- Responsibilities: Renders `home.html` (search entry point).

**`/api/reset`:**
- Location: `D:/work/baike/app/api/__init__.py:87-100`
- Triggers: One-shot bootstrap call from `README.md`.
- Responsibilities: Drops and recreates schema, seeds users and lemmas.

## Architectural Constraints

- **Threading / Process model:** `config.ini` sets `processes=1, threads=1` under uWSGI. Single-process, single-thread worker. MySQL is the only external dependency and is on `127.0.0.1`.
- **Global state:** Two singletons at module level: `app` (Flask instance created at import time in `app/__init__.py`) and `db` (SQLAlchemy instance bound to a throwaway Flask instance at import time in `app/api/model.py`, then `init_app`'d on the real `app`). Import order matters: `app/api/model.py` must be importable before `app/__init__.py` finishes wiring.
- **Circular imports / fragile wiring:** `app/api/model.py` constructs a *second* `Flask(__name__)` solely to bind `SQLAlchemy(app)`. This works but is wasteful and confusing; the real `app` is then `init_app`'d. The throwaway `app` is not used elsewhere.
- **Python 2 compatibility shim:** `app/api/__init__.py:2-4` and similar files execute `reload(sys); sys.setdefaultencoding('utf8')`. This is a Python 2 idiom; under Python 3 `reload` is no longer a builtin and the module will crash at import. `requirements.txt` pins `mysql-python` (Python 2 only), confirming the project targets Python 2.
- **Blueprint name vs. variable:** The `user` Python variable in `app/route/user.py` is registered as Blueprint name `'apple'`. All `url_for` calls use `'apple.<endpoint>'`. Do not confuse the Python name with the registered name when adding routes.
- **Form action vs. URL prefix:** Templates hard-code `/api/...` and `/user/...` paths instead of using `url_for`. Changing a blueprint's URL prefix will break templates silently.

## Anti-Patterns

### Blueprint name does not match its variable

**What happens:** In `app/route/user.py:7-10`, `Blueprint('apple', __name__)` is assigned to a variable called `user`. `app/__init__.py:17` registers this variable under `url_prefix='/user'`. Every `url_for` call elsewhere uses `'apple.<endpoint>'`.
**Why it's wrong here:** Code review and search for `url_for('user.')` yields zero hits and can mislead new contributors; the discrepancy between file path (`route/user.py`), Python variable (`user`), URL prefix (`/user`), and Blueprint name (`apple`) makes intent unclear.
**Do this instead:** Either rename the Blueprint to `'user'` for consistency, or rename the file/variable to `apple` so all three identifiers agree. The codebase consistently chooses the Blueprint name `apple`, so renaming the file and variable is the smaller-blast-radius fix.

### Model-level SQLAlchemy bound to throwaway Flask app

**What happens:** `app/api/model.py:8-11` creates `app = Flask(__name__)` and `db = SQLAlchemy(app)`, then `app/__init__.py:12` runs `db.init_app(app)` on the *real* app.
**Why it's wrong here:** Two Flask instances exist at runtime; the one in `model.py` is dead weight. Also couples model imports to a Flask context being available.
**Do this instead:** `db = SQLAlchemy()` with no Flask arg, then `db.init_app(app)` once in `app/__init__.py` (the pattern is already partially scaffolded in `model.py:14` with the commented `# db = SQLAlchemy()`).

### Mutations bypass the route blueprint

**What happens:** `app/api/__init__.py` defines `add`, `modify`, `logout` view functions that are not page renderers. Templates post forms to `/api/...` instead of `/user/...`.
**Why it's wrong here:** The `user` blueprint is supposed to be the page layer, but mutations live in `api`. Conceptually conflates "API" with "form handler." There's no JSON API contract; everything is form-encoded redirects.
**Do this instead:** Pick one of two patterns: (a) keep blueprints purely as REST/JSON endpoints and serve pages from a single renderer module; or (b) move form POST handlers into `app/route/user.py` so all user-facing flows live together and reserve `api/` for true JSON endpoints.

### Hardcoded URLs in templates

**What happens:** `home.html`, `signin.html`, `register.html`, `add.html`, `modify.html`, `result.html`, `detail.html` all reference `/user/login`, `/api/login`, `/api/add`, `/api/modify`, `/api/logout`, `/user/add`, `/user/search`, `/user/detail` directly.
**Why it's wrong here:** Changing a blueprint's `url_prefix` or route path requires editing every template. There is no `url_for` usage in any template.
**Do this instead:** Replace literal paths with `{{ url_for('apple.login') }}`, `{{ url_for('api.add') }}`, etc. This will also surface Blueprint name mismatches at template render time.

### Python 2 reload/sys encoding shim in Python 3 context

**What happens:** `app/api/__init__.py:2-4` and `app/route/user.py` (similar shim) call `reload(sys); sys.setdefaultencoding('utf8')`.
**Why it's wrong here:** `reload` is not a builtin in Python 3; this raises `NameError`. `requirements.txt` still pins `mysql-python`, a Python-2-only package.
**Do this instead:** Drop the shim; Python 3 is UTF-8 by default. Replace `mysql-python` with `mysqlclient` or `PyMySQL` and add the file encoding line at top of files if needed.

### `detail.html` iterates a `Query` not a list

**What happens:** `app/route/user.py:42` returns `Lemma.query.filter_by(title = entirelytitle)` (a SQLAlchemy `Query`) and passes it as `fullcontent`. `detail.html` does `{% for fullcon in fullcontent %}`.
**Why it's wrong here:** A `Query` is iterable but iteration inside a template works only once and not after the session ends. Also, no `.first()` / `.all()` call means the template always expects 0-or-1 row but actually receives a query that may return zero rows silently.
**Do this instead:** `.first()` or `.all()` explicitly in the view, with a fallback when the title does not exist.

### `modify()` view returns no response

**What happens:** `app/api/__init__.py:65-73` ends after `flash('修改成功！')` with no `return`.
**Why it's wrong here:** Flask view functions must return a response; missing return raises `TypeError: 'NoneType' object is not callable` or 500 Internal Server Error.
**Do this instead:** Add `return redirect(url_for('apple.home'))` (or to the detail page for that lemma).

## Error Handling

**Strategy:** Use `flash()` to push a user-facing message and `redirect(url_for('apple.<page>'))` to bounce the user back to a page where the message is rendered.

**Patterns:**
- Duplicate username on `/api/regist` -> flash + redirect to register page (`app/api/__init__.py:28-29`).
- Wrong credentials on `/api/login` -> flash + redirect to login page (`app/api/__init__.py:39-40`).
- Empty search results on `/user/search` -> flash + redirect to home (`app/route/user.py:36-37`).
- Duplicate lemma title on `/api/add` -> flash + redirect to add page (`app/api/__init__.py:62-63`).
- No exception handling around `db.session.add/commit` or `db.session.merge/commit`; failures bubble up as 500s.
- No input validation beyond `required` HTML attribute; `confirm_password` in `register.html` is checked client-side only and never sent to the server.

## Cross-Cutting Concerns

**Logging:** No logging framework configured. Flask's default request log goes to stderr in dev mode (`app.run(debug=True)`).
**Validation:** HTML5 `required` attribute on inputs (`app/templates/*.html`); no server-side schema validation.
**Authentication:** Flask-Login with cookie session. `@login_required` decorators on `/api/logout`, `/api/add`, `/api/modify`, `/user/add`, `/user/modify`. LoginManager's `login_view = '.login'` (relative to a blueprint, which is fragile - likely intended `login` endpoint on the `apple` blueprint).
**Authorization:** None beyond authentication. Any logged-in user can modify any lemma (the modify handler ignores who created the row).
**CSRF:** None. Form submissions rely solely on session cookies; no CSRF token middleware.
**Internationalization:** Hardcoded Chinese strings in templates and flash messages; no i18n framework.

---

*Architecture analysis: 2026-06-11*