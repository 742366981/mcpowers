#!/usr/bin/env bash
# 前端 TypeScript 客户端自动生成脚本（v2.4.0 新增）
#
# 前置：
#   - swagger_spec.json 已生成（python tools/export_docs.py）
#   - 项目的 package.json 里有 openapi-typescript-codegen 依赖
#
# 使用方式：
#   bash scripts/generate-frontend-ts.sh
#   bash scripts/generate-frontend-ts.sh --spec path/to/spec.json --output path/to/src/api
#
# 详细文档：skills/mcpowers-shared/docs/API契约/前端对接流程.md

set -e

SPEC_FILE="docs/API文档/swagger_spec.json"
OUTPUT_DIR="src/api"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --spec) SPEC_FILE="$2"; shift 2 ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

# 检查 spec 文件
if [ ! -f "$SPEC_FILE" ]; then
    echo "❌ spec 文件不存在：$SPEC_FILE"
    echo "   → 先运行 python tools/export_docs.py"
    exit 1
fi

echo "📁 spec 文件: $SPEC_FILE"
echo "📁 输出目录: $OUTPUT_DIR"

# 1. 检查 Node.js / npx
if ! command -v npx >/dev/null 2>&1; then
    echo "❌ npx 不可用，请先安装 Node.js"
    exit 1
fi

# 2. 检查 openapi-typescript-codegen 是否已安装
if [ ! -f "package.json" ]; then
    echo "⚠️  当前目录没有 package.json，跳过（请在 frontend 目录下运行此脚本）"
    exit 0
fi

if ! grep -q "openapi-typescript-codegen" package.json 2>/dev/null; then
    echo "⚠️  package.json 未包含 openapi-typescript-codegen，请先 npm install -D openapi-typescript-codegen"
    echo "   完整步骤见 skills/mcpowers-shared/docs/API契约/前端对接流程.md"
    exit 0
fi

# 3. 执行生成
echo "🚀 生成前端 TS 客户端..."
mkdir -p "$OUTPUT_DIR"

npx openapi-typescript-codegen \
    --input "$SPEC_FILE" \
    --output "$OUTPUT_DIR" \
    --client axios

GENERATED_EXIT=$?

if [ $GENERATED_EXIT -eq 0 ]; then
    echo "✅ 生成成功：$OUTPUT_DIR"
    echo ""
    echo "   提示：建议在 CI 中加自动 commit，避免 spec 变更后前端不同步"
    echo "   详见 skills/mcpowers-shared/docs/API契约/前端对接流程.md §X"
else
    echo "❌ 生成失败（exit $GENERATED_EXIT）"
    exit $GENERATED_EXIT
fi

exit 0
