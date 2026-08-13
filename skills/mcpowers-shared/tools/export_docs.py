#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mcpowers API 文档导出工具(v4.0.0+)

将 Flasgger 拉取的 Swagger 2.0 spec 导出为 `openapi.json` + `API文档.md`,
附带 5 字段契约硬门禁 + 可选 swagger-ui web 服务。

使用方式:

    # 模式 1:Flask 项目模式(默认,自动加载 apps/create_app)
    python tools/export_docs.py

    # 模式 2:spec.json 直传模式(适用 FastAPI/Spring Boot 等)
    python tools/export_docs.py --spec /path/to/openapi.json

    # 自定义输出目录
    python tools/export_docs.py -o /custom/output/dir

    # 跳过 5 字段契约硬门禁(仅一次性紧急用,未来要删)
    python tools/export_docs.py --no-strict-fields

    # 导出后启动 swagger-ui web 服务
    python tools/export_docs.py --serve --port=8080 --open-browser

退出码:
    0 = 成功
    1 = 文件 / 解析错误(项目结构不符、spec 加载失败)
    2 = 5 字段契约违反

设计原则(YAGNI):
- 仅支持 Swagger 2.0(Flask/Flasgger 生态);OpenAPI 3.0 不在本规范内
- 业务接口响应规范检查(HTTP 仅 200 / 业务错误走 code 字段)由写时 hook
  `swagger-lint-helper.py check_business_api_responses` 负责——不在
  本工具重复实现
- API文档模板的「## 通用规范」段从文件动态加载,避免硬编码副本

5 字段契约铁律(接口契约规范 §1):
    tags / summary / description / parameters(每个含 description + example)
    / responses(含 schema + examples)
"""

from __future__ import annotations

import argparse  # v2.27.0+ 顶层 import(铁律)
import functools
import http.server
import importlib.util
import json
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Timer
from typing import Any


# === 常量(v4.0.0+ 写死) ===

DEFAULT_REQUIRED_FIELDS = ('tags', 'summary', 'description', 'parameters', 'responses')

DEFAULT_HTTP_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH'}

DEFAULT_OUTPUT_FILENAME = 'openapi.json'

DEFAULT_MARKDOWN_FILENAME = 'API文档.md'

DEFAULT_SERVE_PORT = 8080


# === swagger-ui HTML 模板(直接 CDN,不下载 5MB 静态资源到仓内) ===

_SWAGGER_UI_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>API 文档</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: './openapi.json',
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis]
    });
  </script>
</body>
</html>
'''


# === 模块级辅助函数 ===

def get_error_codes():
    """返回通用错误码定义 markdown 段。

    Returns:
        markdown 字符串,含 `## 错误码` 段标题 + 错误码表 + 业务错误码说明

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> md = get_error_codes()
        >>> '## 错误码' in md
        True
        >>> '| 0 | 成功 |' in md
        True
    """
    return """## 错误码

| 错误码 | 说明 |
|:------:|:-----|
| 0 | 成功 |
| 400 | 参数错误 |
| 401 | 未登录或token过期 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

> **业务错误码**:业务错误码由各项目自行定义,格式为 10001+,请根据实际业务补充。

"""


def build_example_from_props(props):
    """根据 properties 构建请求示例 dict。

    按 Swagger 字段类型映射默认值:string -> `''` / integer/number -> `0` /
    boolean -> `True` / array -> `[]` / object -> `{}`;若属性有 `example`
    字段,优先使用 example(项目自定义真实示例优先于类型默认值)。

    Args:
        props: 属性字典,key 为字段名,value 为含 `type` / `example` 的 dict

    Returns:
        示例字典,key 与 props 一致,value 为按类型 / example 推断的占位值;
        空 props 返回空 dict

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> build_example_from_props({'name': {'type': 'string', 'example': 'admin'}})
        {'name': 'admin'}
        >>> build_example_from_props({'age': {'type': 'integer'}})
        {'age': 0}
    """
    if not props:
        return {}
    ex: dict[str, Any] = {}
    for pk, pv in props.items():
        if not isinstance(pv, dict):
            continue
        pv_type = pv.get('type', 'string')
        pv_example = pv.get('example')
        if pv_example is not None:
            ex[pk] = pv_example
        elif pv_type == 'string':
            ex[pk] = ''
        elif pv_type in ('integer', 'number'):
            ex[pk] = 0
        elif pv_type == 'boolean':
            ex[pk] = True
        elif pv_type == 'array':
            ex[pk] = []
        elif pv_type == 'object':
            ex[pk] = {}
        else:
            ex[pk] = ''
    return ex


def extract_response_data_fields(resp_props):
    """从响应 properties 中提取 `data` 字段的属性。

    Args:
        resp_props: 响应属性字典(来自 spec 的 responses.200.schema.properties)

    Returns:
        data 字段的 properties dict(若 data 是 object 且有 properties);
        若 data 字段缺失 / data 不是 object / data 无 properties,返回空 dict

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> extract_response_data_fields({
        ...     'code': {'type': 'integer'},
        ...     'data': {'type': 'object', 'properties': {'id': {'type': 'integer'}}}
        ... })
        {'id': {'type': 'integer'}}
        >>> extract_response_data_fields({'code': {'type': 'integer'}})
        {}
    """
    if 'data' in resp_props:
        data_prop = resp_props['data']
        if isinstance(data_prop, dict):
            if 'properties' in data_prop:
                return data_prop['properties']
            return {}
        return {}
    return {}


def is_pagination_response(resp_props):
    """判断响应是否为分页响应(基于 data 字段是否含 5 个标准分页字段)。

    Args:
        resp_props: 响应属性字典

    Returns:
        元组 `(is_page, data_props)`:
          - is_page (bool): True = 含 records/page_no/page_size/total_page/total_count
          - data_props (dict): data 字段的 properties;若 data 缺失则为空 dict

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> is_pagination_response({
        ...     'data': {'type': 'object', 'properties': {
        ...         'records': {}, 'page_no': {}, 'page_size': {},
        ...         'total_page': {}, 'total_count': {}
        ...     }}
        ... })
        (True, {'records': {}, 'page_no': {}, ...})
    """
    data_props = extract_response_data_fields(resp_props)
    pagination_fields = {'records', 'page_no', 'page_size', 'total_page', 'total_count'}
    return all(field in data_props for field in pagination_fields), data_props


# === 业务核心函数 ===

def find_auth_paths(spec):
    """自动识别登录和登出接口路径(基于 path 含 `login` / `logout` 关键字)。

    Args:
        spec: Swagger 2.0 spec dict(由 Flasgger / 外部 spec 文件提供)

    Returns:
        元组 `(login_path, logout_path)`,每个元素是 `'<METHOD> <path>'` 格式字符串
        (如 `'POST /auth/login'`);未识别到则对应元素为 None

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> spec = {'paths': {'/auth/login': {'post': {'summary': '登录'}},
        ...                    '/auth/logout': {'post': {'summary': '登出'}}}}
        >>> find_auth_paths(spec)
        ('POST /auth/login', 'POST /auth/logout')
    """
    paths = spec.get('paths', {})
    login_path = None
    logout_path = None
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, details in methods.items():
            if method.upper() not in DEFAULT_HTTP_METHODS:
                continue
            if 'login' in path.lower() and not login_path:
                login_path = f'{method.upper()} {path}'
            if 'logout' in path.lower() and not logout_path:
                logout_path = f'{method.upper()} {path}'
    return login_path, logout_path


def load_template_section(template_path, start_header, end_header):
    """从 markdown 模板文件中提取 `start_header` 到 `end_header` 之间的内容。

    用于动态加载 `API文档模板.md` 的「## 通用规范」段——避免硬编码副本,
    模板改版 markdown 自动同步。

    Args:
        template_path: 模板文件绝对路径(通常为 mcpowers-shared 内置的
            `docs/API文档/API文档模板.md`)
        start_header: 起始标题(如 `'## 通用规范'`,strip 后精确匹配)
        end_header: 结束标题(不含,即读到该标题**前一行**为止;
            通常为 `'## 接口文档模板'`)

    Returns:
        提取的 markdown 字符串(含起始标题行);模板不存在 / 找不到 start_header
        时返回空字符串(调用方 fallback 走硬编码副本——保守兜底)

    Raises:
        无(IO 异常由本地 try/except 兜底)

    Side Effects:
        - 读取模板文件(磁盘 IO)

    Example:
        >>> import tempfile, os
        >>> p = tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w', encoding='utf-8').name
        >>> _ = open(p, 'w', encoding='utf-8').write('## 通用规范\\n### 基础路径\\n## 接口文档模板')
        >>> load_template_section(p, '## 通用规范', '## 接口文档模板')
        '## 通用规范\\n### 基础路径'
    """
    try:
        text = Path(template_path).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return ''

    lines = text.splitlines()
    in_section = False
    collected: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not in_section:
            if stripped == start_header.strip():
                in_section = True
                collected.append(line)
            continue
        # 已进段,遇 end_header 终止(不含 end_header)
        if stripped == end_header.strip():
            break
        collected.append(line)

    return '\n'.join(collected)


def resolve_template_path(project_root=None):
    """解析 `API文档模板.md` 的实际路径(优先项目内,fallback 到 mcpowers 内置)。

    优先级:
      1. `<project_root>/docs/API文档/API文档模板.md`(项目自定义)
      2. mcpowers 内置 `skills/mcpowers-shared/docs/API文档/API文档模板.md`

    Args:
        project_root: 项目根目录(用于 #1 优先级查找);None 时仅走 #2

    Returns:
        模板文件绝对路径;两边都不存在时返回 #2(供调用方 fallback 字符串,
        可能仍不存在——由 load_template_section 兜底返回空)

    Raises:
        无(纯路径拼接 + isfile,不读文件)

    Side Effects:
        无

    Example:
        >>> resolve_template_path(None)  # mcpowers 内置
        '...skills/mcpowers-shared/docs/API文档/API文档模板.md'
    """
    candidates: list[str] = []
    if project_root:
        candidates.append(
            os.path.join(project_root, 'docs', 'API文档', 'API文档模板.md')
        )
    # mcpowers 内置(tools/export_docs.py -> skills/mcpowers-shared/docs/API文档/API文档模板.md)
    candidates.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'docs', 'API文档', 'API文档模板.md'
    ))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return candidates[-1]


# === 5 字段契约检查(只查 5 字段齐全 + 200 必备;业务接口响应规范由写时 hook 负责) ===

def check_5_field_contract(spec, required_fields=DEFAULT_REQUIRED_FIELDS):
    """遍历 spec 每个 path/method,校验 5 字段齐全 + 200 必备。

    检查内容(v4.0.0+):
      1. 每个接口必须含全部 5 顶层字段(tags / summary / description /
         parameters / responses)
      2. responses 块必须含 `200` 状态码

    注意:业务接口响应规范(HTTP 仅 200 / 业务错误走 code 字段 / 不应在
    docstring responses 块列 4xx/5xx)的检查**不在本函数**——由写时 hook
    `swagger-lint-helper.py check_business_api_responses()` 负责。

    Args:
        spec: Swagger 2.0 spec dict
        required_fields: 顶层必填字段元组;默认 5 字段契约

    Returns:
        violations 列表,每项为 `(path, method, reason)` 三元组:
          - path: 接口路径(如 `'/users/{id}'`)
          - method: HTTP 方法大写(如 `'POST'`)
          - reason: 违规原因(如 `'缺顶层字段 tags'` / `'responses 缺 200'`)
        空 list = 完全合规

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> violations = check_5_field_contract({
        ...     'paths': {'/x': {'post': {
        ...         'tags': ['A'], 'summary': 'x', 'description': 'x',
        ...         'parameters': [], 'responses': {'200': {}}
        ...     }}}
        ... })
        >>> violations
        []
        >>> violations = check_5_field_contract({
        ...     'paths': {'/y': {'get': {'responses': {}}}}
        ... })
        >>> any('缺 200' in v[2] for v in violations)
        True
    """
    violations: list[tuple[str, str, str]] = []
    for path, methods in spec.get('paths', {}).items():
        if not isinstance(methods, dict):
            continue
        for method, details in methods.items():
            if method.upper() not in DEFAULT_HTTP_METHODS:
                continue
            if not isinstance(details, dict):
                continue

            # 1. 5 字段齐全
            for field in required_fields:
                if field not in details:
                    violations.append((path, method.upper(), f'缺顶层字段 `{field}:`'))

            responses = details.get('responses', {})
            if not isinstance(responses, dict):
                violations.append((path, method.upper(), 'responses 必须为 dict'))
                continue

            # 2. 必须含 200
            if '200' not in responses:
                violations.append((path, method.upper(), 'responses 缺 200'))

    return violations


# === JSON -> Markdown 渲染 ===

def json_to_markdown(spec, output_file, login_path=None, template_section=None):
    """将 Swagger 2.0 JSON 渲染为中文 API 文档 markdown。

    输出结构:
      1. 文档头(标题 / 版本 / 更新日期 / 基础路径)
      2. 目录(按 tag 分组)
      3. 通用规范(模板段优先,fallback 走 `get_error_codes()` 硬编码)
      4. 各 tag 模块接口详情

    Args:
        spec: Swagger 2.0 spec dict
        output_file: 输出 markdown 文件路径(绝对路径或相对路径均可)
        login_path: 登录接口路径(如 `'POST /auth/login'`);
            传 None 时自动调 `find_auth_paths` 识别
        template_section: 模板「## 通用规范」段预加载内容;
            传 None 时走 fallback 硬编码副本

    Returns:
        None(直接写文件)

    Raises:
        OSError: 输出文件不可写
        TypeError: spec 不是 dict / 关键字段类型不符

    Side Effects:
        - 写入 output_file 文件(覆盖式)

    Example:
        >>> spec = {'info': {'title': 'X', 'version': '1.0'}, 'paths': {}}
        >>> import tempfile, os
        >>> p = tempfile.NamedTemporaryFile(suffix='.md', delete=False).name
        >>> json_to_markdown(spec, p, template_section='## 通用规范\\ntest')
        >>> os.path.exists(p) and 'X' in open(p, encoding='utf-8').read()
        True
    """
    lines: list[str] = []

    # 自动识别登录路径
    if not login_path:
        auto_login, _ = find_auth_paths(spec)
        login_path = auto_login or 'POST /auth/login'

    # 1. 文档头
    title = spec.get('info', {}).get('title', 'API 文档')
    lines.append(f'# {title}')
    lines.append('')
    lines.append(f'**版本**: {spec.get("info", {}).get("version", "1.0.0")}')
    lines.append(f'**更新日期**: {datetime.now().strftime("%Y-%m-%d")}')
    base_path = spec.get('basePath', '/{prefix}')
    lines.append(f'**基础路径**: `http://{{host}}:{{port}}{base_path}`')
    lines.append('')

    # 2. 目录
    paths = spec.get('paths', {})
    tag_apis: dict[str, list[dict]] = {}
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, details in methods.items():
            if method.upper() not in DEFAULT_HTTP_METHODS:
                continue
            if not isinstance(details, dict):
                continue
            tags = details.get('tags', [])
            for tag in tags:
                tag_apis.setdefault(tag, []).append({
                    'path': path, 'method': method.upper(), 'details': details
                })

    lines.append('## 目录')
    lines.append('')
    for tag in sorted(tag_apis.keys()):
        lines.append(f'- [{tag}](#{tag})')
    lines.append('')
    lines.append('---\n')

    # 3. 通用规范(模板段优先)
    if template_section:
        lines.append(template_section)
        lines.append('')
        lines.append('---\n')
    else:
        # Fallback:硬编码 `认证方式` + `错误码`(模板加载失败兜底)
        lines.append('## 通用规范')
        lines.append('')
        lines.append('### 认证方式')
        lines.append('')
        lines.append('系统采用 JWT Token 认证机制。大部分接口需要携带 Token 才能访问。')
        lines.append('')
        lines.append('#### 1. 获取 Token')
        lines.append('')
        lines.append(f'**接口地址**: `{login_path}`')
        lines.append('')
        lines.append('**请求参数**:')
        lines.append('')
        lines.append('| 参数名 | 类型 | 必填 | 说明 |')
        lines.append('|:------|:----:|:----:|------|')
        lines.append('| username | string | 是 | 用户名(手机号也可以) |')
        lines.append('| password | string | 是 | 密码(MD5格式) |')
        lines.append('')
        lines.append('**请求示例**:')
        lines.append('```json')
        lines.append('{"username": "admin", "password": "0192023a7bbd73250516f069df18b500"}')
        lines.append('```')
        lines.append('')
        lines.append('**响应示例**:')
        lines.append('```json')
        lines.append('''{
  "code": 0,
  "msg": "success",
  "data": {
    "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "user_id": 1,
    "username": "admin"
  }
}''')
        lines.append('```')
        lines.append('')
        lines.append('#### 2. 使用 Token')
        lines.append('')
        lines.append('在请求头中添加 Authorization 字段,格式为:')
        lines.append('')
        lines.append('```')
        lines.append('Authorization: Bearer {token}')
        lines.append('```')
        lines.append('')
        lines.append('---\n')
        lines.append(get_error_codes())
        lines.append('---\n')

    # 4. 各 tag 模块接口详情(保留 v2.4.0 4 类参数 + 分页 + 数组 records)
    for tag in sorted(tag_apis.keys()):
        lines.append(f'## {tag}')
        lines.append('')
        apis = sorted(tag_apis[tag], key=lambda x: (x['path'], x['method']))

        for idx, api in enumerate(apis, 1):
            path = api['path']
            method = api['method']
            details = api['details']

            summary = details.get('summary', f'{method} {path}')
            description = details.get('description', '')
            description = description.replace('<br/>', '').strip() if description else ''
            requires_auth = details.get('security', [])
            is_auth_api = 'login' in path or 'logout' in path or 'verify' in path
            need_auth = bool(requires_auth) or not is_auth_api

            lines.append(f'### {idx}. {summary}')
            lines.append('')
            lines.append(f'**接口地址**: `{method} {path}`')
            lines.append('')
            lines.append(f"**需认证**: {'是' if need_auth else '否'}")
            lines.append('')

            if description:
                lines.append(f'**说明**: {description}')
                lines.append('')

            # 请求参数
            parameters = details.get('parameters', [])
            if parameters:
                lines.append('**请求参数**:')
                lines.append('')
                body_params = [p for p in parameters if p.get('in') == 'body']
                query_path_params = [p for p in parameters if p.get('in') in ('query', 'path')]
                formdata_params = [p for p in parameters if p.get('in') == 'formData']
                header_params = [p for p in parameters if p.get('in') == 'header']

                if body_params:
                    schema = body_params[0].get('schema', {})
                    properties = schema.get('properties', {})
                    required = schema.get('required', [])
                    lines.append('| 参数名 | 类型 | 必填 | 说明 |')
                    lines.append('|:------|:----:|:----:|------|')
                    for prop_name, prop_info in properties.items():
                        if not isinstance(prop_info, dict):
                            continue
                        prop_type = prop_info.get('type', 'string')
                        is_required = '是' if prop_name in required else '否'
                        prop_desc = prop_info.get('description', '')
                        prop_example = prop_info.get('example', '')
                        if prop_example:
                            prop_desc = f'{prop_desc}(示例: {prop_example})'
                        lines.append(f'| {prop_name} | {prop_type} | {is_required} | {prop_desc} |')
                    lines.append('')

                if query_path_params:
                    lines.append('| 参数名 | 位置 | 类型 | 必填 | 说明 |')
                    lines.append('|:------|:----:|:----:|:----:|------|')
                    for param in query_path_params:
                        prop_desc = param.get('description', '')
                        prop_example = param.get('example', '')
                        if prop_example:
                            prop_desc = f'{prop_desc}(示例: {prop_example})'
                        lines.append(
                            f"| {param.get('name')} | {param.get('in')} | "
                            f"{param.get('type')} | {'是' if param.get('required') else '否'} | "
                            f'{prop_desc} |'
                        )
                    lines.append('')

                if header_params:
                    lines.append('**请求头(Headers)**:')
                    lines.append('')
                    lines.append('| 参数名 | 类型 | 必填 | 说明 |')
                    lines.append('|:------|:----:|:----:|------|')
                    for param in header_params:
                        prop_desc = param.get('description', '')
                        prop_example = param.get('example', '')
                        if prop_example:
                            prop_desc = f'{prop_desc}(示例: {prop_example})'
                        lines.append(
                            f"| {param.get('name')} | {param.get('type', 'string')} | "
                            f"{'是' if param.get('required') else '否'} | {prop_desc} |"
                        )
                    lines.append('')

                if formdata_params:
                    lines.append('**请求体(Form Data)**:')
                    lines.append('')
                    lines.append('| 参数名 | 类型 | 必填 | 说明 |')
                    lines.append('|:------|:----:|:----:|------|')
                    for param in formdata_params:
                        prop_desc = param.get('description', '')
                        prop_example = param.get('example', '')
                        if prop_example:
                            prop_desc = f'{prop_desc}(示例: {prop_example})'
                        lines.append(
                            f"| {param.get('name')} | {param.get('type', 'string')} | "
                            f"{'是' if param.get('required') else '否'} | {prop_desc} |"
                        )
                    lines.append('')

                # 请求示例
                if body_params:
                    schema = body_params[0].get('schema', {})
                    example = schema.get('example', {})
                    if example:
                        lines.append('**请求示例**:')
                        lines.append('```json')
                        lines.append(json.dumps(example, ensure_ascii=False, indent=2))
                        lines.append('```')
                        lines.append('')
                    else:
                        props = schema.get('properties', {})
                        if props:
                            lines.append('**请求示例**:')
                            lines.append('```json')
                            lines.append(json.dumps(build_example_from_props(props), ensure_ascii=False, indent=2))
                            lines.append('```')
                            lines.append('')

            # 响应(只渲染 200;4xx/5xx 业务接口不写,认证 / 流式接口例外)
            responses = details.get('responses', {})
            if '200' in responses:
                response_200 = responses['200']
                resp_schema = response_200.get('schema', {})
                resp_desc = response_200.get('description', '')

                lines.append(f'**响应说明**: {resp_desc}')
                lines.append('')

                resp_props = resp_schema.get('properties', {})
                if resp_props:
                    lines.append('**响应参数**:')
                    lines.append('')
                    lines.append('| 字段 | 类型 | 说明 |')
                    lines.append('|:-----|:-----|:-----|')
                    for prop_name, prop_info in resp_props.items():
                        if not isinstance(prop_info, dict):
                            continue
                        prop_type = prop_info.get('type', 'string')
                        prop_desc = prop_info.get('description', '')
                        lines.append(f'| {prop_name} | {prop_type} | {prop_desc} |')
                    lines.append('')

                    is_page, data_props = is_pagination_response(resp_props)
                    if 'data' in resp_props and data_props:
                        lines.append('**data 响应参数**:')
                        lines.append('')
                        lines.append('| 字段 | 类型 | 说明 |')
                        lines.append('|:-----|:-----|:-----|')
                        for prop_name, prop_info in data_props.items():
                            if not isinstance(prop_info, dict):
                                continue
                            prop_type = prop_info.get('type', 'string')
                            prop_desc = prop_info.get('description', '')
                            lines.append(f'| {prop_name} | {prop_type} | {prop_desc} |')
                        lines.append('')

                        if is_page and 'records' in data_props:
                            records_info = data_props.get('records', {})
                            if isinstance(records_info, dict) and records_info.get('type') == 'array':
                                items = records_info.get('items', {})
                                if isinstance(items, dict) and 'properties' in items:
                                    lines.append('**records 字段说明**:')
                                    lines.append('')
                                    lines.append('| 字段 | 类型 | 说明 |')
                                    lines.append('|:-----|:-----|:-----|')
                                    for rec_name, rec_info in items['properties'].items():
                                        if not isinstance(rec_info, dict):
                                            continue
                                        rec_type = rec_info.get('type', 'string')
                                        rec_desc = rec_info.get('description', '')
                                        lines.append(f'| {rec_name} | {rec_type} | {rec_desc} |')
                                    lines.append('')

                        if not is_page:
                            data_info = resp_props.get('data')
                            if isinstance(data_info, dict) and data_info.get('type') == 'array':
                                items = data_info.get('items', {})
                                if isinstance(items, dict) and 'properties' in items:
                                    lines.append('**data 响应参数**:')
                                    lines.append('')
                                    lines.append('| 字段 | 类型 | 说明 |')
                                    lines.append('|:-----|:-----|:-----|')
                                    for item_name, item_info in items['properties'].items():
                                        if not isinstance(item_info, dict):
                                            continue
                                        item_type = item_info.get('type', 'string')
                                        item_desc = item_info.get('description', '')
                                        lines.append(f'| {item_name} | {item_type} | {item_desc} |')
                                    lines.append('')

                # 响应示例
                lines.append('**响应示例**:')
                lines.append('```json')
                example_response = response_200.get('examples', {}).get('application/json')
                if not example_response:
                    example_response = {}
                    for prop_name, prop_info in resp_props.items():
                        if isinstance(prop_info, dict):
                            prop_type = prop_info.get('type', 'string')
                            prop_example = prop_info.get('example')
                            if prop_example is not None:
                                example_response[prop_name] = prop_example
                            elif prop_type == 'object' and 'properties' in prop_info:
                                example_response[prop_name] = build_example_from_props(
                                    prop_info.get('properties', {})
                                )
                            elif prop_type == 'array':
                                example_response[prop_name] = []
                            else:
                                example_response[prop_name] = ''
                if not example_response:
                    example_response = {'code': 0, 'msg': 'success', 'data': {}}
                lines.append(json.dumps(example_response, ensure_ascii=False, indent=2))
                lines.append('```')
                lines.append('')

                # 错误响应(认证 / 流式接口例外;业务接口不会到这里)
                error_codes = [c for c in responses.keys() if str(c) != '200']
                if error_codes:
                    error_codes.sort()
                    lines.append('**错误响应**:')
                    lines.append('')
                    for err_code in error_codes:
                        err_resp = responses[err_code]
                        if not isinstance(err_resp, dict):
                            continue
                        err_desc = err_resp.get('description', '')
                        lines.append(f'- `{err_code}`: {err_desc}')
                        err_example = err_resp.get('examples', {}).get('application/json')
                        if err_example:
                            lines.append('')
                            lines.append('  ```json')
                            indented = json.dumps(err_example, ensure_ascii=False, indent=2).replace('\n', '\n  ')
                            lines.append(indented)
                            lines.append('  ```')
                        else:
                            err_default = {
                                'code': int(err_code) if str(err_code).isdigit() else 500,
                                'msg': err_desc or 'error'
                            }
                            lines.append('')
                            lines.append('  ```json')
                            lines.append('  ' + json.dumps(err_default, ensure_ascii=False, indent=2))
                            lines.append('  ```')
                    lines.append('')

            lines.append('---\n')

    Path(output_file).write_text('\n'.join(lines), encoding='utf-8')


# === Flask 项目根查找 ===

def find_project_root(start_dir=None):
    """向上查找包含 `apps/__init__.py` 的项目根目录。

    策略:从 `start_dir` 出发,逐级向上查找,找到第一个含 `apps/` 子目录
    的目录即返回。

    Args:
        start_dir: 起始目录(默认当前工作目录)

    Returns:
        项目根目录字符串(绝对路径);一路到文件系统根仍未找到返回 None

    Raises:
        无(路径不存在由 `os.path.isdir` 静默跳过)

    Side Effects:
        无(仅读文件系统元数据)

    Example:
        >>> import tempfile, os
        >>> d = tempfile.mkdtemp()
        >>> os.makedirs(os.path.join(d, 'apps'), exist_ok=True)
        >>> find_project_root(d) == os.path.abspath(d)
        True
    """
    current = start_dir or os.getcwd()
    while True:
        if os.path.isdir(os.path.join(current, 'apps')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


# === 用户项目 apps 模块动态加载(importlib.util 顶层实现,避免函数体局部 import) ===

def load_user_app(project_root):
    """动态加载用户 Flask 项目 `apps/__init__.py` 的 `create_app` 函数。

    实现策略:用 `importlib.util.spec_from_file_location` 在项目根目录
    动态加载 `apps/__init__.py`,取其 `create_app` 属性。

    此函数取代原 v2.4.0 的 `from apps import create_app` 局部 import——
    局部 import 违反 v2.27.0+「Python import 位置规范」铁律;动态加载
    既保留功能,又合规。

    Args:
        project_root: 用户 Flask 项目根目录(含 `apps/` 子目录)

    Returns:
        `create_app` callable;加载失败(文件缺失 / 无 create_app 属性)返回 None

    Raises:
        无(异常由本地 try/except 捕获,转为 stderr 警告)

    Side Effects:
        - 读取 `<project_root>/apps/__init__.py`
        - 临时将 `<project_root>` 加入 `sys.path` 并在函数退出时还原

    Example:
        >>> import tempfile, os
        >>> d = tempfile.mkdtemp()
        >>> apps_dir = os.path.join(d, 'apps')
        >>> os.makedirs(apps_dir, exist_ok=True)
        >>> _ = open(os.path.join(apps_dir, '__init__.py'), 'w', encoding='utf-8').write(
        ...     'def create_app():\\n    class A: pass\\n    return A()'
        ... )
        >>> app = load_user_app(d)
        >>> callable(app)
        True
    """
    apps_init = os.path.join(project_root, 'apps', '__init__.py')
    if not os.path.isfile(apps_init):
        return None

    module_name = 'mcpowers_user_apps_dynamic'
    spec = importlib.util.spec_from_file_location(module_name, apps_init)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    saved_path = sys.path[:]
    sys.path.insert(0, project_root)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f'⚠️  加载 {apps_init} 失败:{e}', file=sys.stderr)
        return None
    finally:
        sys.path[:] = saved_path

    return getattr(module, 'create_app', None)


# === swagger-ui web 服务(--serve) ===

def serve_docs(spec_path, port=DEFAULT_SERVE_PORT, open_browser=False):
    """启动临时 HTTP server + swagger-ui 提供交互式文档。

    实现策略(YAGNI):
      - 直接 CDN 加载 swagger-ui(不下载 5MB 静态资源到仓内)
      - 用 `http.server` 而非 Flask(避免 Flask 依赖)
      - 自动打开浏览器用 `webbrowser.open`(stdlib)

    Args:
        spec_path: `openapi.json` 绝对路径(已生成的规范)
        port: HTTP 端口(默认 8080)
        open_browser: 是否自动打开浏览器

    Returns:
        None(阻塞运行直到 Ctrl+C)

    Raises:
        OSError: 端口被占用(`HTTPServer` 绑定失败)

    Side Effects:
        - 在 spec_path 同目录创建 `index.html`(swagger-ui 入口)
        - 启动 HTTP server,阻塞主线程
        - 可能打开浏览器新标签页(若 `open_browser=True`)

    Example:
        # 由 main() 在 --serve 时调用,不可手动直接调用
        serve_docs('/path/to/openapi.json', port=8080, open_browser=True)
    """
    docs_dir = os.path.dirname(spec_path)

    # 生成 swagger-ui index.html(若不存在)
    html_path = os.path.join(docs_dir, 'index.html')
    if not os.path.exists(html_path):
        Path(html_path).write_text(_SWAGGER_UI_HTML_TEMPLATE, encoding='utf-8')

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=docs_dir)

    if open_browser:
        def _open():
            webbrowser.open(f'http://localhost:{port}/')
        Timer(0.5, _open).start()

    print(f'🌐 在线文档: http://localhost:{port}/')
    print('   Ctrl+C 停止')
    try:
        with http.server.HTTPServer(('', port), handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 已停止')


# === 主入口 ===

def main():
    """CLI 入口:解析参数 -> 加载 spec -> 5 字段检查 -> 导出 -> 可选 serve。

    支持 4 类运行模式:
      1. Flask 项目模式(默认):自动 `find_project_root` + `load_user_app`
      2. spec.json 直传模式:`--spec /path/to/openapi.json`
      3. 严格模式(默认):5 字段契约 + 200 必备检查通过才导出
      4. swagger-ui 模式(`--serve`):导出后启动 web 服务

    Args:
        无(从 argv 解析)

    Returns:
        None(退出码由 sys.exit 设置):
          - 0:成功
          - 1:文件 / 解析错误(项目结构不符、spec 加载失败、Flask 导入失败)
          - 2:5 字段契约违反

    Raises:
        无(主流程异常由 `__main__` 块统一兜底)

    Side Effects:
        - 读 / 写文件(`openapi.json` + `API文档.md`)
        - 可能启动 HTTP server(`--serve`)
        - 可能打开浏览器(`--open-browser`)

    Example:
        # 默认模式:Flask 项目根 -> /apispec_1.json -> 导出 + 5 字段检查
        $ python tools/export_docs.py

        # 直传模式 + 跳过严格检查
        $ python tools/export_docs.py --spec /tmp/x.json --no-strict-fields

        # 导出后启动 web 服务
        $ python tools/export_docs.py --serve --port=9000 --open-browser
    """
    parser = argparse.ArgumentParser(
        description='mcpowers API 文档导出工具(v4.0.0+)'
    )
    parser.add_argument('--project', '-p', help='Flask 项目根目录(默认自动向上查找)')
    parser.add_argument('--spec', '-s', help='直接传入 openapi.json 路径(适用 FastAPI/Spring Boot 等)')
    parser.add_argument('--output', '-o', help='输出目录(默认 <project>/docs/API文档/)')
    parser.add_argument(
        '--no-strict-fields', action='store_true',
        help='跳过 5 字段契约检查(仅一次性紧急用,未来要删)'
    )
    parser.add_argument(
        '--serve', action='store_true',
        help='导出后启动 swagger-ui 临时 web 服务(http://localhost:<port>/)'
    )
    parser.add_argument('--port', type=int, default=DEFAULT_SERVE_PORT, help='--serve 端口(默认 8080)')
    parser.add_argument(
        '--open-browser', action='store_true',
        help='--serve 启动后自动打开浏览器'
    )
    args = parser.parse_args()

    # 模式选择
    spec: dict | None = None
    if args.spec:
        # 模式 1:spec.json 直传
        spec_file = os.path.abspath(args.spec)
        if not os.path.isfile(spec_file):
            print(f'❌ 错误:spec 文件不存在:{spec_file}', file=sys.stderr)
            sys.exit(1)
        print(f'📁 spec 文件: {spec_file}')
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec = json.load(f)
        except json.JSONDecodeError as e:
            print(f'❌ spec JSON 解析失败:{e}', file=sys.stderr)
            sys.exit(1)

        # v4.0.0:仅认 Swagger 2.0,OpenAPI 3.0 不在本规范内(砍 --openapi3 装样分支)
        if spec.get('swagger') != '2.0':
            print(
                f"❌ 错误:spec 必须为 Swagger 2.0 格式(spec.swagger = {spec.get('swagger')!r})",
                file=sys.stderr
            )
            print('   OpenAPI 3.0 用户(FastAPI/Node 等)不在 mcpowers 规范内', file=sys.stderr)
            sys.exit(1)

        project_root = os.path.dirname(spec_file)
        if args.output:
            output_dir = os.path.abspath(args.output)
        else:
            output_dir = os.path.join(project_root, 'docs', 'API文档')
    else:
        # 模式 2:Flask 项目模式
        if args.project:
            project_root = os.path.abspath(args.project)
            if not os.path.isdir(os.path.join(project_root, 'apps')):
                print(f'❌ 错误:{project_root} 不包含 apps/ 目录', file=sys.stderr)
                sys.exit(1)
        else:
            project_root = find_project_root()
            if not project_root:
                print('❌ 错误:未找到 Flask 项目(向上查找均无 apps/ 目录)', file=sys.stderr)
                print('   请使用 --project 指定项目根目录', file=sys.stderr)
                sys.exit(1)

        print(f'📁 项目根目录: {project_root}')

        # 顶层动态加载(importlib.util 替代 v2.4.0 局部 import)
        create_app = load_user_app(project_root)
        if create_app is None:
            print('❌ 错误:无法导入 apps.create_app', file=sys.stderr)
            print('   请确认项目结构符合 Flask后端规范.md 第 1 章', file=sys.stderr)
            sys.exit(1)

        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/apispec_1.json')
            if response.status_code != 200:
                print(f'❌ 导出失败:HTTP {response.status_code}', file=sys.stderr)
                print('   请检查 Flasgger 是否正确注册(详见 Flask后端规范.md 第 11 章)', file=sys.stderr)
                sys.exit(1)
            spec = response.get_json()

        output_dir = args.output or os.path.join(project_root, 'docs', 'API文档')

    # === 5 字段契约检查(v4.0.0 硬门禁) ===
    if not args.no_strict_fields:
        violations = check_5_field_contract(spec)
        if violations:
            print(
                f'❌ 5 字段契约违反({len(violations)} 处):',
                file=sys.stderr
            )
            for path, method, reason in violations:
                print(f'   {method} {path}  ->  {reason}', file=sys.stderr)
            print('', file=sys.stderr)
            print('请按 接口契约规范.md §1 补全,详见:', file=sys.stderr)
            print('  - docs/技术规范/接口契约规范.md §1(5 字段契约)', file=sys.stderr)
            print('  - docs/API文档/swagger_template.md(Flasgger docstring 详情锚)', file=sys.stderr)
            print('  - 业务接口响应规范(HTTP 仅 200 / code 字段表业务错误)由写时 hook 负责:', file=sys.stderr)
            print('    swagger-lint-helper.py check_business_api_responses()', file=sys.stderr)
            sys.exit(2)
        path_count = len(spec.get('paths', {}))
        method_count = sum(
            len([m for m in methods if m.upper() in DEFAULT_HTTP_METHODS])
            for methods in spec.get('paths', {}).values()
        )
        print(f'✅ 5 字段契约通过({path_count} 路径,{method_count} 接口)')

    # === 公共输出逻辑 ===
    os.makedirs(output_dir, exist_ok=True)

    json_file = os.path.join(output_dir, DEFAULT_OUTPUT_FILENAME)
    Path(json_file).write_text(
        json.dumps(spec, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f'✅ JSON 规范: {json_file}')

    # 加载模板「## 通用规范」段(项目优先,mcpowers 内置兜底)
    template_path = resolve_template_path(project_root)
    template_section = load_template_section(
        template_path, '## 通用规范', '## 接口文档模板'
    )

    login_path, _ = find_auth_paths(spec)
    md_file = os.path.join(output_dir, DEFAULT_MARKDOWN_FILENAME)
    json_to_markdown(spec, md_file, login_path, template_section)
    print(f'✅ Markdown:  {md_file}')

    # 统计
    path_count = len(spec.get('paths', {}))
    method_count = sum(
        len([m for m in methods if m.upper() in DEFAULT_HTTP_METHODS])
        for methods in spec.get('paths', {}).values()
    )
    print(f'\n📊 共导出 {path_count} 个路径,{method_count} 个接口')

    # === 可选:启动 swagger-ui web 服务 ===
    if args.serve:
        serve_docs(json_file, port=args.port, open_browser=args.open_browser)


if __name__ == '__main__':
    main()