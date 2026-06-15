# Roadmap: 互动百科

**Defined:** 2026-06-11
**Granularity:** coarse (3-5 phases, 1-3 plans each)
**Mode:** mvp — each phase delivers an end-to-end user capability
**Parallel:** true — independent plans within a phase may run simultaneously
**Core Value:** 一个陌生开发者能根据 README 启动 Docker 容器、注册账号、创建词条、发布评论、并以管理员身份看到完整端到端流程。

## Milestones

- ✅ **v1.0 MVP** — Phases 1-5 (shipped 2026-06-12) — see `.planning/milestones/v1.0-ROADMAP.md`
- 📋 **v2** — pending `/gsd-new-milestone` (19 candidate requirements in `.planning/milestones/v1.0-REQUIREMENTS.md` § v2 Requirements)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-5) — SHIPPED 2026-06-12</summary>

- [x] **Phase 1: Foundation (Python 3 + Bug Fixes)** — 应用在 Python 3.11+ 上无 bug 跑通 (completed 2026-06-11)
- [x] **Phase 2: Security & Auth Hardening** — env-var 凭据 + 密码哈希 + CSRF + admin 角色 (completed 2026-06-12)
- [x] **Phase 3: Comment System** — 评论发布/列表/作者删/admin 删 + 详情页评论交互 (completed 2026-06-12)
- [x] **Phase 4: Frontend Modernization & Product Features** — Pico.css + HTMX + Quill + wiki 链接 + view_count + backlinks (completed 2026-06-12)
- [x] **Phase 5: Docker Deployment, Tests & Acceptance** — Dockerfile + entrypoint + pytest 3/3 + README 9-step smoke (completed 2026-06-12)

**Stats:** 5 phases, 12 plans, 46/46 v1 requirements complete, 3/3 tests passing, verifier PASS.

For full details see `.planning/milestones/v1.0-ROADMAP.md`.

</details>

### 📋 v2 (Planned — pending `/gsd-new-milestone`)

暂无规划。V2 候选需求在 `.planning/milestones/v1.0-REQUIREMENTS.md` § v2 Requirements(19 条)。启动 v2 需先跑 `/gsd-new-milestone` 走 questioning → research → requirements → roadmap 流程。

**V2 优先推荐**(从 v1.0 经验提炼,见 PROJECT.md § Next Milestone Goals):
1. **V2-OPS-01** GitHub Actions CI(解决"dev 端无 docker daemon,实际验证需 CI")
2. **V2-OPS-04** `/healthz` endpoint + Docker HEALTHCHECK(解决"人肉看启动日志判断就绪")
3. **V2-AUTH-01** Email 验证(提升用户信任)
4. **V2-CONTENT-01** Lemma revision history + diff viewer(知识库型产品强需求)
5. **V2-FRONT-03** Real-time updates via SSE/WebSocket(评论/浏览数实时刷新)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | ✅ Complete | 2026-06-11 |
| 2. Security & Auth Hardening | v1.0 | 3/3 | ✅ Complete | 2026-06-12 |
| 3. Comment System | v1.0 | 2/2 | ✅ Complete | 2026-06-12 |
| 4. Frontend Modernization | v1.0 | 3/3 | ✅ Complete | 2026-06-12 |
| 5. Docker + Tests + Acceptance | v1.0 | 2/2 | ✅ Complete | 2026-06-12 |
| _v2 — TBD_ | v2 | 0/? | 📋 Planned | — |

---

*Roadmap defined: 2026-06-11*
*Last updated: 2026-06-15 after v1.0 SHIPPED — collapsed to v1.0 details tag, v2 placeholder created*
