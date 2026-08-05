#!/usr/bin/env bash
# mcpowers PreToolUse (Write|Edit|MultiEdit) 钩子 wrapper
# v2.27.0+：Python import 位置检测（防局部 import）
# 复用 pre-write-check-duplicate.sh 的薄 wrapper 模式：
#   - 探测 python 解释器
#   - 转发 stdin JSON 到 Python 检测器
#   - exit 0 = 放行，exit 2 = 触发 confirm UI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DETECTOR="$SCRIPT_DIR/check_python_import_placement.py"

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
    exit 0    # 检测器不可用 → 放行
fi

exec "$PY" "$DETECTOR"