# Phase 5: Docker Deployment, Tests & Acceptance - Discussion Log

**Discussion date:** 2026-06-12
**Discussed by:** chujunqi + Claude

## Selected Gray Areas

1. ✓ Docker entrypoint 启动协议
2. ✓ README 部署文档深度与形态

未选(走 Claude's Discretion 默认):
- pytest 测试环境配置
- gunicorn + 反代细节

---

## Discussion Trace

### Area 1: Docker entrypoint 启动协议

#### Q1-1: Docker entrypoint 首次 vs 重启 如何幂等?不能重启炸掉生产数据。

**Options presented:**
- 检表行数 + --if-empty
- init-schema + 手动 init-db
- 锁文件 .initialized

**User selected:** 检表行数 + --if-empty(D-75)

**Rationale:** Phase 2 D-15 既有 `init_db()` 函数加 `if_empty=False` 参数最小扩展,CLI 加 flag。容器重启**不**清生产数据,首次启动**自动**初始化。比锁文件方案更原子(SQL 查询而非文件系统状态)。

#### Q1-2: MySQL 启动慢于 app 时,entrypoint 怎么处理?

**Options presented:**
- 内联 Python 重试 30s
- 靠 docker --restart
- 不等 + README 提示

**User selected:** 内联 Python 重试 30s(D-76)

**Rationale:** 零外部依赖(stdlib socket),用户体验比"docker restart 反复退出"更平滑。30s 上限兜底防止无限循环。

#### Q1-3: entrypoint 脚本语言 + 是否走非 root 用户?

**Options presented:**
- sh 脚本 + USER appuser
- Python 启动脚本 + USER
- root + sh(最简)

**User selected:** root + sh(最简,D-77)

**Rationale:** Demo 性质 + 外部 nginx 反代已隔离;sh 兼容 python:3.11-slim 默认 shell(免 apt-get install bash 12MB)。`exec gunicorn` 让 gunicorn 作为 PID 1,SIGTERM 正常转发。

---

### Area 2: README 部署文档深度与形态

#### Q2-1: README 部署文档面向怎样的读者?

**Options presented:**
- 资深运维(简洁,~150 行)
- Docker 新手(手把手,~400 行)
- 中间(示例主导,~250 行)

**User selected:** 资深运维(简洁,D-78)

**Rationale:** PROJECT.md 显式假定第三方"陌生开发者根据 README 启动",但本项目交付目标是产品雏形,读者画像是有 Docker / MySQL / nginx 基线知识的开发者。150 行覆盖 env 表 + docker run + nginx snippet + smoke 验收清单即可。

#### Q2-2: TEST-05 验收文档是独立文件还是在 README 里?

**Options presented:**
- 全进 README.md
- README + DEPLOY.md + ACCEPTANCE.md
- README + ACCEPTANCE.md

**User selected:** 全进 README.md(D-79)

**Rationale:** 单一入口,降低读者认知负担。资深运维偏好"一个文件搞定"。README 结构清晰分章节即可。

#### Q2-3: compose / nginx 示例需要多丰富?

**Options presented:**
- docker-compose.example.yml + nginx.conf.example(完整文件)
- 只给 docker run + nginx snippet(全 inline 在 README)
- compose(仅 app) + nginx snippet

**User selected:** compose(仅 app) + nginx snippet(D-80)

**Rationale:** 给运维一个可复用的 compose yaml(降低 copy-paste 错误),但**不**包含 MySQL service(避免"compose 里有 mysql ⇒ 项目打包 mysql"的误导)。nginx 由于本身配置简单 + 风格差异大,给 snippet 即可,不拆独立文件。

---

## Carried-Forward Decisions(未重新讨论)

Phase 1-4 全部 D-01..D-74 + CD-01..CD-17 锁定决策直接生效,Phase 5 不重谈。关键链接:

- Phase 2 D-05/06/07:env vars 清单 + FLASK_SECRET fallback + DB URI 拼装
- Phase 2 D-13..D-16/D-25:init_db() 模块函数 + `flask init-db` CLI
- Phase 2 D-22/D-23/D-24:admin 蓝图 + `@admin_required` + `User.is_admin` + `flask promote-admin` CLI
- Phase 3 D-26..D-41:Comment 模型 + 作者删除 + admin 删除
- Phase 4 D-46/D-73:HTMX HX-Request 分支(Phase 5 不在 smoke 覆盖)
- Phase 4 D-53:Pico.css + HTMX CDN(README 中提示外网访问需求)

详细 carry-forward 清单见 05-CONTEXT.md § Canonical References。

---

## Claude's Discretion Items(未直接询问的决策)

- **pytest DB 后端:** SQLite in-memory(CD-25)— 速度优先,无需 MySQL container
- **conftest 注入策略:** module-level Flask 实例直接 `app.config.update()`,不引入 factory(CD-26)
- **CSRF 在测试中关闭:** WTF_CSRF_ENABLED=False(CD-27)
- **test_admin.py 与 test_smoke.py 分离:** ROADMAP SUCCESS 6 推荐(CD-28)
- **HTMX 路径不覆盖:** 整页 302 路径足够 smoke(CD-29)
- **gunicorn workers=2 threads=4 timeout=30:** 适合 demo + 小流量(CD-21)
- **ProxyFix 启用:** trust 1 层代理(CD-22)
- **不增加 /healthz:** 运维通过 gunicorn 启动日志判断(CD-23)
- **日志走 stdout:** Docker 标准(CD-24)
- **Makefile 简洁:** make test / smoke / docker-build / docker-run(CD-30)
- **conftest.py 位置:** tests/conftest.py(CD-35)
- **不安装调试工具:** vim/curl 等不进镜像(CD-37)

如运维 / planner 对默认有不同看法,在 plan-phase 阶段可重启讨论。

---

## Deferred Ideas Summary

全部记录于 05-CONTEXT.md § Deferred Ideas。主要:
- CI/CD pipeline → V2-OPS-01
- K8s / Helm → V2-OPS-02
- 监控 / OTel → V2-OPS-03
- pytest 覆盖率 → V2
- MySQL 容器测试 → V2
- App Factory 重构 → V2
- /healthz 端点 → V2
- 多架构镜像 → V2

---

*Discussion log: 2026-06-12*
