# Codebase Concerns

**Analysis Date:** 2026-06-11

## Tech Debt

**`/api/modify` route has missing `return` and silently fails:**
- Issue: After `flash('修改成功！')` there is no `return redirect(...)`. Function falls off the end and Flask returns a 500 (NoneType has no __html__) or blank 200 with no body. Bug is real and visible.
- Files: `app/api/__init__.py:65-73`
- Impact: Editing a lemma from `detail.html` always errors out. `/api/modify` is the only path to edit existing entries; users can never modify content.
- Fix approach: Add `return redirect(url_for('apple.home'))` (or detail page) after the flash. While there, also remove the duplicate `newTitle = request.form.get('newContent')` line — both variables are assigned from the same field, so the form field intended for the title is never read.

**`/user/detail` returns `BaseQuery` instead of a Lemma / list:**
- Issue: `Lemma.query.filter_by(...)` is called but `.first()`/`.all()` is missing. The query object is passed as `fullcontent` to `detail.html`, which iterates with `{% for fullcon in fullcontent %}`. Iteration works on a query but every access lazily re-executes a SQL query per attribute, and `None` (no match) crashes the template.
- Files: `app/route/user.py:42`; consumer: `app/templates/detail.html:51-91`
- Impact: Detail page is fragile (N+1-style lazy queries in template), breaks when no result exists, and semantically wrong.
- Fix approach: `fullcontent = Lemma.query.filter_by(title=entirelytitle).all()` and guard with `if not fullcontent: flash(...); return redirect(url_for('apple.home'))`.

**`__tablenanme__` typo on every model (3 occurrences):**
- Issue: SQLAlchemy attribute is `__tablename__`, but here it's spelled `__tablenanme__`. Flask-SQLAlchemy then auto-generates the table name from the class name (`user`, `lemma`, `comment`), which luckily matches the SQL in `baike.sql`. The typo silently means the explicit `= 'user'` etc. assignments are dead code.
- Files: `app/api/model.py:18, 32, 47`
- Impact: Confusing for maintainers; if anyone renames a class, the schema silently drifts from what `baike.sql` declares.
- Fix approach: Rename `__tablenanme__` to `__tablename__` on all three classes.

**Duplicate Flask app instance (`app/api/model.py`):**
- Issue: `app/api/model.py:9` creates `app = Flask(__name__)` purely to instantiate `db = SQLAlchemy(app)`. `app/__init__.py:9` then does the same and calls `db.init_app(app)`. Two Flask app objects exist; `app/api/model.py`'s app is imported by `run.py:2` (`from app import app`), which shadows the canonical one in some import orders.
- Files: `app/api/model.py:6-11`, `app/__init__.py:9-12`, `run.py:2`
- Impact: Import-order dependent behavior; the DB URI is set on both apps. `run.py` correctly imports `from app import app` (the package), but anyone importing `from app.api.model import app` would get a different instance.
- Fix approach: In `app/api/model.py` replace the eager `app = Flask(...)` / `SQLAlchemy(app)` with the deferred pattern (uncomment line 14, delete lines 9–11). Then `db.init_app(app)` in `app/__init__.py` is the only initialization.

**`Comment` model defined but unreachable from any route/UI:**
- Issue: `app/api/__init__.py:76-85` defines a `/commen` route that is commented out. `app/templates/detail.html:104` posts to `/api/commen`, but no handler exists. The `Comment` model has no read-side either (`comments` relationship is `lazy='dynamic'` but no template renders them from a query — `detail.html:77-91` loops `comments` which is never passed in).
- Files: `app/api/__init__.py:76-85`, `app/api/model.py:45-63`, `app/templates/detail.html:77`, `app/templates/detail.html:104`
- Impact: "发布评论" button in `detail.html` is wired to a dead endpoint (404). Comment UI shows nothing because the route never sets `comments`.
- Fix approach: Uncomment and complete the `/commen` route, pass `comments=Lemma.query.get(...).comments` to `detail.html`.

**`/api/reset` endpoint is exposed without auth and drops the database:**
- Issue: `app/api/__init__.py:87-100` defines `reset()` which calls `db.drop_all()`, recreates schema, and seeds data. It is not behind `@login_required` and has no CSRF. It is intended for first-run setup (README points users to it), but the same code will wipe production if hit.
- Files: `app/api/__init__.py:87-100`, `README.md:19`
- Impact: Anyone who can reach the server can delete all data.
- Fix approach: Guard with `if not app.debug: abort(404)` or remove from the URL map and use a CLI command (`flask init-db`) instead.

**Hardcoded MySQL credentials (DB user `root`, password `123456`):**
- Issue: Connection string embedded in source. Same string in two places; updating one and forgetting the other breaks the app.
- Files: `app/__init__.py:11`, `app/api/model.py:10`
- Impact: Credential rotation impossible without code change; credential leaked into git history forever; trivially exploitable if the box is internet-reachable.
- Fix approach: Read from `config.ini` (which exists but is only used for uwsgi) or env vars; load via `app.config.from_object('config.DevelopmentConfig')`.

**Hardcoded Flask `secret_key`:**
- Issue: `app.secret_key = '1frMFuWRVPV1'` is committed to source. Any attacker who reads the repo can forge session cookies (including the Flask-Login session).
- Files: `app/__init__.py:10`
- Impact: Full session forgery; trivial auth bypass.
- Fix approach: Generate a per-environment key, load from env var, rotate the leaked one.

**Plaintext password storage:**
- Issue: `User(name=name, password=password)` stores the raw form value. `loginBusiness` compares with `User.query.filter_by(name=name, password=password).first()` — exact-match against the column. `db.Column(db.String(40))` is too short for any modern hash.
- Files: `app/api/__init__.py:22, 34-35`, `app/api/model.py:21`
- Impact: DB read = total credential leak. Column length `40` will also truncate any salted hash > 40 chars (sha256 hex = 64).
- Fix approach: Use `werkzeug.security.generate_password_hash` / `check_password_hash`; widen column to `db.String(256)`.

**README port mismatch:**
- Issue: README says `127.0.0.1:2002` (port 2002, from `config.ini`'s uwsgi socket). `run.py` calls `app.run(...)` with no port argument → Flask default `5000`. Following README instructions produces a connection refused.
- Files: `README.md:19,21`, `run.py:5`
- Impact: First-run instructions are wrong.
- Fix approach: Either remove `config.ini`/README uwsgi references, or have `run.py` read `config.ini` and pick port 2002.

**`app.route` overlap: `/` defined in `app/__init__.py:24`, blueprints register under `/user` and `/api`:**
- Issue: Only the root route is in the package `__init__.py`; blueprint routes and `home` are duplicated between the package init and `app/route/user.py:12`. Not strictly wrong, but the split (`home` lives in `user.py`, root `/` lives in `app/__init__.py`) makes URL discovery harder.
- Files: `app/__init__.py:24-26`, `app/route/user.py:12-14`
- Impact: Maintenance confusion; nothing is broken today.
- Fix approach: Move `/` to a blueprint, delete the package-level route.

**Stale "example" template left in repo:**
- Issue: `app/templates/detail示例.html` is a hand-written static sample, not a Jinja template (note `value=` instead of `value=""`, hardcoded H1). It will never render and pollutes the templates directory.
- Files: `app/templates/detail示例.html`
- Impact: Confusion; the actual `detail.html` references `comments` that are never passed.
- Fix approach: Delete it; or wire `detail.html` to populate comments.

## Known Bugs

**Modify endpoint returns no response / 500:**
- Symptoms: Clicking "确认修改" on `detail.html` shows flash but the request errors.
- Files: `app/api/__init__.py:65-73`
- Trigger: Edit any lemma and submit.
- Workaround: None in the UI. Direct DB update.

**Modify ignores the intended title field:**
- Symptoms: `newTitle = request.form.get('newContent')` — the form's hidden `newTitle` input (`detail.html:53`) is read into a variable, but immediately overwritten with `newContent`. The lemma being edited is always matched by content-string-as-title, which can collide.
- Files: `app/api/__init__.py:68-69`, `app/templates/detail.html:53`
- Trigger: Any `/api/modify` call.
- Workaround: Edit DB directly.

**`/user/detail` passes a SQLAlchemy Query object to the template:**
- Symptoms: If title not found, `query.first()` returns `None`, the `{% for %}` loop body never runs (no crash), but `comments` loop also never runs — and no flash is shown, so the user sees an empty detail page.
- Files: `app/route/user.py:42-43`
- Trigger: Search for a title that no longer exists.
- Workaround: Search again with a known title.

**Comment submit is a dead link:**
- Symptoms: Clicking "发布评论" then "发布" hits `/api/commen` → 404.
- Files: `app/templates/detail.html:104-117`
- Trigger: Any comment submission.
- Workaround: None.

**`Comment.__init__` assigns the unbound class to `user_name`:**
- Symptoms: `self.user_name = current_user` stores a `LocalProxy`, not the user's name. `Comment.__str__` calls `self.title` which doesn't exist on the model (line 57 in model.py references `self.title`, but the attribute is `content`). Any code that constructs and stringifies a Comment will AttributeError.
- Files: `app/api/model.py:56-63`
- Trigger: `str(Comment(...))` or `repr` in logs.
- Workaround: Don't construct yet (route is commented out).

**`Comment.time` mix of naive/UTC semantics:**
- Issue: `default=datetime.datetime.utcnow` (no parens — pass the function, not a value, so this is correct), but `__init__` then overwrites with `datetime.datetime.now()` (local). The column then depends on whether the model was created via ORM default or `Comment(...)`.
- Files: `app/api/model.py:54, 63`
- Impact: Inconsistent timestamps across rows.
- Workaround: Pick one timezone strategy.

## Security Considerations

**Plaintext passwords (see Tech Debt):** DB compromise = full credential disclosure. No hashing, no salt, no pepper, no bcrypt/scrypt/argon2.

**Hardcoded `secret_key` (see Tech Debt):** Anyone with the repo can mint valid sessions for any user, including `User.query.get(1)` after a `reset()`.

**Hardcoded DB credentials with `root` / `123456`:** The MySQL user is `root` with a guessable password. Combined with `host='127.0.0.1'` it's not directly internet-exposed, but if the dev box is on any LAN it's trivially exploitable. There is no `.env` and no environment-variable plumbing at all.

**No CSRF protection:**
- All mutating endpoints (`/api/regist`, `/api/login`, `/api/add`, `/api/modify`, `/api/logout`) accept POST/GET without CSRF tokens. Flask-WTF / Flask-SeaSurf is not installed.
- Files: `app/api/__init__.py:15,31,42,48,65`
- Impact: A malicious page on the same origin can fire requests; combined with the leaked `secret_key` and a logged-in session cookie, a CSRF on `/api/modify` could rewrite a lemma using the victim's identity.

**No rate limiting / brute-force protection on `/api/login`:**
- No `flask-limiter` or equivalent. `User.query.filter_by(name=name, password=password)` is a simple equality check, so attackers can iterate names and try a wordlist.
- Files: `app/api/__init__.py:31-40`

**No input sanitization on `searchtext`:**
- `Lemma.query.filter(Lemma.title.like("%"+searchtext+"%"))` builds the LIKE pattern by string concatenation. SQLAlchemy parameterizes the user value (so SQLi is blocked), but a wildcard like `%` or `_` lets users enumerate or scan the table. Also, the value flows into `flash()` without escaping — Jinja autoescape handles HTML, but XSS via crafted titles is still possible because `result.title` in `result.html:55` is rendered inside an `input value=` attribute without quotes (`value= {{ result.title }}`), breaking out of the attribute is straightforward.
- Files: `app/route/user.py:31-32`, `app/templates/result.html:55`, `app/templates/detail.html:53`

**Stored XSS via lemma content:**
- Lemma `content` is stored as raw HTML (from the wangEditor) and rendered unescaped into `detail.html:58` (`{{fullcon.content}}` is auto-escaped in Jinja by default, so the HTML won't render — but the wangEditor produces markup that gets stripped to text). Also `result.html:57` and the title flows via `value=` without quoting. The clear stored-XSS risk is in `detail.html:53` `value= {{ fullcon.title }}` (no quotes).
- Files: `app/templates/detail.html:53`, `app/templates/result.html:55`

**`/api/reset` exposed (see Tech Debt):** Anyone can `GET /api/reset` and drop all tables.

**`app.run(debug=True)` in `run.py:5`:**
- Werkzeug debugger PIN-protected but with debug on, tracebacks can leak env (DB URI is in the traceback frame locals — including the `123456` password). Debug mode should never run in production.
- Files: `run.py:5`

**`config.ini` ships hardcoded socket path `/Users/chujunqi/work/python/baike/`:**
- Path belongs to a single developer's machine and is checked into the repo. Not a credential but a privacy/portability leak.
- Files: `config.ini:5`

**No password validation on `/api/regist`:**
- `register.html:33` confirms two passwords client-side only; the server (`/api/regist`) accepts any string. Empty / whitespace / 4-char passwords are accepted.
- Files: `app/api/__init__.py:15-29`, `app/templates/register.html:55-59`

## Performance Bottlenecks

**`Lemma.query.filter(...).like("%...%")` with leading wildcard:**
- Problem: `LIKE '%foo%'` cannot use a B-tree index. As the lemma table grows, search becomes a full scan. For a 2017 dorm project this is irrelevant; flag for any future scale.
- Files: `app/route/user.py:32`
- Cause: Leading `%` disables index usage.
- Improvement path: Add a FULLTEXT index on `title` and use `MATCH ... AGAINST`, or use MySQL `ngram` parser for CJK. Trigram search is overkill for this codebase.

**Template-level N+1 on `Lemma.comments`:**
- Problem: `Lemma.comments = db.relationship('Comment', backref='lemmas', lazy='dynamic')`. When `detail.html` iterates results, every `comments` access fires a fresh query.
- Files: `app/api/model.py:36`, `app/templates/detail.html:77`
- Improvement path: Use `lazy='select'` or eager-load with `joinedload`/`subqueryload` once the comment feature is re-enabled.

**No DB connection pooling configured:**
- `app.config['SQLALCHEMY_DATABASE_URI']` set but no `SQLALCHEMY_ENGINE_OPTIONS`. SQLAlchemy defaults to a QueuePool of size 5 / overflow 10 — fine for this app, but worth noting if multiple workers are added.
- Files: `app/__init__.py:11`

## Fragile Areas

**`/api/modify` (lines 65-73 in `app/api/__init__.py`):**
- Files: `app/api/__init__.py:65-73`
- Why fragile: Three bugs stacked (missing return, duplicate variable, no primary-key lookup for the merge target). `db.session.merge` on a non-persisted `Lemma(...)` instance will INSERT a new row rather than UPDATE the existing one — so the "modify" path actually creates a duplicate lemma with a fresh id. Tests would not catch this because there are none.
- Safe modification: First, switch to `lemma = Lemma.query.filter_by(title=newTitle).first(); if lemma: lemma.content = newContent`, then commit, then add the missing return.
- Test coverage: Zero.

**`/user/detail` (lines 39-43 in `app/route/user.py`):**
- Files: `app/route/user.py:39-43`
- Why fragile: Returns a query object (not evaluated) and passes it to a template that iterates and accesses fields. Any change to the relationship or filter breaks the page silently — no error, just an empty page.
- Safe modification: Replace with `.all()` and an explicit empty-result branch. Add a test that asserts a missing title redirects with a flash.
- Test coverage: Zero.

**`Comment` model (`app/api/model.py:45-63`):**
- Files: `app/api/model.py:45-63`
- Why fragile: `__str__` references `self.title` (does not exist). `__init__` parameter is `lemma_title` but the attribute set is also `self.lemma_title` (no such column). It is dead code but looks alive.
- Safe modification: Decide whether to revive or delete. If delete, drop the table from `baike.sql` and remove the import.
- Test coverage: Zero.

**`/api/reset` (lines 87-100 in `app/api/__init__.py`):**
- Files: `app/api/__init__.py:87-100`
- Why fragile: Drops and recreates the entire schema with hard-coded seed data. One accidental GET in production = total data loss.
- Safe modification: Gate behind `if app.debug`, or replace with a CLI command.
- Test coverage: Zero.

## Scaling Limits

**Single MySQL backend, no caching:**
- Current capacity: Tens of concurrent users on a single Flask dev server.
- Limit: `app.run(debug=True)` is single-process, single-threaded. `config.ini` declares 1 process / 1 thread for uwsgi. No caching layer (no Redis, no in-memory cache).
- Scaling path: Run `gunicorn` workers, add Flask-Caching, move sessions to Redis, add FULLTEXT search (see Performance section).

**Static assets served by Flask in dev:**
- All Bootstrap / jQuery / wangEditor assets are served via Flask's static handler (`/static/...`). Fine in dev; in production this should be nginx.
- Files: `app/templates/*.html` (every `<link>`/`<script>`)

## Dependencies at Risk

**`mysql-python`:**
- Risk: `requirements.txt:4` pins `mysql-python` (a.k.a. `MySQL-python`). It is unmaintained since 2014, does not support Python 3 (`reload(sys)` and `sys.setdefaultencoding` at the top of `app/__init__.py:3-4` and `app/api/__init__.py:3-4` are clear Python 2 idioms — `setdefaultencoding` was removed in Python 3). Project will not install on modern Python.
- Files: `requirements.txt:4`, `app/__init__.py:1-4`, `app/api/__init__.py:1-4`
- Impact: Cannot run on Python 3 without code changes. Cannot install via `pip` on modern systems.
- Migration plan: Replace with `mysqlclient` (drop-in, Python 3 compatible) or `PyMySQL`. Remove `reload(sys)` / `sys.setdefaultencoding` blocks. Pin `Flask-SQLAlchemy>=2.5` and `Flask-Login>=0.5`.

**`flask_SQLAlchemy`:**
- Risk: Package name uses underscore. PyPI canonical is `Flask-SQLAlchemy` (hyphen). Older pip accepts both; new pip resolves only the canonical. No version pin.
- Files: `requirements.txt:3`

**No version pins anywhere:**
- Risk: `flask`, `flask_login`, `flask_SQLAlchemy`, `mysql-python` are unpinned. A future major Flask release (3.x) breaks `@login_required` import path and config key names. Reproducible builds impossible.
- Files: `requirements.txt`

## Missing Critical Features

**Working comment system:**
- Problem: The `Comment` model exists, the UI exists, the seed data references comments — but no live route to create or list them.
- Files: `app/api/__init__.py:76-85`, `app/templates/detail.html:77-91, 104-117`
- Blocks: Any user-facing comment feature; demo path is broken.

**Search by content, not just title:**
- Problem: `like("%"+searchtext+"%")` only searches `title`. The `content` field is never searched. Wiki users expect body matches.
- Files: `app/route/user.py:32`
- Blocks: Useful search.

**Lemma edit history / versioning:**
- Problem: `modify` overwrites content. No audit trail.
- Blocks: Trust in editorial workflow.

**Pagination on `/user/search`:**
- Problem: `results = Lemma.query.filter(...).all()` — single page, no limit. Will OOM if table grows.
- Files: `app/route/user.py:32`

**HTTP security headers:**
- Problem: No CSP, no X-Frame-Options, no X-Content-Type-Options. The wangEditor HTML payload plus XSS-risk attribute rendering makes a CSP important.
- Blocks: Hardening for any non-toy deployment.

## Test Coverage Gaps

**Every code path is untested:**
- What's not tested: All 7 routes (`/api/regist`, `/api/login`, `/api/logout`, `/api/add`, `/api/modify`, `/api/reset`; `/user/home`, `/user/login`, `/user/regist`, `/user/add`, `/user/search`, `/user/detail`, `/user/modify`). All three models (`User`, `Lemma`, `Comment`). Templates (no template-level tests).
- Files: every `app/**` source file
- Risk: Every change is unverified. The known bugs above were undetected for years because nothing runs the code path.
- Priority: High (especially `modify`, `detail`, `reset`, `Comment`).

**No `.planning/` ignore:**
- `.gitignore` does not list `.planning/`, `.claude/`, `__pycache__/`, `*.pyc`, or `.venv/`. The repo already has `app/__pycache__/`, `app/api/__pycache__/`, `app/route/__pycache__/` listed as untracked by git, which means a future `git add .` will commit them.
- Files: `.gitignore`
- Risk: Bytecode + tooling artifacts in version control.
- Priority: Low (one-line fix), but worth doing before any other commit.

**No CI configuration:**
- No `.github/`, no `.gitlab-ci.yml`, no tox / nox / pytest config. Even if tests existed, nothing would run them.
- Priority: Low.

---

*Concerns audit: 2026-06-11*