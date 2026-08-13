#!/usr/bin/env bash
# mcpowers PreToolUse (Write|Edit|MultiEdit) hook — bash wrapper
# v2.29.0+：doc-sync 物理门禁（path/route/env 三类检查）
#
# 设计动机：
#   v2.29.0+ 集中纪律：装好 mcpowers 自动支持，**不向用户项目注入任何文件**，
#   效果靠 hook 物理拦截保证（替代 v2.9.0 引入的 doc-sync-install 技能 [已废弃]）。
#
# 工作流：
#   1. 从 stdin 读 Claude Code 传入的 JSON，提取 file_path
#   2. 快速过滤：只对可能影响 doc 同步的文件路径触发
#      （README.md / app/*.py / src/router/*.ts / scripts/*.sh / requirements.txt / package.json）
#   3. 调 ${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/scripts/doc-sync-check.sh
#   4. helper 失败 → 退出码透传（exit 2 = 触发 Claude Code confirm UI）
#
# 退出码：
#   0 = 放行 / 检查通过
#   2 = 检测到不一致（Claude Code confirm UI 弹窗询问用户）

set -e

# 1. 探测可用 python（用于解析 stdin JSON；Windows 默认 python）
PY=""
for cand in python python3 py; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
            PY="$cand"
            break
        fi
    fi
done

# 读 stdin（Claude Code 传入的 JSON 包含 tool_input.file_path / toolInput.filePath）
STDIN_DATA="$(cat)"

if [ -z "$STDIN_DATA" ]; then
    exit 0
fi

# 2. 提取 file_path
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
    # 无 python → 用 grep 暴力提取（兜底，可能不精确）
    FILE_PATH=$(echo "$STDIN_DATA" | grep -oE '"file[Pp]ath"\s*:\s*"[^"]+"' | head -1 | sed 's/.*: *"//;s/"$//' || echo "")
fi

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# 3. 快速过滤：只对可能影响 doc 同步的文件触发
#    命中模式：README / app 路由 / src/router / scripts / requirements / package.json
case "$FILE_PATH" in
    *README.md|*readme.md|*README*)
        ;;  # README 修改一定影响 path_in_doc
    */app/*.py|*/api/*.py|*/routes/*.py|*/views/*.py)
        ;;  # 后端路由
    */src/router/*.ts|*/src/api/*.ts|*/src/router/*.js|*/src/api/*.js)
        ;;  # 前端路由
    */crawlers/*.py|*/spiders/*.py)
        ;;  # 爬虫 entry
    */scripts/*.sh|*/scripts/*.py|*/bin/*)
        ;;  # 脚本路径
    */requirements.txt|*/package.json)
        ;;  # 依赖清单
    *)
        exit 0  # 不涉及 doc-sync → 放行
        ;;
esac

# 4. 调集中 helper
HELPER="${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/scripts/doc-sync-check.sh"
if [ ! -f "$HELPER" ]; then
    # helper 不存在（开发期/卸载期）→ 放行，不阻断
    exit 0
fi

# 传 file_path 给 helper；helper 在 Claude Code 当前目录（用户项目根）跑
exec bash "$HELPER" --file-path="$FILE_PATH"