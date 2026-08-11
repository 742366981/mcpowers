#!/usr/bin/env bash
# mcpowers 集中 doc-sync 检查脚本（v2.29.0+ 强制）
#
# 三类检查：
#   path_in_doc    README 中提到的 scripts/*.sh / bin/*.py 路径必须真实存在
#   route_in_doc   @app.route / createRouter 定义的路径必须出现在 API 文档或视图 docstring
#   env_in_doc     .env.example 中所有 KEY 必须在配置文档说明
#
# 调用方（两个）：
#   1. hooks/pre-write-check-doc-sync.sh — PreToolUse(Write|Edit|MultiEdit) 物理拦截
#   2. AI 在对话里手动跑：bash ${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/scripts/doc-sync-check.sh
#
# v2.29.0 设计动机：
#   集中纪律：用户装 mcpowers 后自动支持，**不向用户项目注入任何文件**。
#   替代 v2.9.0 引入的 doc-sync-install 技能 [已废弃] + scripts/templates/ 模板。
#
# 用法：
#   bash doc-sync-check.sh                            # 全量检查（cwd 必须是 git 仓库根）
#   bash doc-sync-check.sh --file-path=<rel_path>     # 单文件触发（hook 调用）
#   bash doc-sync-check.sh --no-fail                  # 仅警告不阻断（CI 首次接入）
#
# 退出码：
#   0 = 通过
#   2 = 检测到不一致（hook 会触发 Claude Code confirm UI）

set -e

NO_FAIL=false
TARGET_FILE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --file-path=*) TARGET_FILE="${1#--file-path=}" ;;
        --no-fail) NO_FAIL=true ;;
    esac
    shift
done

# 必须 cd 到 git 仓库根（hook 调用时 cwd 是 Claude Code 当前目录，可能不是 git 根）
WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$WORK_DIR" 2>/dev/null || { echo "✗ 无法进入工作目录: $WORK_DIR"; exit 0; }

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    # 非 git 仓库 → 跳过（mcpowers 装在非 git 项目里也常见）
    exit 0
fi

VIOLATIONS=0
WARNINGS=()

# ============================================================
# 检查 1：path_in_doc
# 读 README.md 提取 ```scripts/xxx.sh``` ```bin/yyy.py``` 等代码块路径
# 验证每个路径真实存在
# ============================================================
check_path_in_doc() {
    local doc="$1"
    [ -f "$doc" ] || return 0

    # 提取 ```scripts/xxx.sh``` 或 ```bin/yyy.py``` 形式路径（围栏代码块内）
    # 同时支持 README.md / docs/*.md
    local hits
    hits=$(grep -oE '`(scripts|bin|tools)/[a-zA-Z0-9_./-]+(\.(sh|py|js|ts))?`' "$doc" 2>/dev/null | tr -d '`' | sort -u || true)

    [ -z "$hits" ] && return 0

    while IFS= read -r path; do
        [ -z "$path" ] && continue
        if [ ! -f "$path" ] && [ ! -d "$path" ]; then
            echo "✗ [path_in_doc] $doc 引用了不存在的路径: $path"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done <<< "$hits"
}

# ============================================================
# 检查 2：route_in_doc
# 扫 app/*.py / src/router/*.ts 提取路由定义
# 验证每条路径在 docs/API文档/API文档.md 或视图 docstring 出现
# ============================================================
check_route_in_doc() {
    local code_dir="$1"
    local doc="$2"
    [ -d "$code_dir" ] || return 0

    # 提取 Flask @app.route('/xxx') 或 @xxx_bp.route('/xxx') 的路径
    local routes
    routes=$(grep -rohE "@[a-zA-Z_]+\.route\(\s*['\"][^'\"]+['\"']([^)]*)\)" "$code_dir" 2>/dev/null \
        | grep -oE "['\"][^'\"]+['\"]" | tr -d "'\"" | sort -u || true)

    # 提取 Vue/JS createRouter path: '/xxx'
    local vue_routes
    vue_routes=$(grep -rohE "path:\s*['\"][^'\"]+['\"]" "$code_dir" 2>/dev/null \
        | grep -oE "['\"][^'\"]+['\"]" | tr -d "'\"" | sort -u || true)
    routes=$(printf "%s\n%s\n" "$routes" "$vue_routes" | grep -v '^$' | sort -u)

    [ -z "$routes" ] && return 0

    # 过滤明显非路径的行（动态参数、特殊字符串）
    routes=$(echo "$routes" | grep -E "^/" | head -50 || true)
    [ -z "$routes" ] && return 0

    # 如果 doc 不存在则跳过（不阻断首次接入）
    [ -f "$doc" ] || return 0

    while IFS= read -r route; do
        [ -z "$route" ] && continue
        # 跳过参数化路由的精确匹配（只检查路径前缀）
        local prefix
        prefix=$(echo "$route" | sed 's/<[^>]*>//g' | sed 's/:[a-zA-Z_][a-zA-Z0-9_]*/[^\/]*/g')
        if ! grep -qE "$route|$prefix" "$doc" 2>/dev/null; then
            echo "✗ [route_in_doc] 路由 $route 未在 $doc 提及"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done <<< "$routes"
}

# ============================================================
# 检查 3：env_in_doc
# 读 .env.example 提取 ^[A-Z_]+= 所有 KEY
# 验证每个变量名在配置文档说明
# ============================================================
check_env_in_doc() {
    local env_file="$1"
    local doc="$2"
    [ -f "$env_file" ] || return 0
    [ -f "$doc" ] || return 0

    # 提取 KEY=xxx 形式（排除注释行和空行）
    local keys
    keys=$(grep -E "^[A-Z_][A-Z0-9_]*=" "$env_file" 2>/dev/null \
        | cut -d= -f1 | sort -u || true)

    [ -z "$keys" ] && return 0

    while IFS= read -r key; do
        [ -z "$key" ] && continue
        if ! grep -qE "\b$key\b" "$doc" 2>/dev/null; then
            echo "✗ [env_in_doc] 环境变量 $key 未在 $doc 说明"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done <<< "$keys"
}

# ============================================================
# 主逻辑：决定跑哪些检查
# ============================================================
echo "=== doc-sync 校验（$WORK_DIR） ==="
echo ""

if [ -n "$TARGET_FILE" ]; then
    # Hook 调用：单文件触发，按文件路径分流
    case "$TARGET_FILE" in
        *README.md|*readme.md)
            check_path_in_doc "$TARGET_FILE"
            ;;
        *scripts/*|*/scripts/*)
            check_path_in_doc "README.md"
            check_path_in_doc "docs/README.md"
            ;;
        *app/*.py|*api/*.py|*src/router/*.ts|*src/api/*.ts|*crawlers/*.py)
            check_route_in_doc "$(dirname "$TARGET_FILE")" "docs/API文档/API文档.md"
            check_route_in_doc "$(dirname "$TARGET_FILE")" "docs/api.md"
            check_route_in_doc "app" "docs/API文档/API文档.md"
            check_route_in_doc "app" "docs/api.md"
            check_route_in_doc "src/router" "docs/API文档/API文档.md"
            check_route_in_doc "src/api" "docs/api.md"
            check_route_in_doc "crawlers" "docs/API文档/API文档.md"
            ;;
        *.env.example|requirements.txt|package.json)
            check_env_in_doc ".env.example" "README.md"
            check_env_in_doc ".env.example" "docs/配置说明.md"
            check_env_in_doc ".env.example" "docs/部署.md"
            ;;
        *)
            exit 0
            ;;
    esac
else
    # 全量检查（AI 手动跑或初次接入）
    check_path_in_doc "README.md"
    check_path_in_doc "docs/README.md"
    check_route_in_doc "app" "docs/API文档/API文档.md"
    check_route_in_doc "app" "docs/api.md"
    check_route_in_doc "src/router" "docs/API文档/API文档.md"
    check_route_in_doc "src/api" "docs/api.md"
    check_route_in_doc "crawlers" "docs/API文档/API文档.md"
    check_env_in_doc ".env.example" "README.md"
    check_env_in_doc ".env.example" "docs/配置说明.md"
    check_env_in_doc ".env.example" "docs/部署.md"
fi

echo ""
if [ "$VIOLATIONS" -gt 0 ]; then
    if [ "$NO_FAIL" = true ]; then
        echo "⚠️  共 $VIOLATIONS 项不一致（--no-fail 模式，仅警告不阻断）"
        exit 0
    fi
    echo "❌ 共 $VIOLATIONS 项不一致"
    echo "   修复：在对应文档（README.md / docs/api.md / docs/配置说明.md 等）补齐引用"
    echo "   或忽略：直接 commit 时选择「确认通过」（Claude Code confirm UI 会询问）"
    exit 2
fi

echo "✅ doc-sync 检查通过"
exit 0