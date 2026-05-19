#!/bin/bash
# sync_skills.sh - 同步文档到 mcpowers 技能仓库
# 用法: 在项目根目录执行 bash sync_skills.sh

set -e

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 源目录（当前项目）
SOURCE_DIR="$SCRIPT_DIR"

# 目标目录（mcpowers 技能仓库）
TARGET_BASE="$HOME/mcpowers"

# 检查目标目录是否存在
if [ ! -d "$TARGET_BASE" ]; then
    echo "错误: 技能仓库不存在: $TARGET_BASE"
    echo "请先创建 mcpowers Git 仓库"
    exit 1
fi

echo "=========================================="
echo "mcpowers 技能同步脚本"
echo "=========================================="
echo ""
echo "源目录: $SOURCE_DIR"
echo "目标目录: $TARGET_BASE"
echo ""

# 1. 同步 docs/ 技术规范
echo "[1/6] 同步技术规范..."
if [ -d "$SOURCE_DIR/docs/技术规范" ]; then
    mkdir -p "$TARGET_BASE/mcpowers-workflow/references/通用规范"
    mkdir -p "$TARGET_BASE/mcpowers-workflow/references/技术锁规范"
    cp -rf "$SOURCE_DIR/docs/技术规范/通用规范/"* "$TARGET_BASE/mcpowers-workflow/references/通用规范/" 2>/dev/null || true
    cp -rf "$SOURCE_DIR/docs/技术规范/技术锁规范/"* "$TARGET_BASE/mcpowers-workflow/references/技术锁规范/" 2>/dev/null || true
    echo "      ✓ 技术规范同步完成"
fi

# 2. 同步 docs/ 产品设计
echo "[2/6] 同步产品设计规范..."
if [ -d "$SOURCE_DIR/docs/产品设计" ]; then
    mkdir -p "$TARGET_BASE/mcpowers-workflow/references/产品设计"
    cp -rf "$SOURCE_DIR/docs/产品设计/"* "$TARGET_BASE/mcpowers-workflow/references/产品设计/" 2>/dev/null || true
    echo "      ✓ 产品设计规范同步完成"
fi

# 3. 同步 docs/ API文档
echo "[3/6] 同步API文档..."
if [ -d "$SOURCE_DIR/docs/API文档" ]; then
    mkdir -p "$TARGET_BASE/mcpowers-workflow/docs/API文档"
    cp -rf "$SOURCE_DIR/docs/API文档/"* "$TARGET_BASE/mcpowers-workflow/docs/API文档/" 2>/dev/null || true
    echo "      ✓ API文档同步完成"
fi

# 4. 同步 tools/ 目录
echo "[4/6] 同步工具脚本..."
if [ -d "$SOURCE_DIR/tools" ]; then
    mkdir -p "$TARGET_BASE/mcpowers-workflow/tools"
    cp -rf "$SOURCE_DIR/tools/"* "$TARGET_BASE/mcpowers-workflow/tools/" 2>/dev/null || true
    echo "      ✓ 工具脚本同步完成"
fi

# 5. 同步根目录规范文件
echo "[5/6] 同步根目录规范..."
for file in "AI操作规范.md" "AGENTS.md" "CLAUDE.md" "README.md" "sync_skills.sh"; do
    if [ -f "$SOURCE_DIR/$file" ]; then
        cp "$SOURCE_DIR/$file" "$TARGET_BASE/$file"
    fi
done
echo "      ✓ 根目录规范同步完成"

# 6. Git 提交并推送
echo ""
echo "[6/6] 提交到 Git..."
cd "$TARGET_BASE"

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo "      ℹ 没有变更需要提交"
else
    COMMIT_MSG="sync: $(date '+%Y-%m-%d %H:%M') 同步完整文档体系"
    git add .
    git commit -m "$COMMIT_MSG"
    git push
    echo "      ✓ 已推送: $COMMIT_MSG"
fi

echo ""
echo "=========================================="
echo "同步完成!"
echo "=========================================="
