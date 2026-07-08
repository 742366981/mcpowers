#!/usr/bin/env bash
# mcpowers install 冒烟测试
# 用途：CI 跑完所有断言无失败即视为安装流程通过
# 退出码 0 = 通过，1 = 失败
#
# 关键设计：使用真实 HOME + 真实 ~/.claude 路径
#   原因：install.sh 写死了 $HOME/.claude，预检在脚本最开头，无法 override
#   安全性：仅做只读断言，不修改任何文件（避免污染）
#
# 用法：bash tests/install-smoke.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="$HOME"
SKILLS_DIR="$HOME_DIR/.claude/skills"
SETTINGS_FILE="$HOME_DIR/.claude/settings.json"
PASS=0
FAIL=0

# ============== 工具函数 ==============
assert() {
    local desc="$1"
    local cond="$2"
    set +e
    eval "$cond" >/dev/null 2>&1
    local rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
        echo "  ✓ $desc"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $desc"
        FAIL=$((FAIL + 1))
    fi
}

# ============== 1-3 预检 ==============
echo "[1/8] 预检：mcpowers 仓库存在"
assert "仓库目录存在" "[ -d '$REPO_DIR' ]"
assert "install.sh 存在" "[ -f '$REPO_DIR/install.sh' ]"
assert "mcpowers/SKILL.md 存在" "[ -f '$REPO_DIR/mcpowers/SKILL.md' ]"

echo "[2/8] 预检：Claude Code ~/.claude 已就位"
assert ".claude 目录存在" "[ -d '$HOME_DIR/.claude' ]"
assert "skills 目录存在" "[ -d '$SKILLS_DIR' ]"

echo "[3/8] 预检：Git Bash 可用"
assert "bash 可执行" "command -v bash >/dev/null"

# ============== 4 验证安装 ==============
echo "[4/8] 断言：路由器已安装"
assert "mcpowers/SKILL.md 已安装" "[ -f '$SKILLS_DIR/mcpowers/SKILL.md' ]"
assert "mcpowers/hooks 目录已安装" "[ -d '$SKILLS_DIR/mcpowers/hooks' ]"

# ============== 5 验证技能数 ==============
echo "[5/8] 断言：20 个 mcpowers* 全部安装（1 路由器 + 18 技能 + 1 规范库）"
SKILL_COUNT=$(ls -1 "$SKILLS_DIR" 2>/dev/null | grep -c '^mcpowers' || true)
assert "技能数=20" "[ '$SKILL_COUNT' = '20' ]"

# ============== 6 验证规范库 ==============
echo "[6/8] 断言：mcpowers-shared 规范库完整"
SPEC_COUNT=$(find "$SKILLS_DIR/mcpowers-shared/docs" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$SPEC_COUNT" -ge 18 ]; then
    echo "  ✓ 规范数=$SPEC_COUNT (≥18)"
    PASS=$((PASS + 1))
else
    echo "  ✗ 规范数=$SPEC_COUNT (<18)"
    FAIL=$((FAIL + 1))
fi

# ============== 7 验证 hooks 注册 ==============
echo "[7/8] 断言：hooks 已注册到 settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    assert "_mcpowers_marker 已写入" "grep -q '\"_mcpowers_marker\": true' '$SETTINGS_FILE'"
    assert "SessionStart 段存在" "grep -q '\"SessionStart\"' '$SETTINGS_FILE'"
    assert "PreToolUse 段存在" "grep -q '\"PreToolUse\"' '$SETTINGS_FILE'"
else
    echo "  ⊘ settings.json 不存在（可能用了 --no-hooks 安装）"
    FAIL=$((FAIL + 1))
fi

# ============== 8 验证 hooks 资产 ==============
echo "[8/8] 断言：hooks 资产文件就位"
assert "pre-bash-guard.sh 存在" "[ -f '$SKILLS_DIR/mcpowers/hooks/pre-bash-guard.sh' ]"
assert "session-start.sh 存在" "[ -f '$SKILLS_DIR/mcpowers/hooks/session-start.sh' ]"
assert "pre-bash-guard 可执行" "[ -x '$SKILLS_DIR/mcpowers/hooks/pre-bash-guard.sh' ]"

# ============== 9 行为断言：pre-bash-guard 真阻断 ==============
echo "[9/9] 行为断言：pre-bash-guard 危险命令应被阻断"
set +e
bash "$SKILLS_DIR/mcpowers/hooks/pre-bash-guard.sh" <<<'{"tool_input":{"command":"rm -rf /"}}' >/dev/null 2>&1
RC_DANGEROUS=$?
set -e
assert "rm -rf / 被阻断（exit 2）" "[ '$RC_DANGEROUS' = '2' ]"

# ============== 汇总 ==============
echo ""
echo "=== $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] || exit 1
exit 0
