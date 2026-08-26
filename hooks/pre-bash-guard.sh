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

# ============== v4.6.3+ git commit 字眼兜底检测 ==============
# 设计动机:
#   v4.3.0~v4.6.2 期间 22 字眼硬门禁挂在 PreToolUse Write/Edit/MultiEdit 上,
#   用户反馈两大问题:① 每 Edit 一行就被 confirm UI 阻塞,全自动场景下整个流程卡住;
#   ② AI 都想办法绕开(同义词池无限 vs 22 字眼封闭集,这场对抗 hook 永远输).
#   v4.6.3 改为提交前一次性兜底:开发期不再拦截,git commit 时扫暂存区所有变更文件.
#
# 触发条件:命令以 `git commit ` 或 `git commit` 开头(任何选项组合,含 -m/-a/-S 等)
# 兜底方式:从暂存区逐个 Read 文件,喂给 check_no_ref_words.py,ERROR 违规累计即阻断
#
# 性能:每个暂存文件启一次 Python 子进程;常规 commit 5-10 文件 ~100ms/文件,2 秒内完成.
#       对比原 PreToolUse Edit 每行触发 ~50ms × 10 次= 500ms,反而更快.
if [ -z "$DENY_REASON" ] && [[ "$COMMAND" =~ ^[[:space:]]*git[[:space:]]+commit([[:space:]]|$) ]]; then
    DETECTOR="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)}/skills/mcpowers-shared/scripts/check_no_ref_words.py"
    # WORK_DIR 优先用 Claude Code 注入的 CLAUDE_PROJECT_DIR,否则 fallback 当前 pwd
    WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    # 探测可用 python 解释器（pre-bash-guard.sh 原本无 PY 探测,这里按需探测）
    PY_BASH=""
    for cand in python python3 py; do
        if command -v "$cand" >/dev/null 2>&1; then
            if "$cand" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
                PY_BASH="$cand"
                break
            fi
        fi
    done
    if [ -n "$PY_BASH" ] && [ -f "$DETECTOR" ]; then
        STAGED_FILES=$(cd "$WORK_DIR" 2>/dev/null && git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
        REF_BLOCKED=0
        REF_VIOLATIONS=""
        if [ -n "$STAGED_FILES" ]; then
            while IFS= read -r f; do
                [ -z "$f" ] && continue
                case "$f" in
                    *.py|*.sh|*.js|*.ts|*.jsx|*.tsx|*.mjs|*.cjs|*.go|*.java|*.kt|*.swift|*.rb|*.rs|\
                    *.yaml|*.yml|*.json|*.ini|*.toml|*.conf)
                        CONTENT=$(cd "$WORK_DIR" 2>/dev/null && git show ":$f" 2>/dev/null || true)
                        if [ -n "$CONTENT" ]; then
                            PAYLOAD=$(printf '%s' "$CONTENT" | "$PY_BASH" -c "
import json, sys
print(json.dumps({'file_path': sys.argv[1], 'content': sys.stdin.read()}, ensure_ascii=False))
" "$f" 2>/dev/null || true)
                            if [ -n "$PAYLOAD" ]; then
                                STDERR_OUT=$(printf '%s' "$PAYLOAD" | "$PY_BASH" "$DETECTOR" --level=ERROR 2>&1 >/dev/null || true)
                                if [ -n "$STDERR_OUT" ]; then
                                    REF_BLOCKED=1
                                    REF_VIOLATIONS="${REF_VIOLATIONS}   → $f:"$'\n'"${STDERR_OUT}"$'\n'
                                fi
                            fi
                        fi
                        ;;
                esac
            done <<< "$STAGED_FILES"
        fi
        if [ "$REF_BLOCKED" = "1" ]; then
            echo "❌ [mcpowers 铁律 · git commit 字眼门禁 v4.6.3+] 检测到暂存区文件含禁用字眼" >&2
            echo "" >&2
            echo "   违规摘要:" >&2
            printf '%s' "$REF_VIOLATIONS" >&2
            echo "   修复依据:mcpowers-shared/docs/技术规范/代码规范.md §11.3.1 智能二分判定" >&2
            echo "   修复建议:删掉禁用字眼,直接陈述当前做法(v4.3.0+ 铁律)" >&2
            echo "   修正后重新 git commit" >&2
            exit 2
        fi
    fi
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
