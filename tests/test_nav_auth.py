# tests/test_nav_auth.py
# 回归守护:登录态必须能在导航栏反映出来。
# 历史 bug:base.html #nav-right 的 hx-trigger 只有 "nav-refresh from:body" 无 load,
# 而登录/登出走整页 302(原生 form 非 hx-post),HX-Trigger 响应头对浏览器导航无效,
# 导致 nav-refresh 事件永不触发 → 导航栏恒为硬编码的"登录/注册",登录态不可见。
# 修复:hx-trigger 加 load,首屏加载后 HTMX 自动拉 /api/nav-fragment 渲染真实态。
# 本测试锁住两端契约:(1) 片段端点按登录态返回正确内容;(2) base 模板保留 load 触发器。


def test_nav_fragment_anonymous_shows_login_register(client):
    r = client.get('/api/nav-fragment')
    assert r.status_code == 200
    assert b'baike-cta' in r.data        # 未登录态"注册"按钮的 class(_nav_right.html)
    assert '注销'.encode() not in r.data  # 未登录不应出现注销


def test_nav_fragment_authenticated_shows_user_and_logout(client):
    client.post('/api/login', data={'name': 'a', 'password': 'a'})
    r = client.get('/api/nav-fragment')
    assert r.status_code == 200
    assert '注销'.encode() in r.data       # 登录态出现注销
    assert '写词条'.encode() in r.data      # 登录态出现写词条入口
    assert b'baike-cta' not in r.data       # 登录态不再有注册按钮


def test_base_nav_right_has_load_trigger(client):
    # 防止 base.html 回退到无 load 的旧触发器(否则首屏永不拉取真实登录态)
    r = client.get('/user/home')
    assert r.status_code == 200
    assert b'hx-trigger="load' in r.data
