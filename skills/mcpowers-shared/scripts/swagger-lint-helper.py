#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mcpowers swagger 单文件 lint helper(v2.31.0+)

被 swagger-contract-check.sh 调用的 Python 端精确 lint。

复用 lint_api_docstrings.py 的 module-level 函数(parse_python_docstring + lint_docstring),
在其基础上扩展"必填字段名存在性"检查(原 lint 不查顶层 tags/summary/description 等字段名)。

使用方式:
    python swagger-lint-helper.py --file-path=<rel_path> --fields-file=<path>

--fields-file 由 swagger-required-fields.sh 生成,3 行:
    line1: 必填字段名(空格分隔)
    line2: parameters 子字段必填项(空格分隔)
    line3: responses 子字段必填项(空格分隔)

退出码:
    0 = 无违规(或非 .py 文件放行,留给未来扩展)
    2 = 有 ERROR 级别违规(触发 Claude Code confirm UI)

设计原则(YAGNI):
- 只支持 Python(Flasgger docstring 解析);JS/TS router 暂直接放行
- 不引入 pyyaml(字段清单由 shell helper 预解析)
- 不重写 lint_docstring,只在其基础上叠加"必填字段名"层
"""

import argparse
import ast
import re
import sys
from pathlib import Path

# 复用现有 lint 模块(parse_python_docstring 是稳定函数;
# lint_docstring 不调,其正则有 catastrophic backtracking 风险)
_LINT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_LINT_DIR))
try:
    from lint_api_docstrings import parse_python_docstring
except ImportError as e:
    print(f"⚠️  [swagger-lint-helper] 无法 import lint_api_docstrings:{e}", file=sys.stderr)
    sys.exit(0)  # 自身 bug 不阻断开发


# v4.5.0+ 装饰器解析器(独立于 lint_api_docstrings.py,避免污染基础模块)
# 用 ast 解析 @bp.route('/path', methods=['GET']) 的 methods 列表 + path 模板
# 返回 {route_path: str, methods: list[str], line: int}
# parse_python_docstring 已经返回 route_path,这里只补 methods
def _parse_route_decorators(file_path: Path) -> dict[int, dict[str, object]]:
    """解析 Python 文件中所有 @bp.route/@bp.get/@app.post 等装饰器。

    Returns:
        {行号(装饰器所在 1-based): {'path': str, 'methods': list[str]}}
        行号作为 key,与 parse_python_docstring 的 entry['line'] 对齐

    Raises:
        无(AST 解析失败 → 返回空 dict,不阻断)

    Side Effects:
        无

    Example:
        >>> # @bp.route('/detail', methods=['GET']) 在第 10 行 → {10: {'path': '/detail', 'methods': ['GET']}}
    """
    decorators: dict[int, dict[str, object]] = {}
    if not file_path.exists() or file_path.suffix != '.py':
        return decorators
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        # Python 解析失败 → 放行(不让自身 bug 阻塞开发)
        return decorators
    except Exception:
        return decorators

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            # 形式 1:@bp.route('path', methods=['GET'])  → Call(func=Attribute(Name, 'route'), ...)
            # 形式 2:@bp.get('path') / @bp.post('path')   → Call(func=Attribute(Name, 'get'/'post'), ...)
            # 形式 3:@app.route(...) / @user_bp.route(...) — 同上,Name 部分是任意标识符
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Name):
                continue
            method_name_upper = func.attr.upper()
            path = ''
            methods: list[str] = []
            if method_name_upper == 'ROUTE':
                # 第一个位置参数 = path
                if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                    path = dec.args[0].value
                # methods= 关键字参数
                for kw in dec.keywords:
                    if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                methods.append(elt.value.upper())
                # 默认 methods(Flask 默认 ['GET'] 仅在某些版本,稳妥起见若未声明视为 ['GET'])
                if not methods:
                    methods = ['GET']
            elif method_name_upper in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
                # @bp.get('path') / @bp.post('path') 形式
                if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                    path = dec.args[0].value
                methods = [method_name_upper]
            else:
                continue

            decorators[node.lineno] = {'path': path, 'methods': methods}

    return decorators


def parse_fields_file(fields_file: Path) -> tuple[list[str], list[str], list[str]]:
    """解析字段清单文件(3 行文本)

    Returns:
        (required_fields, param_subfields, resp_subfields)
    """
    if not fields_file.exists():
        return (['tags', 'summary', 'description', 'parameters', 'responses'],
                ['description', 'example'],
                ['schema', 'examples'])

    try:
        lines = fields_file.read_text(encoding='utf-8').splitlines()
        required = lines[0].split() if len(lines) > 0 else []
        param_sub = lines[1].split() if len(lines) > 1 else []
        resp_sub = lines[2].split() if len(lines) > 2 else []
        return (required, param_sub, resp_sub)
    except Exception as e:
        print(f"⚠️  [swagger-lint-helper] 字段清单解析失败:{e},fallback 默认", file=sys.stderr)
        return (['tags', 'summary', 'description', 'parameters', 'responses'],
                ['description', 'example'],
                ['schema', 'examples'])


def check_required_field_names(docstring: str, required_fields: list[str]) -> list[tuple[str, str]]:
    """检查 docstring 是否包含所有必填顶层字段名

    Returns:
        list of (level, msg) — level: 'ERROR' / 'WARNING'
    """
    violations = []

    # 无 docstring 或缺 YAML 块(---) → 整体违规(接口函数必须按 5 字段契约)
    if not docstring or not docstring.strip():
        violations.append(('ERROR', '视图函数无 docstring(接口契约规范 §1 强制)'))
        return violations

    if '---' not in docstring:
        violations.append(('ERROR', 'docstring 缺 Flasgger YAML 块(`---\\n...\\n---`,接口契约规范 §1)'))
        return violations

    for field in required_fields:
        # 字段名出现规则:`field:`(顶层键)
        # 排除子键:`description:` 不应误判为 `description` 字段名(顶层和子键都叫 description)
        # 简化:只要 docstring 含 `<field>:` 就视为存在(子键也算覆盖;lint_docstring 会进一步细化)
        if f'{field}:' not in docstring and f'{field} :' not in docstring:
            violations.append(('ERROR', f'缺顶层字段 `{field}:`'))
    return violations




def check_parameter_subfields(docstring: str, param_subfields: list[str]) -> list[tuple[str, str]]:
    """检查每个 parameter 块是否含必填子字段(如 description + example)

    字符串扫描:以 `      - in:`(6 空格 `- in:`)为参数项起点,直到下一个
    `      - in:` 或 `    responses:`(4 空格顶层)止。逐行扫每个子字段是否存在。

    Returns:
        list of (level, msg) — level: 'ERROR' / 'WARNING'
    """
    violations = []

    if not param_subfields:
        return violations

    lines = docstring.splitlines()
    # 收集所有参数块:(start_line, end_line, name)
    blocks: list[tuple[int, int, str]] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        # 参数项起点:6 空格 `- in:` 或 `6空格 in:`
        if lines[i].startswith('      - in:') or lines[i].startswith('      in:'):
            start = i
            # 提 name(在 in: 同一行 or 下一行 name: ...)
            in_loc = stripped.split('in:', 1)[1].strip()
            name = ''
            if 'name:' in lines[i]:
                name = lines[i].split('name:', 1)[1].strip()
            else:
                # 下一行找 name:
                for j in range(i + 1, min(i + 5, len(lines))):
                    if 'name:' in lines[j]:
                        name = lines[j].split('name:', 1)[1].strip()
                        break
            # 找结束:下一个参数项起点 or 顶层字段或 `---`
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if lines[j].startswith('      - in:') or lines[j].startswith('      in:'):
                    break
                if lines[j] and not lines[j].startswith(' ') and ':' in s:
                    break
                if s == '---':
                    break
                j += 1
            blocks.append((start, j, name))
            i = j
        else:
            i += 1

    for start, end, name in blocks:
        block_text = '\n'.join(lines[start:end])
        for sub in param_subfields:
            if f'{sub}:' not in block_text and f'{sub} :' not in block_text:
                # WARNING(不阻断 commit,但让 AI 看见)
                violations.append(('WARNING', f'parameters[{name or "?"}] 缺 `{sub}:`'))
    return violations


# v4.0.0+ 业务接口响应规范铁律（用户决策 A）：
# - 业务接口 HTTP 永远 200；业务成功/失败由响应体 `code` 字段判断
# - 4xx/5xx 仅在框架层（Flask abort / Webargs / Flask-JWT-Extended 中间件）抛出
# - 业务接口 docstring 的 responses 块只允许列 200
# - 例外：认证接口（login/logout/refresh/verify/register/password）可保留 401/403；
#        流式/下载接口（download/export/stream/upload/file）可保留 416
_AUTH_PATH_KEYWORDS = ('login', 'logout', 'refresh', 'verify', 'register', 'password')
_STREAM_PATH_KEYWORDS = ('download', 'export', 'stream', 'upload', 'file', 'attachment')


# v4.5.0+ 硬门禁:HTTP 方法白名单(只许 GET/POST)
# 依据:接口契约规范 §1.H + API规范 §3.2 HTTP 方法规范 + Flask后端规范 §0 全表
# 业务接口 update/delete 一律 POST,不允许 PUT/PATCH/DELETE
# 例外路径(认证 login/logout/refresh/verify/register/password)也是 POST,无新增豁免
_ALLOWED_HTTP_METHODS = frozenset({'GET', 'POST'})

# v4.5.0+ 硬门禁:路径禁止动态参数白名单(必须用 path param 的极少数场景)
# 依据:接口契约规范 §1.G 例外段 + §10.B OAuth callback + §2.12 webhook
# 业务接口一律走 query/body,不允许 `/detail/<int:id>` `/user/<user_id>` 等
_DYNAMIC_PATH_EXCEPTIONS = (
    'webhook',       # §2.12 webhook 回调 `/webhook/{source}`
    'callback',      # §10.B OAuth callback `/auth/oauth/{provider}/callback`
    'oauth',         # 兜底
)

# v4.5.0+ description 字段禁鉴权字眼清单(接口契约规范 §1.I)
# 全局 security 已声明 Bearer 鉴权,description 不必重述
# v4.4.0 已加部分(见 _FORBIDDEN_DESCRIPTION_CONTENT),
# 本表扩 4 类:精确覆盖 description / parameters[].description / responses[].description 全字段
_AUTH_WORDS_IN_DESCRIPTION = (
    'JWT', 'Bearer', '需登录', '需要登录', '需 JWT', '需要 JWT',
    '需认证', '需要认证', '需鉴权', '需要鉴权', '需 token', '需要 token',
    'Authorization header', 'Authorization 头', '鉴权失败',
)

# v4.5.0+ description 字段禁错误码清单(接口契约规范 §1.J)
# 错误码应放 responses.examples 或 BizError 组件;description 不列「10001 用户不存在」清单
_ERROR_CODE_LIST_PATTERNS = (
    # 中文:「错误码：」/「错误码:」/「错误码列表」/「返回码」
    re.compile(r'错误码[：:]\s*\d+'),
    re.compile(r'错误码列表'),
    re.compile(r'返回码[：:]?\s*\d+'),
    re.compile(r'\d{5}\s+[一-鿿]'),  # 5 位业务码 + 中文:「10001 用户不存在」
    re.compile(r'code[:\s]+\d{4,}'),  # code: 10001 / code 10001
    re.compile(r'\d{5}\s*[、，,/]'),  # 多码并列:「10001、10002」
)


# v4.5.1+ POST 强制 JSON 铁律(接口契约规范 §1.K)
# 业务接口 POST 一律 `Content-Type: application/json`,禁止 form-urlencoded / multipart
# 例外(必须用 multipart 或其他 Content-Type 的场景):upload / import / 第三方回调
#   - /upload:文件上传必须 `multipart/form-data`
#   - /import:Excel/CSV 导入必须 `multipart/form-data`
#   - 第三方回调(微信/支付宝/Stripe/webhook/oauth callback):Content-Type 受第三方协议约束
_POST_JSON_EXCEPTIONS = (
    # 上传 / 导入路径段
    'upload', 'import', 'attachment',
    # 第三方回调路径段
    'webhook', 'callback', 'notify', 'oauth',
)
# docstring 中显式声明的 Content-Type 不合规清单(命中即报 ERROR)
_NON_JSON_CONTENT_TYPES = (
    'application/x-www-form-urlencoded',
    'multipart/form-data',
    'application/x-www-form-urlencoded; charset=utf-8',
)


# v4.0.1+ API 文档零引用铁律:docstring / spec / md 全链路禁用字眼清单
# 设计动机:接口文档应聚焦"接口怎么对接调用",不应含指向其他文档的字眼
# ——这些字眼会让对接方以为还要再去查其他文档才能用
# 跳过规则:YAML 字段名行(形如 `key:` 末尾冒号且无 value)不算违规(这是结构不是字眼)
_FORBIDDEN_REF_WORDS = (
    # 中文
    '参考', '参见', '详见', '引用', '参照', '引自',
    '根据规范', '按照规范', '按规范要求', '遵守规范', '按规范',
    # 英文
    'according to', 'refer to', 'referring to',
    'as described in', 'as specified in', 'see also',
    'conform to', 'conforms to', 'based on', 'defined in', 'outlined in',
)


def check_no_reference_words(docstring: str, route: str = '') -> list[tuple[str, str]]:
    """检查 docstring 是否含禁用引用字眼（v4.0.1+ API 文档零引用铁律）。

    接口文档（docstring / spec / md 全链路）应聚焦"接口怎么对接调用"——
    不应含「参考」「参见」「详见」「引用」等指向其他文档的字眼（这些会让
    对接方以为还要再去查其他文档才能用）。

    禁用字眼清单：中文 11 个（参考/参见/详见/引用/参照/引自/根据规范/按规范/按规范要求/按照规范/遵守规范）+ 英文 11 个（according to/refer to/referring to/as described in/as specified in/see also/conform to/conforms to/based on/defined in/outlined in）。

    扫描范围:docstring 所有非 YAML 字段名行（含 description / summary /
    parameters[].description / responses[].description 等字段值）。
    跳过规则:YAML 字段名行（stripped 末尾 `:` 且不含值）不算违规——这是
    结构标记不是字眼。

    Args:
        docstring: 路由函数的 docstring 文本（含 Flasgger YAML 块）
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) 元组 — level: `'ERROR'` / `'WARNING'`
        空 list = 合规

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> # description 含「参考」 → ERROR
        >>> check_no_reference_words(
        ...     'description:\\n  本接口参考 RBAC 模型实现',
        ...     '/users'
        ... )
        [('ERROR', 'docstring L2 含禁用引用字眼「参考」...')]
        >>> # 纯 YAML 字段名 → 合规
        >>> check_no_reference_words('description:\\n  用户登录', '/auth/login')
        []
    """
    violations: list[tuple[str, str]] = []
    if not docstring:
        return violations

    for line_no, line in enumerate(docstring.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        # 跳过 YAML 字段名行:形如 `key:` 末尾冒号且后面无 value
        # 示例: `summary:`, `description:`, `parameters:`, `- in:`, `200:`
        if stripped.endswith(':') and len(stripped) > 1 and not stripped.startswith('#'):
            continue
        # 扫禁用字眼(子串包含,大小写不敏感)
        line_lower = line.lower()
        for word in _FORBIDDEN_REF_WORDS:
            if word in line_lower:
                violations.append((
                    'ERROR',
                    f'docstring L{line_no} 含禁用引用字眼「{word}」'
                    f'——接口文档应聚焦"怎么对接调用",不应指向其他文档'
                    f'(v4.0.1+ API 文档零引用铁律)',
                ))
                break  # 一行只报第一个命中
    return violations


# v4.4.0+ description 字段禁用字眼（接口契约规范 §1.A.1）
# 这些内容应该在全局组件 / parameters[].description / responses[error_code].description
# 接口 description 字段只写"接口功能"这一句话
_FORBIDDEN_DESCRIPTION_CONTENT = (
    # HTTP 状态码相关
    'HTTP 永远 200', 'HTTP 200', 'business interface', '业务接口 HTTP',
    # 认证方式
    '需登录', '需要登录', '需 JWT', '需要 JWT', 'Bearer Token', '需认证',
    '需鉴权', '需要鉴权', '需要 token', '需 token',
    # 响应结构描述（应交给 schema）
    '返回 {code, msg, data}', '返回 code, msg, data', '响应格式：{code', '返回 {code, data}',
    # 完整路径
    '完整路径', 'full path',
)


# v4.4.0+ $ref 复用铁律（接口契约规范 §1.F）
# schema 重复展开模式（应改为 $ref 引用）
_REPEATED_SCHEMA_MARKERS = (
    "type: object\n      required: [code, msg]",  # StandardResponse 内联展开
    "type: object\n        properties:\n          code:",  # BizResponse 内联展开
    "type: object\n        required: [records, page_no",  # PageResponse 内联展开
    "type: object\n        properties:\n          records:",  # PageResponse 内联展开
)


def check_description_redundant_content(docstring: str, route: str = '') -> list[tuple[str, str]]:
    """检查 description 字段是否含 v4.4.0+ 禁用内容（接口契约规范 §1.A.1）。

    description 字段只写"接口功能"这一句话；HTTP 状态码 / 认证方式 / 错误码清单
    / 响应结构 / 完整路径都不应在每个接口重复。

    跳过规则：YAML 字段名行（`key:` 末尾冒号且无 value）不参与扫描。

    Args:
        docstring: 路由函数的 docstring 文本（含 Flasgger YAML 块）
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) 元组 — level: `'WARNING'` / `'ERROR'`
        v4.4.0+ 默认 WARNING（渐进迁移），v4.5.0 起升级为 ERROR
    """
    violations: list[tuple[str, str]] = []
    if not docstring:
        return violations

    # 抽取 description 字段值（YAML 字段名跳过，仅扫字段值）
    lines = docstring.splitlines()
    in_description = False
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        # 跳过 YAML 字段名行
        if stripped.endswith(':') and len(stripped) > 1 and not stripped.startswith('#'):
            in_description = stripped.startswith('description:')
            if in_description:
                # 同一行可能有 inline value
                inline = stripped.split(':', 1)[1].strip()
                if inline:
                    for word in _FORBIDDEN_DESCRIPTION_CONTENT:
                        if word in inline:
                            violations.append((
                                'WARNING',
                                f'docstring L{line_no} description 字段含冗余内容「{word}」'
                                f'——description 只写接口功能一句话，'
                                f'HTTP 状态码 / 认证 / 错误码 / 响应结构 / 完整路径禁在每个接口重述'
                                f'(v4.4.0+ description 字段禁用内容清单)',
                            ))
                            break
            continue
        if not in_description:
            continue
        # description 字段值行
        for word in _FORBIDDEN_DESCRIPTION_CONTENT:
            if word in line:
                violations.append((
                    'WARNING',
                    f'docstring L{line_no} description 字段含冗余内容「{word}」'
                    f'——description 只写接口功能一句话，'
                    f'HTTP 状态码 / 认证 / 错误码 / 响应结构 / 完整路径禁在每个接口重述'
                    f'(v4.4.0+ description 字段禁用内容清单)',
                ))
                break
        # description 块结束（下一个顶层字段，或 `---`）
        if line and not line.startswith(' ') and ':' in stripped:
            in_description = False
        if stripped == '---':
            in_description = False

    return violations


def check_no_path_in_description(docstring: str, route: str = '') -> list[tuple[str, str]]:
    """检查 description 字段是否误写完整路径前缀（接口契约规范 §1.A.1）。

    完整路径 = basePath + 蓝图 url_prefix + @bp.route 路径——已分别在 Swagger
    template.basePath / Blueprint(url_prefix=...) / @bp.route(...) 声明，
    不应在每个接口 description 重述。

    判定：description 字段值形如 `/api/v1/xxx` / `完整路径：xxx` 命中。

    Args:
        docstring: 路由函数的 docstring 文本
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) — 空 list = 合规
    """
    violations: list[tuple[str, str]] = []
    if not docstring:
        return violations

    lines = docstring.splitlines()
    in_description = False
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.endswith(':') and len(stripped) > 1 and not stripped.startswith('#'):
            in_description = stripped.startswith('description:')
            if in_description:
                inline = stripped.split(':', 1)[1].strip()
                if inline and (inline.startswith('/') or '完整路径' in inline or 'full path' in inline):
                    violations.append((
                        'WARNING',
                        f'docstring L{line_no} description 字段含完整路径「{inline[:50]}」'
                        f'——路径在 basePath / Blueprint url_prefix / @bp.route 声明，'
                        f'不在 description 重述(v4.4.0+ description 字段禁用内容清单)',
                    ))
            continue
        if not in_description:
            continue
        if line.startswith('/') and ('/' in line[1:]) or '完整路径' in line or 'full path' in line.lower():
            violations.append((
                'WARNING',
                f'docstring L{line_no} description 字段含完整路径'
                f'——路径在 basePath / Blueprint url_prefix / @bp.route 声明，'
                f'不在 description 重述(v4.4.0+ description 字段禁用内容清单)',
            ))
        if line and not line.startswith(' ') and ':' in stripped:
            in_description = False
        if stripped == '---':
            in_description = False

    return violations


def check_no_repeated_schema(docstring: str, route: str = '') -> list[tuple[str, str]]:
    """检查 responses schema 是否重复展开通用结构（接口契约规范 §1.F）。

    业务接口 responses.200 schema 应为 `$ref: '#/definitions/BizResponse'` / `PageResponse`
    / `StandardResponse` / `FileResponse` 之一，**禁止**每个接口手工展开 `{code, msg, data}`。

    判定：schemar 字符串含 `{code, msg, data}` / `{records, page_no, ...}` 模式
    （即代码/配置内联展开）→ WARNING。

    Args:
        docstring: 路由函数的 docstring 文本
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) — 空 list = 合规
    """
    violations: list[tuple[str, str]] = []
    if not docstring:
        return violations

    # 简单字符串匹配：检测 schema 段是否含 `code: {type: integer, ...}` 模式
    # 即内联展开 StandardResponse / BizResponse 的 code + msg 字段
    if 'code:' in docstring and 'msg:' in docstring and 'integer' in docstring and 'string' in docstring:
        # 进一步定位：找一个 $ref BizResponse 替代
        if '$ref: \'#/definitions/BizResponse\'' not in docstring and '$ref: "#/definitions/BizResponse"' not in docstring:
            if 'responses:' in docstring:
                # 简化判定：docstring 含 `code: {type: integer` 且 `msg: {type: string` 视为内联展开
                if 'code:\n          type: integer' in docstring or 'code:\n            type: integer' in docstring:
                    violations.append((
                        'WARNING',
                        f'docstring responses schema 疑似手工展开 {{code, msg, data}} 结构'
                        f'——应改为 `$ref: \'#/definitions/BizResponse\'`'
                        f'(v4.4.0+ 通用响应必须用 $ref 复用)',
                    ))

    # 检测分页结构展开（records + page_no + page_size + total_page + total_count）
    page_keys = ('records:', 'page_no:', 'page_size:', 'total_page:', 'total_count:')
    if all(k in docstring for k in page_keys) and '$ref: \'#/definitions/PageResponse\'' not in docstring and '$ref: "#/definitions/PageResponse"' not in docstring:
        if 'responses:' in docstring:
            violations.append((
                'WARNING',
                f'docstring responses.schema 疑似手工展开 {{records, page_no, ...}} 分页结构'
                f'——应改为 `$ref: \'#/definitions/PageResponse\'`'
                f'(v4.4.0+ 通用分页结构必须用 $ref 复用)',
            ))

    return violations


def _has_dynamic_path_param(path: str) -> bool:
    """判断路由路径模板是否含动态参数 `<xxx>` / `<int:xxx>` / `<string:xxx>`。

    Flask path 转换器语法:`<name>` / `<type:name>` / `<type:name1|name2>`。
    任何 `<...>` 形式都视为动态参数(违反 §1.G)。
    """
    if not path:
        return False
    return bool(re.search(r'<[^>]+>', path))


def check_no_dynamic_path(
    path: str,
    docstring: str,
    route: str = '',
) -> list[tuple[str, str]]:
    """检查装饰器路由是否含动态参数（v4.5.0+ 接口契约规范 §1.G 铁律）。

    铁律：业务接口路径模板**禁止**含动态参数 `<xxx>` / `<int:xxx>`。
    所有资源标识（id / user_id / order_id 等）必须走 query 或 body。

    反例：`@bp.route('/detail/<int:id>', methods=['GET'])`
    正例：`@bp.route('/detail', methods=['GET'])` + query `id`

    例外（必须含 path param 的场景）：
      - webhook 回调：`/webhook/{source}`（§2.12）
      - OAuth callback：`/auth/oauth/{provider}/callback`（§10.B）

    Args:
        path: 装饰器第一位置参数的路径模板字符串
        docstring: 路由函数的 docstring 文本（保留参数以与其他 check_* 签名一致）
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) 元组 — level: `'ERROR'`
        空 list = 合规或为例外路径

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> # 含路径参数 → ERROR
        >>> check_no_dynamic_path('/detail/<int:id>', '', '/detail')
        [('ERROR', '路由 `/detail/<int:id>` 含动态参数 `<int:id>`...')]
        >>> # webhook 例外 → 合规
        >>> check_no_dynamic_path('/webhook/<source>', '', '/webhook/payment')
        []
    """
    violations: list[tuple[str, str]] = []
    if not path or not _has_dynamic_path_param(path):
        return violations

    # 例外白名单判定:路径段内含 webhook/oauth/callback 关键字
    route_lower = (route or path).lower()
    segments = [seg for seg in re.split(r'[/\-_.<>:]', route_lower) if seg]
    is_exception = any(kw in segments for kw in _DYNAMIC_PATH_EXCEPTIONS)
    if is_exception:
        return violations

    # 提取所有动态参数便于诊断
    params = re.findall(r'<[^>]+>', path)
    violations.append((
        'ERROR',
        f'路由 `{path}` 含动态参数 {params}'
        f'——所有资源标识(id/user_id/order_id 等)必须走 query 或 body 传递'
        f'(v4.5.0+ 接口契约规范 §1.G 路径禁止动态参数铁律)'
        f'；例如 `/detail/<int:id>` 改为 `/detail?id={{id}}`'
    ))
    return violations


def check_allowed_methods(
    methods: list[str],
    path: str = '',
    route: str = '',
) -> list[tuple[str, str]]:
    """检查装饰器 methods= 是否在白名单内（v4.5.0+ 接口契约规范 §1.H 铁律）。

    铁律：业务接口 HTTP 方法**只允许 GET 或 POST**。
    列表/详情/字典/导出/下载/进度/流式 → GET；创建/更新/删除/批量删除/导入/上传/bind/webhook → POST。
    禁止 PUT/PATCH/DELETE/HEAD/OPTIONS——避免前端区分语义（§2.4 update 显式说明）。

    Args:
        methods: 装饰器 methods 列表(如 `['GET']` / `['POST']`)
        path: 装饰器路径模板(诊断信息用)
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) 元组 — level: `'ERROR'`
        空 list = 合规

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> # PUT → ERROR
        >>> check_allowed_methods(['PUT'], '/update', '/update')
        [('ERROR', '路由 `/update` methods=含 PUT...')]
        >>> # GET → 合规
        >>> check_allowed_methods(['GET'], '/list', '/list')
        []
        >>> # @bp.get() → 也算 ['GET'] → 合规
        >>> check_allowed_methods(['GET'], '/list', '/list')
        []
    """
    violations: list[tuple[str, str]] = []
    if not methods:
        return violations

    bad_methods = [m for m in methods if m.upper() not in _ALLOWED_HTTP_METHODS]
    if bad_methods:
        violations.append((
            'ERROR',
            f'路由 `{path or route or "(未知)"}` methods=含 {bad_methods}'
            f'——业务接口 HTTP 方法只允许 GET 或 POST'
            f'(v4.5.0+ 接口契约规范 §1.H HTTP 方法白名单铁律)'
            f'；依据 §0 速查表 + §2 接口类型表,列表/详情/导出用 GET,'
            f'创建/更新/删除/bind/webhook 用 POST(避免 PUT/PATCH 语义混淆)'
        ))
    return violations


def check_no_auth_in_description(
    docstring: str,
    route: str = '',
) -> list[tuple[str, str]]:
    """检查 description / parameters[].description / responses[].description
    是否含鉴权相关字眼（v4.5.0+ 接口契约规范 §1.I 铁律）。

    铁律：鉴权方式由 Swagger 全局 `securityDefinitions` + `security` 声明，
    UI 自动展示锁图标——description / parameters[].description /
    responses[].description 不必重述「JWT / Bearer / 需登录」。

    反例：`description: 本接口需 JWT Bearer Token 认证后调用`
    正例：`description: 查询用户详情。` + 全局 `security: - Bearer: []`

    扫描范围：description 字段值 + parameters[].description + responses[].description。
    跳过规则：YAML 字段名行（`key:` 末尾冒号且无 value）不参与扫描。

    Args:
        docstring: 路由函数的 docstring 文本
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) 元组 — level: `'ERROR'`
        空 list = 合规

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> # description 含「JWT」 → ERROR
        >>> check_no_auth_in_description(
        ...     'description:\\n  本接口需 JWT Bearer Token 认证',
        ...     '/users'
        ... )
        [('ERROR', 'docstring L2 description 字段含鉴权字眼「JWT」...')]
        >>> # 纯字段名 → 合规
        >>> check_no_auth_in_description('description:\\n  用户登录', '/login')
        []
    """
    violations: list[tuple[str, str]] = []
    if not docstring:
        return violations

    in_description = False
    current_field = ''  # 当前正在扫描的字段名
    for line_no, line in enumerate(docstring.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        # 跳过 YAML 字段名行(`key:` 末尾冒号无 value)
        if stripped.endswith(':') and len(stripped) > 1 and not stripped.startswith('#'):
            field_name = stripped[:-1].strip()
            # description / parameters[].description / responses[].description 都参与
            if field_name == 'description' or field_name.endswith('.description'):
                in_description = True
                current_field = field_name
                # inline value 扫描
                inline = stripped.split(':', 1)[1].strip()
                if inline:
                    for word in _AUTH_WORDS_IN_DESCRIPTION:
                        if word in inline:
                            violations.append((
                                'ERROR',
                                f'docstring L{line_no} {current_field} 字段含鉴权字眼「{word}」'
                                f'——鉴权方式由全局 `securityDefinitions` + `security` 声明,'
                                f'UI 自动展示锁图标,不在 description 重述'
                                f'(v4.5.0+ 接口契约规范 §1.I description 禁鉴权字眼铁律)'
                            ))
                            break
            else:
                in_description = False
                current_field = ''
            continue
        if not in_description:
            continue
        # 字段值行扫描
        for word in _AUTH_WORDS_IN_DESCRIPTION:
            if word in line:
                violations.append((
                    'ERROR',
                    f'docstring L{line_no} {current_field} 字段含鉴权字眼「{word}」'
                    f'——鉴权方式由全局 `securityDefinitions` + `security` 声明,'
                    f'UI 自动展示锁图标,不在 description 重述'
                    f'(v4.5.0+ 接口契约规范 §1.I description 禁鉴权字眼铁律)'
                ))
                break
        # 字段块结束
        if line and not line.startswith(' ') and ':' in stripped:
            in_description = False
        if stripped == '---':
            in_description = False

    return violations


def check_no_error_codes_in_description(
    docstring: str,
    route: str = '',
) -> list[tuple[str, str]]:
    """检查 description 是否含错误码清单（v4.5.0+ 接口契约规范 §1.J 铁律）。

    铁律：错误码放 `responses.examples` 或 `$ref BizError` 组件；
    description 不列「10001 用户不存在 / 10002 用户已禁用」清单——这种列表应统一
    在 `BizError` 组件里维护,description 短句仅说明接口功能。

    反例：
        description: |
          错误码：
          10001 用户不存在
          10002 用户已禁用

    正例：
        description: 用户登录。
        responses:
          200:
            examples:
              application/json:
                $ref: '#/definitions/BizError'

    Args:
        docstring: 路由函数的 docstring 文本
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) 元组 — level: `'ERROR'`
        空 list = 合规

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> # description 含「10001 用户不存在」 → ERROR
        >>> check_no_error_codes_in_description(
        ...     'description:\\n  错误码:\\n  10001 用户不存在',
        ...     '/login'
        ... )
        [('ERROR', 'docstring description 含错误码清单「10001 用户不存在」...')]
    """
    violations: list[tuple[str, str]] = []
    if not docstring:
        return violations

    in_description = False
    for line_no, line in enumerate(docstring.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.endswith(':') and len(stripped) > 1 and not stripped.startswith('#'):
            in_description = stripped.startswith('description:')
            # inline value 扫描
            if in_description:
                inline = stripped.split(':', 1)[1].strip()
                if inline:
                    for pat in _ERROR_CODE_LIST_PATTERNS:
                        m = pat.search(inline)
                        if m:
                            violations.append((
                                'ERROR',
                                f'docstring L{line_no} description 字段含错误码清单「{m.group()}」'
                                f'——错误码统一在 responses.examples 或 BizError 组件维护,'
                                f'description 短句仅说明接口功能'
                                f'(v4.5.0+ 接口契约规范 §1.J description 禁错误码清单铁律)'
                            ))
                            break
            continue
        if not in_description:
            continue
        # 字段值行扫描
        for pat in _ERROR_CODE_LIST_PATTERNS:
            m = pat.search(line)
            if m:
                violations.append((
                    'ERROR',
                    f'docstring L{line_no} description 字段含错误码清单「{m.group()}」'
                    f'——错误码统一在 responses.examples 或 BizError 组件维护,'
                    f'description 短句仅说明接口功能'
                    f'(v4.5.0+ 接口契约规范 §1.J description 禁错误码清单铁律)'
                ))
                break
        # 字段块结束
        if line and not line.startswith(' ') and ':' in stripped:
            in_description = False
        if stripped == '---':
            in_description = False

    return violations


def check_post_must_be_json(
    methods: list[str],
    docstring: str,
    route: str = '',
) -> list[tuple[str, str]]:
    """检查 POST 接口的 Content-Type 是否声明为 application/json（v4.5.1+ §1.K 铁律）。

    铁律：业务接口 HTTP POST 一律 `Content-Type: application/json`，禁止
    `application/x-www-form-urlencoded` / `multipart/form-data`——
    避免后端代码 `request.form` / `request.files` 兜底导致接口语义混乱
    （后端应统一 `request.get_json()`，schema 校验交给 Webargs / pydantic）。

    反例（POST + form-urlencoded）：
        ---
        tags:
          - 用户
        parameters:
          - name: username
            in: formData        # ← form 形式，违反 §1.K
            type: string
        ---

    正例（POST + JSON）：
        ---
        tags:
          - 用户
        parameters:
          - name: body
            in: body
            schema:
              type: object
              properties:
                username: {type: string}
        ---

    例外（必须用 multipart / 第三方协议 Content-Type 的路径段）：
      - 文件上传：`/upload` / `/attachment` 段
      - 数据导入：`/import` 段（Excel/CSV）
      - 第三方回调：`/webhook/<source>` / `/callback/<provider>` /
        `/notify` / `/oauth/<provider>/callback` 段

    扫描方式：
      1. methods= 含 POST → 检查 path 段是否在 _POST_JSON_EXCEPTIONS
      2. 在白名单 → 跳过
      3. 不在 → 扫描 docstring 内 parameters[] 的 in: formData / consumes
         字段是否含 `_NON_JSON_CONTENT_TYPES` 之一

    Args:
        methods: 装饰器 methods 列表
        docstring: 路由函数的 docstring 文本
        route: 路由路径字符串（用于错误信息标识）

    Returns:
        list of (level, msg) 元组 — level: `'ERROR'`
        空 list = 合规或为例外路径

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> # POST + formData → ERROR
        >>> check_post_must_be_json(['POST'], 'parameters:\\n  - in: formData', '/users/create')
        [('ERROR', '路由 `/users/create` 是 POST 但 parameters 含 `in: formData`...')]
        >>> # POST + JSON body → 合规
        >>> check_post_must_be_json(['POST'], 'parameters:\\n  - in: body\\n    schema:', '/users/create')
        []
        >>> # POST /upload → 例外豁免
        >>> check_post_must_be_json(['POST'], 'parameters:\\n  - in: formData', '/files/upload')
        []
    """
    violations: list[tuple[str, str]] = []
    if not methods or not docstring:
        return violations

    # 1. 仅 POST 触发（GET 不参与——GET 没有 body，Content-Type 无关）
    methods_upper = {m.upper() for m in methods}
    if 'POST' not in methods_upper:
        return violations

    # 2. 例外白名单判定
    route_lower = (route or '').lower()
    route_segments = [seg for seg in re.split(r'[/\-_.]', route_lower) if seg]
    is_exception = any(kw in route_segments for kw in _POST_JSON_EXCEPTIONS)
    if is_exception:
        return violations

    # 3. 扫描 docstring parameters[] 的 in: 字段
    #    命中 in: formData / in: formData  / consumes 字段含 _NON_JSON_CONTENT_TYPES
    for line_no, line in enumerate(docstring.splitlines(), 1):
        stripped = line.strip()
        # 3a. in: formData / in: formdata（大小写不敏感）
        if re.search(r'\bin:\s*formdata\b', line, re.IGNORECASE):
            violations.append((
                'ERROR',
                f'路由 `{route}` 是 POST 但 parameters 含 `in: formData`'
                f'——业务接口 POST 一律 `Content-Type: application/json`'
                f'(v4.5.1+ 接口契约规范 §1.K POST 强制 JSON 铁律)；'
                f'改写为 `in: body` + JSON schema(JSON body 走 `request.get_json()`,'
                f'schema 校验交 Webargs / pydantic)；'
                f'上传文件场景请走 /upload 段(已豁免)或独立 multipart 接口'
            ))
            break  # 一条违规足够

    # 3b. consumes 字段含 form-urlencoded / multipart（Swagger 2.0 全局声明）
    for ct in _NON_JSON_CONTENT_TYPES:
        if ct in docstring:
            # 进一步定位:在 consumes 字段里
            if re.search(rf'^\s*consumes:.*\b{re.escape(ct)}\b', docstring, re.MULTILINE):
                violations.append((
                    'ERROR',
                    f'路由 `{route}` 是 POST 但 docstring `consumes:` 声明 `{ct}`'
                    f'——业务接口 POST 一律 `Content-Type: application/json`'
                    f'(v4.5.1+ 接口契约规范 §1.K POST 强制 JSON 铁律)；'
                    f'上传/导入/回调场景请走豁免路径段(upload/import/webhook/callback/oauth)'
                ))
                break

    return violations


def check_business_api_responses(docstring: str, route: str = '') -> list[tuple[str, str]]:
    """检查业务接口的 responses 块是否误列 4xx/5xx（v4.0.0+ 业务接口响应规范铁律）。

    业务接口（一般路由）的 docstring `responses:` 块**只允许列 `200`**——
    业务成功/失败由响应体 `code` 字段判断（`code: 0` = 成功；`code: 10001` = 业务失败）。
    错误码（4xx/5xx）由框架层（Flask abort / Webargs / Flask-JWT-Extended 中间件）自动抛出，
    不应由业务接口在 docstring 声明。

    例外路径（不参与本检查）：
      - 认证接口：含 `login` / `logout` / `refresh` / `verify` / `register` / `password` 关键字
      - 流式接口：含 `download` / `export` / `stream` / `upload` / `file` / `attachment` 关键字

    Args:
        docstring: 路由函数的 docstring 文本（含 Flasgger YAML 块）
        route: 路由路径字符串（如 `'/users/{id}'`），用于识别是否为例外路径

    Returns:
        list of (level, msg) 元组 — level: `'ERROR'` / `'WARNING'`
        空 list = 合规或为例外路径

    Raises:
        无

    Side Effects:
        无

    Example:
        >>> # 业务接口误列 401 → ERROR
        >>> check_business_api_responses(
        ...     "responses:\\n    200:\\n      description: ok\\n    401:\\n      description: 未登录",
        ...     "/users"
        ... )
        [('ERROR', '业务接口 responses 误列 4xx/5xx (401)...')]
        >>> # 认证接口保留 401 → 合规（跳过）
        >>> check_business_api_responses(
        ...     "responses:\\n    200:\\n      description: ok\\n    401:\\n      description: 未登录",
        ...     "/auth/login"
        ... )
        []
        >>> # 业务接口只列 200 → 合规
        >>> check_business_api_responses(
        ...     "responses:\\n    200:\\n      description: ok",
        ...     "/users"
        ... )
        []
    """
    violations = []

    # 1. 识别例外路径（按 / 和 - 切分，段内匹配关键字）
    #    避免 `profile` 含 `file` / `password_reset` 含 `password` / `exported` 含 `export`
    #    等子串误判——仅当路径段本身就是关键字才算例外
    route_lower = (route or '').lower()
    route_segments = [seg for seg in re.split(r'[/\-_.]', route_lower) if seg]
    is_exception = any(
        kw in route_segments for kw in _AUTH_PATH_KEYWORDS + _STREAM_PATH_KEYWORDS
    )
    if is_exception:
        return violations

    # 2. 扫 responses 块（同 check_responses_error_codes 的简化扫描）
    lines = docstring.splitlines()
    in_responses = False
    codes: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_responses:
            if stripped.startswith('responses:') or stripped.startswith('responses :'):
                in_responses = True
            continue
        # 顶层字段结束
        if line and not line.startswith(' ') and ':' in stripped:
            break
        if stripped == '---':
            break
        # 状态码行（4 空格 + 数字 + :）
        if line.startswith('    ') and stripped.endswith(':') and stripped[:-1].isdigit():
            codes.append(stripped[:-1])

    if not codes:
        # 没列出任何状态码 → 5 字段契约检查已先报错，这里不重复
        return violations

    # 3. 业务接口：必须只含 200
    if '200' not in codes:
        violations.append((
            'ERROR',
            '业务接口 responses 缺 200（v4.0.0+ 铁律：业务接口 HTTP 必须 200）'
        ))

    bad_codes = [c for c in codes if c != '200' and c[0] in ('4', '5')]
    if bad_codes:
        violations.append((
            'ERROR',
            f'业务接口 responses 误列 4xx/5xx ({", ".join(sorted(bad_codes))})；'
            f'按 v4.0.0+ 业务接口响应规范铁律，HTTP 一律 200，业务错误（认证失败等）走响应体 `code` 字段；'
            f'4xx/5xx 由框架层（Flask abort / Webargs / Flask-JWT-Extended 中间件）抛出，不由业务接口声明。'
        ))

    return violations


def main():
    parser = argparse.ArgumentParser(description='mcpowers swagger 单文件 lint helper')
    parser.add_argument('--file-path', required=True, help='要 lint 的文件路径(相对项目根或绝对)')
    parser.add_argument('--fields-file', required=True, help='字段清单文件路径(swagger-required-fields.sh 输出)')
    args = parser.parse_args()

    file_path = Path(args.file_path)

    # 非 .py 文件 → 放行(YAGNI,JS/TS 留给未来扩展)
    if file_path.suffix != '.py':
        sys.exit(0)

    if not file_path.exists():
        print(f"⚠️  [swagger-lint-helper] 文件不存在:{file_path}", file=sys.stderr)
        sys.exit(0)

    # 解析字段清单
    required_fields, param_sub, resp_sub = parse_fields_file(Path(args.fields_file))

    # 复用现有 lint:提取 (路由, docstring) 三元组
    entries = parse_python_docstring(file_path)
    if not entries:
        sys.exit(0)  # 无路由函数 → 不查

    # v4.5.0+ AST 解析装饰器,提取 path / methods 用于 check_no_dynamic_path /
    # check_allowed_methods。失败时返回 {} → 新检查自动跳过(不阻断存量代码)。
    try:
        decorators_by_line = _parse_route_decorators(file_path)
    except Exception as exc:
        print(
            f"[swagger-contract] _parse_route_decorators 失败（不影响其它检查）:{exc}",
            file=sys.stderr,
        )
        decorators_by_line = {}

    all_violations: list[tuple[str, int, str, str]] = []  # (level, line, func, msg)
    error_count = 0
    warning_count = 0

    for entry in entries:
        route = entry['route']
        func = entry['func']
        line_no = entry['line']
        docstring = entry['docstring']

        # 关联装饰器：entry 的 line 是 def 行号；装饰器行号 = line - 1（最常见）
        # 同时兼容装饰器行 = line - 2 / - 3（多装饰器场景）
        deco = decorators_by_line.get(line_no - 1) or decorators_by_line.get(line_no - 2) or decorators_by_line.get(line_no - 3) or {}
        path = deco.get('path') or route  # 兜底用 entry['route']
        methods = deco.get('methods') or []

        # 必填顶层字段名检查(v2.31.0+ 写时硬门禁的核心检查)
        for level, msg in check_required_field_names(docstring, required_fields):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # parameters 子字段必填项(WARNING 不阻断,仅提醒)
        for level, msg in check_parameter_subfields(docstring, param_sub):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.0.0+ 业务接口响应规范铁律（替代旧 check_responses_error_codes）
        # 业务接口 responses 块只列 200；4xx/5xx 由框架层抛出，不由业务接口声明
        for level, msg in check_business_api_responses(docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.0.1+ API 文档零引用铁律：description / summary 等字段值
        # 禁含「参考 / 参见 / 详见 / 引用」等指向其他文档的字眼
        for level, msg in check_no_reference_words(docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.4.0+ description 字段禁用内容清单（接口契约规范 §1.A.1）
        # description 字段只写"接口功能"这一句话；HTTP 状态码 / 认证方式 / 错误码清单
        # / 响应结构 / 完整路径都禁在每个接口重述
        for level, msg in check_description_redundant_content(docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.4.0+ description 字段禁用完整路径
        for level, msg in check_no_path_in_description(docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.4.0+ 通用响应/分页结构必须用 $ref 复用
        for level, msg in check_no_repeated_schema(docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.5.0+ 接口契约规范 §1.G 路径禁动态参数铁律
        # 装饰器 @bp.route('/detail/<int:id>') → ERROR（除 webhook/oauth/callback 例外）
        for level, msg in check_no_dynamic_path(path, docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.5.0+ 接口契约规范 §1.H HTTP 方法白名单铁律
        # methods= 只允许 GET / POST（PUT/PATCH/DELETE/HEAD/OPTIONS → ERROR）
        for level, msg in check_allowed_methods(methods, path, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.5.0+ 接口契约规范 §1.I description 禁鉴权字眼铁律
        # JWT / Bearer / 需登录 等不应出现在 description / parameters[].description
        for level, msg in check_no_auth_in_description(docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.5.0+ 接口契约规范 §1.J description 禁错误码清单铁律
        # 错误码统一在 responses.examples / BizError 组件维护
        for level, msg in check_no_error_codes_in_description(docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # v4.5.1+ 接口契约规范 §1.K POST 强制 JSON 铁律
        # 业务接口 POST 一律 application/json;禁 form-urlencoded / multipart
        # 例外:upload / import / attachment / webhook / callback / notify / oauth 路径段
        for level, msg in check_post_must_be_json(methods, docstring, route):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

    # ---------- 输出违规汇总 ----------
    if not all_violations:
        sys.exit(0)

    # 按函数分组输出(单条汇总,不刷屏)
    print(f"[swagger-contract] [{file_path}] 共 {len(all_violations)} 条违规( ERROR: {error_count}, WARNING: {warning_count})", file=sys.stderr)
    print('', file=sys.stderr)
    for level, line_no, func, msg in all_violations:
        prefix = '❌ ERROR' if level == 'ERROR' else '⚠️  WARN '
        print(f'  {prefix} L{line_no} {func}(): {msg}', file=sys.stderr)

    print('', file=sys.stderr)
    print('请补全 5 字段契约,详见:', file=sys.stderr)
    print('  - mcpowers-shared/docs/技术规范/接口契约规范.md §1', file=sys.stderr)
    print('  - mcpowers-shared/docs/技术规范/Swagger字段契约.md', file=sys.stderr)
    print('  - Flask/Flasgger 实现参考:mcpowers-shared/docs/API文档/swagger_template.md', file=sys.stderr)

    # ERROR > 0 时阻断
    if error_count > 0:
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    sys.exit(main())
