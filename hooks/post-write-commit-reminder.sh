#!/usr/bin/env bash
# mcpowers PostToolUse hook — 改完即 commit 提醒
# 触发条件：Write/Edit/MultiEdit 工具被调用
# 行为：检查 git 暂存区，已暂存但未提交时提示
# 退出码 0 = 注入信息（不阻断）
#
# 设计：仅提醒不阻断，避免打断 AI 流程
# 触发条件：已暂存文件数 > 0 且未暂存修改数 = 0（开发完毕待 commit 状态）

set -e

# ============== 读取 stdin JSON ==============
INPUT="$(cat)"

# 提取 tool_name 字段
TOOL_NAME=""

if command -v jq >/dev/null 2>&1; then
    TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)
fi

if [ -z "$TOOL_NAME" ] && command -v python3 >/dev/null 2>&1; then
    TOOL_NAME=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_name', ''))
except Exception:
    pass
" 2>/dev/null || true)
fi

if [ -z "$TOOL_NAME" ] && command -v python >/dev/null 2>&1; then
    TOOL_NAME=$(printf '%s' "$INPUT" | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_name', ''))
except Exception:
    pass
" 2>/dev/null || true)
fi

if [ -z "$TOOL_NAME" ] && command -v node >/dev/null 2>&1; then
    TOOL_NAME=$(printf '%s' "$INPUT" | node -e "
let data = '';
process.stdin.on('data', c => data += c);
process.stdin.on('end', () => {
  try {
    const obj = JSON.parse(data);
    process.stdout.write(obj.tool_name || '');
  } catch (e) {}
});
" 2>/dev/null || true)
fi

# 兜底：grep
if [ -z "$TOOL_NAME" ]; then
    TOOL_NAME=$(printf '%s' "$INPUT" | grep -oE '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' || true)
fi

# 只对 Write/Edit/MultiEdit 触发
case "$TOOL_NAME" in
    Write|Edit|MultiEdit) ;;
    *) exit 0 ;;
esac

# ============== 检查 git 暂存区 ==============
# 必须先 cd 到 git 仓库根目录（hook 触发时 cwd 不一定是仓库根）
# PostToolUse 协议不提供 cwd，需从环境变量或 pwd 获取
WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# 切换到工作目录检查
cd "$WORK_DIR" 2>/dev/null || exit 0

# 不在 git 仓库 → 放行
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    exit 0
fi

# 检查暂存区和未暂存修改
STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
UNSTAGED=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')

# 仅在"已暂存 + 未暂存为空"时提醒（开发完毕待 commit）
if [ "$STAGED" -gt 0 ] && [ "$UNSTAGED" -eq 0 ]; then
    cat >&2 <<EOF
[mcpowers 铁律] 已修改 $STAGED 个文件且全部暂存，请立即 commit
   → 调 mcpowers-git-commit 或运行 git commit -m '<message>'
   → 代码和文档必须同 commit
EOF
fi

# ============== v2.4.0 接口变更提醒 ==============
# 检测本次 commit 是否改了 Flask 视图函数/Java Controller/Express route
# 如改了 → 提醒"必须同步更新 docstring 并重跑 export_docs.py"
# 仅提醒不阻断（尊重开发者主动权）

# 取出暂存区中的接口类文件
STAGED_VIEW_FILES=$(git diff --cached --name-only 2>/dev/null | grep -E "(views\.py|views/|\.java$|router\.(py|js|ts)$|controllers?/)" || true)

if [ -n "$STAGED_VIEW_FILES" ]; then
    VIEW_COUNT=$(echo "$STAGED_VIEW_FILES" | wc -l | tr -d ' ')

    # 检查是否同时改了 docs/API文档/（导出的文档）
    STAGED_API_DOCS=$(git diff --cached --name-only 2>/dev/null | grep -E "docs/API文档/" || true)

    if [ -z "$STAGED_API_DOCS" ]; then
        cat >&2 <<EOF

[mcpowers 接口契约提醒 v2.4.0] 检测到 $VIEW_COUNT 个接口文件改动，但暂存区未见 docs/API文档/ 变更：

EOF
        echo "$STAGED_VIEW_FILES" | head -5 | sed 's/^/   → /' >&2
        if [ "$VIEW_COUNT" -gt 5 ]; then
            echo "   ... 还有 $((VIEW_COUNT - 5)) 个文件" >&2
        fi
        cat >&2 <<EOF

   建议：
   1. 如修改了 docstring → 跑 python tools/export_docs.py 重导出 openapi.json + API文档.md
   2. 跑 bash scripts/check_api_docs_sync.sh 检查一致性
   3. 确认 docs/API文档/openapi.json 与 API文档.md 也加入本次 commit
EOF
    fi
fi

exit 0
