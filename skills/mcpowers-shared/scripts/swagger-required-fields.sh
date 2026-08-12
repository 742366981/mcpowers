#!/usr/bin/env bash
# mcpowers swagger 字段清单加载器(v2.31.0+)
#
# 加载项目自定义必填字段清单(.swagger-required-fields.yml),无则落 mcpowers 默认。
# 解析失败 → 软警告 + fallback 默认(不阻断)。
#
# 使用方式:
#   TMP=$(bash swagger-required-fields.sh)
#   eval "$(cat "$TMP")"  # 或 sed/awk 读 3 行
#
# 输出格式:3 行文本到 stdout(临时文件路径):
#   line1: 必填字段名(空格分隔)
#   line2: parameters 子字段必填项(空格分隔)
#   line3: responses 子字段必填项(空格分隔)
#
# 退出码:
#   0 = 成功输出清单
#   1 = 完全无法生成清单(理论上 fallback 永远成功)

set -e

WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$WORK_DIR" 2>/dev/null || WORK_DIR="$(pwd)"

PROJECT_MANIFEST="$WORK_DIR/.swagger-required-fields.yml"
DEFAULT_MANIFEST="${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/docs/API契约/默认Swagger必填字段.yml"

# ---------- 1. 选择 manifest ----------
MANIFEST=""
SOURCE="default"

if [ -f "$PROJECT_MANIFEST" ]; then
    MANIFEST="$PROJECT_MANIFEST"
    SOURCE="project"
fi

if [ -z "$MANIFEST" ] && [ -f "$DEFAULT_MANIFEST" ]; then
    MANIFEST="$DEFAULT_MANIFEST"
    SOURCE="default"
fi

if [ -z "$MANIFEST" ]; then
    # 兜底:硬编码默认值(灾难 fallback)
    echo "[mcpowers swagger-required-fields] 默认清单也不存在,使用硬编码兜底" >&2
    TMP=$(mktemp)
    cat > "$TMP" <<'EOF'
tags summary description parameters responses
description example
schema examples
EOF
    echo "$TMP"
    exit 0
fi

# ---------- 2. 极简解析(grep/awk) ----------
# 解析规则:
#   required_fields: 块后每行 "  - <name>" 收集 name
#   parameter_subfields: / response_subfields: 同理
#   注释(#)与空行跳过
#   解析异常 → 软警告 + fallback 默认

REQUIRED=""
PARAM_SUB=""
RESP_SUB=""

CURRENT_BLOCK=""
PARSE_OK=1

while IFS= read -r line; do
    # 跳过注释与空行
    case "$line" in
        '#'*|'') continue ;;
    esac

    # 检测块切换
    case "$line" in
        *required_fields:*)
            CURRENT_BLOCK="required"
            continue
            ;;
        *parameter_subfields:*)
            CURRENT_BLOCK="param"
            continue
            ;;
        *response_subfields:*)
            CURRENT_BLOCK="resp"
            continue
            ;;
    esac

    # 数组项提取
    if echo "$line" | grep -qE '^[[:space:]]*-[[:space:]]+[A-Za-z_][A-Za-z0-9_]*'; then
        ITEM=$(echo "$line" | sed -E 's/^[[:space:]]*-[[:space:]]+//' | awk '{print $1}')
        case "$CURRENT_BLOCK" in
            required) REQUIRED="$REQUIRED $ITEM" ;;
            param) PARAM_SUB="$PARAM_SUB $ITEM" ;;
            resp) RESP_SUB="$RESP_SUB $ITEM" ;;
            *)
                # 数组项在已知块外出现 → 解析异常
                PARSE_OK=0
                ;;
        esac
    fi
done < "$MANIFEST" || PARSE_OK=0

# 解析异常 → 软警告 + fallback 默认
if [ "$PARSE_OK" = "0" ]; then
    echo "[mcpowers swagger-required-fields] 解析异常:$MANIFEST,fallback 默认" >&2
    MANIFEST="$DEFAULT_MANIFEST"
    SOURCE="default"
    REQUIRED=""
    PARAM_SUB=""
    RESP_SUB=""
    CURRENT_BLOCK=""

    while IFS= read -r line; do
        case "$line" in
            '#'*|'') continue ;;
        esac
        case "$line" in
            *required_fields:*) CURRENT_BLOCK="required"; continue ;;
            *parameter_subfields:*) CURRENT_BLOCK="param"; continue ;;
            *response_subfields:*) CURRENT_BLOCK="resp"; continue ;;
        esac
        if echo "$line" | grep -qE '^[[:space:]]*-[[:space:]]+[A-Za-z_][A-Za-z0-9_]*'; then
            ITEM=$(echo "$line" | sed -E 's/^[[:space:]]*-[[:space:]]+//' | awk '{print $1}')
            case "$CURRENT_BLOCK" in
                required) REQUIRED="$REQUIRED $ITEM" ;;
                param) PARAM_SUB="$PARAM_SUB $ITEM" ;;
                resp) RESP_SUB="$RESP_SUB $ITEM" ;;
            esac
        fi
    done < "$MANIFEST"
fi

# ---------- 3. trim 空格 + 输出 ----------
trim() {
    echo "$1" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/[[:space:]]+/ /g'
}

REQUIRED=$(trim "$REQUIRED")
PARAM_SUB=$(trim "$PARAM_SUB")
RESP_SUB=$(trim "$RESP_SUB")

TMP=$(mktemp)
{
    echo "${REQUIRED:-tags summary description parameters responses}"
    echo "${PARAM_SUB:-description example}"
    echo "${RESP_SUB:-schema examples}"
} > "$TMP"

# 软提示(非阻断,仅在用户主动看 stderr 时可见)
[ "$SOURCE" = "project" ] && \
    echo "[mcpowers swagger-required-fields] 使用项目自定义清单:$PROJECT_MANIFEST" >&2

echo "$TMP"
