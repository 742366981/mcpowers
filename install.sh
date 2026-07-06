#!/usr/bin/env bash
# mcpowers 一键安装脚本（symlink 模式，参考 superpowers）
#
# 设计原则：
#   - 用 symlink 引用源文件，编辑源文件后立即生效，无需重装
#   - 升级 = git pull（无需重装）
#   - 幂等：重复运行结果一致
#   - 自动检测并替换旧安装（copy 或断链的 symlink）
#
# 用法：
#   bash install.sh                # 默认 symlink 模式
#   bash install.sh --copy         # 复制模式（无 symlink 权限时使用）
#
# 仓库地址：git@github.com:742366981/mcpowers.git

set -e

# ============== 解析参数 ==============
MODE="symlink"
if [ "${1:-}" = "--copy" ]; then
    MODE="copy"
fi

# ============== 定位源和目标 ==============
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

# ============== 预检 ==============
if [ ! -d "$HOME/.claude" ]; then
    echo "✗ ~/.claude 不存在，请先安装 Claude Code"
    exit 1
fi
mkdir -p "$SKILLS_DIR"

# ============== 打印头部 ==============
echo "=== mcpowers 安装 ==="
echo "源:   $REPO_DIR"
echo "目标: $SKILLS_DIR"
echo "模式: $MODE"
echo

# ============== 通用安装函数 ==============
# 把 src 安装到 dst，已存在则替换
install_item() {
    local src="$1"
    local dst="$2"
    local name="$3"

    # 已存在且已正确链接 → 跳过
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        echo "  ✓ $name (已链接)"
        return 0
    fi

    # 已存在但不是正确链接 → 删除后重建
    if [ -e "$dst" ] || [ -L "$dst" ]; then
        echo "  ⚠ $name 已存在，替换中..."
        rm -rf "$dst"
    fi

    if [ "$MODE" = "symlink" ]; then
        # 平台适配：
        #   - macOS/Linux: ln -s 创建真正的 symlink
        #   - Windows (Git Bash): ln -s 在没有 Developer Mode 时会静默退化为复制，
        #     用 cmd //c mklink /J (junction) 作为 fallback，无需管理员
        if is_windows; then
            # 转换为 Windows 路径
            local win_src win_dst
            win_src=$(cygpath -w "$src" 2>/dev/null || echo "$src")
            win_dst=$(cygpath -w "$dst" 2>/dev/null || echo "$dst")
            # Git Bash 把 cmd 命令里的反斜杠吞掉，所以写到临时 .cmd 文件再执行
            local tmp_cmd
            tmp_cmd=$(mktemp --suffix=.cmd 2>/dev/null || mktemp)
            printf '@echo off\r\nmklink /J "%s" "%s"\r\n' "$win_dst" "$win_src" > "$tmp_cmd"
            local tmp_win
            tmp_win=$(cygpath -w "$tmp_cmd" 2>/dev/null || echo "$tmp_cmd")
            if cmd //c "$(cygpath -w "$tmp_cmd")" >/dev/null 2>&1; then
                echo "  ✓ $name (junction)"
            else
                echo "  ✗ $name 创建 junction 失败，试试 --copy 模式"
                rm -f "$tmp_cmd"
                return 1
            fi
            rm -f "$tmp_cmd"
        else
            if ln -s "$src" "$dst" 2>/dev/null; then
                echo "  ✓ $name → $src"
            else
                echo "  ✗ $name 创建 symlink 失败"
                return 1
            fi
        fi
    else
        cp -r "$src" "$dst"
        echo "  ✓ $name (copied)"
    fi
}

# 平台检测
is_windows() {
    case "$(uname -s 2>/dev/null)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
        *) return 1 ;;
    esac
}

# ============== 1. 主入口 ==============
echo "[1/3] 安装主入口 mcpowers/"
install_item "$REPO_DIR/mcpowers" "$SKILLS_DIR/mcpowers" "mcpowers"

# ============== 2. 18 个技能（扁平化） ==============
echo "[2/3] 安装技能（scene + method，共 18 个）"
for skill_dir in "$REPO_DIR/skills/scene"/* "$REPO_DIR/skills/method"/*; do
    [ -d "$skill_dir" ] || continue
    name=$(basename "$skill_dir")
    install_item "$skill_dir" "$SKILLS_DIR/$name" "$name"
done

# ============== 3. 规范库 ==============
echo "[3/3] 安装规范库 mcpowers-shared/"
install_item "$REPO_DIR/mcpowers-shared" "$SKILLS_DIR/mcpowers-shared" "mcpowers-shared"

# ============== 收尾 ==============
echo
echo "=== 安装完成 ==="
SKILL_COUNT=$(ls -1 "$SKILLS_DIR" 2>/dev/null | grep -c '^mcpowers' || true)
echo "  技能数: $SKILL_COUNT（含 1 个路由器 + 18 个技能 + 1 个规范库）"
echo
if [ "$MODE" = "symlink" ]; then
    echo "✓ symlink 模式已启用："
    echo "  - 编辑源文件后无需重装，重启 Claude Code 即可生效"
    echo "  - 升级: cd $REPO_DIR && git pull"
else
    echo "✓ copy 模式已启用："
    echo "  - 编辑源文件后需重新运行 install.sh 才生效"
    echo "  - 升级: cd $REPO_DIR && git pull && bash install.sh --copy"
fi
echo
echo "请重启 Claude Code 使技能生效。"
echo "验证: 在任意项目说\"加个功能\"，看 AI 是否自动调 mcpowers-feat"
