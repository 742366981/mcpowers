#!/usr/bin/env bash
# mcpowers 接口契约软提醒 hook（v2.4.0 新增，E-06）
#
# 触发时机：用户写 .py 接口文件时
# 行为：检测是否漏写 docstring，若漏写 → stderr 软提醒（exit 0，不阻断）
# 退出码：永远 0（软提醒不阻断，尊重开发者主动）
#
# 设计原则：
# - 只提醒，不阻断（避免打断 AI 流程）
# - 与 pre-write-confirm.sh 互不冲突（pre-write-confirm 只拦核心目录）

set -e

INPUT="$(cat)"
FILE_PATH=""

# 提取 file_path（兼容多种 JSON 解析方式）
if command -v jq >/dev/null 2>&1; then
    FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty' 2>/dev/null || true)
elif command -v python3 >/dev/null 2>&1; then
    FILE_PATH=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except Exception:
    pass
" 2>/dev/null || true)
elif command -v python >/dev/null 2>&1; then
    FILE_PATH=$(printf '%s' "$INPUT" | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except Exception:
    pass
" 2>/dev/null || true)
fi

# 非接口文件 → 放行
if [ -z "$FILE_PATH" ] || ! echo "$FILE_PATH" | grep -qE "(views\.py|/views/|router\.(py|js|ts)|controllers?/)"; then
    exit 0
fi

# 提示
cat >&2 <<EOF
[mcpowers 接口契约软提醒 v2.4.0] 检测到写接口类文件：

   $FILE_PATH

   提醒（如尚未写）：
   1. 先写 docstring 5 字段契约（tags / summary / description / parameters / responses）
   2. 详见 mcpowers-shared/docs/技术规范/接口契约规范.md §1
   3. Flask/Flasgger 项目参考 mcpowers-shared/docs/API文档/swagger_template.md 模板
   4. 写完跑 python tools/export_docs.py 导出 spec

   → 这是软提醒，不会阻断你的操作
   → 提交时会由 post-write-commit-reminder 强制检查
EOF

exit 0
