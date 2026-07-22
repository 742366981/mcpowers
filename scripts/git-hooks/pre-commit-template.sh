#!/usr/bin/env bash
# mcpowers 自更新 pre-commit hook 模板
# 作用：commit 前自动跑 check-readme-sync.sh + plugin-verify.sh，任一失败即阻塞。
# 安装方式：bash scripts/git-hooks/install.sh
#         或手动 git config core.hooksPath scripts/git-hooks
#         或手动 cp scripts/git-hooks/pre-commit-template.sh .git/hooks/pre-commit && chmod +x
#
# v2.9.0: 新增（解决"改了技能数/版本号等数字声明忘改其他地方"漏改问题）

set -e

REPO_DIR="$(git rev-parse --show-toplevel)"

echo "[pre-commit] 跑 check-readme-sync.sh ..."
if ! bash "$REPO_DIR/scripts/check-readme-sync.sh"; then
    echo ""
    echo "✗ pre-commit 中止：文档/技能/版本号同步校验失败。"
    echo "  详见上方 FAIL 项；改完后重新 git commit 即可。"
    exit 1
fi

echo ""
echo "[pre-commit] 跑 plugin-verify.sh ..."
if ! bash "$REPO_DIR/tests/plugin-verify.sh"; then
    echo ""
    echo "✗ pre-commit 中止：插件结构校验失败。"
    echo "  详见上方断言失败项；改完后重新 git commit 即可。"
    exit 1
fi

echo ""
echo "✓ pre-commit 通过，commit 继续。"
exit 0
