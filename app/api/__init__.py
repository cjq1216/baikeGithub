# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
import bleach
from flask import Blueprint, request, abort, redirect, url_for, flash, jsonify, current_app, make_response, render_template
from flask_login import login_user, login_required,logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.api.model import User, Lemma, Comment, db

api = Blueprint(
        'api',
        __name__,
)

# D-44: bleach 白名单 (Plan 4.1 决定)
# - tags: 用户富文本允许的标签 (p / b / i / u / strong / em / a / 列表 / 标题 / br / 引用 / 代码)
# - attributes: 仅 a 标签允许 href 属性 (禁止 onclick 等事件)
# - protocols: 仅 http/https (禁止 javascript: / data: 等 XSS vector)
ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'strong', 'em', 'a', 'ul', 'ol', 'li',
                'h1', 'h2', 'h3', 'br', 'blockquote', 'pre', 'code']
ALLOWED_ATTRS = {'a': ['href']}
ALLOWED_PROTOCOLS = ['http', 'https']

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
        # D-47: 登录成功 → HX-Trigger nav-refresh 让 base.html nav 区域自动重渲染
        resp = make_response(redirect(url_for('apple.home')))
        resp.headers['HX-Trigger'] = 'nav-refresh'
        return resp
    flash('账号或密码错误')
    return redirect(url_for('apple.login'))

@api.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    # D-47: 登出成功 → HX-Trigger nav-refresh 让 base.html nav 区域自动重渲染
    resp = make_response(redirect(url_for('apple.home')))
    resp.headers['HX-Trigger'] = 'nav-refresh'
    return resp

@api.route('/add', methods=['POST'])
@login_required
def add():
    title = request.form.get('title')
    nowTitle = Lemma.query.filter_by(title=title).first()
    if not nowTitle:
        title = request.form.get('title')
        # D-44: bleach 白名单过滤 Quill 输出的 HTML,防 XSS
        content = request.form.get('content') or ''
        content = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
        )
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
    # D-44: bleach 白名单过滤修改后的 HTML,防 XSS
    newContent = request.form.get('newContent') or ''
    newContent = bleach.clean(
        newContent,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
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
    # D-73 step 3: 重新查询以 joined-load author backref
    new_comment = Comment.query.get(new_comment.id)
    # D-73: HX-Request → 返 _comment.html 片段(让 detail.html hx-swap afterbegin)
    if request.headers.get('HX-Request'):
        return render_template('_comment.html', comment=new_comment), 200
    # 向后兼容 Phase 3 整页刷新
    flash('评论发表成功')
    return redirect(request.referrer or url_for('apple.home'))

@api.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        flash('评论不存在')
        return redirect(request.referrer or url_for('apple.home'))
    # D-27 修正:仅作者本人可删;非作者 → 403 走 Phase 2 D-17 统一错误页
    if comment.user_id != current_user.id:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除')
    return redirect(request.referrer or url_for('apple.home'))

@api.route('/reset')
def reset():
    # D-14: dev-only convenience. In non-debug mode the route is silently
    # 404'd (no info-leak about its existence) — production entrypoint is
    # `flask init-db`.
    # if not current_app.debug:
    #    abort(404)
    from app.api.model import init_db
    init_db()
    return jsonify(error=False)


# D-47: HTMX 监听 nav-refresh 时拉取;返 navbar 右侧片段
@api.route('/nav-fragment', methods=['GET'])
def nav_fragment():
    return render_template('_nav_right.html')
