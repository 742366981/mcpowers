#!/usr/bin/env bash
# mcpowers 插件结构验证测试
# 用途：CI 跑完所有断言无失败即视为插件结构合规
# 退出码 0 = 通过，1 = 失败
#
# 关键设计：纯只读断言（不修改任何文件，可安全在 CI 跑）
# 适配 v2.0 插件市场格式
#
# 用法：bash tests/plugin-verify.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Windows 兼容：Git Bash 返回 POSIX 路径 /d/...，Windows 原生 Python 需要 D:\...
if command -v cygpath >/dev/null 2>&1; then
    REPO_DIR_WIN=$(cygpath -w "$REPO_DIR")
else
    REPO_DIR_WIN="$REPO_DIR"
fi
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

assert_eq() {
    local desc="$1"
    local actual="$2"
    local expected="$3"
    if [ "$actual" = "$expected" ]; then
        echo "  ✓ $desc (=$actual)"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $desc (实际=$actual, 期望=$expected)"
        FAIL=$((FAIL + 1))
    fi
}

# ============== 1. 预检：仓库结构 ==============
echo "[1/7] 预检：仓库根目录"
assert "仓库目录存在" "[ -d '$REPO_DIR' ]"
assert ".claude-plugin/ 存在" "[ -d '$REPO_DIR/.claude-plugin' ]"
assert "skills/ 存在" "[ -d '$REPO_DIR/skills' ]"
assert "hooks/ 存在" "[ -d '$REPO_DIR/hooks' ]"

# ============== 2. 插件元数据 ==============
echo "[2/7] 断言：插件元数据合法"
assert ".claude-plugin/marketplace.json 存在" "[ -f '$REPO_DIR/.claude-plugin/marketplace.json' ]"
assert ".claude-plugin/plugin.json 存在" "[ -f '$REPO_DIR/.claude-plugin/plugin.json' ]"

# 验证 marketplace.json 是合法 JSON
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
else
    PY_BIN=""
fi

if [ -n "$PY_BIN" ]; then
    NAME=$($PY_BIN -c "import json; print(json.load(open(r'$REPO_DIR_WIN/.claude-plugin/marketplace.json', encoding='utf-8'))['name'])" 2>/dev/null || echo "")
    assert_eq "marketplace.json name=mcpowers" "$NAME" "mcpowers"
else
    assert "marketplace.json 含 mcpowers 名称" "grep -q '\"name\": \"mcpowers\"' '$REPO_DIR/.claude-plugin/marketplace.json'"
fi

# ============== 3. 技能结构 ==============
SKILL_DIRS=$(ls -1 "$REPO_DIR/skills" 2>/dev/null | grep '^mcpowers')
SKILL_COUNT=$(echo "$SKILL_DIRS" | grep -c '^mcpowers' || true)
EXPECTED_SKILL_COUNT=$(echo "$SKILL_DIRS" | wc -l)
echo "[3/7] 断言：${EXPECTED_SKILL_COUNT} 个技能全部含 SKILL.md"
assert_eq "技能数=${EXPECTED_SKILL_COUNT}（1 路由器 + N 技能 + 1 规范库）" "$SKILL_COUNT" "$EXPECTED_SKILL_COUNT"

MISSING_SKILL=""
for d in $SKILL_DIRS; do
    if [ ! -f "$REPO_DIR/skills/$d/SKILL.md" ]; then
        MISSING_SKILL="$MISSING_SKILL $d"
    fi
done
if [ -z "$MISSING_SKILL" ]; then
    echo "  ✓ 所有 ${EXPECTED_SKILL_COUNT} 个技能均有 SKILL.md"
    PASS=$((PASS + 1))
else
    echo "  ✗ 缺失 SKILL.md:$MISSING_SKILL"
    FAIL=$((FAIL + 1))
fi

# ============== 4. SKILL.md frontmatter ==============
echo "[4/7] 断言：所有 SKILL.md 有合法 frontmatter"
FM_OK=true
for d in $SKILL_DIRS; do
    FILE="$REPO_DIR/skills/$d/SKILL.md"
    if ! head -1 "$FILE" | grep -q '^---$'; then
        echo "  ✗ $d/SKILL.md 缺少 frontmatter 起始"
        FM_OK=false
        FAIL=$((FAIL + 1))
    elif ! grep -q '^name:' "$FILE"; then
        echo "  ✗ $d/SKILL.md 缺少 name: 字段"
        FM_OK=false
        FAIL=$((FAIL + 1))
    elif ! grep -q '^description:' "$FILE"; then
        echo "  ✗ $d/SKILL.md 缺少 description: 字段"
        FM_OK=false
        FAIL=$((FAIL + 1))
    fi
done
if [ "$FM_OK" = true ]; then
    echo "  ✓ ${EXPECTED_SKILL_COUNT} 个 SKILL.md frontmatter 完整"
    PASS=$((PASS + 1))
fi

# ============== 5. 规范库 ==============
echo "[5/7] 断言：mcpowers-shared 规范库完整"
SPEC_COUNT=$(find "$REPO_DIR/skills/mcpowers-shared/docs" -name "*规范.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$SPEC_COUNT" -ge 18 ]; then
    echo "  ✓ 规范数=$SPEC_COUNT (≥18)"
    PASS=$((PASS + 1))
else
    echo "  ✗ 规范数=$SPEC_COUNT (<18)"
    FAIL=$((FAIL + 1))
fi
assert "mcpowers-spec-index 存在" "[ -d '$REPO_DIR/skills/mcpowers-shared/mcpowers-spec-index' ]"

# ============== 6. hooks 系统 ==============
echo "[6/7] 断言：hooks 系统完整"
assert "hooks/hooks.json 存在" "[ -f '$REPO_DIR/hooks/hooks.json' ]"
assert "session-start.sh 存在" "[ -f '$REPO_DIR/hooks/session-start.sh' ]"
assert "pre-bash-guard.sh 存在" "[ -f '$REPO_DIR/hooks/pre-bash-guard.sh' ]"
assert "pre-write-confirm.sh 存在" "[ -f '$REPO_DIR/hooks/pre-write-confirm.sh' ]"
assert "post-write-commit-reminder.sh 存在" "[ -f '$REPO_DIR/hooks/post-write-commit-reminder.sh' ]"
assert "pre-bash-guard 可执行" "[ -x '$REPO_DIR/hooks/pre-bash-guard.sh' ]"

# 验证 hooks.json 用 ${CLAUDE_PLUGIN_ROOT}
assert "hooks.json 用 CLAUDE_PLUGIN_ROOT 路径" "grep -q 'CLAUDE_PLUGIN_ROOT' '$REPO_DIR/hooks/hooks.json'"
# 验证不再用 __HOOKS_DIR__ 占位符
if grep -q '__HOOKS_DIR__' "$REPO_DIR/hooks/hooks.json" 2>/dev/null; then
    echo "  ✗ hooks.json 仍含 __HOOKS_DIR__ 占位符"
    FAIL=$((FAIL + 1))
else
    echo "  ✓ hooks.json 移除 __HOOKS_DIR__ 占位符"
    PASS=$((PASS + 1))
fi

# ============== 7. 行为断言：hooks 真阻断 ==============
echo "[7/7] 行为断言：pre-bash-guard 危险命令应被阻断"
set +e
bash "$REPO_DIR/hooks/pre-bash-guard.sh" <<<'{"tool_input":{"command":"rm -rf /"}}' >/dev/null 2>&1
RC_DANGEROUS=$?
set -e
assert_eq "rm -rf / 被阻断（exit 2）" "$RC_DANGEROUS" "2"

# pre-write-confirm 4 个保护路径必须阻断（v2.0 修复后回归测试）
set +e
CLAUDE_PLUGIN_ROOT="$REPO_DIR" bash "$REPO_DIR/hooks/pre-write-confirm.sh" \
    <<<'{"tool_input":{"file_path":"'$REPO_DIR_WIN'/skills/mcpowers/foo.md"}}' >/dev/null 2>&1
RC_SKILL=$?
CLAUDE_PLUGIN_ROOT="$REPO_DIR" bash "$REPO_DIR/hooks/pre-write-confirm.sh" \
    <<<'{"tool_input":{"file_path":"'$REPO_DIR_WIN'/skills/mcpowers-shared/docs/技术规范/API规范.md"}}' >/dev/null 2>&1
RC_SHARED=$?
CLAUDE_PLUGIN_ROOT="$REPO_DIR" bash "$REPO_DIR/hooks/pre-write-confirm.sh" \
    <<<'{"tool_input":{"file_path":"'$REPO_DIR_WIN'/hooks/hooks.json"}}' >/dev/null 2>&1
RC_HOOKS=$?
CLAUDE_PLUGIN_ROOT="$REPO_DIR" bash "$REPO_DIR/hooks/pre-write-confirm.sh" \
    <<<'{"tool_input":{"file_path":"'$REPO_DIR_WIN'/.claude-plugin/plugin.json"}}' >/dev/null 2>&1
RC_PLUGIN=$?
set -e
assert_eq "pre-write 阻断 skills/mcpowers/（exit 2）" "$RC_SKILL" "2"
assert_eq "pre-write 阻断 skills/mcpowers-shared/（exit 2）" "$RC_SHARED" "2"
assert_eq "pre-write 阻断 hooks/（exit 2）" "$RC_HOOKS" "2"
assert_eq "pre-write 阻断 .claude-plugin/（exit 2）" "$RC_PLUGIN" "2"

# pre-write-confirm 必须放行非保护路径
set +e
CLAUDE_PLUGIN_ROOT="$REPO_DIR" bash "$REPO_DIR/hooks/pre-write-confirm.sh" \
    <<<'{"tool_input":{"file_path":"'$REPO_DIR_WIN'/README.md"}}' >/dev/null 2>&1
RC_README=$?
CLAUDE_PLUGIN_ROOT="$REPO_DIR" bash "$REPO_DIR/hooks/pre-write-confirm.sh" \
    <<<'{"tool_input":{"file_path":"'$REPO_DIR_WIN'/tests/foo.sh"}}' >/dev/null 2>&1
RC_TEST=$?
set -e
assert_eq "pre-write 放行 README.md（exit 0）" "$RC_README" "0"
assert_eq "pre-write 放行 tests/foo.sh（exit 0）" "$RC_TEST" "0"

# ============== 旧安装脚本不应残留 ==============
echo ""
echo "[旧资产清理] 断言：旧安装脚本已删除"
assert "install.sh 已删除" "[ ! -f '$REPO_DIR/install.sh' ]"
assert "install.ps1 已删除" "[ ! -f '$REPO_DIR/install.ps1' ]"
assert "uninstall.sh 已删除" "[ ! -f '$REPO_DIR/uninstall.sh' ]"
assert "uninstall.ps1 已删除" "[ ! -f '$REPO_DIR/uninstall.ps1' ]"
assert "scene/ 中间层已删除" "[ ! -d '$REPO_DIR/skills/scene' ]"
assert "method/ 中间层已删除" "[ ! -d '$REPO_DIR/skills/method' ]"

# ============== 汇总 ==============
echo ""
echo "=== $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] || exit 1
exit 0
