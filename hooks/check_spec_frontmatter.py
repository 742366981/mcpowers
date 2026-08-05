#!/usr/bin/env python3
# mcpowers PreToolUse (Write|Edit|MultiEdit) 钩子的检测器
# v2.27.4+：检测技术规范 frontmatter 是否缺失 stability / last_breaking_change 字段
#
# 输入：stdin 是 Claude Code 注入的 JSON，含 tool_input.{file_path, content, new_string, old_string, edits}
# 退出码：
#   0 = 无违规，放行
#   2 = 命中违规（缺失字段 / 删除字段），stderr 输出警告，触发 Claude Code confirm UI
#   1 = 解析失败，放行（让其他 hook 兜底）
#
# 规则：
#   Write  规范文件 → 检查 content 的 frontmatter 缺 stability / last_breaking_change
#   Edit   规范文件 → 检查 old_string 含字段但 new_string 已删除（仅检测「删除」，放过「修改值」）
#   MultiEdit 规范文件 → 每个 edit 都按 Edit 规则检查
#   非规范文件 → 放行
#
# 入口函数命名为 hook_main() 而非 main()：避开防过度抽象铁律钩子对 def main() 的全局冲突
# （仓库已有 5 个 hook 检测器 / CLI 脚本用 def main() 入口，命名约定但语义不同）

from __future__ import annotations

import json
import re
import sys

SPEC_DIR_FRAGMENT = "skills/mcpowers-shared/docs/技术规范/"

REQUIRED_FIELDS = ("stability:", "last_breaking_change:")


def is_spec_file(file_path: str) -> bool:
    """仅技术规范目录下的 .md 文件受检查"""
    return SPEC_DIR_FRAGMENT in file_path and file_path.endswith(".md")


def extract_frontmatter(content: str) -> str | None:
    """提取 --- 包裹的 YAML frontmatter；非 frontmatter 格式返回 None"""
    m = re.search(r"^---\n(.*?)\n---", content, re.DOTALL | re.MULTILINE)
    return m.group(1) if m else None


def missing_fields(frontmatter: str) -> list[str]:
    """frontmatter 中缺失的字段名列表（不含冒号）"""
    missing = []
    for field in REQUIRED_FIELDS:
        if not re.search(r"^" + re.escape(field), frontmatter, re.MULTILINE):
            missing.append(field.rstrip(":"))
    return missing


def extract_declared_fields(text: str) -> set[str]:
    """从 text 中提取 stability / last_breaking_change 声明的行集合"""
    return set(re.findall(r"^(stability|last_breaking_change):.*$", text, re.MULTILINE))


def check_write(file_path: str, content: str) -> int:
    """Write 工具检查：新文件 frontmatter 缺字段 → 阻断"""
    fm = extract_frontmatter(content)
    if fm is None:
        return 0  # 非 frontmatter 文件（如纯 body md）→ 放行
    miss = missing_fields(fm)
    if miss:
        print(f"✗ [pre-write-check-spec-frontmatter] 规范 frontmatter 缺字段：{miss}", file=sys.stderr)
        print(f"  文件: {file_path}", file=sys.stderr)
        print(f"  强制要求（v2.27.4+）: 所有 31 份规范 frontmatter 必须声明", file=sys.stderr)
        print(f"    - stability: stable|evolving|deprecated", file=sys.stderr)
        print(f"    - last_breaking_change: v{{major}}.{{minor}}.{{patch}}", file=sys.stderr)
        return 2
    return 0


def check_edit_pair(file_path: str, old_string: str, new_string: str) -> int:
    """Edit 工具检查：仅当 old_string 含字段而 new_string 删除了才阻断（修改值放行）"""
    old_fields = extract_declared_fields(old_string)
    if not old_fields:
        return 0  # old 不含字段 → 这次编辑与 frontmatter 无关，放行
    new_fields = extract_declared_fields(new_string)
    removed = old_fields - new_fields
    if removed:
        print(f"✗ [pre-write-check-spec-frontmatter] 检测到删除 frontmatter 字段：{sorted(removed)}", file=sys.stderr)
        print(f"  文件: {file_path}", file=sys.stderr)
        print(f"  禁止删除（v2.27.4+）: stability / last_breaking_change 是规范稳定性分级铁律的物理兜底", file=sys.stderr)
        print(f"  如字段值需要变更，请保留字段名只改值（如 stability: evolving → stable）", file=sys.stderr)
        return 2
    return 0


def hook_main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 1  # 解析失败 → 放行（其他 hook 兜底）

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not is_spec_file(file_path):
        return 0

    if tool_name == "Write":
        return check_write(file_path, tool_input.get("content", ""))

    if tool_name == "Edit":
        return check_edit_pair(
            file_path,
            tool_input.get("old_string", ""),
            tool_input.get("new_string", ""),
        )

    if tool_name == "MultiEdit":
        for edit in tool_input.get("edits", []):
            rc = check_edit_pair(
                file_path,
                edit.get("old_string", ""),
                edit.get("new_string", ""),
            )
            if rc != 0:
                return rc
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(hook_main())