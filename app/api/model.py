# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):

    __tablename__= 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)

    def __str__(self):
        return '用户<id:%s, 姓名:%s>' % (self.id, self.name)

    def __init__(self, name = None, password = None, is_admin = None ):
        self.name = name
        self.password = password
        self.is_admin = is_admin if is_admin is not None else False

class Lemma(db.Model):

    __tablename__= 'lemma'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40))
    content = db.Column(db.Text)
    comments = db.relationship('Comment', backref='lemmas', lazy='dynamic')

    def __str__(self):
        return '词条<title:%s, contet:%s>' % (self.title, self.content)

    def __init__(self, title = None, content = None ):
        self.title = title
        self.content =content

class Comment(db.Model):

    __tablename__= 'comment'
    id = db.Column(db.Integer, primary_key=True)
    #user_name = db.Column(db.String(30), db.ForeignKey('User.name'))
    user_name = db.Column(db.String(30))
    lemma_id = db.Column(db.Integer, db.ForeignKey('lemma.id'))
    #title = db.Column(db.String(40))
    content = db.Column(db.String(320))
    time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __str__(self):
        return '评论<%s>' % (self.title)

    def __init__(self, user_name = None, lemma_title = None, content = None ):
        self.user_name = current_user
        self.lemma_title = lemma_title
        self.content = content
        self.time = datetime.now()
