#!/usr/bin/env bash
# scripts/check-min-module.sh
# §0 绝对零业务审计（v2.28.1+ 定义性铁律）
# 用法：bash scripts/check-min-module.sh {module_dir}/ [--exclude PATTERN]...
#   PATTERN 为 rg --glob '!PATTERN' 形式（如 '!SKILL.md' / '!*README.md'）
# 退出码：0 通过 / 1 有命中（打印命中位置） / 2 参数错误
#
# 示例：
#   bash scripts/check-min-module.sh my_module/
#   bash scripts/check-min-module.sh my_module/ --exclude SKILL.md --exclude README.md
#   bash scripts/check-min-module.sh skills/ --exclude SKILL.md --exclude '*.md'

set -u

if [[ $# -lt 1 ]]; then
  echo "用法：bash $0 {module_dir}/ [--exclude PATTERN]..."
  echo ""
  echo "示例："
  echo "  bash $0 my_module/"
  echo "  bash $0 my_module/ --exclude SKILL.md --exclude '*.md'"
  exit 2
fi

target="$1"
shift

# 解析 --exclude 参数（多个）
declare -a exclude_globs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --exclude)
      exclude_globs+=("!$2")
      shift 2
      ;;
    *)
      echo "[FAIL] 未知参数：$1"
      exit 2
      ;;
  esac
done

if [[ ! -d "$target" ]]; then
  echo "[FAIL] 目录不存在：$target"
  exit 2
fi

# 排除自身（防止扫描脚本本身命中"参考"等关键词）
target_abs=$(cd "$target" && pwd)

RED='\033[0;31m'
GREEN='\033[0m'
YELLOW='\033[1;33m'
NC='\033[0m'

declare -i total_hits=0
declare -i fail_count=0

# 构建 rg 排除参数
build_exclude_args() {
  local args=()
  for glob in "${exclude_globs[@]:-}"; do
    args+=("--glob" "$glob")
  done
  echo "${args[@]}"
}
exclude_args=$(build_exclude_args)

scan() {
  local label="$1"
  local pattern="$2"
  local description="$3"

  echo ""
  echo "─── [$label] $description ───"

  # shellcheck disable=SC2086,SC2046
  local hits
  hits=$(rg --no-heading -n $exclude_args "$pattern" "$target" 2>/dev/null | grep -v "^${target_abs}/\(check-min-module.sh\)" || true)

  if [[ -z "$hits" ]]; then
    echo -e "  ${GREEN}✓ 通过${NC}：零命中"
  else
    echo -e "  ${RED}✗ FAIL${NC}：发现命中"
    echo "$hits" | head -20 | sed 's/^/    /'
    local hit_count
    hit_count=$(echo "$hits" | wc -l | tr -d ' ')
    if [[ "$hit_count" -gt 20 ]]; then
      echo "    ...（共 ${hit_count} 处命中，仅显示前 20 行）"
    fi
    total_hits=$((total_hits + hit_count))
    fail_count=$((fail_count + 1))
  fi
}

echo "═══════════════════════════════════════════════════════════════"
echo "  §0 绝对零业务审计（v2.28.1+ 定义性铁律）"
echo "  目标目录：$target"
if [[ ${#exclude_globs[@]} -gt 0 ]]; then
  echo "  排除规则：${exclude_globs[*]}"
fi
echo "═══════════════════════════════════════════════════════════════"

# 1. 业务字眼（按需替换具体词；脚本默认扫描常见业务模式）
scan "1/7 业务字眼" \
  '(?i)(order_status|payment_token|payment_pending|order_id|user_id|api_key|secret_key|access_token|refresh_token|client_id|tenant_id|org_id)' \
  "常见业务字段名（按需替换为你的项目具体业务字眼）"

# 2. 具体路径字面值
scan "2/7 路径字面值" \
  'C:\\|D:\\|/Users/[^/]+/|/home/[^/]+/|C:/|D:/' \
  "Windows / Linux / macOS 机器路径字面值"

# 3. 环境变量读取
scan "3/7 环境变量读取" \
  'os\.getenv|os\.environ|process\.env|\$\{ENV[A-Z_]*\}' \
  "Python / Node / Shell 环境变量读取"

# 4. 真实凭据
scan "4/7 真实凭据" \
  'sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|Bearer [A-Za-z0-9._-]{20,}|ghp_[A-Za-z0-9]{36}' \
  "API key / AWS access key / Bearer token / GitHub token"

# 5. 外部参考字眼
scan "5/7 外部参考字眼" \
  '(?i)(参考|引用|参照|借鉴|致谢|致敬|改进自|参考:|reference:|see also|详见|参见|类似|based on|inspired by)' \
  "含中文 / 英文「参考 / 引用 / 借鉴 / 致谢 / 类似」字眼"

# 6. 其他项目路径（含抽象项目路径）
scan "6/7 其他项目路径" \
  '<project|<your.*project|<your_workspace|<repo_root|<app_root|<project_root>|<your_app>|<your_repo>' \
  "抽象项目路径占位符（即使是占位符也禁止——只能用 Path.home() / Path(__file__).parent）"

# 7. 模块名 / 文件名业务前缀（文件级扫描）
echo ""
echo "─── [7/7] 模块名 / 文件名业务前缀 ───"
bad_files=$(find "$target" -type f \( -name "*order*" -o -name "*payment*" -o -name "*bangkokair*" -o -name "*user*" -o -name "*auth*" -o -name "*business*" \) 2>/dev/null || true)
if [[ -z "$bad_files" ]]; then
  echo -e "  ${GREEN}✓ 通过${NC}：零业务前缀文件名"
else
  echo -e "  ${RED}✗ FAIL${NC}：发现业务前缀文件"
  echo "$bad_files" | head -10 | sed 's/^/    /'
  local_count=$(echo "$bad_files" | wc -l | tr -d ' ')
  if [[ "$local_count" -gt 10 ]]; then
    echo "    ...（共 ${local_count} 个文件，仅显示前 10 个）"
  fi
  total_hits=$((total_hits + local_count))
  fail_count=$((fail_count + 1))
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  审计汇总"
echo "═══════════════════════════════════════════════════════════════"
echo "  目标：$target"
if [[ ${#exclude_globs[@]} -gt 0 ]]; then
  echo "  排除规则：${exclude_globs[*]}"
fi
echo "  扫描项：7 类"
echo "  命中类别数：$fail_count / 7"
echo "  命中条目总数：$total_hits"
echo ""

if [[ "$fail_count" -eq 0 ]]; then
  echo -e "  ${GREEN}✓ §0 审计通过——可称为 min-module / SDK${NC}"
  exit 0
else
  echo -e "  ${RED}✗ §0 审计不通过——不是 min-module / SDK${NC}"
  echo -e "  ${YELLOW}提示：替换业务字眼为抽象占位符；删除参考字眼；移除具体路径${NC}"
  exit 1
fi