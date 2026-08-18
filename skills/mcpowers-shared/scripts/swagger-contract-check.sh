#!/usr/bin/env bash
# mcpowers swagger 接口契约集中 helper(v2.31.0+)
#
# 完整流程:
#   1. swagger-stack-detect.sh → 项目是否装了 swagger(无 → exit 0 放行)
#   2. swagger-required-fields.sh → 加载字段清单(项目优先 + 默认 fallback)
#   3. swagger-lint-helper.py → 单文件 lint(违规 → exit 2 触发 confirm UI)
#
# 被 wrapper hook(由 pre-write-confirm-api-hint.sh 改造而成)调用:
#   bash swagger-contract-check.sh --file-path=<rel_path>
#
# 退出码语义(与 doc-sync-check.sh:32 一致):
#   0 = 检查通过或无需检查
#   2 = 检测到违规(Claude Code confirm UI 弹窗)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECT_SH="$SCRIPT_DIR/swagger-stack-detect.sh"
FIELDS_SH="$SCRIPT_DIR/swagger-required-fields.sh"
LINT_PY="$SCRIPT_DIR/swagger-lint-helper.py"

# ---------- 解析参数 ----------
FILE_PATH=""
# v4.5.2+ PreToolUse wrapper 可传 --content-file=<tmp_path>,含用户即将写入/修改的代码;
#       PostToolUse wrapper 不传(读磁盘即可);helper 优先用 content-file,缺失则回退磁盘
CONTENT_FILE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --file-path=*)
            FILE_PATH="${1#--file-path=}"
            ;;
        --content-file=*)
            CONTENT_FILE="${1#--content-file=}"
            ;;
        *)
            # 忽略未知参数(兼容性)
            ;;
    esac
    shift
done

if [ -z "$FILE_PATH" ]; then
    exit 0  # 无 file_path → 不查(防呆)
fi

# ---------- 路径归一化 ----------
# FILE_PATH 可能是绝对 / 相对(对 CLAUDE_PROJECT_DIR)。lint-helper 内部用 Path.exists()
# 检查相对当前 cwd,如果用户项目目录 ≠ 当前 cwd 就会误报"文件不存在"。
# 这里统一转绝对路径传给 lint-helper。
if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    case "$FILE_PATH" in
        /*|[A-Za-z]:/*) ;;  # 已是绝对路径
        *) FILE_PATH="$CLAUDE_PROJECT_DIR/$FILE_PATH" ;;
    esac
fi

# ---------- Step 1: 探测项目 swagger 栈 ----------
if [ ! -f "$DETECT_SH" ]; then
    # helper 缺失(开发期/卸载期)→ 放行
    exit 0
fi

if ! bash "$DETECT_SH" >/dev/null 2>&1; then
    # 项目未装 swagger → exit 0,不骚扰
    exit 0
fi

# ---------- Step 2: 加载字段清单 ----------
if [ ! -f "$FIELDS_SH" ]; then
    exit 0  # helper 缺失 → 放行
fi

FIELDS_FILE=$(bash "$FIELDS_SH" 2>/dev/null)
if [ -z "$FIELDS_FILE" ] || [ ! -f "$FIELDS_FILE" ]; then
    # 字段清单生成失败 → 放行(避免 lint 自身 bug 阻塞)
    exit 0
fi

# ---------- Step 3: 跑 lint ----------
if [ ! -f "$LINT_PY" ]; then
    rm -f "$FIELDS_FILE"
    exit 0  # helper 缺失 → 放行
fi

# 探测可用 python
PY=""
for cand in python python3 py; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
            PY="$cand"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    rm -f "$FIELDS_FILE"
    exit 0  # 无 python → 放行(Windows 兜底)
fi

# 跑 lint,exit 0/2 透传
LINT_ARGS=(--file-path="$FILE_PATH" --fields-file="$FIELDS_FILE")
if [ -n "$CONTENT_FILE" ] && [ -f "$CONTENT_FILE" ]; then
    LINT_ARGS+=(--content-file="$CONTENT_FILE")
fi
"$PY" "$LINT_PY" "${LINT_ARGS[@]}" || LINT_EXIT=$?
LINT_EXIT=${LINT_EXIT:-0}

# 清理临时文件
rm -f "$FIELDS_FILE"

exit "$LINT_EXIT"
