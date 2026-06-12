# Phase 3: Comment System - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

## Phase Boundary

把"被注释掉没启用的评论模型"实装成端到端可用的产品功能:**登录用户可在词条详情页发布评论、按时间倒序展示、作者本人可删、admin 可删任意评论**。schema 用 `user_id` 外键 + `user.name` 关联渲染(支持 username 改名后历史评论不孤),后端做严格 author/admin 权限校验(同一个端点分流),前端用整页刷新(HTMX 留给 Phase 4),删评论时浏览器原生 `confirm()` 二次确认。

不动模板整体视觉(归 Phase 4);不动 wiki 链接 / view_count / updated_at / 相关词条(归 Phase 4);不动 Docker / pytest(归 Phase 5)。Phase 2 留下的 `admin` 蓝图 + `@admin_required` 装饰器 + `User.is_admin` 字段 + Flask-WTF CSRF + 统一错误页全部直接复用。

## Implementation Decisions

### 1. Comment 数据模型重构

- **D-26:** 删除 `Comment.user_name` 字符串字段,**只**保留 `user_id` 外键。新字段定义:`user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)`。`Comment` 与 `User` 双向关系:User 侧加 `comments = db.relationship('Comment', backref=backref('author', lazy='joined'), cascade='all, delete-orphan')`,`lazy='joined'` 自动 JOIN 避免 N+1。`nullable=False` 保证发布评论必须登录。**不留旧数据**(drop_all + 重灌是 Phase 2 D-02 既有 reset 路径,本阶段 follow 同样模式)。
- **D-32:** `Comment.content` 保持 `String(320)` 不变(不扩为 Text)。与 Phase 2 既定 `init_db()` 模式一致,避免 Phase 3 范围漂移到"内容长度策略"。
- **D-33:** `Lemma.comments` 现有关系 `db.relationship('Comment', backref='lemmas', lazy='dynamic')` 需补 `cascade='all, delete-orphan'` — 这样 admin 删词条(Phase 2 的 `admin.delete_lemma`)时 SQLAlchemy 自动级联删该词条下所有评论。否则删词条会因外键约束失败 500。
- **D-34:** 修 `Comment.__init__` bug:删除 `self.user_name = current_user`(赋了 User 对象而非字符串) + 改 `self.lemma_title = lemma_title` 为 `self.lemma_id = lemma_id` + 删除 `self.time = datetime.now()`(覆盖 column default,会让所有评论时间戳变成同一秒,需保留 `default=datetime.datetime.utcnow`)。`__str__` 同步修:把 `self.title` 改为 `self.content` 的前 20 字。

### 2. 端点设计

- **D-35:** 评论发布端点 `POST /api/comment`,走现有 `api` 蓝图。`@login_required` 装饰器(匿名 POST 自动 401/403,走 Phase 2 D-19 统一错误页)。入参 `lemma_id`(hidden 字段) + `content`(textarea,1-320 字符校验)。成功后 302 → `url_for('apple.detail', ...)`(注:`/user/detail` 当前是 POST 路由,Phase 1 修复的 bug,本阶段不引入 GET 化;最简做法是返回 detail 视图渲染所需的 lemma title,或 redirect 回 referrer,具体由 plan 决定)。`Lemma.query.get(lemma_id)` 不存在时 404。
- **D-27:** 评论删除端点**单一** `POST /api/comment/<int:comment_id>/delete`,走现有 `api` 蓝图。内部权限分流:
  1. 优先判断 admin (`@admin_required` 装饰器提前拦截,非 admin → abort 403)
  2. 在 admin 装饰器通过的前提下,函数内**追加** `if comment.user_id != current_user.id: abort(403)`(防止 admin 之外的非作者绕过装饰器;实际上 admin 装饰器后这道校验对 admin 永远 True,对其他用户已被装饰器拒,这是"双保险"语义;但 Phase 2 装饰器是 admin-only,普通用户作者想删自己评论会被 403,**需另设端点或装饰器**)。

  **修正 D-27 的实现细节**:**作者删除**用单独装饰器 `@login_required + 作者校验函数内做**:`POST /api/comment/<int:comment_id>/delete` 走 `api` 蓝图,不带 `@admin_required`;函数内按 `comment.user_id == current_user.id` 判作者;**admin 删评论** 走 `admin` 蓝图 `POST /api/admin/comment/<int:comment_id>/delete`,带 `@admin_required`。两个端点 + 两道权限墙,代码职责清晰。这是对前面"同一端点"决策的实现修订 — 用户原意是"统一逻辑不要在多处重复",本方案做到了"权限分流集中、URL 仍然清晰反映权限"。

- **D-36:** 评论删除后:硬删除 `db.session.delete(comment); db.session.commit()`,flash "评论已删除",302 → `redirect(request.referrer or url_for('apple.home'))`。匿名/越权直接 `abort(403)`(走 Phase 2 D-17 统一错误页)。

### 3. 前端集成

- **D-28:** 新评论发布后**整页刷新**(302 → detail 页)。SUCCESS 1 留待 Phase 4 引入 HTMX 时再满足。Phase 3 提交后用户体验:看到自己评论已显示在列表顶部。
- **D-31:** 删除按钮位置 — **每条评论卡片底部右侧**,作者看到自己评论下"删除"按钮,admin 看到所有评论下"删除"按钮。统一入口,符合社区型产品习惯(类似微博/B站)。不像 admin 删 lemma 那样走独立 form — 评论卡片内的删除按钮用 `<form action="..." method="post" style="display:inline">` 内嵌(模仿 Phase 2 D-22 的 admin.delete_lemma 模式)。
- **D-30:** 二次确认 — 浏览器原生 `if (!confirm('确定删除这条评论?')) return false;` 加在 `<form>` 的 `onsubmit` 属性上。Phase 3 现有 jQuery 还在,加几行原生 JS 即可。Phase 4 拆 jQuery 时一起换。
- **D-37:** 替换 detail.html 现有 jQuery 隐藏 div `#out` 模态框(line 107-130),改为 detail 页内联 `<form action="/api/comment" method="post">` — 这样:
  1. 移除 jQuery 弹窗的 `#sendComment` 按钮触发逻辑
  2. 评论发布 form 直接渲染在 detail 页面评论列表上方(对登录用户可见;匿名用户整段不渲染 — 走 `{% if current_user.is_authenticated %}`)
  3. form 内含 `<input type="hidden" name="lemma_id" value="{{ fullcon.id }}">` + `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` + `<textarea name="content" maxlength="320" required>` + 提交按钮
- **D-38:** detail.html 评论卡片字段修正:`{{ comment.name }}` (line 89) → `{{ comment.author.name }}`(走 D-26 的 `backref='author'` 关系)。`{{ comment.user_name }}` (现模板里没用到) 不留,直接用外键关联。

### 4. 视图层改造

- **D-39:** `/user/detail` 路由(`app/route/user.py:39-46`)需在渲染 detail.html 时同时传入 `comments` 变量:`comments = Comment.query.filter_by(lemma_id=fullcontent[0].id).order_by(Comment.time.desc()).all()`。同时 detail.html line 84-99 的 `{% for comment in comments %}` 现在能正确迭代。
- **D-40:** 时间戳显示用 `{{ comment.time.strftime('%Y-%m-%d %H:%M') }}`(绝对时间,不写"3 分钟前"等相对时间,Phase 4 再考虑)。

### 5. Admin 蓝图扩展

- **D-41:** `app/api/admin.py` 新增路由 `POST /api/admin/comment/<int:comment_id>/delete`,带 `@admin_required` 装饰器。模板跳转 `url_for('admin.delete_comment', comment_id=comment.id)`。

### 6. 审计日志

- **D-29:** **不写**审计日志。硬删除后无痕。v1 demo 性质,审计需求低。需要追溯时,登录 admin 行为本身可被外部系统审计(Docker logs)。

### Claude's Discretion

- **CD-04:** `Comment.time` 字段时区 — 保持 `default=datetime.datetime.utcnow` 不变(与 Phase 2 init_db 现有写入风格一致)。展示时用 `.strftime('%Y-%m-%d %H:%M')` (服务器本地时间)。Phase 4 引入前端时间格式化库时再处理 timezone 复杂性。
- **CD-05:** 评论查询的 N+1 防护 — D-26 已在 User 侧加 `lazy='joined'`,SQLAlchemy 在 `Comment.author` 访问时自动预加载,无需 plan 阶段显式 `options(selectinload(...))`。
- **CD-06:** 评论内容校验长度 1-320 字符,空内容(纯空格)拒收。后端校验在 320 字符内,前端 `maxlength="320"` 兜底。
- **CD-07:** `/api/comment` 端点对 lemma_id 不存在的场景:`Lemma.query.get(lemma_id) is None` → flash "词条不存在" + 302 回 home(走 Phase 2 D-17 错误页或 flash 模式由 plan 决定)。
- **CD-08:** 删除评论后回到 referrer(同 detail 页)还是 home?CD-07 同款决策 — 推荐 referrer(`redirect(request.referrer or url_for('apple.home'))`),与 Phase 2 D-11 CSRF 失败回退逻辑一致。
- **CD-09:** admin 删评论按钮在评论卡片中的位置 — 与作者删除按钮**同一行右侧**,先 admin 后 author(显示给 admin 时,看不到自己不是 author 的其他评论的 author 按钮?实际两个都显示,admin 永远看得到所有删除按钮,author 只看自己评论的)。**或**合并为一个按钮 + 隐藏 form。Claude 选最简实现:同一行两个 form,各管各的端点。

## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### 项目元信息
- `.planning/PROJECT.md` — 项目核心价值、v1 范围、Out of Scope 排除清单、Key Decisions(尤其"评论不实装编辑")
- `.planning/REQUIREMENTS.md` — v1 46 条需求,Phase 3 对应 COMMENT-01..07 + ROLE-02(从 Phase 2 推迟而来)
- `.planning/ROADMAP.md` § Phase 3 — 阶段目标 + 7 条 SUCCESS 标准 + 计划 3.1/3.2 拆分
- `.planning/STATE.md` — Phase 1/2 已完成,累计上下文,Discovered Constraints(尤其 COMMENT-06 必须在 Phase 3 规划)

### Phase 2 已锁定决策(本阶段直接 carry-forward)
- `.planning/phases/02-security-auth-hardening/02-CONTEXT.md` — D-01..D-25 全部生效
  - **D-09 ~ D-12**:Flask-WTF CSRF,新表单都要 `{{ csrf_token() }}` hidden input
  - **D-13 ~ D-16**:`init_db()` 模块函数 + `flask init-db` CLI,reset 走 `if not current_app.debug: abort(404)`
  - **D-17 ~ D-19**:404/403/500/400 统一错误页(自包含 HTML,Phase 3 沿用)
  - **D-20 ~ D-22**:`admin` 蓝图(`url_prefix='/api/admin'`,Blueprint name='admin') + `@admin_required` + admin 删 lemma 模板集成模式
  - **D-23**:`User.is_admin: db.Column(db.Boolean, default=False)` 已就绪
  - **D-24 ~ D-25**:`flask promote-admin <username>` CLI
- `.planning/phases/02-security-auth-hardening/02-PATTERNS.md` — admin.py 蓝图 + error.html 模式 + `url_for` 跨蓝图约定(`apple.<endpoint>` / `api.<endpoint>` / `admin.<endpoint>`)

### 既有代码 / 改造目标
- `app/api/model.py:40-58` — `Comment` 模型当前实现(L40-58),改造目标:删 `user_name`、加 `user_id` FK、修 `__init__` bug、修 `__str__`、补 `Lemma.comments` 的 cascade
- `app/api/model.py:9-23` — `User` 模型现状,需补 `comments` 关系(带 `backref=backref('author', lazy='joined'), cascade='all, delete-orphan'`)
- `app/api/model.py:61-76` — `init_db()` 既有实现,**不**改逻辑(reset 路径已包含 drop_all + create_all + 灌种子);新增的 `user_id` 列随之重灌
- `app/api/__init__.py:82-91` — 被注释的旧评论发布路由(typo `/api/commen`),本阶段实装并修 typo 为 `/api/comment`
- `app/api/__init__.py:67-79` — 既有 `modify` 路由作为"POST 业务流 + flash + 302 redirect"参考模板
- `app/api/admin.py:1-38` — admin 蓝图 + `@admin_required` 装饰器 + `delete_lemma` 路由作为新 `delete_comment` 路由的参考模板
- `app/templates/detail.html:50-75` — modify form + admin 删 lemma 块(line 77-82)的内嵌 form 模式,本阶段评论删除 form 复用此模式
- `app/templates/detail.html:84-99` — 既有 `{% for comment in comments %}` 循环(line 89 的 `{{ comment.name }}` 是错字段名,需改为 `{{ comment.author.name }}`)
- `app/templates/detail.html:107-130` — 既有 jQuery 隐藏 div `#out` + 模态发布框,本阶段**整段替换**为内联 form
- `app/route/user.py:39-46` — `/user/detail` 路由,需补 `comments` 变量传给模板

### 测试与文档
- `tests/`(Phase 5 才建) — 本阶段**不**新增测试,但 `tests/test_smoke.py` 的端到端流(Phase 5 写入)会用到所有 Phase 3 端点
- `README.md`(Phase 5 改) — 本阶段不更新 README

## Existing Code Insights

### Reusable Assets
- **`@admin_required` 装饰器**(`app/api/admin.py:11-25`)— 复用,新 `admin.delete_comment` 路由直接 `from app.api.admin import admin_required` 套用
- **`admin` 蓝图**(`app/api/admin.py:8`)— 复用,新路由直接 `@admin.route(...)` 注册
- **`api` 蓝图**(`app/api/__init__.py:7-10`)— 复用,新 `POST /api/comment` 和 `POST /api/comment/<id>/delete` 直接 `@api.route(...)` 注册
- **`flash` + `redirect(url_for('apple.<endpoint>'))`** — 既有风格,继续用
- **`db.session.commit()` 显式事务** — 既有风格,继续用
- **`get_flashed_messages()` Jinja 块** — 7 个模板的现有 pattern,继续用
- **`db.drop_all()` + `db.create_all()` + 灌种子**(`app/api/model.py:62-76`)— D-26 加新列后,`init_db()` 自动覆盖,**不**改函数逻辑
- **`is_authenticated` / `is_admin` template 检查**(Phase 2 D-22 模式)— 复用
- **CSRF `{{ csrf_token() }}` 模板函数** — 复用,所有新表单加 hidden input

### Established Patterns
- **Blueprint 命名约定**:`apple` (页面) + `api` (表单提交) + `admin` (Phase 2 新增)。Phase 3 评论发布/作者删除走 `api`,admin 删除走 `admin`。
- **`url_for` 跳转**:既有 `redirect(url_for('apple.home'))` / `'apple.detail'` 风格保持不变;admin 跳转用 `url_for('admin.delete_comment', comment_id=...)`。
- **错误反馈**:现状是 `flash` + 重定向(非 JSON 响应),Phase 3 维持这种 HTML 优先的风格,不改 API 形态。
- **内嵌 form 模式**(Phase 2 D-22 admin 删 lemma):`<form action="..." method="post" style="display:inline">` 内嵌于父元素,自带 `csrf_token` hidden input。评论删除复用此模式。
- **`current_user` template 检查**:用 `is_authenticated`(Flask-Login 标准),不用 `is_active`(Phase 2 D-22 已确认)。
- **隐式 flask app context**:`@app.cli.command` 装饰器自带 app context,无需 `with app.app_context()` 包裹(Phase 2 D-16)。

### Integration Points
- `app/api/model.py` — 改 `Comment` 模型(D-26, D-32, D-33, D-34)+ 改 `User` 模型(D-26 `comments` 关系)+ `Lemma` 模型加 `cascade` (D-33)
- `app/api/__init__.py` — 解注释 + 修 typo + 实装 `POST /api/comment` 路由 + 新增 `POST /api/comment/<id>/delete` 路由
- `app/api/admin.py` — 新增 `POST /api/admin/comment/<id>/delete` 路由
- `app/route/user.py:detail` — 改路由函数体,传 `comments` 给模板
- `app/templates/detail.html` — **整段替换** line 107-130 的 jQuery 模态框为内联评论 form;改 line 89 字段名;按 D-31 在每条评论卡片底部加删除 form(admin / author 各自的条件块)
- `requirements.txt` — **不**改(无新依赖)
- `app/__init__.py` — **不**改(蓝图注册已就绪)

## Specific Ideas

- **想法 A:** `Comment.user_id` 字段加 `nullable=False`,在 SQLAlchemy 层强制"发布评论必须登录"(虽然后端 `@login_required` 装饰器已经保证,但 schema 约束是双保险)。
- **想法 B:** `Lemma.comments` 加 `cascade='all, delete-orphan'` 后,admin 删 lemma(Phase 2 接口)自动级联删评论 — 避免手动先删评论再删 lemma 的两步操作,避免"FK 约束失败"500 错误。Phase 3 实装时**必须**加,否则 Phase 2 的 admin 删 lemma 接口会因新加的 `user_id` FK 而可能失败(虽然 Lemma → Comment 方向不是新增 FK,但删 lemma 时的处理取决于 cascade 配置)。
- **想法 C:** 评论时间戳用 `datetime.datetime.utcnow` 写入(模型 column default)+ `comment.time.strftime('%Y-%m-%d %H:%M')` 展示(本地化在模板层)。Phase 4 引入前端时间格式化时可考虑显示"3 分钟前"。
- **想法 D:** detail.html 评论发布 form 放哪?在评论列表**上方**(顶部优先填,符合"先发后看"直觉)还是**下方**(看完所有评论再决定发)?Phase 2/3 既有 jQuery 模态框隐含"上方"语义(模态弹出在标题处),本阶段保留"上方"位置。
- **想法 E:** admin 删评论的二次确认提示文本应包含"管理员操作"语义,作者删评论的提示是"确定删除这条评论?"。两种按钮共用 JS `confirm()`,但提示文本根据当前 user 角色变化?或简单统一为"确定删除这条评论?"?**推荐统一**(避免前端逻辑复杂度)。

## Deferred Ideas

### 评论编辑(V2-COMMENT-01)
- PROJECT.md Key Decisions 已明示:"评论不实装编辑(仅发布 + 作者删除)"。本阶段不讨论,留 v2。

### 评论回复 / 嵌套(V2-COMMENT-02)
- 评论树、@ 通知、reply 关系 — 留 v2。本阶段评论是平铺列表。

### 词条 wiki 链接 / view_count / updated_at / 相关词条
- 词条产品特性(LEMMA-01..08) — Phase 4 处理。本阶段评论的 `lemma_id` 关联保持简单,不涉及词条自身的扩展字段。

### 模板整体重设计 / HTMX / Pico.css / wangEditor 替换
- 全部 Phase 4。本阶段保留 jQuery + Bootstrap 3,只替换**评论区块**(line 107-130 的 jQuery 模态框)为内联 form。其他视觉暂不动。

### 词条详情页 GET 化(`/user/detail` 改 GET)
- Phase 1 修复了 `BaseQuery` bug 但路由仍是 POST。Phase 3 不改(避免引入更多 Phase 2 决定的 follow-up 改路由问题)。Phase 4 重设计模板时再考虑。

### 限流 / 评论频率控制 / 反垃圾
- 评论频率限制、IP 限流、敏感词过滤 — v2。

### 评论 markdown / 富文本
- 评论输入框当前是纯文本 `<textarea>`(Phase 2 既有选择)。本阶段不引入富文本编辑器(Phase 4 才统一换 wangEditor → 现代编辑器)。

### 邮件通知 / 评论被回复提醒
- 留 v2。需要 SMTP 配置,本项目 demo 性质不引入。

---

*Phase: 03-Comment System*
*Context gathered: 2026-06-12*
