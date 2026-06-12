# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import backref
import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):

    __tablename__= 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    comments = db.relationship(
        'Comment',
        backref=backref('author', lazy='joined'),
        cascade='all, delete-orphan',
    )

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
    comments = db.relationship(
        'Comment',
        backref='lemmas',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def __str__(self):
        return '词条<title:%s, contet:%s>' % (self.title, self.content)

    def __init__(self, title = None, content = None ):
        self.title = title
        self.content =content

class Comment(db.Model):

    __tablename__= 'comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lemma_id = db.Column(db.Integer, db.ForeignKey('lemma.id'), nullable=False)
    content = db.Column(db.String(320))
    time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __str__(self):
        snippet = (self.content or '')[:20]
        return '评论<%s>' % (snippet)

    def __init__(self, user_id=None, lemma_id=None, content=None):
        self.user_id = user_id
        self.lemma_id = lemma_id
        self.content = content


def init_db():
    # Note: seed users (e.g. 'a'/'a') bypass registBusiness length validation — they are created directly here, not via HTTP form. Do not route seed users through registBusiness; the 6-30 char check in Plan 2.1's registBusiness is an HTTP-form contract and does not apply to direct User() construction.
    db.drop_all()
    db.create_all()
    # D-08: default admin seed account 'a' / 'a' (hashed, is_admin=True).
    db.session.add(User(name='a', password=generate_password_hash('a'), is_admin=True))
    # 7 seed Lemma rows (verbatim copy from prior /api/reset body in
    # app/api/__init__.py, preserving HTML content exactly).
    db.session.add(Lemma(title='123', content='<p><font size="6">第一</font></p><p>这里是第一</p><p><font color="#800080" size="6">第二</font></p><p><font color="#ff0000" size="4">竣棋超神了</font></p><p><font color="#0000ff" size="6">第三</font></p><p><font color="#ff00ff" size="5">加个鸡腿</font></p><p><br></p>'))
    db.session.add(Lemma(title='啦啦啦1我是竣棋呀', content='<p><font color="#880000" size="4">完全不想睡觉</font></p><p><font size="6">爽到飞起</font></p><p><font color="#ff0000" size="5">一句话写完了查询</font><br></p><p><br></p>'))
    db.session.add(Lemma(title='hh哈哈哈641好厉害哦', content='<p><font size="6">本学期第四次看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真他妈精神</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">明天就回家了好开心</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如"孩子是祖国的明天"。</span></font></p><p><br></p>'))
    db.session.add(Lemma(title='分工-张芳淋-前端设计与实现，配置运行环境', content='<p><font size="6">本学期第四次看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真他妈精神</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">明天就回家了好开心</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如"孩子是祖国的明天"。</span></font></p><p><br></p>'))
    db.session.add(Lemma(title='苏庭轩-分工-前端实现与后台开发', content='<p><font size="6">本学期第四次看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真他妈精神</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">明天就回家了好开心</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如"孩子是祖国的明天"。</span></font></p><p><br></p>'))
    db.session.add(Lemma(title='刘中琦-分工-数据库设计、后台数据库操作', content='<p><font size="6">本学期第四次看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真他妈精神</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">明天就回家了好开心</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如"孩子是祖国的明天"。</span></font></p><p><br></p>'))
    db.session.add(Lemma(title='楚竣棋-后台逻辑设计与实现，服务器管理与维护-分工', content='<p><font size="6">来看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真开心</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">我爱软件架构</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如"孩子是祖国的明天"。</span></font></p><p><br></p>'))
    db.session.commit()
