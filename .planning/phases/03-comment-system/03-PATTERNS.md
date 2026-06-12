# Phase 3: Comment System - Pattern Map

**Mapped:** 2026-06-12
**Files analyzed:** 5 (1 new route block + 4 modified touchpoints)
**Analogs found:** 5 / 5 (all touchpoints have close role-match in Phase 2 admin blueprint or existing api/routes)

## Reused Phase 2 Patterns

以下 Phase 2 模式在 Phase 3 继续复用,本文件不重复全文,详见 `D:\work\baike\.planning\phases\02-security-auth-hardening\02-PATTERNS.md`:

- **`@admin_required` 装饰器** (02-PATTERNS.md L11-25 / `app/api/admin.py:11-25`) — 新 `admin.delete_comment` 路由直接 `from app.api.admin import admin_required` 套用,Phase 2 已固化为 admin 蓝图成员
- **`admin` 蓝图** (02-PATTERNS.md L8 / `app/api/admin.py:8`) — `admin = Blueprint('admin', __name__)`,新路由直接 `@admin.route(...)` 注册
- **`url_for` 跨蓝图约定** (02-PATTERNS.md L509-515) — 永远写 `apple.<endpoint>` / `api.<endpoint>` / `admin.<endpoint>`,**不**写 `user.<endpoint>`(Blueprint name 是 `apple`)
- **CSRF `{{ csrf_token() }}` 模板函数** (02-PATTERNS.md L364-405) — 所有新 `<form>` 在第一个真实 input 之前插入 `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- **`flash` + `redirect(url_for('apple.<endpoint>'))` 错误反馈** (02-PATTERNS.md L492-498) — 既有风格继续使用,HTML 优先
- **`db.session.delete()` + `db.session.commit()` 硬删除事务** (02-PATTERNS.md L517-523 / `app/api/admin.py:35-36`) — admin.delete_lemma 已示范,admin.delete_comment 直接套用
- **`@login_required` 装饰器** (02-PATTERNS.md L479-490) — 作者删除评论和发布评论都需要
- **`current_user.is_authenticated` 模板检查** (02-PATTERNS.md L500-507) — Phase 2 D-22 已统一用 `is_authenticated`,**不**用 `is_active`
- **统一错误页** (02-PATTERNS.md L94-137 / `app/__init__.py` errorhandler) — `abort(403)` 走 Phase 2 D-17 统一 403 错误页,匿名 POST 走 401
- **`init_db()` 模块函数** (02-PATTERNS.md L260-285 / `app/api/model.py:61-76`) — D-26 新增 `user_id` 列后,`init_db()` 自动覆盖,**不**改函数逻辑

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/api/model.py` (modify) | model | CRUD | (self) `User` / `Lemma` 类 | exact |
| `app/api/__init__.py` (modify) | blueprint | request-response | (self) `modify` (L67-79) / `add` (L50-65) / 注释的 `commen` (L82-91) | exact |
| `app/api/admin.py` (modify) | blueprint | request-response | (self) `delete_lemma` (L28-38) | exact |
| `app/route/user.py:detail` (modify) | blueprint | request-response | (self) `search` (L29-37) — 模板传参模式 | exact |
| `app/templates/detail.html` (modify) | template | render | (self) admin 删 lemma 内嵌 form 块 (L77-82) / modify form CSRF 块 (L50-51) | exact |

## Pattern Assignments

### `app/api/model.py` (model, CRUD) — MODIFY

**Analog:** 自身 `User` 类 (L9-23) 和 `Lemma` 类 (L25-38)

**User 模型改造 — 新增 `comments` 关系** (D-26,需在 `is_admin` 字段后追加):

现有 `User` (L9-23):
```python
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
```

需追加:
```python
from sqlalchemy.orm import backref

# 在 User 类内,is_admin 字段后:
comments = db.relationship(
    'Comment',
    backref=backref('author', lazy='joined'),
    cascade='all, delete-orphan',
)
```

`lazy='joined'` 在访问 `comment.author` 时自动 JOIN,避免 N+1 (CD-05)。
`cascade='all, delete-orphan'` 让 User 删除时级联清掉评论 — 与 Lemma 方向对称,避免 FK 悬空。

**Lemma 模型改造 — 补 cascade** (D-33,`comments` 关系行):

现有 (L31):
```python
comments = db.relationship('Comment', backref='lemmas', lazy='dynamic')
```

改为:
```python
comments = db.relationship(
    'Comment',
    backref='lemmas',
    lazy='dynamic',
    cascade='all, delete-orphan',
)
```

`backref='lemmas'` 与 `Comment` 端的 `lemma_id` FK 自动构成双向关系。`cascade='all, delete-orphan'` 让 admin 删 lemma (Phase 2 D-22) 时 SQLAlchemy 自动级联删评论,避免 500 错误。

**Comment 模型完整重写** (D-26, D-32, D-33, D-34 — L40-58 整段替换):

现有 (L40-58):
```python
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
```

改为 (D-26 删 user_name + D-26 加 user_id FK + D-32 content 保持 String(320) + D-34 修 __init__/__str__ bug):
```python
class Comment(db.Model):
    __tablename__ = 'comment'
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
        # 注意:不写 self.time,保留 column default
```

**关键修正点 (D-34):**
- 删 `self.user_name = current_user`(赋了 User 对象到字符串列,会 TypeError)
- 改 `self.lemma_title = lemma_title` 为 `self.lemma_id = lemma_id`
- 删 `self.time = datetime.now()`(覆盖 column default,所有评论时间戳相同;`time` 用 `default=datetime.datetime.utcnow` 自动填充)
- `__str__` 用 `self.content` 前 20 字(不再引用不存在的 `self.title`)

**`init_db()` 不动** (D-26 follow Phase 2 D-02 既有 reset 路径):D-26 加新 `user_id` 列后,`init_db()` 的 `db.drop_all() + db.create_all() + 灌种子` 自动覆盖。Phase 3 不修改 `init_db()` 函数体。

---

### `app/api/__init__.py` (blueprint, request-response) — MODIFY

**Analog:** `modify` 路由 (L67-79) — POST 业务流 + flash + 302 redirect 模板;`add` 路由 (L50-65) — `@login_required` + 业务校验 + flash + redirect 模板;被注释的 `commen` 旧路由 (L82-91) — 替换为实装的 `/api/comment`

**修改点 1:解注释 + 修 typo + 实装 `POST /api/comment`** (D-35,L82-91 整段替换为):

被注释的旧代码 (L82-91) — 删除:
```python
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
```

替换为 (D-35,基于 `modify` 模式 L67-79 + 修 typo `/api/commen` → `/api/comment`):
```python
@api.route('/comment', methods=['POST'])
@login_required
def comment():
    lemma_id = request.form.get('lemma_id')
    content = request.form.get('content', '').strip()
    # CD-06: 1-320 字符校验,空内容拒收
    if not content or len(content) > 320:
        flash('评论内容不能为空且不超过 320 字符')
        return redirect(request.referrer or url_for('apple.home'))
    # CD-07: lemma_id 不存在则回 home
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
    return redirect(request.referrer or url_for('apple.detail'))
```

**关键修正点:**
- 路由路径从 `/commen` (typo) 改为 `/comment`
- 入参从 `commentcontent` 改为 `content`(对齐 detail.html 内联 form 的 `<textarea name="content">`)
- 删 `user_name = current_user` 反模式,改用 `user_id=current_user.id`(D-26 schema)
- 删 `lemma_id =`(语法错误占位符),从 `request.form.get('lemma_id')` 取
- 删 `self.time = datetime.now()` 写法,模型层 column default 处理
- `comment` 函数名替换 `commen` 错拼写

**修改点 2:新增 `POST /api/comment/<int:comment_id>/delete` — 作者删除** (D-27 修正版,放在 modify 路由后、reset 路由前):

基于 `modify` 模式 (L67-79) + `@login_required` 装饰器 (`add` L50-65):
```python
@api.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        flash('评论不存在')
        return redirect(request.referrer or url_for('apple.home'))
    # D-27 修正:作者本人可删(非作者 → 403 走 Phase 2 D-17 统一错误页)
    if comment.user_id != current_user.id:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除')
    return redirect(request.referrer or url_for('apple.home'))
```

**关键点:**
- **不**带 `@admin_required`(admin 删评论走 `admin` 蓝图,见下一节)
- 函数内 `user_id != current_user.id` 双保险,即使装饰器被绕过也守住作者权限
- `abort(403)` 走 Phase 2 D-17 统一 403 错误页

---

### `app/api/admin.py` (blueprint, request-response) — MODIFY

**Analog:** `delete_lemma` 路由 (L28-38) — admin 蓝图下"查询 → flash-not-found → 删除 → flash-success → redirect"模板

**修改点:新增 `POST /api/admin/comment/<int:comment_id>/delete`** (D-41,在 `delete_lemma` 后追加):

基于 `delete_lemma` (L28-38) — `@admin_required` + `query.get()` + `delete` + `commit` + flash + redirect 模式:
```python
@admin.route('/comment/<int:comment_id>/delete', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        flash('删除失败！评论不存在')
        return redirect(request.referrer or url_for('apple.home'))
    db.session.delete(comment)
    db.session.commit()
    flash('删除成功！')
    return redirect(request.referrer or url_for('apple.home'))
```

需在文件顶部 import 行 (L6) 补充 `Comment`:
```python
from app.api.model import Lemma, Comment, db
```

**与 `delete_lemma` 的一致性:**
- 同样的 `@admin_required` 装饰器(Phase 2 D-20 已固化)
- 同样的 `query.get() is None → flash → redirect` 兜底
- 同样的 `db.session.delete() + commit` 硬删除
- 同样的 flash 中文文案风格("删除成功!" / "删除失败！...")

**与 `api` 蓝图 `delete_comment` 的差异:**
- 走 `admin` 蓝图(URL 前缀 `/api/admin`),权限装饰器不同
- admin 不需要函数内作者校验(装饰器已保证 admin 通行)
- 模板跳转用 `url_for('admin.delete_comment', comment_id=comment.id)`

---

### `app/route/user.py:detail` (blueprint, request-response) — MODIFY

**Analog:** `search` 路由 (L29-37) — 模板渲染 + 多变量传入

**修改点:detail 路由函数体补 `comments` 查询** (D-39,L39-46 整段替换):

现有 (L39-46):
```python
@user.route('/detail', methods=['POST'])
def detail():
    entirelytitle = request.form.get('linklist')
    fullcontent = Lemma.query.filter_by(title = entirelytitle).all()
    if not fullcontent:
        flash('所查词条不存在')
        return redirect(url_for('apple.home'))
    return render_template('detail.html', fullcontent=fullcontent)
```

改为 (D-39 — D-40 时间戳按 desc 倒序,CD-05 N+1 由 model `lazy='joined'` 自动防):
```python
@user.route('/detail', methods=['POST'])
def detail():
    entirelytitle = request.form.get('linklist')
    fullcontent = Lemma.query.filter_by(title = entirelytitle).all()
    if not fullcontent:
        flash('所查词条不存在')
        return redirect(url_for('apple.home'))
    # D-39: 传 comments 给模板;按时间倒序(D-40 绝对时间戳展示)
    comments = Comment.query.filter_by(lemma_id=fullcontent[0].id).order_by(Comment.time.desc()).all()
    return render_template('detail.html', fullcontent=fullcontent, comments=comments)
```

**关键点:**
- `fullcontent[0].id` — 既有用法,Phase 3 沿用
- `.order_by(Comment.time.desc())` — D-40 倒序展示(最新评论在前)
- `Comment` 已在 L4 import,无需新增

---

### `app/templates/detail.html` (template, render) — MODIFY

**Analog:** admin 删 lemma 内嵌 form 块 (L77-82) — `<form action="..." method="post" style="display:inline">` + csrf_token hidden input 模式

**修改点 1:评论循环字段名修正** (D-38,L89 一行):

现有 (L89):
```html
<h4>{{ comment.name }}</h4>
```

改为 (D-38 — 走 D-26 的 `backref='author'` 关系):
```html
<h4>{{ comment.author.name }}</h4>
```

**修改点 2:评论卡片底部加删除 form** (D-31,在 L94-96 `comment-footer` 内/下方追加 admin 和 author 各自的 form):

参照 admin 删 lemma 内嵌 form (L77-82):
```html
<div class="comment-footer">
    <p>{{ comment.time.strftime('%Y-%m-%d %H:%M') }}</p>
    {% if current_user.is_authenticated and current_user.is_admin %}
    <form action="{{ url_for('admin.delete_comment', comment_id=comment.id) }}" method="post" style="display:inline" onsubmit="return confirm('确定删除这条评论?');">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <button class="btn btn-xs btn-danger" type="submit">删除</button>
    </form>
    {% endif %}
    {% if current_user.is_authenticated and comment.user_id == current_user.id %}
    <form action="{{ url_for('api.delete_comment', comment_id=comment.id) }}" method="post" style="display:inline" onsubmit="return confirm('确定删除这条评论?');">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <button class="btn btn-xs btn-danger" type="submit">删除</button>
    </form>
    {% endif %}
</div>
```

**关键点:**
- D-30: 浏览器原生 `confirm()` 二次确认,加在 `onsubmit` 属性上
- CD-09: 同一行两个 form,各管各端点(避免前端逻辑复杂度)
- 时间戳显示 D-40: `{{ comment.time.strftime('%Y-%m-%d %H:%M') }}`
- 模板 `comment.user_id` 访问模型字段;`current_user.id` Flask-Login 标准

**修改点 3:替换 jQuery 模态框为内联评论 form** (D-37,L107-130 整段替换,L143-155 内的 jQuery `sendComment`/`out` 触发逻辑删除):

现有 jQuery 模态框 (L107-130):
```html
<div style="display:none;top:15%;left:40%;position:absolute;width:600px; height:25%; background-color:#ccc; z-index:999" id="out">
    <div class="container">
        <div class="row">
            <div class="col-xs-12" style="padding-top:30px;">
                <form class="form-signin" role="form" action="/api/commen", method="post">
                    <input style="width:570px" type="text" class="form-control" name="commentcontent" placeholder="您说～" required autofocus>
                    <br />
                    {% with messages = get_flashed_messages() %}
                    ...
                </form>
            </div>
        </div>
    </div>
</div>
```

替换为 (D-37,放在 L84 `comment-container` **上方**,即 L83 后插入):
```html
{% if current_user.is_authenticated %}
<div class="comment-form-container">
    <form action="/api/comment" method="post" class="form-signin">
        <input type="hidden" name="lemma_id" value="{{ fullcon.id }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <textarea name="content" maxlength="320" required class="form-control" rows="3" placeholder="您说～"></textarea>
        <button class="btn btn-primary" type="submit">发布评论</button>
    </form>
</div>
{% endif %}
```

**关键点:**
- 路由 `/api/commen` → `/api/comment`(对齐后端修 typo)
- 入参 `commentcontent` → `content`(对齐后端 D-35 改的字段)
- 移除 jQuery 模态触发:`$("#sendComment").click(...)` 和 `$("#out").show()` 全部删除
- 删除 `<button id="sendComment">` (L71) — 已无对应模态框
- `{% if current_user.is_authenticated %}` 包裹 — 匿名用户整段不渲染
- D-37: 位置在评论列表**上方**(顶部优先填,保留既有 jQuery 模态弹出位置语义)

**修改点 4:删除 jQuery 触发逻辑** (L143-155 内的 jQuery 代码 — 在 L155 `$("#sendComment").click` 段整段删除):

需删除的 jQuery 代码 (L153-155):
```javascript
$("#sendComment").click(function(){
    $("#out").show();
})
```

以及 L71 的 `<button class="btn btn-lg btn-primary btn-block" type="button" id="sendComment">发布评论</button>`(整行删除)。

**修改点 5:admin 删 lemma 按钮位置保持不变** (L77-82):Phase 2 D-22 已就位,Phase 3 不动。

---

## Shared Patterns

### `url_for` 跨蓝图约定 (Phase 2 已锁定)
**Source:** `app/api/admin.py:34,38`; `app/route/user.py:37,45`
**Apply to:** Phase 3 所有新 redirect
```python
return redirect(url_for('apple.home'))           # 页面蓝图(注意 name='apple')
return redirect(url_for('apple.detail'))         # 评论发布后回 detail 页(D-35)
return redirect(url_for('admin.delete_comment', comment_id=comment.id))  # admin 删评论
return redirect(url_for('api.delete_comment', comment_id=comment.id))    # 作者删评论
```

### 内嵌 form + CSRF + 二次确认(评论卡片删除)
**Source:** `app/templates/detail.html:77-82` (admin 删 lemma 模式)
**Apply to:** 每条评论卡片的 admin 删除 form + 作者删除 form
```html
<form action="{{ url_for('admin.delete_comment', comment_id=comment.id) }}" method="post" style="display:inline" onsubmit="return confirm('确定删除这条评论?');">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <button class="btn btn-xs btn-danger" type="submit">删除</button>
</form>
```

### `@admin_required` 装饰器复用
**Source:** `app/api/admin.py:11-25`
**Apply to:** 新 `admin.delete_comment` 路由
```python
from app.api.admin import admin_required

@admin.route('/comment/<int:comment_id>/delete', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    ...
```

### POST 业务流:`query.get()` → `delete` → `commit` → `flash` → `redirect`
**Source:** `app/api/admin.py:28-38` (delete_lemma)
**Apply to:** admin 删评论 + 作者删评论(后者加 user_id 校验)
```python
comment = Comment.query.get(comment_id)
if comment is None:
    flash('...不存在')
    return redirect(...)
db.session.delete(comment)
db.session.commit()
flash('...成功!')
return redirect(...)
```

### `@login_required` + `current_user.id` 作者校验
**Source:** `app/api/__init__.py:67-68` (modify 路由) + `app/route/user.py:3` (current_user import)
**Apply to:** 作者删除评论路由
```python
@api.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        abort(404)
    if comment.user_id != current_user.id:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    return redirect(...)
```

### 模板 `current_user.is_authenticated` 检查
**Source:** `app/templates/detail.html:77` (admin 块), `app/templates/add.html:29` (登录导航)
**Apply to:** 评论发布 form 包裹 + 评论删除按钮条件渲染
```html
{% if current_user.is_authenticated %}
    <form action="/api/comment" ...>...</form>
{% endif %}

{% if current_user.is_authenticated and comment.user_id == current_user.id %}
    <button>删除</button>
{% endif %}
```

### `Comment.user_id` 关联 `User.name` 渲染(走 backref='author')
**Source:** 现有 `app/api/model.py:31` (Lemma.comments backref='lemmas') 模式;Phase 3 在 User 侧新增 `backref=backref('author', lazy='joined')`
**Apply to:** 模板 `{{ comment.author.name }}` (D-38 改字段名)
```python
# model 端(User 类内):
comments = db.relationship('Comment', backref=backref('author', lazy='joined'), cascade='all, delete-orphan')
```
```html
<!-- template 端 -->
<h4>{{ comment.author.name }}</h4>
```

### `Lemma.comments` cascade='all, delete-orphan' 防 FK 500
**Source:** `app/api/model.py:31` (现有 Lemma.comments)
**Apply to:** admin 删 lemma (Phase 2 D-22) 自动级联删该词条下所有评论
```python
comments = db.relationship('Comment', backref='lemmas', lazy='dynamic', cascade='all, delete-orphan')
```

## No Analog Found

Phase 3 5 个 touchpoint 全部有 Phase 2 / 既有代码可参考,无新增空白领域。

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | All Phase 3 touchpoints have role-match or exact analogs in Phase 2 (admin blueprint) or existing api/routes/templates |

## Metadata

**Analog search scope:** `app/api/admin.py`、`app/api/__init__.py`、`app/api/model.py`、`app/route/user.py`、`app/templates/detail.html`(重点),Phase 2 PATTERNS.md 全文
**Files scanned:** 5 (3 Python source, 1 blueprint file, 1 template)
**Pattern extraction date:** 2026-06-12
**Reuse rate:** 5 / 5 = 100% touchpoints have close analog(Phase 2 admin blueprint + 既有 api routes)
