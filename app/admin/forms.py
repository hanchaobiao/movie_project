#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : forms.py
# @Author: 韩朝彪
# @Date  : 2018/5/4
# @Desc  :
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, FileField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, ValidationError, Length, EqualTo
from flask_wtf.file import FileField, FileAllowed
from ..models import Admin, Tag, Auth, Role


"""
validators 数据校验，render_kw 因为forms会为我们直接生成html代码，
通过该参数加上各种class等。 
form 表单 在界面不使用 {{form.name}}也可以验证，只要name='字段名' 与 form相同即可
"""


class LoginForm(FlaskForm):
    """
    管理员登录表单
    """
    account = StringField(
        label="账号",
        validators=[
            DataRequired(U"账号不能为空")
        ],
        description="账号",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入账号！",
            # 注释此处显示forms报错errors信息
            "required": "required"
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired(U"密码不能为空")
        ],
        description="密码",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入密码！",
            # 注释此处显示forms报错errors信息
            "required": "required"
        }
    )
    submit = SubmitField(
        u'登录',
        render_kw={
            "class": "btn btn-primary btn-block btn-flat",
        }
    )

    def validate_account(self, field):
        """
        验证账号是否存在,自定义验证, 注意此处自定义验证方法的命名规范validate_+字段名
        :param field: 
        :return: 
        """
        account = field.data
        admin = Admin.query.filter_by(name=account).count()
        if admin == 0:
            raise ValidationError(u"账号不存在! ")


class TagForm(FlaskForm):
    name = StringField(
        label=u"名称",
        validators=[
            DataRequired(u"标签名不能为空")
        ],
        description="标签",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": u"请输入标签名称！"
        }
    )

    submit = SubmitField(
        u'添加',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class MovieForm(FlaskForm):
    title = StringField(
        label=u"片名",
        validators=[
            DataRequired(u"片名不能为空！")
        ],
        description=u"片名",
        render_kw={
            "class": "form-control",
            "id": "input_title",
            "placeholder": u"请输入片名！"
        }
    )

    url = FileField(
        label=U"文件",
        validators=[
            DataRequired(U"请上传文件！")
        ],
        description=U"文件",
    )

    info = TextAreaField(
        label=U"简介",
        validators=[
            DataRequired(U"简介不能为空！")
        ],
        description=U"简介",
        render_kw={
            "class": "form-control",
            "rows": 10
        }
    )

    logo = FileField(
        label=U"封面",
        validators=[
            DataRequired(U"请上传封面！"),
            FileAllowed(['jpg', 'png'], 'Image Only')
        ],
        description=U"封面",
    )

    star = SelectField(
        label=U"星级",
        validators=[
            DataRequired(U"请选择星级！")
        ],
        # star的数据类型
        coerce=int,
        choices=[(1, U"1星"), (2, U"2星"), (3, U"3星"), (4, U"4星"), (5, U"5星")],
        description=U"星级",
        render_kw={
            "class": "form-control",
        }
    )

    # 标签要在数据库中查询已存在的标签
    tag_id = SelectField(
        label=U"标签",
        validators=[
            DataRequired(U"请选择标签！")
        ],
        coerce=int,
        # 通过列表生成器生成列表
        choices=[(v.id, v.name) for v in Tag.query.all()],
        description=U"标签",
        render_kw={
            "class": "form-control",
        }
    )

    area = StringField(
        label=u"地区",
        validators=[
            DataRequired(u"请输入地区！")
        ],
        description=u"地区",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入地区！"
        }
    )

    length = StringField(
        label=u"片长",
        validators=[
            DataRequired(u"片长不能为空！")
        ],
        description=u"片长",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入片长！"
        }
    )

    release_time = StringField(
        label=u"上映时间",
        validators=[
            DataRequired(u"上映时间不能为空！")
        ],
        description=u"上映时间",
        render_kw={
            "class": "form-control",
            "placeholder": u"请选择上映时间！",
            "id": "input_release_time"
        }
    )

    submit = SubmitField(
        u'添加',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class PreviewForm(FlaskForm):
    title = StringField(
        label=u"预告标题",
        validators=[
            DataRequired(u"预告标题不能为空！")
        ],
        description=u"预告标题",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入预告标题！"
        }
    )

    logo = FileField(
        label=u"预告封面",
        validators=[
            DataRequired(u"预告封面不能为空！")
        ],
        description=u"预告封面",
    )
    submit = SubmitField(
        u'添加',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class PwdForm(FlaskForm):
    old_pwd = PasswordField(
        label=u"旧密码",
        validators=[
            DataRequired(u"旧密码不能为空！"),
            Length(min=5, max=16, message=u"密码长度在6~16字符之间")
        ],
        description=u"旧密码",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入旧密码！",
        }
    )

    new_pwd = PasswordField(
        label=u"新密码",
        validators=[
            DataRequired(u"新密码不能为空！"),
            Length(min=5, max=16, message=u"密码长度在6~16字符之间")
        ],
        description=u"新密码",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入新密码！",
        }
    )

    submit = SubmitField(
        u'编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )

    # 自定义验证旧密码是否正确
    def validate_old_pwd(self, field):
        from flask import session
        pwd = field.data
        name = session["admin"]
        admin = Admin.query.filter_by(name=name).first()
        if not admin.check_pwd(pwd):
            raise ValidationError(u"旧密码错误")


class AuthForm(FlaskForm):
    name = StringField(
        label=u"权限名称",
        validators=[
            DataRequired(u"权限名称不能为空！")
        ],
        description=u"权限名称",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入权限名称！"
        }
    )

    url = StringField(
        label=u"权限地址",
        validators=[
            DataRequired(u"权限地址不能为空！")
        ],
        description=u"权限地址",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入权限地址！"
        }
    )

    submit = SubmitField(
        u'编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class RoleForm(FlaskForm):
    name = StringField(
        label=u"角色名称",
        validators=[
            DataRequired(u"角色名称不能为空！")
        ],
        description=u"角色名称",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入角色名称！"
        }
    )

    # 多选框
    auths = SelectMultipleField(
        label=u"权限列表",
        validators=[
            DataRequired(u"权限列表不能为空！")
        ],
        # 动态数据填充选择栏：列表生成器
        coerce=int,
        choices=[(v.id, v.name) for v in Auth.query.all()],
        description=u"权限列表",
        render_kw={
            "class": "form-control",
        }
    )

    submit = SubmitField(
        u'编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class AdminForm(FlaskForm):
    name = StringField(
        label=u"管理员名称",
        validators=[
            DataRequired(u"管理员名称不能为空！")
        ],
        description=u"管理员名称",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入管理员名称！",
        }
    )

    pwd = PasswordField(
        label=u"管理员密码",
        validators=[
            DataRequired(u"管理员密码不能为空！")
        ],
        description=u"管理员密码",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入管理员密码！",
        }
    )

    repwd = PasswordField(
        label=u'管理员重复密码',
        validators=[
            DataRequired(u"管理员重复密码不能为空！"),
            EqualTo('pwd', message=u"两次密码不一致！")
        ],
        description=u"管理员重复密码",
        render_kw={
            "class": "form-control",
            "placeholder": u"请输入管理员重复密码！",
        }
    )

    role_id = SelectField(
        label=u"所属角色",
        coerce=int,
        choices=[(v.id, v.name) for v in Role.query.all()],
        render_kw={
            "class": "form-control",
        }
    )

    submit = SubmitField(
        u'编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )

    def validate_name(self, field):
        """
        验证用户名是否已存在
        :param field: 
        :return: 
        """
        if Admin.query.filter_by(name=field.data).count() > 0:
            raise ValidationError(U'用户名已存在')