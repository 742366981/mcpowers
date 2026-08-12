#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导出 Flasgger 文档为 JSON 和 Markdown

使用方式：
    python tools/export_docs.py
"""

import os
import sys
import json
from datetime import datetime


def get_error_codes():
    """返回通用错误码定义"""
    return """## 错误码

| 错误码 | 说明 |
|:------:|:-----|
| 0 | 成功 |
| 400 | 参数错误 |
| 401 | 未登录或token过期 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

> **业务错误码**：业务错误码由各项目自行定义，格式为 10001+，请根据实际业务补充。

"""


def build_example_from_props(props):
    """根据 properties 构建请求示例

    Args:
        props: 属性字典

    Returns:
        示例字典
    """
    if not props:
        return {}
    ex = {}
    for pk, pv in props.items():
        if not isinstance(pv, dict):
            continue
        pv_type = pv.get('type', 'string')
        pv_example = pv.get('example')
        if pv_example is not None:
            ex[pk] = pv_example
        elif pv_type == 'string':
            ex[pk] = ''
        elif pv_type == 'integer' or pv_type == 'number':
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
    """从响应 properties 中提取 data 字段的属性

    Args:
        resp_props: 响应属性字典

    Returns:
        data 字段的属性字典，如果没有 data 字段则返回空字典
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
    """判断是否为分页响应

    Args:
        resp_props: 响应属性字典

    Returns:
        (bool, data字段属性字典)
    """
    data_props = extract_response_data_fields(resp_props)
    pagination_fields = {'records', 'page_no', 'page_size', 'total_page', 'total_count'}
    return all(field in data_props for field in pagination_fields), data_props


def find_auth_paths(spec):
    """自动识别登录和登出接口路径"""
    paths = spec.get('paths', {})
    login_path = None
    logout_path = None

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                continue
            # 识别登录接口
            if 'login' in path.lower() and not login_path:
                login_path = f"{method.upper()} {path}"
            # 识别登出接口
            if 'logout' in path.lower() and not logout_path:
                logout_path = f"{method.upper()} {path}"

    return login_path, logout_path


def json_to_markdown(spec, output_file, login_path=None):
    """将 Swagger JSON 转换为 Markdown

    Args:
        spec: Swagger JSON 对象
        output_file: 输出文件路径
        login_path: 登录接口路径（如 "POST /auth/login"），自动识别时可传 None
    """
    lines = []

    # 自动识别登录路径
    if not login_path:
        auto_login, _ = find_auth_paths(spec)
        login_path = auto_login or "POST /auth/login"

    # 文档头部
    title = spec.get('info', {}).get('title', 'API 文档')
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**版本**: {spec.get('info', {}).get('version', '1.0.0')}")
    lines.append(f"**更新日期**: {datetime.now().strftime('%Y-%m-%d')}")
    base_path = spec.get('basePath', '/{prefix}')
    lines.append(f"**基础路径**: `http://{{host}}:{{port}}{base_path}`")
    lines.append("")

    # 目录
    paths = spec.get('paths', {})
    tag_apis = {}

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                continue
            tags = details.get('tags', [])
            for tag in tags:
                if tag not in tag_apis:
                    tag_apis[tag] = []
                tag_apis[tag].append({'path': path, 'method': method.upper(), 'details': details})

    lines.append("## 目录")
    lines.append("")
    for tag in sorted(tag_apis.keys()):
        lines.append(f"- [{tag}](#{tag})")
    lines.append("")
    lines.append("---\n")

    # 通用规范
    lines.append("## 通用规范")
    lines.append("")
    lines.append("### 认证方式")
    lines.append("")
    lines.append("系统采用 JWT Token 认证机制。大部分接口需要携带 Token 才能访问。")
    lines.append("")
    lines.append("#### 1. 获取 Token")
    lines.append("")
    lines.append(f"**接口地址**: `{login_path}`")
    lines.append("")
    lines.append("**请求参数**:")
    lines.append("")
    lines.append("| 参数名 | 类型 | 必填 | 说明 |")
    lines.append("|:------|:----:|:----:|------|")
    lines.append("| username | string | 是 | 用户名（手机号也可以） |")
    lines.append("| password | string | 是 | 密码（MD5格式） |")
    lines.append("")
    lines.append("**请求示例**:")
    lines.append("```json")
    lines.append('{"username": "admin", "password": "0192023a7bbd73250516f069df18b500"}')
    lines.append("```")
    lines.append("")
    lines.append("**响应示例**:")
    lines.append("```json")
    lines.append("""{
  "code": 0,
  "msg": "success",
  "data": {
    "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "user_id": 1,
    "username": "admin"
  }
}""")
    lines.append("```")
    lines.append("")
    lines.append("#### 2. 使用 Token")
    lines.append("")
    lines.append("在请求头中添加 Authorization 字段，格式为：")
    lines.append("")
    lines.append("```")
    lines.append("Authorization: Bearer {token}")
    lines.append("```")
    lines.append("")
    lines.append("---\n")

    # 错误码
    lines.append(get_error_codes())
    lines.append("---\n")

    # 各模块接口
    for tag in sorted(tag_apis.keys()):
        lines.append(f"## {tag}")
        lines.append("")

        apis = tag_apis[tag]
        apis.sort(key=lambda x: (x['path'], x['method']))

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

            lines.append(f"### {idx}. {summary}")
            lines.append("")
            lines.append(f"**接口地址**: `{method} {path}`")
            lines.append("")
            lines.append(f"**需认证**: {'是' if need_auth else '否'}")
            lines.append("")

            if description:
                lines.append(f"**说明**: {description}")
                lines.append("")

            # 请求参数
            parameters = details.get('parameters', [])
            if parameters:
                lines.append("**请求参数**:")
                lines.append("")

                body_params = [p for p in parameters if p.get('in') == 'body']
                query_path_params = [p for p in parameters if p.get('in') in ('query', 'path')]
                formdata_params = [p for p in parameters if p.get('in') == 'formData']  # v2.4.0 新增
                header_params = [p for p in parameters if p.get('in') == 'header']     # v2.4.0 新增

                if body_params:
                    schema = body_params[0].get('schema', {})
                    properties = schema.get('properties', {})
                    required = schema.get('required', [])

                    lines.append("| 参数名 | 类型 | 必填 | 说明 |")
                    lines.append("|:------|:----:|:----:|------|")

                    for prop_name, prop_info in properties.items():
                        if not isinstance(prop_info, dict):
                            continue
                        prop_type = prop_info.get('type', 'string')
                        is_required = '是' if prop_name in required else '否'
                        prop_desc = prop_info.get('description', '')
                        prop_example = prop_info.get('example', '')
                        if prop_example:
                            prop_desc = f"{prop_desc}（示例: {prop_example}）"
                        lines.append(f"| {prop_name} | {prop_type} | {is_required} | {prop_desc} |")
                    lines.append("")

                if query_path_params:
                    lines.append("| 参数名 | 位置 | 类型 | 必填 | 说明 |")
                    lines.append("|:------|:----:|:----:|:----:|------|")
                    for param in query_path_params:
                        prop_desc = param.get('description', '')
                        prop_example = param.get('example', '')
                        if prop_example:
                            prop_desc = f"{prop_desc}（示例: {prop_example}）"
                        lines.append(f"| {param.get('name')} | {param.get('in')} | {param.get('type')} | {'是' if param.get('required') else '否'} | {prop_desc} |")
                    lines.append("")

                if header_params:
                    lines.append("**请求头（Headers）**:")
                    lines.append("")
                    lines.append("| 参数名 | 类型 | 必填 | 说明 |")
                    lines.append("|:------|:----:|:----:|------|")
                    for param in header_params:
                        prop_desc = param.get('description', '')
                        prop_example = param.get('example', '')
                        if prop_example:
                            prop_desc = f"{prop_desc}（示例: {prop_example}）"
                        lines.append(f"| {param.get('name')} | {param.get('type', 'string')} | {'是' if param.get('required') else '否'} | {prop_desc} |")
                    lines.append("")

                if formdata_params:
                    lines.append("**请求体（Form Data）**:")
                    lines.append("")
                    lines.append("| 参数名 | 类型 | 必填 | 说明 |")
                    lines.append("|:------|:----:|:----:|------|")
                    for param in formdata_params:
                        prop_desc = param.get('description', '')
                        prop_example = param.get('example', '')
                        if prop_example:
                            prop_desc = f"{prop_desc}（示例: {prop_example}）"
                        lines.append(f"| {param.get('name')} | {param.get('type', 'string')} | {'是' if param.get('required') else '否'} | {prop_desc} |")
                    lines.append("")

                # 请求示例
                if body_params:
                    schema = body_params[0].get('schema', {})
                    example = schema.get('example', {})

                    if example:
                        lines.append("**请求示例**:")
                        lines.append("```json")
                        # 格式化JSON
                        example_str = json.dumps(example, ensure_ascii=False, indent=2)
                        lines.append(example_str)
                        lines.append("```")
                        lines.append("")
                    else:
                        # 根据properties生成示例
                        props = schema.get('properties', {})
                        if props:
                            lines.append("**请求示例**:")
                            lines.append("```json")
                            lines.append(json.dumps(build_example_from_props(props), ensure_ascii=False, indent=2))
                            lines.append("```")
                            lines.append("")

            # 响应
            responses = details.get('responses', {})
            if '200' in responses:
                response_200 = responses['200']
                resp_schema = response_200.get('schema', {})
                resp_desc = response_200.get('description', '')

                lines.append(f"**响应说明**: {resp_desc}")
                lines.append("")

                # 响应参数
                resp_props = resp_schema.get('properties', {})
                if resp_props:
                    lines.append("**响应参数**:")
                    lines.append("")
                    lines.append("| 字段 | 类型 | 说明 |")
                    lines.append("|:-----|:-----|:-----|")

                    for prop_name, prop_info in resp_props.items():
                        if not isinstance(prop_info, dict):
                            continue
                        prop_type = prop_info.get('type', 'string')
                        prop_desc = prop_info.get('description', '')
                        lines.append(f"| {prop_name} | {prop_type} | {prop_desc} |")
                    lines.append("")

                    # 检查是否是分页响应
                    is_page, data_props = is_pagination_response(resp_props)

                    # data 响应参数（如果有 data 字段）
                    if 'data' in resp_props and data_props:
                        lines.append("**data 响应参数**:")
                        lines.append("")
                        lines.append("| 字段 | 类型 | 说明 |")
                        lines.append("|:-----|:-----|:-----|")

                        for prop_name, prop_info in data_props.items():
                            if not isinstance(prop_info, dict):
                                continue
                            prop_type = prop_info.get('type', 'string')
                            prop_desc = prop_info.get('description', '')
                            lines.append(f"| {prop_name} | {prop_type} | {prop_desc} |")
                        lines.append("")

                        # 分页响应添加 records 字段说明
                        if is_page and 'records' in data_props:
                            records_info = data_props.get('records', {})
                            if isinstance(records_info, dict) and records_info.get('type') == 'array':
                                items = records_info.get('items', {})
                                if isinstance(items, dict) and 'properties' in items:
                                    lines.append("**records 字段说明**:")
                                    lines.append("")
                                    lines.append("| 字段 | 类型 | 说明 |")
                                    lines.append("|:-----|:-----|:-----|")
                                    for rec_name, rec_info in items['properties'].items():
                                        if not isinstance(rec_info, dict):
                                            continue
                                        rec_type = rec_info.get('type', 'string')
                                        rec_desc = rec_info.get('description', '')
                                        lines.append(f"| {rec_name} | {rec_type} | {rec_desc} |")
                                    lines.append("")

                        # data 是数组时，添加数组元素字段说明（非分页场景）
                        if not is_page:
                            data_info = resp_props.get('data')
                            if isinstance(data_info, dict) and data_info.get('type') == 'array':
                                items = data_info.get('items', {})
                                if isinstance(items, dict) and 'properties' in items:
                                    lines.append("**data 响应参数**:")
                                    lines.append("")
                                    lines.append("| 字段 | 类型 | 说明 |")
                                    lines.append("|:-----|:-----|:-----|")
                                    for item_name, item_info in items['properties'].items():
                                        if not isinstance(item_info, dict):
                                            continue
                                        item_type = item_info.get('type', 'string')
                                        item_desc = item_info.get('description', '')
                                        lines.append(f"| {item_name} | {item_type} | {item_desc} |")
                                    lines.append("")

                # 响应示例
                lines.append("**响应示例**:")
                lines.append("```json")

                # 优先从examples字段获取完整响应示例
                example_response = response_200.get('examples', {}).get('application/json')
                if not example_response:
                    # 回退到从schema.properties构建
                    example_response = {}
                    for prop_name, prop_info in resp_props.items():
                        if isinstance(prop_info, dict):
                            prop_type = prop_info.get('type', 'string')
                            prop_example = prop_info.get('example')
                            if prop_example is not None:
                                example_response[prop_name] = prop_example
                            elif prop_type == 'object' and 'properties' in prop_info:
                                example_response[prop_name] = build_example_from_props(prop_info.get('properties', {}))
                            elif prop_type == 'array':
                                example_response[prop_name] = []
                            else:
                                example_response[prop_name] = ''

                if not example_response:
                    example_response = {'code': 0, 'msg': 'success', 'data': {}}

                lines.append(json.dumps(example_response, ensure_ascii=False, indent=2))
                lines.append("```")
                lines.append("")

                # ===== v2.4.0 新增：错误码响应段 =====
                # 渲染除 200 外的所有状态码（含 4xx/5xx），让前端/测试看到完整错误响应
                error_codes = [code for code in responses.keys() if str(code) != '200']
                if error_codes:
                    # 按状态码顺序排序
                    error_codes.sort()
                    lines.append("**错误响应**:")
                    lines.append("")

                    for err_code in error_codes:
                        err_resp = responses[err_code]
                        if not isinstance(err_resp, dict):
                            continue

                        err_desc = err_resp.get('description', '')
                        lines.append(f"- `{err_code}`: {err_desc}")

                        # 错误码的 example 优先
                        err_example = err_resp.get('examples', {}).get('application/json')
                        if err_example:
                            lines.append("")
                            lines.append("  ```json")
                            lines.append("  " + json.dumps(err_example, ensure_ascii=False, indent=2).replace('\n', '\n  '))
                            lines.append("  ```")
                        else:
                            # 没有 example → 至少给一个最简示意
                            err_default = {'code': int(err_code) if str(err_code).isdigit() else 500, 'msg': err_desc or 'error'}
                            lines.append("")
                            lines.append("  ```json")
                            lines.append("  " + json.dumps(err_default, ensure_ascii=False, indent=2))
                            lines.append("  ```")
                    lines.append("")

            lines.append("---\n")

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def find_project_root(start_dir=None):
    """向上查找包含 apps/__init__.py 的项目根目录

    策略：从 start_dir 出发，逐级向上查找，找到第一个包含 apps/ 的目录即返回
    """
    current = start_dir or os.getcwd()
    while True:
        if os.path.isdir(os.path.join(current, 'apps')):
            return current
        parent = os.path.dirname(current)
        if parent == current:  # 已到根目录
            return None
        current = parent


def main():
    """主入口：解析参数 → 加载 spec → 导出文档

    支持两种模式：
    1. Flask 项目模式（默认）：自动加载 Flask app，从 /apispec_1.json 拉 spec
    2. spec.json 直输入模式（v2.4.0 新增）：--spec 参数直接传入 swagger_spec.json（适用非 Flask 项目）
    """
    import argparse
    parser = argparse.ArgumentParser(description='一键导出 API 文档（JSON + Markdown）')
    parser.add_argument('--project', '-p', help='Flask 项目根目录（默认自动向上查找）')
    parser.add_argument('--spec', '-s', help='直接传入 swagger_spec.json 路径（适用 FastAPI/Spring Boot 等非 Flask 项目）')
    parser.add_argument('--output', '-o', help='输出目录（默认 <project>/docs/API文档/）')
    parser.add_argument('--openapi3', action='store_true', help='输入为 OpenAPI 3.0 格式（v2.4.0 新增，需装 openapi-spec-validator）')
    args = parser.parse_args()

    # 模式选择：spec 直传模式 vs Flask 加载模式
    if args.spec:
        # ============== 模式 1：spec.json 直传（非 Flask 项目） ==============
        spec_file = os.path.abspath(args.spec)
        if not os.path.isfile(spec_file):
            print(f"❌ 错误：spec 文件不存在：{spec_file}")
            sys.exit(1)

        print(f"📁 spec 文件: {spec_file}")

        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)

        # v2.4.0 增量支持 OpenAPI 3.0 转 Swagger 2.0（可选）
        if spec.get('swagger') != '2.0' and spec.get('openapi', '').startswith('3.'):
            if args.openapi3 or args.spec.endswith('openapi.json'):
                print("ℹ️  检测到 OpenAPI 3.0 格式，做最小字段映射（如未安装 openapi-spec-validator，部分字段可能丢失）")
                try:
                    from openapi_spec_validator import validate
                    validate(spec)
                except ImportError:
                    print("⚠️  提示：安装 openapi-spec-validator 可获得更准确校验（pip install openapi-spec-validator）")
                except Exception as e:
                    print(f"⚠️  spec 校验警告：{e}")
                # 简化映射：paths 不变；responses 直接使用 OpenAPI 3.0 子结构
                # 完整转换需要 apispec 或 prance，此处仅做基础兼容

        # 默认输出到 spec.json 同目录下的 docs/API文档/，或用户指定输出
        if args.output:
            output_dir = os.path.abspath(args.output)
        else:
            output_dir = os.path.join(os.path.dirname(spec_file), '..', 'docs', 'API文档')
        project_root = os.path.dirname(spec_file)
    else:
        # ============== 模式 2：Flask 项目模式（默认，原有逻辑） ==============
        # 1. 解析项目根目录
        if args.project:
            project_root = os.path.abspath(args.project)
            if not os.path.isdir(os.path.join(project_root, 'apps')):
                print(f"❌ 错误：{project_root} 不包含 apps/ 目录")
                sys.exit(1)
        else:
            project_root = find_project_root()
            if not project_root:
                print("❌ 错误：未找到 Flask 项目（向上查找均无 apps/ 目录）")
                print("   请使用 --project 指定项目根目录")
                sys.exit(1)

        print(f"📁 项目根目录: {project_root}")

        # 2. 加载 Flask 应用
        sys.path.insert(0, project_root)
        try:
            from apps import create_app
        except ImportError as e:
            print(f"❌ 错误：无法导入 apps 模块: {e}")
            print("   请确认项目结构符合 Flask后端规范.md 第 1 章")
            sys.exit(1)

        app = create_app()
        # 触发 register_swagger 内部的 protect_swagger 钩子动态跳过 Basic Auth
        # （详见 Flask后端规范.md 第 11.1 节）；否则 test_client 拉 /apispec_1.json 会被 401 拦掉
        app.config['TESTING'] = True

        # 3. 通过 test_client 拉取 swagger spec
        with app.test_client() as client:
            response = client.get('/apispec_1.json')
            if response.status_code != 200:
                print(f"❌ 导出失败：HTTP {response.status_code}")
                print("   请检查 Flasgger 是否正确注册（详见 Flask后端规范.md 第 11 章）")
                sys.exit(1)

            spec = response.get_json()

        # 4. 输出目录
        output_dir = args.output or os.path.join(project_root, 'docs', 'API文档')

    # ============== 公共输出逻辑 ==============
    os.makedirs(output_dir, exist_ok=True)

    json_file = os.path.join(output_dir, 'swagger_spec.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON 规范: {json_file}")

    login_path, _ = find_auth_paths(spec)
    md_file = os.path.join(output_dir, 'API文档.md')
    json_to_markdown(spec, md_file, login_path)
    print(f"✅ Markdown:  {md_file}")

    # 5. 统计
    path_count = len(spec.get('paths', {}))
    method_count = sum(
        len([m for m in methods if m.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']])
        for methods in spec.get('paths', {}).values()
    )
    print(f"\n📊 共导出 {path_count} 个路径，{method_count} 个接口")
    print(f"💡 提示：dev 环境可在 http://localhost:{{端口}}/apidocs/ 查看交互式文档")


if __name__ == '__main__':
    main()
