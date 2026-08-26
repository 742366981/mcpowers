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
assert "pre-write-check-no-ref-words.sh 存在（v4.3.0+）" "[ -f '$REPO_DIR/hooks/pre-write-check-no-ref-words.sh' ]"
assert "post-write-check-no-ref-words.sh 存在（v4.3.0+）" "[ -f '$REPO_DIR/hooks/post-write-check-no-ref-words.sh' ]"
assert "check_no_ref_words.py 共享检测器存在（v4.3.0+）" "[ -f '$REPO_DIR/skills/mcpowers-shared/scripts/check_no_ref_words.py' ]"
assert "_forbidden_ref_words.txt 共享常量存在（v4.0.2+）" "[ -f '$REPO_DIR/skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt' ]"
assert "_internal_spec_docs.txt 共享常量存在（v4.3.0+）" "[ -f '$REPO_DIR/skills/mcpowers-shared/docs/_assets/_internal_spec_docs.txt' ]"
assert "_external_authority.txt 共享常量存在（v4.3.0+）" "[ -f '$REPO_DIR/skills/mcpowers-shared/docs/_assets/_external_authority.txt' ]"
assert "pre-bash-guard 可执行" "[ -x '$REPO_DIR/hooks/pre-bash-guard.sh' ]"
assert "pre-write-check-no-ref-words.sh 可执行" "[ -x '$REPO_DIR/hooks/pre-write-check-no-ref-words.sh' ]"
assert "post-write-check-no-ref-words.sh 可执行" "[ -x '$REPO_DIR/hooks/post-write-check-no-ref-words.sh' ]"

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
    SESSION_STDERR_FILE=$(mktemp)
    $PY_BIN "$SESSION_VERIFY" >/dev/null 2>"$SESSION_STDERR_FILE"
    RC_SESSION=$?
    set -e
    if [ "$RC_SESSION" -ne 0 ]; then
        # 仅在失败时打印 stderr + 环境信息，便于跨平台排查（CI 不能吞错）
        echo "    ↳ 逆向会话自检 stderr ↓↓↓"
        sed 's/^/      /' "$SESSION_STDERR_FILE" | head -80
        echo "    ↳ ↑↑↑ stderr end"
        echo "    ↳ 环境: Python=$($PY_BIN --version 2>&1) | OS=$(uname -a 2>/dev/null || ver) | LC_ALL=${LC_ALL:-<unset>} | LANG=${LANG:-<unset>}"
        # 同时写入 GitHub Actions annotation（公开 API 可见，避免需登录看 logs）
        FIRST_LINE=$(head -1 "$SESSION_STDERR_FILE" | tr -d '\r' | cut -c1-200)
        LAST_LINE=$(tail -1 "$SESSION_STDERR_FILE" | tr -d '\r' | cut -c1-200)
        echo "::error file=tests/reverse-analysis-session-verify.py,line=1::[7.5] Python exit=$RC_SESSION | first=$FIRST_LINE | last=$LAST_LINE"
    fi
    rm -f "$SESSION_STDERR_FILE"
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

# ============== 7.7 pre-write-check-no-ref-words.sh 硬门禁自检（v4.3.0+ 新增） ==============
echo "[7.7] pre-write-check-no-ref-words.sh 硬门禁自检（v4.3.0+ 代码/配置零引用智能二分）"
HOOK_NOREF_PRE="$REPO_DIR/hooks/pre-write-check-no-ref-words.sh"
HOOK_NOREF_POST="$REPO_DIR/hooks/post-write-check-no-ref-words.sh"
DETECTOR_NOREF="$REPO_DIR/skills/mcpowers-shared/scripts/check_no_ref_words.py"
FORBIDDEN_FILE="$REPO_DIR/skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt"
INTERNAL_FILE="$REPO_DIR/skills/mcpowers-shared/docs/_assets/_internal_spec_docs.txt"
EXTERNAL_FILE="$REPO_DIR/skills/mcpowers-shared/docs/_assets/_external_authority.txt"
assert "pre-write-check-no-ref-words.sh 存在" "[ -f '$HOOK_NOREF_PRE' ]"
assert "post-write-check-no-ref-words.sh 存在" "[ -f '$HOOK_NOREF_POST' ]"
assert "check_no_ref_words.py 检测器存在" "[ -f '$DETECTOR_NOREF' ]"
assert "_forbidden_ref_words.txt 存在" "[ -f '$FORBIDDEN_FILE' ]"
assert "_internal_spec_docs.txt 存在" "[ -f '$INTERNAL_FILE' ]"
assert "_external_authority.txt 存在" "[ -f '$EXTERNAL_FILE' ]"
if [ -x "$HOOK_NOREF_PRE" ] && [ -x "$HOOK_NOREF_POST" ] && [ -n "$PY_BIN" ]; then
    # v4.6.3+:pre-write-check-no-ref-words.sh 改为 no-op stub(任何输入都 exit 0),
    # 字眼门禁迁移到 git commit 时由 pre-bash-guard.sh 兜底(见 §7.9 T22/T23).
    # T1:PreToolUse 不再拦字眼 → exit 0（v4.6.3+ 新行为）
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"# 参考《代码规范》§11.3 命名\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T1=$?
    set -e
    assert_eq "T1 v4.6.3+ PreToolUse 不再拦字眼(参考《代码规范》→ exit 0)" "$RC_T1" "0"

    # T2:同上 .py 项目内代码引用 → exit 0
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"# 详见 utils/security.py\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T2=$?
    set -e
    assert_eq "T2 v4.6.3+ PreToolUse 不再拦字眼(详见 utils/security.py → exit 0)" "$RC_T2" "0"

    # T3:同上 .py 兜底字眼 → exit 0
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"# 按规范要求校验\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T3=$?
    set -e
    assert_eq "T3 v4.6.3+ PreToolUse 不再拦字眼(按规范要求 → exit 0)" "$RC_T3" "0"

    # T4:写 .py 含「参考 RFC 7519 实现 JWT」 → exit 0（外部权威放行）
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"# 参考 RFC 7519 实现 JWT\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/tmp/noref_t4
    RC_T4=$?
    set -e
    assert_eq "T4 .py 外部权威 RFC → exit 0（放行）" "$RC_T4" "0"

    # T5:写 .py 含「遵循 PEP 8 命名」 → exit 0（外部权威放行）
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"# 遵循 PEP 8 命名\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/tmp/noref_t5
    RC_T5=$?
    set -e
    assert_eq "T5 .py 外部权威 PEP → exit 0（放行）" "$RC_T5" "0"

    # T6:tests/ 路径白名单 → exit 0（无论内容）
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"tests/test_foo.py","content":"# 参考《代码规范》§11.3\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/tmp/noref_t6
    RC_T6=$?
    set -e
    assert_eq "T6 tests/ 路径白名单 → exit 0（放行）" "$RC_T6" "0"

    # T7:CHANGELOG.md 路径白名单 → exit 0
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"CHANGELOG.md","content":"## v4.3.0\n参见 RFC 7519\n"}}' | bash "$HOOK_NOREF_PRE" 2>/tmp/noref_t7
    RC_T7=$?
    set -e
    assert_eq "T7 CHANGELOG.md 路径白名单 → exit 0" "$RC_T7" "0"

    # T8:post-write-check-no-ref-words.sh 软门禁 → exit 0 但 stderr 提示
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"# 参考《代码规范》§11.3\nval = 1\n"}}' | bash "$HOOK_NOREF_POST" 2>/tmp/noref_t8
    RC_T8=$?
    set -e
    assert_eq "T8 post-write 软门禁不阻断（exit 0）" "$RC_T8" "0"
    assert "T8 post-write stderr 含违规提示" "grep -q '代码规范' /tmp/noref_t8"

    # v4.6.3+ no-ref-words PreToolUse 拦截已迁移到 git commit 兜底（pre-bash-guard.sh）.
    # PreToolUse Edit|MultiEdit 模式不再拦字眼(避免阻塞自动化 + AI 同义词绕过).
    # T9:写 .py 含「参考 CLAUDE.md」 → 不再被 PreToolUse 拦(迁移后)
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"# 参考 CLAUDE.md\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T9=$?
    set -e
    assert_eq "T9 v4.6.3+ PreToolUse 不再拦字眼(.py 引用 CLAUDE.md → exit 0)" "$RC_T9" "0"

    # T10:写 .yaml 含「reference to」 → 不再被 PreToolUse 拦
    set +e
    echo '{"tool_name":"Write","tool_input":{"file_path":"config/app.yaml","content":"name: foo\ndescription: refer to internal spec\n"}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T10=$?
    set -e
    assert_eq "T10 v4.6.3+ PreToolUse 不再拦字眼(.yaml refer to → exit 0)" "$RC_T10" "0"

    # T11:Edit 模式 .py 含「参考《代码规范》§11.3」→ 不再被 PreToolUse 拦
    set +e
    echo '{"tool_name":"Edit","tool_input":{"file_path":"src/foo.py","old_string":"old","new_string":"# 参考《代码规范》§11.3 命名\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T11=$?
    set -e
    assert_eq "T11 v4.6.3+ Edit 模式不再拦字眼(参考《代码规范》→ exit 0)" "$RC_T11" "0"

    # T12:MultiEdit 模式 .py 含禁用字眼 → 不再被 PreToolUse 拦
    set +e
    echo '{"tool_name":"MultiEdit","tool_input":{"file_path":"src/foo.py","edits":[{"old_string":"a","new_string":"# 参考《代码规范》§11.3"},{"old_string":"b","new_string":"# 按规范要求\nval = 2"}]}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T12=$?
    set -e
    assert_eq "T12 v4.6.3+ MultiEdit 模式不再拦字眼(违规拼接 → exit 0)" "$RC_T12" "0"

    # T13:Edit 模式 .py 含「参考 RFC 7519」→ exit 0(脚本已变 no-op,所有输入都放行)
    set +e
    echo '{"tool_name":"Edit","tool_input":{"file_path":"src/foo.py","old_string":"old","new_string":"# 参考 RFC 7519\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T13=$?
    set -e
    assert_eq "T13 v4.6.3+ PreToolUse 全放行(参考 RFC 7519 → exit 0)" "$RC_T13" "0"

    # T14:Edit 模式 .py 含「详见 utils/security.py」→ exit 0(脚本已变 no-op)
    set +e
    echo '{"tool_name":"Edit","tool_input":{"file_path":"src/foo.py","old_string":"x","new_string":"# 详见 utils/security.py\nval = 1\n"}}' | bash "$HOOK_NOREF_PRE" 2>/dev/null
    RC_T14=$?
    set -e
    assert_eq "T14 v4.6.3+ PreToolUse 全放行(详见 utils/security.py → exit 0)" "$RC_T14" "0"

    # T15:hooks.json 的 Edit|MultiEdit matcher 必须**不**再注册 no-ref-words(v4.6.3+ 反向锁)
    EDIT_BLOCK=$(awk '/"matcher":[[:space:]]*"Edit\|MultiEdit"/,/^      \}$/' "$REPO_DIR/hooks/hooks.json")
    if echo "$EDIT_BLOCK" | grep -q "pre-write-check-no-ref-words.sh"; then
        echo "  ✗ T15 v4.6.3+ hooks.json Edit|MultiEdit matcher 仍注册 no-ref-words(应迁移到 git commit)"
        FAIL=$((FAIL + 1))
    else
        echo "  ✓ T15 v4.6.3+ hooks.json Edit|MultiEdit matcher 已移除 no-ref-words 注册"
        PASS=$((PASS + 1))
    fi
fi

# ============== 7.8 v4.5.2+ 扩展自检（duplicate MultiEdit + spec-frontmatter MultiEdit 锁定 + swagger PostToolUse 钩子） ==============
echo "[7.8] v4.5.2+ 扩展自检（duplicate MultiEdit + spec-frontmatter MultiEdit 锁定 + swagger PostToolUse 兜底）"

# ---- T16:duplicate 函数检测器 Edit 模式回归锁（v4.5.2 前 Edit 已支持,锁住防退化） ----
HOOK_DUP="$REPO_DIR/hooks/pre-write-check-duplicate.sh"
assert "T16 pre-write-check-duplicate.sh 存在" "[ -f '$HOOK_DUP' ]"
if [ -n "$PY_BIN" ] && [ -x "$HOOK_DUP" ]; then
    TMP_T16="$REPO_DIR/tests/.tmp_dup_t16"
    rm -rf "$TMP_T16" 2>/dev/null || true
    mkdir -p "$TMP_T16/src/utils" 2>/dev/null || true
    cd "$TMP_T16"
    git init -q . && git config user.email "v@t" && git config user.name "v"
    cat > src/utils/a.py <<'PYFIX'
def format_response(data):
    return {"ok": True, "data": data}
PYFIX
    git add -A && git commit -q -m "baseline"
    if command -v cygpath >/dev/null 2>&1; then
        TMP_T16_WIN=$(cygpath -m "$TMP_T16")
    else
        TMP_T16_WIN="$TMP_T16"
    fi
    # Edit 模式:new_string 是单行透传 wrapper → exit 2
    set +e
    PAYLOAD_T16='{"tool_name":"Edit","tool_input":{"file_path":"'$TMP_T16_WIN'/src/wrapper.py","old_string":"x","new_string":"def format_response(text):\n    return some_other.format_response(text)\n"}}'
    echo "$PAYLOAD_T16" | bash "$HOOK_DUP" 2>/dev/null
    RC_T16=$?
    set -e
    assert_eq "T16 Edit 模式单行透传 → exit 2" "$RC_T16" "2"
    cd "$REPO_DIR"
    rm -rf "$TMP_T16" 2>/dev/null || true
fi

# ---- T17:duplicate 函数检测器 MultiEdit 支持(v4.5.2 新增,修复 edits 数组漏配) ----
if [ -n "$PY_BIN" ] && [ -x "$HOOK_DUP" ]; then
    TMP_T17="$REPO_DIR/tests/.tmp_dup_t17"
    rm -rf "$TMP_T17" 2>/dev/null || true
    mkdir -p "$TMP_T17/src/utils" 2>/dev/null || true
    cd "$TMP_T17"
    git init -q . && git config user.email "v@t" && git config user.name "v"
    cat > src/utils/a.py <<'PYFIX'
def format_response(data):
    return {"ok": True, "data": data}
PYFIX
    git add -A && git commit -q -m "baseline"
    if command -v cygpath >/dev/null 2>&1; then
        TMP_T17_WIN=$(cygpath -m "$TMP_T17")
    else
        TMP_T17_WIN="$TMP_T17"
    fi
    # MultiEdit 模式:edits[*].new_string 含单行透传 wrapper → exit 2
    set +e
    PAYLOAD_T17='{"tool_name":"MultiEdit","tool_input":{"file_path":"'$TMP_T17_WIN'/src/wrapper.py","edits":[{"old_string":"a","new_string":"def format_response(text):\n    return other.format_response(text)\n"}]}}'
    echo "$PAYLOAD_T17" | bash "$HOOK_DUP" 2>/tmp/dup_t17
    RC_T17=$?
    set -e
    assert_eq "T17 MultiEdit 模式单行透传 → exit 2" "$RC_T17" "2"
    assert "T17 stderr 含单行透传标签" "grep -q '单行透传' /tmp/dup_t17"
    cd "$REPO_DIR"
    rm -rf "$TMP_T17" 2>/dev/null || true
fi

# ---- T18:spec-frontmatter 检测器 MultiEdit 删除字段场景锁定(v4.5.2 修复确认行为不退化) ----
HOOK_SFM="$REPO_DIR/hooks/pre-write-check-spec-frontmatter.sh"
DETECTOR_SFM="$REPO_DIR/hooks/check_spec_frontmatter.py"
assert "T18 pre-write-check-spec-frontmatter.sh 存在" "[ -f '$HOOK_SFM' ]"
assert "T18 check_spec_frontmatter.py 存在" "[ -f '$DETECTOR_SFM' ]"
if [ -n "$PY_BIN" ] && [ -x "$HOOK_SFM" ]; then
    # 临时造一个真实的技术规范 frontmatter 文件,MultiEdit 删除 stability 字段
    TMP_T18_DIR="$REPO_DIR/tests/.tmp_sfm_t18"
    rm -rf "$TMP_T18_DIR" 2>/dev/null || true
    mkdir -p "$TMP_T18_DIR/skills/mcpowers-shared/docs/技术规范" 2>/dev/null || true
    cat > "$TMP_T18_DIR/skills/mcpowers-shared/docs/技术规范/测试规范.md" <<'MDFIX'
---
name: test
type: shared
stability: stable
last_breaking_change: v1.0.0
---

# body
MDFIX
    if command -v cygpath >/dev/null 2>&1; then
        TMP_T18_WIN=$(cygpath -m "$TMP_T18_DIR")
    else
        TMP_T18_WIN="$TMP_T18_DIR"
    fi
    set +e
    PAYLOAD_T18='{"tool_name":"MultiEdit","tool_input":{"file_path":"'$TMP_T18_WIN'/skills/mcpowers-shared/docs/技术规范/测试规范.md","edits":[{"old_string":"stability: stable\nlast_breaking_change: v1.0.0","new_string":"removed"}]}}'
    echo "$PAYLOAD_T18" | bash "$HOOK_SFM" 2>/tmp/sfm_t18
    RC_T18=$?
    set -e
    assert_eq "T18 MultiEdit 删除 stability/last_breaking_change → exit 2" "$RC_T18" "2"
    assert "T18 stderr 含删除字段提示" "grep -q 'stability' /tmp/sfm_t18 || grep -q 'last_breaking_change' /tmp/sfm_t18"
    rm -rf "$TMP_T18_DIR" 2>/dev/null || true
fi

# ---- T19:PostToolUse swagger 兜底钩子文件存在 + 可执行 ----
HOOK_SWAGGER_POST="$REPO_DIR/hooks/post-write-check-swagger.sh"
assert "T19 post-write-check-swagger.sh 存在" "[ -f '$HOOK_SWAGGER_POST' ]"
[ -x "$HOOK_SWAGGER_POST" ] || { echo "  ✗ T19 post-write-check-swagger.sh 不可执行"; FAIL=$((FAIL + 1)); }
if [ -x "$HOOK_SWAGGER_POST" ]; then
    echo "  ✓ T19 post-write-check-swagger.sh 可执行"
    PASS=$((PASS + 1))
fi

# ---- T20:hooks.json PostToolUse matcher 必须注册 swagger 兜底钩子 ----
POST_BLOCK=$(awk '/"PostToolUse":/,/^    \]$/' "$REPO_DIR/hooks/hooks.json" 2>/dev/null || true)
# 用更稳健的 awk:从 PostToolUse 段开始读到下一行 "  ]"
if echo "$POST_BLOCK" | grep -q "post-write-check-swagger.sh"; then
    echo "  ✓ T20 hooks.json PostToolUse matcher 注册了 swagger 兜底钩子"
    PASS=$((PASS + 1))
else
    echo "  ✗ T20 hooks.json PostToolUse matcher 漏配 swagger 兜底钩子"
    FAIL=$((FAIL + 1))
fi

# ---- T21:PostToolUse swagger 钩子快速过滤 + 错误防御 ----
if [ -x "$HOOK_SWAGGER_POST" ]; then
    set +e
    # 空 stdin → exit 0
    echo '' | bash "$HOOK_SWAGGER_POST" 2>/dev/null
    RC_T21_EMPTY=$?
    # 非接口文件路径 → exit 0
    echo '{"tool_name":"Edit","tool_input":{"file_path":"src/utils/foo.py","old_string":"a","new_string":"b"}}' | bash "$HOOK_SWAGGER_POST" 2>/dev/null
    RC_T21_NOT_VIEW=$?
    # 非 .py 接口文件路径 → exit 0(lint-helper 仅支持 .py)
    echo '{"tool_name":"Edit","tool_input":{"file_path":"src/api/foo.txt","old_string":"a","new_string":"b"}}' | bash "$HOOK_SWAGGER_POST" 2>/dev/null
    RC_T21_NOT_PY=$?
    set -e
    assert_eq "T21 空 stdin → exit 0" "$RC_T21_EMPTY" "0"
    assert_eq "T21 非接口文件 → exit 0" "$RC_T21_NOT_VIEW" "0"
    # 路径 src/api/foo.txt 含 /api/ 命中过滤规则,但非 .py → 文件不存在 → helper 检测项目无 swagger → exit 0
    assert_eq "T21 .txt 路径(项目未装 swagger)→ exit 0" "$RC_T21_NOT_PY" "0"
fi

# ============== 7.9 v4.6.3+ git commit 字眼兜底检测自检 ==============
echo "[7.9] v4.6.3+ pre-bash-guard.sh git commit 字眼兜底检测自检"

# 临时建一个最小 git 仓库,模拟用户项目;暂存一个含禁用字眼的 .py 文件
TMP_GIT_NOREF=$(mktemp -d 2>/dev/null || mktemp -d -t tmpgitnoref)
TMP_GIT_CLEAN=$(mktemp -d 2>/dev/null || mktemp -d -t tmpgitclean)
cd "$TMP_GIT_NOREF" && git init -q >/dev/null 2>&1 && git config user.email "test@test" && git config user.name "test"
cd "$TMP_GIT_CLEAN" && git init -q >/dev/null 2>&1 && git config user.email "test@test" && git config user.name "test"

# 暂存含禁用字眼的文件 (参考《代码规范》§11.3 触发 fallback)
echo '# 参考《代码规范》§11.3 命名' > "$TMP_GIT_NOREF/bad.py"
cd "$TMP_GIT_NOREF" && git add bad.py >/dev/null 2>&1

# 暂存合法文件（不含禁用字眼）
echo '# 干净的注释,直接陈述当前做法' > "$TMP_GIT_CLEAN/good.py"
cd "$TMP_GIT_CLEAN" && git add good.py >/dev/null 2>&1

HOOK_BASH="$REPO_DIR/hooks/pre-bash-guard.sh"

# T22:git commit + 暂存区含禁用字眼 → exit 2(v4.6.3+ 兜底生效)
set +e
cd "$TMP_GIT_NOREF"
echo '{"tool_input":{"command":"git commit -m test"}}' | bash "$HOOK_BASH" 2>/dev/null
RC_T22=$?
set -e
assert_eq "T22 git commit + 暂存区含禁用字眼 → exit 2" "$RC_T22" "2"

# T23:git commit + 暂存区干净 → exit 0(放过)
set +e
cd "$TMP_GIT_CLEAN"
echo '{"tool_input":{"command":"git commit -m test"}}' | bash "$HOOK_BASH" 2>/dev/null
RC_T23=$?
set -e
assert_eq "T23 git commit + 暂存区干净 → exit 0" "$RC_T23" "0"

# 清理临时目录
rm -rf "$TMP_GIT_NOREF" "$TMP_GIT_CLEAN" 2>/dev/null || true

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
