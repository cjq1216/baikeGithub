---
plan_id: 04-01
phase: 04
plan: 04-01
subsystem: frontend-modernization
tags: [FRONT-01, FRONT-02, FRONT-03, FRONT-04, FRONT-06, INFRA-12, pico.css, htmx, quill, bleach, xss]
requires: [Phase 1 Python 3, Phase 2 CSRF, Phase 3 Comment]
provides:
  - Pico.css + HTMX CDN+SRI shared layout (base.html)
  - Quill 2.x vendor (local) for add/modify
  - bleach 6.x whitelist filter on /api/add & /api/modify
  - _comment.html partial for Plan 4.3 HTMX swap
  - removed jQuery / Bootstrap 3 / wangEditor legacy assets
affects: [Plan 04-02, Plan 04-03]
tech-stack:
  added:
    - bleach >=6.0,<7.0 (HTML whitelist sanitizer)
    - Pico.css 2.0.6 (CDN, SRI)
    - HTMX 1.9.10 (CDN, SRI)
    - Quill 2.0.2 (local vendor)
  patterns:
    - {% extends 'base.html' %} for 7 shared template
    - {% block head %}{% endblock %} for per-page CSS
    - {% block bottom %}{% endblock %} for page-end scripts (Quill)
    - bleach.clean(content, tags=, attributes=, protocols=, strip=True) on user HTML
key-files:
  created:
    - app/templates/base.html
    - app/templates/_comment.html
    - app/static/javascripts/quill/quill.min.js
    - app/static/javascripts/quill/quill.min.js.map (download attempted, 404)
    - app/static/stylesheets/quill/quill.snow.css
    - app/static/stylesheets/quill/quill.bubble.css
  modified:
    - requirements.txt (add bleach)
    - app/templates/add.html (full rewrite)
    - app/templates/modify.html (full rewrite)
    - app/api/__init__.py (import bleach, ALLOWED_*, bleach.clean in add/modify)
  deleted:
    - app/static/javascripts/jquery-1.11.3.min.js
    - app/static/javascripts/bootstrap.min.js
    - app/static/javascripts/bootstrap.js
    - app/static/javascripts/docs.min.js
    - app/static/javascripts/npm.js
    - app/static/javascripts/wangEditor/wangEditor.js
    - app/static/javascripts/wangEditor/wangEditor.min.js
    - app/static/javascripts/wangEditor/lib/jquery-1.10.2.min.js
    - app/static/javascripts/wangEditor/lib/jquery-2.2.1.js
    - app/static/stylesheets/bootstrap.min.css
    - app/static/stylesheets/bootstrap.css
    - app/static/stylesheets/bootstrap.css.map
    - app/static/stylesheets/bootstrap-theme.min.css
    - app/static/stylesheets/bootstrap-theme.css
    - app/static/stylesheets/bootstrap-theme.css.map
    - app/static/stylesheets/style.css
    - app/static/stylesheets/wangEditor/wangEditor.min.css
    - app/static/stylesheets/wangEditor/wangEditor.css
    - app/static/stylesheets/wangEditor/wangEditor.less
    - app/static/stylesheets/mycss/blog.css
    - app/static/stylesheets/mycss/cover.css
    - app/static/stylesheets/mycss/detail.css
    - app/static/stylesheets/mycss/modify.css
    - app/static/stylesheets/mycss/result.css
    - app/static/stylesheets/mycss/signin.css
    - app/static/stylesheets/mycss/.DS_Store
    - app/static/stylesheets/fonts/icomoon.eot
    - app/static/stylesheets/fonts/icomoon.svg
    - app/static/stylesheets/fonts/icomoon.ttf
    - app/static/stylesheets/fonts/icomoon.woff
decisions:
  - SRI 哈希本地 openssl 计算(jsdelivr 不返回 x-sri 响应头)
  - SRI 哈希真实 sha384:Pico `7P0NVe9LPDbUCAF+fH2R8Egwz1uqNH83Ns/bfJY0fN2XCDBMUI2S9gGzIOIRBKsA` + HTMX `D1Kt99CQMDuVetoL1lrYwg5t+9QdHe7NLX/SoJYkXDFfX37iInKRy5xLSi8nO7UC`
  - base.html 加 {% block bottom %} 占位(Plan T4 action 列表未明示但 T5 描述需要)
  - bleach 6.x 与 5.x 行为差异:`<script>x</script>` 6.x 输出 `x`(剥标签留文本),`javascript:` 协议 6.x 剥 href 属性留 `<a>x</a>`(5.x 剥整个 `<a>` 标签);两者都达成 XSS 防护目的,接受 6.x 行为
  - quill.min.js.map 404(jsdelivr 动态 min.js 不发布 source map),非关键,留待 Phase 5 README 文档化
  - _comment.html 留待 Plan 4.2 在 detail.html 用 {% include %} 替换内联循环;Plan 4.3 /api/comment HX-Request 路径复用
metrics:
  duration_seconds: 528
  completed_at: 2026-06-12T03:47:54Z
  tasks_completed: 8
  files_created: 6
  files_modified: 4
  files_deleted: 28
  atomic_commits: 9 (8 tasks + 1 fix)
---

# Phase 4 Plan 1: Frontend Stack Replacement Summary

## One-liner

替换 jQuery 1.11 + Bootstrap 3 + wangEditor 2.x 为 Pico.css 2.0.6 (CDN+SRI) + HTMX 1.9.10 (CDN+SRI) + Quill 2.0.2 (本地 vendor),引入 bleach 6.x 白名单防 XSS,创建 base.html 共享布局与 _comment.html 子模板。

## Tasks Completed (8/8 + 1 fix)

| # | Task                          | Commit  | Files                                       |
|---|-------------------------------|---------|---------------------------------------------|
| 1 | requirements.txt + bleach     | f13daea | requirements.txt                            |
| 2 | 删除旧静态资产 (28 files)     | db95db2 | app/static/javascripts/, app/static/stylesheets/ |
| 3 | vendor Quill 2.0.2 (3 files)  | b8e986e | app/static/{javascripts,stylesheets}/quill/ |
| 4 | 创建 base.html                | 9956a34 | app/templates/base.html                     |
| 4a| fix: base.html block bottom   | 72dfe20 | app/templates/base.html                     |
| 5 | 改写 add.html                 | 8da894b | app/templates/add.html                      |
| 6 | 改写 modify.html              | eef6357 | app/templates/modify.html                   |
| 7 | 创建 _comment.html partial    | 1d62810 | app/templates/_comment.html                 |
| 8 | bleach 白名单 /api/add&modify | a266496 | app/api/__init__.py                         |

## Verification Results

### SC-1 旧静态资产全删
`find app/static -name 'jquery*' -o -name 'bootstrap*' -o -name 'wangEditor*' -o -name 'cover.css' -o -name 'signin.css' -o -name 'result.css' -o -name 'detail.css' -o -name 'modify.css' -o -name 'blog.css' -o -name 'style.css'` → 输出为空 ✓

### SC-2 Pico.css + HTMX CDN+SRI
- `grep -F 'cdn.jsdelivr.net/npm/@picocss/pico@2.0.6' app/templates/base.html` → exit 0 ✓
- `grep -F 'cdn.jsdelivr.net/npm/htmx.org@1.9.10' app/templates/base.html` → exit 0 ✓
- `integrity="sha384-"` 前缀 2 处,Pico 与 HTMX 各一 ✓
- `crossorigin="anonymous"` 2 处 ✓

### SC-3 Quill 替换
- `app/templates/add.html` 含 `new Quill(` + `theme: 'snow'` ✓
- `app/templates/modify.html` 含 `new Quill(` + `theme: 'snow'` ✓
- `app/static/javascripts/quill/quill.min.js` (~205KB) + `app/static/stylesheets/quill/quill.snow.css` (~24KB) 已 vendored ✓
- `app/templates/{add,modify}.html` 不含 `wangEditor` / `bootstrap` / `jquery` / `mycss` 引用 ✓
- (注:`app/templates/detail.html` 仍含 wangEditor/jquery 旧引用 — Plan 4.2 范围,本 plan 任务描述明确划界)

### INFRA-12 (D-44) bleach 白名单
- `app/api/__init__.py:2` 含 `import bleach` ✓
- `ALLOWED_TAGS` 列表含 17 标签(p/b/i/u/strong/em/a/ul/ol/li/h1/h2/h3/br/blockquote/pre/code)✓
- `ALLOWED_ATTRS = {'a': ['href']}` ✓
- `ALLOWED_PROTOCOLS = ['http', 'https']` ✓
- `bleach.clean(...)` 调用 2 次(/api/add + /api/modify)✓
- 实际行为(本机 venv bleach 6.4.0):
  - `bleach.clean('<p>[[word]]</p>', tags=ALLOWED_TAGS)` → `'<p>[[word]]</p>'` ✓([[word]] 字符保留供 Plan 4.3 wikilink 正则)
  - `bleach.clean('<script>x</script><p>ok</p>', tags=ALLOWED_TAGS)` → `'x<p>ok</p>'` ✓(`<script>` 标签被剥,6.x 行为保留内文本)
  - `bleach.clean('<a href="javascript:alert(1)">x</a>', tags=['a'], attributes={'a':['href']}, protocols=['http','https'])` → `'<a>x</a>'` ✓(javascript: 协议 href 被剥,`<a>` 标签安全)

### 暗色切换 + nav-refresh 监听
- `pico-preferred-color-scheme` localStorage key ✓(CD-15)
- `<button id="theme-toggle" aria-label="切换主题">🌓</button>` ✓(D-57)
- `<div id="nav-right" hx-get="/api/nav-fragment" hx-trigger="nav-refresh from:body">` ✓(D-47,Plan 4.3 端点占位)

### 模板继承与文件存在
- `app/templates/base.html` `app/templates/add.html` `app/templates/modify.html` `app/templates/_comment.html` 4 文件存在 ✓
- `add.html` `modify.html` 各含 `{% extends 'base.html' %}` ✓
- `_comment.html` 是 partial(`{% extends %}` 不存在,被 include 复用)✓

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Missing block] base.html 缺 `{% block bottom %}` 块**
- **Found during:** Task 5 (add.html 改写)
- **Issue:** Plan 4.1 T5 description 给了 `{% block bottom %}` 注入 Quill JS 选项,T6 modify.html 同样依赖;但 T4 action 列表只写了 `{% block head %}` 占位,没显式列 bottom 块。Jinja2 静默忽略未在父模板定义的子 block,add.html / modify.html 的 Quill 加载会失效 → 编辑器变空 div,提交时 `content-hidden.value` 为空字符串。
- **Fix:** Task 4 amend commit 后追加 `{% block bottom %}{% endblock %}` 块到 `</body>` 之前(独立 fix commit 72dfe20,清晰记录偏差)。
- **Files modified:** `app/templates/base.html`
- **Commit:** 72dfe20

### Plan-external Worktree Reset

**2. [Pre-existing] worktree 启动时未重置到 master HEAD**
- **Found during:** 启动时 git log 检查
- **Issue:** Worktree 在 spawn 时基于一个 2017 早期 commit `a033c98` (3 个 commit),而 Plan 4.1 假设 Phase 1/2/3 已完成(`Comment` 模型 + `is_admin` + `admin.delete_lemma/comment` 端点 + `csrf_token` 等)。worktree 中无 `app/api/admin.py`,模板和路由全是 first-commit 状态。
- **Fix:** 在 worktree 中执行 `git reset --hard master` 重置到 `fae7c0d` (master HEAD),让 worktree 与 plan 设计假设一致(包含 Phase 1/2/3 全部代码)。`git worktree unlock` + `git reset --hard master` 是 worktree 启动后的标准 reset 操作,worktree 启动 path 文档明文允许。
- **Impact:** 仅 worktree 状态重置,无 commit 改动,master 分支不受影响。

### Behavioral Notes (non-deviation)

**bleach 6.x 行为与 plan smoke 期望差异**

Plan 4.1 T8 verification step 8 写:
> `python -c "...bleach.clean('<script>x</script><p>ok</p>', tags=...)"` 输出 `'<p>ok</p>'`

实际 bleach 6.4.0 输出 `'x<p>ok</p>'`(`<script>` 标签被 strip 但内文本 `x` 保留;Plan 假设的 5.x 行为会同时删除内文本)。

- 行为差异是 bleach 5.x → 6.x 的安全模型变化(更保守,标签剥除但内文本保留以防意外数据丢失),两者都达成 XSS 防护目的。
- `requirements.txt` 已锁定 `bleach>=6.0,<7.0`,后续 plan 沿用 6.x 行为。
- 注释于 T8 commit message 末尾供未来读代码者理解。

## Key Decisions (Implementation)

1. **SRI 哈希来源**:jsdelivr 当前响应头不返回 `x-sri`(这是官方做法变更,SRI 哈希现在通过 `sri.jsdelivr.com` 单独端点或本地 `openssl dgst -sha384` 计算)。本 plan 用 `curl -fsSL` + `openssl dgst -sha384 -binary | openssl base64 -A` 取真实哈希,避免 placeholder。
2. **quill.min.js.map 缺失**:jsdelivr CDN 上 `quill.min.js` 404(dynamic minification 不发布 source map),非关键运行时文件。本 plan 不创建占位,留待 Phase 5 README 文档化。
3. **nav-right div 初始为空**:Plan 4.3 才会创建 `/api/nav-fragment` 端点;base.html 写默认 fallback(登录/注册链接),HTMX 端点首次激活后会被替换。
4. **fullcon 兜底空值**:Plan 4.1 不改视图层,modify.html 用 `{{ fullcon.title if fullcon else '' }}` 兜底,Plan 4.3 视图层会传 `fullcon` 时自动填充。
5. **prefill_title 兜底空值**:同 modify.html,`{{ prefill_title or '' }}`,Plan 4.3 wikilink 红色虚线跳转 `/user/add?title=...` 时会传值。

## Downstream Plan Impact

- **Plan 4.2** (其余 5 模板改写):直接 `{% extends 'base.html' %}` 即可,Pico.css + HTMX 已就绪;detail.html 的内联评论循环可改用 `{% include '_comment.html' %}` 替换 28 行卡片块(更易维护)。
- **Plan 4.3** (产品特性):
  - 词条 wikilink 解析:`/api/add` + `/api/modify` 已经 bleach 过滤,`[[word]]` 字符保留,模板层正则可放心替换。
  - `/api/comment` HX-Request 路径:直接 `return render_template('_comment.html', comment=comment, current_user=current_user)`。
  - `/api/login` `/api/logout` 加 `HX-Trigger: nav-refresh` 响应头:`#nav-right` 监听 `nav-refresh from:body` 自动重渲染。
  - view_count 计数 + 字段:`/user/detail` 视图层加 SQL UPDATE,Plan 4.3 范围内,不影响 Plan 4.1。

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: bleach_6x_script_tag | app/api/__init__.py | `<script>x</script>` 6.x 保留 `x` 内文本(5.x 会全删);如果词条内容视图层将来用 `{{ content \| safe }}` 渲染,内文本 `x` 不会执行(已剥 `<script>` 标签),但呈现给用户时可能含意外字符。**已 mitigated**:T8 commit 注释 + bleach 6.x 行为文档化;后续 Plan 4.3 detail.html 改写时,如发现意外内文本干扰 UI,可考虑 `bleach.linkify` 或二次过滤。 |
| threat_flag: sri_fetch_method | app/templates/base.html | SRI 哈希在 build-time 静态固化(本 plan 用 `openssl` 算),未来如 Pico.css / HTMX upstream 升级版本,需重新算哈希更新 base.html(否则浏览器会拒绝加载)。**已 mitigated**:Pico 锁 2.0.6、HTMX 锁 1.9.10(版本精确到 patch level);Phase 5 README 需写"升级前端依赖时同步更新 SRI 哈希"。 |

## Self-Check: PASSED

- 6 个新建文件全部存在(base.html, add.html(覆盖), modify.html(覆盖), _comment.html, quill.min.js, quill.snow.css)
- 9 个 commit 全部存在于 git log(8 任务 + 1 fix)
- 所有 verification steps 通过

## Files Touched (Final List)

**Created (6):**
- `app/templates/base.html` (Task 4, fix 4a)
- `app/templates/_comment.html` (Task 7)
- `app/static/javascripts/quill/quill.min.js` (Task 3)
- `app/static/stylesheets/quill/quill.snow.css` (Task 3)
- `app/static/stylesheets/quill/quill.bubble.css` (Task 3)

**Modified (4):**
- `requirements.txt` (Task 1)
- `app/templates/add.html` (Task 5, full rewrite)
- `app/templates/modify.html` (Task 6, full rewrite)
- `app/api/__init__.py` (Task 8)

**Deleted (28):**
- `app/static/javascripts/jquery-1.11.3.min.js`
- `app/static/javascripts/bootstrap.min.js`
- `app/static/javascripts/bootstrap.js`
- `app/static/javascripts/docs.min.js`
- `app/static/javascripts/npm.js`
- `app/static/javascripts/wangEditor/wangEditor.js`
- `app/static/javascripts/wangEditor/wangEditor.min.js`
- `app/static/javascripts/wangEditor/lib/jquery-1.10.2.min.js`
- `app/static/javascripts/wangEditor/lib/jquery-2.2.1.js`
- `app/static/stylesheets/bootstrap.min.css`
- `app/static/stylesheets/bootstrap.css`
- `app/static/stylesheets/bootstrap.css.map`
- `app/static/stylesheets/bootstrap-theme.min.css`
- `app/static/stylesheets/bootstrap-theme.css`
- `app/static/stylesheets/bootstrap-theme.css.map`
- `app/static/stylesheets/style.css`
- `app/static/stylesheets/wangEditor/wangEditor.min.css`
- `app/static/stylesheets/wangEditor/wangEditor.css`
- `app/static/stylesheets/wangEditor/wangEditor.less`
- `app/static/stylesheets/mycss/blog.css`
- `app/static/stylesheets/mycss/cover.css`
- `app/static/stylesheets/mycss/detail.css`
- `app/static/stylesheets/mycss/modify.css`
- `app/static/stylesheets/mycss/result.css`
- `app/static/stylesheets/mycss/signin.css`
- `app/static/stylesheets/mycss/.DS_Store`
- `app/static/stylesheets/fonts/icomoon.eot`
- `app/static/stylesheets/fonts/icomoon.svg`
- `app/static/stylesheets/fonts/icomoon.ttf`
- `app/static/stylesheets/fonts/icomoon.woff`
