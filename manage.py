#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : manage.py
# @Author: 韩朝彪
# @Date  : 2018/5/4
# @Desc  :
from app import app


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)
