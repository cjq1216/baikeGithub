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


@api.route('/comment', methods=['POST'])
@login_required
def comment():
    lemma_id = request.form.get('lemma_id')
    content = (request.form.get('content') or '').strip()
    # CD-06: 1-320 字符校验,空内容(纯空格)拒收
    if not content or len(content) > 320:
        flash('评论内容不能为空且不超过 320 字符')
        return redirect(request.referrer or url_for('apple.home'))
    # CD-07: lemma_id 不存在 → flash 词条不存在 + 302 回 home
    lemma = Lemma.query.get(lemma_id)
    if lemma is None:
        flash('词条不存在')
        return redirect(url_for('apple.home'))
    new_comment = Comment(
        user_id=current_user.id,
        lemma_id=lemma_id,
        content=content,
    )
    db.session.add(new_comment)
    db.session.commit()
    flash('评论发表成功')
    return redirect(request.referrer or url_for('apple.home'))

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
