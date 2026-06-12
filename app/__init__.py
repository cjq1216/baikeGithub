# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
import os
from urllib.parse import quote_plus
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.engine.url import URL
import click

from app.route.user import user
from app.api import api
from app.api.admin import admin
from app.api.model import db, User
import sys


def _resolve_flask_secret():
    # 1. Explicit env var wins.
    secret = os.environ.get('FLASK_SECRET')
    if secret:
        return str(secret)
    # 2. Optional override path (not exposed in README; for ops to point
    #    at a mounted secret in containerized environments).
    secret_file = os.environ.get('FLASK_SECRET_FILE')
    if secret_file:
        with open(secret_file, 'r') as f:
            return f.read().strip()
    # 3. Dev-friendly fallback: persist a random secret on disk so session
    #    cookies survive a process restart. No chmod (CD-02); umask decides.
    instance_dir = app.instance_path
    secret_path = os.path.join(instance_dir, '.flask_secret')
    if os.path.exists(secret_path):
        with open(secret_path, 'r') as f:
            stored = f.read().strip()
            if stored:
                return stored
    os.makedirs(instance_dir, exist_ok=True)
    new_secret = os.urandom(32).hex()
    with open(secret_path, 'w') as f:
        f.write(new_secret)
    return new_secret


app = Flask(__name__)
app.secret_key = _resolve_flask_secret()
# D-05/D-07: DB_* are required; missing any one is a hard fail (no silent
# default back to the old hardcoded values).
_required_db_vars = ('DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME')
for _name in _required_db_vars:
    if _name not in os.environ:
        raise RuntimeError("Missing required env var: " + _name)
app.config['SQLALCHEMY_DATABASE_URI'] = URL.create(
    drivername='mysql+mysqlclient',
    username=os.environ['DB_USER'],
    password=quote_plus(os.environ['DB_PASSWORD']),
    host=os.environ['DB_HOST'],
    port=int(os.environ['DB_PORT']),
    database=os.environ['DB_NAME'],
)
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = '.login'
login_manager.init_app(app)

app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(admin, url_prefix='/api/admin')

# D-10: Enable global CSRF protection on every state-changing POST.
csrf = CSRFProtect(app)

# D-11: CSRF failures (Flask-WTF raises 400) must NOT surface as the default
# Flask 400 traceback — flash a friendly message and redirect back to the
# originating page (or home if referrer is missing).
@app.errorhandler(400)
def handle_csrf_error(e):
    flash('会话已过期，请重试')
    return redirect(request.referrer or url_for('apple.home'))

# D-17 / D-18: unified error page for 403 / 404 / 500. Tracebacks are still
# written to stderr by Flask's default logger; they are not exposed to the
# browser because the rendered template only consumes server-controlled
# `error.code` / `error.name` / `error.description`.
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    return render_template('error.html', error=e), e.code

# D-16 / D-25: `flask init-db` is the production / container entrypoint for
# bootstrapping the database. It calls the same `init_db()` function used
# by the dev-only /api/reset route, so dev and prod share one seed path.
@app.cli.command("init-db")
def init_db_command():
    """Drop all, recreate all, seed."""
    from app.api.model import init_db
    init_db()
    print('Database initialized.')

# D-24: `flask promote-admin <username>` flips is_admin=True on an existing
# user. Unknown username exits 1 with a printed error. This is the only
# HTTP-less way to grant admin status — the User model accepts is_admin
# for the seeder, but no request handler passes that arg.
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

@login_manager.user_loader
def load_user(id):
        return User.query.get(int(id))

@app.route('/')
def home():
    return render_template('home.html')
