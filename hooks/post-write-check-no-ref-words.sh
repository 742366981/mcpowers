#!/usr/bin/env bash
# mcpowers PostToolUse (Write|Edit|MultiEdit) 钩子 wrapper
# v4.3.0+：代码/配置/.md 零引用字眼软门禁（智能二分兜底扫描）
#
# 触发场景：AI 完成 Write/Edit/MultiEdit 后,无论 PreToolUse 是否拦截过,
#           这里都做一次兜底扫描,确保最终落盘的文件内容不含画蛇添足字眼.
#           例如:
#             - Edit 修改 .py 注释（PreToolUse Edit 无 content 跳过硬门禁）
#             - Write .md 文件（PreToolUse .md 走的是软门禁,这里是同源兜底）
#             - PreToolUse 拦截后 AI 修改再 Write（兜底二次校验）
#
# v4.3.0 重构动机:
#   原 post-write-check-doc-content.sh 仅覆盖 .md;重构后统一为 PostToolUse 兜底
#   调用 check_no_ref_words.py 智能二分判定,覆盖 .md + 代码/配置所有写入场景.
#
# 退出码:
#   - 0  = 始终放行（兜底软门禁,即使有违规也只是 stderr 提示不阻断）
#   - 1  = 检测器自身错误 → 放行

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/.." 2>/dev/null && pwd)}"
DETECTOR="$PLUGIN_ROOT/skills/mcpowers-shared/scripts/check_no_ref_words.py"

PY=""
for cand in python python3 py; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
            PY="$cand"
            break
        fi
    fi
done

if [ -z "$PY" ] || [ ! -f "$DETECTOR" ]; then
    exit 0    # 检测器不可用 → 放行（软门禁,不阻断）
fi

# 调用检测器,使用 WARNING 级别（软提示不阻断）
# 检测器自己从 stdin 解析 Claude Code PostToolUse JSON,提取 file_path + content
exec "$PY" "$DETECTOR" --level=WARNING