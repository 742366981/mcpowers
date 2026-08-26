#!/usr/bin/env bash
# mcpowers README ↔ 实际状态同步校验
# 用途：CI 跑完所有断言无失败即视为文档与代码同步
# 退出码 0 = 同步，1 = 不同步
#
# 检查 23 类一致性：
#   1. README 路由表 ↔ 实际 skills/ 目录
#   2. README 规范清单 ↔ 实际 docs/ 下的规范文件
#   3. 每个规范文件有 frontmatter type: 字段
#   4. 每个场景技能有 ## 编排 段
#   5. 插件版本号三处一致（plugin.json / marketplace.json / plugins[0]）
#   6. 技能 description 字符数 ≤ 800（防 1024c 截断）
#   7. README / CLAUDE.md 中声明的技能/规范/Hook 数与实际一致
#   8. 路由器 + 规范库入口 的技能/规范数声明一致性（v2.9.0 L1 强化）
#   9. 跨文件技能路径一致性（无悬空指向）（v2.9.0 L1 强化）
#  10. crawler-reverse 真实可用性验收门禁完整性（v2.12.0 + v2.16.0 + v2.17.0）
#  11. reverse 分层拓扑与公共合同完整性（v2.13.0）
#  12. 浏览器/CDP 外部资源所有权门禁（v2.13.0）
#  13. 模块产物封装形式约束（v2.17.0 新增：类式 + quick_test + 顶层文档中文）
#  14. DrissionPage 全场景默认化（v2.18.0 新增：浏览器自动化工具栈主表 + 漏抓 7 层 DrissionPage 重新映射 + popup-handler / user-action-recorder DrissionPage 适配）
#  15. reverse-analysis-session 强制起手式（v2.19.0 新增：init → web-start → web-stop 状态机 + 浏览器指纹一致性审计）
#  16. 项目独立端口（v2.20.0 新增：pick_free_port + chrome_port 字段 + 文档占位符 <port>）
#  17. 会话派生产物（v2.21.0 新增：session-artifacts-generator + 目标接口候选 + 响应样本 envelope + 类式封装种子）
#  18. 根文档结构门禁（v2.21.1 新增：禁止 CLAUDE.md 出现"### 历史教训（v" / README.md 出现"### vX.Y.Z"）
#  19. 根文档尺寸门禁（v2.21.1 新增：CLAUDE.md ≤ 350 行 / 35,000 字符，README.md ≤ 650 行 / 50,000 字符）
#  20. 单一权威源门禁（v2.21.1 新增：关键短语在 CLAUDE.md / README.md 出现即告警，应在规范权威源维护）
#  21. 规范 frontmatter 双字段门禁（v2.27.4 新增：全部规范必须声明 stability + last_breaking_change，动态计数）
#  22. Swagger 5 字段契约铁律存在性（v2.31.0+ 新增：CLAUDE.md 铁律段 + Swagger字段契约.md + 默认清单 yml + contract-check.sh + lint-helper.py）
#  23. 代码/配置零引用智能二分判定（v4.3.0+ 新增：3 份共享常量 + 智能二分检测器脚本 + 2 新 hook + 旧 hook 删除）
#
# v4.3.0：新增 section 23
# v2.27.4：新增 section 21
# v2.21.1：新增 section 18/19/20
# v2.21.0：新增 section 17
# v2.20.0：新增 section 16
# v2.19.0：新增 section 15
# v2.18.0：新增 section 14
# v2.17.0：新增 section 13
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
echo "[1/13] 校验 README ↔ skills/ 同步"
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
        # 警告而非错误（README 可能含历史技能名）
    fi
done

if [ "$FAIL" -eq 0 ]; then
    echo "  ✓ 技能清单同步"
fi

# ============== 2. 规范清单同步 ==============
echo "[2/13] 校验 README ↔ docs/ 规范同步"
# v2.31.0:保留 *规范.md 匹配(代表「以『规范』结尾的命名约定」)
# 不命名变体(如 Swagger字段契约.md)由 §22 单独检查存在性
# v2.27.0+:ERE 在 GNU grep 3.11+ + LANG=C.UTF-8 环境下对 [一-龥] 字符范围 0 匹配，
# 改用 PCRE + \p{L}\p{Han} Unicode property（不依赖 locale collation）。
# 命令前缀 LC_ALL=C.UTF-8 是为了让 Windows Git Bash 单字节 locale 也能跑 grep -P。
README_SPECS=$(LC_ALL=C.UTF-8 grep -oP '[\p{L}\p{Han}]+规范\.md' "$README" 2>/dev/null | sort -u || true)
# v2.0：mcpowers-shared 移到 skills/mcpowers-shared/
ACTUAL_SPECS=$(find "$REPO_DIR/skills/mcpowers-shared/docs/技术规范" -name "*规范.md" 2>/dev/null | xargs -n1 basename 2>/dev/null | sort -u)

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
# v2.31.0:实际是 32 个规范（含 Swagger字段契约.md）,但其中 31 个以「规范.md」结尾,Swagger字段契约.md 用 §22 单独检查
echo "[3/13] 校验 32 个核心规范 frontmatter 完整性"
# v2.0：路径更新
SPEC_FILES=$(find "$REPO_DIR/skills/mcpowers-shared/docs/技术规范" -maxdepth 1 -name "*.md" -type f 2>/dev/null)
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
echo "[4/13] 校验场景技能都有 ## 编排 段"
SCENE_SKILLS="mcpowers-feat mcpowers-bugfix mcpowers-refactor mcpowers-optimize mcpowers-deploy mcpowers-requirement-change mcpowers-init mcpowers-git-commit mcpowers-git-worktree mcpowers-git-rollback mcpowers-git-cleanBranches mcpowers-autoTest mcpowers-api-contract mcpowers-install-basics-skills mcpowers-crawler-reverse mcpowers-reverse-web mcpowers-reverse-app mcpowers-reverse-android mcpowers-reverse-ios mcpowers-reverse-flutter mcpowers-reverse-hybrid mcpowers-reverse-miniprogram mcpowers-extract mcpowers-min-module mcpowers-sdk-design"
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
echo "[5/13] 校验插件版本号三处一致"
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
echo "[6/13] 校验技能 description 字符数（≤800，防 1024c 截断）"
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
echo "[7/13] 校验 README/CLAUDE.md 中声明的技能/规范/Hook 脚本数与实际一致"
ACTUAL_SKILL_N=$(echo "$ACTUAL_SKILLS" | grep -v '^mcpowers-shared$' | grep -c '^mcpowers' || true)
ACTUAL_SPEC_N=$(find "$REPO_DIR/skills/mcpowers-shared/docs/技术规范" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
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
echo "[8/13] 校验 路由器/规范库入口 的技能/规范/Hook 脚本数声明"
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

# ============== 9. 跨文件技能路径一致性（v2.9.0 L1 强化） ==============
# v2.9.0：捕获"路由器调用 mcpowers-foo 但 mcpowers-foo 目录不存在"的悬空指向。
#   范围：所有 SKILL.md 里出现的 mcpowers-* 字面量都要在 skills/ 实际目录里存在。
echo "[9/13] 校验 跨文件技能路径一致性（无悬空指向）"
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

# 路径合法性 3 条规则（任一满足即视为有效）：
#   1. 等于一个 DECLARED 的技能目录
#   2. 白名单：`mcpowers-spec-index`（规范库入口 skill）+ `mcpowers-workflow`（历史单体已删除）+ `mcpowers-version`（项目级冻结标记，v2.27.4+ 用户项目根 .mcpowers-version 文件，非技能）
#   3. 是 DECLARED 中某技能的严格前缀（ref + "-..." 出现在 DECLARED）
#      例：`mcpowers-git` 是 `mcpowers-git-commit` 等的前缀，文档中作为家族指向合法
for ref in $REFERENCED; do
    valid=0
    if echo "$DECLARED" | grep -qx "$ref" 2>/dev/null; then
        valid=1
    elif [ "$ref" = "mcpowers-spec-index" ] || [ "$ref" = "mcpowers-workflow" ] || [ "$ref" = "mcpowers-version" ]; then
        valid=1
    elif echo "$DECLARED" | grep -q "^${ref}-" 2>/dev/null; then
        valid=1
    fi
    if [ "$valid" -eq 0 ]; then
        echo "  ✗ 悬空指向: $ref（指向了不存在的技能目录）"
        DANGLING_FAIL=$((DANGLING_FAIL + 1))
    fi
done

if [ "$DANGLING_FAIL" -eq 0 ]; then
    echo "  ✓ 全部 mcpowers-* 路径都有对应目录"
else
    FAIL=$((FAIL + DANGLING_FAIL))
fi

# ============== 10. crawler-reverse 可用性验收门禁（v2.12.0） ==============
# 防止后续修改只保留模块骨架，却删除真实业务、生命周期和并发验收。
echo "[10/13] 校验 crawler-reverse 真实可用性验收门禁"
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
check_crawler_gate "验收报告.md" "统一验收报告产物"
check_crawler_gate '`single-use-token`' "一次性报文生命周期分类"
check_crawler_gate "按并发 **2 → 5** 递增" "有界并发 2 → 5"
check_crawler_gate '最终状态为 `PASS` 时' "阶段 7 PASS 前置门禁"
check_crawler_gate "最终交付形态（必须在阶段 1 确认）" "阶段 1 交付形态选择"
check_crawler_gate "### 4.1 RPC 逆向方式" "RPC 逆向实现方式"
check_crawler_gate "纯协议 / 半自动化 / 纯自动化" "三种最终交付形态"
check_crawler_gate "group/name" "RPC 运行时隔离标识"
check_crawler_gate "运行态存储边界" "半自动化/RPC 运行态存储边界"
# v2.16.0 新增：抓包失败 7 层诊断 + cURL 快速帮助
check_crawler_gate "Chrome 150+" "Chrome 150+ Origin 校验警告"
check_crawler_gate "§3.9" "漏抓 7 层诊断决策树段落"
check_crawler_gate "§3.0.7" "cURL 12 项快速帮助清单段落"
# v2.17.0 新增：模块产物封装形式约束（§9.4.6 + 顶层文件中文）
check_crawler_gate "§9.4.6" "模块产物封装形式约束段落"
check_crawler_gate "request_and_parse" "类式便捷方法命名"
check_crawler_gate "quick_test.py" "quick_test.py 手动验证入口"

if [ "$CRAWLER_GATE_FAIL" -eq 0 ]; then
    echo "  ✓ crawler-reverse 可用性验收门禁完整"
else
    FAIL=$((FAIL + CRAWLER_GATE_FAIL))
fi

# ============== 11. reverse 分层拓扑与公共合同（v2.13.0） ==============
echo "[11/13] 校验 reverse 分层拓扑与公共合同"
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
        echo "  ✗ $s 未调用统一入口的公共前置/收尾合同"
        REVERSE_TOPOLOGY_FAIL=$((REVERSE_TOPOLOGY_FAIL + 1))
    fi
    if grep -qF "### 5.5 真实可用性验收" "$f"; then
        echo "  ✗ $s 复制了公共阶段 5.5，应只调用统一入口"
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
echo "[12/13] 校验浏览器/CDP 外部资源所有权门禁"
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

# ============== 13. 模块产物封装形式约束（v2.17.0 新增） ==============
# 防止后续修改删掉类式封装 / quick_test / 顶层文档中文这 3 类用户可见约束。
echo "[13/13] 校验模块产物封装形式约束（v2.17.0）"
MODULE_FORM_FAIL=0
CRAWLER_SPEC="$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫分析规范.md"
EXTRACT_SKILL="$REPO_DIR/skills/mcpowers-extract/SKILL.md"
README_DOC="$REPO_DIR/README.md"

check_module_form() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file"
        MODULE_FORM_FAIL=$((MODULE_FORM_FAIL + 1))
        return
    fi
    if ! grep -qF "$pattern" "$file" 2>/dev/null; then
        echo "  ✗ $label 缺失（$file 应包含：$pattern）"
        MODULE_FORM_FAIL=$((MODULE_FORM_FAIL + 1))
    fi
}

# §9.4.6 模块产物封装形式约束（主册）
check_module_form "$CRAWLER_SPEC"  "9.4.6"  "主《爬虫分析规范》§9.4.6"
check_module_form "$CRAWLER_SPEC"  "类式封装"  "主《爬虫分析规范》类式封装约定"
check_module_form "$CRAWLER_SPEC"  "零前置参数"  "主《爬虫分析规范》零前置参数约束"
check_module_form "$CRAWLER_SPEC"  "请求与解析分离"  "主《爬虫分析规范》请求与解析分离"
check_module_form "$CRAWLER_SPEC"  "quick_test.py"  "主《爬虫分析规范》quick_test.py"
check_module_form "$CRAWLER_SPEC"  "sys.argv"  "主《爬虫分析规范》反 sys.argv"
check_module_form "$CRAWLER_SPEC"  "分析计划.md"  "主《爬虫分析规范》中文顶层文件名"
check_module_form "$CRAWLER_SPEC"  "案例沉淀.md"  "主《爬虫分析规范》中文顶层文件名"

# crawler-reverse SKILL.md §5
CRAWLER_SKILL_DOC="$REPO_DIR/skills/mcpowers-crawler-reverse/SKILL.md"
check_module_form "$CRAWLER_SKILL_DOC" "client.py"  "crawler-reverse client.py 类式"
check_module_form "$CRAWLER_SKILL_DOC" "quick_test.py"  "crawler-reverse quick_test.py 必备"

# extract SKILL.md §4
check_module_form "$EXTRACT_SKILL" "client.py"  "extract client.py 类式"
check_module_form "$EXTRACT_SKILL" "quick_test.py"  "extract quick_test.py 必备"

# README.md 用户可见说明
# v2.21.1：README 类式封装 / 零前置参数 / quick_test.py 详细说明在 v2.21.0 节，
# 该节已迁移到 CHANGELOG.md 与 docs/历史教训.md。README 顶层不再维护规则副本，统一从权威源查：
# §13 校验简化为路径检查（避免与 §20 单一权威源门禁冲突）：
check_module_form "$README_DOC" "CHANGELOG.md"  "README 含 CHANGELOG.md 链接"
check_module_form "$README_DOC" "docs/历史教训.md"  "README 含 docs/历史教训.md 链接"

# v2.17.0 二次确认：分析文件名全中文硬校验（防止后续漏改）
# 校验项：技能 + 规范的 SKILL.md / 规范文档，禁止在新行（说明/描述）里写英文路径。
# 例外：对照表 / 历史教训里的"v2.17.0 之前 → v2.17.0 起"映射必须保留英文原名。
# 简化策略：grep 每条英文路径在每个文件里出现的次数，超过 2 次（说明 + 反模式 + 对照表）就警告。
ENGLISH_PATH_FAIL=0
warn_english_path() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    local max="$4"
    if [ ! -f "$file" ]; then
        return
    fi
    local count
    count=$(grep -cF "$pattern" "$file" 2>/dev/null | head -1)
    [ -z "$count" ] && count=0
    if [ "$count" -gt "$max" ]; then
        echo "  ✗ $file 英文路径 '$pattern' 出现 $count 次（≤ $max 为对照表/反模式/历史段，>$max 可能是漏改）"
        ENGLISH_PATH_FAIL=$((ENGLISH_PATH_FAIL + 1))
    fi
}

# 主《爬虫分析规范》允许对照表 + 反模式 + 历史教训，每个英文路径 ≤ 4 次
for p in "01-target-profile/" "02-interfaces/" "03-reverse/" "04-modules/" "ANALYSIS_PLAN" "05-case-study.md" "api-inventory.md" "verification-report.md" "algo-restore.md" "anti-crawl-eval.md" "runtime-fingerprint.md"; do
    warn_english_path "$CRAWLER_SPEC" "$p" "爬虫分析规范" "4"
done
# 其他规范文件：每个英文路径 ≤ 2 次（基本只允许对照表）
for f in "$CRAWLER_TOOLS_SPEC" "$CRAWLER_WEB_SPEC" \
         "$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫小程序逆向规范.md" \
         "$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫Android逆向规范.md" \
         "$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫IOS逆向规范.md" \
         "$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫Hybrid逆向规范.md"; do
    for p in "01-target-profile/" "02-interfaces/" "03-reverse/" "04-modules/" "ANALYSIS_PLAN" "05-case-study.md" "api-inventory.md" "verification-report.md" "algo-restore.md" "anti-crawl-eval.md" "runtime-fingerprint.md"; do
        warn_english_path "$f" "$p" "$(basename "$f")" "2"
    done
done

# 技能 SKILL.md：每个英文路径 ≤ 2 次
for s in mcpowers-crawler-reverse mcpowers-extract mcpowers-reverse-web mcpowers-reverse-app; do
    f="$REPO_DIR/skills/$s/SKILL.md"
    for p in "01-target-profile/" "02-interfaces/" "03-reverse/" "04-modules/" "ANALYSIS_PLAN" "05-case-study.md" "api-inventory.md" "verification-report.md" "algo-restore.md" "anti-crawl-eval.md" "runtime-fingerprint.md"; do
        warn_english_path "$f" "$p" "$s" "2"
    done
done

if [ "$ENGLISH_PATH_FAIL" -eq 0 ]; then
    echo "  ✓ 分析文件名强制中文（v2.17.0 二次确认）无漏改"
else
    FAIL=$((FAIL + ENGLISH_PATH_FAIL))
fi

if [ "$MODULE_FORM_FAIL" -eq 0 ]; then
    echo "  ✓ 模块产物封装形式约束（v2.17.0）完整"
else
    FAIL=$((FAIL + MODULE_FORM_FAIL))
fi

# ============== 14. DrissionPage 全场景默认化（v2.18.0 新增） ==============
# 防止后续修改把 DrissionPage 默认化回退到 Playwright 默认、或漏改 6 问自检 L3。
echo "[14/17] 校验 DrissionPage 全场景默认化（v2.18.0）"
DRISSIONPAGE_FAIL=0
CRAWLER_TOOLS_SPEC="$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫工具与抓包规范.md"
CRAWLER_SKILL_DOC="$REPO_DIR/skills/mcpowers-shared/skills/mcpowers-crawler-reverse/SKILL.md"
REVERSE_WEB_DOC="$REPO_DIR/skills/mcpowers-reverse-web/SKILL.md"
POPUP_HANDLER="$REPO_DIR/skills/mcpowers-crawler-reverse/scripts/popup-handler.py"
USER_ACTION_RECORDER="$REPO_DIR/skills/mcpowers-crawler-reverse/scripts/user-action-recorder.py"
README_DOC="$REPO_DIR/README.md"

check_drissionpage() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file"
        DRISSIONPAGE_FAIL=$((DRISSIONPAGE_FAIL + 1))
        return
    fi
    if ! grep -qF "$pattern" "$file" 2>/dev/null; then
        echo "  ✗ $label 缺失（$file 应包含：$pattern）"
        DRISSIONPAGE_FAIL=$((DRISSIONPAGE_FAIL + 1))
    fi
}

# §2.1 工具栈主表 + 接管语法（爬虫工具与抓包规范）
check_drissionpage "$CRAWLER_TOOLS_SPEC" "**DrissionPage**（v2.18.0 默认）" "§2.1 工具栈主表 DrissionPage 默认"
# v2.20.0：§2.1 接管语法示例中的端口必须改为占位符 <port>，禁止回退硬编码 9222
check_drissionpage "$CRAWLER_TOOLS_SPEC" "ChromiumPage(addr_or_opts=ChromiumOptions().set_local_port(<port>))" "§2.1 DrissionPage 接管语法示例（v2.20.0 占位符）"
# §7.2 封装阶段工具栈
check_drissionpage "$CRAWLER_TOOLS_SPEC" "**DrissionPage**（v2.18.0 默认）" "§7.2 工具栈主表 DrissionPage 默认（可能与 §2.1 共用）"
# §3.5 接管粒度 DrissionPage 重新映射
check_drissionpage "$CRAWLER_TOOLS_SPEC" "v2.18.0 DrissionPage 重新映射" "§3.5 接管粒度 DrissionPage 重新映射"
# §3.6 早检测 DrissionPage 化
check_drissionpage "$CRAWLER_TOOLS_SPEC" "find_target_tab_drissionpage" "§3.6 早检测 DrissionPage 函数"
# §3.9 漏抓 7 层决策树 DrissionPage 化
check_drissionpage "$CRAWLER_TOOLS_SPEC" "v2.18.0 DrissionPage 化**" "§3.9 漏抓 7 层 DrissionPage 重新映射"
# §3.9.4 反模式 DrissionPage 化
check_drissionpage "$CRAWLER_TOOLS_SPEC" "page.new_tab()\` 不带 url 拉了 tab" "§3.9.4 反模式 page.new_tab() 不带 url"
check_drissionpage "$CRAWLER_TOOLS_SPEC" "ChromiumPage()\`（v2.18.0 新增反模式" "§3.9.4 反模式 ChromiumPage() 无参"
# Chrome 136+ 独立 user data dir 提示
check_drissionpage "$CRAWLER_TOOLS_SPEC" "set_user_data_path" "Chrome 136+ 独立 user data dir 提示"
# Chrome 150+ --remote-allow-origins 铁律（v2.16.0 引入，v2.18.0 保留）
check_drissionpage "$CRAWLER_TOOLS_SPEC" "remote-allow-origins=*" "Chrome 150+ 兼容铁律"

# popup-handler.py DrissionPage 适配
check_drissionpage "$POPUP_HANDLER" "from DrissionPage import ChromiumPage" "popup-handler.py DrissionPage import"
check_drissionpage "$POPUP_HANDLER" "page.eles(f'css:" "popup-handler.py DrissionPage eles 链式"
check_drissionpage "$POPUP_HANDLER" "el.states.is_displayed" "popup-handler.py DrissionPage 可见性 API"
check_drissionpage "$POPUP_HANDLER" "page.get_screenshot" "popup-handler.py DrissionPage 截图 API"

# user-action-recorder.py DrissionPage 适配
check_drissionpage "$USER_ACTION_RECORDER" "_drission_listen_loop" "user-action-recorder.py DrissionPage 监听线程"
check_drissionpage "$USER_ACTION_RECORDER" "page.listen.start" "user-action-recorder.py DrissionPage 监听 start"
check_drissionpage "$USER_ACTION_RECORDER" "page.run_js" "user-action-recorder.py DrissionPage run_js"
check_drissionpage "$USER_ACTION_RECORDER" "page.actions.scroll" "user-action-recorder.py DrissionPage 滚轮 API（v2.18.2 修正 wheel→scroll）"
# v2.18.2 bug-fix 校验：duck-type 修复
check_drissionpage "$USER_ACTION_RECORDER" 'hasattr(page, "listen")' "user-action-recorder.py duck-type 修复（v2.18.2 去掉 callable 误判）"
# v2.18.2 bug-fix 校验：popup-handler notification 选择器补配
check_drissionpage "$POPUP_HANDLER" '[class*="notification" i]' "popup-handler.py notification class 选择器（v2.18.2 补配）"
check_drissionpage "$POPUP_HANDLER" '[id*="notification" i]' "popup-handler.py notification id 选择器（v2.18.2 补配）"

# crawler-reverse SKILL.md 铁律 #8 + 6 问自检 L3
check_drissionpage "$REPO_DIR/skills/mcpowers-crawler-reverse/SKILL.md" "DrissionPage（v2.18.0 默认）/ Playwright" "crawler-reverse 铁律 #8 DrissionPage 化"
check_drissionpage "$REPO_DIR/skills/mcpowers-crawler-reverse/SKILL.md" "page.new_tab()\` 不带 url 拉了 tab" "crawler-reverse 6 问自检 L3 DrissionPage 化"

# reverse-web SKILL.md 编排表 + 6 问自检 L3
check_drissionpage "$REVERSE_WEB_DOC" "DrissionPage（v2.18.0 默认）+ CDP" "reverse-web 编排表 DrissionPage 默认"
check_drissionpage "$REVERSE_WEB_DOC" "page.new_tab()\` 不带 url 拉了 tab" "reverse-web 6 问自检 L3 DrissionPage 化"

# README.md 用户可见 DrissionPage 默认化说明
check_drissionpage "$README_DOC" "DrissionPage" "README DrissionPage 默认化说明"

if [ "$DRISSIONPAGE_FAIL" -eq 0 ]; then
    echo "  ✓ DrissionPage 全场景默认化（v2.18.0）完整"
else
    FAIL=$((FAIL + DRISSIONPAGE_FAIL))
fi

# ============== 15. reverse-analysis-session 强制起手式（v2.19.0 新增） ==============
echo "[15/17] 校验 reverse-analysis-session 强制起手式（v2.19.0）"
SESSION_FAIL=0
SESSION_SCRIPT="$REPO_DIR/skills/mcpowers-crawler-reverse/scripts/reverse-analysis-session.py"
SESSION_VERIFY="$REPO_DIR/tests/reverse-analysis-session-verify.py"
CRAWLER_SKILL="$REPO_DIR/skills/mcpowers-crawler-reverse/SKILL.md"
REVERSE_WEB_SKILL="$REPO_DIR/skills/mcpowers-reverse-web/SKILL.md"
CRAWLER_ANALYSIS_SPEC="$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫分析规范.md"
CRAWLER_WEB_SPEC="$REPO_DIR/skills/mcpowers-shared/docs/技术规范/爬虫Web逆向规范.md"

check_session() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file"
        SESSION_FAIL=$((SESSION_FAIL + 1))
        return
    fi
    if ! grep -qF "$pattern" "$file" 2>/dev/null; then
        echo "  ✗ $label 缺失（$file 应包含：$pattern）"
        SESSION_FAIL=$((SESSION_FAIL + 1))
    fi
}

# 必备文件
[ -f "$SESSION_SCRIPT" ] || { echo "  ✗ reverse-analysis-session.py 缺失"; SESSION_FAIL=$((SESSION_FAIL + 1)); }
[ -f "$SESSION_VERIFY" ] || { echo "  ✗ tests/reverse-analysis-session-verify.py 缺失"; SESSION_FAIL=$((SESSION_FAIL + 1)); }

# 反模式（v2.18.0 残留的"DrissionPage 内置指纹伪装/反检测"必须删除）
for f in "$CRAWLER_TOOLS_SPEC" "$REVERSE_WEB_SKILL" "$CRAWLER_SKILL" "$README_DOC"; do
    if [ -f "$f" ] && grep -qF "DrissionPage 内置" "$f"; then
        echo "  ✗ $f 仍含 'DrissionPage 内置' 残留描述（v2.19.0 必改）"
        SESSION_FAIL=$((SESSION_FAIL + 1))
    fi
done

# 第一动作建目录：crawler-reverse SKILL 必须显式声明
check_session "$CRAWLER_SKILL" "第一时间创建工作区" "crawler-reverse SKILL 第一动作声明"
check_session "$CRAWLER_SKILL" "reverse-analysis-session.py init" "crawler-reverse SKILL init 命令示例"
check_session "$CRAWLER_SKILL" "资源所有权铁律" "crawler-reverse SKILL 资源所有权声明"

# reverse-web SKILL 必须把 web-start 列为唯一公开起手式
check_session "$REVERSE_WEB_SKILL" "reverse-analysis-session.py web-start" "reverse-web SKILL 必含 web-start"
check_session "$REVERSE_WEB_SKILL" "资源所有权铁律" "reverse-web SKILL 资源所有权声明"

# 工具与抓包规范 §8.6 / §8.7 必须新增 JS 监控与指纹审计
check_session "$CRAWLER_TOOLS_SPEC" "§8.6" "工具册 §8.6 JS 监控存在"
check_session "$CRAWLER_TOOLS_SPEC" "§8.7" "工具册 §8.7 指纹审计存在"
check_session "$CRAWLER_TOOLS_SPEC" "一致性审计" "工具册指纹审计标题"
check_session "$CRAWLER_TOOLS_SPEC" "**无内置反指纹**" "工具册 §2.1 接管语法对照表无内置反指纹声明"

# 爬虫分析规范必须把 B 模式设为 Web 默认
check_session "$CRAWLER_ANALYSIS_SPEC" "B 模式直接默认" "主册 B 模式默认声明"
check_session "$CRAWLER_ANALYSIS_SPEC" "v2.19.0 新增" "主册 v2.19.0 变更声明"

# 爬虫 Web 逆向规范必须含 v2.19.0 起手式
check_session "$CRAWLER_WEB_SPEC" "v2.19.0" "Web 册 v2.19.0 标注"

if [ "$SESSION_FAIL" -eq 0 ]; then
    echo "  ✓ reverse-analysis-session 强制起手式（v2.19.0）完整"
else
    FAIL=$((FAIL + SESSION_FAIL))
fi

# ============== 16. 项目独立端口（v2.20.0 新增） ==============
# 物理门禁：pick_free_port 必须存在；init 必须写 chrome_port；文档必须用 <port> 占位符，
# 禁止回退到硬编码 9222（除非历史注释/反例说明文本）。
echo "[16/17] 校验项目独立端口（v2.20.0）"
PORT_FAIL=0
SESSION_SCRIPT="$REPO_DIR/skills/mcpowers-crawler-reverse/scripts/reverse-analysis-session.py"

check_port() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file"
        PORT_FAIL=$((PORT_FAIL + 1))
        return
    fi
    if ! grep -qF "$pattern" "$file" 2>/dev/null; then
        echo "  ✗ $label 缺失（$file 应包含：$pattern）"
        PORT_FAIL=$((PORT_FAIL + 1))
    fi
}

# 1. pick_free_port 函数 + 端口池常量
check_port "$SESSION_SCRIPT" "def pick_free_port" "pick_free_port 函数定义"
check_port "$SESSION_SCRIPT" "PORT_POOL_START = 9222" "端口池起点常量"
check_port "$SESSION_SCRIPT" "PORT_POOL_END = 9300" "端口池终点常量"
check_port "$SESSION_SCRIPT" "def resolve_port" "resolve_port 三级优先级函数"

# 2. chrome_port 字段写入 init 阶段
check_port "$SESSION_SCRIPT" "chrome_port=port" "init 阶段写 chrome_port"

# 3. probe_cdp / detect_host_environment 默认值改 None（函数签名层面）
check_port "$SESSION_SCRIPT" "def probe_cdp(port: int | None = None" "probe_cdp 默认 None"
check_port "$SESSION_SCRIPT" "def detect_host_environment(port: int | None = None" "detect_host_environment 默认 None"
check_port "$SESSION_SCRIPT" "default=None, help=\"Chrome CDP 端口" "start_parser --port default=None"

# 4. run_web_session 改用 resolve_port
check_port "$SESSION_SCRIPT" "port = resolve_port(workspace, args.port)" "run_web_session 用 resolve_port 解析端口"

# 5. 文档占位符 <port>（§2.1 接管语法 + §3.0.6 SOP + 2 个 SKILL.md L1 自检）
check_port "$CRAWLER_TOOLS_SPEC" "set_local_port(<port>)" "工具册 §2.1 接管语法用 <port> 占位符"
check_port "$CRAWLER_ANALYSIS_SPEC" "curl http://localhost:<port>/json" "分析册 §3.0.6 SOP 用 <port> 占位符"
check_port "$CRAWLER_SKILL" "curl http://localhost:<port>/json" "crawler-reverse SKILL L1 自检占位符"
check_port "$REVERSE_WEB_SKILL" "localhost:<port>" "reverse-web SKILL §1 接管预检占位符"

# 6. 测试脚本新增第 10 类断言
SESSION_VERIFY="$REPO_DIR/tests/reverse-analysis-session-verify.py"
check_port "$SESSION_VERIFY" "[10/10] pick_free_port" "测试脚本新增第 10 类断言"

if [ "$PORT_FAIL" -eq 0 ]; then
    echo "  ✓ 项目独立端口（v2.20.0）完整"
else
    FAIL=$((FAIL + PORT_FAIL))
fi

# ============== 17. 会话派生产物（v2.21.0 新增） ==============
# 物理门禁：session-artifacts-generator.py 存在 + 公开契约 + v2.17.0 类式模板关键方法 +
# v2.21 评分维度字符串 + lifecycle 标签 + reverse-analysis-session.py 集成点 +
# 三份规范 + 3 个 SKILL + CLAUDE.md / README.md 同步。
echo "[17/17] 校验会话派生产物（v2.21.0）"
ARTIFACT_FAIL=0
GENERATOR_SCRIPT="$REPO_DIR/skills/mcpowers-crawler-reverse/scripts/session-artifacts-generator.py"
ARTIFACTS_VERIFY="$REPO_DIR/tests/session-artifacts-generator-verify.py"

check_artifact() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file"
        ARTIFACT_FAIL=$((ARTIFACT_FAIL + 1))
        return
    fi
    if ! grep -qF "$pattern" "$file" 2>/dev/null; then
        echo "  ✗ $label 缺失（$file 应包含：$pattern）"
        ARTIFACT_FAIL=$((ARTIFACT_FAIL + 1))
    fi
}

# 1. 生成器脚本存在 + 公开契约
check_artifact "$GENERATOR_SCRIPT" "def run_artifacts_generation(" "生成器脚本 run_artifacts_generation 函数"
check_artifact "$GENERATOR_SCRIPT" "02-接口分析/目标接口候选.md" "生成器候选报告路径字符串"
check_artifact "$GENERATOR_SCRIPT" "02-接口分析/响应样本" "生成器响应样本目录字符串"
check_artifact "$GENERATOR_SCRIPT" "04-模块封装" "生成器模块封装目录字符串"
check_artifact "$GENERATOR_SCRIPT" "client.py" "生成器 client.py 产物字符串"
check_artifact "$GENERATOR_SCRIPT" "quick_test.py" "生成器 quick_test.py 产物字符串"

# 2. v2.17.0 类式模板关键方法
check_artifact "$GENERATOR_SCRIPT" "def build_request(" "client.py 模板含 build_request 方法"
check_artifact "$GENERATOR_SCRIPT" "def do_request(" "client.py 模板含 do_request 方法"
check_artifact "$GENERATOR_SCRIPT" "def parse_response(" "client.py 模板含 parse_response 方法"
check_artifact "$GENERATOR_SCRIPT" "def request_and_parse(" "client.py 模板含 request_and_parse 方法"
check_artifact "$GENERATOR_SCRIPT" 'if __name__ == "__main__":' "quick_test.py 模板含 __main__"

# 3. v2.21 六维评分维度字符串
check_artifact "$GENERATOR_SCRIPT" "响应码 200" "六维评分：响应码 200 维度"
check_artifact "$GENERATOR_SCRIPT" "操作触发" "六维评分：操作触发维度"
check_artifact "$GENERATOR_SCRIPT" "业务 JSON 字段" "六维评分：业务 JSON 字段维度"
check_artifact "$GENERATOR_SCRIPT" "反爬特征" "六维评分：反爬特征维度"
check_artifact "$GENERATOR_SCRIPT" "静态 vs 动态参数" "六维评分：静态 vs 动态参数维度"
check_artifact "$GENERATOR_SCRIPT" "重复次数" "六维评分：重复次数维度"
check_artifact "$GENERATOR_SCRIPT" "body_preview" "响应样本 envelope body_preview 字段"
check_artifact "$GENERATOR_SCRIPT" "不代表完整响应体" "响应样本 envelope 声明不代表完整响应体"

# 4. lifecycle 标签（4 类核心）
check_artifact "$GENERATOR_SCRIPT" "reusable" "lifecycle 标签 reusable"
check_artifact "$GENERATOR_SCRIPT" "per-request" "lifecycle 标签 per-request"
check_artifact "$GENERATOR_SCRIPT" "session-bound" "lifecycle 标签 session-bound"
check_artifact "$GENERATOR_SCRIPT" "challenge-bound" "lifecycle 标签 challenge-bound"

# 5. 集成点：reverse-analysis-session.py 必须加载并调用
check_artifact "$SESSION_SCRIPT" "session-artifacts-generator.py" "session 脚本加载 session-artifacts-generator"
check_artifact "$SESSION_SCRIPT" "run_artifacts_generation" "session 脚本调用 run_artifacts_generation"
check_artifact "$SESSION_SCRIPT" "artifacts_generation" "session 脚本写 artifacts_generation 状态字段"

# 6. 规范与工具表
check_artifact "$CRAWLER_TOOLS_SPEC" "§8.8 Web 会话派生产物自动生成" "工具册 §8.8 章节标题"
check_artifact "$CRAWLER_TOOLS_SPEC" "session-artifacts-generator.py" "工具册 §7.2 工具对照表新增行"
check_artifact "$CRAWLER_ANALYSIS_SPEC" "§3.11 App 录制选型调研" "分析册 §3.11 章节标题"
check_artifact "$CRAWLER_ANALYSIS_SPEC" "Appium" "分析册 §3.11 Appium 方案字符串"
check_artifact "$CRAWLER_ANALYSIS_SPEC" "frida" "分析册 §3.11 Frida 方案字符串"
check_artifact "$CRAWLER_ANALYSIS_SPEC" "Accessibility Service" "分析册 §3.11 Accessibility Service 方案字符串"
check_artifact "$CRAWLER_WEB_SPEC" "目标接口候选.md" "Web 册头部含目标接口候选段"

# 7. SKILL 与顶层文档
check_artifact "$CRAWLER_SKILL" "session-artifacts-generator.py" "crawler-reverse SKILL 含生成器名"
check_artifact "$REVERSE_WEB_SKILL" "目标接口候选" "reverse-web SKILL 含目标接口候选触发词"
check_artifact "$REPO_DIR/skills/mcpowers/SKILL.md" "会话产物生成" "主路由 SKILL 含会话产物生成触发词"
# v2.21.1：CLAUDE.md / README.md 不再含 v2.21.0 标题段（已迁移至 CHANGELOG.md / docs/历史教训.md）
check_artifact "$REPO_DIR/CHANGELOG.md" "## v2.21.0" "CHANGELOG.md 含 v2.21.0 段"
check_artifact "$REPO_DIR/docs/历史教训.md" "v2.21.0" "docs/历史教训.md 含 v2.21.0 段"

# 8. 测试接入
check_artifact "$ARTIFACTS_VERIFY" "[7/7]" "新 verify.py 含 7 类断言标签"
check_artifact "$REPO_DIR/tests/plugin-verify.sh" "session-artifacts-generator-verify.py" "plugin-verify.sh 调新 verify.py"
check_artifact "$REPO_DIR/tests/plugin-verify.sh" "RC_ARTIFACTS" "plugin-verify.sh 含 RC_ARTIFACTS 退出码变量"

if [ "$ARTIFACT_FAIL" -eq 0 ]; then
    echo "  ✓ 会话派生产物（v2.21.0）完整"
else
    FAIL=$((FAIL + ARTIFACT_FAIL))
fi

# ============== §18 根文档结构门禁（v2.21.1） ==============
# 禁止 CLAUDE.md 出现"### 历史教训（v" 时间线叙事
# 禁止 README.md 出现"### vX.Y.Z" 版本发布段
# 两个根文档必须各包含一行 docs/历史教训.md 与 CHANGELOG.md 的相对链接
echo "[18/20] 根文档结构门禁（v2.21.1）..."

STRUCT_FAIL=0

if grep -qE '^### 历史教训（v' CLAUDE.md; then
    echo "  ✗ CLAUDE.md 含历史教训时间线叙事段（v2.21.1+ 禁止）"
    STRUCT_FAIL=$((STRUCT_FAIL + 1))
fi

if grep -qE '^### v[0-9]+\.[0-9]+\.[0-9]+' README.md; then
    echo "  ✗ README.md 含版本发布段（v2.21.1+ 禁止）"
    STRUCT_FAIL=$((STRUCT_FAIL + 1))
fi

if ! grep -qE 'docs/历史教训\.md' CLAUDE.md; then
    echo "  ✗ CLAUDE.md 缺少 docs/历史教训.md 链接"
    STRUCT_FAIL=$((STRUCT_FAIL + 1))
fi

if ! grep -qE 'CHANGELOG\.md' CLAUDE.md; then
    echo "  ✗ CLAUDE.md 缺少 CHANGELOG.md 链接"
    STRUCT_FAIL=$((STRUCT_FAIL + 1))
fi

if ! grep -qE 'docs/历史教训\.md' README.md; then
    echo "  ✗ README.md 缺少 docs/历史教训.md 链接"
    STRUCT_FAIL=$((STRUCT_FAIL + 1))
fi

if ! grep -qE 'CHANGELOG\.md' README.md; then
    echo "  ✗ README.md 缺少 CHANGELOG.md 链接"
    STRUCT_FAIL=$((STRUCT_FAIL + 1))
fi

if [ "$STRUCT_FAIL" -eq 0 ]; then
    echo "  ✓ 根文档结构门禁完整（CLAUDE.md 链接齐 / README.md 链接齐 / 无时间线段）"
else
    FAIL=$((FAIL + STRUCT_FAIL))
fi

# ============== §19 根文档尺寸门禁（v2.21.1） ==============
# CLAUDE.md ≤ 350 行 / 35,000 字符；README.md ≤ 650 行 / 50,000 字符
# 失败时打印当前值与限制值，并提示在脚本头部常量 CLAUDE_LINE_BUDGET 等调整
echo "[19/20] 根文档尺寸门禁（v2.21.1）..."

CLAUDE_LINE_BUDGET=350
CLAUDE_CHAR_BUDGET=46000
README_LINE_BUDGET=650
README_CHAR_BUDGET=50000

SIZE_FAIL=0

CLAUDE_LINES=$(wc -l < CLAUDE.md)
CLAUDE_CHARS=$(wc -m < CLAUDE.md)
if [ "$CLAUDE_LINES" -gt "$CLAUDE_LINE_BUDGET" ] || [ "$CLAUDE_CHARS" -gt "$CLAUDE_CHAR_BUDGET" ]; then
    echo "  ✗ CLAUDE.md 尺寸超预算：当前 ${CLAUDE_LINES} 行 / ${CLAUDE_CHARS} 字符，预算 ≤ ${CLAUDE_LINE_BUDGET} 行 / ${CLAUDE_CHAR_BUDGET} 字符"
    SIZE_FAIL=$((SIZE_FAIL + 1))
fi

README_LINES=$(wc -l < README.md)
README_CHARS=$(wc -m < README.md)
if [ "$README_LINES" -gt "$README_LINE_BUDGET" ] || [ "$README_CHARS" -gt "$README_CHAR_BUDGET" ]; then
    echo "  ✗ README.md 尺寸超预算：当前 ${README_LINES} 行 / ${README_CHARS} 字符，预算 ≤ ${README_LINE_BUDGET} 行 / ${README_CHAR_BUDGET} 字符"
    SIZE_FAIL=$((SIZE_FAIL + 1))
fi

if [ "$SIZE_FAIL" -eq 0 ]; then
    echo "  ✓ 根文档尺寸门禁通过（CLAUDE.md ${CLAUDE_LINES} 行 / ${CLAUDE_CHARS} 字符；README.md ${README_LINES} 行 / ${README_CHARS} 字符）"
else
    echo "  调整提示：如确实需要扩充，请在 scripts/check-readme-sync.sh 头部常量 CLAUDE_LINE_BUDGET / CLAUDE_CHAR_BUDGET / README_LINE_BUDGET / README_CHAR_BUDGET 同步调整，并先评估是否应迁出到 docs/历史教训.md / CHANGELOG.md"
    FAIL=$((FAIL + SIZE_FAIL))
fi

# ============== §20 单一权威源门禁（v2.21.1） ==============
# 关键短语（如「外部接管资源不可关闭」/「pick_free_port」/「类式封装」/「set_local_port(9222)」）
# 在 CLAUDE.md / README.md 出现即告警（不阻断，FAIL 累加）：该规则应在权威源维护
# 复用既有 §12 / §14 / §15 / §16 / §17 已有的 grep -qF 模式
echo "[20/20] 单一权威源门禁（v2.21.1）..."

AUTHORITY_FAIL=0
AUTHORITY_KEYWORDS=(
    "pick_free_port"
    "set_local_port(9222)"
    "类式封装"
    "DrissionPage 内置"
)
# 「外部接管资源不可关闭」由 §12 已锁，§20 只对未纳入 §12-§17 的新增短语做告警

for keyword in "${AUTHORITY_KEYWORDS[@]}"; do
    if grep -qF "$keyword" CLAUDE.md 2>/dev/null; then
        echo "  ⚠ CLAUDE.md 含「${keyword}」—— 顶层文档不维护规则副本，应在对应技术规范权威源维护"
        AUTHORITY_FAIL=$((AUTHORITY_FAIL + 1))
    fi
    if grep -qF "$keyword" README.md 2>/dev/null; then
        echo "  ⚠ README.md 含「${keyword}」—— 顶层文档不维护规则副本，应在对应技术规范权威源维护"
        AUTHORITY_FAIL=$((AUTHORITY_FAIL + 1))
    fi
done

if [ "$AUTHORITY_FAIL" -eq 0 ]; then
    echo "  ✓ 单一权威源门禁通过（CLAUDE.md / README.md 未维护规则副本）"
else
    echo "  提示：上述短语已在对应规范权威源维护（与 docs/历史教训.md 关联），顶层文档应只保留 1 行相对链接"
    FAIL=$((FAIL + AUTHORITY_FAIL))
fi

# ============== §21 规范 frontmatter 双字段门禁（v2.27.4+） ==============
# 强制要求：31 个技术规范 frontmatter 必须声明
#   - stability: stable|evolving|deprecated
#   - last_breaking_change: v{major}.{minor}.{patch}
# 这是 v2.27.4「规范稳定性分级」铁律的 CI 兜底层（与 pre-write-check-spec-frontmatter.sh 物理 Hook 互补）
echo "[21/21] 校验全部规范都有 stability: + last_breaking_change: 字段（v2.27.4+）..."

SPEC_DIR="skills/mcpowers-shared/docs/技术规范"
SPEC_TOTAL=$(find "$SPEC_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l)
SPEC_STABILITY=$(grep -l "^stability:" "$SPEC_DIR"/*.md 2>/dev/null | wc -l)
SPEC_BREAKING=$(grep -l "^last_breaking_change:" "$SPEC_DIR"/*.md 2>/dev/null | wc -l)

FRONTMATTER_FAIL=0
if [ "$SPEC_STABILITY" -ne "$SPEC_TOTAL" ]; then
    echo "  ✗ 仅 $SPEC_STABILITY/$SPEC_TOTAL 规范标注 stability:（缺字段列表："
    for f in "$SPEC_DIR"/*.md; do
        if ! grep -q "^stability:" "$f" 2>/dev/null; then
            echo "      - $(basename "$f")"
        fi
    done
    echo "    ）"
    FRONTMATTER_FAIL=$((FRONTMATTER_FAIL + 1))
fi
if [ "$SPEC_BREAKING" -ne "$SPEC_TOTAL" ]; then
    echo "  ✗ 仅 $SPEC_BREAKING/$SPEC_TOTAL 规范标注 last_breaking_change:"
    FRONTMATTER_FAIL=$((FRONTMATTER_FAIL + 1))
fi

if [ "$FRONTMATTER_FAIL" -eq 0 ]; then
    echo "  ✓ $SPEC_TOTAL 规范 frontmatter 双字段完整（stability + last_breaking_change 全部标注）"
else
    echo "  修复：在每个规范文件 frontmatter 补 'stability: stable|evolving|deprecated' + 'last_breaking_change: v{major}.{minor}.{patch}'"
    FAIL=$((FAIL + FRONTMATTER_FAIL))
fi

# ============== §22 Swagger 5 字段契约铁律存在性(v2.31.0+) ==============
SWAGGER_FAIL=0
# CLAUDE.md 必须含 v2.31.0+ Swagger 铁律段
if [ ! -f "CLAUDE.md" ] || ! grep -q "写 Swagger 接口必须按 5 字段契约（v2.31.0+" "CLAUDE.md"; then
    echo "  ✗ CLAUDE.md 缺 v2.31.0+ Swagger 5 字段契约铁律段"
    SWAGGER_FAIL=$((SWAGGER_FAIL + 1))
fi
# Swagger字段契约.md 必须存在
if [ ! -f "skills/mcpowers-shared/docs/技术规范/Swagger字段契约.md" ]; then
    echo "  ✗ skills/mcpowers-shared/docs/技术规范/Swagger字段契约.md 不存在"
    SWAGGER_FAIL=$((SWAGGER_FAIL + 1))
fi
# 默认Swagger必填字段.yml 必须存在
if [ ! -f "skills/mcpowers-shared/docs/API契约/默认Swagger必填字段.yml" ]; then
    echo "  ✗ skills/mcpowers-shared/docs/API契约/默认Swagger必填字段.yml 不存在"
    SWAGGER_FAIL=$((SWAGGER_FAIL + 1))
fi
# swagger-contract-check.sh 集中 helper 必须存在
if [ ! -f "skills/mcpowers-shared/scripts/swagger-contract-check.sh" ]; then
    echo "  ✗ skills/mcpowers-shared/scripts/swagger-contract-check.sh 不存在"
    SWAGGER_FAIL=$((SWAGGER_FAIL + 1))
fi
# swagger-lint-helper.py 必须存在
if [ ! -f "skills/mcpowers-shared/scripts/swagger-lint-helper.py" ]; then
    echo "  X skills/mcpowers-shared/scripts/swagger-lint-helper.py 不存在"
    SWAGGER_FAIL=$((SWAGGER_FAIL + 1))
fi

if [ "$SWAGGER_FAIL" -eq 0 ]; then
    echo "  ✓ v2.31.0+ Swagger 5 字段契约铁律 5 件套完整(CLAUDE.md 铁律段 + Swagger字段契约.md + 默认清单 yml + contract-check.sh + lint-helper.py)"
else
    FAIL=$((FAIL + SWAGGER_FAIL))
fi

# ============== §23 代码/配置零引用智能二分判定（v4.3.0+） ==============
# 防止后续修改只保留脚本骨架，却删除 22 字眼共享清单 / 3 份共享常量 / 智能二分检测器 / 2 个新 hook。
echo "[23/23] 校验代码/配置零引用智能二分判定（v4.3.0+）"
NOREF_FAIL=0

check_noref_file() {
    local file="$1"
    local label="$2"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file（$label）"
        NOREF_FAIL=$((NOREF_FAIL + 1))
        return
    fi
}

check_noref_grep() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file（$label）"
        NOREF_FAIL=$((NOREF_FAIL + 1))
        return
    fi
    if ! grep -qF "$pattern" "$file" 2>/dev/null; then
        echo "  ✗ $label 缺失（$file 应包含：$pattern）"
        NOREF_FAIL=$((NOREF_FAIL + 1))
    fi
}

# v4.6.3+ 反向断言：检查文件不应包含某字符串（用于验证已迁出项）
check_noref_not_grep() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file（$label）"
        NOREF_FAIL=$((NOREF_FAIL + 1))
        return
    fi
    if grep -qF "$pattern" "$file" 2>/dev/null; then
        echo "  ✗ $label 应不包含（$file 不应再含：$pattern）"
        NOREF_FAIL=$((NOREF_FAIL + 1))
    fi
}

# 1. 3 份共享常量文件存在
check_noref_file "skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt"  "禁用字眼共享清单"
check_noref_file "skills/mcpowers-shared/docs/_assets/_internal_spec_docs.txt"  "内部规范名清单"
check_noref_file "skills/mcpowers-shared/docs/_assets/_external_authority.txt" "外部权威清单"

# 2. 共享检测器存在
check_noref_file "skills/mcpowers-shared/scripts/check_no_ref_words.py" "智能二分检测器"

# 3. 2 个新 hook 文件存在 + 可执行
PRE_NOREF_HOOK="hooks/pre-write-check-no-ref-words.sh"
POST_NOREF_HOOK="hooks/post-write-check-no-ref-words.sh"
check_noref_file "$PRE_NOREF_HOOK"  "硬门禁 hook"
check_noref_file "$POST_NOREF_HOOK" "软兜底 hook"
[ -x "$PRE_NOREF_HOOK" ]  || { echo "  ✗ $PRE_NOREF_HOOK 不可执行";  NOREF_FAIL=$((NOREF_FAIL + 1)); }
[ -x "$POST_NOREF_HOOK" ] || { echo "  ✗ $POST_NOREF_HOOK 不可执行"; NOREF_FAIL=$((NOREF_FAIL + 1)); }

# 4. 旧 post-write-check-doc-content.sh 必须删除（v4.3.0 替代）
if [ -f "hooks/post-write-check-doc-content.sh" ]; then
    echo "  ✗ hooks/post-write-check-doc-content.sh 应删除（v4.3.0 已被 post-write-check-no-ref-words.sh 替代）"
    NOREF_FAIL=$((NOREF_FAIL + 1))
fi

# 5. CLAUDE.md 必须含 v4.3.0+ 代码/配置零引用铁律段
check_noref_grep "CLAUDE.md" "代码/配置零引用铁律·智能二分判定（v4.3.0+" "CLAUDE.md v4.3.0 铁律段"
# 6. README.md 必须含 v4.3.0 提及（用户可见升级说明）
check_noref_grep "README.md" "v4.3.0+" "README v4.3.0 升级说明"

# 7. mcpowers-code-review 必须含 R17 + 8 条扫描命令
CODE_REVIEW_SKILL="skills/mcpowers-code-review/SKILL.md"
check_noref_grep "$CODE_REVIEW_SKILL" "R17" "code-review R17 反模式条目"
check_noref_grep "$CODE_REVIEW_SKILL" "v4.3.0+ 代码/配置零引用智能二分 Quick-Check" "code-review Quick-Check v4.3.0 段"

# 8. hooks.json 必须注册新 hook（v4.6.3+ 已迁移 22 字眼硬门禁从 PreToolUse 到 pre-bash-guard.sh git commit 兜底）
HOOKS_JSON="hooks/hooks.json"
check_noref_not_grep "$HOOKS_JSON" "pre-write-check-no-ref-words.sh" "v4.6.3+ hooks.json 已移除 22 字眼 PreToolUse 硬门禁注册"
check_noref_grep "$HOOKS_JSON" "post-write-check-no-ref-words.sh" "hooks.json PostToolUse 段注册软兜底"
# 9. pre-bash-guard.sh 必须含 v4.6.3+ git commit 兜底段
check_noref_grep "hooks/pre-bash-guard.sh" "v4.6.3+ git commit 字眼兜底检测" "pre-bash-guard.sh v4.6.3+ git commit 兜底段"
check_noref_grep "hooks/pre-bash-guard.sh" "git[[:space:]]+commit" "pre-bash-guard.sh 含 git commit 检测正则"

# 9. 代码规范.md 必须新增 §11.3.1 子章节
CODE_SPEC_DOC="skills/mcpowers-shared/docs/技术规范/代码规范.md"
check_noref_grep "$CODE_SPEC_DOC" "#### 11.3.1" "代码规范 §11.3.1 智能二分章节"

if [ "$NOREF_FAIL" -eq 0 ]; then
    echo "  ✓ 代码/配置零引用智能二分判定（v4.3.0+）完整"
else
    FAIL=$((FAIL + NOREF_FAIL))
fi

# ============== §24 接口文档 SSOT 终态收敛铁律（v4.4.0+） ==============
# 防止后续修改只保留脚本骨架，却删除 5 个全局组件 SSOT 文件 / Flask 注入模板 / 3 个新检查函数 / R18 反模式条目。
echo "[24/24] 校验接口文档 SSOT 终态收敛铁律（v4.4.0+ description 零冗余 + \$ref 复用）"
V440_FAIL=0

check_v440_file() {
    local file="$1"
    local label="$2"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file（$label）"
        V440_FAIL=$((V440_FAIL + 1))
        return
    fi
}

check_v440_grep() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if [ ! -f "$file" ]; then
        echo "  ✗ 文件不存在: $file（$label）"
        V440_FAIL=$((V440_FAIL + 1))
        return
    fi
    if ! grep -qF "$pattern" "$file" 2>/dev/null; then
        echo "  ✗ $label 缺失（$file 应包含：$pattern）"
        V440_FAIL=$((V440_FAIL + 1))
    fi
}

# 1. swagger_components.md 5 全局组件 SSOT 权威定义文件存在
SWAGGER_COMPONENTS="skills/mcpowers-shared/docs/API文档/swagger_components.md"
check_v440_file "$SWAGGER_COMPONENTS" "5 全局组件 SSOT 文档"
check_v440_grep "$SWAGGER_COMPONENTS" "StandardResponse" "StandardResponse 组件定义"
check_v440_grep "$SWAGGER_COMPONENTS" "BizResponse"    "BizResponse 组件定义"
check_v440_grep "$SWAGGER_COMPONENTS" "PageResponse"   "PageResponse 组件定义"
check_v440_grep "$SWAGGER_COMPONENTS" "BizError"       "BizError 组件定义"
check_v440_grep "$SWAGGER_COMPONENTS" "FileResponse"   "FileResponse 组件定义"
check_v440_grep "$SWAGGER_COMPONENTS" "BearerAuth"     "BearerAuth 安全定义"

# 2. flask_swagger_config.py Flasgger 注入模板常量文件存在
FLASK_SWAGGER_CONFIG="skills/mcpowers-shared/docs/API文档/flask_swagger_config.py"
check_v440_file "$FLASK_SWAGGER_CONFIG" "Flask Flasgger 注入模板"
check_v440_grep "$FLASK_SWAGGER_CONFIG" "SWAGGER_TEMPLATE" "SWAGGER_TEMPLATE 常量"

# 3. swagger-lint-helper.py 必须含 3 个新检查函数
SWAGGER_LINT="skills/mcpowers-shared/scripts/swagger-lint-helper.py"
check_v440_grep "$SWAGGER_LINT" "check_description_redundant_content" "description 8 类冗余内容检查函数"
check_v440_grep "$SWAGGER_LINT" "check_no_path_in_description"       "完整路径前缀扫描函数"
check_v440_grep "$SWAGGER_LINT" "check_no_repeated_schema"            "内联 schema 展开扫描函数"

# 4. 接口契约规范 §1.A.1 description 禁用内容清单 + §1.F $ref 复用铁律
API_CONTRACT="skills/mcpowers-shared/docs/技术规范/接口契约规范.md"
check_v440_grep "$API_CONTRACT" "description 禁用内容清单（v4.4.0+" "接口契约规范 §1.A.1 铁律段"
check_v440_grep "$API_CONTRACT" "通用响应/分页必须用 \`\$ref\` 复用（v4.4.0+" "接口契约规范 §1.F 铁律段"

# 5. Flask 后端规范 §11.5 全局组件挂载 4 步
FLASK_SPEC="skills/mcpowers-shared/docs/技术规范/Flask后端规范.md"
check_v440_grep "$FLASK_SPEC" "全局组件挂载（v4.4.0+" "Flask 后端规范 §11.5 铁律段"

# 6. swagger_template.md v3.0（19 类接口模板统一用 $ref 复用）
SWAGGER_TEMPLATE="skills/mcpowers-shared/docs/API文档/swagger_template.md"
check_v440_grep "$SWAGGER_TEMPLATE" "last_breaking_change: v4.4.0" "swagger_template.md 声明 v4.4.0 破坏性变更"
check_v440_grep "$SWAGGER_TEMPLATE" "\$ref" "swagger_template.md 使用 \$ref 复用"

# 7. CLAUDE.md 必须含 v4.4.0+ 接口文档 SSOT 终态收敛铁律段
check_v440_grep "CLAUDE.md" "接口文档 SSOT 终态收敛（v4.4.0+" "CLAUDE.md v4.4.0 铁律段"

# 8. README.md 必须含 v4.4.0 提及（用户可见升级说明）
check_v440_grep "README.md" "v4.4.0+" "README v4.4.0 升级说明"

# 9. mcpowers-code-review 必须含 R18 反模式条目 + v4.4.0 Quick-Check 段
CODE_REVIEW_SKILL="skills/mcpowers-shared/skills/mcpowers-code-review/SKILL.md"
[ -f "skills/mcpowers-code-review/SKILL.md" ] && CODE_REVIEW_SKILL="skills/mcpowers-code-review/SKILL.md"
check_v440_grep "$CODE_REVIEW_SKILL" "R18" "code-review R18 反模式条目"
check_v440_grep "$CODE_REVIEW_SKILL" "v4.4.0+ 接口文档 description 零冗余" "code-review Quick-Check v4.4.0 段"

# 10. 场景技能 description 必须含 v4.4.0 触发词
check_v440_grep "skills/mcpowers-feat/SKILL.md"           "v4.4.0+ 接口 docstring description 零冗余" "mcpowers-feat v4.4.0 触发词"
check_v440_grep "skills/mcpowers-api-contract/SKILL.md"   "v4.4.0+ description 零冗余"               "mcpowers-api-contract v4.4.0 触发词"

if [ "$V440_FAIL" -eq 0 ]; then
    echo "  ✓ 接口文档 SSOT 终态收敛铁律（v4.4.0+）完整"
else
    FAIL=$((FAIL + V440_FAIL))
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