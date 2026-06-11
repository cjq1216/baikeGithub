---
phase: 01-foundation-python-3-bug-fixes
plan: 01
subsystem: runtime-foundation
tags: [python-3-migration, dependency-update, in-progress]
dependency_graph:
  requires: []
  provides: [INFRA-01, INFRA-02]
  affects: [plan-01-02-bug-fixes, phase-02-auth, phase-05-docker]
tech-stack:
  added:
    - Python>=3.14 (interpreter)
    - Flask>=3.0,<4.0 (3.1.3 installed)
    - Flask-Login>=0.6,<1.0 (0.6.3 installed)
    - Flask-SQLAlchemy>=3.0,<4.0 (3.1.1 installed)
    - mysqlclient>=2.2,<3.0 (2.2.8 installed; provides MySQLdb shim)
  patterns:
    - "Fresh venv on Python 3.11+ interpreter; mysqlclient uses prebuilt cpXY-cpXY-win_amd64 wheels"
    - "Deferred SQLAlchemy() initialization site unchanged in this plan (Plan 01-02 will consolidate duplicate Flask instance)"
key-files:
  created: []
  modified:
    - requirements.txt
    - app/__init__.py
    - app/api/__init__.py
    - app/api/model.py
decisions:
  - "Pin Flask 3.1.x (3.1.3) — current LTS, no breaking changes for this codebase"
  - "Pin mysqlclient 2.2.8 — confirmed prebuilt wheel for cp314-cp314-win_amd64 (matches Python 3.14.5)"
  - "Remove (not comment) reload(sys) blocks — per RESEARCH § Pitfall 3, commented lines still AttributeError on Python 3"
  - "Extended Task 3 scope to also clean app/api/model.py:2-4 (same Python 2 idiom blocking import) — auto-fix Rule 3"
  - "Delete stale .pyc cache files committed in 2017 — they referenced Python 2 byte-code"
  - "Test/verify commit for Task 4 is empty-tree — plan's <behavior> is command-line smoke, not new test code"
metrics:
  duration: "~5 minutes (env verify + venv + 3 commits)"
  completed_date: "2026-06-11"
---

# Phase 1 Plan 1: Python 3 Migration + Dependency Replacement Summary

Migrated baike codebase from Python 2.7 to Python 3.14.5 by replacing the `mysql-python`/`MySQLdb` dependency with `mysqlclient` and removing all `reload(sys); sys.setdefaultencoding('utf8')` blocks. The Flask app now imports cleanly on Python 3.14.5 with a fresh `.venv/` containing Flask 3.1.3, Flask-Login 0.6.3, Flask-SQLAlchemy 3.1.1, and mysqlclient 2.2.8.

## Task Completion

| # | Task | Type | Commit | Status |
|---|------|------|--------|--------|
| 1 | Verify Python 3.11+ interpreter and MySQL availability | checkpoint:human-verify | (pre-approved, no commit) | PASSED |
| 2 | Replace requirements.txt with Python 3 stack and rebuild venv | auto | f927c49 | DONE |
| 3 | Remove Python 2 reload(sys) blocks from both __init__.py files | auto | 7519782 | DONE |
| 4 | Verify end-to-end smoke flow (interpreter + dependencies + imports) | auto (tdd) | 4fe1eff | DONE |

## Task Details

### Task 1: Environment Verification (pre-approved by orchestrator)
- `py -3 --version` → `Python 3.14.5`
- `py -3 -c "import sys; print(sys.executable)"` → `C:\Users\chx12\AppData\Local\Programs\Python\Python314\python.exe` (CPython.org installer path — mysqlclient wheel compatible)
- `netstat -an | grep 3306` → MySQL 80 service listening on `0.0.0.0:3306` and `0.0.0.0:33060` (MySQL 8.0 X Protocol)

### Task 2: requirements.txt replacement
- Replaced 4 lines (flask / flask_login / flask_SQLAlchemy / mysql-python) with pinned 4-line Python 3 stack
- Built fresh `.venv/` with `py -3 -m venv .venv` (no Python 2 contamination)
- `pip install -r requirements.txt` resolved all 4 packages plus 9 transitive deps (werkzeug, jinja2, sqlalchemy, etc.) using **wheel-based install** (`mysqlclient-2.2.8-cp314-cp314-win_amd64.whl`, 211 kB) — no source build
- Final versions: Flask 3.1.3, Flask-Login 0.6.3, Flask-SQLAlchemy 3.1.1, mysqlclient 2.2.8

### Task 3: Remove Python 2 idioms
- `app/__init__.py`: replaced `# coding=utf-8` with single explanatory comment (file did not have reload block — already clean)
- `app/api/__init__.py`: deleted 3-line `import sys; reload(sys); sys.setdefaultencoding('utf8')` block, replaced with single comment
- `app/api/model.py`: same removal — **deviation (Rule 3)**: this file also had the reload block; cleaning it was necessary for the import smoke test in Task 4 to pass
- Cleaned 5 stale `.pyc` files (from 2017 Python 2 byte-code) — committed the deletions

### Task 4: Smoke verification
All 7 acceptance criteria met:
- `python --version` → 3.14.5
- `import flask` → 3.1.3
- `import flask_sqlalchemy` → 3.1.1
- `import flask_login` → 0.6.3
- `import MySQLdb` → version_info `(2, 2, 8, 'final', 0)` (mysqlclient 2.2.8)
- `from app import app; app.url_map.iter_rules()` → **15 rules** (>=13 required)
- `from app.api.model import db` → constructs `<SQLAlchemy>` cleanly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed reload(sys) block from app/api/model.py**
- **Found during:** Task 3 verification
- **Issue:** `grep` found reload(sys)/setdefaultencoding in three files, not just the two `__init__.py` files named in the plan. The third file, `app/api/model.py:2-4`, was not mentioned in the plan's Task 3 acceptance_criteria, but the same `sys.setdefaultencoding('utf8')` line would `AttributeError: module 'sys' has no attribute 'setdefaultencoding'` on import. The plan's `files_modified:` frontmatter did include `app/api/model.py`, so the change is within the plan's listed scope; only the task description (Task 3) under-emphasized this file.
- **Fix:** Same removal as the two `__init__.py` files (delete 3 lines, leave single comment)
- **Files modified:** `app/api/model.py`
- **Commit:** 7519782

**2. [Rule 1 - Bug] Stale .pyc files from 2017 Python 2 build**
- **Found during:** Task 3 grep verification
- **Issue:** `Binary file app/__init__.pyc matches` lines were polluting grep output for the `setdefaultencoding` check, and the `.pyc` files referenced Python 2 byte-code that was incompatible with the Python 3.14 interpreter.
- **Fix:** Deleted the 5 stale `.pyc` files and committed the deletions alongside the source-code edits.
- **Files modified:** `app/__init__.pyc`, `app/api/__init__.pyc`, `app/api/model.pyc`, `app/route/__init__.pyc`, `app/route/user.pyc` (all deleted)
- **Commit:** 7519782

### Architectural Decisions (not deviations, but recorded)

- **`MySQLdb.__version__` does not exist in mysqlclient 2.2.x.** The version is exposed as `MySQLdb.version_info` or via `importlib.metadata.version('mysqlclient')`. Plan's smoke command would AttributeError; recorded the alternative here for the Phase 5 test suite to use.
- **Test/verify commit for Task 4 is empty-tree** (no source file changed in Task 4 — the task is purely verification). Using `--allow-empty` is the standard GSD convention for a "test" commit that records the verification gate result; this preserves the `test(...):` prefix the orchestrator looks for in TDD plans.

## Must-Have Verification

| Must-have | Status | Evidence |
|-----------|--------|----------|
| App starts via `python run.py` on Python 3.11+ | PARTIAL | `from app import app` succeeds; full `python run.py` boot deferred to Plan 01-02 (the duplicate Flask instance in `app/api/model.py` is still present — see plan § Tasks → Task 4 note) |
| `requirements.txt` installs cleanly from a fresh venv using `mysqlclient` | PASS | All 4 packages installed via wheel on `py -3 -m venv .venv` |
| No `reload(sys)` or `sys.setdefaultencoding` calls remain | PASS | `grep -rn "reload(sys)\|sys.setdefaultencoding" app/` exits 1 (no matches) |
| Python 3.11+ and all runtime imports succeed | PASS | Python 3.14.5; flask/flask_sqlalchemy/flask_login/MySQLdb all import; `from app import app` succeeds; 15 URL rules |

## Files Changed

```
M  requirements.txt                  (4 lines: flask/flask_login/flask_SQLAlchemy/mysql-python -> Flask/Flask-Login/Flask-SQLAlchemy/mysqlclient with version pins)
M  app/__init__.py                   (line 1: # coding=utf-8 -> Python 3 UTF-8 comment)
M  app/api/__init__.py               (lines 1-4: removed reload(sys) block)
M  app/api/model.py                  (lines 1-4: removed reload(sys) block; duplicate Flask instance + __tablenanme__ typos preserved for Plan 01-02)
D  app/__init__.pyc                  (stale 2017 Python 2 byte-code)
D  app/api/__init__.pyc              (stale 2017 Python 2 byte-code)
D  app/api/model.pyc                 (stale 2017 Python 2 byte-code)
D  app/route/__init__.pyc            (stale 2017 Python 2 byte-code)
D  app/route/user.pyc                (stale 2017 Python 2 byte-code)
```

## What's Next (Plan 01-02 — out of scope here)

- Fix `__tablenanme__` typo on all 3 models (`User`, `Lemma`, `Comment`)
- Consolidate duplicate `Flask(__name__)` + `SQLAlchemy(app)` in `app/api/model.py` to deferred `db = SQLAlchemy()` pattern
- Add missing `return` to `/api/modify` (current code falls off end → `NoneType` 500 in Flask 3.x)
- Add `.all()` + `None` guard to `/user/detail`
- Re-run full `/api/reset` smoke flow (Section E/F in RESEARCH § Validation Architecture) — depends on Plan 01-02 bug fixes

## Self-Check: PASSED

- `requirements.txt` exists, contains 4 pinned Python 3 packages, no `mysql-python`
- `app/__init__.py` line 1 is the UTF-8 comment, not `import sys` or `reload`
- `app/api/__init__.py` lines 1-4 are now `# Python 3 sources are UTF-8 by default; ...` + blank + `from flask import ...`
- `app/api/model.py` lines 1-4 are now UTF-8 comment + blank + 2 import lines (no `import sys`)
- `grep -rn "reload(sys)\|sys.setdefaultencoding" app/` → exit code 1 (no matches)
- `.venv/Scripts/python.exe -c "from app import app; print(len(list(app.url_map.iter_rules())))"` → `15`
- Commits f927c49, 7519782, 4fe1eff all visible in `git log --oneline`
