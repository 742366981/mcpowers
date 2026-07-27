#!/usr/bin/env bash
# mcpowers README ↔ 实际状态同步校验
# 用途：CI 跑完所有断言无失败即视为文档与代码同步
# 退出码 0 = 同步，1 = 不同步
#
# 检查 12 类一致性：
#   1. README 路由表 ↔ 实际 skills/ 目录
#   2. README 规范清单 ↔ 实际 docs/ 下的规范文件
#   3. 每个规范文件有 frontmatter type: 字段
#   4. 每个场景技能有 ## 编排 段
#   5. 插件版本号三处一致（plugin.json / marketplace.json / plugins[0]）
#   6. 技能 description 字符数 ≤ 800（防 1024c 截断）
#   7. README / CLAUDE.md 中声明的技能/规范/Hook 数与实际一致
#   8. 路由器 + 规范库入口 的技能/规范数声明一致性（v2.9.0 L1 强化）
#   9. 跨文件技能引用一致性（无悬空引用）（v2.9.0 L1 强化）
#  10. crawler-reverse 真实可用性验收门禁完整性（v2.12.0）
#  11. reverse 分层拓扑与公共合同完整性（v2.13.0）
#  12. 浏览器/CDP 外部资源所有权门禁（v2.13.0）
#
# v2.9.0：新增 section 8/9
# v2.5.2：新增 section 5/6/7
# v2.0： 适配扁平化 skills/ 结构（删除 scene/method 分层）

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Windows 兼容：Git Bash 返回 POSIX 路径 /d/...，Windows 原生 Python 需要 D:\...
if command -v cygpath >/dev/null 2>&1; then
    REPO_DIR_WIN=$(cygpath -w "$REPO_DIR")
else
    REPO_DIR_WIN="$REPO_DIR"
fi
README="$REPO_DIR/README.md"
CLAUDE_MD="$REPO_DIR/CLAUDE.md"
FAIL=0

# 优先使用可执行的 python3；Windows Store 占位命令可能存在但不可用，需回退到 python
if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
    PY_BIN="python"
else
    PY_BIN=""
fi

# ============== 1. 技能清单同步 ==============
echo "[1/12] 校验 README ↔ skills/ 同步"
README_SKILLS=$(grep -oE 'mcpowers-[a-zA-Z-]+' "$README" 2>/dev/null | sort -u || true)
# v2.0：扁平结构，直接列 skills/ 下所有目录（mcpowers-* 前缀）
ACTUAL_SKILLS=$(ls "$REPO_DIR/skills" 2>/dev/null | grep '^mcpowers-' | sort -u)

for s in $ACTUAL_SKILLS; do
    if ! echo "$README_SKILLS" | grep -qx "$s" 2>/dev/null; then
        echo "  ✗ README 缺少技能: $s"
        FAIL=$((FAIL + 1))
    fi
done

# 反向：README 有但实际不存在的（可能是文档笔误）
for s in $README_SKILLS; do
    # mcpowers-spec-index 是规范库子目录，不是 skills/ 顶层技能目录。
    if [ "$s" = "mcpowers-spec-index" ]; then
        continue
    fi
    if ! echo "$ACTUAL_SKILLS" | grep -qx "$s" 2>/dev/null; then
        echo "  ⚠ README 提到但实际不存在: $s（可能是文档笔误）"
        # 警告而非错误（README 可能引用历史技能名）
    fi
done

if [ "$FAIL" -eq 0 ]; then
    echo "  ✓ 技能清单同步"
fi

# ============== 2. 规范清单同步 ==============
echo "[2/12] 校验 README ↔ docs/ 规范同步"
README_SPECS=$(grep -oE '[A-Za-z一-龥]+规范\.md' "$README" 2>/dev/null | sort -u || true)
# v2.0：mcpowers-shared 移到 skills/mcpowers-shared/
ACTUAL_SPECS=$(find "$REPO_DIR/skills/mcpowers-shared/docs" -name "*规范.md" 2>/dev/null | xargs -n1 basename 2>/dev/null | sort -u)

MISSING_SPEC=0
for s in $ACTUAL_SPECS; do
    if ! echo "$README_SPECS" | grep -qxF "$s" 2>/dev/null; then
        echo "  ✗ README 缺少规范: $s"
        MISSING_SPEC=$((MISSING_SPEC + 1))
    fi
done

if [ "$MISSING_SPEC" -eq 0 ]; then
    echo "  ✓ 规范清单同步"
else
    FAIL=$((FAIL + MISSING_SPEC))
fi

# ============== 3. 规范 frontmatter 完整性 ==============
# 只检查 技术规范/ 子目录（24 个核心规范范围，AI操作规范和产品设计规范不在范围）
echo "[3/12] 校验 24 个核心规范 frontmatter 完整性"
# v2.0：路径更新
SPEC_FILES=$(find "$REPO_DIR/skills/mcpowers-shared/docs/技术规范" -name "*规范.md" 2>/dev/null)
MISSING_FM=0
# 用 while + read 避免路径空格被 word splitting
while IFS= read -r f; do
    if ! head -10 "$f" | grep -q "^type:" 2>/dev/null; then
        echo "  ✗ 缺 frontmatter: $f"
        MISSING_FM=$((MISSING_FM + 1))
    fi
done <<< "$SPEC_FILES"

if [ "$MISSING_FM" -eq 0 ]; then
    echo "  ✓ 全部核心规范有 frontmatter"
else
    FAIL=$((FAIL + MISSING_FM))
fi

# ============== 4. 场景技能都有 ## 编排 段 ==============
# v2.0：场景技能 = skills/ 下非方法类的 mcpowers-* 技能
#   硬编码场景技能列表（原 skills/scene/*）
echo "[4/12] 校验场景技能都有 ## 编排 段"
SCENE_SKILLS="mcpowers-feat mcpowers-bugfix mcpowers-refactor mcpowers-optimize mcpowers-deploy mcpowers-requirement-change mcpowers-init mcpowers-git-commit mcpowers-git-worktree mcpowers-git-rollback mcpowers-git-cleanBranches mcpowers-autoTest mcpowers-api-contract mcpowers-install-basics-skills mcpowers-crawler-reverse mcpowers-reverse-web mcpowers-reverse-app mcpowers-reverse-android mcpowers-reverse-ios mcpowers-reverse-flutter mcpowers-reverse-hybrid mcpowers-reverse-miniprogram mcpowers-extract"
MISSING_ORCH=0
for s in $SCENE_SKILLS; do
    f="$REPO_DIR/skills/$s/SKILL.md"
    if [ ! -f "$f" ]; then
        echo "  ✗ 场景技能不存在: $s"
        MISSING_ORCH=$((MISSING_ORCH + 1))
        continue
    fi
    if ! grep -q "^## 编排" "$f" 2>/dev/null; then
        echo "  ✗ 缺 ## 编排 段: $s"
        MISSING_ORCH=$((MISSING_ORCH + 1))
    fi
done

if [ "$MISSING_ORCH" -eq 0 ]; then
    echo "  ✓ 全部场景技能有 ## 编排 段"
else
    FAIL=$((FAIL + MISSING_ORCH))
fi

# ============== 5. 插件版本号三处一致 ==============
# v2.5.2：保证 plugin.json.version / marketplace.json.version / marketplace.json.plugins[0].version 三处同步
echo "[5/12] 校验插件版本号三处一致"
if [ -n "$PY_BIN" ]; then
    PLUGIN_V=$($PY_BIN -c "import json; print(json.load(open(r'$REPO_DIR_WIN/.claude-plugin/plugin.json', encoding='utf-8'))['version'])" 2>/dev/null || echo "")
    MARKET_V=$($PY_BIN -c "import json; print(json.load(open(r'$REPO_DIR_WIN/.claude-plugin/marketplace.json', encoding='utf-8'))['version'])" 2>/dev/null || echo "")
    PLUGIN_ENTRY_V=$($PY_BIN -c "import json; print(json.load(open(r'$REPO_DIR_WIN/.claude-plugin/marketplace.json', encoding='utf-8'))['plugins'][0]['version'])" 2>/dev/null || echo "")
else
    # 无 Python 时用 grep 解析 JSON（仅做宽松匹配）
    PLUGIN_V=$(grep -oE '"version"[[:space:]]*:[[:space:]]*"[0-9]+\.[0-9]+\.[0-9]+"' "$REPO_DIR/.claude-plugin/plugin.json" | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    MARKET_V=$(grep -oE '"version"[[:space:]]*:[[:space:]]*"[0-9]+\.[0-9]+\.[0-9]+"' "$REPO_DIR/.claude-plugin/marketplace.json" | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    PLUGIN_ENTRY_V=$(awk '/"plugins":/{flag=1} flag && /"version"[[:space:]]*:[[:space:]]*"[0-9]+\.[0-9]+\.[0-9]+"/{print; exit}' "$REPO_DIR/.claude-plugin/marketplace.json" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
fi

if [ "$PLUGIN_V" = "$MARKET_V" ] && [ "$MARKET_V" = "$PLUGIN_ENTRY_V" ] && [ -n "$PLUGIN_V" ]; then
    echo "  ✓ 三处版本号一致: $PLUGIN_V"
else
    echo "  ✗ 版本号不一致: plugin.json=$PLUGIN_V, marketplace.json=$MARKET_V, plugins[0]=$PLUGIN_ENTRY_V"
    FAIL=$((FAIL + 1))
fi

# ============== 6. 技能 description 字符数 ==============
# v2.5.2：硬约束 ≤ 800 字符（1024 字符硬上限的 80% 安全预算）
echo "[6/12] 校验技能 description 字符数（≤800，防 1024c 截断）"
MAX_DESC_LEN=800
BAD_DESC=0
SKILL_DIRS=$(ls "$REPO_DIR/skills" 2>/dev/null | grep '^mcpowers')
for d in $SKILL_DIRS; do
    FILE="$REPO_DIR/skills/$d/SKILL.md"
    [ -f "$FILE" ] || continue
    if [ -n "$PY_BIN" ]; then
        DESC=$($PY_BIN -c "
import re, sys
try:
    c = open(r'$REPO_DIR_WIN/skills/$d/SKILL.md', encoding='utf-8').read()
    m = re.search(r'^---\n(.*?)\n---', c, re.DOTALL)
    if m:
        d_m = re.search(r'description:\s+(.+)', m.group(1))
        if d_m:
            print(len(d_m.group(1)))
            sys.exit(0)
    print(0)
except Exception:
    print(0)
" 2>/dev/null || echo "0")
    else
        # 无 Python 时用 awk 估算（基于 description 行长度）
        DESC=$(awk '/^---$/{c++; next} c==1 && /^description:[[:space:]]/{gsub(/^description:[[:space:]]*/, ""); print length($0); exit}' "$FILE" 2>/dev/null || echo "0")
    fi
    if [ -n "$DESC" ] && [ "$DESC" -gt "$MAX_DESC_LEN" ] 2>/dev/null; then
        echo "  ✗ description 超 ${MAX_DESC_LEN}c: $d ($DESC 字符)"
        BAD_DESC=$((BAD_DESC + 1))
    fi
done

if [ "$BAD_DESC" -eq 0 ]; then
    echo "  ✓ 全部技能 description ≤ ${MAX_DESC_LEN}c"
else
    FAIL=$((FAIL + BAD_DESC))
fi

# ============== 7. 文档数字一致性 ==============
# v2.5.2：README / CLAUDE.md 中"X 个技能/规范/Hook 脚本"声明必须与实际一致
#   技能数排除 mcpowers-shared（规范库）
echo "[7/12] 校验 README/CLAUDE.md 中声明的技能/规范/Hook 脚本数与实际一致"
ACTUAL_SKILL_N=$(echo "$ACTUAL_SKILLS" | grep -v '^mcpowers-shared$' | grep -c '^mcpowers' || true)
ACTUAL_SPEC_N=$(find "$REPO_DIR/skills/mcpowers-shared/docs/技术规范" -name "*规范.md" 2>/dev/null | wc -l | tr -d ' ')
ACTUAL_HOOK_N=$(find "$REPO_DIR/hooks" -maxdepth 1 -name "*.sh" -type f 2>/dev/null | wc -l | tr -d ' ')

# 提取文档中所有"总技能数/规范数/Hook 脚本数"声明
#   严格模式：只匹配修饰词白名单中的"X 个 Y"（避免误识别子集如"4 个 git 技能"）
DOC_NUM_FAIL=0

# --- 技能数：匹配 "X 个技能" / "X 个可路由技能" / "X 个场景/方法技能" / "X 个核心技能"
check_skill_decl() {
    local doc="$1"
    local label="$2"
    local actual="$3"
    # 模式：数字 + 个 + (可路由|核心|场景/方法)? + 技能
    # 排除 "X 个场景技能" / "X 个 git 技能" / "X 个方法技能" 等子集表述
    local decls
    decls=$(grep -oE '[0-9]+[[:space:]]*个[[:space:]]*(可路由|核心|场景/方法|场景与方法)?[[:space:]]*技能' "$doc" 2>/dev/null \
        | grep -oE '^[0-9]+' | sort -u || true)
    for n in $decls; do
        if [ "$n" != "$actual" ]; then
            echo "  ✗ $label 声明技能数 = $n，实际 = $actual"
            DOC_NUM_FAIL=$((DOC_NUM_FAIL + 1))
        fi
    done
}

# --- 规范数：匹配 "X 个技术规范" / "X 个核心规范"
check_spec_decl() {
    local doc="$1"
    local label="$2"
    local actual="$3"
    local decls
    decls=$(grep -oE '[0-9]+[[:space:]]*个[[:space:]]*(技术|核心)?[[:space:]]*规范' "$doc" 2>/dev/null \
        | grep -oE '^[0-9]+' | sort -u || true)
    for n in $decls; do
        if [ "$n" != "$actual" ]; then
            echo "  ✗ $label 声明规范数 = $n，实际 = $actual"
            DOC_NUM_FAIL=$((DOC_NUM_FAIL + 1))
        fi
    done
}

# --- Hook 脚本数：匹配 "X 个 Hook 脚本" 或 "事件组 / X 个脚本"
check_hook_decl() {
    local doc="$1"
    local label="$2"
    local actual="$3"
    # 匹配 "X 个 Hook 脚本"
    local d1
    d1=$(grep -oE '[0-9]+[[:space:]]*个[[:space:]]*Hook[[:space:]]*脚本' "$doc" 2>/dev/null \
        | grep -oE '^[0-9]+' | sort -u || true)
    # 匹配 "事件组 / X 个脚本"（包含括号或斜杠后的脚本数）
    local d2
    d2=$(grep -oE '事件组[[:space:]]*/[[:space:]]*[0-9]+[[:space:]]*个[[:space:]]*脚本' "$doc" 2>/dev/null \
        | grep -oE '[0-9]+' | sort -u || true)
    # 去重合并
    local decls
    decls=$(printf '%s\n%s\n' "$d1" "$d2" | grep -E '^[0-9]+$' | sort -u || true)
    for n in $decls; do
        if [ "$n" != "$actual" ]; then
            echo "  ✗ $label 声明 Hook 脚本数 = $n，实际 = $actual"
            DOC_NUM_FAIL=$((DOC_NUM_FAIL + 1))
        fi
    done
}

# 校验所有文档
check_skill_decl "$README"    "README"    "$ACTUAL_SKILL_N"
check_skill_decl "$CLAUDE_MD" "CLAUDE.md" "$ACTUAL_SKILL_N"

check_spec_decl "$README"     "README"    "$ACTUAL_SPEC_N"
check_spec_decl "$CLAUDE_MD"  "CLAUDE.md" "$ACTUAL_SPEC_N"

check_hook_decl "$README"     "README"    "$ACTUAL_HOOK_N"
check_hook_decl "$CLAUDE_MD"  "CLAUDE.md" "$ACTUAL_HOOK_N"

if [ "$DOC_NUM_FAIL" -eq 0 ]; then
    echo "  ✓ 文档数字声明 = 实际（技能 $ACTUAL_SKILL_N / 规范 $ACTUAL_SPEC_N / Hook 脚本 $ACTUAL_HOOK_N）"
else
    FAIL=$((FAIL + DOC_NUM_FAIL))
fi

# ============== 8. 路由器 + 规范库入口 数字一致性（v2.9.0 L1 强化） ==============
# v2.9.0：把 #7 的技能/规范/Hook 数校验从"只查 README + CLAUDE.md"扩展到
#   skills/mcpowers/SKILL.md (路由器本体) + skills/mcpowers-shared/SKILL.md (规范库入口)。
#   解决历史漏改：路由器说 "23 个可路由技能" 但 README/CLAUDE.md 已改成 24。
echo "[8/12] 校验 路由器/规范库入口 的技能/规范/Hook 脚本数声明"
ROUTER_SKILL="$REPO_DIR/skills/mcpowers/SKILL.md"
SHARED_SKILL="$REPO_DIR/skills/mcpowers-shared/SKILL.md"
DOC_NUM_FAIL2=0

# 复用 #7 的匹配规则，仅替换内部计数器为 DOC_NUM_FAIL2
check_skill_decl_router() {
    local doc="$1"; local label="$2"; local actual="$3"
    local decls
    decls=$(grep -oE '[0-9]+[[:space:]]*个[[:space:]]*(可路由|核心|场景/方法|场景与方法)?[[:space:]]*技能' "$doc" 2>/dev/null \
        | grep -oE '^[0-9]+' | sort -u || true)
    for n in $decls; do
        if [ "$n" != "$actual" ]; then
            echo "  ✗ $label 声明技能数 = $n，实际 = $actual"
            DOC_NUM_FAIL2=$((DOC_NUM_FAIL2 + 1))
        fi
    done
}
check_spec_decl_router() {
    local doc="$1"; local label="$2"; local actual="$3"
    local decls
    decls=$(grep -oE '[0-9]+[[:space:]]*个[[:space:]]*(技术|核心)?[[:space:]]*规范' "$doc" 2>/dev/null \
        | grep -oE '^[0-9]+' | sort -u || true)
    for n in $decls; do
        if [ "$n" != "$actual" ]; then
            echo "  ✗ $label 声明规范数 = $n，实际 = $actual"
            DOC_NUM_FAIL2=$((DOC_NUM_FAIL2 + 1))
        fi
    done
}
check_hook_decl_router() {
    local doc="$1"; local label="$2"; local actual="$3"
    local d1 d2
    d1=$(grep -oE '[0-9]+[[:space:]]*个[[:space:]]*Hook[[:space:]]*脚本' "$doc" 2>/dev/null \
        | grep -oE '^[0-9]+' | sort -u || true)
    d2=$(grep -oE '事件组[[:space:]]*/[[:space:]]*[0-9]+[[:space:]]*个[[:space:]]*脚本' "$doc" 2>/dev/null \
        | grep -oE '[0-9]+' | sort -u || true)
    local decls
    decls=$(printf '%s\n%s\n' "$d1" "$d2" | grep -E '^[0-9]+$' | sort -u || true)
    for n in $decls; do
        if [ "$n" != "$actual" ]; then
            echo "  ✗ $label 声明 Hook 脚本数 = $n，实际 = $actual"
            DOC_NUM_FAIL2=$((DOC_NUM_FAIL2 + 1))
        fi
    done
}

check_skill_decl_router "$ROUTER_SKILL"  "router" "$ACTUAL_SKILL_N"
check_skill_decl_router "$SHARED_SKILL" "shared" "$ACTUAL_SKILL_N"
check_spec_decl_router  "$ROUTER_SKILL"  "router" "$ACTUAL_SPEC_N"
check_spec_decl_router  "$SHARED_SKILL" "shared" "$ACTUAL_SPEC_N"
check_hook_decl_router  "$ROUTER_SKILL"  "router" "$ACTUAL_HOOK_N"

if [ "$DOC_NUM_FAIL2" -eq 0 ]; then
    echo "  ✓ 路由器/规范库入口数字声明与实际一致"
else
    FAIL=$((FAIL + DOC_NUM_FAIL2))
fi

# ============== 9. 跨文件技能引用一致性（v2.9.0 L1 强化） ==============
# v2.9.0：捕获"路由器调用 mcpowers-foo 但 mcpowers-foo 目录不存在"的悬空引用。
#   范围：所有 SKILL.md 里出现的 mcpowers-* 字面量都要在 skills/ 实际目录里存在。
echo "[9/12] 校验 跨文件技能引用一致性（无悬空引用）"
DANGLING_FAIL=0
DECLARED=$(ls "$REPO_DIR/skills" 2>/dev/null | grep '^mcpowers-' | sort -u)
# ripgrep: 所有 SKILL.md 里出现的 mcpowers-* 字面量。
#   regex 要求首字符是字母、尾字符是字母/数字，避免 `mcpowers-git-*` 通配符被截成 `mcpowers-git-`。
#   v2.9.5: --exclude-dir 跳过 __pycache__（避免 Python 编译缓存 .pyc 被 grep 当成二进制文件）。
REFERENCED=$(grep -rhoE 'mcpowers-[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]' \
    --exclude-dir=__pycache__ \
    --exclude='*.pyc' --exclude='*.pyo' \
    "$REPO_DIR/skills" 2>/dev/null \
    | sort -u || true)

# 引用合法性 3 条规则（任一满足即视为有效）：
#   1. 等于一个 DECLARED 的技能目录
#   2. 历史白名单（仅 2 个：mcpowers-spec-index / mcpowers-workflow）
#   3. 是 DECLARED 中某技能的严格前缀（ref + "-..." 出现在 DECLARED）
#      例：`mcpowers-git` 是 `mcpowers-git-commit` 等的前缀，文档中作为家族引用合法
for ref in $REFERENCED; do
    valid=0
    if echo "$DECLARED" | grep -qx "$ref" 2>/dev/null; then
        valid=1
    elif [ "$ref" = "mcpowers-spec-index" ] || [ "$ref" = "mcpowers-workflow" ]; then
        valid=1
    elif echo "$DECLARED" | grep -q "^${ref}-" 2>/dev/null; then
        valid=1
    fi
    if [ "$valid" -eq 0 ]; then
        echo "  ✗ 悬空引用: $ref（引用了不存在的技能目录）"
        DANGLING_FAIL=$((DANGLING_FAIL + 1))
    fi
done

if [ "$DANGLING_FAIL" -eq 0 ]; then
    echo "  ✓ 全部 mcpowers-* 引用都有对应目录"
else
    FAIL=$((FAIL + DANGLING_FAIL))
fi

# ============== 10. crawler-reverse 可用性验收门禁（v2.12.0） ==============
# 防止后续修改只保留模块骨架，却删除真实业务、生命周期和并发验收。
echo "[10/12] 校验 crawler-reverse 真实可用性验收门禁"
CRAWLER_SKILL="$REPO_DIR/skills/mcpowers-crawler-reverse/SKILL.md"
CRAWLER_GATE_FAIL=0

check_crawler_gate() {
    local pattern="$1"
    local label="$2"
    if ! grep -qF "$pattern" "$CRAWLER_SKILL" 2>/dev/null; then
        echo "  ✗ crawler-reverse 缺少: $label"
        CRAWLER_GATE_FAIL=$((CRAWLER_GATE_FAIL + 1))
    fi
}

check_crawler_gate "### 5.5 真实可用性验收" "阶段 5.5 可用性验收"
check_crawler_gate "verification-report.md" "统一验收报告产物"
check_crawler_gate '`single-use-token`' "一次性报文生命周期分类"
check_crawler_gate "按并发 **2 → 5** 递增" "有界并发 2 → 5"
check_crawler_gate '最终状态为 `PASS` 时' "阶段 7 PASS 前置门禁"
check_crawler_gate "最终交付形态（必须在阶段 1 确认）" "阶段 1 交付形态选择"
check_crawler_gate "### 4.1 RPC 逆向方式" "RPC 逆向实现方式"
check_crawler_gate "纯协议 / 半自动化 / 纯自动化" "三种最终交付形态"
check_crawler_gate "group/name" "RPC 运行时隔离标识"
check_crawler_gate "运行态存储边界" "半自动化/RPC 运行态存储边界"

if [ "$CRAWLER_GATE_FAIL" -eq 0 ]; then
    echo "  ✓ crawler-reverse 可用性验收门禁完整"
else
    FAIL=$((FAIL + CRAWLER_GATE_FAIL))
fi

# ============== 11. reverse 分层拓扑与公共合同（v2.13.0） ==============
echo "[11/12] 校验 reverse 分层拓扑与公共合同"
REVERSE_SKILLS="mcpowers-reverse-web mcpowers-reverse-app mcpowers-reverse-android mcpowers-reverse-ios mcpowers-reverse-flutter mcpowers-reverse-hybrid mcpowers-reverse-miniprogram"
REVERSE_TOPOLOGY_FAIL=0
ROUTER_SKILL="$REPO_DIR/skills/mcpowers/SKILL.md"

for s in $REVERSE_SKILLS; do
    f="$REPO_DIR/skills/$s/SKILL.md"
    if [ ! -f "$f" ]; then
        echo "  ✗ reverse 专项技能不存在: $s"
        REVERSE_TOPOLOGY_FAIL=$((REVERSE_TOPOLOGY_FAIL + 1))
        continue
    fi
    if ! grep -qF "公共前置合同" "$f" || ! grep -qF "公共收尾合同" "$f"; then
        echo "  ✗ $s 未引用统一入口的公共前置/收尾合同"
        REVERSE_TOPOLOGY_FAIL=$((REVERSE_TOPOLOGY_FAIL + 1))
    fi
    if grep -qF "### 5.5 真实可用性验收" "$f"; then
        echo "  ✗ $s 复制了公共阶段 5.5，应只引用统一入口"
        REVERSE_TOPOLOGY_FAIL=$((REVERSE_TOPOLOGY_FAIL + 1))
    fi
    if [ "$s" != "mcpowers-reverse-app" ] && grep -qE '^\|.*`mcpowers-reverse-' "$f" 2>/dev/null; then
        echo "  ✗ $s 的编排递归调用了其他逆向专项，应只读辅助规范并返回重新分流证据"
        REVERSE_TOPOLOGY_FAIL=$((REVERSE_TOPOLOGY_FAIL + 1))
    fi
    if ! grep -E '^\|' "$ROUTER_SKILL" 2>/dev/null | grep -qF "\`$s\`"; then
        echo "  ✗ 主路由表缺少 reverse 专项: $s"
        REVERSE_TOPOLOGY_FAIL=$((REVERSE_TOPOLOGY_FAIL + 1))
    fi
done

APP_ROUTER="$REPO_DIR/skills/mcpowers-reverse-app/SKILL.md"
for child in mcpowers-reverse-android mcpowers-reverse-ios mcpowers-reverse-flutter mcpowers-reverse-hybrid; do
    if ! grep -qF "$child" "$APP_ROUTER" 2>/dev/null; then
        echo "  ✗ App 二级入口缺少下游: $child"
        REVERSE_TOPOLOGY_FAIL=$((REVERSE_TOPOLOGY_FAIL + 1))
    fi
done

if [ "$REVERSE_TOPOLOGY_FAIL" -eq 0 ]; then
    echo "  ✓ reverse 分层拓扑与公共合同完整"
else
    FAIL=$((FAIL + REVERSE_TOPOLOGY_FAIL))
fi

# ============== 12. 浏览器/CDP 外部资源所有权（v2.13.0） ==============
echo "[12/12] 校验浏览器/CDP 外部资源所有权门禁"
BROWSER_OWNERSHIP_FAIL=0
CRAWLER_SPEC="$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫分析规范.md"
# v2.14.0：爬虫分析规范拆分为 7 册，铁律字符串同时存在于 4 个规范文件 + 3 个 reverse SKILL.md
CRAWLER_TOOLS_SPEC="$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫工具与抓包规范.md"
CRAWLER_WEB_SPEC="$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫Web逆向规范.md"
CRAWLER_MINIPGM_SPEC="$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫小程序逆向规范.md"
OWNERSHIP_FILES="$CRAWLER_SKILL
$REPO_DIR/skills/mcpowers-reverse-web/SKILL.md
$REPO_DIR/skills/mcpowers-reverse-hybrid/SKILL.md
$REPO_DIR/skills/mcpowers-reverse-miniprogram/SKILL.md
$CRAWLER_SPEC
$CRAWLER_TOOLS_SPEC
$CRAWLER_WEB_SPEC
$CRAWLER_MINIPGM_SPEC"

while IFS= read -r f; do
    [ -n "$f" ] || continue
    if [ ! -f "$f" ] || ! grep -qF "外部接管资源不可关闭" "$f" 2>/dev/null; then
        echo "  ✗ 缺少外部接管资源不可关闭铁律: $f"
        BROWSER_OWNERSHIP_FAIL=$((BROWSER_OWNERSHIP_FAIL + 1))
    fi
done <<< "$OWNERSHIP_FILES"

if grep -qF "browser.contexts[0] or browser.new_context()" "$CRAWLER_SPEC" 2>/dev/null; then
    echo "  ✗ 爬虫分析规范仍允许接管失败时静默新建 context"
    BROWSER_OWNERSHIP_FAIL=$((BROWSER_OWNERSHIP_FAIL + 1))
fi
if grep -qF "bb-browser daemon stop &&" "$CRAWLER_SPEC" 2>/dev/null; then
    echo "  ✗ 爬虫分析规范仍会无所有权判断地停止外部 daemon"
    BROWSER_OWNERSHIP_FAIL=$((BROWSER_OWNERSHIP_FAIL + 1))
fi
if grep -qF "关闭浏览器/App/RPC 后" "$CRAWLER_SKILL" 2>/dev/null; then
    echo "  ✗ 纯协议验收仍可能关闭用户浏览器，应改为停止依赖且保持外部资源存活"
    BROWSER_OWNERSHIP_FAIL=$((BROWSER_OWNERSHIP_FAIL + 1))
fi

if [ "$BROWSER_OWNERSHIP_FAIL" -eq 0 ]; then
    echo "  ✓ 浏览器/CDP 外部资源所有权门禁完整"
else
    FAIL=$((FAIL + BROWSER_OWNERSHIP_FAIL))
fi

# ============== 汇总 ==============
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "=== ✓ README ↔ 实际状态同步 ==="
    exit 0
else
    echo "=== ✗ $FAIL 项不一致 ==="
    exit 1
fi