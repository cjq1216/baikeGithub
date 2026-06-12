# tests/test_admin.py
# D-86: admin 删 + 非 admin 403
def test_admin_can_delete_any(client):
    from app import app
    from app.api.model import User, Lemma, Comment

    # admin 'a'/'a' 登录(init_db 已 seed, is_admin=True)
    r = client.post('/api/login', data={'name': 'a', 'password': 'a'})
    assert r.status_code == 302

    # 普通用户 bob 注册 + 创建 lemma + 评论
    client.get('/api/logout')
    client.post('/api/regist', data={'name': 'bobuser', 'password': 'bobpass123'})
    client.post('/api/add', data={'title': 'bob 词条', 'content': '<p>bob 内容</p>'})
    client.post('/api/add', data={'title': 'bob 词条二', 'content': '<p>bob 内容二</p>'})

    # bob 在自己 lemma(最后一个新建的)下发评论
    with app.app_context():
        bob = User.query.filter_by(name='bobuser').first()
        bob_lemma = Lemma.query.filter_by(title='bob 词条二').first()
        assert bob_lemma is not None
        # 动态取 lemma_id
        target_lemma_id = bob_lemma.id

    r = client.post('/api/comment', data={
        'lemma_id': str(target_lemma_id),
        'content': 'bob 评论',
    })
    assert r.status_code == 302

    # admin 重新登录
    client.get('/api/logout')
    r = client.post('/api/login', data={'name': 'a', 'password': 'a'})
    assert r.status_code == 302

    # admin 删 bob 那个 lemma(级联删其下评论)
    r = client.post(f'/api/admin/lemma/{target_lemma_id}/delete')
    assert r.status_code == 302

    # GAP-3: 验证 lemma 已被删 + 级联删 comments
    with app.app_context():
        assert Lemma.query.get(target_lemma_id) is None
        # 级联删验证:该 lemma 下没有任何 comment
        assert Comment.query.filter_by(lemma_id=target_lemma_id).count() == 0, \
            'expected cascade delete to remove all comments under the lemma'

    # admin 删另一条 comment 路径覆盖:
    # bob 在另一个 lemma 下建评论,admin 单独删 comment
    client.get('/api/logout')
    client.post('/api/login', data={'name': 'bobuser', 'password': 'bobpass123'})
    with app.app_context():
        bob = User.query.filter_by(name='bobuser').first()
        other_lemma = Lemma.query.filter_by(title='bob 词条').first()
        other_lemma_id = other_lemma.id

    r = client.post('/api/comment', data={
        'lemma_id': str(other_lemma_id),
        'content': 'bob 在另一个 lemma 的评论',
    })
    assert r.status_code == 302

    # GAP-4: 动态查 comment id(替换字面 <id> 硬编码)
    with app.app_context():
        bob = User.query.filter_by(name='bobuser').first()
        bob_comment = Comment.query.filter_by(
            user_id=bob.id, lemma_id=other_lemma_id
        ).first()
        assert bob_comment is not None
        bob_comment_id = bob_comment.id

    client.get('/api/logout')
    client.post('/api/login', data={'name': 'a', 'password': 'a'})

    # admin 删该 comment
    r = client.post(f'/api/admin/comment/{bob_comment_id}/delete')
    assert r.status_code == 302

    with app.app_context():
        assert Comment.query.get(bob_comment_id) is None


def test_non_admin_forbidden(client):
    # bob 登录(注册同时自动登录)
    r = client.post('/api/regist', data={'name': 'bobuser2', 'password': 'bobpass123'})
    assert r.status_code == 302

    # bob 尝试 admin 删 lemma → 403(@admin_required → abort(403))
    r = client.post('/api/admin/lemma/1/delete')
    assert r.status_code == 403

    # bob 尝试 admin 删 comment → 403
    r = client.post('/api/admin/comment/1/delete')
    assert r.status_code == 403
