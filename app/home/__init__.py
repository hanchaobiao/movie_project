#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : __init__.py.py
# @Author: 韩朝彪
# @Date  : 2018/5/4
# @Desc  :
from flask import Blueprint

home = Blueprint("home", __name__)

from app.home import views
