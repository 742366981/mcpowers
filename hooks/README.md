# mcpowers Hooks

mcpowers 通过 Claude Code 的 hooks 机制实现**铁律的硬约束**——LLM 必须遵守的规则从"软提示"升级为"物理阻断"。

## 包含的钩子

| 钩子 | 触发时机 | 作用 |
|:-----|:---------|:-----|
| `SessionStart` | 每次 Claude Code 启动 | 注入路由器铁律摘要，AI 每轮对话开始就知道 mcpowers 流程 |
| `PreToolUse (Bash)` | 每次执行 Bash 命令前 | 阻断 `rm -rf /`、`git push --force main` 等危险操作 |

## 安装位置

```
~/.claude/skills/mcpowers/hooks/    # symlink 到本仓库的 hooks/ 目录
├── hooks.json                       # Claude Code hooks 配置
├── session-start.sh                 # 启动注入逻辑
└── pre-bash-guard.sh                # 危险命令阻断逻辑
```

`install.sh` / `install.ps1` 会把本目录 symlink 到 `~/.claude/skills/mcpowers/hooks/`，**编辑源文件后无需重装**，重启 Claude Code 即生效（与 mcpowers 现有 symlink 模式一致）。

## 跨平台说明

`hooks.json` 中配置的命令是 `bash "..."` 形式，**依赖 Git Bash**：

- ✅ macOS / Linux：原生 bash
- ✅ Windows + Git Bash：Claude Code 默认配套 Git Bash

如果你的 Windows 环境**没有 Git Bash**，hooks 会失败——请改用 WSL 或安装 Git for Windows。

## 跳过 hooks 安装

不需要 hooks 的用户可以：

```bash
bash install.sh --no-hooks       # macOS / Linux / Git Bash
.\install.ps1 -NoHooks           # Windows PowerShell
```

跳过安装后，`~/.claude/settings.json` 不会被修改；卸载时也不会清理（因为没有 mcpowers 标记）。

## 卸载

`uninstall.sh` / `uninstall.ps1` 会**精确清理** mcpowers 注册的 hooks 段，**不会影响**其他来源的 hooks：

- 检测 `~/.claude/settings.json` 顶层是否有 `_mcpowers_marker: true`
- 有 → mcpowers 是唯一 hooks 来源 → 删除整个 `hooks` 段
- 无 → 存在其他 hooks → 只删除 mcpowers 标记的子项

清理前会备份原文件为 `settings.json.bak.mcpowers`，失败自动回滚。

## 故障排查

### 钩子没生效

1. 确认 `~/.claude/settings.json` 含 `_mcpowers_marker: true` 和 `hooks` 段
2. 确认 symlink 存在：`ls -la ~/.claude/skills/mcpowers/hooks/`
3. 重启 Claude Code 会话

### 误伤正常命令

`pre-bash-guard.sh` 内置白名单覆盖 `node_modules/`、`dist/`、`build/`、`tmp/` 等常见 `rm -rf` 场景。如果被误伤：

1. 查看 stderr 输出的具体阻断原因
2. 编辑 `hooks/pre-bash-guard.sh` 的白名单段
3. 重启 Claude Code 生效

### 卸载后 hooks 仍在

说明 `_mcpowers_marker` 检测失败。手动清理：

```bash
# 查看当前 settings.json
cat ~/.claude/settings.json

# 备份
cp ~/.claude/settings.json ~/.claude/settings.json.bak

# 用编辑器打开，删除 mcpowers 注册的 hooks 段
# 或重装 mcpowers 后再卸载
bash install.sh && bash uninstall.sh --yes
```

## 设计原则

- **保守阻断**：宁可少拦、不可误伤；白名单优先于黑名单
- **退出码 2 = 拒绝**：遵循 Claude Code PreToolUse 协议
- **std 输出 = 信息**：SessionStart hook 仅注入信息，不阻断
- **幂等安装**：重复 `install.sh` 结果一致，hooks 段会被完全覆盖为当前仓库版本
