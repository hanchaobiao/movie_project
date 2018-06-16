#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : views.py
# @Author: 韩朝彪
# @Date  : 2018/5/4
# @Desc  :
from . import home
from flask import render_template, redirect, url_for, flash, session, request, Response
from .forms import RegistForm, LoginForm, UserdetailForm, PwdForm, CommentForm
from ..models import User, Userlog, Preview, Tag, Movie, Comment, Moviecol
from .. import db, app, rd
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import uuid
import os
from ..admin.views import change_filename
import json
import datetime


def user_login_req(f):
    """
    登录装饰器
    :param f: 
    :return: 
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("home.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# 首页列表
@home.route("/<int:page>/", methods=["GET"])
@home.route("/", methods=["GET"])
def index(page=1):
    """
    首页电影列表
    """
    tags = Tag.query.all()
    page_data = Movie.query
    # 标签
    tid = request.args.get("tid", 0)
    if int(tid) != 0:
        page_data = page_data.filter_by(tag_id=int(tid))
    # 星级
    star = request.args.get("star", 0)
    if int(star) != 0:
        page_data = page_data.filter_by(star=int(star))
    # 时间
    time = request.args.get("time", 0)
    if int(time) != 0:
        if int(time) == 1:
            page_data = page_data.order_by(Movie.addtime.desc())
        else:
            page_data = page_data.order_by(Movie.addtime.asc())
    # 播放量
    pm = request.args.get("pm", 0)
    if int(pm) != 0:
        if int(pm) == 1:
            page_data = page_data.order_by(Movie.playnum.desc())
        else:
            page_data = page_data.order_by(Movie.playnum.asc())
    # 评论量
    cm = request.args.get("cm", 0)
    if int(cm) != 0:
        if int(cm) == 1:
            page_data = page_data.order_by(Movie.commentnum.desc())
        else:
            page_data = page_data.order_by(Movie.commentnum.asc())
    page_data = page_data.paginate(page=page, per_page=8)
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=pm,
        cm=cm,
    )
    return render_template('home/index.html', page_data=page_data, p=p, tags=tags)


# 动画
@home.route("/animation/")
def animation():
    """
    首页轮播动画
    :return: 
    """
    data = Preview.query.all()
    return render_template("home/animation.html", data=data)


# 登录
@home.route('/login/', methods=['GET', 'POST'])
def login():
    """
    登录
    :return: 
    """
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        _user = User.query.filter_by(name=data["name"]).first()
        if not _user.check_pwd(data['pwd']):
            flash(u"密码错误！", "err")
            return redirect(url_for("home.login"))
        session["user"] = _user.name
        session["user_id"] = _user.id
        userlog = Userlog(
            user_id=_user.id,
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for("home.user"))
    return render_template("home/login.html", form=form)


# 退出
@home.route('/logout/')
@user_login_req
def logout():
    """
    退出
    :return: 
    """
    # 重定向到home模块下的登录。
    session.pop("user", None)
    session.pop("user_id", None)
    return redirect(url_for('home.login'))


# 会员注册
@home.route("/register/", methods=['GET', 'POST'])
def register():
    """
    会员注册
    :return: 
    """
    form = RegistForm()
    if form.validate_on_submit():
        data = form.data
        from werkzeug.security import generate_password_hash
        _user = User(name=data['name'], phone=data['phone'], email=data['email'],
                     pwd=generate_password_hash(data["pwd"]), uuid=uuid.uuid4().hex)
        db.session.add(_user)
        db.session.commit()
        flash(u"注册成功", 'ok')
    return render_template("home/register.html", form=form)


@home.route("/user/", methods=['GET', 'POST'])
@user_login_req
def user():
    """
    用户中心,修改个人信息
    """
    form = UserdetailForm()
    user = User.query.get(int(session["user_id"]))
    form.face.validators = []
    if request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data
        if form.face.data and form.face.data.filename != "":
            file_face = secure_filename(form.face.data.filename)
            if not os.path.exists(app.config["FC_DIR"]):
                os.makedirs(app.config["FC_DIR"])
                # os.chmod(app.config["FC_DIR"], "rw")
            user.face = change_filename(file_face)
            form.face.data.save(app.config["FC_DIR"] + user.face)
        if data['name'] != user.name and User.query.filter_by(name=data['name']).count() > 1:
            flash(u"昵称已经存在！", "err")
            return redirect(url_for("home.user"))
        if data['email'] != user.name and User.query.filter_by(email=data['email']).count() > 1:
            flash(u"邮箱已经存在！", "err")
            return redirect(url_for("home.user"))

        if data['phone'] != user.name and User.query.filter_by(phone=data['phone']).count() > 1:
            flash(u"手机号已经存在！", "err")
            return redirect(url_for("home.user"))

        user.name = data["name"]
        user.email = data["email"]
        user.phone = data["phone"]
        user.info = data["info"]
        db.session.add(user)
        db.session.commit()
        flash(u"修改成功！", "ok")
        return redirect(url_for("home.user"))
    return render_template("home/user.html", form=form, user=user)


@home.route("/pwd/", methods=['GET', 'POST'])
@user_login_req
def pwd():
    """
    修改密码
    """
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=session["user"]).first()
        if not user.check_pwd(data["old_pwd"]):
            flash(u"旧密码错误！", "err")
            return redirect(url_for('home.pwd'))
        user.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(user)
        db.session.commit()
        flash(u"修改密码成功，请重新登录！", "ok")
        return redirect(url_for('home.logout'))
    return render_template("home/pwd.html", form=form)


@home.route("/comments/<int:page>")
@user_login_req
def comments(page=1):
    """
    个人中心评论记录
    """

    page_data = Comment.query.join(Movie).join(User).filter(User.id == session['user_id']).\
        order_by(Comment.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("home/comments.html", page_data=page_data)


@home.route("/loginlog/<int:page>")
@user_login_req
def loginlog(page=1):
    """
    登录日志
    """
    page_data = Userlog.query.filter_by(user_id=int(session["user_id"])).order_by(Userlog.addtime.desc()).\
        paginate(page=page, per_page=10)
    return render_template("home/loginlog.html", page_data=page_data)


@home.route("/moviecol/<int:page>")
@user_login_req
def moviecol(page=1):
    """
    收藏电影
    """
    page_data = Moviecol.query.join(Movie).join(User).filter(User.id==session['user_id']).order_by(Moviecol.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("home/moviecol.html", page_data=page_data)


@home.route("/moviecol/add")
@user_login_req
def moviecol_add():
    """
    收藏电影
    """
    if 'user_id' not in session:
        flash(u'请先登录', 'err')
        return redirect(url_for('home.login'))
    uid = request.args.get("uid", "")
    mid = request.args.get("mid", "")
    moviecol_ = Moviecol.query.filter_by(user_id=int(uid), movie_id=int(mid)).count()
    # 已收藏
    if moviecol_ == 1:
        data = dict(ok=0)
    # 未收藏进行收藏
    if moviecol_ == 0:
        moviecol_ = Moviecol(user_id=int(uid), movie_id=int(mid))
        db.session.add(moviecol_)
        db.session.commit()
        data = dict(ok=1)
    return json.dumps(data)


@home.route("/search/<int:page>/")
def search(page=1):
    """
    搜索
    """
    key = request.args.get("key", "")

    movie_count = Movie.query.filter(Movie.title.ilike('%' + key + '%')).count()
    page_data = Movie.query.filter(Movie.title.ilike('%' + key + '%')).order_by(
        Movie.addtime.desc()).paginate(page=page, per_page=10)
    page_data.key = key
    return render_template("home/search.html", movie_count=movie_count, page_data=page_data, key=key)


@home.route("/play/<int:id>/<int:page>/", methods=["GET", "POST"])
@user_login_req
def play(id=None, page=1):
    """
    播放
    """
    movie = Movie.query.join(Tag).filter(Movie.id == int(id)).first_or_404()
    page_data = Comment.query.join(Movie).filter(Movie.id == int(id)).order_by(Comment.addtime.desc()).\
        paginate(page=page, per_page=10)
    movie.playnum += 1
    if 'user_id' not in session['user_id']:
        moviecol = 0
    else:
        moviecol = Moviecol.query.filter(Moviecol.user_id == session['user_id'], Moviecol.movie_id == id).count()
    form = CommentForm()
    # 必须登录
    if "user" in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        movie.commentnum += 1
        db.session.add(movie)
        db.session.commit()
        flash(u"添加评论成功！", "ok")
        return redirect(url_for('home.play', id=movie.id, page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template("home/play.html", movie=movie, form=form, page_data=page_data, moviecol=moviecol)


@home.route("/video/<int:id>/<int:page>/", methods=["GET", "POST"])
def video(id=None, page=None):
    """
    弹幕播放器
    :param id: 
    :param page: 
    :return: 
    """
    movie = Movie.query.join(Tag).filter(Movie.id == int(id)).first_or_404()
    page_data = Comment.query.join(Movie).filter(Movie.id == int(id)).order_by(Comment.addtime.desc()). \
        paginate(page=page, per_page=10)
    movie.playnum += 1

    form = CommentForm()
    # 必须登录
    if "user" in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        movie.commentnum += 1
        db.session.add(movie)
        db.session.commit()
        flash(u"添加评论成功！", "ok")
        return redirect(url_for('home.play', id=movie.id, page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template("home/video.html", movie=movie, form=form, page_data=page_data, moviecol=moviecol)


@home.route("/tm/", methods=["GET", "POST"])
@user_login_req
def tm():
    """
    弹幕消息处理
    :return: 
    """

    if request.method == 'GET':
        # 获取弹幕消息队列
        id = request.args.get('id')
        # 存放在redis队列中的键值
        key = "movie" + str(id)
        if rd.llen(key):
            msgs = rd.lrange(key, 0, 2999)
            res = {
                "code": 1,
                "danmaku": [json.loads(v) for v in msgs]
            }
        else:
            res = {
                "code": 1,
                "danmaku": []
            }
        resp = json.dumps(res)
    elif request.method == 'POST':
        # 添加弹幕
        data = json.loads(request.get_data())
        msg = {
            "__v": 0,
            "author": data["author"],
            "time": data["time"],
            "text": data["text"],
            "color": data["color"],
            "type": data['type'], "ip": request.remote_addr,
            "_id": datetime.datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex,
            "player": [data["player"]]
        }
        res = {
            "code": 1,
            "data": msg
        }
        resp = json.dumps(res)
        # 将添加的弹幕推入redis的队列中
        rd.lpush("movie" + str(data["player"]), json.dumps(msg))
    return Response(resp, mimetype='application/json')
