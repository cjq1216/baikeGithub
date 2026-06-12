# Phase 4: Frontend Modernization & Product Features - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

## Phase Boundary

把 7 模板从 jQuery 1.11 + Bootstrap 3 + wangEditor 2.x 升级到 Pico.css (CDN+SRI) + HTMX (CDN+SRI) + Quill 2.x (本地 vendor),并补齐词条产品特性:Lemma 加 `updated_at` + `view_count` 字段、`/user/detail` 改 GET、`[[词条名]]` 双向链接(模板层正则 + 服务端不解析存原文)、不存在的目标走红色虚线 + "(创建此词条) →" 跳转 `/user/add?title=...` 预填、详情页底部"相关词条"区(评论区下方)显示 backlinks。

4 个 HTMX 局部刷新流全部启用(取代 Phase 3 D-28 整页刷新决策):
- 搜索边输边出(`keyup changed delay:300ms`,1 字符起,20 条上限)
- 评论发布不刷新(服务端检测 HX-Request,返回单条新评论 HTML 片段,`hx-swap='afterbegin'`)
- 登录/登出后**手动**重写导航栏右侧状态(hx-swap-oob,不轮询,不需新端点)
- view_count 计数走 **GET 同步 SQL UPDATE 原子**(在 detail 路由中执行,不靠 HTMX)

不动:Docker 化(Phase 5)、pytest smoke(Phase 5)、admin 蓝图与 `@admin_required`(Phase 2)、`User.is_admin`、评论数据模型(Phase 3)。Phase 2/3 已锁定决策全部 carry-forward。

## Implementation Decisions

### 1. 富文本编辑器

- **D-42:** 编辑器选 **Quill 2.x**(WYSIWYG,~200KB,BSD-3,中文 IME 兼容好,产出标准 HTML 子集,迁移心智模型与 wangEditor 2.x 接近)。
- **D-43:** Quill 工具栏 = **精简集**:粗体/斜体/下划线 + 有序/无序列表 + 标题 H1-H3 + 引用 + 链接 + 清除格式。8 个按钮,宽度 ~400px。不含代码块/表格/图片上传/字体/字号/颜色/对齐。
- **D-44:** Quill 输出 HTML 存 DB 前**用 bleach 库白名单过滤**。白名单标签:`p / b / i / u / strong / em / a / ul / ol / li / h1 / h2 / h3 / br / blockquote / pre / code`。`a` 标签要求 `href` 必须以 `http://` / `https://` / `/` 开头,禁止 `javascript:`。增加 `bleach` 到 `requirements.txt`(~50KB)。

### 2. HTMX 局部刷新(覆盖 Phase 3 D-28 决策)

- **D-45:** **搜索边输边出** — `home.html` 搜索框加 `hx-get="/user/search" hx-trigger="keyup changed delay:300ms" hx-target="#results" hx-indicator="#spinner"`。1 字符起即触发(后端判空,空查询不发请求),最多 20 条结果。后端 `/user/search` 端点接受 GET,`q` query 参数,返回搜索结果 HTML 片段(非整页)。
- **D-46:** **评论发布不刷新**(覆盖 Phase 3 D-28) — `detail.html` 评论 form 改 `hx-post="/api/comment" hx-target="#comments" hx-swap="afterbegin" hx-on::after-request="if(event.detail.successful) this.reset()"`.服务端路由 `/api/comment` 检测 `request.headers.get('HX-Request')`,存在时返回单条新增 comment 卡片的 HTML 片段(走 `templates/_comment.html` 子模板,避免 整页 /api/comment 整页返回的 flash 重渲染);HX-Request 不存在时保持 302 redirect(向后兼容 Phase 3 既定的整页刷新行为)。失败(非登录/超长/lemma 不存在)时 `HX-Retarget: #comment-form` + `HX-Reswap: outerHTML` 重写 form 区块 + 内嵌 flash 文本。
- **D-47:** **登录状态手动刷新**(不轮询)— `/api/login` 与 `/api/logout` 路由成功响应里,在重定向的 flash 之外,额外返回 `HX-Trigger: nav-refresh` 事件;`base.html` 导航栏右侧区域用 `hx-get="/api/nav-fragment" hx-trigger="nav-refresh from:body"` 监听,自动重渲染登录/用户名/登出按钮。**不**加 `/api/whoami` 端点,也不每 30s 轮询。多设备场景(用户在另一台设备登出后本机要感知)不在 Phase 4 范围。
- **D-48:** **view_count +1 走 GET 同步 SQL UPDATE**(不靠 HTMX)— `/user/detail` 路由函数体第一行执行:
  ```python
  db.session.execute(update(Lemma).where(Lemma.id == lemma.id).values(view_count=Lemma.view_count + 1))
  db.session.commit()
  ```
  原子,SQL 层 `view_count = view_count + 1`,无 lost-update。作者本人访问也算 +1(产品 demo 不特判)。

### 3. Wiki 链接

- **D-49:** **红色虚线下划线 + 词条标题 + 尾部小字"(创建此词条)→"**。点击跳 `/user/add?title=<URL-encoded>`,`/user/add` 视图读 `request.args.get('title')` 预填到 `title` input。视觉上"红虚线"风格用 `text-decoration: underline dashed red; color: var(--pico-color-red-500);` 加 Pico.css `:hover` 加深。
- **D-50:** **服务端不解析 wiki 链接** — 词条内容原样存 HTML 入 DB(Quill 产出 + bleach 过滤后)。模板层(`detail.html`)做正则替换:`re.sub(r'\[\[([^\[\]\n]+?)\]\]', lambda m: render_wikilink(m.group(1)), content)`,`render_wikilink(title)` 函数预先 `Lemma.query.filter_by(title=title).first()` 判存在,存在 → 蓝链接 `apple.detail`,不存在 → 红色虚线 + "(创建此词条)→" 跳 `apple.add`。模板层实现走 Jinja2 自定义 filter `{% content_with_wikilinks %}` 注册到 app.jinja_env。
- **D-51:** wiki 链接正则 `r'\[\[([^\[\]\n]+?)\]\]'`,**非贪婪 + 不跨行**。避免 `[[a]] [[b]]` 匹配成 `[[a]] [[b]]`(贪婪导致整段)。中文标题不需要额外处理,直接 `title.strip()`。
- **D-52:** 词条内容从 HTML 解析出所有 `[[xxx]]` 一次性生成 backlinks map(`Lemma.query.filter(Lemma.content.contains('[[' + title + ']]'))`),为避免 N+1,wiki 链接替换和 backlinks 各自走单次批量查询。

### 4. 静态资源加载

- **D-53:** **Pico.css + HTMX 走 jsdelivr CDN + SRI 哈希**。版本锁定:`@picocss/pico@2.0.6/css/pico.min.css` + `htmx.org@1.9.10/dist/htmx.min.js`。`base.html` `<head>` 加 `integrity="sha384-..."` 与 `crossorigin="anonymous"`。Phase 5 README 部署文档要写明"需要外网访问 jsdelivr",如果内网部署则改为本地 vendor(README 给出替换步骤)。
- **D-54:** **Quill 2.x 走本地 vendor** 放 `app/static/javascripts/quill/quill.min.js` + `app/static/stylesheets/quill/quill.snow.css`(`snow` 是 Quill 默认带边框工具栏主题)。Phase 2/3 既有本地 vendor 风格延续。
- **D-55:** **删** jQuery 1.11 (`app/static/javascripts/jquery-1.11.3.min.js` + wangEditor 内置的两份 jQuery)、Bootstrap 3 (`bootstrap.min.css` + `bootstrap.min.js` + `bootstrap-theme.min.css` + `docs.min.js` + fonts 目录)、wangEditor (`app/static/javascripts/wangEditor/*` + `app/static/stylesheets/wangEditor/*`)、`style.css`、`mycss/` 下所有 `cover/signin/result/detail/modify/blog.css`。`app/static/stylesheets/mycss/` 目录整体删(改用 Pico.css 主题变量)。

### 5. 模板结构

- **D-56:** **抽取 `base.html`** 共享 `<head>` + nav + flash 块 + 底部 + 暗色切换开关。用 `{% block content %}{% endblock %}` 占位主内容。7 子模板(`home / signin / register / add / modify / result / detail`)全部 `{% extends 'base.html' %}` 改写。`base.html` 自身在 7 子模板的 `{% block content %}` 中填入各自的主内容。
- **D-57:** **手动暗/亮主题切换开关**(navbar 右上角一个图标按钮)。`base.html` 加 `<button id="theme-toggle" aria-label="切换主题">` + 30 行 JS 监听 click,设置 `<html data-theme="dark|light">` + `localStorage.setItem('pico-preferred-color-scheme', value)`。初次加载 JS 读 localStorage 决定 data-theme。Pico.css 自带 `prefers-color-scheme` 暗色变量,直接用。失败时回退到 `prefers-color-scheme: dark` CSS 媒体查询。
- **D-58:** **系统字体栈** — Pico.css 默认 `system-ui, -apple-system, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif`。零体积,跨平台一致。
- **D-59:** **顶部 inline 导航** — Pico.css `<nav>` 容器内横向排列(主页 / 词条 / 写词条 / 登录 / 注册 / 用户名 / 登出)。手机宽度 < 768px 时 Pico.css 自动 wrap 换行,**不**加 hamburger(Phase 4 demo 性质可接受 wrap 视觉)。
- **D-60:** **result.html 词条列表用 Pico.css card grid** — `<div class="grid">` 内每个 lemma 一张 `<article>`,内含 `<header><h3>...</h3></header>` + 截断 content 200 字 + `<footer>` 显示 `view_count` + `updated_at` + "查看 →" 链接。空结果时显示"未找到相关词条"卡片 + "新增词条"按钮跳 `apple.add`。

### 6. Schema / 数据层

- **D-61:** `Lemma` 加两个字段:
  ```python
  updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
  view_count = db.Column(db.Integer, default=0, nullable=False, server_default='0')
  ```
  `view_count` 用 `server_default='0'` 双保险(MySQL 列默认值,即使 `Lemma()` 不传参也能落库)。
- **D-62:** `updated_at` **仅在词条创建/修改时**更新(SQLAlchemy `onupdate=datetime.utcnow` 自动触发)。**评论发布/删除不更新词条时间**(语义:时间代表"词条内容"最后变更,非"该页活动")。
- **D-63:** `view_count` +1 走 SQLAlchemy 2.x 风格 `update(Lemma).where(...).values(view_count=Lemma.view_count + 1)`,**不**走 Python `lemma.view_count += 1`(避免 race condition + 显式 commit)。view_count +1 与 detail 渲染**同一事务**中,失败回滚。
- **D-64:** schema 变更(Lemma 新增 2 列 + 既存数据清空)**走 init_db() drop+create+灌种子**(沿用 Phase 2 D-13..D-16),**不**引入 alembic。Phase 4 demo 性质接受重灌。`init_db()` 函数体不改(自动覆盖新 schema,种子数据按新 model 重建)。
- **D-65:** **`/user/detail` 从 POST 改为 GET**(顺带修) — 路由 `methods=['GET']`,参数从 `request.form.get('newTitle')` 改 `request.args.get('title')`(或 path 参数 `<title>` 二选一,选 `?title=foo` 与既有 query 习惯一致)。`result.html` 每条结果的 `<form action="/user/detail" method="post">` 改 `<a href="{{ url_for('apple.detail', title=lemma.title) }}">`,删除 form 包裹。view_count +1 移到 detail 路由首行(与 D-63 一致)。
- **D-66:** `User.comments` / `Lemma.comments` 关系保持 Phase 3 既定(`User.comments = db.relationship('Comment', backref=backref('author', lazy='joined'), cascade='all, delete-orphan')` + `Lemma.comments = db.relationship('Comment', backref='lemmas', lazy='dynamic', cascade='all, delete-orphan')`),**不**加新关系/backref。
- **D-67:** `Lemma.__init__` 加 `view_count=0, updated_at=None`(后者由 column default 兜底),保持与 Phase 3 D-34 一致的 `__init__` 风格(`def __init__(self, title=None, content=None)`),`view_count` 与 `updated_at` 走 column default,不在 `__init__` 显式赋值。

### 7. 相关词条

- **D-68:** "相关词条"位置 = **评论区下方**,用 Pico.css `<aside>` 包裹 `<h2>相关词条</h2>` + 卡片列表。空结果时整段不渲染(`{% if related_lemmas %}`)。
- **D-69:** backlinks 查询 = `Lemma.query.filter(Lemma.content.contains('[[' + fullcon.title + ']]')).limit(10).all()`。SQL `LIKE %[[Title]]%` 子串匹配。**大小写敏感**(词条 title 是 unique,Phase 2 已确认;用户新建词条时大小写不一致会触发 unique 冲突,所以 `[[大小写一致]]` 即可)。**不**做 normalize/lowercase。
- **D-70:** 限 10 条结果(与首页搜索一致),**不**做分页 — 用户场景下 1 个词条被引用 10+ 次罕见,UX 收益不抵复杂度。
- **D-71:** 详情页加载**先查 backlinks 再渲染**(顺序无关紧要,但同一路由函数体内集中查询便于回滚);**不**做缓存(每访问重新查,Phase 4 demo 数据量小,缓存失效逻辑不值)。

### 8. 评论 HTMX swap 细节

- **D-72:** `templates/_comment.html` 子模板渲染单条 comment 卡片(作者名 / 时间 / 内容 / admin 删按钮 / author 删按钮)。与现有 detail.html `{% for comment in comments %}` 块内的卡片结构保持一致(避免视觉不一致)。
- **D-73:** 评论发布成功时 `/api/comment` 路由:
  1. 创建 `Comment` 对象
  2. commit
  3. 重新查询这条 comment(让 `author` backref joined load)
  4. 检测 `request.headers.get('HX-Request')`:
     - 存在 → `return render_template('_comment.html', comment=comment, current_user=current_user)`,HTTP 200
     - 不存在 → `flash('评论已发布')` + `return redirect(url_for('apple.detail', title=lemma.title))` 走整页(向后兼容 Phase 3)
  5. 失败(匿名 / 超长 / lemma 不存在) — **始终** `flash` + redirect(无论 HX-Request),用户用 Phase 2 统一错误页感知
- **D-74:** 评论 form 客户端成功提交后通过 `hx-on::after-request="if(event.detail.successful) this.reset()"`(Pico.css 的 `<form>` reset 清空 textarea);失败时由 `HX-Retarget` 服务端推送重写 form 区块(用户重试)。

### Claude's Discretion

- **CD-10:** 移动端响应式(< 768px) 折叠导航是否需要 hamburger — 选**不**(Pico.css 自动 wrap 即可,Phase 5 写 README 时如用户强烈要求再补)。
- **CD-11:** 首页 hero 区是否做大标题搜索框 — 选**否**,保持现有"cover.css 风格小标题 + 搜索框"语义,Pico.css `<header>` 重写。
- **CD-12:** 错误页(404/500)视觉风格 — 与 Phase 2 D-17..D-19 既有 `error.html` 一致,**不**改文案,**改** Pico.css 样式(用 Pico container + 错误码大字)。
- **CD-13:** 词条创建默认值:view_count=0(SQLAlchemy column default + server_default 双保险),updated_at=now(SQLAlchemy column default)。
- **CD-14:** 评论 swap 失败 UX 细节 — flash + 清空 textarea(让用户重试);具体重置逻辑由 plan 决定(`hx-on::after-request` vs 服务端 HX-Retarget)。
- **CD-15:** 暗色切换 localStorage key 命名 — 沿用社区惯例 `pico-preferred-color-scheme`(Pico.css 官方 demo 用的 key)。
- **CD-16:** Pico.css 版本锁定 — `@picocss/pico@2.0.6`(jsdelivr 上 2.x 最新稳定,Phase 4 写时为 2.0.6;如 release 更新,planner 锁定具体版本号)。
- **CD-17:** HTMX 触发评论 form 客户端错误时(网络断/500),浏览器原生表单兜底 — 失败时 `hx-on::htmx:send-error` 提示"网络错误,请重试"。简单 JS 处理。

## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### 项目元信息
- `.planning/PROJECT.md` — 项目核心价值、v1 范围、Out of Scope 排除清单、Key Decisions(尤其"HTMX + Pico.css 而非 React")
- `.planning/REQUIREMENTS.md` — v1 46 条需求,Phase 4 对应 FRONT-01..06 + LEMMA-01..08(共 14 条)
- `.planning/ROADMAP.md` § Phase 4 — 阶段目标 + 7 条 SUCCESS 标准 + 计划 4.1/4.2/4.3 拆分
- `.planning/STATE.md` — Phase 1/2/3 已完成,累计上下文

### Phase 2/3 已锁定决策(本阶段直接 carry-forward)
- `.planning/phases/02-security-auth-hardening/02-CONTEXT.md` — D-01..D-25 全部生效
  - **D-09 ~ D-12**:Flask-WTF CSRF,新表单都要 `{{ csrf_token() }}` hidden input
  - **D-13 ~ D-16**:`init_db()` 模块函数 + `flask init-db` CLI
  - **D-17 ~ D-19**:404/403/500/400 统一错误页(Phase 4 重写为 Pico.css 风格,见 CD-12)
  - **D-20 ~ D-22**:`admin` 蓝图 + `@admin_required` + admin 删 lemma 模板集成模式
  - **D-23**:`User.is_admin` 已就绪
  - **D-24 ~ D-25**:`flask promote-admin <username>` CLI
- `.planning/phases/03-comment-system/03-CONTEXT.md` — D-26..D-41 全部生效
  - **D-26**:`Comment.user_id FK` + `backref=backref('author', lazy='joined')` + cascade
  - **D-28**:评论发布**整页刷新**(Phase 4 D-46 覆盖)
  - **D-31 ~ D-32**:评论删除端点(`api.delete_comment` + `admin.delete_comment`)+ 卡片底部删除按钮
  - **D-37**:`detail.html` 内联评论 form
  - **D-39**:`/user/detail` 传 `comments` 变量(Phase 4 D-65 改 GET 后保留 comments 传递)

### 既有代码 / 改造目标
- `app/api/model.py:30-44` — `Lemma` 模型当前实现,Phase 4 加 `updated_at` + `view_count` 两列(D-61)
- `app/api/model.py:11-28` — `User` 模型现状(D-66 不动)
- `app/api/model.py:46-58` — `Comment` 模型(Phase 3 D-26 + D-34 已就绪,本阶段不碰)
- `app/api/model.py:60-78` — `init_db()` 既有实现,新增列后自动覆盖(D-64)
- `app/route/user.py:1-50` — `apple` 蓝图所有路由,Phase 4 改 `/user/detail` 从 POST → GET(D-65)+ 加 search GET 端点(D-45)
- `app/api/__init__.py:1-100` — `api` 蓝图所有路由,Phase 4 改 `/api/comment` 检测 HX-Request(D-46/D-73)+ `/api/login` / `/api/logout` 返回 HX-Trigger(D-47)
- `app/api/admin.py:1-38` — admin 蓝图(D-66 不动)
- `app/__init__.py:7-15` — Flask app 工厂:secret_key / SQLALCHEMY_DATABASE_URI / LoginManager / 蓝图注册(D-56 加 base.html 路径无需改 `__init__.py`)
- `app/templates/home.html` — 现有 nav 行 26-39 + cover 搜索框 + flash 行 44-52。Phase 4 整页重写为 `{% extends 'base.html' %}` + Pico.css + HTMX 搜索
- `app/templates/signin.html / register.html / add.html / modify.html / result.html / detail.html` — 全部 7 模板 Phase 4 重写(除 error.html 沿用 Phase 2 D-17..D-19 模式)
- `app/templates/error.html` — Phase 2 D-17..D-19 已就绪,Phase 4 改 Pico.css 样式(CD-12)
- `app/static/javascripts/jquery-1.11.3.min.js` + `bootstrap.min.js` + `docs.min.js` + `npm.js` + `bootstrap.js` — 全部删除(D-55)
- `app/static/javascripts/wangEditor/*` + `app/static/stylesheets/wangEditor/*` — 全部删除(D-55)
- `app/static/stylesheets/bootstrap.min.css` + `bootstrap-theme.css*` + `style.css` + `mycss/*` — 全部删除(D-55)
- `app/static/fonts/` — Bootstrap icon font,删除(D-55)
- `requirements.txt` — 加 `bleach` 依赖(D-44);不动 `Flask-WTF` / `Flask-Login` / `mysqlclient` / `SQLAlchemy` 等

### 测试与文档
- `tests/`(Phase 5 才建)— 本阶段**不**新增测试,Phase 5 pytest smoke 会覆盖本阶段所有端点
- `README.md`(Phase 5 改)— 本阶段不更新 README,但 planner 应在执行清单中标记"Phase 5 README 需要加 CDN 外网说明(D-53)"

## Existing Code Insights

### Reusable Assets
- **`@admin_required` 装饰器**(`app/api/admin.py:11-25`)— 复用,Phase 4 不动
- **`admin` 蓝图**(`app/api/admin.py:8`)— 复用,Phase 4 不动
- **`api` 蓝图**(`app/api/__init__.py:7-10`)— 复用,Phase 4 改 `/api/comment` 加 HX-Request 检测(D-46)+ 改 `/api/login` / `/api/logout` 加 HX-Trigger(D-47)
- **`apple` 蓝图**(`app/route/user.py:7-10`)— 复用,Phase 4 改 `/user/detail` method(D-65)+ 新增 search GET 端点(D-45)
- **`flash` + `redirect(url_for('apple.<endpoint>'))`** — 既有风格,继续用(评论 swap 失败回退走 flash)
- **`db.session.commit()` 显式事务** — 既有风格,继续用
- **`get_flashed_messages()` Jinja 块** — 7 模板现有 pattern,Phase 4 改写在 `base.html` 中保留一次
- **`db.drop_all()` + `db.create_all()` + 灌种子**(`app/api/model.py:62-76`)— D-64 不改函数体,新 schema 自动覆盖
- **`is_authenticated` / `is_admin` template 检查**(Phase 2 D-22 模式)— 复用
- **CSRF `{{ csrf_token() }}` 模板函数** — 复用,所有新表单加 hidden input(HTMX form 也需要)
- **`{{ url_for('api.<endpoint>') }}` 跨蓝图约定** — 复用
- **Phase 3 的 `templates/_comment.html` 子模板**(新增,Phase 4 D-72)— 抽出来给 HTMX swap 用
- **Flask-SQLAlchemy 2.x `update().where().values()` API** — Phase 4 D-63 view_count 计数用

### Established Patterns
- **Blueprint 命名约定**:`apple` (页面) + `api` (表单提交) + `admin` (Phase 2 新增)
- **`url_for` 跳转**:既有 `redirect(url_for('apple.home'))` 风格保持不变;admin 跳转用 `url_for('admin.delete_lemma', lemma_id=...)`
- **错误反馈**:现状是 `flash` + 重定向(非 JSON 响应),Phase 4 维持这种 HTML 优先的风格;HTMX 路径上失败仍走 flash(由服务端 HX-Retarget 重写 form 区块,JS 端兜底)
- **内嵌 form 模式**(Phase 2 D-22 admin 删 lemma):评论删除 form 复用
- **`current_user` template 检查**:用 `is_authenticated`(Flask-Login 标准),不用 `is_active`
- **隐式 flask app context**:`@app.cli.command` 装饰器自带 app context
- **`reloader=True` 调试模式**:`run.py` 已有 `app.run(debug=True)`,Phase 4 改模板/路由后**不需要**重启 Flask 即可刷新页面

### Integration Points
- `app/api/model.py:30-44` — `Lemma` 模型加 `updated_at` + `view_count` 两列(D-61)+ `__init__` 不显式赋值(D-67)
- `app/api/__init__.py` — 改 `/api/comment` 路由加 HX-Request 分支(D-46 / D-73)+ 改 `/api/login` + `/api/logout` 加 HX-Trigger 响应头(D-47)
- `app/route/user.py` — 改 `/user/detail` 从 POST → GET + 加 view_count +1 SQL UPDATE(D-48 / D-65)+ 新增 search GET 端点(D-45)+ 加 wikilink 渲染辅助函数 + Jinja2 filter(D-50 / D-51)+ 加 backlinks 查询(D-69)
- `app/templates/` — 7 模板重写为 `{% extends 'base.html' %}`(D-56)+ 删旧模板(wangEditor / jQuery modal / mycss 引用)+ 新增 `templates/_comment.html` 子模板(D-72)+ 新增 `templates/base.html`(D-56)
- `app/static/` — 删 jQuery / Bootstrap / wangEditor / mycss / fonts / style.css(D-55);新增 `app/static/javascripts/quill/quill.min.js` + `app/static/stylesheets/quill/quill.snow.css`(D-54)
- `app/static/stylesheets/mycss/` — 整体删除(D-55)
- `requirements.txt` — 加 `bleach` 依赖(D-44)
- `app/__init__.py` — **不**改(app 工厂结构不变);可选:注册 Jinja2 filter `wikilink`(D-50)的代码放在 `app/__init__.py:app.jinja_env.filters['wikilink'] = ...`,或单独 `app/utils/wikilink.py` import

## Specific Ideas

- **想法 A:** Pico.css 2.0 的暗色模式默认跟随 OS,但用户切换按钮覆盖 OS 选择(写 `data-theme="dark"` 后即使用户系统是亮色也走暗)。localStorage 持久化跨会话。
- **想法 B:** HTMX 搜索结果点击应该是 `<a href="/user/detail?title=...">` 而不是按钮 — 这样:
  1. 中键点击可新标签页打开
  2. 浏览器历史前进/后退工作
  3. URL 可分享
  4. 禁用 JS 时仍可用(渐进增强)
- **想法 C:** 评论 HTMX form 客户端 JS 失败兜底 — Pico.css 的 `<form>` 默认浏览器原生提交,所以即使 HTMX 加载失败,form 仍能走整页 POST 提交。已有渐进增强。
- **想法 D:** wikilink 渲染走 Jinja2 filter 而非模板 if 块,语法简洁:`{{ lemma.content|wikilink|safe }}`(注意 `|safe` 必须有,因为 filter 返回 HTML 字符串)。filter 内部访问 DB 查 `Lemma.query.filter_by(title=t).first()`,N+1 风险 — 但**只**查一次(对每个不同的 title 缓存),demo 数据量小可接受。
- **想法 E:** `view_count` 作者本人访问也 +1 — 现实 wiki 一般不 +1(作者不算独立访客),但 Phase 4 demo 简化决策,且无"独立访客"识别 cookie/IP 机制。Claude discretion 决定不特判。
- **想法 F:** 词条内容渲染走 Jinja2 filter `|wikilink` 而非在 `app/route/user.py:detail` 视图层做替换 — 视图层保留纯数据,模板层负责展示。分离关注点。
- **想法 G:** 错误页(error.html)Phase 4 用 Pico.css 重写,但保留 Phase 2 既有的中文错误码 + flash 提示语义(404 → "页面未找到" 等)。视觉更协调,文案不变。

## Deferred Ideas

### 词条版本历史(V2-CONTENT-01)
- PROJECT.md Key Decisions 已明示不实装;留 v2。本阶段不引入 `lemma_revision` 表。

### 评论编辑 / 嵌套 / markdown(V2-COMMENT-01, 02)
- 留 v2。Phase 4 评论是平铺列表 + 纯文本(无 markdown / 无富文本)。

### 全文搜索(V2-CONTENT-02)
- 留 v2。Phase 4 仍用 SQL `LIKE` / SQLAlchemy `contains()`。

### 词条保护 / 锁定(V2-CONTENT-03)
- 留 v2。Phase 4 任何登录用户都可编辑,管理员删除兜底。

### 编辑者 / 版主角色(V2-CONTENT-04)
- v1 维持 regular + admin 二元角色,Phase 4 不引入第三角色。

### alembic / 数据库迁移工具
- Phase 4 不引入。demo 性质接受 drop+create 重灌。生产部署走 Phase 5 init-db 一次性初始化。

### 图片上传
- Quill 工具栏精简集不含图片上传,Phase 4 不实现文件存储 / OSS / S3 集成。

### 词条创建时自动建 backlinks 占位
- 当前没有"占位词条"概念,`[[X]]` 跳到 add.html 是用户主动创建。自动占位不在 Phase 4 范围。

### i18n / 移动端 App / PWA / 实时更新
- V2-FRONT-01, 02, 03 — 留 v2。

### CI/CD
- V2-OPS-01, 02 — 留 v2。Phase 5 部署文档手写,不接 GitHub Actions。

### 监控 / OpenTelemetry
- V2-OPS-03 — 留 v2。

### 暗色切换的"系统跟随"模式
- 当前按钮只支持 dark/light 二选一;如果想"跟随系统"需要加第三档。Phase 4 简化只做 dark/light。

### 词条 RSS / Atom 订阅
- 留 v2。Phase 4 不实现 feed。

### 词条打印样式
- Pico.css 自带 print 样式,够用;不专门优化。

### mobile 端 hamburger 菜单
- Phase 4 决策不引入(CD-10)。如 Phase 5 用户强烈要求再补。

---

*Phase: 04-Frontend Modernization & Product Features*
*Context gathered: 2026-06-12*
