#!/usr/bin/env bash
# mcpowers PreToolUse (Write) hook
# Claude Code 每次执行 Write 前调用本脚本
# 输入：stdin 上是 JSON 字符串（含 tool_input.file_path 字段）
# 输出策略：
#   - 命中受保护路径 → stderr 写原因 + exit 2（阻断，触发 confirm UI）
#   - 未命中 → exit 0（放行）
#
# 保护范围：mcpowers-shared/、mcpowers/、hooks/ 三个核心目录
# 设计：仅 Write（不拦 Edit，避免路由器改一次触发 5 次）

set -e

# ============== 读取 stdin JSON ==============
INPUT="$(cat)"

# 提取 file_path 字段（兼容多种 JSON 解析方式）
FILE_PATH=""

# 优先用 jq
if command -v jq >/dev/null 2>&1; then
    FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty' 2>/dev/null || true)
fi

# 降级到 python3
if [ -z "$FILE_PATH" ] && command -v python3 >/dev/null 2>&1; then
    FILE_PATH=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except Exception:
    pass
" 2>/dev/null || true)
fi

# 降级到 python（Windows 默认 python 而非 python3）
if [ -z "$FILE_PATH" ] && command -v python >/dev/null 2>&1; then
    FILE_PATH=$(printf '%s' "$INPUT" | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except Exception:
    pass
" 2>/dev/null || true)
fi

# 降级到 node
if [ -z "$FILE_PATH" ] && command -v node >/dev/null 2>&1; then
    FILE_PATH=$(printf '%s' "$INPUT" | node -e "
let data = '';
process.stdin.on('data', c => data += c);
process.stdin.on('end', () => {
  try {
    const obj = JSON.parse(data);
    process.stdout.write(obj.tool_input?.file_path || '');
  } catch (e) {}
});
" 2>/dev/null || true)
fi

# 兜底：直接 grep
if [ -z "$FILE_PATH" ]; then
    FILE_PATH=$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' || true)
fi

# 提取不到 file_path → 放行
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# ============== 路径转换 ==============
# v2.0 修复：使用 CLAUDE_PLUGIN_ROOT（插件系统自动注入）计算仓库内相对路径
# 避免 sed 贪婪匹配错误（如把 skills/mcpowers/foo.md 误提取为 mcpowers/foo.md）
# 兼容两种 CLAUDE_PLUGIN_ROOT 形式：
#   - POSIX: /d/document/my/workspace/mcpowers
#   - Windows: D:/document/my/workspace/mcpowers

REL_PATH=""

# 把 file_path 转成正斜杠
FILE_NORM=$(echo "$FILE_PATH" | tr '\\' '/')

if [ -n "$CLAUDE_PLUGIN_ROOT" ]; then
    # 准备三种可能的插件根形式
    PLUGIN_ROOT_NORM=$(echo "$CLAUDE_PLUGIN_ROOT" | tr '\\' '/')
    PLUGIN_ROOT_WIN=""
    if command -v cygpath >/dev/null 2>&1; then
        PLUGIN_ROOT_WIN=$(cygpath -w "$CLAUDE_PLUGIN_ROOT" 2>/dev/null | tr '\\' '/')
    fi

    # 依次尝试 POSIX 前缀、Windows 前缀
    for prefix in "$PLUGIN_ROOT_NORM" "$PLUGIN_ROOT_WIN"; do
        if [ -n "$prefix" ] && [[ "$FILE_NORM" == "${prefix}/"* ]]; then
            REL_PATH="${FILE_NORM#${prefix}/}"
            break
        fi
    done
fi

# 兜底：旧逻辑（用 sed 找最后一个 mcpowers/），仅在 CLAUDE_PLUGIN_ROOT 不可用时
if [ -z "$REL_PATH" ] && echo "$FILE_NORM" | grep -q 'mcpowers/'; then
    REL_PATH=$(echo "$FILE_NORM" | sed 's|.*\(mcpowers/[^}]*\).*|\1|' 2>/dev/null || true)
    REL_PATH=$(echo "$REL_PATH" | sed 's|["'"'"'}].*||' 2>/dev/null || true)
fi

# 如果没匹配到插件根或 mcpowers/，说明路径不在仓库内，放行
if [ -z "$REL_PATH" ]; then
    exit 0
fi

# ============== 受保护路径检查 ==============
# v2.0（插件市场格式）：白名单改为新结构
#   - skills/mcpowers/         （路由器，原 mcpowers/）
#   - skills/mcpowers-shared/  （规范库，原 mcpowers-shared/）
#   - hooks/                   （hooks 资产）
#   - .claude-plugin/          （插件元数据，必须保护）
PROTECTED_PREFIXES=(
    "skills/mcpowers/"
    "skills/mcpowers-shared/"
    "hooks/"
    ".claude-plugin/"
)

PROTECTED=false
for prefix in "${PROTECTED_PREFIXES[@]}"; do
    if [[ "$REL_PATH" == "$prefix"* ]]; then
        PROTECTED=true
        break
    fi
done

# 未命中受保护路径 → 放行
if [ "$PROTECTED" = false ]; then
    exit 0
fi

# ============== 命中 → 阻断确认 ==============
cat >&2 <<EOF
[mcpowers 铁律] 检测到修改核心资产：
   路径: $REL_PATH
   原因: 命中受保护目录白名单（skills/mcpowers/、skills/mcpowers-shared/、hooks/、.claude-plugin/）

[确认] 继续操作前请先向用户报告：
   1. 修改影响范围（哪些技能/规范会受影响）
   2. 是否已获得用户明确同意
   3. 是否需要先 Read 相关 SKILL.md / 规范文件

按 Y 继续，按 N 取消。
EOF

# exit 2 = Claude Code PreToolUse 约定的"拒绝"退出码
# Claude Code CLI 会自动弹 confirm UI，无需脚本内交互
exit 2
