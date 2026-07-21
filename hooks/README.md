# mcpowers Hooks

mcpowers 通过 Claude Code 的 hooks 机制实现**铁律的硬约束**——LLM 必须遵守的规则从"软提示"升级为"物理阻断"。

## 包含的钩子（4 个事件组 / 5 个脚本）

| 钩子 | 触发时机 | 作用 |
|:-----|:---------|:-----|
| `SessionStart` | 每次 Claude Code 启动 | 注入路由器铁律摘要，AI 每轮对话开始就知道 mcpowers 流程 |
| `PreToolUse (Bash)` | 每次执行 Bash 命令前 | 阻断 `rm -rf /`、`git push --force main` 等危险操作 |
| `PreToolUse (Write)` | 每次 Write 文件前 | 保护核心资产（`skills/mcpowers/`、`skills/mcpowers-shared/`、`hooks/`、`.claude-plugin/`），需用户确认；接口变更时额外提示同步 API 文档 |
| `PostToolUse (Write/Edit/MultiEdit)` | 每次修改后 | 改完即 commit 提醒（仅在已暂存且工作区干净时触发） |

## 注册机制（v2.0 插件市场）

v2.0 起，hooks 由 Claude Code 插件系统自动注册——**无需修改 `settings.json`**。

- `hooks/hooks.json` 通过 `${CLAUDE_PLUGIN_ROOT}` 环境变量定位脚本
- 插件系统会注入此环境变量，跨平台零适配
- 卸载时由 `/plugin uninstall` 自动清理，零残留

**安装方式**：

```bash
/plugin marketplace add https://github.com/742366981/mcpowers
/plugin install mcpowers@mcpowers
```

## 跨平台说明

`hooks.json` 中配置的命令是 `bash "..."` 形式，**依赖 Git Bash**：

- ✅ macOS / Linux：原生 bash
- ✅ Windows + Git Bash：Claude Code 默认配套 Git Bash

如果你的 Windows 环境**没有 Git Bash**，hooks 会失败——请改用 WSL 或安装 Git for Windows。

## 故障排查

### 钩子没生效

1. 确认插件已安装：`/plugin list` 看到 `mcpowers@mcpowers`
2. 确认脚本可执行：`ls -la ${CLAUDE_PLUGIN_ROOT}/hooks/*.sh`
3. 完全退出 Claude Code 会话（按 Ctrl+C 或 `/exit`）后重新启动

### 误伤正常命令

`pre-bash-guard.sh` 内置白名单覆盖 `node_modules/`、`dist/`、`build/`、`tmp/` 等常见 `rm -rf` 场景。如果被误伤：

1. 查看 stderr 输出的具体阻断原因
2. 编辑 `hooks/pre-bash-guard.sh` 的白名单段
3. 重启 Claude Code 生效

### 误伤正常文件写入

`pre-write-confirm.sh` 保护核心资产目录。如果被误伤：

1. 编辑 `hooks/pre-write-confirm.sh` 的 `PROTECTED_PREFIXES` 数组
2. 重启 Claude Code 生效

### 卸载后 hooks 仍在

`/plugin uninstall mcpowers@mcpowers` 应自动清理。如有残留：

```bash
# 手动检查 settings.json
cat ~/.claude/settings.json | grep -A 5 hooks
# 删除含 "mcpowers" 或 "$CLAUDE_PLUGIN_ROOT" 的 hooks 条目
```

## 设计原则

- **保守阻断**：宁可少拦、不可误伤；白名单优先于黑名单
- **退出码 2 = 拒绝**：遵循 Claude Code PreToolUse 协议
- **std 输出 = 信息**：SessionStart hook 仅注入信息，不阻断
- **零手动配置**：依赖 `${CLAUDE_PLUGIN_ROOT}` 插件系统注入，跨平台统一
