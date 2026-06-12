# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
import os
from urllib.parse import quote_plus
from flask import Flask, render_template
from flask_login import LoginManager
from sqlalchemy.engine.url import URL

from app.route.user import user
from app.api import api
from app.api.model import db, User


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

@login_manager.user_loader
def load_user(id):
        return User.query.get(int(id))

@app.route('/')
def home():
    return render_template('home.html')
