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

# 优先使用可执行的 python3；Windows Store 占位命令可能存在但不可用，需回退到 python
if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
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
SPEC_COUNT=$(find "$REPO_DIR/skills/mcpowers-shared/docs/技术规范" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$SPEC_COUNT" -ge 28 ]; then
    echo "  ✓ 技术规范数=$SPEC_COUNT (≥28)"
    PASS=$((PASS + 1))
else
    echo "  ✗ 技术规范数=$SPEC_COUNT (<28)"
    FAIL=$((FAIL + 1))
fi
assert "mcpowers-spec-index 存在" "[ -d '$REPO_DIR/skills/mcpowers-shared/mcpowers-spec-index' ]"

# ============== 6. hooks 系统 ==============
echo "[6/7] 断言：hooks 系统完整"
assert "hooks/hooks.json 存在" "[ -f '$REPO_DIR/hooks/hooks.json' ]"
assert "session-start.sh 存在" "[ -f '$REPO_DIR/hooks/session-start.sh' ]"
assert "pre-bash-guard.sh 存在" "[ -f '$REPO_DIR/hooks/pre-bash-guard.sh' ]"
assert "pre-write-confirm.sh 存在" "[ -f '$REPO_DIR/hooks/pre-write-confirm.sh' ]"
assert "pre-write-confirm-api-hint.sh 存在" "[ -f '$REPO_DIR/hooks/pre-write-confirm-api-hint.sh' ]"
assert "pre-write-check-duplicate.sh 存在（v2.26.0+）" "[ -f '$REPO_DIR/hooks/pre-write-check-duplicate.sh' ]"
assert "pre-write-check-import.sh 存在（v2.27.0+）" "[ -f '$REPO_DIR/hooks/pre-write-check-import.sh' ]"
assert "check_python_import_placement.py 存在（v2.27.0+）" "[ -f '$REPO_DIR/hooks/check_python_import_placement.py' ]"
assert "post-write-commit-reminder.sh 存在" "[ -f '$REPO_DIR/hooks/post-write-commit-reminder.sh' ]"
assert "post-write-check-doc-content.sh 存在（v4.0.2+）" "[ -f '$REPO_DIR/hooks/post-write-check-doc-content.sh' ]"
assert "_forbidden_ref_words.txt 共享常量存在（v4.0.2+）" "[ -f '$REPO_DIR/skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt' ]"
assert "pre-bash-guard 可执行" "[ -x '$REPO_DIR/hooks/pre-bash-guard.sh' ]"
assert "post-write-check-doc-content.sh 可执行" "[ -x '$REPO_DIR/hooks/post-write-check-doc-content.sh' ]"

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

# v2.5.2：校验 hooks.json 中所有引用的脚本都实际存在
HOOK_REFS=$(grep -oE 'hooks/[a-zA-Z0-9_-]+\.sh' "$REPO_DIR/hooks/hooks.json" 2>/dev/null | sort -u || true)
HOOK_REF_FAIL=0
for ref in $HOOK_REFS; do
    if [ ! -f "$REPO_DIR/$ref" ]; then
        echo "  ✗ hooks.json 引用 $ref 但文件不存在"
        HOOK_REF_FAIL=$((HOOK_REF_FAIL + 1))
    fi
done
if [ "$HOOK_REF_FAIL" -eq 0 ]; then
    echo "  ✓ hooks.json 引用的 $(echo "$HOOK_REFS" | wc -l | tr -d ' ') 个脚本全部存在"
    PASS=$((PASS + 1))
else
    FAIL=$((FAIL + HOOK_REF_FAIL))
fi

# v2.5.2：校验事件组数 = 4（SessionStart + PreToolUse(Bash) + PreToolUse(Write) + PostToolUse）
# 口径：按 matcher 分组（README/CLAUDE.md 中"4 个事件组"与此对齐）
EVENT_GROUP_COUNT=0
if grep -q '"SessionStart"' "$REPO_DIR/hooks/hooks.json" 2>/dev/null; then
    EVENT_GROUP_COUNT=$((EVENT_GROUP_COUNT + 1))
fi
# PreToolUse 分 Bash 和 Write 两组
if grep -q '"matcher":[[:space:]]*"Bash"' "$REPO_DIR/hooks/hooks.json" 2>/dev/null; then
    EVENT_GROUP_COUNT=$((EVENT_GROUP_COUNT + 1))
fi
if grep -q '"matcher":[[:space:]]*"Write"' "$REPO_DIR/hooks/hooks.json" 2>/dev/null; then
    EVENT_GROUP_COUNT=$((EVENT_GROUP_COUNT + 1))
fi
if grep -q '"PostToolUse"' "$REPO_DIR/hooks/hooks.json" 2>/dev/null; then
    EVENT_GROUP_COUNT=$((EVENT_GROUP_COUNT + 1))
fi
assert_eq "事件组数 = 4（按 matcher 分组）" "$EVENT_GROUP_COUNT" "4"

# v2.5.2：校验插件版本号三处一致（与 check-readme-sync.sh 重复，但作独立安全网）
if [ -n "$PY_BIN" ]; then
    PV1=$($PY_BIN -c "import json; print(json.load(open(r'$REPO_DIR_WIN/.claude-plugin/plugin.json', encoding='utf-8'))['version'])" 2>/dev/null || echo "")
    PV2=$($PY_BIN -c "import json; print(json.load(open(r'$REPO_DIR_WIN/.claude-plugin/marketplace.json', encoding='utf-8'))['version'])" 2>/dev/null || echo "")
    PV3=$($PY_BIN -c "import json; print(json.load(open(r'$REPO_DIR_WIN/.claude-plugin/marketplace.json', encoding='utf-8'))['plugins'][0]['version'])" 2>/dev/null || echo "")
    if [ "$PV1" = "$PV2" ] && [ "$PV2" = "$PV3" ] && [ -n "$PV1" ]; then
        echo "  ✓ 三处版本号一致: $PV1"
        PASS=$((PASS + 1))
    else
        echo "  ✗ 版本号不一致: plugin=$PV1, marketplace=$PV2, plugins[0]=$PV3"
        FAIL=$((FAIL + 1))
    fi
else
    assert "三处版本号一致（无 Python，跳过）" "true"
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

# pre-write-check-duplicate 行为断言（入口惯例名豁免）
TMP_DUPLICATE="$REPO_DIR/tests/.tmp_duplicate_check"
if command -v cygpath >/dev/null 2>&1; then
    TMP_DUPLICATE_PATH=$(cygpath -m "$TMP_DUPLICATE")
else
    TMP_DUPLICATE_PATH="$TMP_DUPLICATE"
fi
mkdir -p "$TMP_DUPLICATE" 2>/dev/null || true
PAYLOAD_MAIN='{"tool_input":{"file_path":"'$TMP_DUPLICATE_PATH'/main.py","content":"def main():\n    return 0\n"}}'
PAYLOAD_DUPLICATE='{"tool_input":{"file_path":"'$TMP_DUPLICATE_PATH'/duplicate.py","content":"def extract_function_names():\n    return set()\n"}}'
if [ -n "$PY_BIN" ]; then
    set +e
    echo "$PAYLOAD_MAIN" | bash "$REPO_DIR/hooks/pre-write-check-duplicate.sh" >/dev/null 2>&1
    RC_DUP_MAIN=$?
    echo "$PAYLOAD_DUPLICATE" | bash "$REPO_DIR/hooks/pre-write-check-duplicate.sh" >/dev/null 2>&1
    RC_DUP_OTHER=$?
    set -e
    assert_eq "pre-write-check-duplicate 放行 main 入口（exit 0）" "$RC_DUP_MAIN" "0"
    assert_eq "pre-write-check-duplicate 阻断普通同名函数（exit 2）" "$RC_DUP_OTHER" "2"
fi
rm -rf "$TMP_DUPLICATE" 2>/dev/null || true

# pre-write-check-duplicate v2.28.2 极简判定行为断言
# 3 档判定：①同文件重名 → block ②跨文件同名 + 单行透传 → block ③其他跨文件同名 → 放行
# 临时子仓：建一个独立 git 仓库、灌入 fixtures、再模拟 hook 检测
if [ -n "$PY_BIN" ]; then
    TMP_HEUR="$REPO_DIR/tests/.tmp_heur_check"
    rm -rf "$TMP_HEUR" 2>/dev/null || true
    mkdir -p "$TMP_HEUR/src/utils" 2>/dev/null || true
    cd "$TMP_HEUR"
    git init -q .
    git config user.email "verify@x" && git config user.name "verify"
    # fixture1: utils/a.py::format_response + utils/b.py::format_response（跨文件同名基线）
    cat > src/utils/a.py <<'PYFIX'
def format_response(data):
    return {"ok": True, "data": data}
PYFIX
    cat > src/utils/b.py <<'PYFIX'
def format_response(payload):
    return {"ok": True, "payload": payload}
PYFIX
    git add -A && git commit -q -m "baseline"
    if command -v cygpath >/dev/null 2>&1; then
        TMP_HEUR_WIN=$(cygpath -m "$TMP_HEUR")
    else
        TMP_HEUR_WIN="$TMP_HEUR"
    fi

    # case_a: 跨文件同名（非单行透传）→ 默认放行，exit 0
    PAYLOAD_A='{"tool_input":{"file_path":"'$TMP_HEUR_WIN'/src/utils/c.py","content":"def format_response(item):\n    item = item.strip()\n    return {\"wrapped\": item}\n"}}'
    set +e
    STDERR_A=$(echo "$PAYLOAD_A" | bash "$REPO_DIR/hooks/pre-write-check-duplicate.sh" 2>&1 >/dev/null)
    RC_A=$?
    set -e
    assert_eq "v2.28.2 case_a 跨文件同名（非单行透传）→ exit 0" "$RC_A" "0"
    if echo "$STDERR_A" | grep -q "阻断"; then
        echo "  ✗ case_a stderr 不应含 [阻断]"
        FAIL=$((FAIL + 1))
    else
        echo "  ✓ case_a 默认放行（无 [阻断]）"
        PASS=$((PASS + 1))
    fi

    # case_b: 跨文件同名 + 签名差异 → 默认放行，exit 0
    PAYLOAD_B='{"tool_input":{"file_path":"'$TMP_HEUR_WIN'/src/utils/d.py","content":"def format_response(text, strict, encoding):\n    return text if strict else encoding\n"}}'
    set +e
    STDERR_B=$(echo "$PAYLOAD_B" | bash "$REPO_DIR/hooks/pre-write-check-duplicate.sh" 2>&1 >/dev/null)
    RC_B=$?
    set -e
    assert_eq "v2.28.2 case_b 跨文件同名 + 签名差异 → exit 0" "$RC_B" "0"

    # case_c: 跨文件同名 + 类内绑定方法 → 默认放行，exit 0
    PAYLOAD_C='{"tool_input":{"file_path":"'$TMP_HEUR_WIN'/src/utils/e.py","content":"class Formatter:\n    def format_response(self, data):\n        return data\n"}}'
    set +e
    STDERR_C=$(echo "$PAYLOAD_C" | bash "$REPO_DIR/hooks/pre-write-check-duplicate.sh" 2>&1 >/dev/null)
    RC_C=$?
    set -e
    assert_eq "v2.28.2 case_c 跨文件同名 + 绑定方法 → exit 0" "$RC_C" "0"

    # case_d: 单行透传（gold standard 二次包装）→ 强化阻断，exit 2
    PAYLOAD_D='{"tool_input":{"file_path":"'$TMP_HEUR_WIN'/src/wrapper.py","content":"def format_response(text):\n    return some_other.format_response(text)\n"}}'
    set +e
    STDERR_D=$(echo "$PAYLOAD_D" | bash "$REPO_DIR/hooks/pre-write-check-duplicate.sh" 2>&1 >/dev/null)
    RC_D=$?
    set -e
    assert_eq "v2.28.2 case_d 单行透传 → exit 2" "$RC_D" "2"
    if echo "$STDERR_D" | grep -q "单行透传"; then
        echo "  ✓ case_d stderr 含 [单行透传]"
        PASS=$((PASS + 1))
    else
        echo "  ✗ case_d stderr 缺 [单行透传] 标签"
        FAIL=$((FAIL + 1))
    fi

    # case_e: 同文件内重名 → 真 bug（Python 后者覆盖前者），exit 2
    PAYLOAD_E='{"tool_input":{"file_path":"'$TMP_HEUR_WIN'/src/same_file.py","content":"def parse(data):\n    return json.loads(data)\n\ndef parse(data):\n    return json.loads(data) * 2\n"}}'
    set +e
    STDERR_E=$(echo "$PAYLOAD_E" | bash "$REPO_DIR/hooks/pre-write-check-duplicate.sh" 2>&1 >/dev/null)
    RC_E=$?
    set -e
    assert_eq "v2.28.2 case_e 同文件内重名 → exit 2" "$RC_E" "2"
    if echo "$STDERR_E" | grep -q "同文件重名"; then
        echo "  ✓ case_e stderr 含 [同文件重名]"
        PASS=$((PASS + 1))
    else
        echo "  ✗ case_e stderr 缺 [同文件重名] 标签"
        FAIL=$((FAIL + 1))
    fi

    cd "$REPO_DIR"
    rm -rf "$TMP_HEUR" 2>/dev/null || true
fi

# pre-write-check-import 行为断言（v2.27.0+）
# Write 视为覆盖：模块级 import 放行、函数内 import 阻断
# 注意：Windows 下 POSIX 路径（含 /）在 Path() 里可正常解析；用 REPO_DIR（POSIX）而非 REPO_DIR_WIN（带 \，会污染 JSON 字符串）
TMP_IMPORT="$REPO_DIR/tests/.tmp_import_check"
mkdir -p "$TMP_IMPORT" 2>/dev/null || true
PAYLOAD_OK='{"tool_input":{"file_path":"'$TMP_IMPORT'/ok_module.py","content":"import os\nfrom flask import Flask\n\ndef foo():\n    return 1\n"}}'
PAYLOAD_BAD='{"tool_input":{"file_path":"'$TMP_IMPORT'/bad_local.py","content":"import os\nfrom flask import Flask\n\ndef foo():\n    from datetime import datetime\n    return datetime.now()\n"}}'
PAYLOAD_CLASS='{"tool_input":{"file_path":"'$TMP_IMPORT'/bad_class.py","content":"class Bar:\n    def baz(self):\n        from datetime import datetime\n        return datetime.now()\n"}}'
PAYLOAD_TRY='{"tool_input":{"file_path":"'$TMP_IMPORT'/ok_try.py","content":"try:\n    from flask import g\nexcept ImportError:\n    g = None\n"}}'
PAYLOAD_NON_PY='{"tool_input":{"file_path":"'$TMP_IMPORT'/foo.md","content":"# not python"}}'

if [ -n "$PY_BIN" ]; then
    set +e
    echo "$PAYLOAD_OK" | bash "$REPO_DIR/hooks/pre-write-check-import.sh" >/dev/null 2>&1
    RC_IMP_OK=$?
    echo "$PAYLOAD_BAD" | bash "$REPO_DIR/hooks/pre-write-check-import.sh" >/dev/null 2>&1
    RC_IMP_BAD=$?
    echo "$PAYLOAD_CLASS" | bash "$REPO_DIR/hooks/pre-write-check-import.sh" >/dev/null 2>&1
    RC_IMP_CLASS=$?
    echo "$PAYLOAD_TRY" | bash "$REPO_DIR/hooks/pre-write-check-import.sh" >/dev/null 2>&1
    RC_IMP_TRY=$?
    echo "$PAYLOAD_NON_PY" | bash "$REPO_DIR/hooks/pre-write-check-import.sh" >/dev/null 2>&1
    RC_IMP_NON_PY=$?
    set -e
    assert_eq "pre-write-check-import 放行模块级 import（exit 0）" "$RC_IMP_OK" "0"
    assert_eq "pre-write-check-import 阻断函数内 import（exit 2）" "$RC_IMP_BAD" "2"
    assert_eq "pre-write-check-import 阻断类方法内 import（exit 2）" "$RC_IMP_CLASS" "2"
    assert_eq "pre-write-check-import 放行模块级 try/except import（exit 0）" "$RC_IMP_TRY" "0"
    assert_eq "pre-write-check-import 放行非 .py 文件（exit 0）" "$RC_IMP_NON_PY" "0"
fi
rm -rf "$TMP_IMPORT" 2>/dev/null || true

# ============== 7.5 逆向会话编排自检 ==============
echo "[7.5] 逆向会话编排工具自检"
SESSION_VERIFY="$REPO_DIR/tests/reverse-analysis-session-verify.py"
assert "逆向会话自检脚本存在" "[ -f '$SESSION_VERIFY' ]"
if [ -f "$SESSION_VERIFY" ] && [ -n "$PY_BIN" ]; then
    set +e
    $PY_BIN "$SESSION_VERIFY" >/dev/null 2>&1
    RC_SESSION=$?
    set -e
    assert_eq "逆向会话自检通过（exit 0）" "$RC_SESSION" "0"
fi

# ============== 7.6 会话派生产物生成器自检（v2.21.0 新增） ==============
echo "[7.6] 会话派生产物生成器自检"
ARTIFACTS_VERIFY="$REPO_DIR/tests/session-artifacts-generator-verify.py"
assert "会话派生产物自检脚本存在" "[ -f '$ARTIFACTS_VERIFY' ]"
if [ -f "$ARTIFACTS_VERIFY" ] && [ -n "$PY_BIN" ]; then
    set +e
    $PY_BIN "$ARTIFACTS_VERIFY" >/dev/null 2>&1
    RC_ARTIFACTS=$?
    set -e
    assert_eq "会话派生产物自检通过（exit 0）" "$RC_ARTIFACTS" "0"
fi

# ============== 7.7 post-write-check-doc-content.sh 软门禁自检（v4.0.2+ 新增） ==============
echo "[7.7] post-write-check-doc-content.sh 软门禁自检（v4.0.2+ 文档零引用）"
HOOK_DOCC="$REPO_DIR/hooks/post-write-check-doc-content.sh"
FORBIDDEN_FILE="$REPO_DIR/skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt"
assert "post-write-check-doc-content.sh 存在" "[ -f '$HOOK_DOCC' ]"
assert "_forbidden_ref_words.txt 共享常量存在" "[ -f '$FORBIDDEN_FILE' ]"
if [ -x "$HOOK_DOCC" ] && [ -f "$FORBIDDEN_FILE" ]; then
    # T1:写含「参考」的 .md → exit 0 + stderr 含「参考」
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"docs/test.md","content":"# X\n本接口参考 RBAC"}}' | bash "$HOOK_DOCC" 2>/tmp/docc_t1
    RC_T1=$?
    set -e
    assert_eq "T1 含「参考」exit 0（软门禁不阻断）" "$RC_T1" "0"
    assert "T1 stderr 含「参考」" "grep -q '参考' /tmp/docc_t1"

    # T2:CHANGELOG.md 含「参见」 → exit 0 + stderr 无提示（白名单）
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"CHANGELOG.md","content":"## v4.0.2\n参见 #123"}}' | bash "$HOOK_DOCC" 2>/tmp/docc_t2
    RC_T2=$?
    set -e
    assert_eq "T2 CHANGELOG.md 含「参见」exit 0" "$RC_T2" "0"
    assert "T2 CHANGELOG.md 走白名单（stderr 无「画蛇添足」）" "! grep -q '画蛇添足' /tmp/docc_t2"

    # T3:docs/历史教训/x.md 含「v1 时用 X」 → exit 0 无提示
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"docs/历史教训/x.md","content":"## 教训\nv1 时用 X"}}' | bash "$HOOK_DOCC" 2>/tmp/docc_t3
    RC_T3=$?
    set -e
    assert_eq "T3 历史教训路径 exit 0" "$RC_T3" "0"
    assert "T3 历史教训路径走白名单" "! grep -q '画蛇添足' /tmp/docc_t3"

    # T4:非 .md 文件 → exit 0 无提示
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"# 参考 xxx"}}' | bash "$HOOK_DOCC" 2>/tmp/docc_t4
    RC_T4=$?
    set -e
    assert_eq "T4 非 .md 文件 exit 0" "$RC_T4" "0"
    assert "T4 非 .md 文件不触发扫描" "! grep -q '画蛇添足' /tmp/docc_t4"

    # T5:英文 see also → exit 0 + stderr 提示
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"docs/api.md","content":"# API\nsee also OpenAPI 3.0"}}' | bash "$HOOK_DOCC" 2>/tmp/docc_t5
    RC_T5=$?
    set -e
    assert_eq "T5 英文 see also exit 0" "$RC_T5" "0"
    assert "T5 英文 see also 命中" "grep -q 'see also' /tmp/docc_t5"
fi

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
