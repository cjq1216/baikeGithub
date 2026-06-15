# Milestones: 互动百科

Living history of shipped versions. Each entry summarizes what was delivered, when, and links to full archive.

---

## v1.0 — 互动百科 产品化升级 MVP

**Shipped:** 2026-06-12
**Phases:** 5 | **Plans:** 12 | **Tasks:** 33+ atomic commits | **Tests:** 3/3 pytest passing

**Core value delivered:** 一个陌生开发者能根据 README 启动 Docker 容器、注册账号、创建词条、发布评论、并以管理员身份看到完整端到端流程。

### One-liner
将 2017 年 Python 2 时代的 Flask + MySQL 课堂作业(641 宿舍软工大作业)从"能跑通的课堂作业"升级为"可部署演示的产品雏形"。

### Key accomplishments

1. **Python 2 → 3.11+ 全栈迁移**(reload(sys)/mysql-python/sys.setdefaultencoding 全部移除,mysqlclient + PyMySQL shim 兼容 Windows)
2. **6 个 known bug 全部修复**(`/api/modify` 500、`/user/detail` BaseQuery、`__tablenanme__` typo、重复 Flask 实例、明文密码、硬编码凭据)
3. **生产级 Auth 体系**(env-var secret_key、pbkdf2 hash、Flask-WTF CSRF 全站、二元 admin 角色 + `flask promote-admin` CLI)
4. **完整评论系统实装**(Comment schema user_id FK + cascade、作者/admin 双删端点、HTMX detail 页交互)
5. **前端现代化升级**(Bootstrap 3 / jQuery 1.11 / wangEditor 全部移除 → Pico.css + HTMX 1.9.10 + Quill 2.x;`[[wikilink]]` 双向渲染、view_count 原子 +1、backlinks)
6. **Docker + 测试 + 文档三位一体交付**(多阶段 Dockerfile + wait-for-mysql entrypoint + SQLite in-memory pytest 3/3 绿 + 9 步 smoke 清单嵌入 README)

### Verifier verdict

**PASS** (high confidence, 8/8 SUCCESS criteria verified, 4 acknowledged deviations all acceptable)

### Tech debt carried into v2

- 41 条 SQLAlchemy LegacyAPIWarning(Query.get() → db.session.get() refactor)
- conftest.py engine 替换 hack(Flask-SQLAlchemy 3.x 缓存)
- Makefile Windows 不可用(Git Bash 无 make;Linux verifier 端跑)

### V2 candidate requirements (19 条,待 `/gsd-new-milestone` 启动时正式立项)

- V2-AUTH-01..04: email 验证 / 密码重置 / OAuth / 2FA
- V2-AUTH-05: 登录失败限流
- V2-CONTENT-01..04: 版本历史 / 全文搜索 / 词条保护 / editor 角色
- V2-COMMENT-01..02: 评论编辑 / 线程回复
- V2-OPS-01..04: GitHub Actions CI / K8s / 监控 / `/healthz` endpoint
- V2-FRONT-01..03: i18n / PWA / SSE WebSocket

**优先推荐**:V2-OPS-01 (CI) / V2-OPS-04 (healthz) / V2-AUTH-01 (email 验证) / V2-CONTENT-01 (revision history) / V2-FRONT-03 (real-time)

### Archive files

- `.planning/milestones/v1.0-ROADMAP.md` — 全 5 phase 详情 + 决策 + tech debt
- `.planning/milestones/v1.0-REQUIREMENTS.md` — 46/46 v1 标 Complete + 19 v2 candidates

### Git tag

`v1.0` (annotated) — 见本次 commit

---

*For current project status, see `.planning/ROADMAP.md` (collapsed to v1.0 SHIPPED) and `.planning/PROJECT.md` (v1.0 Validated)*
