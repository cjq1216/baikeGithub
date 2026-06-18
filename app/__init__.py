# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
# PyMySQL registers itself as the MySQLdb module so SQLAlchemy's
# `mysql+mysqldb` driver name (the `mysql+mysqlclient` alias was removed
# in SQLAlchemy 2.x) works on every platform without compiling a C extension.
import pymysql
pymysql.install_as_MySQLdb()
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.{APP_ENV} before any config check. APP_ENV defaults to 'dev'.
# 'test' is reserved for conftest — it pre-sets DB_* via os.environ.setdefault
# and skips the .env lookup so pytest doesn't need an .env file on disk.
# python-dotenv's default override=False means shell env / docker --env-file
# always wins over the .env file values.
APP_ENV = os.environ.get('APP_ENV', 'dev')
if APP_ENV != 'test':
    _dotenv_path = Path(__file__).resolve().parent.parent / f'.env.{APP_ENV}'
    load_dotenv(dotenv_path=str(_dotenv_path), override=False)

import re
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup, escape
from sqlalchemy.engine.url import URL
import click

from app.route.user import user
from app.api import api
from app.api.admin import admin
from app.api.model import db, User, Lemma
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

# D-88 / CD-22: ProxyFix 条件启用,默认关闭(dev python run.py 不经代理,
# 避免 X-Forwarded-For 伪报头被信任)。Dockerfile 设 ENV FLASK_BEHIND_PROXY=true
# 触发自动启用,让 nginx 反代下 url_for(_external=True) 生成 https URL,
# request.remote_addr 显示真实客户端 IP。trust 1 层代理(本项目无 CDN/LB)。
if os.environ.get('FLASK_BEHIND_PROXY', '').lower() == 'true':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.secret_key = _resolve_flask_secret()


# D-50: Jinja2 wikilink filter 解析 [[xxx]] — 存在 → 蓝链接,不存在 → 红虚线 + "(创建此词条)"
@app.template_filter('wikilink')
def wikilink_filter(content):
    if not content:
        return content

    def render_wikilink(match):
        title = match.group(1).strip()
        if not title:
            return match.group(0)
        # D-51: 标题转义防 XSS(markupsafe.escape 转 < > & 等)
        safe_title = escape(title)
        target = Lemma.query.filter_by(title=title).first()
        if target is not None:
            return f'<a href="/user/detail?title={title}">{safe_title}</a>'
        else:
            return (
                f'<a class="wikilink-missing" '
                f'href="/user/add?title={title}">'
                f'{safe_title} (创建此词条)→</a>'
            )

    # D-51: 非贪婪 + 不跨行
    return Markup(re.sub(r'\[\[([^\[\]\n]+?)\]\]', render_wikilink, content))


# D-05/D-07: DB_* are required; missing any one is a hard fail (no silent
# default back to the old hardcoded values). Values come from .env.{APP_ENV}
# (dev) or `docker run --env-file` / shell (prod), never hardcoded.
# 空字符串也算缺(.env.prod 模板里 DB_* 都是空,用户必须填)。
# dev 模式 DB_PASSWORD 允许空(XAMPP/MAMP 本地 MySQL 常见无密码场景)。
_required = ('DB_HOST', 'DB_PORT', 'DB_USER', 'DB_NAME')
_missing = [v for v in _required if not os.environ.get(v, '').strip()]
if APP_ENV != 'dev' and not os.environ.get('DB_PASSWORD', '').strip():
    _missing.append('DB_PASSWORD')
# DB_PORT 还必须是合法整数,否则 URL.create 里的 int() 静默炸
_db_port_raw = os.environ.get('DB_PORT', '')
if _db_port_raw.strip():
    try:
        int(_db_port_raw)
    except ValueError:
        _missing.append(f'DB_PORT (must be a valid integer, got {_db_port_raw!r})')
elif 'DB_PORT' not in _missing:
    _missing.append('DB_PORT')

if _missing:
    raise RuntimeError(
        f"Missing/empty required env var(s): {', '.join(_missing)}\n"
        f"  APP_ENV={APP_ENV} (tried to load .env.{APP_ENV})\n"
        f"  dev  mode: ensure .env.{APP_ENV} exists in project root\n"
        f"  prod mode: pass via 'docker run --env-file .env.prod ...'"
    )

# prod 模式 FLASK_SECRET 必传:容器未挂卷,instance/.flask_secret 兜底
# 在容器重启时会重新生成,全员 session 立即失效。
if APP_ENV == 'prod':
    if not (os.environ.get('FLASK_SECRET') or os.environ.get('FLASK_SECRET_FILE')):
        raise RuntimeError(
            "FLASK_SECRET (or FLASK_SECRET_FILE) required when APP_ENV=prod\n"
            "  容器未挂卷,instance/.flask_secret 兜底会丢失,重启后全员 session 失效"
        )

app.config['SQLALCHEMY_DATABASE_URI'] = URL.create(
    drivername='mysql+mysqldb',
    username=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
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
# D-75: --if-empty flag 让容器启动幂等(已有数据秒返,避免重启清生产数据)。
# 不传 flag 行为完全等同改造前(强制 drop+create+seed)。
@app.cli.command("init-db")
@click.option('--if-empty', is_flag=True, help='Skip re-init if User table already has rows.')
def init_db_command(if_empty):
    """Drop all, recreate all, seed (idempotent with --if-empty)."""
    from app.api.model import init_db
    init_db(if_empty=if_empty)
    if if_empty:
        print('Database initialized (or skipped if non-empty).')
    else:
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
