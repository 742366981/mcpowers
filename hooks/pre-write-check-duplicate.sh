#!/usr/bin/env bash
# mcpowers PreToolUse (Write|Edit|MultiEdit) hook — bash wrapper
# v2.26.0+：检测新增函数与仓库已有 def 重名（防过度抽象/二次包装）
#
# 设计：所有逻辑委托给同目录 check_duplicate_function.py，避免 Git Bash 下
# bash/python 字节交互的 CRLF / $'\x1e' / stdin 解析等兼容性陷阱。
# 本 shell 仅做：(1) 探测可用 python; (2) 透传 stdin; (3) 透传退出码

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DETECTOR="$SCRIPT_DIR/check_duplicate_function.py"

# 找可用 python（python 优先，Windows 默认；python3 在 WindowsApps 下是 stub）
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
    exit 0    # 检测器不可用 → 放行，不阻断
fi

# 透传 stdin 给 python 检测器
exec "$PY" "$DETECTOR"
