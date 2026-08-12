# -*- coding: utf-8 -*-
"""测试 fixture: 缺 docstring 的 view 函数"""
from flask import Blueprint
bp = Blueprint('test', __name__)


@bp.route('/users/list', methods=['GET'])
def list_users():
    return {'code': 0, 'data': []}
