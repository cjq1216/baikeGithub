# Python 3 sources are UTF-8 by default; no setdefaultencoding needed
from functools import wraps
from flask import Blueprint, abort, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.api.model import Lemma, Comment, db

admin = Blueprint('admin', __name__)


def admin_required(f):
    """Compose Flask-Login's login_required with an is_admin check.

    The inner wrapper is decorated with @login_required so unauthenticated
    users are redirected to login_view BEFORE the is_admin check runs. Once
    the user is authenticated, a non-admin gets abort(403) which routes
    through the Plan 2.2 unified error handler.
    """
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@admin.route('/lemma/<int:lemma_id>/delete', methods=['POST'])
@admin_required
def delete_lemma(lemma_id):
    lemma = Lemma.query.get(lemma_id)
    if lemma is None:
        flash('删除失败！词条不存在')
        return redirect(url_for('apple.home'))
    db.session.delete(lemma)
    db.session.commit()
    flash('删除成功！')
    return redirect(url_for('apple.home'))


@admin.route('/comment/<int:comment_id>/delete', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        flash('删除失败！评论不存在')
        return redirect(request.referrer or url_for('apple.home'))
    db.session.delete(comment)
    db.session.commit()
    flash('删除成功！')
    return redirect(request.referrer or url_for('apple.home'))
