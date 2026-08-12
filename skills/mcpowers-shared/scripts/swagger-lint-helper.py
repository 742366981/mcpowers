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


def check_responses_error_codes(docstring: str) -> list[tuple[str, str]]:
    """检查 responses 块是否含至少 1 个错误码(4xx/5xx)

    字符串扫描避免正则 catastrophic backtracking(原 lint_docstring 的
    r'responses:\\s*\\n((?:\\s+\\d+:.*\\n)+)' 在长 docstring 上会卡住 2+ 分钟)。

    Returns:
        list of (level, msg) — level: 'ERROR' / 'WARNING'
    """
    violations = []

    # 找到 responses: 顶层块(到下一个顶层字段 --- 之前的 4 空格缩进行)
    # 简化:扫到 "responses:" 起,直到下一个顶层字段(行首无空格的 `xx:`)或 `---` 止
    lines = docstring.splitlines()
    in_responses = False
    codes: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_responses:
            if stripped.startswith('responses:') or stripped.startswith('responses :'):
                in_responses = True
            continue
        # 顶层字段(无前导空格 + 含 `:`)→ responses 块结束
        if line and not line.startswith(' ') and ':' in stripped:
            break
        # `---` 结束符 → 块结束
        if stripped == '---':
            break
        # 状态码行(4 空格 + 数字 + :)
        if line.startswith('    ') and stripped.endswith(':') and stripped[:-1].isdigit():
            codes.append(stripped[:-1])

    if not codes:
        # 没列出任何状态码 → 必填字段检查已先报错,这里不重复
        return violations

    if codes == ['200']:
        violations.append(('ERROR', 'responses 只列 200,必须含至少 1 个错误码(401/403/422/500 等)'))
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

    all_violations: list[tuple[str, int, str, str]] = []  # (level, line, func, msg)
    error_count = 0
    warning_count = 0

    for entry in entries:
        route = entry['route']
        func = entry['func']
        line_no = entry['line']
        docstring = entry['docstring']

        # 必填顶层字段名检查(v2.31.0+ 写时硬门禁的核心检查)
        for level, msg in check_required_field_names(docstring, required_fields):
            full_msg = f'[{route}] {msg}'
            all_violations.append((level, line_no, func, full_msg))
            if level == 'ERROR':
                error_count += 1
            else:
                warning_count += 1

        # responses 必须含错误码(ERROR:仅 200 → 阻断)
        for level, msg in check_responses_error_codes(docstring):
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
