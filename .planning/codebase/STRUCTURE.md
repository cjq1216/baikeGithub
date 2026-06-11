# Codebase Structure

**Analysis Date:** 2026-06-11

## Directory Layout

```
D:/work/baike/                          # Project root
├── run.py                              # Dev-server entrypoint; imports `app`
├── config.ini                          # uWSGI deployment config (socket, chdir, callable=app)
├── requirements.txt                    # Pinned deps: flask, flask_login, flask_SQLAlchemy, mysql-python
├── baike.sql                           # Reference MySQL schema dump (user, lemma, comment)
├── README.md                           # Manual setup + /api/reset bootstrap instructions
├── CLAUDE.md                           # Local AI assistant guidance
├── .gitignore                          # Standard Python ignores
├── .venv/                              # Virtualenv (uncommitted)
├── .idea/                              # JetBrains IDE metadata (uncommitted)
├── .claude/                            # Claude assistant local config (uncommitted)
├── .planning/                          # GSD planning outputs (codebase maps)
│   └── codebase/                       # This directory holds ARCHITECTURE.md, STRUCTURE.md, etc.
└── app/                                # Flask application package
    ├── __init__.py                     # App singleton wiring: secret_key, DB URI, LoginManager, blueprint registration, `/` route
    ├── api/                            # Mutation/form-submission layer
    │   ├── __init__.py                 # `api` blueprint (name='api', no url_prefix here; /api is set at registration)
    │   └── model.py                    # SQLAlchemy singleton `db` + User/Lemma/Comment models
    ├── route/                          # Page-rendering layer
    │   ├── __init__.py                 # Empty package marker (file is 0 bytes)
    │   └── user.py                     # `user` Blueprint (registered name='apple'); GET pages + POST search/detail
    ├── templates/                      # Jinja2 templates (server-rendered)
    │   ├── home.html                   # Search entry; GET `/` and `/user/home` both render this
    │   ├── signin.html                 # Login form (posts to /api/login)
    │   ├── register.html               # Register form (posts to /api/regist)
    │   ├── add.html                    # Add lemma (posts to /api/add); uses wangEditor for content
    │   ├── modify.html                 # Standalone modify page (renders /user/modify); not wired to a real POST handler
    │   ├── result.html                 # Search results; each result is a form posting to /user/detail
    │   ├── detail.html                 # Lemma detail page (renders fullcontent + comment loop); uses wangEditor
    │   └── detail示例.html             # Reference/sample file; not referenced by any view
    └── static/                         # Frontend assets served by Flask's static handler
        ├── javascripts/                # jQuery, Bootstrap JS, wangEditor JS
        │   ├── jquery-1.11.3.min.js    # Used by templates
        │   ├── bootstrap.min.js        # Used by templates
        │   ├── docs.min.js             # Used by templates
        │   ├── bootstrap.js            # Unminified source (unused at runtime)
        │   ├── npm.js                  # npm metadata (unused at runtime)
        │   └── wangEditor/             # wangEditor rich-text editor
        │       ├── wangEditor.js       # Full source (unused at runtime)
        │       ├── wangEditor.min.js   # Used by add.html and detail.html
        │       └── lib/                # Bundled jQuery versions inside wangEditor (likely unused)
        │           ├── jquery-1.10.2.min.js
        │           └── jquery-2.2.1.js
        └── stylesheets/                # CSS
            ├── bootstrap.css           # Unminified (unused at runtime)
            ├── bootstrap.css.map
            ├── bootstrap.min.css       # Used by every template
            ├── bootstrap-theme.css     # Unused
            ├── bootstrap-theme.css.map
            ├── bootstrap-theme.min.css # Unused
            ├── style.css               # Tiny placeholder; loaded by signin/register
            ├── fonts/                  # Bootstrap icon font files
            ├── mycss/                  # Custom per-page stylesheets
            │   ├── cover.css           # Used by home.html
            │   ├── signin.css          # Used by signin.html + register.html
            │   ├── result.css          # Used by result.html
            │   ├── detail.css          # Used by detail.html
            │   ├── modify.css          # Used by add.html and modify.html
            │   └── blog.css            # Unused
            └── wangEditor/             # Editor CSS
                ├── wangEditor.min.css  # Used by add.html, detail.html, modify.html
                ├── wangEditor.css      # Unminified (unused)
                └── wangEditor.less     # LESS source (unused at runtime)
```

## Directory Purposes

**`app/`:**
- Purpose: Flask application package. Contains the app singleton (`__init__.py`), the `api` and `route` subpackages, Jinja2 templates, and static assets.
- Contains: Python source, HTML templates, CSS, JS, fonts.
- Key files: `D:/work/baike/app/__init__.py` (app wiring), `D:/work/baike/app/api/__init__.py` (mutation handlers), `D:/work/baike/app/route/user.py` (page rendering), `D:/work/baike/app/api/model.py` (ORM).

**`app/api/`:**
- Purpose: Form-submission / mutation layer. Imports models and exposes the `api` Blueprint.
- Contains: One Blueprint with view functions for login/logout/regist/add/modify/reset.
- Key files: `D:/work/baike/app/api/__init__.py`, `D:/work/baike/app/api/model.py`.

**`app/route/`:**
- Purpose: Page-rendering layer. Currently contains a single Blueprint in `user.py`.
- Contains: One Blueprint (`user`, registered name `apple`) with GET endpoints for page rendering and POST endpoints for search/detail.
- Key files: `D:/work/baike/app/route/user.py` (only source file).

**`app/templates/`:**
- Purpose: Jinja2 templates rendered by Flask via `render_template(...)`.
- Contains: One HTML file per page (`home.html`, `signin.html`, `register.html`, `add.html`, `modify.html`, `result.html`, `detail.html`) plus an unused sample (`detail示例.html`).
- Key files: All `*.html` in `D:/work/baike/app/templates/`.

**`app/static/`:**
- Purpose: Static assets served by Flask at `/static/...`.
- Contains: Bootstrap CSS/JS, jQuery, wangEditor, custom per-page CSS, fonts.
- Key files: `D:/work/baike/app/static/stylesheets/bootstrap.min.css`, `D:/work/baike/app/static/javascripts/wangEditor/wangEditor.min.js`, `D:/work/baike/app/static/stylesheets/wangEditor/wangEditor.min.css`, `D:/work/baike/app/static/stylesheets/mycss/*.css`.

**`app/__pycache__/`, `app/api/__pycache__/`, `app/route/__pycache__/`:**
- Purpose: Python bytecode caches.
- Generated: Yes (Python interpreter).
- Committed: Should NOT be (currently shown in `git status` as untracked, suggesting they slipped past `.gitignore`).

## Key File Locations

**Entry Points:**
- `D:/work/baike/run.py`: Development server entrypoint (`python run.py` -> `app.run(debug=True, host='0.0.0.0')`).
- `D:/work/baike/config.ini`: uWSGI deployment config; `wsgi-file = run.py`, `callable = app`.

**Configuration:**
- `D:/work/baike/config.ini`: Production deployment config (uWSGI socket, chdir, processes/threads).
- `D:/work/baike/requirements.txt`: Pinned Python dependencies.
- `D:/work/baike/baike.sql`: Reference DDL for the MySQL `baike` database.
- `D:/work/baike/app/__init__.py:10-11`: Hardcoded `app.secret_key` and `SQLALCHEMY_DATABASE_URI` (NO env-var indirection).
- `D:/work/baike/app/api/model.py:10`: Duplicate hardcoded MySQL URI (the throwaway `app`'s config).

**Core Logic:**
- `D:/work/baike/app/__init__.py`: App singleton + LoginManager + blueprint registration.
- `D:/work/baike/app/api/__init__.py`: Mutation handlers (regist, login, logout, add, modify, reset).
- `D:/work/baike/app/api/model.py`: SQLAlchemy models.
- `D:/work/baike/app/route/user.py`: Page rendering + search/detail.

**Templates (rendered by view functions):**
- `D:/work/baike/app/templates/home.html`: home page (`/` and `/user/home`).
- `D:/work/baike/app/templates/signin.html`: login page (`/user/login`).
- `D:/work/baike/app/templates/register.html`: register page (`/user/regist`).
- `D:/work/baike/app/templates/add.html`: add lemma page (`/user/add`).
- `D:/work/baike/app/templates/modify.html`: modify lemma page (`/user/modify`).
- `D:/work/baike/app/templates/result.html`: search results (`/user/search`).
- `D:/work/baike/app/templates/detail.html`: lemma detail (`/user/detail`).

**Static Assets (referenced by templates):**
- `D:/work/baike/app/static/stylesheets/bootstrap.min.css`: All pages.
- `D:/work/baike/app/static/javascripts/jquery-1.11.3.min.js`: All pages.
- `D:/work/baike/app/static/javascripts/bootstrap.min.js`: All pages.
- `D:/work/baike/app/static/javascripts/docs.min.js`: All pages.
- `D:/work/baike/app/static/stylesheets/mycss/{cover,signin,result,detail,modify}.css`: One per page.
- `D:/work/baike/app/static/javascripts/wangEditor/wangEditor.min.js`: `add.html`, `detail.html`, `modify.html`.
- `D:/work/baike/app/static/stylesheets/wangEditor/wangEditor.min.css`: `add.html`, `detail.html`, `modify.html`.

**Database:**
- `D:/work/baike/baike.sql`: Schema dump (tables: `user`, `lemma`, `comment`).
- Schema is created by `db.create_all()` called from `/api/reset` (see `app/api/__init__.py:90`).

**Testing:**
- None detected. There is no `tests/`, `test_*.py`, or `pytest.ini`/`tox.ini`/`conftest.py` anywhere in the repo.

## Naming Conventions

**Files:**
- Python modules: lowercase, snake_case or single-word (`user.py`, `model.py`, `__init__.py`).
- HTML templates: single lowercase word or hyphen-less (`home.html`, `signin.html`, `register.html`, `add.html`, `modify.html`, `result.html`, `detail.html`); one sample uses Chinese filename (`detail示例.html`).
- CSS in `mycss/`: matches the template it styles (`cover.css` -> `home.html`, `signin.css` -> `signin.html`, `result.css` -> `result.html`, `detail.css` -> `detail.html`, `modify.css` -> `add.html` and `modify.html`).
- Vendor assets keep upstream names (`bootstrap.min.css`, `jquery-1.11.3.min.js`, `wangEditor.min.js`).

**Directories:**
- Lowercase single words: `app`, `api`, `route`, `templates`, `static`, `javascripts`, `stylesheets`, `mycss`, `fonts`, `lib`.
- No nesting beyond `app/`.

**Python identifiers:**
- Blueprints: snake_case Python variable (`api`, `user`) but the `user` Blueprint registers the name `apple`.
- View functions: short verbs or nouns (`home`, `login`, `regist`, `add`, `search`, `detail`, `modify`, `logout`, `reset`, `registBusiness`, `loginBusiness`).
- Models: PascalCase (`User`, `Lemma`, `Comment`); SQLAlchemy `__tablename__` would be lowercase plural-like (`user`, `lemma`, `comment`), but the typo `__tablenanme__` means SQLAlchemy falls back to the class name.

**Routes (URL paths):**
- Lowercase verbs/nouns under `/user/*` (`/user/home`, `/user/login`, `/user/regist`, `/user/add`, `/user/search`, `/user/detail`, `/user/modify`).
- Lowercase verbs/nouns under `/api/*` (`/api/regist`, `/api/login`, `/api/logout`, `/api/add`, `/api/modify`, `/api/reset`).

## Where to Add New Code

**New page (read flow):**
- Add view function to `D:/work/baike/app/route/user.py` (Blueprint name `apple`, prefix `/user`).
- Create template at `D:/work/baike/app/templates/<page>.html`.
- Add per-page CSS at `D:/work/baike/app/static/stylesheets/mycss/<page>.css` if needed.
- Register the route under `@user.route('/<page>')`.
- Reference from other templates using `{{ url_for('apple.<endpoint>') }}` (the codebase currently hardcodes paths; prefer `url_for` for new code).

**New mutation / form handler:**
- Add view function to `D:/work/baike/app/api/__init__.py` (Blueprint name `api`, prefix `/api`).
- Decorate with `@login_required` if anonymous users must not access it.
- Mutate via `db.session.add(...)` / `db.session.merge(...)` and `db.session.commit()`.
- On success: `flash('<message>')` + `return redirect(url_for('apple.<page>'))`.
- On failure: `flash('<error>')` + `return redirect(url_for('apple.<form-page>'))`.
- From templates, POST to `/api/<endpoint>` (or `{{ url_for('api.<endpoint>') }}`).

**New model:**
- Add class to `D:/work/baike/app/api/model.py` inheriting `db.Model`. Include `__tablename__` (correctly spelled, unlike the existing typo) and a primary-key `id`.
- Import the new model in any view file that uses it.
- For dev: hit `GET /api/reset` to drop and recreate (this also re-seeds, so back up data first). For prod: write a migration script (no migration framework is currently in use).

**New shared utility / helper:**
- This project has no `app/utils/` directory. Add new helpers either as a new `app/utils.py` module, or as private functions at the top of the file where they are used. There is no `services/` or `lib/` layer.

**New static asset:**
- CSS: place under `D:/work/baike/app/static/stylesheets/` (vendor) or `D:/work/baike/app/static/stylesheets/mycss/` (custom).
- JS: place under `D:/work/baike/app/static/javascripts/` or a subdirectory like `wangEditor/`.
- Reference from templates with relative path `../static/<subdir>/<file>`.

**Configuration / secret change:**
- `app.secret_key`: `D:/work/baike/app/__init__.py:10`.
- `SQLALCHEMY_DATABASE_URI`: `D:/work/baike/app/__init__.py:11` (and duplicate at `D:/work/baike/app/api/model.py:10`).
- uWSGI deployment: `D:/work/baike/config.ini`.
- There is no `.env` file or environment-variable indirection.

## Special Directories

**`app/__pycache__/`, `app/api/__pycache__/`, `app/route/__pycache__/`:**
- Purpose: Python bytecode caches.
- Generated: Yes (Python).
- Committed: No (currently shown as untracked in `git status`).

**`.venv/`:**
- Purpose: Local Python virtualenv.
- Generated: Yes (`python -m venv .venv`).
- Committed: No.

**`.idea/`:**
- Purpose: JetBrains IDE workspace settings.
- Generated: Yes (PyCharm/IntelliJ).
- Committed: No.

**`.claude/`:**
- Purpose: Claude Code assistant local state (skills, hooks, session data).
- Generated: Yes.
- Committed: No.

**`.planning/`:**
- Purpose: GSD (Get-Shit-Done) planning artifacts.
- Contains: `codebase/` for codebase maps, plus phase plans and roadmap files created during planning.
- Generated: Yes (by GSD workflow).
- Committed: Varies; current `.gitignore` does not exclude it.

---

*Structure analysis: 2026-06-11*