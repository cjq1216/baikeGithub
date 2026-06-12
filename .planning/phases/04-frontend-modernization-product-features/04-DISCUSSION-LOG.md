# Phase 4: Frontend Modernization & Product Features - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 04-Frontend Modernization & Product Features
**Areas discussed:** 编辑器选型, HTMX 范围, Wiki 链接 red-link 行为, 静态资源加载, Quill 工具栏, 搜索触发, 评论 swap, view_count 发起, CDN+SRI, 登录状态轮询, red-link 视觉, HTML 安全过滤, schema 迁移, detail GET 化, 相关词条位置, updated_at 触发, 暗色模式, 字体, 词条列表形态, 导航形态

---

## 1. 富文本编辑器选型

| Option | Description | Selected |
|--------|-------------|----------|
| Quill 2.x(推荐) | WYSIWYG, ~200KB, 中文 IME 友好, 产出标准 HTML, License BSD-3 | ✓ |
| EasyMDE + CodeMirror | 纯 Markdown, ~150KB, 数据存储从 HTML 改 Markdown, wiki 链接正则提取更易 | |
| Tiptap(ProseMirror 内核) | 现代框架化 WYSIWYG, ~300KB, schema-first 可编程, 中文化成熟度一般 | |
| Claude 自主决断 | 让 Claude 按'轻量 + 中文友好 + HTML 兼容'选 | |

**User's choice:** Quill 2.x(推荐)
**Notes:** 选用 WYSIWYG 风格与既有 wangEditor 心智模型一致,迁移成本最低;中文输入法回车不重置。

## 2. HTMX 局部刷新范围(多选)

| Option | Description | Selected |
|--------|-------------|----------|
| 搜索边输边出(推荐) | home.html keyup 300ms, hx-get /user/search, 取代整页跳转 | ✓ |
| 评论发布不刷新 | Phase 3 D-28 升级为 HTMX, hx-post /api/comment, hx-swap afterbegin | ✓ |
| 登录/注册状态条局部刷新 | 导航栏右上角根据 current_user 实时变 | ✓ |
| view_count 实时计数 | 详情页打开后异步 POST 一次 view_count | ✓ |

**User's choice:** 全部 4 项全选(回答中混入"页面样式"字样,被理解为补充标签而非新选项)
**Notes:** 实际选中"全部 4 个 HTMX 流程"。理由:Phase 4 是"前端现代化",HTMX 是核心展示点;多流程比单流程更"现代感"。

## 3. Wiki 链接红色虚线行为

| Option | Description | Selected |
|--------|-------------|----------|
| 跳到 add.html 并预填 title(推荐) | /user/add?title=<URL-encoded>, 自动填到 title input | ✓ |
| 链接到 home 然后用户再点"添加" | 红色虚线是死链 + 普通文本提示 | |
| 链接直接 POST 创建空词条 | 激进 UX, 跳到 edit 模式 | |

**User's choice:** 跳到 add.html 并预填 title(推荐)
**Notes:** 最少点击路径,符合 wiki 直觉(类似 wikipedia 的"创建此页面")。

## 4. 静态资源加载方式

| Option | Description | Selected |
|--------|-------------|----------|
| 本地 vendor, 删 jQuery/Bootstrap/wangEditor | 镜像稍大但离线可用, 与 Phase 2/3 风格一致 | |
| CDN(jsdelivr / unpkg) | 镜像最小, 但部署时要求外网可达 | |
| 混合: Pico.css/HTMX 用 CDN, 编辑器本地 | 轻量库走 CDN 节省体积, 复杂编辑器本地 vendor | ✓ |

**User's choice:** 混合 — Pico.css + HTMX 走 CDN, Quill 走本地
**Notes:** Pico.css/HTMX 是头部轻量库,CDN 加载快且不占镜像;Quill 编辑器体积大,本地 vendor 保证稳定。**注意**:Phase 5 README 部署文档要写明 CDN 外网要求。

## 5. Quill 工具栏按钮配置

| Option | Description | Selected |
|--------|-------------|----------|
| 精简集(推荐) | 粗体/斜体/下划线 + 有序/无序列表 + 标题(H1-H3) + 引用 + 链接 + 清除格式, 8 个按钮 | ✓ |
| 全量 | 含代码块/表格/图片上传/字体/字号/颜色/对齐, ~20 个按钮 | |
| 极简 | 只有粗体/斜体/列表/链接 4 个 | |

**User's choice:** 精简集(推荐)
**Notes:** 词条是说明类文本,不需要表格/代码块/图片(图片上传不在 Phase 4 范围)。

## 6. HTMX 搜索触发策略

| Option | Description | Selected |
|--------|-------------|----------|
| keyup 300ms 延迟 + 1 字符起 + 20 条上限(推荐) | hx-get /user/search hx-trigger 'keyup changed delay:300ms' | ✓ |
| keyup 500ms 延迟 + 2 字符起 + 10 条上限 | 更保守, 请求更少 | |
| Focus 失焦或 Enter 触发 | 不边输边出, 失去 HTMX 最大价值 | |

**User's choice:** keyup 300ms 延迟 + 1 字符起 + 20 条上限(推荐)
**Notes:** 1 字符起即响应,300ms 静默期避免每个键击都发请求。

## 7. HTMX 评论 swap 策略

| Option | Description | Selected |
|--------|-------------|----------|
| 返回新评论 HTML 片段, afterbegin 插入(推荐) | 服务端检测 HX-Request, 返回 _comment.html 子模板, 客户端 hx-swap afterbegin | ✓ |
| 返回整个评论列表片段重染 | 服务端重查 DB 返回最新排序, 客户端 hx-swap outerHTML | |
| 保留 Phase 3 的整页刷新 | 不引入 HTMX 评论发布, 文档标记跳过 | |

**User's choice:** 返回新评论 HTML 片段, afterbegin 插入(推荐)
**Notes:** 覆盖 Phase 3 D-28 决策(整页刷新);新增 `templates/_comment.html` 子模板;失败时 HX-Retarget 重写 form 区块。

## 8. view_count 发起方式

| Option | Description | Selected |
|--------|-------------|----------|
| GET 同步 + SQL UPDATE 原子(推荐) | /user/detail 路由中执行 update(Lemma).where(id=x).values(view_count=view_count+1) | ✓ |
| HTMX 异步 POST 计数 | 详情页打开后 hx-post /api/lemma/<id>/view | |
| GET 同步 + 作者本人不计 | 作者本人在编辑器手动 +1, 其他人 HTMX +1 | |

**User's choice:** GET 同步 + SQL UPDATE 原子(推荐)
**Notes:** LEMMA-05 验收"无 race condition lost-update"通过 SQL `view_count = view_count + 1` 原子表达式保证;作者本人访问也 +1(demo 简化)。

## 9. CDN 选型 + SRI

| Option | Description | Selected |
|--------|-------------|----------|
| jsdelivr + SRI(推荐) | @picocss/pico@2 + htmx.org@1.9.10, 补 SRI 哈希, 内网/课堂使用不会动 | ✓ |
| jsdelivr 不带 SRI | 不带 SRI, 部署最简, 但 CDN 妥协会影响 demo | |
| cdnjs | 只用 cdnjs, 社区维护者多 | |

**User's choice:** jsdelivr + SRI(推荐)
**Notes:** SRI 防止 CDN 被妥协会影响 demo;Phase 5 README 部署文档说明外网访问 jsdelivr 要求。

## 10. 登录/注册状态条轮询

| Option | Description | Selected |
|--------|-------------|----------|
| 仅在 login/logout 后手动刷新(推荐) | 路由响应加 hx-swap-oob 重写导航栏右侧, 不轮询 | ✓ |
| 保持 every 30s 轮询 | 多设备场景下另一台登录后本机导航能及时反映 | |

**User's choice:** 仅在 login/logout 后手动刷新(推荐)
**Notes:** 词条 wiki 不是多设备重交互场景,节约请求/服务端代码;具体实现:login/logout 路由返回 HX-Trigger 事件,base.html 导航栏 hx-get /api/nav-fragment hx-trigger="nav-refresh from:body"。

## 11. Red-link 视觉

| Option | Description | Selected |
|--------|-------------|----------|
| 下划线+红虚线+尾部小字(创建此词条)→(推荐) | 标准 wiki 行为, 类似 wikipedia | ✓ |
| 只要下划线+红色虚线 | 最简 | |
| 下划线+灰背景框+提示 | 不同于 Wikipedia 风格 | |

**User's choice:** 下划线+红虚线+尾部小字(创建此词条)→(推荐)
**Notes:** 符合用户对 wiki 视觉的预期,与 wikipedia 一致。

## 12. Quill HTML 安全过滤

| Option | Description | Selected |
|--------|-------------|----------|
| bleach 白名单过滤(推荐) | 白名单 p/b/i/u/strong/em/a/ul/ol/li/h1-h3/br/blockquote/pre/code, a 标签要求 http:// https:// / 开头 | ✓ |
| 不过滤, 只走 Jinja2 \|safe | Quill 内部已过滤 <script>, 代码最简 | |
| 自定义简易过滤 | 手写 re.sub 过滤, 免依赖但可被绕过 | |

**User's choice:** bleach 白名单过滤(推荐)
**Notes:** 安全优先,接受 ~50KB bleach 依赖;a 标签 href 限制防止 javascript: 协议 XSS。

## 13. 数据库 schema 迁移

| Option | Description | Selected |
|--------|-------------|----------|
| 走 init_db() drop+create(推荐) | 与 Phase 2 D-13..D-16 一致, demo 性质可接受重灌 | ✓ |
| 写 alembic migration | 增量迁移, 保留历史数据, 复杂度+1 | |

**User's choice:** 走 init_db() drop+create(推荐)
**Notes:** Phase 4 不引入 alembic;Phase 5 README 说明首次部署后只能走 init-db 一次性初始化。

## 14. /user/detail GET 化

| Option | Description | Selected |
|--------|-------------|----------|
| 顺带改 GET(推荐) | 路由 methods=['GET'] 或 GET ?title=, result.html form 改 a 链接 | ✓ |
| 不改, 保持 POST | Phase 1 修过 BaseQuery bug 但未改 method, Phase 4 不引入额外路由改动 | |

**User's choice:** 顺带改 GET(推荐)
**Notes:** 与 HTMX 搜索结果点击语义一致(URL 可分享);view_count +1 移到 detail GET 路由首行。

## 15. 相关词条位置

| Option | Description | Selected |
|--------|-------------|----------|
| 评论区下方(推荐) | 词条主体 + 评论 + 相关词条 三段式, Pico.css <aside> | ✓ |
| 侧边栏(桌面)/ 顶部(手机) | 布局更复杂, 需响应式判断 | |
| 不显示, 只看主内容 | Phase 4 跳过 LEMMA-08 | |

**User's choice:** 评论区下方(推荐)
**Notes:** 三段式最自然;空结果时整段不渲染。

## 16. updated_at 触发

| Option | Description | Selected |
|--------|-------------|----------|
| 仅创建/修改词条时(推荐) | updated_at = 词条创建时 / modify 路由中 onupdate=datetime.utcnow | ✓ |
| 评论 + 修改都触发 | 评论发布 / admin 删词条 / 作者修改都更新词条 updated_at | |

**User's choice:** 仅创建/修改词条时(推荐)
**Notes:** 语义清晰:时间代表"词条内容"最后变更,非"该页活动"。

## 17. 暗色主题

| Option | Description | Selected |
|--------|-------------|----------|
| 启用 Pico 默认暗色(推荐) | Pico.css 自带 prefers-color-scheme: dark, 零成本 | |
| 仅亮色 | 固定亮色, 实现最简 | |
| 加手动开关 | 切换按钮 + localStorage + Pico data-theme | ✓ |

**User's choice:** 加手动开关
**Notes:** navbar 右上角图标按钮 + 30 行 JS + localStorage `pico-preferred-color-scheme` 记忆;Pico.css 暗色变量直接用。

## 18. 字体方案

| Option | Description | Selected |
|--------|-------------|----------|
| 系统字体栈(推荐) | Pico.css 默认 system-ui + 中文 -apple-system/PingFang SC/Microsoft YaHei, 零体积 | ✓ |
| Noto Sans SC(CDN) | 跨平台统一中文, 增加 200KB 外部请求 | |
| 本地字体 vendor | 下载 Noto Sans SC woff2 放到 app/static/fonts/, 镜像增加 ~500KB | |

**User's choice:** 系统字体栈(推荐)
**Notes:** 零体积,跨平台一致;Phase 5 部署不需额外说明。

## 19. 词条列表形态

| Option | Description | Selected |
|--------|-------------|----------|
| 卡片网格(推荐) | result.html 改成 grid container, 每个 lemma 一张 Pico.css article card | ✓ |
| 简洁列表 | 保持表格/列表样式, 传统 wiki 风格 | |
| 时间线 | result.html 以时间线展示 | |

**User's choice:** 卡片网格(推荐)
**Notes:** 视觉上"百科"感强;Pico.css `<article>` + `<h3>` + 截断 content 200 字 + 浏览数 + 最后编辑时间。

## 20. 导航形态

| Option | Description | Selected |
|--------|-------------|----------|
| 顶部 inline 导航(推荐) | 主页 / 词条 / 写词条 / 登录 横排, Pico.css <nav> | ✓ |
| 顶部 + hamburger 菜单 | 768px 以下折叠 | |
| 左侧侧边导航 | 垂直导航栏 + 随机词条 / 热门词条 | |

**User's choice:** 顶部 inline 导航(推荐)
**Notes:** 768px 以下 Pico.css 自动 wrap 换行,**不**加 hamburger(CD-10)。

---

## Claude's Discretion

- **CD-10:** 移动端响应式 hamburger 菜单 — 选**不**(Pico.css 自动 wrap 即可)
- **CD-11:** 首页 hero 区大标题搜索框 — 选**否**(保持现有 cover 风格)
- **CD-12:** 错误页(404/500)视觉风格 — Phase 2 D-17..D-19 既有 error.html 一致,Pico.css 重写
- **CD-13:** 词条创建默认值:view_count=0, updated_at=now
- **CD-14:** 评论 swap 失败 UX 细节 — flash + 清空 textarea
- **CD-15:** 暗色切换 localStorage key — `pico-preferred-color-scheme`
- **CD-16:** Pico.css 版本锁定 — `@picocss/pico@2.0.6`
- **CD-17:** HTMX 触发评论 form 客户端错误(网络断/500)时浏览器原生表单兜底

## Deferred Ideas

### 词条版本历史(V2-CONTENT-01)
- 留 v2。本阶段不引入 `lemma_revision` 表。

### 评论编辑 / 嵌套 / markdown(V2-COMMENT-01, 02)
- 留 v2。Phase 4 评论是平铺列表 + 纯文本。

### 全文搜索(V2-CONTENT-02)
- 留 v2。Phase 4 仍用 SQL `LIKE` / SQLAlchemy `contains()`。

### 词条保护 / 锁定(V2-CONTENT-03)
- 留 v2。Phase 4 任何登录用户都可编辑,管理员删除兜底。

### 编辑者 / 版主角色(V2-CONTENT-04)
- v1 维持 regular + admin 二元角色,Phase 4 不引入第三角色。

### alembic / 数据库迁移工具
- Phase 4 不引入。demo 性质接受 drop+create 重灌。

### 图片上传
- Quill 工具栏精简集不含图片上传,Phase 4 不实现文件存储 / OSS / S3 集成。

### 词条 RSS / Atom 订阅
- 留 v2。

### mobile 端 hamburger 菜单
- Phase 4 决策不引入(CD-10)。如 Phase 5 用户强烈要求再补。

### 暗色切换"系统跟随"模式
- Phase 4 简化只做 dark/light 二选一。

### i18n / 移动 App / PWA / 实时更新 / 监控 / CI/CD
- V2 系列,留 v2。
