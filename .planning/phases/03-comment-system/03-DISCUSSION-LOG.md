# Phase 3: Comment System - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 03-Comment System
**Areas discussed:** Comment schema 改造, 删除端点设计, 新评论刷新策略, 审计日志, 二次确认, 删除按钮位置, 评论 content 长度

---

## Comment schema 改造 (COMMENT-06)

| Option | Description | Selected |
|--------|-------------|----------|
| 只保留 user_id FK (推荐) | 删 `user_name` 字段,只留 `user_id` 外键。schema 干净,渲染要 JOIN User 表取 name(N+1 风险由 `backref lazy='joined'` 缓解) | ✓ |
| 保留 user_name 字符串 + 新增 user_id FK | 两列并存:写入时记 username + durable FK。读快,但 username 改名后字段不一致 | |
| 只保留 user_id + 缓存 User.name 渲染时 | 用 `selectinload(Comment.user)` 显式预加载。和方案 1 实际效果一样 | |

**User's choice:** 只保留 user_id FK (推荐)
**Notes:** schema 干净是首要价值。`backref lazy='joined'` 自动 JOIN 解决 N+1,无需 plan 阶段显式 `selectinload`。

### Follow-up: User.comments 关系双向关联

| Option | Description | Selected |
|--------|-------------|----------|
| backref='author', lazy='joined' (推荐) | 模板 `comment.author.name` 一步取 username,自动 JOIN | ✓ |
| backref='user', lazy='select' | 模板 `comment.user.name` 多一次查询 | |
| 不加双向关系,查询时 `db.session.query(User).get(comment.user_id)` | 显式 JOIN,代码冗长 | |

**User's choice:** backref='author', lazy='joined' (推荐) — 隐含在 schema 选项中
**Notes:** backref 命名 'author' 比 'user' 更语义化(comment 里"作者"是 author,User 实体里"用户"是 user)。

### Follow-up: Comment.content 长度

| Option | Description | Selected |
|--------|-------------|----------|
| 保持 String(320) (推荐) | 320 字符够长文评论,与既有 model 一致 | ✓ |
| 扩为 db.Text | 不限长,可贴代码。Phase 3 范围漂移风险 | |

**User's choice:** 保持 String(320) (推荐)
**Notes:** Phase 3 不引入"内容长度策略"。

---

## 删除端点设计 (COMMENT-04/05/07 + ROLE-02)

| Option | Description | Selected |
|--------|-------------|----------|
| 同一个端点 + 权限分流 (推荐) | `POST /api/comment/<id>/delete`,内部按 author/admin 分流,代码简洁 | ✓ |
| 两个独立端点 | `/api/comment/<id>/delete` + `/api/admin/comment/<id>/delete`,职责清晰但 URL 多 | |

**User's choice:** 同一个端点 + 权限分流 (推荐)
**Notes:** 实现细节修订:作者删除走 `api` 蓝图(无 `@admin_required`),admin 删除走 `admin` 蓝图(带 `@admin_required`)。两个端点 + 两道权限墙,既符合"统一逻辑"又 URL 反映权限。已写入 CONTEXT.md D-27 修正。

---

## 新评论刷新策略 (COMMENT-01 vs Phase 4 HTMX 范围)

| Option | Description | Selected |
|--------|-------------|----------|
| 整页刷新 (推荐) | 302 → detail 页,Phase 边界清晰,SUCCESS 1 留 Phase 4 | ✓ |
| Phase 3 提前引入 HTMX | 破坏 Phase 边界,SUCCESS 1 当场满足 | |
| 沿用现有 jQuery 模态框 | 零前端改动,但仍带 jQuery — Phase 4 拆 jQuery 时一起处理 | |

**User's choice:** 整页刷新 (推荐)
**Notes:** Phase 3 不破 Phase 4 的 HTMX 引入节奏。用户体验:评论发布后看到自己评论已在列表顶部(整页刷新后)。

---

## 审计日志 (B-06)

| Option | Description | Selected |
|--------|-------------|----------|
| 不写审计日志 (推荐) | 硬删除后无痕,v1 demo 性质,审计需求低 | ✓ |
| 写 stderr 审计日志 | 走 Flask current_app.logger,Docker logs 可查 | |
| 建独立 audit_log 表 | 最重,可查询历史,但与"轻量 v1 demo"目标不符 | |

**User's choice:** 不写审计日志 (推荐)
**Notes:** 零新依赖、零新表。需要追溯时,Docker logs + admin 行为本身可被外部审计。

---

## 二次确认 (COMMENT-04)

| Option | Description | Selected |
|--------|-------------|----------|
| JS confirm() 弹窗 (推荐) | 浏览器原生,Phase 3 现有 jQuery 还在,加几行 JS 即可 | ✓ |
| 独立确认页面 | 跳中间页再 POST,零 JS 但多一次跳转 | |
| 不加二次确认 | 直接提交,误删无恢复 | |

**User's choice:** JS confirm() 弹窗 (推荐)
**Notes:** SUCCESS 4 明确要求"with confirmation"。`if (!confirm('确定删除这条评论?')) return false;` 加在 `<form onsubmit="...">` 上。

---

## 删除按钮位置 (COMMENT-04/05)

| Option | Description | Selected |
|--------|-------------|----------|
| 每条评论卡片底部 (推荐) | 作者看自己评论右下角"删除",admin 看所有评论右下角"删除" | ✓ |
| admin 独立管理区 | 顶部"管理员操作"区列出所有评论 + 勾选删除 | |

**User's choice:** 每条评论卡片底部 (推荐)
**Notes:** 符合社区型产品习惯(类似微博/B站)。不像 admin 删 lemma 那样走独立 form(因为 lemma 只有 1 条,评论有多条)。内嵌 form 模式: `<form action="..." method="post" style="display:inline">` 模仿 Phase 2 D-22。

---

## 评论 content 长度 (次要)

| Option | Description | Selected |
|--------|-------------|----------|
| 保持 String(320) (推荐) | 320 字符够长文评论,1.3 KB/条 | ✓ |
| 扩为 db.Text | 不限长,可贴代码 | |

**User's choice:** 保持 String(320) (推荐)
**Notes:** 与既有 model 一致,Phase 3 不引入"内容长度策略"。

---

## Claude's Discretion

- **CD-04:** `Comment.time` 保持 `default=datetime.datetime.utcnow`,展示用 `.strftime('%Y-%m-%d %H:%M')`。Phase 4 再考虑 timezone 复杂性。
- **CD-05:** N+1 防护由 D-26 的 `lazy='joined'` 自动处理,plan 阶段无需显式 `selectinload`。
- **CD-06:** 评论内容校验长度 1-320 字符,空内容(纯空格)拒收。
- **CD-07:** `/api/comment` 对 lemma_id 不存在 → flash "词条不存在" + 302 回 home。
- **CD-08:** 删除评论后回到 referrer(同 detail 页)还是 home?推荐 referrer,与 Phase 2 D-11 CSRF 失败回退逻辑一致。
- **CD-09:** admin 删除按钮与作者删除按钮同一行右侧,各管各的 form 端点。两种按钮共用 JS `confirm()` 提示文本(统一"确定删除这条评论?")。

## Deferred Ideas

- **评论编辑 (V2-COMMENT-01)** — PROJECT.md Key Decisions 显式排除
- **评论回复 / 嵌套 (V2-COMMENT-02)** — 留 v2
- **词条 wiki 链接 / view_count / updated_at / 相关词条 (LEMMA-01..08)** — Phase 4
- **模板整体重设计 / HTMX / Pico.css / wangEditor 替换** — Phase 4
- **词条详情页 GET 化 (`/user/detail` 改 GET)** — Phase 4 改路由
- **限流 / 评论频率控制 / 反垃圾** — v2
- **评论 markdown / 富文本输入** — Phase 4 统一换编辑器
- **邮件通知 / 评论被回复提醒** — v2 (需要 SMTP)
