# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
from flask import Blueprint, request, abort, redirect, url_for, flash, jsonify, current_app
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
    # D-14: dev-only convenience. In non-debug mode the route is silently
    # 404'd (no info-leak about its existence) — production entrypoint is
    # `flask init-db`.
    if not current_app.debug:
        abort(404)
    from app.api.model import init_db
    init_db()
    return jsonify(error=False)
