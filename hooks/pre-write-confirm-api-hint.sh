#!/usr/bin/env bash
# mcpowers Swagger 接口契约硬门禁 hook(v2.31.0+ 改造自 v2.4.0 软提醒)
#
# 设计动机:
#   v2.4.0+ 是软提醒(exit 0,永不阻断),仅 stderr 提示 docstring 规范。
#   v2.31.0+ 升级为**真正硬门禁**——wrapper hook,把 stdin JSON 解析后转发到
#   ${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/scripts/swagger-contract-check.sh,
#   由其完成:栈探测 → 字段清单加载 → 单文件 lint → exit 0/2 透传。
#
# 触发时机:PreToolUse(Write|Edit|MultiEdit) 时 Claude Code 传入 stdin JSON(含 tool_input.file_path)
# 快速过滤:仅匹配接口文件(views.py / /views/ / router.{py,js,ts} 或 /router/ / /controllers/ / /api/ / /routes/ / /handlers/ / /endpoints/ / urls.py / /resources/ / /blueprints/)
#         其他文件 → exit 0(沿用 v2.4.0 行为)
#
# 退出码:
#   0 = 放行(非接口文件 / 项目未装 swagger / lint 通过)
#   2 = 检测到 5 字段契约违规(Claude Code confirm UI 弹窗询问用户)
#
# 与 v2.4.0 行为差异:
#   - 退出码由 exit 0 改为可能 exit 2(透传 lint 结果)
#   - 阻断提示文案由本脚本输出(集中 helper 内已含违规汇总,这里补一段铁律引导)

set -e

# 1. 探测可用 python(用于解析 stdin JSON;Windows 默认 python)
PY=""
for cand in python python3 py; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
            PY="$cand"
            break
        fi
    fi
done

# 2. 读 stdin(Claude Code 传入的 JSON 包含 tool_input.file_path / toolInput.filePath)
STDIN_DATA="$(cat)"

if [ -z "$STDIN_DATA" ]; then
    exit 0
fi

# 3. 提取 file_path
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
    # 降级 grep(兜底)
    FILE_PATH=$(echo "$STDIN_DATA" | grep -oE '"file[Pp]ath"\s*:\s*"[^"]+"' | head -1 | sed 's/.*: *"//;s/"$//' || echo "")
fi

# 4. 快速过滤:只对接口文件触发
if [ -z "$FILE_PATH" ] || ! echo "$FILE_PATH" | grep -qE "(views\.py|/views/|router/|(router\.(py|js|ts))|controllers?/|/api/|/routes/|/handlers/|/endpoints/|urls\.py|/resources/|/blueprints/)"; then
    exit 0
fi

# 5. 调集中 helper
HELPER="${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/scripts/swagger-contract-check.sh"
if [ ! -f "$HELPER" ]; then
    # helper 不存在(开发期/卸载期)→ 放行,不阻断
    exit 0
fi

# 6. 转发 file_path 给 helper,helper 内 exit 0/2 透传
LINT_EXIT=0
bash "$HELPER" --file-path="$FILE_PATH" 2>&1 || LINT_EXIT=$?

# 7. helper 已输出违规汇总(stderr),这里只在 exit 2 时补一段铁律引导
if [ "$LINT_EXIT" = "2" ]; then
    cat >&2 <<'EOF'

   [mcpowers Swagger 契约门禁 v2.31.0]
   → 这是硬门禁,confirm UI 选择"否"以阻断;选择"是"放行
   → 真正硬门禁在你的项目 CI;此处是"写完那一刻意识到漏写"的设计
   → 权威规范:mcpowers-shared/docs/技术规范/接口契约规范.md §1
   → 项目自定义字段清单:mcpowers-shared/docs/技术规范/Swagger字段契约.md §2
EOF
fi

exit "$LINT_EXIT"
