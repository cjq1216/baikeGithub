# coding=utf-8
from flask import render_template, Blueprint, redirect, url_for, request, session, current_app, flash
from flask_login import login_required, current_user
from app.api.model import User, Lemma, Comment, db
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
    return render_template('add.html')

@user.route('/search',methods=['POST'])
def search():
    searchtext = request.form.get('searchtext')
    results = Lemma.query.filter(Lemma.title.like("%"+searchtext+"%")).all()
    if results:
        return render_template('result.html', results=results)
    else :
        flash('所查词条不存在，工作人员正在努力完整词条库～～')
    return redirect(url_for('apple.home'))

@user.route('/detail', methods=['POST'])
def detail():
    entirelytitle = request.form.get('linklist')
    fullcontent = Lemma.query.filter_by(title = entirelytitle)
    return render_template('detail.html', fullcontent=fullcontent)

@user.route('/modify')
@login_required
def modify():
    return render_template('modify.html')

# @user.route('/detail1')
# @login_required
# def detail():
#     return render_template('detail.html')
