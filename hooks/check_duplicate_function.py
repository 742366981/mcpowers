#!/usr/bin/env python3
# mcpowers PreToolUse (Write|Edit|MultiEdit) 钩子的检测器
# v2.26.0+：检测新增函数是否与仓库已有函数重名（防过度抽象/二次包装）
#
# 输入：stdin 是 Claude Code 注入的 JSON，含 tool_input.{file_path, content, new_string, old_string}
# 退出码：
#   0 = 无重名，放行
#   2 = 命中重名，stderr 输出警告，触发 Claude Code confirm UI
#   1 = 解析失败，放行（让其他 hook 兜底）
#
# 设计要点（针对 Git Bash/Windows CRLF 兼容）：
#   - 全程 Python 处理 stdin bytes（含 Claude Code 注入的 JSON）
#   - 用 pathlib 探测仓库根（向上找 .git）
#   - 用 subprocess 跑 git grep 排除自身文件
#   - 最终输出走 sys.stderr.write + 退出码控制

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# 多语言函数定义关键字
DEF_KEYWORDS = r'(?:def|function|func|fn)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
ASYNC_DEF_RE = re.compile(
    r'(?m)^\s*(?:async\s+)?' + DEF_KEYWORDS
)


def extract_function_names(source: str) -> set[str]:
    """从源码文本中提取函数定义名。过滤私有（_ 前缀，__魔术__方法保留）。"""
    if not source:
        return set()
    names = set()
    for m in ASYNC_DEF_RE.finditer(source):
        name = m.group(1)
        if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
            # 单下划线前缀的私有辅助函数跳过；__魔术__保留
            continue
        names.add(name)
    return names


def find_repo_root(file_path: Path) -> Path | None:
    """沿 file_path 向上探测最近一层含 .git 目录的祖先。失败返回 None。"""
    cur = file_path if file_path.is_absolute() else (Path.cwd() / file_path).resolve()
    cur = cur.parent
    while True:
        if (cur / '.git').exists():
            return cur
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def is_protected_path(rel_path: str) -> bool:
    """mcpowers 自身仓库的规范/路由/SKILL.md 等不应被本 hook 打扰。"""
    protected_prefixes = (
        'skills/mcpowers-shared/',
        'skills/mcpowers/SKILL.md',
        'skills/mcpowers/',
    )
    for p in protected_prefixes:
        if rel_path.startswith(p):
            return True
    if rel_path == 'skills/mcpowers-' and False:
        # 双 SKILL.md 入口单独匹配（避免上方前缀吃掉 skills/mcpowers-feat/SKILL.md）
        pass
    # 各技能 SKILL.md
    if re.match(r'skills/mcpowers-[^/]+/SKILL\.md$', rel_path):
        return True
    return False


def code_file_exts() -> set[str]:
    return {'.py', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.go', '.java', '.kt', '.swift', '.rb', '.rs'}


def git_grep_duplicate(repo_root: Path, rel_path: str, name: str) -> list[str]:
    """在仓库内（除自身文件）找同名函数定义。返回命中的相对路径:行号 列表（最多 5 条）。

    不用 git grep（Windows 下 regex 兼容性差），改用 pathlib + 内置正则扫描代码文件：
      - 直接遍历仓库根，过滤扩展名（代码文件）
      - 跳过自身文件（rel_path）
      - 跳过 .git / __pycache__ / node_modules 等
      - 正则：def/function/func/fn + name + (
    """
    code_exts = code_file_exts()
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', '.next', '.nuxt'}
    matches: list[str] = []

    # 用 Python re 编译一次
    try:
        regex = re.compile(
            r'(^|[^A-Za-z0-9_])(?:def|function|func|fn)\s+' + re.escape(name) + r'\s*\('
        )
    except re.error:
        return []

    for root_dir, dirs, files in os.walk(repo_root):
        # in-place 过滤目录，跳过明显无关的
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for fname in files:
            fp = Path(root_dir) / fname
            # 用相对路径比对
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
                            matches.append(f'  {rel}:{ln_no}: {sig}')
                            if len(matches) >= 5:
                                return matches
            except (OSError, UnicodeDecodeError):
                continue
    return matches


def main() -> int:
    # 1. 读 stdin
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        return 1    # 解析失败放行

    tool_input = data.get('tool_input', {}) or {}
    file_path = tool_input.get('file_path', '') or ''
    new_str = tool_input.get('content', '') or tool_input.get('new_string', '') or ''
    old_str = tool_input.get('old_string', '') or ''

    if not file_path:
        return 0

    # 2. 探测仓库根
    fp = Path(file_path)
    repo_root = find_repo_root(fp)
    if repo_root is None:
        return 0    # 非 git 仓库 → 放行

    # 3. 计算仓库内相对路径
    try:
        rel_path = str(fp.resolve().relative_to(repo_root)).replace('\\', '/')
    except ValueError:
        return 0

    # 4. 白名单（mcpowers 自身规范/路由）
    if is_protected_path(rel_path):
        return 0

    # 5. 仅处理代码文件
    ext = Path(rel_path).suffix.lower()
    if ext not in code_file_exts():
        return 0

    # 6. 提取新增函数名
    new_names = extract_function_names(new_str)
    if not new_names:
        return 0

    # 7. 仓库内扫重名
    duplicates = []
    for name in sorted(new_names):
        hits = git_grep_duplicate(repo_root, rel_path, name)
        if hits:
            duplicates.append((name, hits))

    if not duplicates:
        return 0

    # 8. 输出警告 + exit 2
    block = [
        '[mcpowers 铁律 · v2.26.0+ 复用优先] 检测到新增函数与仓库已有定义重名：',
        '',
        f'   路径: {rel_path}',
        '   影响范围:',
    ]
    for name, hits in duplicates:
        block.append(f'   ❌ 函数 `{name}` 已被定义于：')
        block.extend(hits)
        block.append('')

    block.extend([
        '[说明] 本检查对齐 `代码规范.md §6.1.1 复用优先于二次抽象`：',
        '   - 命中重名通常意味着：SDK / 通用模块已有等价实现，不必再写',
        '   - 例外场景（如双版本兼容、duck type 故意同名）→ 用户在 confirm 中选 Y 继续',
        '',
        '按 Y 继续（确认仍需新增），按 N 取消（改为复用已有）。',
    ])
    sys.stderr.write('\n'.join(block))
    sys.stderr.write('\n')
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:    # 兜底：hook 自身出错不要阻断开发
        sys.stderr.write(f'[mcpowers 重复检测 hook 内部错误：{e}]\n')
        sys.exit(0)
