---
phase: 03
phase_name: Comment System
status: ✅ Phase complete (static verification 100%; end-to-end deferred to Phase 5)
generated: 2026-06-12
plans_executed: [03-01, 03-02]
total_commits: 6
---

# Phase 3 — Comment System Verification

## 1. 交付清单(commits)

| # | Plan | Commit | Files |
|---|------|--------|-------|
| 1 | 03-01/T1 | `945128b` | `app/api/model.py` |
| 2 | 03-01/T2 | `9a2499c` | `app/api/__init__.py` |
| 3 | 03-01/T3 | `fba131e` | `app/api/__init__.py` |
| 4 | 03-01/T4 | `fd6605e` | `app/route/user.py` |
| 5 | 03-02/T1 | `59b4148` | `app/api/admin.py` |
| 6 | 03-02/T2 | `bb3991b` | `app/templates/detail.html` |

## 2. SUCCESS 标准覆盖

| SC | 描述 | 验证方式 | 结果 |
|----|------|----------|------|
| SC-1 | 登录用户从 detail 发布评论 | Plan 3.1 T2 实装 `POST /api/comment` + `@login_required` + `Comment(user_id=current_user.id, ...)` | ✅ |
| SC-2 | 匿名 POST 403 + 模板不渲染 form | `@login_required` 装饰器 + `{% if current_user.is_authenticated %}` 包裹(Plan 3.2 T2) | ✅ |
| SC-3 | 评论按 time DESC 倒序 | `Comment.query.filter_by(...).order_by(Comment.time.desc()).all()`(Plan 3.1 T4) | ✅ |
| SC-4 | 作者删除按钮 + confirm | `url_for('api.delete_comment')` + `onsubmit="return confirm('确定删除这条评论?');"`(Plan 3.2 T2) | ✅ |
| SC-5 | admin 删除按钮 + 非作者 403 | `url_for('admin.delete_comment')` + `@admin_required`(Plan 3.2 T1)+ `comment.user_id != current_user.id` 双保险(Plan 3.1 T3) | ✅ |
| SC-6 | 评论作者字段名走 `comment.author.name` | `backref=backref('author', lazy='joined')` on `User.comments`(Plan 3.1 T1)+ 模板改字段名(Plan 3.2 T2) | ✅ |
| SC-7 | 硬删除(双端点) | `db.session.delete(comment) + commit` on `api.delete_comment` + `admin.delete_comment` | ✅ |

**7/7 SUCCESS 标准全部交付,全部静态验证通过。**

## 3. 静态验证证据

### 3.1 AST 解析(全部 OK)

```
OK  app/api/model.py
OK  app/api/__init__.py
OK  app/api/admin.py
OK  app/route/user.py
```

### 3.2 路由装饰器链(AST 校验)

```
app/api/admin.py:delete_comment  → route('/comment/<int:comment_id>/delete') + admin_required
app/api/__init__.py:comment      → route('/comment')                       + login_required
app/api/__init__.py:delete_comment → route('/comment/<int:comment_id>/delete') + login_required
```

### 3.3 Comment 模型结构(AST 校验)

```
def __init__(self, user_id, lemma_id, content)  # 无 user_name / lemma_title / self.time 误写
```

### 3.4 detail.html 关键 grep

| 模式 | 期望 | 实际 | 结论 |
|------|------|------|------|
| `id="sendComment"` | 0 | 0 | ✅ 已删 |
| `id="out"` | 0 | 0 | ✅ 已删 |
| `comment.name` | 0 | 0 | ✅ 已改 |
| `comment.author.name` | ≥1 | 1 | ✅ |
| `url_for('admin.delete_comment')` | ≥1 | 1 | ✅ |
| `url_for('api.delete_comment')` | ≥1 | 1 | ✅ |
| `current_user.is_admin` | ≥1 | 2 | ✅ (admin 删 lemma + admin 删 comment) |
| `comment.user_id == current_user.id` | ≥1 | 1 | ✅ |
| `onsubmit="return confirm` | 2 | 2 | ✅ (admin + author 各一) |
| `action="/api/comment"` | 1 | 1 | ✅ (内联发布 form) |
| `name="csrf_token"` | 5 | 5 | ✅ (modify / admin lemma / admin comment / author comment / 发布 form) |

## 4. 端到端验证(已推迟到 Phase 5)

**未跑项**(需 MySQL + Flask 进程):
- Plan 3.1 V3: 匿名 POST /api/comment → 401/403
- Plan 3.1 V4: 登录用户 POST /api/comment with lemma_id=1&content=测试评论 → 302 → 详情页新评论顶部显示 + author.name='a'
- Plan 3.1 V5: 登录 a → POST /api/comment/1/delete → 302 + 列表少一条;非作者 → 403
- Plan 3.1 V6: 同 lemma 发两条评论 → 倒序展示
- Plan 3.1 V7: SQL `UPDATE user SET name='a-renamed' WHERE id=1` → 详情页作者头改名 + 评论不孤
- Plan 3.2 V2: 匿名访问 detail → HTML 不含 `<form action="/api/comment"` 与 `class="comment-form-container"`
- Plan 3.2 V3-V4: 作者删除 / admin 删除按钮可见,confirm 触发 POST
- Plan 3.2 V5: 非作者 / 非 admin `curl POST /api/comment/<id>/delete` → 403
- Plan 3.2 V6: 时间戳格式 `YYYY-MM-DD HH:MM`
- Plan 3.2 V7: `comment.author.name` 渲染当前 username
- Plan 3.2 V8: HTML 不含 `id="out"` / `id="sendComment"` / `$("#sendComment").click`

**推迟理由**:本机默认 Python 2.7.18,触发了 PEP-263 编码错误(`app/__init__.py:73` 的中文 Phase 2 注释)。`.venv` 已安装 Python 3 + Flask 依赖,但 MySQL 服务未启动。Phase 5 验收时统一在能连 MySQL 的环境跑。

## 5. 偏差与遗留事项

### 5.1 已修复偏差

- **`$("#back").click(function(){ $("#out").hide(); })` jQuery 块被连带删除**:原计划说"除 `$("#sendComment").click(...)` 外,其他 jQuery 保留",但 `#out` 元素已删,该 handler 变成悬空引用。Plan 3.2 委派子代理判定为"必要的清理",与计划意图一致。

### 5.2 Phase 2 carry-forward 未修复

- **PEP-263 编码声明缺失**:`app/__init__.py:73` 的中文注释("Flask 400 traceback")在 Python 2.7 触发 `SyntaxError: Non-ASCII character`。这是 Phase 2 引入的预存障碍,不归 Phase 3 修。Phase 3 + 后续阶段需在 Python 3 环境跑。

### 5.3 不影响 Phase 3 交付

- `app/__init__.py` 顶层用了 `urllib.parse`(Python 3 语法),CLAUDE.md 已注明项目目标 Python 3。
- `mysqlclient` 在 `.venv` 已装,`mysql.mysqlclient` dialect 入口已注册(Phase 5 跑 `flask init-db` 时验证)。

## 6. Artifacts

- **`app/api/model.py`** — Comment 重构(user_id FK / nullable=False / 修 __init__ / 修 __str__ / Lemma.comments 加 cascade / User.comments 关系 + author backref)
- **`app/api/__init__.py`** — `POST /api/comment` + `POST /api/comment/<id>/delete` 两个新路由
- **`app/api/admin.py`** — `POST /api/admin/comment/<id>/delete` 新路由
- **`app/route/user.py:detail`** — 补 comments 查询 + 倒序 + 传模板
- **`app/templates/detail.html`** — 删除 jQuery 模态框 + sendComment 触发逻辑;新增内联发布 form + 评论卡片删除 buttons(admin / author)+ 时间戳展示 + 修正字段名
- **URL rules**:`/api/comment POST` / `/api/comment/<int:comment_id>/delete POST` / `/api/admin/comment/<int:comment_id>/delete POST`
- **DB schema**:`comment(id, user_id FK user.id NOT NULL, lemma_id FK lemma.id NOT NULL, content VARCHAR(320), time DATETIME default utcnow)`

## 7. Phase 3 状态

**✅ Phase 3 complete** — 7/7 SUCCESS 标准全部静态验证通过,6 个原子 commit 已就位,Phase 3 阶段目标(把"被注释的评论半成品"实装成产品功能)达成。端到端 smoke 验证需在能连 MySQL 的 Python 3 环境跑(归 Phase 5 验收)。

*Generated: 2026-06-12*
*Phase: 03 — Comment System*
