#!/usr/bin/env bash
# mcpowers PreToolUse (Bash) hook
# Claude Code 每次执行 Bash 前调用本脚本
# 输入：stdin 上是 JSON 字符串（含 tool_input.command 字段）
# 输出策略：
#   - 匹配危险模式 → stderr 写原因 + exit 2（阻断）
#   - 白名单通过 → exit 0
#   - 正常命令 → exit 0

set -e

# ============== 读取 stdin JSON ==============
# Claude Code 把工具调用参数通过 stdin 传入
INPUT="$(cat)"

# 提取 command 字段（兼容多种 JSON 解析方式）
COMMAND=""

# 优先用 jq
if command -v jq >/dev/null 2>&1; then
    COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // .command // empty' 2>/dev/null || true)
fi

# 降级到 python3
if [ -z "$COMMAND" ] && command -v python3 >/dev/null 2>&1; then
    COMMAND=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except Exception:
    pass
" 2>/dev/null || true)
fi

# 降级到 node
if [ -z "$COMMAND" ] && command -v node >/dev/null 2>&1; then
    COMMAND=$(printf '%s' "$INPUT" | node -e "
let data = '';
process.stdin.on('data', c => data += c);
process.stdin.on('end', () => {
  try {
    const obj = JSON.parse(data);
    process.stdout.write(obj.tool_input?.command || '');
  } catch (e) {}
});
" 2>/dev/null || true)
fi

# 兜底：直接 grep
if [ -z "$COMMAND" ]; then
    COMMAND=$(printf '%s' "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' || true)
fi

# 提取不到命令 → 放行（让 Claude Code 自己的校验处理）
if [ -z "$COMMAND" ]; then
    exit 0
fi

# ============== 白名单检查（先于黑名单） ==============
# 已知安全的 rm -rf 模式（构建产物、依赖目录等）
SAFE_RM_PATTERNS=(
    'rm -rf node_modules'
    'rm -rf dist'
    'rm -rf build'
    'rm -rf .next'
    'rm -rf .nuxt'
    'rm -rf __pycache__'
    'rm -rf .cache'
    'rm -rf coverage'
    'rm -rf target'
    'rm -rf .pytest_cache'
    'rm -rf .mypy_cache'
    'rm -rf .tox'
    'rm -rf tmp'
    'rm -rf temp'
    'rm -rf out'
    'rm -rf .turbo'
    'rm -rf .parcel-cache'
    'rm -rf .vite'
    'rm -rf .claude/.*skills'
)

for pattern in "${SAFE_RM_PATTERNS[@]}"; do
    if [[ "$COMMAND" == *"$pattern"* ]]; then
        exit 0
    fi
done

# ============== 黑名单（危险模式） ==============
DENY_REASON=""

# 1. rm -rf /  或 rm -rf /*  或 rm -rf ~ 或 rm -rf ~/*
if [[ "$COMMAND" =~ rm[[:space:]]+-rf[[:space:]]+~?/?\*?[[:space:]]*$ ]] \
   || [[ "$COMMAND" =~ rm[[:space:]]+-rf[[:space:]]+/( |$) ]] \
   || [[ "$COMMAND" =~ rm[[:space:]]+-rf[[:space:]]+/\* ]]; then
    DENY_REASON="rm -rf 根目录或家目录（破坏性操作）"
fi

# 2. git push --force 到 main / master
if [ -z "$DENY_REASON" ] && [[ "$COMMAND" =~ git[[:space:]]+push[[:space:]]+.*(--force|-f)[[:space:]]+.*(main|master) ]]; then
    DENY_REASON="git push --force 到 main/master（强推主分支）"
fi

# 3. dd if=
if [ -z "$DENY_REASON" ] && echo "$COMMAND" | grep -qE '(^|[^A-Za-z0-9])dd[[:space:]]+if='; then
    DENY_REASON="dd 块设备操作（可能导致数据丢失）"
fi

# 4. mkfs（格式化）
if [ -z "$DENY_REASON" ] && [[ "$COMMAND" =~ mkfs\. ]]; then
    DENY_REASON="mkfs 格式化操作"
fi

# 5. chmod -R 777 /
if [ -z "$DENY_REASON" ] && [[ "$COMMAND" =~ chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+/ ]]; then
    DENY_REASON="chmod -R 777 /（权限炸弹）"
fi

# 6. :(){:|:&};:  （fork 炸弹）— 用 grep 避免 [[ =~ ]] 处理特殊字符
if [ -z "$DENY_REASON" ] && echo "$COMMAND" | grep -qE ':\(\)\{[[:space:]]*:\|:&[[:space:]]*\};:*'; then
    DENY_REASON="fork 炸弹"
fi

# 7. > /dev/sda 之类（重定向到块设备）— 用 grep 避免 [[ =~ ]] 处理特殊字符
if [ -z "$DENY_REASON" ] && echo "$COMMAND" | grep -qE '>[[:space:]]*/dev/[sh]d|>[[:space:]]*/dev/nvme'; then
    DENY_REASON="重定向到块设备"
fi

# 8. 关闭防火墙 / 禁用 SELinux
if [ -z "$DENY_REASON" ] && echo "$COMMAND" | grep -qE 'iptables[[:space:]]+-F|setenforce[[:space:]]+0'; then
    DENY_REASON="关闭防火墙/SELinux"
fi

# ============== 决策 ==============
if [ -n "$DENY_REASON" ]; then
    echo "❌ [mcpowers 铁律阻断] $DENY_REASON" >&2
    echo "   命令: $COMMAND" >&2
    echo "   提示：如确需执行，请用更具体的路径或先在 Claude Code 中确认" >&2
    exit 2  # Claude Code PreToolUse 约定的拒绝退出码
fi

# 默认放行
exit 0
