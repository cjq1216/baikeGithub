# tests/conftest.py
# CD-26: module-level Flask 实例(app/__init__.py:62)直接 import,不走 factory。
# CD-25: SQLite in-memory + WTF_CSRF_ENABLED=False + TESTING=True,无需 MySQL。
# CD-35: fixture 放 tests/conftest.py(社区惯例),不放 tests/__init__.py。
import os
import pytest
from sqlalchemy import create_engine


# 给 DB_* env vars 占位(app/__init__.py 在 import 时会检查这些变量;我们随后通过
# 替换 db.engines[None] 把 URI 切到 sqlite:///:memory:,这样 5 个 env vars 只是
# 为了让 app/__init__.py 的 import-time RuntimeError 守卫不触发)。
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
        # Flask-SQLAlchemy 3.x 在 init_app 时按 mysql URI 缓存了 engine,config
        # update 后 engine 不自动重建。直接 dispose 旧 engine 并替换为 sqlite
        # in-memory engine(避免 MySQL 驱动连接尝试 + 真实 MySQL 依赖)。
        old = flask_app.extensions['sqlalchemy'].engines[None]
        old.dispose()
        flask_app.extensions['sqlalchemy'].engines[None] = create_engine(
            'sqlite:///:memory:', future=True
        )
        db.create_all()
        from app.api.model import init_db
        init_db(if_empty=False)  # 灌 admin 'a'/'a' + 7 条种子 lemma
        yield flask_app
        db.session.remove()
        db.drop_all()
        # teardown: dispose sqlite engine,清 extensions 里的引用,避免后续
        # 测试因 WeakKeyDictionary 拿到旧 MySQL engine。
        if None in flask_app.extensions['sqlalchemy'].engines:
            flask_app.extensions['sqlalchemy'].engines[None].dispose()


@pytest.fixture
def client(app):
    return app.test_client()
