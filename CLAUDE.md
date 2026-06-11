# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概要

641 宿舍软件架构大作业 —— 互动百科。基于 Flask + MySQL + flask_login 的小型 Wiki,支持用户注册/登录、词条(Lemma)搜索/查看/添加/修改、评论(Comment)模型(已建模但未实装评论接口)。

代码为 2017 年课堂作业,使用 **Python 2 时代风格**(`reload(sys)`、`mysql-python`、硬编码 `sys.setdefaultencoding('utf8')`),在 Python 3 上需要小幅迁移。

## 本地启动

```bash
# 1. 准备 MySQL
#    在本地 MySQL 中创建空库 baike(用户名 root / 密码 123456,见 app/__init__.py:11)

# 2. 准备虚拟环境
python -m venv venvbaike
source venvbaike/bin/activate          # Windows: venvbaike\Scripts\activate
pip install -r requirements.txt

# 3. 初始化数据(种子数据 + 默认账号 a/a)
python run.py                          # 实际监听 Flask 默认 5000 端口
# 浏览器打开 http://127.0.0.1:5000/api/reset   触发建表 + 灌种子

# 4. 访问应用
# http://127.0.0.1:5000
```

> README 写的 `127.0.0.1:2002` 来自 `config.ini` 的 uwsgi 部署配置;`run.py` 用 `app.run()` 默认是 5000 端口。两种访问方式不要混淆。

## 没有测试 / 没有 lint

项目无 `tests/` 目录、无 pytest、无 CI、无 lint 配置。`requirements.txt` 仅有运行时依赖,无开发依赖。

## 架构与关键文件

```
run.py                  # 入口:启动 app
app/__init__.py         # 创建 Flask app、配置 SQLAlchemy URI、注册蓝图、login_manager
app/api/model.py        # SQLAlchemy 模型 (User / Lemma / Comment),并在此模块再 new 了一个 Flask app 用于 db 绑定
app/api/__init__.py     # api 蓝图: 表单提交类接口(注册/登录/登出/添加/修改/reset)
app/route/user.py       # apple 蓝图(注意 Blueprint name='apple',不是 'user'):页面渲染 + 搜索 + 详情
app/templates/          # Jinja2 模板: home / signin / register / add / modify / result / detail
app/static/             # 静态资源,含 wangEditor 富文本编辑器
config.ini              # uwsgi 部署配置(非本地开发用)
baike.sql               # MySQL 表结构 dump(手动初始化时参考,应用自身用 db.create_all)
```

### 数据模型 (app/api/model.py)

- `User(id, name unique, password)` — 密码明文存储,无 hash
- `Lemma(id, title, content, comments)` — 一对多关联到 Comment
- `Comment(id, user_name, lemma_id, content, time)` — 外键 `lemma_id`,但 `user_name` 未建外键

`Comment` 模型已定义但应用层无任何创建评论的路由/接口(被注释在 `app/api/__init__.py:76-85`)。

### 请求流

页面型路由(GET 渲染模板)集中在 `app/route/user.py` 的 `apple` 蓝图(`/user/*` 前缀):
`/user/home`、`/user/login`、`/user/regist`、`/user/add`、`/user/search`、`/user/detail`、`/user/modify`。

表单提交(POST 处理业务逻辑)集中在 `app/api/__init__.py` 的 `api` 蓝图(`/api/*` 前缀):
`/api/regist`、`/api/login`、`/api/logout`、`/api/add`、`/api/modify`、`/api/reset`。

`url_for` 在跨蓝图跳转时使用 `apple.<endpoint>` 写法(对应 `user` 蓝图)或 `api.<endpoint>`,不要写 `user.<endpoint>` —— Blueprint 的 `name='apple'` 在 `app/route/user.py:7-10` 已明确。

## 已知坑(改前必看)

- **MySQL 凭据硬编码** 在 `app/__init__.py:11` 和 `app/api/model.py:10`,改了 model.py 里的不会生效,以 `app/__init__.py` 为准。生产前必须抽到环境变量。
- **secret_key 硬编码** (`app/__init__.py:10`),无 CSRF 保护。
- **typo**: `__tablenanme__` 应为 `__tablename__`(`app/api/model.py` 三处),但表名恰好与默认生成一致,目前不影响运行。
- **`/api/modify`** 没有 return,没有 redirect(`app/api/__init__.py:65-73`),提交后只 flash 一次,后续代码会 NoneType 错误。
- **`/user/detail`** 返回的是 `Lemma.query.filter_by(...)` 的 BaseQuery(`app/route/user.py:42`),未 `.first()`/`.all()`,模板里取 `fullcontent` 会渲染错。
- **密码明文** 存储,无 hash(`app/api/__init__.py:34` 直接比对)。
- **Comment 路由已注释**(`app/api/__init__.py:76-85`),模板里也没有评论表单,`Comment` 表当前无人写入。
- **`app/api/model.py:9-11`** 额外 `Flask(__name__)` + `SQLAlchemy(app)` 是早期兼容写法,`app/__init__.py:12` 才是真正生效的 `db.init_app(app)`,不要清理。
- **Python 2 代码**: `reload(sys)`、`mysql-python`、`sys.setdefaultencoding` 都需要在迁移到 Python 3 时移除(改为 `mysqlclient`、去掉 reload 块)。

## 调试小贴士

- 改完模板/路由后**不需要重启** Flask 即可刷新页面(`app.run(debug=True)`)。
- 数据库要重置:访问 `/api/reset`,会 drop_all + create_all + 重新灌种子。
- 默认账号:用户名 `a`,密码 `a`(`app/api/__init__.py:91`)。
