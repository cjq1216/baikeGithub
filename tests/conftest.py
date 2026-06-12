# tests/conftest.py
# CD-26: module-level Flask 实例(app/__init__.py:62)直接 import,不走 factory。
# CD-25: SQLite in-memory + WTF_CSRF_ENABLED=False + TESTING=True,无需 MySQL。
# CD-35: fixture 放 tests/conftest.py(社区惯例),不放 tests/__init__.py。
import os
import pytest

# 给 DB_* env vars 占位(app/__init__.py 在 import 时会检查这些变量;我们随后覆盖
# SQLALCHEMY_DATABASE_URI 改为 sqlite:///:memory:,这样 5 个 env vars 只是为了让
# app/__init__.py 的 import-time RuntimeError 守卫不触发)。
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_USER', 'test')
os.environ.setdefault('DB_PASSWORD', 'test')
os.environ.setdefault('DB_NAME', 'test')


@pytest.fixture
def app():
    from app import app as flask_app, db
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,  # CD-27
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
    )
    with flask_app.app_context():
        db.create_all()
        from app.api.model import init_db
        init_db(if_empty=False)  # 灌 admin 'a'/'a' + 7 条种子 lemma
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
