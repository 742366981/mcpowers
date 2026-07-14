#!/usr/bin/env bash
# mcpowers README ↔ 实际状态同步校验
# 用途：CI 跑完所有断言无失败即视为文档与代码同步
# 退出码 0 = 同步，1 = 不同步
#
# 检查 4 类一致性：
#   1. README 路由表 ↔ 实际 skills/ 目录
#   2. README 规范清单 ↔ 实际 docs/ 下的规范文件
#   3. 每个规范文件有 frontmatter type: 字段
#   4. 每个场景技能有 ## 编排 段
#
# v2.0：适配扁平化 skills/ 结构（删除 scene/method 分层）

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
README="$REPO_DIR/README.md"
FAIL=0

# ============== 1. 技能清单同步 ==============
echo "[1/4] 校验 README ↔ skills/ 同步"
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
    if ! echo "$ACTUAL_SKILLS" | grep -qx "$s" 2>/dev/null; then
        echo "  ⚠ README 提到但实际不存在: $s（可能是文档笔误）"
        # 警告而非错误（README 可能引用历史技能名）
    fi
done

if [ "$FAIL" -eq 0 ]; then
    echo "  ✓ 技能清单同步"
fi

# ============== 2. 规范清单同步 ==============
echo "[2/4] 校验 README ↔ docs/ 规范同步"
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
# 只检查 技术规范/ 子目录（18 核心规范范围，AI操作规范和产品设计规范不在范围）
echo "[3/4] 校验 18 个核心规范 frontmatter 完整性"
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
    echo "  ✓ 全部 18 个核心规范有 frontmatter"
else
    FAIL=$((FAIL + MISSING_FM))
fi

# ============== 4. 场景技能都有 ## 编排 段 ==============
# v2.0：场景技能 = skills/ 下非方法类的 mcpowers-* 技能
#   硬编码场景技能列表（原 skills/scene/*）
echo "[4/4] 校验场景技能都有 ## 编排 段"
SCENE_SKILLS="mcpowers-feat mcpowers-bugfix mcpowers-refactor mcpowers-optimize mcpowers-deploy mcpowers-requirement-change mcpowers-init mcpowers-git-commit mcpowers-git-worktree mcpowers-git-rollback mcpowers-git-cleanBranches mcpowers-autoTest"
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

# ============== 汇总 ==============
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "=== ✓ README ↔ 实际状态同步 ==="
    exit 0
else
    echo "=== ✗ $FAIL 项不一致 ==="
    exit 1
fi
