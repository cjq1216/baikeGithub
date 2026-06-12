---
plan_id: 04-02
phase: 04
plan: 04-02
subsystem: frontend-templates
tags: [FRONT-05, LEMMA-01, LEMMA-02, LEMMA-03, LEMMA-04, LEMMA-05, LEMMA-06, LEMMA-07, LEMMA-08, pico.css, htmx, semantic-html, csrf]
requires: [Plan 04-01 base.html, Plan 04-03 detail.html + result.html + Lemma schema]
provides:
  - HTMX 边输边出搜索(home.html 增量更新结果区)
  - /user/search GET 端点(从 POST 迁移,支持 HTMX 片段返回)
  - _search_result.html partial 共享给 home/result/search
  - signin/register/error 三个 Bootstrap 模板的 Pico.css 重写
  - 7 模板全部 extends base.html 统一布局
affects: [Phase 5 pytest smoke, README, Phase 4 demo 视觉一致性]
tech-stack:
  added: []
  patterns:
    - HTMX 1.9.10 hx-get + hx-trigger keyup changed delay:300ms
    - HX-Request header detection 区分片段 vs 整页返回
    - Jinja2 partial(无 {% extends %})被 include 和 render_template 复用
    - Progressive enhancement:<noscript><form method=get> 兜底
    - url_for 跨蓝图约定:apple.<endpoint> / api.<endpoint>(CLAUDE.md 强约束)
key-files:
  created:
    - app/templates/_search_result.html
  modified:
    - app/templates/home.html
    - app/templates/signin.html
    - app/templates/register.html
    - app/templates/error.html
    - app/route/user.py
  deleted: []
  verified-no-modify:
    - app/templates/add.html (Plan 04-01 T5 状态)
    - app/templates/modify.html (Plan 04-01 T6 状态)
    - app/templates/result.html (Plan 04-03 T9 状态)
    - app/templates/detail.html (Plan 04-03 T9 状态)
decisions:
  - _search_result.html partial 命名用下划线前缀(Jinja2 partial 约定,Plan 04-01 _comment.html 一致)
  - /user/search 旧 POST 端点删除(不留 fallback),noscript 用户走 GET 整页 + result.html
  - HTMX 片段返回用 request.headers.get('HX-Request') 头检测(HTMX 1.x 标准做法)
  - 空 q 返 200 + 空结果片段(不 400),与 plan 设计一致(D-45)
  - url_for('apple.search') 而非硬编码 /user/search(蓝图重构路径时不需改模板)
  - signin/register 跨蓝图跳转走 url_for('api.loginBusiness') / 'api.registBusiness'(CLAUDE.md 强约束)
  - error.html 大字号 6rem 错误码 + 中文 error.name 保留 Phase 2 D-17..D-19 语义
  - Task 3/4/7/8 为 verification-only(Plan 04-01/04-03 已完成对应工作,无需重写)
metrics:
  duration_seconds: 0
  completed_at: 2026-06-12T12:08:00Z
  tasks_completed: 9
  tasks_verification_only: 4
  files_created: 1
  files_modified: 5
  files_deleted: 0
  atomic_commits: 5
---

# Phase 4 Plan 2: 七模板重设计 + HTMX 边输边出搜索 Summary

## One-liner

home.html / signin.html / register.html / error.html 改写为 Pico.css + extends base.html 统一布局,新增 _search_result.html partial,改 /user/search 路由从 POST → GET 并支持 HTMX 片段返回,1 字符起 300ms 防抖的边输边出搜索完成。

## Tasks Completed (5 atomic commits + 4 verification-only)

| #  | Task                                                     | Commit  | Type        | Files                                                |
|----|----------------------------------------------------------|---------|-------------|------------------------------------------------------|
| 1  | 改写 home.html(extends base + HTMX 搜索 + #results 容器) | 3becd5a | feat        | app/templates/home.html                              |
| 2  | 改写 signin.html / register.html(Pico.css 表单)          | a35d82c | feat        | app/templates/signin.html, app/templates/register.html |
| 3  | 验证 add.html / modify.html                              | —       | verification | (Plan 04-01 T5/T6 状态保持)                          |
| 4  | 验证 result.html                                          | —       | verification | (Plan 04-03 T9 状态保持)                             |
| 5  | 创建 _search_result.html partial                          | ec9e3cf | feat        | app/templates/_search_result.html                    |
| 6  | 改 /user/search POST → GET + HTMX 片段返回               | b282950 | feat        | app/route/user.py                                    |
| 7  | 验证 detail.html                                          | —       | verification | (Plan 04-03 T9 状态保持)                             |
| 8  | 验证 /user/detail 路由                                    | —       | verification | (Plan 04-03 T2 状态保持)                             |
| 9  | 改写 error.html(extends base + Pico.css 大字错误码)      | bb1e4a9 | feat        | app/templates/error.html                             |

## Verification Results

### SC-4: 7 模板全部 extends base.html
- 7 模板 + error.html = 8 文件全部 `{% extends 'base.html' %}` ✓
- `_search_result.html` 和 `_comment.html` 是 partial(无 `{% extends %}`)✓

### SC-2 部分(Plan 4.2):HTMX 边输边出搜索
- `home.html` 含 `hx-get="{{ url_for('apple.search') }}"` + `hx-trigger="keyup changed delay:300ms"` ✓
- `hx-target="#results"` + `hx-indicator="#spinner"` ✓
- 1 字符起触发(`changed` 修饰符,空 q 不会触发)
- `<noscript><form method=get>...</form></noscript>` 渐进增强兜底 ✓

### LEMMA-03:/user/search GET 端点
- `methods=['GET']`(旧 POST 端点删除)✓
- `q = request.args.get('q', '').strip()`(空字符串兜底,空 q 返 200 不 400)✓
- `Lemma.query.filter(Lemma.title.like('%' + q + '%')).limit(20)` SQLAlchemy 模糊匹配 + 20 条上限 ✓
- `request.headers.get('HX-Request')` 头检测:存在则返 `_search_result.html` 片段,否则返 `result.html` 完整页 / 空结果 flash + redirect home ✓

### FRONT-05 配套:7 模板 Pico.css + semantic HTML
- 全部 7 模板用 `<article>` / `<header>` / `<label>` 等语义化标签
- Pico.css 内置 focus 状态(无需手动调)+ 暗色模式自动跟随 base.html
- 表单 `<label>` 包裹 `<input>`(Pico.css 表单 a11y 模式)
- `<noscript>` 兜底:禁用 JS 用户走整页 GET 提交

### D-09 CSRF 全保护
- signin.html / register.html / add.html / modify.html / detail.html 5 个 `method="post"` 模板全部含 `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` ✓

### url_for 跨蓝图约定(CLAUDE.md 强约束)
- `grep -rn "url_for('user\."` 输出为空 ✓
- 全部用 `apple.<endpoint>` / `api.<endpoint>` / `admin.<endpoint>`

### CD-12 error.html Pico.css 化
- extends base + `<article>` 卡片 + 大字号 6rem 错误码 + 中文 `error.name`
- 保留 Phase 2 D-17..D-19 错误码 + 中文文案语义
- 不暴露 traceback(`e.__traceback__` 不在模板中)

### Plan 4.3 兼容性
- `result.html` (Plan 4.3 T9 状态) 使用 `url_for('apple.detail', title=...)` GET 链接 ✓
- `detail.html` (Plan 4.3 T9 状态) 使用 `fullcon` 单对象 + `|wikilink|safe` + `related_lemmas` + `_comment.html` include ✓
- `_search_result.html` 使用与 `result.html` 一致的 `{{ lemma.view_count }}` + `{{ lemma.updated_at }}` 字段名,无 schema 漂移

## Deviations from Plan

### Plan-external Worktree Reset

**1. [Pre-existing] worktree spawn baseline mismatch with plan assumptions**
- **Found during:** Task 3 verification
- **Issue:** Worktree spawn-time HEAD was at `a033c98` (3 commits, first-commit state — no Phase 1/2/3 work, no Phase 04-01 / 04-03 commits, no `base.html`, no Pico.css / HTMX, no `add.html` / `modify.html` rewrites, no `_comment.html`, no `Lemma.updated_at` / `view_count`, no `wikilink` filter). Plan 04-02 assumes Phase 1-3 + Plan 04-01 + Plan 04-03 are committed.
- **Fix:** `git reset --hard master` in the worktree at startup, aligning with the standard worktree-agent reset path (allowed by `<worktree_branch_check>` block in execution context). master HEAD is `58b5977` (Plan 04-03 complete), so Plan 04-02's prerequisites (Pico.css + HTMX in `base.html`, `add.html` / `modify.html` rewrites with Quill 2.x, `result.html` / `detail.html` rewrites, `Lemma.updated_at` + `view_count` schema, `/user/detail` GET, `wikilink` filter, `_comment.html` / `_nav_right.html` partials) are present.
- **Impact:** Worktree state reset, no commit mutation, master branch unaffected. After reset, all 4 verification-only tasks (T3 / T4 / T7 / T8) become true positives — Plan 04-01 and Plan 04-03 are confirmed committed.
- **Note:** Plan 04-01 SUMMARY.md "Plan-external Worktree Reset" 偏差 2 记录了相同性质的问题(同样的 3-commit baseline,同样的 `git reset --hard master` 解决方案)。此偏差在 Phase 4 三个 plan 反复出现,建议 Phase 5 协调层在 worktree spawn 路径中自动 reset 到 master HEAD,避免重复。

## Key Decisions (Implementation)

1. **HTMX 触发器用 `keyup changed delay:300ms` 而非 `input`**:Plan 4.1 D-45 既定值;`changed` 修饰符确保只在值实际变化时触发(避免 IME 中文输入中间态);`delay:300ms` 防抖避免每键击发请求。
2. **空 q 返 200 + 空结果**:Plan 4.2 D-45 决策 — 避免 HTMX 客户端报 "404 / 400" 错误状态(HTMX 1.x 默认所有非 2xx 触发 swap error 事件)。
3. **HX-Request 头检测而非 query 参数**:HTMX 1.x 标准做法,所有 HTMX 请求自动带 `HX-Request: true` 头,服务端检测单一标识;`?partial=1` 之类的 query 方案需要客户端 + 服务端双改。
4. **`_search_result.html` partial 命名用下划线前缀**:与 Plan 04-01 `_comment.html` 一致(Jinja2 partial 约定),也避免被 `find app/templates -name '*.html'` 当作"页面模板"误判。
5. **`noscript` 渐进增强**:home.html 内的 `<noscript><form method=get>` 是禁用 JS 时的兜底(整页跳转 `/user/search?q=...` 走 result.html 完整页),与 HTMX 主路径并存不冲突。
6. **/user/search 不留 POST fallback**:旧 `methods=['POST']` 路由已删除,POST 请求返 405 method not allowed。整页搜索的 noscript 用户走 GET + query 参数,POST 没有用途。
7. **`url_for('apple.search')` 而非硬编码 `/user/search`**:与 `url_for('api.loginBusiness')` 等跨蓝图约定一致;未来蓝图重命名 / 路径重构时无需改模板。
8. **Task 3 / 4 / 7 / 8 标记 verification-only**:Plan 04-01 负责 `add.html` / `modify.html`,Plan 04-03 负责 `result.html` / `detail.html` / `/user/detail` 路由 — Plan 04-02 不重复实施。Plan 04-02 的 acceptance_criteria 中这些任务的"重写"部分已由前置 plan 完成。

## Downstream / Future Plan Impact

- **Phase 5 pytest smoke**:
  - URL map assertion: `/user/search GET` (was POST), 接受 `?q=...`, 返 HTMX 片段 / 整页 result.html
  - Template render assertion: 7 模板 extends base.html,含语义化标签,无 `<!DOCTYPE html>` 自包含
  - 模板可被 `flask test_client` 渲染,无需浏览器环境
- **README**:
  - 127.0.0.1:5000/user/search?q=test 是新搜索入口(GET 化)
  - HTMX 增量搜索需外网访问 jsdelivr CDN(与现有 Pico.css 共享)
- **Phase 4 demo 视觉**:
  - 7 模板 Pico.css 统一布局 + 暗色切换 + 主题按钮
  - HTMX 边输边出搜索 UX 提升(无需回车即出结果)
  - 错误页(404/500)与主页视觉一致

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: htmx_search_xss | app/templates/_search_result.html | T2 — `{{ lemma.title }}` 等用户内容字段由 Jinja2 自动 HTML-escape,无 XSS 风险;`{{ (lemma.content\|striptags)\|truncate(200) }}` 在 escape 前 `striptags` 剥 HTML 标签,双保险。**已 mitigated**:Jinja2 default autoescape;`striptags` + truncate;`error.code` / `error.name` / `error.description` 来自 Flask HTTPException(服务器侧构造)。 |
| threat_flag: htmx_indicator_default | app/static/stylesheets/pico.min.css (CDN) | T1 缓解 — `class="htmx-indicator"` 是 HTMX 1.x 内置类(默认 `opacity: 0`),无需自定义 CSS。但当前 Pico.css 不提供 `htmx-indicator` 类,默认样式在 HTMX 加载时 `display: none` / `opacity: 0`,loading 时变 visible。如果未来想自定义 spinner 样式需加 `<style>.htmx-indicator{...}</style>` 块到 base.html。**已 mitigated**:Pico.css 内置 spinner animation 可直接套用,Plan 5 README 文档化。 |
| threat_flag: search_get_no_csrf | app/route/user.py | `/user/search` 是 GET,不改状态,无 CSRF 风险。**已 mitigated**:GET method 不触发 Flask-WTF CSRF 校验(Phase 2 D-09 默认对 GET 不强制)。 |
| threat_flag: htmx_404_status | app/route/user.py | T2 缓解 — 空 q 不返 400,HTMX 1.x 默认非 2xx 触发 swap error。如果未来有端点要返 404 给 HTMX,需显式 `HX-Trigger: 404-not-found` 事件。**已 mitigated**:本 plan 所有 HTMX 端点(q 不空时返 200 / q 空时返 200 空结果)都符合 HTMX 期望。 |
| threat_flag: plan_external_worktree_reset | worktree spawn | 偏差 1 — worktree 启动时 baseline 为 first commit 而非 master HEAD,需 `git reset --hard master` 才能匹配 plan 设计假设。此问题在 Phase 4 三个 plan 反复出现。**已 mitigated**:本 plan 内 `git reset --hard master` + 文档化,建议 Phase 5 协调层在 worktree spawn 路径自动 reset。 |

## Self-Check: PASSED

- 1 新建文件 `_search_result.html` 存在 ✓
- 5 改写文件全部存在:`home.html` (39 行) + `signin.html` (24 行) + `register.html` (24 行) + `error.html` (12 行) + `app/route/user.py` 的 `search()` 函数 (16 行)
- 5 atomic commits 在 git log 中(3becd5a, a35d82c, ec9e3cf, b282950, bb1e4a9)
- 4 verification-only tasks(T3/T4/T7/T8)确认前置 plan 已完成
- 所有静态 SC 检查 PASS
- 无 `user.<endpoint>` url_for 引用(CLAUDE.md 强约束)
- 所有 `method="post"` form 含 `csrf_token` hidden input
- 7 模板 + 1 partial = 8 文件符合 Jinja2 规范

## Files Touched (Final List)

**Created (1):**
- `app/templates/_search_result.html` (Task 5)

**Modified (5):**
- `app/templates/home.html` (Task 1, full rewrite)
- `app/templates/signin.html` (Task 2, full rewrite)
- `app/templates/register.html` (Task 2, full rewrite)
- `app/templates/error.html` (Task 9, full rewrite)
- `app/route/user.py` (Task 6, `search()` 函数 POST → GET + HTMX 片段返回)

**Deleted (0):**
- None

**Verified-Not-Modified (4):**
- `app/templates/add.html` (Plan 04-01 T5 状态保持)
- `app/templates/modify.html` (Plan 04-01 T6 状态保持)
- `app/templates/result.html` (Plan 04-03 T9 状态保持)
- `app/templates/detail.html` (Plan 04-03 T9 状态保持)
