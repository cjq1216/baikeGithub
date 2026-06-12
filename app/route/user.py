# coding=utf-8
from flask import render_template, Blueprint, redirect, url_for, request, session, current_app, flash
from flask_login import login_required, current_user
from app.api.model import User, Lemma, Comment, db
from sqlalchemy import update
import random

user = Blueprint(
        'apple',
        __name__
)

@user.route('/home')
def home():
    return render_template('home.html')

@user.route('/login')
def login():
    return render_template('signin.html')

@user.route('/regist')
def regist():
    return render_template('register.html')

@user.route('/add')
@login_required
def add():
    # D-49: 接受 ?title=... query 参数预填到 title input
    prefill_title = request.args.get('title', '').strip()
    return render_template('add.html', prefill_title=prefill_title)

@user.route('/search',methods=['POST'])
def search():
    searchtext = request.form.get('searchtext')
    results = Lemma.query.filter(Lemma.title.like("%"+searchtext+"%")).all()
    if results:
        return render_template('result.html', results=results)
    else :
        flash('所查词条不存在，工作人员正在努力完整词条库～～')
    return redirect(url_for('apple.home'))

@user.route('/detail', methods=['GET'])
def detail():
    title = request.args.get('title', '').strip()
    if not title:
        flash('未指定词条')
        return redirect(url_for('apple.home'))
    fullcon = Lemma.query.filter_by(title=title).first()
    if fullcon is None:
        flash('所查词条不存在')
        return redirect(url_for('apple.home'))
    # D-48: 原子 view_count +1,SQL 层 `view_count = view_count + 1`,无 lost-update
    db.session.execute(
        update(Lemma).where(Lemma.id == fullcon.id).values(view_count=Lemma.view_count + 1)
    )
    db.session.commit()
    # D-39 携带 + D-69: 查 comments(时间倒序)和 backlinks(wiki 链接引用本词条)
    comments = Comment.query.filter_by(lemma_id=fullcon.id).order_by(Comment.time.desc()).all()
    related_lemmas = Lemma.query.filter(Lemma.content.contains('[[' + fullcon.title + ']]')).limit(10).all()
    return render_template(
        'detail.html',
        fullcon=fullcon,
        comments=comments,
        related_lemmas=related_lemmas,
    )

@user.route('/modify')
@login_required
def modify():
    return render_template('modify.html')

# @user.route('/detail1')
# @login_required
# def detail():
#     return render_template('detail.html')
