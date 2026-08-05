#!/usr/bin/env python3
# mcpowers PreToolUse (Write|Edit|MultiEdit) 钩子的检测器
# v2.27.0+：检测 Python 文件中是否新增了函数/方法/类内部的 import（局部 import）
#
# 输入：stdin 是 Claude Code 注入的 JSON，含 tool_input.{file_path, content, new_string, old_string, edits}
# 退出码：
#   0 = 无新增违规，放行
#   2 = 命中新增违规，stderr 输出警告，触发 Claude Code confirm UI
#   1 = 解析失败，放行（让其他 hook 兜底）

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

LOCAL_SCOPE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _scope_label(scope):
    if isinstance(scope, ast.ClassDef):
        return 'class ' + scope.name
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = 'async def' if isinstance(scope, ast.AsyncFunctionDef) else 'def'
        return prefix + ' ' + scope.name
    return type(scope).__name__


def _import_text(node):
    if isinstance(node, ast.Import):
        return 'import ' + ', '.join(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        module = node.module or ''
        names = ', '.join(alias.name for alias in node.names)
        if node.level:
            module = '.' * node.level + module
        return 'from ' + module + ' import ' + names
    return ''


def _walk_with_ancestors(tree):
    results = []

    def walk(node, ancestors):
        # 先判断当前节点本身是否是 import
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            scope = None
            for s in reversed(ancestors):
                if isinstance(s, LOCAL_SCOPE_TYPES):
                    scope = s
                    break
            results.append((node, scope, ancestors))
            return  # import 节点无子语句，不再下钻

        # 进入新作用域（函数/类）
        new_ancestors = ancestors
        if isinstance(node, LOCAL_SCOPE_TYPES):
            new_ancestors = ancestors + [node]

        # 递归子节点（其他节点如 If/Try 不引入新作用域，保留 ancestors）
        for child in ast.iter_child_nodes(node):
            walk(child, new_ancestors)

    walk(tree, [])
    return results


def collect_local_imports(source):
    if not source or not source.strip():
        return []
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []

    violations = []
    for node, scope, _ancestors in _walk_with_ancestors(tree):
        if scope is None:
            continue
        violations.append({
            'lineno': getattr(node, 'lineno', 0),
            'scope': _scope_label(scope),
            'text': _import_text(node),
        })
    return violations


def _diff_local_imports(before, after):
    # 用 (scope, text) 二元组做集合去重——同一作用域内同一 import 文本视为同一项。
    # 行号变化（新增/删除上下文行）不应被误判为新增违规。
    before_keys = {(v['scope'], v['text']) for v in before}
    new_violations = []
    for v in after:
        key = (v['scope'], v['text'])
        if key not in before_keys:
            new_violations.append(v)
    return new_violations


def _read_existing_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def _rebuild_after_edit(old_source, old_string, new_string):
    if old_string == '':
        return new_string
    if old_string in old_source:
        return old_source.replace(old_string, new_string, 1)
    return None


def _rebuild_after_multi_edit(old_source, edits):
    current = old_source
    for edit in edits or []:
        old_string = edit.get('old_string', '')
        new_string = edit.get('new_string', '')
        if old_string == '':
            current = new_string
            continue
        if old_string not in current:
            return None
        current = current.replace(old_string, new_string, 1)
    return current


def _format_violation(rel_path, violation):
    return (
        '   - ' + rel_path + ':' + str(violation['lineno'])
        + ' in ' + violation['scope'] + ': ' + violation['text']
    )


main = lambda: None


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        return 1

    tool_input = data.get('tool_input', {}) or {}
    file_path = tool_input.get('file_path', '') or ''
    if not file_path:
        return 0

    fp = Path(file_path)
    if fp.suffix.lower() != '.py':
        return 0

    before_source = _read_existing_file(fp) or ''

    after_source = None
    is_write = False
    if 'content' in tool_input:
        # Write 工具：覆盖式操作，所有违规视为新增（避免既有遗留被掩盖）
        after_source = tool_input.get('content') or ''
        is_write = True
    elif 'edits' in tool_input:
        # MultiEdit 工具：增量编辑，仅 diff 新增违规
        after_source = _rebuild_after_multi_edit(before_source, tool_input.get('edits') or [])
    elif 'new_string' in tool_input:
        # Edit 工具：增量编辑，仅 diff 新增违规
        after_source = _rebuild_after_edit(
            before_source,
            tool_input.get('old_string', '') or '',
            tool_input.get('new_string', '') or '',
        )
    else:
        return 0

    if after_source is None:
        return 0

    before_violations = collect_local_imports(before_source) if before_source else []
    after_violations = collect_local_imports(after_source)

    if not after_violations:
        return 0

    if is_write or not before_source:
        # Write 工具是覆盖式：所有违规都视为新增
        # 全新文件：所有违规都视为新增
        new_violations = after_violations
    else:
        # Edit/MultiEdit：仅 diff 新增违规
        new_violations = _diff_local_imports(before_violations, after_violations)

    if not new_violations:
        return 0

    try:
        rel_path = str(fp.resolve()).replace('\\', '/')
    except (OSError, ValueError):
        rel_path = file_path

    block = [
        '[mcpowers 铁律 · v2.27.0+ Python import 位置] 检测到新增的局部 import：',
        '',
        '   路径: ' + rel_path,
        '   新增违规:',
    ]
    for v in new_violations[:20]:
        block.append(_format_violation(rel_path, v))
    if len(new_violations) > 20:
        block.append('   ... 另 ' + str(len(new_violations) - 20) + ' 条未列出')

    block.extend([
        '',
        '[说明] 对齐 `代码规范.md §Python import 位置规范`：',
        '   - 所有 import / from ... import 必须位于模块级导入区',
        '   - 函数、方法、类体、条件块、装饰器内部禁止局部 import',
        '   - 循环依赖或真正可选依赖可例外，必须写明原因并由用户确认',
        '',
        '按 Y 继续（确认本处局部 import 是必要例外），按 N 取消（改为模块级导入）。',
    ])
    sys.stderr.write('\n'.join(block))
    sys.stderr.write('\n')
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write('[mcpowers import 位置检测 hook 内部错误：' + str(e) + ']\n')
        sys.exit(0)
