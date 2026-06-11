# Phase 2: Security & Auth Hardening - Pattern Map

**Mapped:** 2026-06-11
**Files analyzed:** 9 (2 new files + 7 modified touchpoints)
**Analogs found:** 7 / 9 (admin blueprint + error page need research-backed patterns; no existing analog)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/api/admin.py` (new) | blueprint + decorator + route | request-response | `app/api/__init__.py` (api blueprint) | role-match |
| `app/templates/error.html` (new) | template | render | `app/templates/signin.html` (self-contained HTML) | role-match |
| `app/__init__.py` (modify) | app factory | bootstrap | (self) — incremental changes | exact |
| `app/api/model.py` (modify) | model | CRUD | (self) `User` class | exact |
| `app/api/__init__.py` (modify) | blueprint | request-response | (self) — incremental changes | exact |
| `app/templates/register.html` (modify) | template | render | (self) — add csrf_token hidden input | exact |
| `app/templates/signin.html` (modify) | template | render | (self) — add csrf_token hidden input | exact |
| `app/templates/add.html` (modify) | template | render | (self) — add csrf_token hidden input | exact |
| `app/templates/modify.html` (modify) | template | render | (self) — add csrf_token hidden input | exact |
| `app/templates/result.html` (modify) | template | render | (self) — add csrf_token hidden input (search form) | exact |
| `app/templates/detail.html` (modify) | template | render | (self) — add admin button block | exact |
| `requirements.txt` (modify) | config | — | (self) — append one line | exact |
| `.dockerignore` (new) | config | — | none — file does not exist | no-analog |

## Pattern Assignments

### `app/api/admin.py` (blueprint, request-response) — NEW

**Analog:** `app/api/__init__.py` (api blueprint)

**Blueprint + route pattern** (`app/api/__init__.py:1-9`):
```python
from flask import Blueprint, request, abort, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from app.api.model import User, Lemma, Comment, db

api = Blueprint(
        'api',
        __name__,
)
```

**Login-required POST pattern** (`app/api/__init__.py:38-42`):
```python
@api.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('apple.home'))
```

**Delete-row + flash + redirect pattern** (combine `modify` at `app/api/__init__.py:61-73` with delete-by-id intent):
```python
@api.route('/modify', methods=['POST'])
@login_required
def modify():
    newTitle = request.form.get('newTitle')
    newContent = request.form.get('newContent')
    lemma = Lemma.query.filter_by(title=newTitle).first()
    if lemma is None:
        flash('修改失败！词条不存在')
        return redirect(url_for('apple.home'))
    lemma.content = newContent
    db.session.commit()
    flash('修改成功！')
    return redirect(url_for('apple.home'))
```

**Custom decorator pattern** — NO existing analog. Compose from `flask_login.login_required` + `current_user` (used at `app/api/__init__.py:80` and `app/route/user.py:3`). Standard Flask decorator factory:
```python
from functools import wraps
from flask import abort
from flask_login import login_required, current_user

def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            abort(403)
        return f(*args, **kwargs)
    return wrapper
```

**`url_for` cross-blueprint convention** (`app/api/__init__.py:22`, `app/route/user.py:37`):
```python
return redirect(url_for('apple.home'))   # page blueprint (named 'apple', not 'user')
return redirect(url_for('api.<endpoint>')) # for self-blueprint
# Phase 2: also use 'admin.<endpoint>' for the new blueprint
```

---

### `app/templates/error.html` (template, render) — NEW

**Analog:** `app/templates/signin.html` (self-contained HTML, no base template)

**Self-contained HTML structure** (`app/templates/signin.html:1-19`):
```html
<!DOCTYPE html>
<html lang="zh-cn">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description" content="">
        <meta name="author" content="">
        <title>Signin</title>
        <link rel='stylesheet' href="../static/stylesheets/style.css">
        <link rel="stylesheet" href="../static/stylesheets/bootstrap.min.css">
        <link href="../static/stylesheets/mycss/signin.css" rel="stylesheet">
    </head>
    <body>...</body>
</html>
```

**`get_flashed_messages` block pattern** (used in 5 templates; `app/templates/signin.html:24-32`):
```html
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

**Bootstrap 3 + jQuery script block** (`app/templates/signin.html:44-54`):
```html
<script src="../static/javascripts/jquery-1.11.3.min.js"></script>
<script src="../static/javascripts/bootstrap.min.js"></script>
<script src="../static/javascripts/docs.min.js"></script>
```

**Notes for error.html** (per CD-03): self-contained, same style as `signin.html` / `register.html`. Use Bootstrap 3 + the same `style.css` link. Display status code (e.g. `{{ error.code }}`) and short message (e.g. `{{ error.description }}`) with a link to `url_for('apple.home')` for the back-to-home button.

---

### `app/__init__.py` (app factory, bootstrap) — MODIFY

**Current state** (`app/__init__.py:1-23`):
```python
from urllib.parse import quote
from flask import Flask, render_template
from flask_login import LoginManager

from app.route.user import user
from app.api import api
from app.api.model import db, User

app = Flask(__name__)
app.secret_key = '1frMFuWRVPV1'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://%s:%s@%s:%s/%s" % ('cjq', quote('Cjq@123456'), '162.14.107.126', '3307', 'baike')
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = '.login'
login_manager.init_app(app)

app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(api, url_prefix='/api')

@login_manager.user_loader
def load_user(id):
        return User.query.get(int(id))
```

**Blueprint registration pattern to add** (line 19 — repeat for `admin`):
```python
app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(api, url_prefix='/api')
# Phase 2 add:
app.register_blueprint(admin, url_prefix='/api/admin')
```

**SQLAlchemy URL composition pattern** — use `sqlalchemy.engine.url.URL` per D-07:
```python
from sqlalchemy.engine.url import URL
from urllib.parse import quote_plus
url = URL.create(
    drivername='mysql+mysqlclient',
    username=os.environ['DB_USER'],
    password=quote_plus(os.environ['DB_PASSWORD']),
    host=os.environ['DB_HOST'],
    port=int(os.environ['DB_PORT']),
    database=os.environ['DB_NAME'],
)
app.config['SQLALCHEMY_DATABASE_URI'] = url
```

**`login_manager.login_view` convention** (line 15 — value is endpoint name `'login'` resolved relative to the blueprint it's used in; with current apple blueprint, the relative `.login` resolves to `apple.login`. Keep this — Phase 2 does not change login_view per D-19):
```python
login_manager.login_view = '.login'
```

**`@app.cli.command` pattern** — NO existing analog. Standard Flask CLI command (D-16, D-24):
```python
@app.cli.command("init-db")
def init_db_command():
    """Drop all, recreate all, seed."""
    from app.api.model import init_db
    init_db()
    print("Database initialized.")

@app.cli.command("promote-admin")
@click.argument("username")
def promote_admin_command(username):
    from app.api.model import User, db
    user = User.query.filter_by(name=username).first()
    if user is None:
        print(f"User {username!r} not found.")
        sys.exit(1)
    user.is_admin = True
    db.session.commit()
    print(f"User {username!r} promoted to admin.")
```

**`errorhandler` pattern** — NO existing analog. Add to `app/__init__.py`:
```python
from flask import render_template, flash, redirect, request

@app.errorhandler(400)
def handle_csrf_error(e):
    flash('会话已过期，请重试')
    return redirect(request.referrer or url_for('apple.home'))

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(500)
def handle_error(e):
    return render_template('error.html', error=e), e.code
```

---

### `app/api/model.py` (model, CRUD) — MODIFY

**Current `User` model** (`app/api/model.py:8-20`):
```python
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(40))

    def __str__(self):
        return '用户<id:%s, 姓名:%s>' % (self.id, self.name)

    def __init__(self, name=None, password=None):
        self.name = name
        self.password = password
```

**Field changes** (D-02, D-23):
- `password = db.Column(db.String(40))` → `db.Column(db.String(255))`
- Add: `is_admin = db.Column(db.Boolean, default=False)`
- Extend `__init__` to accept `is_admin` parameter

**Module-level `init_db()` pattern** (D-15, D-25) — refactor from `app/api/__init__.py:87-100`:
```python
# Current reset (app/api/__init__.py:87-100):
@api.route('/reset')
def reset():
    db.drop_all()
    db.create_all()
    db.session.add(User(name='a', password='a'))
    db.session.add(Lemma(title='123', content='...'))
    # ... 6 more Lemma rows
    db.session.commit()
    return jsonify(error=False)
```

Extract to `app/api/model.py`:
```python
from werkzeug.security import generate_password_hash

def init_db():
    db.drop_all()
    db.create_all()
    db.session.add(User(name='a', password=generate_password_hash('a'), is_admin=True))
    db.session.add(Lemma(title='123', content='<p>...'))  # same 7 seed rows
    # ... copy verbatim
    db.session.commit()
```

**SQLAlchemy import convention** (`app/api/model.py:1-6`):
```python
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
import datetime

db = SQLAlchemy()
```

---

### `app/api/__init__.py` (blueprint, request-response) — MODIFY

**Current `regist` route** (`app/api/__init__.py:11-25`):
```python
@api.route('/regist', methods=['POST'])
def registBusiness():
    name = request.form.get('name')
    nowUser = User.query.filter_by(name=name).first()
    if not nowUser:
        uesrname = request.form.get('name')
        password = request.form.get('password')
        user = User(name=name, password=password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('apple.home'))
    else:
        flash('注册失败！帐号已存在')
    return redirect(url_for('apple.regist'))
```

**Hash on registr** (D-01) — modify to use `generate_password_hash`:
```python
from werkzeug.security import generate_password_hash, check_password_hash

# inside regist:
user = User(name=name, password=generate_password_hash(password))
```

**Current `login` route** (`app/api/__init__.py:27-36`):
```python
@api.route('/login', methods=['POST'])
def loginBusiness():
    name = request.form.get('name')
    password = request.form.get('password')
    nowUser = User.query.filter_by(name=name, password=password).first()
    if nowUser:
        login_user(nowUser)
        return redirect(url_for('apple.home'))
    flash('登录失败，请检查账号和密码！')
    return redirect(url_for('apple.login'))
```

**Hash on login** (D-01, D-03) — change to `check_password_hash` and unify error message:
```python
nowUser = User.query.filter_by(name=name).first()
if nowUser and check_password_hash(nowUser.password, password):
    login_user(nowUser)
    return redirect(url_for('apple.home'))
flash('账号或密码错误')
return redirect(url_for('apple.login'))
```

**Reset route guard** (D-13, D-14) — keep the route, add `debug` guard, delegate to `init_db`:
```python
@api.route('/reset')
def reset():
    if not app.debug:
        abort(404)
    from app.api.model import init_db
    init_db()
    return jsonify(error=False)
```

(Note: `app` is in scope only if `from app import app` is added at top — adjust imports accordingly. Alternative: `if not current_app.debug`.)

---

### Templates — add `csrf_token` hidden input (5 files)

**Insertion pattern** (after the `<form ...>` tag, before the first real input):

For `register.html:20` (after `<form class="form-signin" role="form" action="/api/regist" method="post">`):
```html
<form class="form-signin" role="form" action="/api/regist" method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <h2 class="form-signin-heading">新用户注册</h2>
```

For `signin.html:22` (after `<form class="form-signin" role="form" action="/api/login", method="post">`):
```html
<form class="form-signin" role="form" action="/api/login", method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <h2 class="form-signin-heading">用户登录</h2>
```

For `add.html:42` (after `<form role="form" action="/api/add" method="post">`):
```html
<form role="form" action="/api/add" method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <div class="blog-header">
```

For `modify.html:50` (after `<form role="form" action="/api/modify" method="post">`):
```html
<form role="form" action="/api/modify" method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <div class="blog-header">
```

For `result.html:40` (search form, after `<form action="/user/search" method="post">`):
```html
<form action="/user/search" method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <input type="text" class="col-sm-8 form-control searchtext" id="searchtext" name="searchtext" required></input>
```

(For `detail.html:50`, the modify form also needs a CSRF token because it POSTs to `/api/modify`.)

**`get_flashed_messages` reference block** (already present in 5 templates — leave untouched).

---

### `app/templates/detail.html` (template, render) — add admin button block

**Current admin-conditional pattern** (`app/templates/detail.html:64-73`):
```html
{% if current_user.is_active %}
<div class="modify-btn">
    <button class="btn btn-lg btn-primary btn-block" type="button" id="modify">修改词条</button>
    <button class="btn btn-lg btn-primary btn-block" type="submit" id="confirmModify">确认修改</button>
    <button class="btn btn-lg btn-primary btn-block" type="button" id="cancelModify">放弃修改</button>
    <br>
    <button class="btn btn-lg btn-primary btn-block" type="button" id="sendComment">发布评论</button>
    <br>
</div>
{% endif %}
```

**Add admin-only delete block** (D-22) — note: `is_active` is an attribute on Flask-Login's `UserMixin` (always True for authenticated non-anonymous users); replace with `is_authenticated` to follow Flask-Login convention. New block goes inside the existing modify form, after the existing `{% if %}`:
```html
{% if current_user.is_authenticated and current_user.is_admin %}
<button class="btn btn-lg btn-danger btn-block" type="button" id="deleteLemma">删除词条</button>
{% endif %}
```

If the delete button is to actually submit, wrap in its own form (separate from the modify form) so CSRF tokens stay clean:
```html
<form action="{{ url_for('admin.delete_lemma', lemma_id=fullcon.id) }}" method="post" style="display:inline">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    {% if current_user.is_authenticated and current_user.is_admin %}
    <button class="btn btn-lg btn-danger btn-block" type="submit" id="deleteLemma">删除词条</button>
    {% endif %}
</form>
```

---

### `requirements.txt` (config) — append

**Current contents**:
```
Flask>=3.0,<4.0
Flask-Login>=0.6,<1.0
Flask-SQLAlchemy>=3.0,<4.0
mysqlclient>=2.2,<3.0
```

**Append**:
```
Flask-WTF>=1.2,<2.0
```

---

### `.dockerignore` (config) — NEW

**No existing analog.** Standard minimal `dockerignore` based on the repo layout. Suggested contents (planner decides exact lines):
```
instance/
__pycache__/
*.pyc
.venv/
venvbaike/
.planning/
```

---

## Shared Patterns

### Authentication — login_required decorator
**Source:** `app/api/__init__.py:3,39` and `app/route/user.py:3,25,49`
**Apply to:** All routes requiring session, including new `admin` blueprint
```python
from flask_login import login_required, current_user

@api.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('apple.home'))
```

### Flash + redirect error feedback
**Source:** `app/api/__init__.py:24,35,55,58,68,72`; `app/route/user.py:36,44`
**Apply to:** All routes, including new admin delete
```python
flash('添加失败！该词条已存在！')
return redirect(url_for('apple.add'))
```

### `current_user` template check
**Source:** `app/templates/add.html:29`, `detail.html:64`, `home.html:30`
**Apply to:** `detail.html` admin block (use `is_authenticated`, not `is_active`)
```html
{% if current_user.is_authenticated and current_user.is_admin %}
    <button ...>删除词条</button>
{% endif %}
```

### `url_for` cross-blueprint convention
**Source:** `app/api/__init__.py:22,25,34,36,42,56,59,69,73`; `app/route/user.py:37,45`
**Apply to:** All redirects — use `apple.<endpoint>` for page routes, `api.<endpoint>` for form routes, `admin.<endpoint>` for the new admin blueprint
```python
return redirect(url_for('apple.home'))   # page blueprint (NOT 'user.<endpoint>')
return redirect(url_for('admin.delete_lemma', lemma_id=id))
```

### db.session transaction pattern
**Source:** `app/api/__init__.py:19-20,53-54,71,99`
**Apply to:** `init_db()` extraction + new admin delete
```python
db.session.add(user)
db.session.commit()
```

### `db.drop_all()` + `db.create_all()` reset pattern
**Source:** `app/api/__init__.py:89-90`
**Apply to:** `init_db()` extracted function
```python
db.drop_all()
db.create_all()
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `app/api/admin.py` | blueprint | request-response | New blueprint — no existing admin route. Compose from `api` blueprint + `flask_login.login_required` + custom decorator factory pattern. |
| `app/templates/error.html` | template | render | No existing error template. Mirror self-contained `signin.html` per CD-03. |
| `app/__init__.py` — errorhandler block | handler | request-response | No existing `errorhandler` calls in the codebase. Use Flask `@app.errorhandler(400/403/404/500)` standard pattern. |
| `app/__init__.py` — `@app.cli.command` | CLI | command | No existing CLI commands. Use Flask standard `@app.cli.command("init-db")` / `@app.cli.command("promote-admin")` with `@click.argument("username")` for the latter. |
| `app/__init__.py` — env var loading | config | bootstrap | No existing env handling. `os.environ[...]` strict read, fallback `os.urandom(32)` for `FLASK_SECRET` written to `instance/.flask_secret` per D-06. |
| `.dockerignore` | config | — | File does not exist. |

## Metadata

**Analog search scope:** `app/` (root, api/, route/, templates/), `requirements.txt`
**Files scanned:** 13 (3 Python source, 7 templates, 1 config, 1 entrypoint, 1 readme-equivalent via CLAUDE.md)
**Pattern extraction date:** 2026-06-11
