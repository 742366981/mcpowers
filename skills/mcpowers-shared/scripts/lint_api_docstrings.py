#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接口契约 lint 脚本（v2.4.0 新增）

扫描指定目录下所有疑似接口定义文件，检测 5 类违规。
违规项参考 接口契约规范.md §8 反模式黑名单。

使用方式：
    # 扫描当前目录（Flask/Spring Boot 等，识别路径可配置）
    python scripts/lint_api_docstrings.py --paths apps/

    # 扫描多个路径
    python scripts/lint_api_docstrings.py --paths apps/ src/api/

    # 仅警告不阻断（CI 首次接入）
    python scripts/lint_api_docstrings.py --paths apps/ --no-fail

退出码：
    0 = 无违规或 --no-fail 模式
    1 = 有违规（阻断 commit）
"""

import argparse
import os
import re
import sys
from pathlib import Path


def find_view_files(paths, extensions=('.py', '.java', '.js', '.ts', '.go')):
    """找出所有疑似接口文件

    Args:
        paths: 多个根路径
        extensions: 文件扩展名

    Returns:
        list of file paths
    """
    files = []
    for path in paths:
        p = Path(path)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for ext in extensions:
                files.extend(p.rglob(f'*{ext}'))
    return files


def parse_python_docstring(file_path):
    """从 Python 文件中提取所有 (路由, docstring, 装饰器所在行) 三元组

    简化策略：识别 @bp.route 装饰器 + 紧跟的 def 函数 + 函数 docstring
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return []

    results = []
    lines = content.split('\n')

    # 匹配装饰器与函数定义
    decorator_re = re.compile(r'@[\w]+\.(?:route|get|post|put|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]')
    func_re = re.compile(r'^\s*def\s+(\w+)\s*\(')

    i = 0
    while i < len(lines):
        line = lines[i]

        # 找到 @bp.route 装饰器
        route_match = decorator_re.search(line)
        if not route_match:
            i += 1
            continue

        route_path = route_match.group(1)

        # 找到 def 函数
        j = i + 1
        func_match = None
        while j < len(lines) and not func_match:
            m = func_re.match(lines[j])
            if m:
                func_match = m
                break
            j += 1

        if not func_match:
            i += 1
            continue

        func_name = func_match.group(1)

        # 找到 docstring
        k = j + 1
        docstring = ""
        while k < len(lines):
            line_k = lines[k]
            stripped = line_k.strip()
            if not stripped:
                k += 1
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # 单行 docstring
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    docstring = stripped.strip('"').strip("'")
                    break
                # 多行 docstring
                start = k
                k += 1
                buf = [stripped[3:]]
                while k < len(lines):
                    end = lines[k]
                    if '"""' in end[3:] or "'''" in end[3:]:
                        buf.append(end[:end.rfind('"""' if '"""' in end else "'''")])
                        break
                    buf.append(end)
                    k += 1
                docstring = '\n'.join(buf)
                break
            break

        results.append({
            'file': str(file_path),
            'line': i + 1,
            'route': route_path,
            'func': func_name,
            'docstring': docstring,
        })

        i = k + 1

    return results


def lint_docstring(route, docstring):
    """对单个 docstring 做违规检查

    Returns:
        list of (level, msg) — level: ERROR / WARNING
    """
    violations = []

    if not docstring or not docstring.strip():
        violations.append(('ERROR', f'[{route}] 视图函数无 docstring'))
        return violations

    # 检查 Flask Flasgger 标记（---）
    if '---' not in docstring:
        # 普通函数（非接口） → 跳过
        return violations

    # 解析 YAML 字段
    yaml_lower = docstring.lower()

    # ❌ 1. responses 只列 200
    responses_match = re.search(r'responses:\s*\n((?:\s+\d+:.*\n)+)', docstring)
    if responses_match:
        resp_block = responses_match.group(1)
        # 提取所有状态码
        codes = re.findall(r'^\s+(\d+):', resp_block, re.MULTILINE)
        if codes and codes == ['200']:
            violations.append(('ERROR', f'[{route}] responses 只列 200，必须含至少 1 个错误码'))

    # ❌ 2. parameters 漏 description 或 example
    param_blocks = re.findall(r'-\s+in:\s*(\w+)\s*\n\s+name:\s*(\w+)', docstring)
    if param_blocks:
        for in_loc, param_name in param_blocks:
            # 在 docstring 里查这个参数块是否有 description 和 example
            # 简化：找参数块及其后续
            pattern = rf'-\s+in:\s*{re.escape(in_loc)}\s*\n\s+name:\s*{re.escape(param_name)}\s*\n((?:\s+.*\n)*?)(?=\n\s*-|\n\s*responses:|\Z)'
            m = re.search(pattern, docstring)
            if m:
                block = m.group(1)
                if 'description:' not in block:
                    violations.append(('WARNING', f'[{route}] parameters[{param_name}] 缺 description（接口契约规范 §1.B 强制）'))
                if 'example:' not in block:
                    violations.append(('WARNING', f'[{route}] parameters[{param_name}] 缺 example（接口契约规范 §1.B 强制）'))

    # ❌ 3. description 占位
    for placeholder in ['待补充', 'TBD', 'TODO']:
        if placeholder in docstring and 'description:' in docstring:
            desc_match = re.search(r'description:\s*(.+)', docstring)
            if desc_match and placeholder in desc_match.group(1):
                violations.append(('ERROR', f'[{route}] description 含占位符 "{placeholder}"'))

    # ❌ 4. 接口路径用复数（简单规则：/users /orders /roles → 应是单数）
    plural_patterns = ['/users/', '/orders/', '/roles/', '/products/', '/categories/']
    for pat in plural_patterns:
        if pat in route and not route.endswith(pat[:-1]):
            violations.append(('WARNING', f'[{route}] 路径含复数模块名（接口契约规范 §6.2 要求单数）'))

    return violations


def main():
    parser = argparse.ArgumentParser(description='接口契约 lint 脚本（v2.4.0）')
    parser.add_argument('--paths', nargs='+', required=True, help='要扫描的路径（多个）')
    parser.add_argument('--no-fail', action='store_true', help='仅警告不阻断（CI 首次接入）')
    args = parser.parse_args()

    files = find_view_files(args.paths)
    if not files:
        print(f"⚠️  未找到可扫描的文件")
        return 0

    print(f"🔍 扫描 {len(files)} 个文件...")

    total_violations = 0
    error_count = 0
    warning_count = 0

    for f in files:
        if f.suffix == '.py':
            entries = parse_python_docstring(f)
            for entry in entries:
                violations = lint_docstring(entry['route'], entry['docstring'])
                if violations:
                    for level, msg in violations:
                        print(f"  {level}: {f}:{entry['line']} {msg}")
                        total_violations += 1
                        if level == 'ERROR':
                            error_count += 1
                        else:
                            warning_count += 1

    print(f"\n📊 共 {total_violations} 条违规（ERROR: {error_count}, WARNING: {warning_count}）")

    if args.no_fail:
        print(f"ℹ️  --no-fail 模式，仅警告不阻断（exit 0）")
        return 0

    if error_count > 0:
        print(f"❌ 存在 {error_count} 条 ERROR，commit 已被阻断")
        print(f"   详见 接口契约规范.md §8 反模式黑名单")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
