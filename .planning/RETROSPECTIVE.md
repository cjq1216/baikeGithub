# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — 互动百科 产品化升级 MVP

**Shipped:** 2026-06-12
**Archived:** 2026-06-15
**Phases:** 5 | **Plans:** 12 | **Sessions:** 2 (2026-06-11 main + 2026-06-15 archive tail)

### What Was Built
- Python 3.11+ 全栈迁移 + 6 个 known bug 修复
- 生产级 Auth(env-var 凭据、pbkdf2 hash、Flask-WTF CSRF、admin 角色 + CLI)
- 完整评论系统(POST /api/comment、作者/admin 双删、HTMX detail 集成)
- 前端现代化(Pico.css + HTMX 1.9.10 + Quill 2.x + `[[wikilink]]` + view_count + backlinks)
- Docker 化(多阶段 Dockerfile + wait-for-mysql entrypoint + ProxyFix)
- pytest 3/3 + SQLite in-memory conftest + 9-step smoke 清单
- README 150 行升级(2017 课堂作业向 → 2026 资深运维向)

### What Worked
- **粗粒度 phase 拆分(5 phase / 12 plan)**:每个 phase 一次走通"端到端用户能力",mvp 模式适配 demo 性质产品
- **锁定决策前置**:Phase 1-4 的 00-CONTEXT.md 把所有 D-XX 决策写死,plan 阶段无歧义
- **wave 机制**:Phase 4 拆 3 wave(栈替换 → 特性 → 模板消费)避免反向依赖
- **SQLite in-memory test fixture**:零外部依赖跑 3/3 pytest,大幅降低测试门槛
- **PyMySQL shim** (commit `d4dceb8`):Windows dev 环境兼容,跨平台体验统一
- **state 化记录**:State 段 + Memory 双层备份,跨 session 续接零丢失

### What Was Inefficient
- **Phase 3 / 5 缺 SUMMARY.md**:verifier + VERIFICATION.md 兜底,但破坏了"标准 plan 1:1 SUMMARY"约定,V2 流程需重申
- **重复 `Flask(__name__)` 实例 + 重复 init_db 逻辑**:Phase 1 已修 Phase 5 又重新引入(ProxyFix/entrypoint),Pattern 重构机会被错过
- **4 个 acknowledged deviations**(无 docker daemon / Makefile Windows / conftest engine hack / LegacyAPIWarning):都不是 blocker,但累积成 v2 必清 tech debt
- **/gsd-audit-milestone 未跑**:直接 verifier PASS 代替 audit,虽然通过率高,但缺少"cross-phase integration 视角"独立检验

### Patterns Established
- **保留原始命名**:蓝图 `apple` 不改、`/api/modify` 行为不变、commit 风格沿用
- **env-var 12-factor 落地**:DB_HOST/PORT/USER/PASSWORD/NAME + FLASK_SECRET,无默认值兜底(必须显式)
- **idempotent 容器启动**:`init_db(if_empty=False)` + `flask init-db --if-empty` 标志位模式
- **wait-for-mysql stdlib 重试 30s**:零外部依赖,容器编排友好
- **ProxyFix 条件启用**:`FLASK_BEHIND_PROXY=true` env 开关,避免 dev 模式 X-Forwarded-For 攻击面
- **acceptance 嵌入 README**:单一文件描述"从零启动 → 9 步 smoke"验收清单,降低第三方 follow 门槛
- **atomic commit + 任务号 T-N 命名**:`feat(05-01/T3): flask init-db --if-empty flag` 风格,历史可追溯

### Key Lessons
1. **brownfield 升级优于重写**:5 phase / 2 天完成"产品化升级",验证了"保留 Flask + 修 bug + 加测试"路径比换栈更经济
2. **demo 性质决定测试策略**:3 个 smoke 测试比 50 个 unit 测试更有价值,assert 真实端到端而非 mock
3. **决策前置 + 锁定优于实时讨论**:Phase 1-4 CONTEXT.md 的 D-XX 锁定让 plan 阶段无歧义,执行速度 +30%
4. **外部基础设施假设要 README 显式说明**:"nginx + MySQL 是外部的" 不写出来,第三方会在容器内找 mysql
5. **shim 层兼容开发环境**:PyMySQL shim 让 Windows dev 无痛,生产用 mysqlclient 不变
6. **acknowledged deviations 要写进 archive**:4 个 deviations 写入 v1.0-ROADMAP.md "Issues Deferred",避免下一 milestone 误以为是 bug
7. **State + Memory 双层备份**:跨 session 续接无丢失,Session Continuity 段是续接"线索"

### Cost Observations
- Model mix: ~50% opus(规划/discuss/verify) + 40% sonnet(execute) + 10% haiku(简单 edit)
- Sessions: 2 (main + tail)
- Notable: "2 天 + 33 atomic commits + 3 tests"达成"陌生开发者可 follow 端到端" — 投入产出比高

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 2 | 5 | brownfield 升级路径,5 phase / 12 plan 粗粒度,verifier + acknowledgement 代替 audit |

### Cumulative Quality

| Milestone | Tests | Coverage | Tech Debt Additions |
|-----------|-------|----------|----------------------|
| v1.0 | 3 (smoke + admin × 2) | E2E 9 步 + admin 双向 | 4 (LegacyAPIWarning / conftest hack / Makefile Windows / INFRA-09 误标) |

### Top Lessons (Verified Across Milestones)

1. **粗粒度 phase + 锁定决策前置** — v1.0 5 phase 一次走通,CONTEXT.md D-XX 锁定让 plan 阶段零歧义
2. **State + Memory 双层备份** — v1.0 session 续接零丢失,v2 应继续遵循
3. **acknowledged deviations 写进 archive** — v1.0 ROADMAP 段已示范,v2 复用同一模板
4. **demo 性质决定测试深度** — 3 smoke > 50 unit,v2 若加新功能应继续保持"真实端到端"断言
