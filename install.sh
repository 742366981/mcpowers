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
#   bash install.sh                # 默认 symlink 模式（含 hooks 注册）
#   bash install.sh --copy         # 复制模式（无 symlink 权限时使用）
#   bash install.sh --no-hooks     # 跳过 hooks 注册（仅安装 skills）
#   bash install.sh --copy --no-hooks  # 组合使用
#
# 仓库地址：git@github.com:742366981/mcpowers.git

set -e

# ============== 解析参数 ==============
MODE="symlink"
INSTALL_HOOKS=true
for arg in "$@"; do
    case "$arg" in
        --copy) MODE="copy" ;;
        --no-hooks) INSTALL_HOOKS=false ;;
    esac
done

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

# ============== 注册 hooks 到 ~/.claude/settings.json ==============
# 策略：合并式写入 — 保留用户的 permissions / mcpServers 等其他段
# 工具降级：python3 → node → jq → 纯 bash 字符串操作
# 失败回滚：先备份再修改
register_hooks() {
    local settings="$HOME/.claude/settings.json"
    local hooks_file="$REPO_DIR/hooks/hooks.json"
    local hooks_install_dir="$SKILLS_DIR/mcpowers/hooks"  # symlink 后的路径

    if [ ! -f "$hooks_file" ]; then
        echo "  ✗ hooks 配置不存在: $hooks_file"
        return 1
    fi

    # 关键：Windows 下 Python 是 Windows 原生进程，认不到 Git Bash 的 /c/Users/...
    # 必须把路径转成 Windows 形式 (C:\Users\...) 才能被 Python 看到
    local settings_py settings_w
    if is_windows; then
        settings_w=$(cygpath -w "$settings" 2>/dev/null || echo "$settings")
    else
        settings_w="$settings"
    fi
    settings_py="$settings_w"

    # 1. 备份已有 settings.json
    local backup=""
    if [ -f "$settings" ]; then
        backup="$settings.bak.mcpowers.$$"
        if ! cp "$settings" "$backup" 2>/dev/null; then
            echo "  ⚠ 备份 settings.json 失败，继续（不阻塞）"
            backup=""
        fi
    fi

    # 2. 渲染 hooks.json（替换 __HOOKS_DIR__ 占位符）
    # 关键：Windows 下 Python 看不到 Git Bash 的 /tmp 路径，必须用 cygpath -w 转换
    local rendered_hooks rendered_hooks_py
    rendered_hooks=$(mktemp)
    if is_windows; then
        # 把 /tmp/xxx 转成 C:\Users\...\Temp\xxx 供 Python 使用
        rendered_hooks_py=$(cygpath -w "$rendered_hooks" 2>/dev/null || echo "$rendered_hooks")
    else
        rendered_hooks_py="$rendered_hooks"
    fi
    if ! sed "s|__HOOKS_DIR__|$hooks_install_dir|g" "$hooks_file" > "$rendered_hooks" 2>/dev/null; then
        echo "  ✗ 渲染 hooks.json 失败"
        [ -n "$backup" ] && cp "$backup" "$settings" && rm -f "$backup"
        rm -f "$rendered_hooks"
        return 1
    fi

    # 3. 合并写入 settings.json
    local merge_ok=false
    mkdir -p "$(dirname "$settings")"

    if [ ! -f "$settings" ]; then
        # settings.json 不存在 → 直接复制
        if cp "$rendered_hooks" "$settings"; then
            merge_ok=true
        fi
    else
        # settings.json 已存在 → 合并（只覆盖 hooks 段）
        # 优先 python3，回退 python（Windows 默认安装为 python 而非 python3）
        local py_bin=""
        if command -v python3 >/dev/null 2>&1; then
            py_bin="python3"
        elif command -v python >/dev/null 2>&1; then
            py_bin="python"
        fi

        if [ -n "$py_bin" ]; then
            if $py_bin -c "
import json, sys
try:
    with open(r'$settings_py', 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(r'$rendered_hooks_py', 'r', encoding='utf-8') as f:
        hooks = json.load(f)
    data['hooks'] = hooks['hooks']
    data['_mcpowers_marker'] = hooks.get('_mcpowers_marker', True)
    with open(r'$settings_py', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('ok')
except Exception as e:
    print('err: ' + str(e), file=sys.stderr)
    sys.exit(1)
" >/dev/null 2>&1; then
                merge_ok=true
            fi
        elif command -v node >/dev/null 2>&1; then
            if node -e "
const fs = require('fs');
try {
  const data = JSON.parse(fs.readFileSync('$settings_py', 'utf8'));
  const hooks = JSON.parse(fs.readFileSync('$rendered_hooks_py', 'utf8'));
  data.hooks = hooks.hooks;
  data._mcpowers_marker = hooks._mcpowers_marker || true;
  fs.writeFileSync('$settings_py', JSON.stringify(data, null, 2));
  console.log('ok');
} catch (e) {
  console.error('err: ' + e.message);
  process.exit(1);
}
" >/dev/null 2>&1; then
                merge_ok=true
            fi
        elif command -v jq >/dev/null 2>&1; then
            # jq 路径：用临时文件 + jq -s 合并
            if jq -s '.[0] * {hooks: .[1].hooks, _mcpowers_marker: .[1]._mcpowers_marker}' \
                "$settings" "$rendered_hooks" > "$settings.tmp" 2>/dev/null; then
                mv "$settings.tmp" "$settings"
                merge_ok=true
            fi
        else
            # 兜底：纯 bash — 仅在 settings.json 无 hooks 段时追加
            if ! grep -q '"hooks"' "$settings" 2>/dev/null; then
                # 在文件末尾追加 hooks 段
                local hooks_payload
                hooks_payload=$(grep -A 1000 '"hooks"' "$rendered_hooks" | head -n -1)
                if echo "," >> "$settings" && echo "$hooks_payload" >> "$settings"; then
                    merge_ok=true
                fi
            else
                echo "  ⚠ 已有 hooks 段但无 python3/node/jq，跳过合并（请手动处理）"
            fi
        fi
    fi

    # 4. 结果处理
    rm -f "$rendered_hooks"
    if [ "$merge_ok" = true ]; then
        echo "  ✓ hooks 已注册到 $settings"
        [ -n "$backup" ] && rm -f "$backup"
    else
        echo "  ✗ hooks 合并失败"
        if [ -n "$backup" ] && [ -f "$backup" ]; then
            cp "$backup" "$settings"
            echo "  ↻ 已从备份回滚"
            rm -f "$backup"
        fi
        return 1
    fi
}

# ============== 1. 主入口 + hooks 资产 ==============
echo "[1/4] 安装主入口 mcpowers/"
install_item "$REPO_DIR/mcpowers" "$SKILLS_DIR/mcpowers" "mcpowers"

# hooks 资产在仓库根 hooks/ 目录，但 settings.json 指向 ~/.claude/skills/mcpowers/hooks/
# 在这里 symlink 一下，让两边对齐
if [ -d "$REPO_DIR/hooks" ]; then
    install_item "$REPO_DIR/hooks" "$SKILLS_DIR/mcpowers/hooks" "mcpowers/hooks (hooks assets)"
fi

# ============== 2. 18 个技能（扁平化） ==============
echo "[2/4] 安装技能（scene + method，共 18 个）"
for skill_dir in "$REPO_DIR/skills/scene"/* "$REPO_DIR/skills/method"/*; do
    [ -d "$skill_dir" ] || continue
    name=$(basename "$skill_dir")
    install_item "$skill_dir" "$SKILLS_DIR/$name" "$name"
done

# ============== 3. 规范库 ==============
echo "[3/4] 安装规范库 mcpowers-shared/"
install_item "$REPO_DIR/mcpowers-shared" "$SKILLS_DIR/mcpowers-shared" "mcpowers-shared"

# ============== 4. 注册 Claude Code Hooks ==============
if [ "$INSTALL_HOOKS" = true ]; then
    echo "[4/4] 注册 Claude Code Hooks 到 ~/.claude/settings.json"
    register_hooks
else
    echo "[4/4] 跳过 hooks 注册（--no-hooks）"
fi

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
if [ "$INSTALL_HOOKS" = true ]; then
    echo "Hooks: SessionStart + PreToolUse(Bash) 已注册，重启后生效"
    echo "  跳过: bash install.sh --no-hooks"
fi
