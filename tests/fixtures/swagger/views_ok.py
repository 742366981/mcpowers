# -*- coding: utf-8 -*-
"""测试 fixture: 完全合规的 view"""
from flask import Blueprint
bp = Blueprint('test', __name__)


@bp.route('/users/list', methods=['GET'])
def list_users():
    """---
    tags:
      - 用户/列表
    summary: 用户列表
    description: 查询用户列表。
    parameters:
      - in: query
        name: page
        required: false
        type: integer
        description: 页码
        example: 1
      - in: query
        name: page_size
        required: false
        type: integer
        description: 每页数量
        example: 20
    responses:
      200:
        description: 成功
        schema:
          type: object
        examples:
          code: 0
          data: []
      401:
        description: 未登录
        schema:
          type: object
        examples:
          code: 401
          msg: 未登录
    ---"""
    return {'code': 0, 'data': []}
