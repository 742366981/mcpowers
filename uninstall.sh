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

# ============== 清理 ~/.claude/settings.json 中的 mcpowers hooks ==============
# 逻辑：
#   - settings.json 不存在 → 无需清理
#   - 顶层 _mcpowers_marker: true → mcpowers 是唯一 hooks 来源 → 删除整个 hooks 段
#   - 顶层 _mcpowers_marker 不存在但 hooks 段存在 → 只清理 mcpowers 自己的子项
#   - 失败时回滚备份
cleanup_hooks() {
    local settings="$HOME/.claude/settings.json"

    if [ ! -f "$settings" ]; then
        echo "  ⊘ ~/.claude/settings.json 不存在，跳过"
        return 0
    fi

    # 1. 备份
    local backup="$settings.bak.mcpowers.uninstall.$$"
    if ! cp "$settings" "$backup" 2>/dev/null; then
        echo "  ✗ 备份 settings.json 失败，跳过清理"
        return 1
    fi

    # 2. 合并式清理（优先 python3 → python → node → 纯 bash）
    # 优先 python3，回退 python（Windows 默认安装为 python 而非 python3）
    local py_bin=""
    if command -v python3 >/dev/null 2>&1; then
        py_bin="python3"
    elif command -v python >/dev/null 2>&1; then
        py_bin="python"
    fi
    local ok=false

    if [ -n "$py_bin" ]; then
        if $py_bin -c "
import json, sys
try:
    with open(r'$settings', 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        print('settings.json 不是对象格式，跳过')
        sys.exit(0)
    is_owner = data.get('_mcpowers_marker') is True
    if is_owner:
        # mcpowers 是唯一来源 → 删除整个 hooks 段和 marker
        data.pop('hooks', None)
        data.pop('_mcpowers_marker', None)
    elif 'hooks' in data:
        # 存在其他 hooks → 只清理 mcpowers 标记的子项
        # mcpowers 标记法：检查 command 字符串中是否含 'mcpowers'
        if isinstance(data['hooks'], dict):
            for event_name in list(data['hooks'].keys()):
                groups = data['hooks'][event_name]
                if not isinstance(groups, list):
                    continue
                filtered = []
                for g in groups:
                    if not isinstance(g, dict):
                        filtered.append(g); continue
                    hks = g.get('hooks', [])
                    if not isinstance(hks, list):
                        filtered.append(g); continue
                    new_hks = [h for h in hks
                              if not (
                                  isinstance(h, dict) and
                                  isinstance(h.get('command'), str) and
                                  'mcpowers' in h['command']
                              )]
                    if new_hks:
                        g['hooks'] = new_hks
                        filtered.append(g)
                if filtered:
                    data['hooks'][event_name] = filtered
                else:
                    del data['hooks'][event_name]
            if not data['hooks']:
                data.pop('hooks')
    with open(r'$settings', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
except Exception as e:
    print('err: ' + str(e), file=sys.stderr)
    sys.exit(1)
" >/dev/null 2>&1; then
            ok=true
        fi
    elif command -v node >/dev/null 2>&1; then
        if node -e "
const fs = require('fs');
try {
  const data = JSON.parse(fs.readFileSync('$settings', 'utf8'));
  const isOwner = data._mcpowers_marker === true;
  if (isOwner) {
    delete data.hooks;
    delete data._mcpowers_marker;
  } else if (data.hooks) {
    for (const eventName of Object.keys(data.hooks)) {
      const groups = data.hooks[eventName];
      if (!Array.isArray(groups)) continue;
      const filtered = groups.map(g => {
        if (!g || !Array.isArray(g.hooks)) return g;
        g.hooks = g.hooks.filter(h =>
          !(h && typeof h.command === 'string' && h.command.includes('mcpowers'))
        );
        return g;
      }).filter(g => g && Array.isArray(g.hooks) && g.hooks.length > 0);
      if (filtered.length > 0) {
        data.hooks[eventName] = filtered;
      } else {
        delete data.hooks[eventName];
      }
    }
    if (Object.keys(data.hooks).length === 0) {
      delete data.hooks;
    }
  }
  fs.writeFileSync('$settings', JSON.stringify(data, null, 2));
} catch (e) {
  console.error('err: ' + e.message);
  process.exit(1);
}
" >/dev/null 2>&1; then
            ok=true
        fi
    else
        # 纯 bash 兜底：仅当存在 _mcpowers_marker 时整段删除 hooks
        if grep -q '"_mcpowers_marker"[[:space:]]*:[[:space:]]*true' "$settings" 2>/dev/null; then
            if grep -q '"hooks"' "$settings" 2>/dev/null; then
                # 找到 "hooks": { ... } 段并删除（用 sed 多行删除比较复杂，这里用 Python 都行不通就警告用户）
                echo "  ⚠ 纯 bash 兜底无法精确删除非 owner 的 hooks 段，请安装 python3 后重试"
                rm -f "$backup"
                return 1
            else
                ok=true
            fi
        else
            ok=true  # 不是 owner 且无 mcpowers 标记命令，无需处理
        fi
    fi

    # 3. 结果
    if [ "$ok" = true ]; then
        echo "  ✓ hooks 已从 settings.json 清理"
        rm -f "$backup"
    else
        echo "  ✗ 清理失败，从备份回滚"
        cp "$backup" "$settings"
        rm -f "$backup"
        return 1
    fi
}

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

# ============== 清理 ~/.claude/settings.json 中的 mcpowers hooks ==============
echo "=== 清理 Claude Code Hooks ==="
cleanup_hooks
echo
echo "如需重装: bash install.sh"
