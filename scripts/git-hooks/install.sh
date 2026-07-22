#!/usr/bin/env bash
# mcpowers pre-commit hook 安装脚本（幂等）
# v2.9.0: 用 git config core.hooksPath 把 hooks 目录指向 scripts/git-hooks
#
# 用法：
#   bash scripts/git-hooks/install.sh
#
# 行为：
#   - 若已设置过：提示当前状态，不重复设置
#   - 若未设置：执行 git config core.hooksPath scripts/git-hooks
#   - 设置后所有 git 命令走 scripts/git-hooks/ 下的 hook
#
# 卸载：
#   git config --unset core.hooksPath
#   或：git config core.hooksPath .git/hooks

set -e

REPO_DIR="$(git rev-parse --show-toplevel)"
cd "$REPO_DIR"

CURRENT=$(git config --get core.hooksPath || echo "")

if [ "$CURRENT" = "scripts/git-hooks" ]; then
    echo "✓ core.hooksPath 已设置为 scripts/git-hooks（无需操作）"
    exit 0
fi

if [ -n "$CURRENT" ]; then
    echo "⚠ 当前 core.hooksPath = $CURRENT（与本仓库推荐值不同）"
    echo "  仍要切换到 scripts/git-hooks？[y/N]"
    read -r ans
    case "$ans" in
        [yY]*) ;;
        *) echo "已跳过，未修改"; exit 0 ;;
    esac
fi

git config core.hooksPath scripts/git-hooks
echo "✓ 已设置 core.hooksPath = scripts/git-hooks"
echo "  下次 git commit 自动跑 scripts/git-hooks/pre-commit-template.sh"
