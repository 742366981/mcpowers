#!/usr/bin/env bash
# mcpowers PreToolUse (Write|Edit|MultiEdit) 钩子 wrapper
# v4.3.0+：代码/配置文件零引用字眼检测（智能二分硬门禁）
#
# 触发场景：AI 写入代码注释/配置时若含「参考《代码规范》§11.3」
#           「详见 utils/security.py」「按规范要求校验」等指向其他文档的字眼,
#           hook 调用 check_no_ref_words.py 智能二分判定:
#             - 命中外部权威 (RFC/PEP/W3C/OWASP/官方 URL) → 放行
#             - 命中内部规范名 / 项目内代码文件路径 → 阻断 (exit 2 → confirm UI)
#             - 命中「按规范要求」无外部前缀 → 阻断 (画蛇添足兜底)
#
# v4.3.0 设计动机:
#   v4.0.1 接口零引用 / v4.0.2 .md 零引用已覆盖,但代码注释/配置/yaml 文件
#   仍存在指向其他文档的字眼污染.本 hook 把保护面扩展到所有代码/配置写入场景.
#
# 覆盖范围:
#   - PreToolUse Write/Edit/MultiEdit
#   - .py / .sh / .js / .ts / .jsx / .tsx / .go / .java / .rs /
#     .yaml / .yml / .json / .ini / .toml / .conf
#   - .md 由 post-write-check-doc-content.sh 软门禁覆盖（v4.0.2+ 已就绪,v4.3.0 沿用）
#
# 退出码:
#   - 0  = 合规 / 检测器不可用 / 边界豁免
#   - 2  = 有 ERROR 级违规（confirm UI）
#   - 1  = 检测器自身错误（视为放行,避免破坏工作流）

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DETECTOR="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/.." 2>/dev/null && pwd)}/skills/mcpowers-shared/scripts/check_no_ref_words.py"

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
    exit 0    # 检测器不可用 → 放行（不破坏工作流）
fi

# 转发 stdin JSON 到 Python 检测器
# 检测器自己解析 JSON 提取 file_path + content
exec "$PY" "$DETECTOR" --level=ERROR