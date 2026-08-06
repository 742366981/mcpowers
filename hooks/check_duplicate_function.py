#!/usr/bin/env python3
# mcpowers PreToolUse (Write|Edit|MultiEdit) 钩子的检测器
# v2.27.6+：重复函数检测启发式精细化（防过度抽象/二次包装）
#
# 检测策略（v2.27.6 启发式分级）：
#   - 命名空间启发式：新文件与命中点都在同一通用命名空间（utils/ helpers/ ...）
#     但不同目录 → 视为模块自治，降级 warn
#   - 签名启发式：新签名与命中签名参数列表不同 → 视为同名异义，降级 warn
#   - 绑定方法启发式：新是 def foo(self, ...) 命中点是模块函数（或反之）
#     → 视为绑定对象不同，降级 warn
#   - 单行透传启发式：函数体仅一行 `return <已有函数>(...)` → 最经典二次包装
#     → 强化阻断（即使触发上述任一降级也仍阻断）
# 退出码：
#   0 = 无命中（block/warn 均无），或仅命中 warn → 放行（warn 仅 stderr 写提示）
#   2 = 命中 block 候选 → stderr 写警告，触发 Claude Code confirm UI
#   1 = 解析失败，放行
#
# 输入：stdin 是 Claude Code 注入的 JSON，含 tool_input.{file_path, content, new_string, old_string}
#
# 入口函数命名为 hook_main() 而非 main()：避开防过度抽象铁律钩子对 def main()
# 的全局冲突（与 check_spec_frontmatter.py 的约定一致）。

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DEF_KEYWORDS = r'(?:def|function|func|fn)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
ASYNC_DEF_RE = re.compile(r'(?m)^\s*(?:async\s+)?' + DEF_KEYWORDS)

# v2.27.5+ 入口命名惯例。v2.27.6+ 进一步为 hook 自身的 hook_main() 约定提供豁免。
CONVENTION_NAMES = frozenset({'main', 'hook_main'})

NAMESPACE_SEGMENTS = frozenset({
    'utils', 'helpers', 'common', 'lib', 'libs', 'sdk',
    'adapters', 'parsers', 'serializers', 'handlers',
    'models', 'views', 'controllers', 'services',
    'repositories', 'factories', 'mixins', 'extensions',
    'plugins', 'tools', 'shared', 'internal',
})
SELF_NAMES = frozenset({'self', 'cls', '_self', '_cls', 'this', 'myself'})


def extract_function_names(source):
    if not source:
        return set()
    names = set()
    for m in ASYNC_DEF_RE.finditer(source):
        name = m.group(1)
        if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
            continue
        names.add(name)
    return names


def classify_namespace(rel_path):
    parts = rel_path.replace('\\', '/').split('/')
    for p in parts[:-1]:
        if p in NAMESPACE_SEGMENTS:
            return p
    return None


def is_cross_namespace(rel_new, rel_hit):
    ns_new = classify_namespace(rel_new)
    ns_hit = classify_namespace(rel_hit)
    if ns_new is None or ns_hit is None:
        return False
    return ns_new != ns_hit


def extract_signature(source, name):
    if not source:
        return None
    m = re.search(
        r'(?:async\s+)?(?:def|function|func|fn)\s+'
        + re.escape(name) + r'\s*\(([^)]*)\)',
        source,
    )
    return m.group(1).strip() if m else None


def normalize_params(params):
    if not params:
        return ()
    parts = []
    for raw in params.split(','):
        p = raw.strip()
        if not p:
            continue
        if '=' in p:
            p = p.split('=', 1)[0].strip()
        if ':' in p:
            p = p.split(':', 1)[0].strip()
        p = p.lstrip('*').strip()
        if p:
            parts.append(p)
    return tuple(parts)


def is_bound_method(params):
    norm = normalize_params(params)
    if not norm:
        return False
    return norm[0] in SELF_NAMES


def is_one_line_wrapper(source, name):
    if not source:
        return False
    lines = source.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if re.search(r'(?:async\s+)?(?:def|function|func|fn)\s+' + re.escape(name) + r'\s*\(', line):
            start_idx = i
            break
    if start_idx is None:
        return False
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        ln = lines[j]
        if not ln.strip():
            continue
        if ln[0] not in (' ', '\t'):
            if re.match(r'(?:async\s+)?(?:def|function|func|fn|class)\s+', ln):
                end_idx = j
                break
    body = lines[start_idx + 1:end_idx]
    meaningful = [ln.strip() for ln in body if ln.strip() and not ln.strip().startswith('#')]
    if not meaningful:
        return False
    if len(meaningful) == 1 and (
        meaningful[0].startswith('"""') or meaningful[0].startswith("'''")
    ):
        return False
    if len(meaningful) == 2:
        if (meaningful[0].startswith('"""') or meaningful[0].startswith("'''")) and \
           (meaningful[1].endswith('"""') or meaningful[1].endswith("'''")):
            return False
    control_kw = (
        'if ', 'for ', 'while ', 'with ', 'try:', 'assert ',
        'yield ', 'raise ', 'global ', 'nonlocal ', 'lambda ',
    )
    for code in meaningful:
        if any(code.startswith(k) for k in control_kw):
            return False
        if '=' in code and not code.lstrip().startswith('return '):
            return False
    if len(meaningful) > 2:
        return False
    for code in meaningful:
        if re.match(r'return\s+\w[\w.]*\s*\(', code) or re.match(r'\w[\w.]*\s*\(', code):
            continue
        return False
    return True


def find_repo_root(file_path):
    cur = file_path if file_path.is_absolute() else (Path.cwd() / file_path).resolve()
    cur = cur.parent
    while True:
        if (cur / '.git').exists():
            return cur
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def is_protected_path(rel_path):
    protected_prefixes = (
        'skills/mcpowers-shared/',
        'skills/mcpowers/SKILL.md',
        'skills/mcpowers/',
    )
    for p in protected_prefixes:
        if rel_path.startswith(p):
            return True
    if re.match(r'skills/mcpowers-[^/]+/SKILL\.md$', rel_path):
        return True
    return False


def code_file_exts():
    return {'.py', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.go', '.java', '.kt', '.swift', '.rb', '.rs'}


def git_grep_duplicate(repo_root, rel_path, name):
    code_exts = code_file_exts()
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', '.next', '.nuxt'}
    matches = []
    try:
        regex = re.compile(
            r'(^|[^A-Za-z0-9_])(?:def|function|func|fn)\s+' + re.escape(name) + r'\s*\('
        )
    except re.error:
        return []
    for root_dir, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for fname in files:
            fp = Path(root_dir) / fname
            try:
                rel = str(fp.relative_to(repo_root)).replace('\\', '/')
            except ValueError:
                continue
            if rel == rel_path:
                continue
            if Path(rel).suffix.lower() not in code_exts:
                continue
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                    for ln_no, line in enumerate(fh, start=1):
                        if regex.search(line):
                            sig = line.strip()
                            if len(sig) > 100:
                                sig = sig[:100] + '...'
                            matches.append((rel, ln_no, sig))
                            if len(matches) >= 5:
                                return matches
            except (OSError, UnicodeDecodeError):
                continue
    return matches


def decide_severity(rel_new, new_sig, is_wrapper, hits):
    if is_wrapper:
        return ('block', [])

    reasons = []
    for rel_hit, _ln, _sig in hits:
        if is_cross_namespace(rel_new, rel_hit):
            reasons.append('命名空间')
            break

    if new_sig is not None and hits:
        new_norm = normalize_params(new_sig)
        new_bound = is_bound_method(new_sig)
        for rel_hit, _ln, sig_line in hits:
            m = re.search(r'\(([^)]*)\)', sig_line)
            hit_sig = m.group(1) if m else None
            if hit_sig is None:
                continue
            hit_norm = normalize_params(hit_sig)
            hit_bound = is_bound_method(hit_sig)
            if new_norm != hit_norm:
                reasons.append('签名')
                break
            if new_bound != hit_bound:
                reasons.append('绑定方法')
                break

    if reasons:
        return ('warn', reasons)
    return ('block', [])


def format_block_message(rel_path, duplicates):
    block = [
        '[mcpowers 铁律 · v2.27.6 重复检测分级] 检测到新增函数与仓库已有定义冲突（建议复用）：',
        '',
        f'   路径: {rel_path}',
        '   影响范围:',
    ]
    for name, hits, _sev, _reason in duplicates:
        block.append(f'   ❌ [阻断] 函数 `{name}` 已被定义于：')
        for rel, ln, sig in hits:
            block.append(f'     {rel}:{ln}: {sig}')
        block.append('')

    block.extend([
        '[说明] 本检查对齐 `代码规范.md §6.1.1 复用优先于二次抽象`：',
        '   - 命中通常意味着：SDK / 通用模块已有等价实现，不必再写',
        '   - 例外场景（如双版本兼容、duck type 故意同名）→ 请在 Claude Code confirm UI 中选择是否继续',
        '',
        '请在 Claude Code confirm UI 中确认是否继续；取消则改为复用已有实现。',
    ])
    return '\n'.join(block) + '\n'


def format_warn_message(rel_path, duplicates_warn):
    lines = [
        '[mcpowers 提示 · v2.27.6 启发式降级] 命中函数同名但启发式判定为合法重名（已自动放行）：',
        '',
        f'   路径: {rel_path}',
    ]
    for name, hits, _sev, reasons in duplicates_warn:
        reason_str = '·'.join(reasons) if reasons else '启发式'
        lines.append(f'   ⚠ [降级 · 合法重名·{reason_str}] 函数 `{name}`：')
        for rel, ln, sig in hits:
            lines.append(f'     {rel}:{ln}: {sig}')
        lines.append('')
    lines.append('（已自动放行。如需强制复用/重命名，请手动调整。）')
    return '\n'.join(lines) + '\n'


def hook_main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        return 1

    tool_input = data.get('tool_input', {}) or {}
    file_path = tool_input.get('file_path', '') or ''
    new_str = tool_input.get('content', '') or tool_input.get('new_string', '') or ''
    old_str = tool_input.get('old_string', '') or ''

    if not file_path:
        return 0

    fp = Path(file_path)
    repo_root = find_repo_root(fp)
    if repo_root is None:
        return 0

    try:
        rel_path = str(fp.resolve().relative_to(repo_root)).replace('\\', '/')
    except ValueError:
        return 0

    if is_protected_path(rel_path):
        return 0

    ext = Path(rel_path).suffix.lower()
    if ext not in code_file_exts():
        return 0

    new_names = extract_function_names(new_str)
    if not new_names:
        return 0

    duplicates = []
    for name in sorted(new_names):
        if name in CONVENTION_NAMES:
            continue
        hits = git_grep_duplicate(repo_root, rel_path, name)
        if not hits:
            continue
        new_sig = extract_signature(new_str, name)
        is_wrapper = is_one_line_wrapper(new_str, name)
        severity, reasons = decide_severity(rel_path, new_sig, is_wrapper, hits)
        duplicates.append((name, hits, severity, reasons))

    if not duplicates:
        return 0

    blocks = [d for d in duplicates if d[2] == 'block']
    warns = [d for d in duplicates if d[2] == 'warn']

    if blocks:
        sys.stderr.write(format_block_message(rel_path, blocks))
        return 2
    if warns:
        sys.stderr.write(format_warn_message(rel_path, warns))
        return 0
    return 0


if __name__ == '__main__':
    try:
        sys.exit(hook_main())
    except Exception as e:
        sys.stderr.write(f'[mcpowers 重复检测 hook 内部错误：{e}]\n')
        sys.exit(0)
