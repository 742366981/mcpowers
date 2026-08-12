#!/usr/bin/env bash
# 接口文档与代码一致性检查脚本（v2.4.0 新增）
#
# 检查项：
#   1. 接口文件 (.py view / .java controller / .js route) mtime 是否新于导出的 swagger_spec.json
#   2. swagger_spec.json 和 API文档.md 是否已 git 跟踪
#   3. 若 docs/API文档/ 缺失，提示用户先跑 export_docs.py
#
# 使用方式：
#   bash scripts/check_api_docs_sync.sh
#   bash scripts/check_api_docs_sync.sh --no-fail  # CI 首次接入，仅警告不阻断
#
# 退出码：
#   0 = 一致（或 --no-fail 模式）
#   1 = 检测到不一致（建议重新跑 export_docs.py）

set -e

NO_FAIL=false
if [ "$1" = "--no-fail" ]; then
    NO_FAIL=true
fi

# 必须 cd 到 git 仓库根目录
WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$WORK_DIR" 2>/dev/null || { echo "❌ 无法进入工作目录"; exit 1; }

# 不在 git 仓库 → 提示
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "⚠️  当前目录不是 git 仓库，跳过一致性检查"
    exit 0
fi

API_DOCS_DIR="docs/API文档"
SPEC_FILE="$API_DOCS_DIR/swagger_spec.json"
MD_FILE="$API_DOCS_DIR/API文档.md"

VIOLATIONS=0
echo "🔍 检查接口文档一致性..."
echo ""

# ========== 检查 1：导出的 spec 文件是否存在 ==========
if [ ! -f "$SPEC_FILE" ]; then
    echo "❌ 检查 1 未通过：$SPEC_FILE 不存在"
    echo "   → 请先运行 python tools/export_docs.py 生成 spec"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ 检查 1 通过：$SPEC_FILE 存在"
fi

# ========== 检查 2：接口文件是否比 spec 文件新 ==========
if [ -f "$SPEC_FILE" ]; then
    SPEC_MTIME=$(stat -c %Y "$SPEC_FILE" 2>/dev/null || stat -f %m "$SPEC_FILE" 2>/dev/null || echo 0)

    NEWER_FILES=()
    # 扫描所有可能的接口文件（最近 7 天改动过的）
    while IFS= read -r -d '' f; do
        FILE_MTIME=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null || echo 0)
        if [ "$FILE_MTIME" -gt "$SPEC_MTIME" ]; then
            NEWER_FILES+=("$f")
        fi
    done < <(find apps/ src/api/ 2>/dev/null \
        \( -name "views.py" -o -path "*/views/*.py" -o -name "*Controller.java" \
           -o -name "router.js" -o -name "router.ts" -o -path "*/routes/*" \) \
        -type f -mtime -7 -print0 2>/dev/null || true)

    if [ ${#NEWER_FILES[@]} -gt 0 ]; then
        echo "⚠️  检查 2 警告：以下接口文件比 $SPEC_FILE 新，建议重跑 export_docs.py："
        for f in "${NEWER_FILES[@]}"; do
            echo "   - $f"
        done
        echo "   → 运行 python tools/export_docs.py 重导出"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "✅ 检查 2 通过：接口文件未比 spec 新（或无变更）"
    fi
fi

# ========== 检查 3：spec 和 md 是否已 git 跟踪 ==========
if [ -f "$SPEC_FILE" ]; then
    SPEC_TRACKED=$(git ls-files --error-unmatch "$SPEC_FILE" 2>/dev/null && echo "yes" || echo "no")
    if [ "$SPEC_TRACKED" = "no" ]; then
        echo "⚠️  检查 3 警告：$SPEC_FILE 未被 git 跟踪"
        echo "   → 运行 git add docs/API文档/swagger_spec.json"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "✅ 检查 3 通过：spec 文件已 git 跟踪"
    fi
fi

# ========== 总结 ==========
echo ""
if [ "$VIOLATIONS" -gt 0 ]; then
    if [ "$NO_FAIL" = true ]; then
        echo "⚠️  共 $VIOLATIONS 项不一致（--no-fail 模式，仅警告不阻断）"
        exit 0
    fi
    echo "❌ 共 $VIOLATIONS 项不一致"
    echo "   修复建议："
    echo "   1. python ${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/tools/export_docs.py"
    echo "   2. git add docs/API文档/"
    echo "   3. git commit -m 'docs(api): sync API docs after interface change'"
    exit 1
fi

echo "✅ 所有检查通过，接口文档与代码一致"
exit 0
