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
# 兼容 Windows 绝对路径（D:\...）和 Unix 绝对路径（/...）
# 提取路径中 mcpowers/ 之后的部分作为相对路径
# 例：D:\document\my\workspace\mcpowers\mcpowers\SKILL.md → mcpowers/SKILL.md
#     /home/user/mcpowers/hooks/pre-bash-guard.sh → hooks/pre-bash-guard.sh

# 把反斜杠转成正斜杠（Windows 兼容）
NORMALIZED=$(echo "$FILE_PATH" | tr '\\' '/')

# 尝试提取 mcpowers/ 之后的部分
# 关键：用 sed 只匹配最后一次出现的 mcpowers/（避免贪婪匹配）
# 路径 D:\...\mcpowers\mcpowers\SKILL.md 应提取为 mcpowers/SKILL.md（不是 SKILL.md）
REL_PATH=""
if echo "$NORMALIZED" | grep -q 'mcpowers/'; then
    # 用 sed 反向引用，匹配最后一个 mcpowers/
    REL_PATH=$(echo "$NORMALIZED" | sed 's|.*\(mcpowers/[^}]*\).*|\1|' 2>/dev/null || true)
    # 清理 JSON 残留（如果 file_path 后面有 "}} 等）
    REL_PATH=$(echo "$REL_PATH" | sed 's|["'"'"'}].*||' 2>/dev/null || true)
fi

# 如果没匹配到 mcpowers/，用原路径（说明路径不在仓库内，放行）
if [ -z "$REL_PATH" ]; then
    exit 0
fi

# ============== 受保护路径检查 ==============
PROTECTED_PREFIXES=(
    "mcpowers-shared/"
    "mcpowers/"
    "hooks/"
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
   原因: 命中受保护目录白名单（mcpowers-shared/、mcpowers/、hooks/）

[确认] 继续操作前请先向用户报告：
   1. 修改影响范围（哪些技能/规范会受影响）
   2. 是否已获得用户明确同意
   3. 是否需要先 Read 相关 SKILL.md / 规范文件

按 Y 继续，按 N 取消。
EOF

# exit 2 = Claude Code PreToolUse 约定的"拒绝"退出码
# Claude Code CLI 会自动弹 confirm UI，无需脚本内交互
exit 2
