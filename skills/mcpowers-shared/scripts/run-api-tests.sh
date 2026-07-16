#!/usr/bin/env bash
# API 测试自动运行脚本（v2.4.0 新增）
#
# 基于 swagger_spec.json 自动跑 schemathesis / dredd 进行 API fuzz 测试
# 检测所有接口的：
#   - HTTP 状态码符合契约
#   - 响应 schema 与 docstring 一致
#   - 参数必填约束正确触发 400
#
# 使用方式：
#   bash scripts/run-api-tests.sh
#   bash scripts/run-api-tests.sh --base-url http://localhost:5000 --token xxx
#
# 详细文档：skills/mcpowers-shared/docs/API契约/API测试自动生成.md

set -e

SPEC_FILE="docs/API文档/swagger_spec.json"
BASE_URL="${API_BASE_URL:-http://localhost:5000}"
TOKEN="${API_TOKEN:-}"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --spec) SPEC_FILE="$2"; shift 2 ;;
        --base-url) BASE_URL="$2"; shift 2 ;;
        --token) TOKEN="$2"; shift 2 ;;
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
echo "🌐 测试目标: $BASE_URL"

# 1. 检查 schemathesis 是否安装
if ! command -v schemathesis >/dev/null 2>&1; then
    echo "❌ schemathesis 不可用"
    echo "   → pip install schemathesis"
    echo "   详见 skills/mcpowers-shared/docs/API契约/API测试自动生成.md"
    exit 1
fi

# 2. 构建认证参数
AUTH_ARGS=""
if [ -n "$TOKEN" ]; then
    AUTH_ARGS="--header 'Authorization: Bearer $TOKEN'"
fi

# 3. 跑 schemathesis
echo "🚀 开始 API 测试（基于 spec）..."
echo ""

# 设置超时（每个用例 5s，总共 10 分钟）
schemathesis run "$SPEC_FILE" \
    --base-url "$BASE_URL" \
    --checks all \
    --max-response-time=5000 \
    --request-timeout=10 \
    --workers=4 \
    $AUTH_ARGS \
    || SCHEMA_EXIT=$?

SCHEMA_EXIT=${SCHEMA_EXIT:-0}

echo ""
if [ "$SCHEMA_EXIT" -eq 0 ]; then
    echo "✅ 所有 API 测试通过"
    exit 0
fi

echo "❌ 部分 API 测试失败（exit $SCHEMA_EXIT）"
echo "   详细报告请用 schemathesis run --report=report.html"
exit $SCHEMA_EXIT
