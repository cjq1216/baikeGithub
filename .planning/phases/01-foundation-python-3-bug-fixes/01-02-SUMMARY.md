---
phase: 01-foundation-python-3-bug-fixes
plan: 02
subsystem: runtime-foundation
tags: [bug-fixes, model-consolidation, handler-fixes, smoke-verified]
dependency_graph:
  requires: [INFRA-01, INFRA-02]
  provides: [INFRA-03, INFRA-04]
  affects: [phase-02-auth, phase-03-comments, phase-04-frontend, phase-05-docker]
tech-stack:
  added: []
  patterns:
    - "Deferred SQLAlchemy() init — single binding site in app/__init__.py via db.init_app(app)"
    - "Handler pattern: lookup-or-flash-and-redirect for idempotent resource mutation"
key-files:
  created: []
  modified:
    - app/api/model.py
    - app/api/__init__.py
    - app/route/user.py
decisions:
  - "Consolidated to single Flask app construction site (app/__init__.py) — removes dead duplicate instance in app/api/model.py"
  - "/api/modify uses query-then-mutate pattern, not db.session.merge() — merge would INSERT a transient (no PK) and silently duplicate rows"
  - "/user/detail guards empty result with flash+redirect (matches /user/search pattern) — prevents 200-with-blank-page UX trap"
  - "Read newTitle/newContent separately from request.form — detail.html:53 hidden input posts two distinct fields, original code read the same field twice"
metrics:
  duration: "~6 minutes (4 tasks, 3 source edits + 1 verification gate)"
  completed_date: "2026-06-11"
---

# Phase 1 Plan 2: Runtime Bug Fixes Summary

Eliminated four latent runtime bugs in the application code (one model-level code smell + three handler-level correctness bugs) and verified the full end-to-end flow against the remote MySQL server. All fixes were surgical — no new features, no refactoring of unrelated code, no architectural changes.

## Task Completion

| # | Task | Type | Commit | Status |
|---|------|------|--------|--------|
| 1 | Fix `__tablenanme__` typo + remove duplicate Flask instance in `app/api/model.py` | auto | 00c123c | DONE |
| 2 | Fix `/api/modify` — lookup by title, commit, redirect | auto (tdd) | c24a33a | DONE |
| 3 | Fix `/user/detail` — materialize query, guard empty result | auto (tdd) | df1d708 | DONE |
| 4 | End-to-end smoke flow against remote MySQL | auto (tdd) | c0da552 | DONE |

## Task Details

### Task 1: model.py consolidation
- Deleted the duplicate `Flask(__name__)` + `app.config[...]` + `db = SQLAlchemy(app)` block (old lines 4-7).
- Removed unused `from flask import Flask` import.
- Top-level is now `db = SQLAlchemy()` with NO arguments — bound later by `app/__init__.py:13` via `db.init_app(app)`.
- Renamed `__tablenanme__` -> `__tablename__` on all three models (`User`, `Lemma`, `Comment`).
- Table name strings unchanged (`'user'`, `'lemma'`, `'comment'`) — match `baike.sql` schema.

### Task 2: /api/modify fix
Replaced buggy body (old lines 65-73). Original code had three stacked bugs:
1. Read `request.form.get('newContent')` into `newTitle` variable (wrong field — form posts two distinct fields per `detail.html:53`).
2. Used `db.session.merge()` on a transient instance with no primary key — Flask-SQLAlchemy treats this as INSERT, not UPDATE.
3. Missing `return` — Flask 3.x raises `TypeError: 'NoneType' object does not support the '__html__' protocol` on the implicit `None` return.

New handler:
```python
newTitle = request.form.get('newTitle')
newContent = request.form.get('newContent')
lemma = Lemma.query.filter_by(title=newTitle).first()
if lemma is None:
    flash('修改失败！词条不存在')
    return redirect(url_for('apple.home'))
lemma.content = newContent
db.session.commit()
flash('修改成功！')
return redirect(url_for('apple.home'))
```

### Task 3: /user/detail fix
Replaced buggy body (old lines 39-43). Original code passed a `BaseQuery` to the template; `{% for fullcon in fullcontent %}` in `detail.html:51` would iterate, but Flask 3.x serializes the query object differently — and a missing lemma would render an empty page (200 OK) with no user feedback, leaving the user stuck.

New handler:
```python
entirelytitle = request.form.get('linklist')
fullcontent = Lemma.query.filter_by(title=entirelytitle).all()
if not fullcontent:
    flash('所查词条不存在')
    return redirect(url_for('apple.home'))
return render_template('detail.html', fullcontent=fullcontent)
```

The empty-result guard mirrors the pattern already in `/user/search` (`app/route/user.py:32-37`).

### Task 4: End-to-end smoke against remote MySQL

Smoke flow against `162.14.107.126:3307 / baike / cjq`:

| Step | Endpoint | Method | Status | Body Assertion |
|------|----------|--------|--------|----------------|
| 1 | `/api/reset` | GET | 200 | `b'{"error":false}\n'` |
| 2 | `/api/regist` (`name=tester&password=pw`) | POST | 302 | (auto-login via `login_user`) |
| 3 | `/api/add` (`title=T1&content=<p>hello</p>`) | POST | 302 | |
| 4 | `/user/search` (`searchtext=T1`) | POST | 200 | `b'T1'` in body |
| 5 | `/user/detail` (`linklist=T1`) | POST | 200 | `b'hello'` in body |
| 6 | `/api/modify` (`newTitle=T1&newContent=<p>updated</p>`) | POST | 302 | (NO 500, NO NoneType) |
| 7 | `/user/detail` (`linklist=T1` re-fetch) | POST | 200 | `b'updated'` in body |
| 8 | `/user/detail` (`linklist=__nonexistent__`) | POST | 302 | (empty guard fires) |

Post-condition checks:
- `Lemma.query.filter_by(title='T1').count()` == 1 (modify is UPDATE, no duplicate row)
- Lemma with `title='T1'` has `content == '<p>updated</p>'`

All assertions passed.

## Deviations from Plan

None — plan executed exactly as written. All four task actions matched the plan's `<action>` blocks.

## Must-Have Verification

| Must-have | Status | Evidence |
|-----------|--------|----------|
| `/api/modify` returns 302 to `/user/home` after successful edit | PASS | Smoke step 6 |
| `/user/detail` renders a real lemma list; missing lemma redirects with flash | PASS | Smoke steps 5, 7, 8 |
| `app/api/model.py` has no duplicate `Flask(__name__)` | PASS | `grep -rn "Flask(__name__)" app/` shows only `app/__init__.py:10` |
| All three models declare correct `__tablename__` (not `__tablenanme__`) | PASS | `User/Lemma/Comment.__tablename__` prints `user lemma comment` |
| `db = SQLAlchemy()` with no app arg | PASS | `type(db).__name__` is `SQLAlchemy` (unbound) |
| End-to-end smoke flow passes 7+ POST assertions | PASS | 7 POST assertions, all green |
| No duplicate row after modify | PASS | `Lemma.query.filter_by(title='T1').count() == 1` |
| Modified content persisted | PASS | Lemma content == `<p>updated</p>` |

## Files Changed

```
M  app/api/model.py                  (4 inserts, 8 deletes: removed duplicate Flask+SQLAlchemy(app) block + 3 __tablenanme__ typos)
M  app/api/__init__.py               (7 inserts, 3 deletes: rewrote /api/modify body)
M  app/route/user.py                 (4 inserts, 1 delete:   rewrote /user/detail body)
```

No new files. No new symbols. No new dependencies. No template changes.

## Threat Surface

- T-01-04 (`__tablenanme__` typo silently falls back to class-name-derived table name) — mitigated by Task 1.
- T-01-05 (duplicate `Flask(__name__)` confusion about app ownership) — mitigated by Task 1.
- T-01-06 (DoS via blank page on missing lemma) — mitigated by Task 3.

No new threat surface introduced. The modify handler's `newContent` is still treated as opaque HTML (XSS protection is Phase 4 / FRONT-01..06).

## What's Next (Phase 2 — out of scope here)

- Password hashing (`User.password` is plaintext, length 40 — see CLAUDE.md "密码明文" warning)
- `secret_key` hardcoding + CSRF protection (Phase 2)
- `Comment` model `__init__` / `__str__` bugs (Phase 3)
- XSS / wangEditor content sanitization (Phase 4)
- Hardcoded MySQL credentials -> environment variables (Phase 5 / Docker)

## Self-Check: PASSED

- `app/api/model.py` line 1 is `# Python 3 sources are UTF-8 by default; ...`; no `from flask import Flask`
- `db = SQLAlchemy()` is the only top-level SQLAlchemy binding (line 6)
- Three `__tablename__ = '...'` declarations (User at line 11, Lemma at line 25, Comment at line 39)
- `app/api/__init__.py` /api/modify returns `redirect(url_for('apple.home'))` in both branches
- `app/route/user.py` /user/detail calls `.all()` and has empty-result guard
- `grep -rn "__tablenanme__" app/` -> no matches
- `grep -rn "Flask(__name__)" app/` -> only `app/__init__.py:10` (the legitimate one)
- 4 commits visible in `git log --oneline`: 00c123c, c24a33a, df1d708, c0da552
- End-to-end smoke passed against remote MySQL
