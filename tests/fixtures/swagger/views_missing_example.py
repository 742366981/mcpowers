# -*- coding: utf-8 -*-
"""测试 fixture: 缺 parameters[].example"""
from flask import Blueprint
bp = Blueprint('test', __name__)


@bp.route('/users/login', methods=['POST'])
def login():
    """---
    tags:
      - 用户/认证
    summary: 用户登录
    description: 使用用户名密码登录。
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              description: 用户名
              # 缺 example
            password:
              type: string
              description: 密码
              # 缺 example
    responses:
      200:
        description: 登录成功
      401:
        description: 用户名或密码错误
    ---"""
    return {'code': 0, 'data': {'token': 'xxx'}}
