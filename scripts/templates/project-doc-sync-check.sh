#!/usr/bin/env bash
# scripts/check-doc-sync.sh
# 用户项目级 doc-sync 校验器（v2.9.0 L2，由 mcpowers-doc-sync-install 注入）
#
# 用法：
#   bash scripts/check-doc-sync.sh
#   # 或作为 git pre-commit hook 触发（详见 mcpowers-doc-sync-install）
#
# 读取项目根 .doc-sync-rules.yml，逐条跑 enabled 规则，FAIL 退出 1。
# 没有依赖（纯 bash + grep + find），可独立运行。
#
# 规则类型（3 个内置）：
#   route_in_doc   从 code_dir 下指定扩展名的文件中提 code_regex 命中，
#                  要求每个命中字符串在 doc_file 中出现
#                  适用：Flask @app.route / Vue router path / 任意 URL 模式
#   env_in_doc     读 env_file，匹配 code_regex（如 ^[A-Z_]+=）提所有变量，
#                  要求每个变量名在 doc_file 中被提及
#                  适用：.env.example 中所有 KEY 必须在配置文档说明
#   path_in_doc    从 doc_file 提取 ```scripts/xxx.sh``` ```bin/yyy.py``` 等代码块，
#                  验证每个路径真实存在
#                  适用：README 中引用的脚本路径都必须真实存在
#
# v2.9.0：初版（项目级纪律）

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"
RULES_FILE=".doc-sync-rules.yml"
FAIL=0

if [ ! -f "$RULES_FILE" ]; then
    echo "✗ $RULES_FILE 不存在"
    echo "  解决：跑 mcpowers-doc-sync-install 初始化，或 touch 空文件禁用检查"
    exit 2
fi

echo "=== doc-sync 校验（$PROJECT_ROOT） ==="
echo ""

# 极简 DSL（避免外部 YAML 依赖）：
#   RULE_START <rule_name>
#   enabled=true|false
#   type=route_in_doc|env_in_doc|path_in_doc
#   跟随规则类型需要的字段
#   RULE_END

in_rule=0
r_name=""
r_enabled=""
r_type=""
r_code_dir=""
r_code_ext=""
r_code_regex=""
r_env_file=""
r_doc_file=""

reset_rule() {
    in_rule=0; r_name=""; r_enabled=""; r_type=""
    r_code_dir=""; r_code_ext=""; r_code_regex=""; r_env_file=""; r_doc_file=""
}

run_rule() {
    [ "$r_enabled" = "true" ] || return 0
    case "$r_type" in
        route_in_doc) check_route_in_doc ;;
        env_in_doc)   check_env_in_doc ;;
        path_in_doc)  check_path_in_doc ;;
        *) echo "  ⚠ [$r_name] 未知规则类型: $r_type（跳过）" ;;
    esac
}

check_route_in_doc() {
    echo "[规则 $r_name] route_in_doc: dir=$r_code_dir ext=$r_code_ext"
    if [ ! -d "$r_code_dir" ]; then
        echo "  ⚠ dir 不存在: $r_code_dir（跳过）"
        return
    fi
    if [ ! -f "$r_doc_file" ]; then
        echo "  ✗ doc 文件不存在: $r_doc_file"
        FAIL=$((FAIL + 1))
        return
    fi
    # 用 code_regex 命中整段，再用 grep -oE 从命中里提 /path 这种路径子串。
    # 这样用户写 regex 时不用关心 capture group——只要能匹配 `@app.route('/foo'`
    # 样式即可，路径本身由后处理统一抽出。
    local hits
    hits=$(find "$r_code_dir" -name "*.$r_code_ext" -type f -exec grep -hoE "$r_code_regex" {} + 2>/dev/null \
        | grep -oE '/[a-zA-Z][a-zA-Z0-9_./-]*' \
        | sort -u || true)
    if [ -z "$hits" ]; then
        echo "  ℹ 无匹配（dir 下没找到 code_regex 命中）"
        return
    fi
    local missing=0
    while IFS= read -r hit; do
        [ -z "$hit" ] && continue
        if ! grep -qF "$hit" "$r_doc_file" 2>/dev/null; then
            echo "  ✗ 代码路径未在 $r_doc_file 中提及: $hit"
            missing=$((missing + 1))
        fi
    done <<< "$hits"
    if [ "$missing" -eq 0 ]; then
        echo "  ✓ 全部提及"
    else
        FAIL=$((FAIL + missing))
    fi
}

check_env_in_doc() {
    echo "[规则 $r_name] env_in_doc: file=$r_env_file"
    if [ ! -f "$r_env_file" ]; then
        echo "  ⚠ env 文件不存在: $r_env_file（跳过）"
        return
    fi
    if [ ! -f "$r_doc_file" ]; then
        echo "  ✗ doc 文件不存在: $r_doc_file"
        FAIL=$((FAIL + 1))
        return
    fi
    local vars
    vars=$(grep -hoE "$r_code_regex" "$r_env_file" 2>/dev/null | sed 's/=$//' | sort -u || true)
    if [ -z "$vars" ]; then
        echo "  ℹ env 文件无匹配"
        return
    fi
    local missing=0
    while IFS= read -r v; do
        [ -z "$v" ] && continue
        if ! grep -qF "$v" "$r_doc_file" 2>/dev/null; then
            echo "  ✗ env 变量未在 $r_doc_file 中提及: $v"
            missing=$((missing + 1))
        fi
    done <<< "$vars"
    if [ "$missing" -eq 0 ]; then
        echo "  ✓ 全部提及"
    else
        FAIL=$((FAIL + missing))
    fi
}

check_path_in_doc() {
    echo "[规则 $r_name] path_in_doc: doc=$r_doc_file（README 中提到的脚本路径必须真实存在）"
    if [ ! -f "$r_doc_file" ]; then
        echo "  ℹ doc 不存在: $r_doc_file（跳过）"
        return
    fi
    local paths
    paths=$(grep -oE '`(scripts|bin|tools)/[a-zA-Z0-9_./-]+\.(sh|py|js|ts)`' "$r_doc_file" 2>/dev/null \
        | tr -d '`' | sort -u || true)
    if [ -z "$paths" ]; then
        echo "  ℹ doc 中无脚本路径"
        return
    fi
    local missing=0
    while IFS= read -r p; do
        [ -z "$p" ] && continue
        if [ ! -f "$p" ]; then
            echo "  ✗ doc 提到但不存在的脚本: $p"
            missing=$((missing + 1))
        fi
    done <<< "$paths"
    if [ "$missing" -eq 0 ]; then
        echo "  ✓ 全部路径存在"
    else
        FAIL=$((FAIL + missing))
    fi
}

while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
        RULE_START*) run_rule; reset_rule
                     in_rule=1
                     r_name="${line#RULE_START }"
                     ;;
        enabled=*)    r_enabled="${line#enabled=}" ;;
        type=*)       r_type="${line#type=}" ;;
        code_dir=*)   r_code_dir="${line#code_dir=}" ;;
        code_ext=*)   r_code_ext="${line#code_ext=}" ;;
        code_regex=*) r_code_regex="${line#code_regex=}" ;;
        env_file=*)   r_env_file="${line#env_file=}" ;;
        doc_file=*)   r_doc_file="${line#doc_file=}" ;;
        RULE_END)     run_rule; reset_rule ;;
    esac
done < "$RULES_FILE"
run_rule
reset_rule

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "=== ✓ 全部 doc-sync 规则通过 ==="
    exit 0
else
    echo "=== ✗ $FAIL 项不一致 ==="
    exit 1
fi
