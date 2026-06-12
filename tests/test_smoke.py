# tests/test_smoke.py
# D-85: 9 步端到端流程(单个 test function,想法 G:贴近"single test"措辞)
# 1. POST /api/regist
# 2. POST /api/login
# 3. POST /api/add
# 4. GET  /user/search
# 5. GET  /user/detail (view_count + 1)
# 6. POST /api/modify
# 7. POST /api/comment
# 8. POST /api/comment/<id>/delete (作者)
# 9. POST /api/logout
def test_full_user_flow(client):
    from app import app
    from app.api.model import User, Lemma, Comment, db

    # 步骤 1:注册 testuser(>6 字符)
    r = client.post('/api/regist', data={'name': 'testuser', 'password': 'testpass123'})
    assert r.status_code == 302
    with client.session_transaction() as sess:
        assert '_user_id' in sess  # login_user 设了 session

    # 步骤 2:登出后再登录
    client.get('/api/logout')
    r = client.post('/api/login', data={'name': 'testuser', 'password': 'testpass123'})
    assert r.status_code == 302

    # 步骤 3:添加词条(含 [[wiki 链接]] 语法,步骤 5 验证渲染)
    r = client.post('/api/add', data={
        'title': '测试词条',
        'content': '测试内容 [[词条 A]]',
    })
    assert r.status_code == 302

    # 步骤 4:搜索
    r = client.get('/user/search?q=测试')
    assert r.status_code == 200
    # 搜索结果或主页闪存可能含'测试',宽松断言
    assert b'\xe6\xb5\x8b\xe8\xaf\x95' in r.data or b'\xe6\x9c\x89\xe6\x9c\x9f' in r.data

    # 步骤 5:看详情
    r = client.get('/user/detail?title=测试词条')
    assert r.status_code == 200
    # GAP-5: wiki 链接渲染验证
    assert b'<a href' in r.data, 'expected wikilink filter to render <a href ...>'
    # GAP-2: view_count 从 0 变 1
    with app.app_context():
        lemma = Lemma.query.filter_by(title='测试词条').first()
        assert lemma is not None
        assert lemma.view_count == 1, f'expected view_count==1, got {lemma.view_count}'

    # 步骤 6:编辑
    r = client.post('/api/modify', data={
        'newTitle': '测试词条',
        'newContent': '改后',
    })
    assert r.status_code == 302

    # 步骤 7:发评论(lemma 1 = seed 词条 '123')
    r = client.post('/api/comment', data={
        'lemma_id': '1',
        'content': '测试评论',
    })
    assert r.status_code == 302

    # 步骤 8:作者删自己评论(动态查 id,避免硬编码)
    with app.app_context():
        testuser_id = User.query.filter_by(name='testuser').first().id
        my_comment = Comment.query.filter_by(user_id=testuser_id).first()
        assert my_comment is not None, 'expected the just-created comment to exist'
        comment_id = my_comment.id

    r = client.post(f'/api/comment/{comment_id}/delete')
    assert r.status_code == 302

    # 验证:comment 已被删
    with app.app_context():
        assert Comment.query.get(comment_id) is None

    # 步骤 9:登出
    r = client.get('/api/logout')
    assert r.status_code == 302
    with client.session_transaction() as sess:
        assert '_user_id' not in sess
