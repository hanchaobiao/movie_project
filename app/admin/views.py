#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : views.py
# @Author: 韩朝彪
# @Date  : 2018/5/4
# @Desc  :
from . import admin
from flask import render_template, redirect, url_for, flash, session, request, abort
from .forms import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm, AuthForm, RoleForm, AdminForm
from ..models import Admin, Tag, Movie, Preview, User, Comment, Moviecol, Adminlog, Oplog, Userlog, Auth, Role
from functools import wraps
from werkzeug.utils import secure_filename
from .. import db, app
from datetime import datetime
import os
import uuid


def admin_login_req(f):
    """
    登录装饰器, 访问控制装饰器一定要写在路由装饰器之后，否则会导致没有效果。
    :param f: 
    :return: 
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_auth(f):
    """
    权限装饰器
    :param f: 
    :return:
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # # _admin = Admin.query.join(Role).filter(Admin.id == session["admin_id"]).first()
        # _admin = Admin.query.filter(Admin.id == session["admin_id"]).first()  # 配置了一对多关系，
        # # 因该在登录后就获取权限信息
        # auths = _admin.role.auths
        # # 将原本存储的权限字符串转换为列表
        # auths = [int(v) for v in auths.split(",")]
        # urls = Auth.query.filter(Auth.id.in_(auths)).with_entities(Auth.url).all()
        # urls = [str(v[0]) for v in urls]
        rule = request.url_rule  # <class 'werkzeug.routing.Rule'> 需转为url
        if str(rule) not in session['urls']:
            abort(404)
        return f(*args, **kwargs)
    return decorated_function


def get_auth_urls():
    """
    获取登录管理员权限， 若角色信息修改，需要重新获取
    :return: 
    """
    # _admin = Admin.query.join(Role).filter(Admin.id == session["admin_id"]).first()
    _admin = Admin.query.filter(Admin.id == session["admin_id"]).first()  # 配置了一对多关系，
    # 因该在登录后就获取权限信息
    auths = _admin.role.auths
    # 将原本存储的权限字符串转换为列表
    auths = [int(v) for v in auths.split(",")]
    urls = Auth.query.filter(Auth.id.in_(auths)).with_entities(Auth.url).all()
    urls = [str(v[0]) for v in urls]
    session['urls'] = urls


@admin.context_processor
def tpl_extra():
    """
    上下应用处理器, 可在界面取online_time, 每取里面参数，都要运行一遍函数
    """
    # 之后直接传个admin。取admin face字段即可
    try:
        _admin = Admin.query.filter_by(name=session["admin"]).first()
    except:
        _admin = None
    data = dict(online_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                logo="mtianyan.jpg",
                admin=_admin,
                )
    return data


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


@admin.route("/login/", methods=['GET', 'POST'])
def login():
    """
    后台登录
    """
    form = LoginForm()
    if form.validate_on_submit():
        # 提交并通过验证
        data = form.data
        _admin = Admin.query.filter_by(name=data['account']).first()
        # 密码错误时，check_pwd返回false,则此时not check_pwd(data["pwd"])为真。
        if not _admin.check_pwd(data['pwd']):
            flash(u"密码错误!", "err")
            return redirect(url_for("admin.login"))
        # 如果是正确的，就要定义session的会话进行保存。
        session["admin"] = data["account"]
        session["admin_id"] = _admin.id
        get_auth_urls()  # 获取权限
        adminlog = Adminlog(
            admin_id=_admin.id,
            ip=request.remote_addr,
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("admin.index"))

    return render_template("admin/login.html", form=form)


@admin.route("/logout/")
@admin_login_req
def logout():
    """
    后台注销登录
    """
    session.pop('admin', None)
    session.pop('admin_id', None)
    session.pop('urls', None)
    return redirect(url_for("admin.login"))


@admin.route("/")
@admin_login_req
def index():
    """
    首页系统管理
    """
    return render_template("admin/index.html")


@admin.route("/pwd/", methods=['GET', 'POST'])
@admin_login_req
def pwd():
    """
    后台密码修改
    """
    form = PwdForm()
    # form.old_pwd.data = request.args.get('old_pwd')
    print form.data
    if form.validate_on_submit():
        data = form.data
        print data
        _admin = Admin.query.filter_by(name=session["admin"]).first()
        from werkzeug.security import generate_password_hash
        _admin.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(_admin)
        db.session.commit()
        flash(u"密码修改成功!", "ok")
        return redirect(url_for('admin.logout'))
    return render_template("admin/pwd.html", form=form)


@admin.route("/tag/add/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def tag_add():
    """
    标签添加与编辑
    """

    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data['name']).count()
        # 说明已经有这个标签了
        if tag == 1:
            flash(u"标签已存在", "err")
        else:
            tag = Tag(name=data['name'])
        oplog = Oplog(admin_id=session["admin_id"], ip=request.remote_addr, reason=u"添加标签%s" % data["name"])
        db.session.add(oplog)
        db.session.commit()
        db.session.add(tag)
        db.session.commit()
        flash(u"标签添加成功", "ok")
    return render_template("admin/tag_add.html", form=form)


@admin.route("/tag/list/<int:page>")
def tag_list(page=1):
    """
    标签列表
    """
    # per_page 每页显示数量
    page_data = Tag.query.order_by(Tag.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/tag_list.html", page_data=page_data)


@admin.route("/tag/edit/<int:tag_id>", methods=["GET", "POST"])
@admin_login_req
def tag_edit(tag_id=None):
    """ 
    标签编辑 
    """
    form = TagForm()
    form.submit.label.text = u"编辑"  # 提交按钮名称 此处对于submit字段的text修改，必须放在redirect之前。
    tag = Tag.query.get_or_404(tag_id)
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=data["name"]).count()
        # 说明已经有这个标签了,此时向添加一个与其他标签重名的标签。
        if tag.name != data["name"] and tag_count == 1:
            flash(u"标签已存在", "err")
            return redirect(url_for("admin.tag_edit", tag_id=tag.id))
        tag.name = data["name"]
        db.session.add(tag)
        db.session.commit()
        flash(u"标签修改成功", "ok")
        redirect(url_for("admin.tag_edit", tag_id=tag.id))
    return render_template("admin/tag_edit.html", form=form, tag=tag)


@admin.route("/tag/del/<int:tag_id>")
@admin_login_req
def tag_del(tag_id=None):

    # filter_by在查不到或多个的时候并不会报错，get会报错。
    tag = Tag.query.filter_by(id=tag_id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash(u"标签<<{0}>>删除成功".format(tag.name), "ok")
    return redirect(url_for("admin.tag_list", page=1))


@admin.route("/movie/add/", methods=["GET", "POST"])
@admin_login_req
def movie_add():
    """
    编辑电影页面
    """
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        file_url = secure_filename(form.url.data.filename)
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            # 创建一个多级目录
            os.makedirs(app.config["UP_DIR"])
            # os.chmod(app.config["UP_DIR"], "rw")
        url = change_filename(file_url)
        logo = change_filename(file_logo)
        # 保存
        form.url.data.save(app.config["UP_DIR"] + url)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        # url,logo为上传视频,图片之后获取到的地址
        movie = Movie(
            title=data["title"],
            url=url,
            info=data["info"],
            logo=logo,
            star=int(data["star"]),
            playnum=0,
            commentnum=0,
            tag_id=int(data["tag_id"]),
            area=data["area"],
            release_time=data["release_time"],
            length=data["length"]
        )
        db.session.add(movie)
        db.session.commit()
        flash(u"添加电影成功！", "ok")
        return redirect(url_for('admin.movie_add'))
    return render_template("admin/movie_add.html", form=form)


@admin.route("/movie/list/")
@admin_login_req
def movie_list(page=1):
    """
    电影列表页面
    """
    # 进行关联Tag的查询,单表查询使用filter_by 多表查询使用filter进行关联字段的声明
    page_data = Movie.query.join(Tag).filter(Tag.id == Movie.tag_id).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/movie_list.html", page_data=page_data)


@admin.route("/movie/del/<int:movie_id>/")
@admin_login_req
def movie_del(movie_id):
    movie = Movie.query.filter_by(id=movie_id).get_or_404()
    db.session.delete(movie)
    db.session.commit()
    flash(u"电影删除成功", "ok")
    return redirect(url_for('admin.movie_list', page=1))


@admin.route("/movie/edit/<int:movie_id>/", methods=["GET", "POST"])
@admin_login_req
def movie_edit(movie_id):
    form = MovieForm()
    # 因为是编辑，所以非空验证空
    form.url.validators = []
    form.logo.validators = []

    movie = Movie.query.get_or_404(movie_id)
    form.submit.label.text = u'编辑'
    if request.method == "GET":  # 特殊的，在后台赋值
        form.info.data = movie.info
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star
    else:
        if form.validate_on_submit():
            data = form.data
            movie_count = Movie.query.filter_by(title=data["title"]).count()
            # 存在一步名字叫这个的电影，有可能是它自己，也有可能是同名。如果是现在的movie不等于要提交的数据中title。那么说明有两个。
            if movie.title != data['title'] and movie_count > 0:
                flash(u"片名已经存在！", "err")
                return redirect(url_for('admin.edit', movie_id=movie.id))
            # 创建目录
            if not os.path.exists(app.config["UP_DIR"]):
                os.makedirs(app.config["UP_DIR"])
                # os.chmod(app.config["UP_DIR"], "rw")
            # 上传视频
            if form.url.data and form.url.data.filename != "" and form.url.data.filename is not None:
                if os.path.exists(app.config["UP_DIR"]+movie.url):
                    os.remove(app.config["UP_DIR"]+movie.url)
                file_url = secure_filename(form.url.data.filename)
                movie.url = change_filename(file_url)
                form.url.data.save(app.config["UP_DIR"] + movie.url)
            # 上传图片
            if form.logo.data and form.logo.data.filename != "" and form.logo.data.filename is not None:
                if os.path.exists(app.config["UP_DIR"] + movie.logo):
                    os.remove(app.config["UP_DIR"] + movie.logo)
                file_url = secure_filename(form.logo.data.filename)
                movie.logo = change_filename(file_url)
                form.logo.data.save(app.config['UP_DIR'] + movie.logo)
            movie.star = data["star"]
            movie.tag_id = data["tag_id"]
            movie.info = data["info"]
            movie.title = data["title"]
            movie.area = data["area"]
            movie.length = data["length"]
            movie.release_time = data["release_time"]
            db.session.add(movie)
            db.session.commit()
            flash(u"修改电影成功！", "ok")
            return redirect(url_for('admin.movie_edit', movie_id=movie.id))
    return render_template("admin/movie_edit.html", form=form, movie=movie)


@admin.route("/preview/add/", methods=['GET', 'POST'])
@admin_login_req
def preview_add():
    """
    上映预告添加
    """
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            # os.chmod(app.config["UP_DIR"], "rw")
        logo = change_filename(file_logo)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        preview = Preview(title=data["title"], logo=logo)
        db.session.add(preview)
        db.session.commit()
        flash(u"添加预告成功！", "ok")
        return redirect(url_for('admin.preview_add'))
    return render_template("admin/preview_add.html", form=form)


@admin.route("/preview/edit/<int:preview_id>", methods=['GET', 'POST'])
@admin_login_req
def preview_edit(preview_id):
    form = PreviewForm()
    form.logo.validators = []  # 不用验证
    form.submit.label.text = u'编辑'
    preview = Preview.query.get_or_404(preview_id)
    if form.validate_on_submit():
        data = form.data
        if form.logo.data and form.logo.data.filename != "":
            if not os.path.exists(app.config["UP_DIR"]):
                os.makedirs(app.config["UP_DIR"])
            file_logo = secure_filename(form.logo.data.filename)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + preview.logo)
        preview.title = data['title']
        db.session.add(preview)
        db.session.commit()
        flash(u"修改预告成功！", "ok")
        return redirect(url_for('admin.preview_edit', preview_id=preview.id))
    return render_template("admin/preview_edit.html", form=form, preview=preview)


@admin.route("/preview/del/<int:preview_id>")
@admin_login_req
def preview_del(preview_id):
    preview = Preview.query.get_or_404(preview_id)
    db.session.delete(preview)
    db.session.commit()
    flash(u"删除预告成功", "ok")
    return render_template("admin/preview_edit.html")


@admin.route("/preview/list/<int:page>")
@admin_login_req
def preview_list(page=1):
    """
    上映预告列表
    """
    page_data = Preview.query.order_by(Preview.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/preview_list.html", page_data=page_data)


@admin.route("/user/list/<int:page>")
@admin_login_req
def user_list(page=1):
    """
    会员列表
    """
    page_data = User.query.order_by(User.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/user_list.html", page_data=page_data)


@admin.route("/user/view/<int:user_id>")
@admin_login_req
def user_view(user_id):
    """
    查看会员
    """
    from_page = request.args.get('fp')
    # 兼容不加参数的无来源页面访问。
    if not from_page:
        from_page = 1
    user = User.query.get_or_404(int(user_id))
    return render_template("admin/user_view.html", user=user, from_page=from_page)


@admin.route("/user/del/<int:user_id>")
@admin_login_req
def user_del(user_id):
    # 因为删除当前页。假如是最后一页，这一页已经不见了。回不到。
    from_page = int(request.args.get('fp')) - 1
    # 此处考虑全删完了，没法前挪的情况，0被视为false
    if not from_page:
        from_page = 1
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(u"删除用户成功", "ok")
    return redirect(url_for('admin.user_list', page=from_page))


@admin.route("/comment/list/<int:page>")
def comment_list(page=1):
    """
    评论列表
    """
    print Comment.query.join(Movie).join(User)
    page_data = Comment.query.join(Movie).join(User).order_by(Comment.addtime.desc()).\
        paginate(page=page, per_page=10)
    return render_template("admin/comment_list.html", page_data=page_data)


@admin.route("/comment/del/<int:comment_id>/")
@admin_login_req
def comment_del(comment_id):
    # 因为删除当前页。假如是最后一页，这一页已经不见了。回不到。
    from_page = int(request.args.get('fp')) - 1
    # 此处考虑全删完了，没法前挪的情况，0被视为false
    if not from_page:
        from_page = 1
    comment = Comment.query.get_or_404(int(comment_id))
    db.session.delete(comment)
    db.session.commit()
    flash(u"删除评论成功！", "ok")
    return redirect(url_for('admin.comment_list', page=from_page))


@admin.route("/moviecol/list/<int:page>")
@admin_login_req
def moviecol_list(page=1):
    """
    电影收藏
    """
    page_data = Moviecol.query.join(Movie).join(User).order_by(Moviecol.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/moviecol_list.html", page_data=page_data)


@admin.route("/moviecol/del/<int:moviecol_id>")
@admin_login_req
def moviecol_del(moviecol_id):
    """
    电影收藏删除
    :param moviecol_id: 
    :return: 
    """
    from_page = request.args.get('fp') - 1
    if not from_page:
        from_page = 1
    moviecol = Moviecol.query.get_or_404(moviecol_id)
    db.session.delete(moviecol)
    db.session.commit()
    flash(u"删除收藏成功!", "ok")
    return redirect("admin.moviecol_list", page=from_page)


@admin.route("/oplog/list/<int:page>")
@admin_login_req
def oplog_list(page=1):
    """
    操作日志管理
    """
    page_data = Oplog.query.join(Admin).order_by(Oplog.addtime.desc()).paginate(
        page=page, per_page=10)
    return render_template("admin/oplog_list.html", page_data=page_data)


@admin.route("/adminloginlog/list/<int:page>/", methods=["GET"])
@admin_login_req
def adminloginlog_list(page=1):
    """
    管理员日志列表
    """
    page_data = Adminlog.query.join(Admin).order_by(Adminlog.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/adminloginlog_list.html", page_data=page_data)


@admin.route("/userloginlog/list/<int:page>/", methods=["GET"])
@admin_login_req
def userloginlog_list(page=1):
    """
    会员日志列表
     """
    page_data = Userlog.query.join(User).filter(User.id == Userlog.user_id, ).order_by(Userlog.addtime.desc()).\
        paginate(page=page, per_page=10)
    return render_template("admin/userloginlog_list.html", page_data=page_data)


@admin.route("/auth/add/", methods=['GET', 'POST'])
def auth_add():
    """
    添加权限
    """
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data["name"],
            url=data["url"]
        )
        db.session.add(auth)
        db.session.commit()
        flash(u"添加权限成功！", "ok")
    return render_template("admin/auth_add.html", form=form)


@admin.route("/auth/del/<int:auth_id>/", methods=["GET"])
@admin_login_req
def auth_del(auth_id=None):
    """
    权限删除
    """
    auth = Auth.query.filter_by(id=auth_id).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash(u"删除权限成功！", "ok")
    return redirect(url_for('admin.auth_list', page=1))


@admin.route("/auth/edit/<int:auth_id>/", methods=["GET", "POST"])
@admin_login_req
def auth_edit(auth_id=None):
    """
    编辑权限
    """
    form = AuthForm()
    auth = Auth.query.get_or_404(auth_id)
    if form.validate_on_submit():
        data = form.data
        auth.url = data["url"]
        auth.name = data["name"]
        db.session.add(auth)
        db.session.commit()
        flash(u"修改权限成功！", "ok")
        redirect(url_for('admin.auth_edit', auth_id=auth_id))
    return render_template("admin/auth_edit.html", form=form, auth=auth)


@admin.route("/auth/list/<int:page>")
@admin_login_req
def auth_list(page=1):
    """
    权限列表
    """
    page_data = Auth.query.order_by(Auth.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/auth_list.html", page_data=page_data)


@admin.route("/role/add/", methods=['GET', 'POST'])
@admin_login_req
def role_add():
    """
    添加角色
    """
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        role = Role(name=data["name"], auths=",".join(map(lambda v: str(v), data["auths"])))
        db.session.add(role)
        db.session.commit()
        flash(U"添加角色成功！", "ok")
    return render_template("admin/role_add.html", form=form)


@admin.route("/role/del/<int:role_id>", methods=['GET', 'POST'])
@admin_login_req
def role_del(role_id=None):
    """
    删除角色
    """
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash(u"删除角色成功!", "ok")
    return redirect('admin.role_list', page=1)


@admin.route("/role/edit/<int:role_id>", methods=['GET', 'POST'])
@admin_login_req
def role_edit(role_id=None):
    """
    编辑角色
    :param role_id: 
    :return: 
    """
    form = RoleForm()
    role = Role.query.get_or_404(role_id)
    if request.method == "GET":
        auths = role.auths
        if auths is None or auths.strip() == "":
            form.auths.data = []
        else:
            # # get时进行赋值。应对无法模板中赋初值
            form.auths.data = list(map(lambda v: int(v), auths.split(",")))
    if form.validate_on_submit():
        data = form.data
        role.name = data['name']
        role.auths=','.join(map(lambda v: str(v), data['auths']))
        db.session.add(role)
        db.session.commit()
        get_auth_urls
        flash(u"修改角色成功", "ok")
        return redirect(url_for('admin.role_list', page=1))
    return render_template("admin/role_edit.html", form=form, role=role)


@admin.route("/role/list/<int:page>")
def role_list(page=1):
    """
    角色列表
    """
    page_data = Role.query.order_by(Role.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/role_list.html", page_data=page_data)


@admin.route("/admin/add/", methods=['GET', 'POST'])
@admin_login_req
def admin_add():
    """
    添加管理员
    """
    form = AdminForm()
    if form.validate_on_submit():
        data = form.data
        from werkzeug.security import generate_password_hash
        _admin = Admin(name=data["name"], pwd=generate_password_hash(data["pwd"]), role_id=data["role_id"], is_super=1)
        db.session.add(_admin)
        db.session.commit()
        flash(u"添加管理员成功！", "ok")
    return render_template("admin/admin_add.html", form=form)


@admin.route("/admin/list/<int:page>")
@admin_login_req
def admin_list(page=1):
    """
    管理员列表
    """
    page_data = Admin.query.join(Role).order_by(Admin.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/admin_list.html", page_data=page_data)










