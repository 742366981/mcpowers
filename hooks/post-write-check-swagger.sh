#!/usr/bin/env bash
# mcpowers PostToolUse (Write|Edit|MultiEdit) swagger 接口契约兜底钩子（v4.5.2+）
#
# 为什么需要 PostToolUse：
#   PreToolUse swagger 钩子从磁盘读 file_path —— Write 模式时新文件还没落盘，
#   Edit/MultiEdit 模式时读到的是旧文件。用户在 Edit 模式新增 @bp.route 但没写
#   docstring → PreToolUse 钩子看到旧文件里没这个函数 → 静默放行（这是用户
#   报告的「api 规范没生效」的根因之一）。
#
# 设计：
#   - PostToolUse 时文件已写入磁盘，磁盘读到最新内容（含本轮 Edit 引入的新函数）
#   - 命中违规 → exit 2 → Claude Code 把 stderr 喂回 Claude 自动修正（强反馈）
#   - 严格语义与 PreToolUse 一致（同一 helper、同一字段清单）
#   - 仅兜底 PreToolUse 漏掉的情况；PreToolUse 不再重复实现 Edit 内容感知
#
# 退出码：
#   0 = 通过 / 无违规 / 非接口文件 / 项目未装 swagger
#   2 = 命中契约违规（stderr 反馈给 Claude 自动修正；不弹 confirm UI）

set -e

# ---------- 1. 解析 stdin JSON 拿 file_path ----------
PY=""
for cand in python python3 py; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
        PY="$cand"
        break
    fi
done

STDIN_DATA="$(cat)"
if [ -z "$STDIN_DATA" ]; then
    exit 0
fi

if [ -n "$PY" ]; then
    FILE_PATH=$(echo "$STDIN_DATA" | "$PY" -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    ti = d.get('tool_input', {})
    print(ti.get('file_path') or ti.get('filePath') or '')
except Exception:
    print('')
" 2>/dev/null || echo "")
else
    FILE_PATH=$(echo "$STDIN_DATA" | grep -oE '"file[Pp]ath"\s*:\s*"[^"]+"' | head -1 | sed 's/.*: *"//;s/"$//' || echo "")
fi

# ---------- 2. 快速过滤：只对接口文件触发（与 PreToolUse 同模式） ----------
if [ -z "$FILE_PATH" ] || ! echo "$FILE_PATH" | grep -qE "(views\.py|/views/|router/|(router\.(py|js|ts))|controllers?/|/api/|/routes/|/handlers/|/endpoints/|urls\.py|/resources/|/blueprints/)"; then
    exit 0
fi

# ---------- 3. 文件必须已落盘（PostToolUse 时应已写入；若不存在即视为异常场景放行） ----------
if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# ---------- 4. 调集中 helper（与 PreToolUse 同一入口，保持 lint 行为一致） ----------
HELPER="${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/scripts/swagger-contract-check.sh"
if [ ! -f "$HELPER" ]; then
    # helper 缺失（开发期/卸载期）→ 放行，不阻断
    exit 0
fi

LINT_EXIT=0
bash "$HELPER" --file-path="$FILE_PATH" 2>&1 || LINT_EXIT=$?

# ---------- 5. 仅在违规时补一段引导文案（告诉 Claude 是 PostToolUse 兜底命中） ----------
if [ "$LINT_EXIT" = "2" ]; then
    cat >&2 <<'EOF'

   [mcpowers Swagger 契约门禁 v4.5.2 兜底 · PostToolUse]
   → PreToolUse 钩子未拦下此违规（典型：Edit 模式新增 @bp.route 时 PreToolUse 读到旧文件）
   → 文件已写入；本钩子通过 stderr 反馈违规清单，请补齐 5 字段契约或回退此 Edit
   → 权威规范：mcpowers-shared/docs/技术规范/接口契约规范.md §1
   → 项目自定义字段清单：mcpowers-shared/docs/技术规范/Swagger字段契约.md §2
EOF
fi

# 透传 helper 的退出码
exit "$LINT_EXIT"