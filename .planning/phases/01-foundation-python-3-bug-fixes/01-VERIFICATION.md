---
status: passed
phase: 01-foundation-python-3-bug-fixes
verified_date: 2026-06-11
must_haves_score: 8/8
requirements_covered: [INFRA-01, INFRA-02, INFRA-03, INFRA-04]
findings:
  critical: 0
  warning: 0
  info: 0
---

# Verification: Phase 1 — Foundation (Python 3 + Bug Fixes)

## Goal Recap

The existing Flask app runs cleanly on Python 3.11+ with all known runtime bugs and code smells eliminated — nothing else changes. (Per ROADMAP § Phase 1)

The current codebase state was verified against (a) the four Success Criteria in ROADMAP.md, (b) the `must_haves` declared in both PLAN.md frontmatter blocks, and (c) the INFRA-01..04 requirements. A full end-to-end smoke flow was re-run live against the remote MySQL (162.14.107.126:3307) using the freshly built `.venv/` — all 8 assertions pass.

## Must-Haves Coverage

| ID | Truth | Status | Evidence |
|----|-------|--------|----------|
| INFRA-01a | App starts via `python run.py` on Python 3.11+; home page loads without 500 | ✓ VERIFIED | `.venv/Scripts/python.exe --version` → `Python 3.14.5`; `from app import app; len(list(app.url_map.iter_rules()))` → 15 rules; smoke step 1 (`GET /api/reset`) returns 200 with `{"error":false}` |
| INFRA-01b | No `reload(sys)` / `sys.setdefaultencoding` calls remain | ✓ VERIFIED | `grep -rn "reload(sys)\|setdefaultencoding" app/` only matches the three new "no setdefaultencoding needed" comment lines; no executable occurrences |
| INFRA-02a | `requirements.txt` lists Python 3 stack (Flask 3.x, Flask-Login 0.6+, Flask-SQLAlchemy 3.x, mysqlclient 2.2+) — no `mysql-python` | ✓ VERIFIED | `requirements.txt` is exactly 4 lines: `Flask>=3.0,<4.0`, `Flask-Login>=0.6,<1.0`, `Flask-SQLAlchemy>=3.0,<4.0`, `mysqlclient>=2.2,<3.0`; no `mysql-python`/`MySQLdb` top-level |
| INFRA-02b | All runtime imports succeed on Python 3.11+ | ✓ VERIFIED | `import flask(3.1.3), flask_sqlalchemy(3.1.1), flask_login(0.6.3), MySQLdb(2.2.8)` all exit 0 |
| INFRA-03a | `app/api/model.py` no longer creates a duplicate `Flask(__name__)` | ✓ VERIFIED | `grep -rn "Flask(__name__)" app/` matches only `app/__init__.py:10`; `model.py:6` is now `db = SQLAlchemy()` (deferred, no app arg) |
| INFRA-03b | `/api/modify` returns 302 (no 500 / NoneType); lemma is UPDATEd, not duplicate-INSERTed | ✓ VERIFIED | Smoke step 6: `POST /api/modify` with `newTitle=T1&newContent=<p>updated</p>` returns 302; `Lemma.query.filter_by(title='T1').count() == 1`; `content == '<p>updated</p>'` |
| INFRA-04a | All three models declare `__tablename__` (not `__tablenanme__`) | ✓ VERIFIED | `grep -rn "__tablenanme__" app/` → 0 matches; `User.__tablename__, Lemma.__tablename__, Comment.__tablename__` → `user lemma comment`; tables declared at model.py lines 10, 24, 39 |
| INFRA-04b | `/user/detail` returns 200 for valid title, 302 + flash for missing | ✓ VERIFIED | Smoke step 5: `POST /user/detail` with `linklist=T1` → 200 with `hello` in body. Smoke step 8: `POST /user/detail` with `linklist=__nonexistent__` → 302 to home with flash "所查词条不存在". Handler at `app/route/user.py:39-46` uses `.all()` and has empty-list guard |

**Score:** 8/8 must-haves verified

## Requirements Traceability

| Requirement | Plan | Truth(s) | Status |
|-------------|------|----------|--------|
| INFRA-01 (Python 3.11+; no `reload(sys)` / `setdefaultencoding`) | 01-01 | INFRA-01a, INFRA-01b | ✓ SATISFIED |
| INFRA-02 (`mysql-python` → `mysqlclient`; fresh venv works) | 01-01 | INFRA-02a, INFRA-02b | ✓ SATISFIED |
| INFRA-03 (no duplicate `Flask(__name__)` in model.py) | 01-02 | INFRA-03a, INFRA-03b | ✓ SATISFIED |
| INFRA-04 (`__tablenanme__` → `__tablename__` in all 3 models) | 01-02 | INFRA-04a, INFRA-04b | ✓ SATISFIED |

## Smoke Verification

End-to-end flow re-executed against remote MySQL (`162.14.107.126:3307` / `baike` / `cjq`) using `app.test_client()` (same 8 assertions as Plan 01-02 Task 4):

| # | Endpoint | Method | Status | Assertion |
|---|----------|--------|--------|-----------|
| 1 | `/api/reset` | GET | 200 | body `{"error":false}\n` |
| 2 | `/api/regist` (`name=tester&password=pw`) | POST | 302 | (auto-login via `login_user`) |
| 3 | `/api/add` (`title=T1&content=<p>hello</p>`) | POST | 302 | lemma created |
| 4 | `/user/search` (`searchtext=T1`) | POST | 200 | `b'T1'` in body |
| 5 | `/user/detail` (`linklist=T1`) | POST | 200 | `b'hello'` in body |
| 6 | `/api/modify` (`newTitle=T1&newContent=<p>updated</p>`) | POST | 302 | NO 500 / NO NoneType |
| 7 | `/user/detail` (`linklist=T1` re-fetch) | POST | 200 | `b'updated'` in body |
| 8 | `/user/detail` (`linklist=__nonexistent__`) | POST | 302 | empty-guard fires, redirects to home |

Post-conditions: `Lemma.query.filter_by(title='T1').count() == 1` (UPDATE, not duplicate INSERT) and `content == '<p>updated</p>'` (persistence verified).

## Files Actually Modified (vs claimed)

Cross-checked against git diff (working tree) and SUMMARY frontmatter:

| File | Claimed in SUMMARY | Verified in working tree |
|------|--------------------|--------------------------|
| `requirements.txt` | M (4-line Python 3 stack) | ✓ exact content match |
| `app/__init__.py` | M (line 1 UTF-8 comment) | ✓ line 1 is the new comment; line 12 still has hardcoded MySQL credentials (per pre-condition for smoke test — CR-01 finding, see Notes) |
| `app/api/__init__.py` | M (lines 1-4 reload block removed) | ✓ line 1 is the new comment; lines 61-73 `/api/modify` is the lookup-then-mutate rewrite |
| `app/api/model.py` | M (reload block + duplicate Flask + 3 typos) | ✓ no `from flask import Flask`; `db = SQLAlchemy()` at line 6; `__tablename__` correct in all 3 models; no `__tablenanme__` |
| `app/route/user.py` | M (`/user/detail` body rewrite) | ✓ lines 39-46: `.all()` + empty-list guard + `url_for('apple.home')` redirect |
| `app/__init__.pyc` + 4 other `.pyc` files | D (stale 2017 byte-code) | git status shows no uncommitted `.pyc` deletions; the original SUMMARY commit `7519782` already removed them |

No divergence between SUMMARY claims and the working tree. The intermediate commit that switched the MySQL URI to the remote `162.14.107.126:3307` host is a user-requested pre-condition explicitly out of scope for Phase 1's INFRA-01..04 contract; it is referenced in `01-REVIEW.md` as Critical issue CR-01 and deferred to Phase 5 (`INFRA-09`).

## Anti-Patterns Found

None blocking. Code review (`01-REVIEW.md`) flagged 3 Critical + 5 Warning + 4 Info findings — these are all pre-existing or Phase-2/4/5-deferred concerns, not regressions introduced by Phase 1:

- CR-01 (hardcoded prod MySQL credentials) — pre-condition for smoke test, planned in Phase 5
- CR-02 (no owner check on `/api/modify`) — pre-existing pattern, planned in Phase 2 (`/api/admin/...` + role check)
- CR-03 (no `@login_required` on `/user/detail`) — pre-existing pattern, planned in Phase 2
- WR-01..05, IN-01..04 — all documented and tracked in `01-REVIEW.md` for the relevant later phase

## Deferred Items

None. The CR-01..03 / WR-01..05 / IN-01..04 findings are concerns but they were either (a) pre-existing before Phase 1 or (b) explicitly out-of-scope per the PLAN frontmatter `must_haves` (which lists only INFRA-01..04). They are tracked in the codebase review and roll into later phases — not gaps for Phase 1's contract.

## Gaps

None. Phase 1's goal is fully achieved in the codebase.

## Notes for Next Phase (Phase 2)

Phase 2 (`Security & Auth Hardening`, depends on Phase 1) should pre-empt the following by either including the fixes or explicitly deferring with rationale:

- **CR-01 (urgent)** — Rotate the leaked `Cjq@123456` password on the remote MySQL server and migrate `app/__init__.py:12` to read `os.environ['BAIKE_DB_URI']`. `git filter-repo` is needed to strip the credential from history. Plan 2.1 (`AUTH-05` + `INFRA-09`) is the natural home.
- **WR-04** — `app.secret_key = '1frMFuWRVPV1'` is hardcoded; Phase 2 must move it to env vars (`FLASK_SECRET`) for the same reasons as CR-01.
- **CR-02** — Phase 2 should add an `owner_id` / role check on `/api/modify`; otherwise the fix in 01-02 is functionally correct but inherits broken authz.
- **CR-03** — Phase 2 should add `@login_required` to `/user/detail` for symmetry with `/user/add` and `/user/modify`; the routing asymmetry is a real defect.
- **WR-05** — Phase 2/4 should add a length cap on `Lemma.title` and `Lemma.content` to prevent silent truncation / unbounded writes.
- **IN-01** — `Comment.__init__` / `__str__` are still broken; Phase 3 must fix these before the comment routes are uncommented.
- **IN-02** — `# coding=utf-8` at `app/route/user.py:1` is harmless (PEP 263 default for UTF-8) but inconsistent with the other files; a future cleanup pass could drop it.

---

_Verified: 2026-06-11_
_Verifier: Claude (gsd-verifier)_
_Method: Static grep + import smoke + handler source inspection + full end-to-end smoke (8 assertions + 2 post-conditions) against remote MySQL via Flask test client_
