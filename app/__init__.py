# coding=utf-8
from flask import Flask, render_template
from flask_login import LoginManager

from app.route.user import user
from app.api import api
from app.api.model import db, User

app = Flask(__name__)
app.secret_key = '1frMFuWRVPV1'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://%s:%s@%s/%s" % ('root', '123456', '127.0.0.1', 'baike')
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
