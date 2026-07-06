#!/usr/bin/env bash
# mcpowers 卸载脚本
#
# 用法：
#   bash uninstall.sh          # 交互式（要求 y/N 确认）
#   bash uninstall.sh --yes    # 跳过确认
#   bash uninstall.sh -y
#
# 安全：只删 mcpowers* 前缀的目录，不碰用户的 find-skills / skill-creator 等其他技能

set -e

# ============== 解析参数 ==============
AUTO_YES=false
case "${1:-}" in
    --yes|-y) AUTO_YES=true ;;
esac

SKILLS_DIR="$HOME/.claude/skills"
COMMANDS_DIR="$HOME/.claude/commands"

# ============== 列出待删内容 ==============
echo "=== mcpowers 卸载 ==="
echo

TARGETS=()
[ -e "$SKILLS_DIR/mcpowers" ] && TARGETS+=("$SKILLS_DIR/mcpowers")
[ -e "$SKILLS_DIR/mcpowers-shared" ] && TARGETS+=("$SKILLS_DIR/mcpowers-shared")
for d in "$SKILLS_DIR"/mcpowers-*; do
    [ -d "$d" ] || continue
    case "$(basename "$d")" in
        mcpowers|mcpowers-shared) ;;  # 已在上面处理
        *) TARGETS+=("$d") ;;
    esac
done
[ -e "$COMMANDS_DIR/mcpowers" ] && TARGETS+=("$COMMANDS_DIR/mcpowers")

if [ ${#TARGETS[@]} -eq 0 ]; then
    echo "✓ 没有找到 mcpowers 相关的安装，无需卸载"
    exit 0
fi

echo "将删除以下 ${#TARGETS[@]} 项："
for t in "${TARGETS[@]}"; do
    # 区分是 symlink 还是目录
    if [ -L "$t" ]; then
        echo "  - $t (symlink → $(readlink "$t"))"
    else
        echo "  - $t"
    fi
done
echo

# ============== 确认 ==============
if [ "$AUTO_YES" = false ]; then
    read -p "确认删除？[y/N] " answer
    case "$answer" in
        y|Y|yes|YES) ;;
        *) echo "已取消"; exit 0 ;;
    esac
fi

# ============== 执行删除 ==============
for t in "${TARGETS[@]}"; do
    rm -rf "$t"
    echo "  ✓ 删除 $t"
done

echo
echo "=== 卸载完成 ==="
echo "  （不影响 find-skills、skill-creator 等其他技能）"
echo
echo "如需重装: bash install.sh"
