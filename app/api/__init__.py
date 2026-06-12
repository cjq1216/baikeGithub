# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
from flask import Blueprint, request, abort, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required,logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.api.model import User, Lemma, Comment, db

api = Blueprint(
        'api',
        __name__,
)

@api.route('/regist', methods=['POST'])
def registBusiness():
    name = request.form.get('name')
    password = request.form.get('password')
    # D-04: 长度校验放在任何 DB 操作之前,即使名字已存在/不存在都先拒绝。
    # seed user 'a' (1 字符) 由 Plan 2.2 的 init_db() 直接走 User() 构造器创建,
    # 不走此 HTTP 路径,因此 6-30 字符规则不会阻塞 seed 账号。
    if len(name) < 6 or len(name) > 30 or len(password) < 6 or len(password) > 30:
        flash('用户名和密码长度需在 6-30 字符之间')
        return redirect(url_for('apple.regist'))
    nowUser = User.query.filter_by(name=name).first()
    if not nowUser:
        user = User(name=name, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('apple.home'))
    else :
        flash('注册失败！帐号已存在')
    return redirect(url_for('apple.regist'))

@api.route('/login',methods=['POST'])
def loginBusiness():
    name = request.form.get('name')
    password = request.form.get('password')
    nowUser = User.query.filter_by(name=name).first()
    if nowUser and check_password_hash(nowUser.password, password):
        login_user(nowUser)
        return redirect(url_for('apple.home'))
    flash('账号或密码错误')
    return redirect(url_for('apple.login'))

@api.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('apple.home'))

@api.route('/add', methods=['POST'])
@login_required
def add():
    title = request.form.get('title')
    nowTitle = Lemma.query.filter_by(title=title).first()
    if not nowTitle:
        title = request.form.get('title')
        content = request.form.get('content')
        lemma = Lemma(title=title, content=content)
        db.session.add(lemma)
        db.session.commit()
        flash('添加成功！')
        return redirect(url_for('apple.home'))
    else :
        flash('添加失败！该词条已存在！')
    return redirect(url_for('apple.add'))

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


# @api.route('/commen', methods=['POST'])
# @login_required
# def commen():
#     content = request.form.get('commentcontent')
#     user_name = current_user
#     lemma_id =
#     comment = Comment(lemma_id=lemma_id, user_name=user_name, content=content)
#     db.session.add(comment)
#     db.session.commit()
#     return flash('评论发表成功')

@api.route('/reset')
def reset():
    db.drop_all()
    db.create_all()
    db.session.add(User(name='a', password='a'))
    db.session.add(Lemma(title='123', content='<p><font size="6">第一</font></p><p>这里是第一</p><p><font color="#800080" size="6">第二</font></p><p><font color="#ff0000" size="4">竣棋超神了</font></p><p><font color="#0000ff" size="6">第三</font></p><p><font color="#ff00ff" size="5">加个鸡腿</font></p><p><br></p>'))
    db.session.add(Lemma(title='啦啦啦1我是竣棋呀', content='<p><font color="#880000" size="4">完全不想睡觉</font></p><p><font size="6">爽到飞起</font></p><p><font color="#ff0000" size="5">一句话写完了查询</font><br></p><p><br></p>'))
    db.session.add(Lemma(title='hh哈哈哈641好厉害哦', content='<p><font size="6">本学期第四次看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真他妈精神</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">明天就回家了好开心</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如“孩子是祖国的明天”。</span></font></p><p><br></p>'))
    db.session.add(Lemma(title='分工-张芳淋-前端设计与实现，配置运行环境', content='<p><font size="6">本学期第四次看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真他妈精神</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">明天就回家了好开心</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如“孩子是祖国的明天”。</span></font></p><p><br></p>'))
    db.session.add(Lemma(title='苏庭轩-分工-前端实现与后台开发', content='<p><font size="6">本学期第四次看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真他妈精神</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">明天就回家了好开心</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如“孩子是祖国的明天”。</span></font></p><p><br></p>'))
    db.session.add(Lemma(title='刘中琦-分工-数据库设计、后台数据库操作', content='<p><font size="6">本学期第四次看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真他妈精神</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">明天就回家了好开心</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如“孩子是祖国的明天”。</span></font></p><p><br></p>'))
    db.session.add(Lemma(title='楚竣棋-后台逻辑设计与实现，服务器管理与维护-分工', content='<p><font size="6">来看日出</font></p><p><font size="4"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size="6">打代码真开心</font></p><p><font size="4"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size="6">我爱软件架构</font></p><p><font size="4"><span>明天的意思是今天的第二天；也泛指未来、希望，如“孩子是祖国的明天”。</span></font></p><p><br></p>'))
    db.session.commit()
    return jsonify(error=False)
