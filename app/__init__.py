#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : __init__.py.py
# @Author: 韩朝彪
# @Date  : 2018/5/4
# @Desc  :
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
import os

app = Flask(__name__)
# 用于连接数据的数据库。
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@127.0.0.1:3306/movie"
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:tp158917@127.0.0.1:3306/movie"
# 如果设置成 True (默认情况)，Flask-SQLAlchemy 将会追踪对象的修改并且发送信号。

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
# 所有的form表单的提交submit之前都要添加csrf,只添加这个还不行，还需要添加一个secret key。
app.config['SECRET_KEY'] = 'mtianyan_movie'
app.debug = True
db = SQLAlchemy(app)
app.config["REDIS_URL"] = "redis://193.112.46.181:6379"
rd = FlaskRedis(app)

app.config["UP_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/")

app.config["FC_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/users/")


# 不要在生成db之前导入注册蓝图。

from app.home import home as home_blueprint
from admin import admin as admin_buleprint


# 注册蓝图  url_prefix 路径前缀
app.register_blueprint(admin_buleprint, url_prefix='/admin')
app.register_blueprint(home_blueprint)


@app.errorhandler(404)
def page_not_found(error):
    """
    404
    """
    return render_template("home/404.html"), 404