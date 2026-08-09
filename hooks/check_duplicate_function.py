#!/usr/bin/env python3
# mcpowers PreToolUse (Write|Edit|MultiEdit) 钩子的检测器
# v2.28.x：重复函数检测简化（核心原则：只有真 bug 才拦）
#
# 检测策略（v2.28.x 简化）：
#   - 同文件内重名 → block（Python 后者覆盖前者，是真 bug）
#   - 单行透传 wrapper（函数体仅一行 return <call>(...)）→ block（gold standard 二次包装信号）
#   - 跨文件同名（其他情况）→ 默认放行（Python import 是模块级作用域，跨文件同名不冲突）
#   - 豁免：CONVENTION_NAMES (main/hook_main) + DUNDER_NAMES (Python 协议方法) + 单下划线私有名
# 退出码：
#   0 = 无命中 block 候选，放行
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

# v2.27.5+ 入口命名惯例豁免：main() / hook_main() 是模块入口惯例，
# 不视为「可复用普通函数」，hook 不应误拦。
CONVENTION_NAMES = frozenset({'main', 'hook_main'})

# v2.28.x Python dunder 协议方法豁免：__init__ / __new__ / __repr__ 等是 Python
# 语言级协议，不是「可复用普通函数」。任何自定义类都必须重新实现这些 dunder，
# 重复检测不应覆盖它们（否则所有自定义 Exception / dataclass 都会被误判 block）。
DUNDER_NAMES = frozenset({
    # 构造 / 析构
    '__init__', '__new__', '__del__', '__init_subclass__', '__subclasshook__',
    # 字符串表示
    '__repr__', '__str__', '__format__', '__bytes__',
    # 比较 / 哈希
    '__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__', '__hash__', '__bool__',
    # 容器协议
    '__len__', '__length_hint__', '__getitem__', '__setitem__', '__delitem__',
    '__contains__', '__iter__', '__next__', '__reversed__',
    # 可调用 / 上下文
    '__call__', '__enter__', '__exit__', '__aenter__', '__aexit__',
    # 算术
    '__add__', '__radd__', '__sub__', '__rsub__',
    '__mul__', '__rmul__', '__truediv__', '__rtruediv__',
    '__floordiv__', '__rfloordiv__', '__mod__', '__rmod__',
    '__divmod__', '__rdivmod__', '__pow__', '__rpow__',
    '__lshift__', '__rlshift__', '__rshift__', '__rrshift__',
    '__and__', '__rand__', '__or__', '__ror__', '__xor__', '__rxor__',
    '__matmul__', '__rmatmul__',
    '__neg__', '__pos__', '__abs__', '__invert__',
    '__complex__', '__int__', '__float__', '__index__', '__round__', '__trunc__', '__floor__', '__ceil__',
    # 描述符 / 属性
    '__getattr__', '__getattribute__', '__setattr__', '__delattr__', '__dir__',
    '__get__', '__set__', '__delete__', '__set_name__',
    # pickle / copy
    '__reduce__', '__reduce_ex__', '__getstate__', '__setstate__', '__getnewargs__', '__getnewargs_ex__',
    '__copy__', '__deepcopy__', '__sizeof__',
    # 类型相关
    '__class_getitem__', '__instancecheck__', '__subclasscheck__',
    # 异步
    '__await__', '__aiter__', '__anext__',
    # dataclass
    '__post_init__',
    # 模块级常被作为属性的 dunder
    '__annotations__', '__doc__', '__module__', '__name__', '__qualname__',
    '__dict__', '__weakref__', '__all__', '__slots__', '__file__',
    '__path__', '__version__', '__author__', '__copyright__', '__license__',
})


def extract_function_names(source):
    """提取源码中所有顶层函数 / 方法定义的名字集合。

    仅匹配以 def/function/func/fn 关键字开头的定义行（含 async def）。
    跳过以单下划线开头的私有名（除非是 dunder）——私有函数名重名通常属于
    内部封装，hook 不应误拦。
    """
    if not source:
        return set()
    names = set()
    for m in ASYNC_DEF_RE.finditer(source):
        name = m.group(1)
        if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
            continue
        names.add(name)
    return names


def count_in_source(source, name):
    """统计源码中 `def name(` 出现的次数。

    用于同文件内重名检测：count >= 2 说明同一文件对同一函数名多次定义，
    Python 解释器只会保留最后一个，前面的定义被静默覆盖——这是真 bug，必须 block。
    """
    if not source:
        return 0
    regex = re.compile(
        r'(?:async\s+)?(?:def|function|func|fn)\s+' + re.escape(name) + r'\s*\('
    )
    return len(regex.findall(source))


def is_one_line_wrapper(source, name):
    """判断新函数是否为单行透传 wrapper（gold standard 二次包装信号）。

    特征：函数体只有 1 行有效代码（不算 docstring / 空行 / 注释），
    且该行是 `return <其他函数名>(...)` 或 `<其他函数名>(...)`。

    命中规则：
      - 函数体有效代码行 ≤ 2 行
      - 没有 if / for / while / with / try / assert / yield / raise / global / nonlocal / lambda
      - 没有非 return 赋值
      - 唯一有效行匹配 `return <call>(...)` 或 `<call>(...)`

    命中 = 二次包装，无论文件位置（跨文件 / 同文件 / 任意命名空间）一律 block。
    """
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
    """从给定文件路径向上查找最近的 .git 目录，返回仓库根。

    若文件不在任何 git 仓库内，返回 None，hook 自动放行。
    """
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
    """判断给定仓库内相对路径是否为受保护资产（hook 自身 + 注入物）。

    受保护资产由 mcpowers 自身维护，hook 不应对其做重复函数检测
    （避免在修改规范 / SKILL 时触发自身误判）。
    """
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
    """返回 hook 扫描的源代码文件扩展名集合。

    仅扫描会被 AI 实际写入的业务代码类型，避免误扫 .md / .txt / .yaml 等文档。
    """
    return {'.py', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.go', '.java', '.kt', '.swift', '.rb', '.rs'}


def git_grep_duplicate(repo_root, rel_path, name):
    """在整个仓库范围内（排除新文件自身）查找同名函数定义。

    返回 [(rel_path, line_no, signature), ...] 最多 5 条命中。
    用于跨文件同名扫描——v2.28.x 起仅作为「单行透传 wrapper」block 时的辅助信息。
    """
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


def format_block_message(rel_path, duplicates):
    """构造触发 confirm UI 的 stderr 消息。

    duplicates 是 [(name, hits, reason), ...] 三元组：
      - reason = '同文件重名'：hits 为空，提示同一文件内多次定义
      - reason = '单行透传'：hits 为跨文件命中列表（最多 5 条），展示给用户参考
    """
    block = [
        '[mcpowers 铁律 · v2.28.x 重复检测简化] 检测到新增函数与已有定义冲突（建议复用 / 修复）：',
        '',
        f'   路径: {rel_path}',
        '   影响范围:',
    ]
    for name, hits, reason in duplicates:
        if reason == '同文件重名':
            block.append(f'   ❌ [阻断 · 同文件重名] 函数 `{name}` 在同一文件内多次定义（Python 后者覆盖前者，必为 bug）：')
        elif reason == '单行透传':
            block.append(f'   ❌ [阻断 · 单行透传] 函数 `{name}` 函数体仅一行 `return <已有函数>(...)`，是经典二次包装：')
        else:  # pragma: no cover —— 防御性兜底
            block.append(f'   ❌ [阻断 · {reason}] 函数 `{name}`：')
        if hits:
            for rel, ln, sig in hits:
                block.append(f'     {rel}:{ln}: {sig}')
        block.append('')

    block.extend([
        '[说明] 本检查对齐 `代码规范.md §6.1.1`：',
        '   - 同文件重名 → 真 bug（后者覆盖前者），必须修复',
        '   - 单行透传 wrapper → 真二次包装，建议直接调用底层或用装饰器（@retry / @lru_cache）',
        '   - 跨文件同名（非单行透传）→ 已默认放行（Python import 是模块级作用域）',
        '   - 例外场景（如 Python 故意重载、刻意重命名包装）→ 请在 Claude Code confirm UI 中选择是否继续',
        '',
        '请在 Claude Code confirm UI 中确认是否继续；取消则改为复用 / 合并。',
    ])
    return '\n'.join(block) + '\n'


def hook_main():
    """hook 主入口。

    读取 stdin 的 Claude Code JSON 工具调用，按 3 档规则判定是否 block：
      1. 同文件内重名 → block
      2. 跨文件同名 + 函数体单行透传 → block（gold standard）
      3. 其他跨文件同名 → 默认放行（不计入 duplicates）
    """
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
        if name in CONVENTION_NAMES or name in DUNDER_NAMES:
            continue
        # 1. 同文件内重名检测（真 bug，必拦）
        same_file_count = count_in_source(new_str, name)
        if same_file_count >= 2:
            duplicates.append((name, [], '同文件重名'))
            continue
        # 2. 跨文件扫描（辅助信息，仅供单行透传判定使用）
        cross_hits = git_grep_duplicate(repo_root, rel_path, name)
        if not cross_hits:
            continue
        # 3. 单行透传 wrapper 检测（gold standard 二次包装，必拦）
        if is_one_line_wrapper(new_str, name):
            duplicates.append((name, cross_hits, '单行透传'))
            continue
        # 4. 跨文件同名但不是单行透传 → 默认放行
        #    （Python import 是模块级作用域，跨文件同名不冲突）

    if not duplicates:
        return 0

    sys.stderr.write(format_block_message(rel_path, duplicates))
    return 2


if __name__ == '__main__':
    try:
        sys.exit(hook_main())
    except Exception as e:
        sys.stderr.write(f'[mcpowers 重复检测 hook 内部错误：{e}]\n')
        sys.exit(0)