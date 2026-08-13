#!/usr/bin/env bash
# mcpowers 文档画蛇添足字眼软门禁（v4.0.2+）
# 触发：PostToolUse(Write|Edit|MultiEdit)
# 行为：扫禁用字眼 + 路径白名单区分场景；exit 0 + stderr 提示（不阻断）
# 共享常量：${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt
#
# 退出码：
#   0 = 始终放行（软门禁）
#   1 = 自身脚本错误（stdin 解析失败 / 常量文件缺失）—— 放行，不阻断 AI 流程

set -euo pipefail

# 1. 读 stdin JSON（Claude Code PostToolUse 触发）
input=$(cat)
if [ -z "$input" ]; then
  exit 0
fi

# 2. 提取 file_path + content（用 grep -o 简单提取，避开 jq 依赖）
file_path=$(echo "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
content=$(echo "$input" | grep -o '"content"[[:space:]]*:[[:space:]]*"\(.*\)"' | head -1 | sed 's/.*"content"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/')

# 提取不到 content（Edit 而非 Write）—— 放行（diff 由 R16 兜底）
if [ -z "$content" ]; then
  exit 0
fi

# 3. 只对 .md 文件触发
case "$file_path" in
  *.md) ;;
  *) exit 0 ;;
esac

# 4. 路径白名单（6 类）—— 命中即跳过
#    路径后缀或路径段匹配任意一个即可
#    顺序：CHANGELOG / 历史教训 / spec-index / API契约 / 迁移 / deprecation
whitelist_hit=0
case "$file_path" in
  *CHANGELOG.md|*CHANGELOG*.md)            whitelist_hit=1 ;;
  *历史教训*)                                whitelist_hit=1 ;;
  *mcpowers-spec-index*)                    whitelist_hit=1 ;;
  *API契约/*|*API契约*|*API_contract/*)     whitelist_hit=1 ;;
  *迁移*|*migration*|*Migration*|*migrate*) whitelist_hit=1 ;;
  *deprecation*|*Deprecation*|*DEPRECATED*) whitelist_hit=1 ;;
  *README.md|*README_*.md)                  whitelist_hit=1 ;;  # README「最近变更」段落允许
esac
if [ "$whitelist_hit" -eq 1 ]; then
  exit 0
fi

# 5. 加载共享常量（${CLAUDE_PLUGIN_ROOT} —— hooks 唯一允许环境变量场景）
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$PLUGIN_ROOT" ]; then
  # 兜底：尝试从脚本相对路径回溯
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
fi

FORBIDDEN_FILE="$PLUGIN_ROOT/skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt"
if [ ! -f "$FORBIDDEN_FILE" ]; then
  # 兜底：常量文件缺失 —— 放行（不阻断 AI 流程）
  exit 0
fi

# 读字眼清单（过滤 # 注释 + 空行）
# 用 while read 让多词字眼（如 "see also"）保持完整，不被 shell IFS 拆开
forbidden_words=$(grep -v '^#' "$FORBIDDEN_FILE" | grep -v '^$' || true)
if [ -z "$forbidden_words" ]; then
  exit 0
fi

# 6. 扫禁用字眼（按行扫，命中文本行）
violations=""
line_num=0
while IFS= read -r line; do
  line_num=$((line_num + 1))
  # 跳过 YAML 字段名行（仿 swagger-lint-helper 跳过规则）
  stripped=$(echo "$line" | sed 's/^[[:space:]]*//')
  if [ "${stripped%:}" != "$stripped" ] && [ "${#stripped}" -gt 1 ] && ! echo "$stripped" | grep -q '^#'; then
    # 以 ":" 结尾且 > 1 字符且非 # 开头 → YAML 字段名行，跳过
    continue
  fi
  # 字眼扫描（大小写不敏感）
  line_lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
  hit_word=""
  while IFS= read -r word; do
    [ -z "$word" ] && continue
    word_lower=$(echo "$word" | tr '[:upper:]' '[:lower:]')
    if echo "$line_lower" | grep -qF "$word_lower"; then
      hit_word="$word"
      break  # 一行只报第一个
    fi
  done <<< "$forbidden_words"
  if [ -n "$hit_word" ]; then
    violations="${violations}${file_path}:L${line_num}:「${hit_word}」"$'\n'
  fi
done <<< "$content"

# 7. 输出提示（exit 0 不阻断）
if [ -n "$violations" ]; then
  echo "⚠️  [post-write-check-doc-content] 检测到画蛇添足字眼（v4.0.2+ 文档零引用铁律）：" >&2
  echo "" >&2
  while IFS= read -r v; do
    [ -n "$v" ] && echo "  ❌ $v" >&2
  done <<< "$violations"
  echo "" >&2
  echo "💡 决策 3 问（详见 文档编写规范.md §9.5）：" >&2
  echo " ① 这段文字是给谁看的？" >&2
  echo " ② 删掉「参考/参见/详见/引用」等字眼后意思会变吗？" >&2
  echo " ③ 输出型禁止 / 参考型允许且必要 / 历史型允许——按 §9.5 类型判定" >&2
  echo "" >&2
  echo "  路径白名单（命中可保留字眼）：CHANGELOG.md / 历史教训 / mcpowers-spec-index / API契约 / 迁移 / deprecation / README.md" >&2
  echo "  若你确认这是参考型 / 历史型文档，请手动加进本脚本路径白名单（line 47-53）" >&2
fi

exit 0
