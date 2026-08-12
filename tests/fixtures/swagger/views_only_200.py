# -*- coding: utf-8 -*-
"""测试 fixture: responses 只列 200"""
from flask import Blueprint
bp = Blueprint('test', __name__)


@bp.route('/users/detail', methods=['GET'])
def user_detail():
    """---
    tags:
      - 用户/详情
    summary: 用户详情
    description: 查询用户详情。
    parameters:
      - in: query
        name: id
        required: true
        type: integer
        description: 用户 ID
        example: 1
    responses:
      200:
        description: 成功
        schema:
          type: object
        examples:
          id: 1
          username: alice
    ---"""
    return {'code': 0, 'data': {'id': 1, 'username': 'alice'}}
