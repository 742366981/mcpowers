---
name: mcpowers-install-basics-skills
description: "安装基础技能 / 一键装基础 / 装上所有基础 / 装基础技能 / 装全部基础技能 → 触发本技能。口语：给我装基础技能、帮我装上基础技能、帮我装基础环境、装备基础技能、把基础技能都装上、把所有基础技能都装上、配齐基础技能、安装基础工具、装上基础必备技能、装上全局基础技能、一键配基础技能、装上基础办公技能、装上基础文档技能、装上基础 UI 技能、给我把基础工具装好、把基础环境装好。中英：install basics, install basic skills, setup base skills, basic dependencies, basic setup, npx skills add。边界：项目初始化/脚手架→mcpowers-init（项目级 vs 环境级）；维护 mcpowers 自身→README 维护指南；查/找技能→find-skills 本身。一键执行 4 条 npx skills add 全局安装 document-skills/ui-ux-pro-max/find-skills/skill-creator 等 4 类外部基础技能到 ~/.claude/skills/。"
---

# mcpowers-install-basics-skills（安装基础技能）

> **mcpowers 自身设计**，封装外部 `npx skills`（vercel-labs/skills）的 4 条安装命令。
> **目标**：用户在新环境首次使用 Claude Code 时，一句话装好 document / UI-UX / find / creator 4 类基础技能到全局。

---

## 编排

本技能按顺序执行以下步骤：

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | 环境检测（node + npx + 全局安装目录） | 内联 | 必走 | 任一缺失则中断并给出修复指引 |
| 2 | 现状检测（4 个技能是否已存在） | 内联 | 必走 | 已存在 → 询问"重装 / 跳过 / 更新" |
| 3 | 与用户确认清单 | 交互 | 必走 | 用户取消则退出 |
| 4 | 顺序执行 4 条 npx 命令 | Bash | 全部执行 | 单条失败 → 记录错误并继续余下 |
| 5 | 校验安装结果 | Bash | 必走 | 给出手动验证指引 |

**与 `mcpowers-init` 的区别**：

| 维度 | `mcpowers-init` | `mcpowers-install-basics-skills` |
|:-----|:----------------|:---------------------------------|
| 作用对象 | 工作目录（项目级） | `~/.claude/skills/`（环境级） |
| 装的是 | mcpowers 内部规范 | 外部 `npx skills`（vercel-labs/skills）生态技能 |
| 触发时机 | 每个新项目一次 | 首次使用 Claude Code 一次 |

**铁律**：禁止未确认就批量装；禁止跳过现状检测；禁止在断网状态下硬跑。

---

## 触发即执行

### 1. 环境检测

| 检测项 | 命令 | 通过标准 |
|:-------|:-----|:---------|
| Node.js | `node -v` | ≥ 16（npx 已默认带） |
| npx | `npx -v` | ≥ 7 |
| 全局安装目录 | `ls ~/.claude/skills/ 2>/dev/null \|\| mkdir -p ~/.claude/skills` | 存在或可创建 |

任一不通过 → **立刻停止**，给出对应安装指引（"请先安装 Node.js LTS" 等），不要硬装。

⚠️ **跨平台注意**：Windows 下 `~/.claude/skills/` 等价于 `%USERPROFILE%\.claude\skills\`（git bash 已自动展开，但提示用户时需给两条命令）。

### 2. 现状检测

对下列 4 类技能逐一检测：

- `document-skills`（仓库内含 `docx` / `pdf` / `pptx` / `xlsx` 等 4 个子技能）
- `ui-ux-pro-max`（`nextlevelbuilder/ui-ux-pro-max-skill` 仓库的子技能）
- `find-skills`（`vercel-labs/skills` 仓库的子技能）
- `skill-creator`（`anthropics/skills` 仓库的子技能）

**判定结果**：

| 状态 | 动作 |
|:-----|:-----|
| 全部已存在 | 询问"是否要覆盖重装（y/n）" |
| 部分存在 | 列出已存在的项，询问"重装全部 / 重装未存在的 / 跳过已存在的" |
| 全部不存在 | 直接进入第 3 步 |

**检测方式**（按优先级，任一可用）：

1. `ls ~/.claude/skills/ | grep -E "^(document-skills|ui-ux-pro-max|find-skills|skill-creator)$"`
2. `npx skills ls 2>/dev/null`（若 vercel-labs/skills CLI 提供此命令）

### 3. 与用户确认

打印将执行的命令清单：

```bash
npx skills add appautomaton/document-skills -g
npx skills add https://github.com/nextlevelbuilder/ui-ux-pro-max-skill --skill ui-ux-pro-max -g
npx skills add https://github.com/vercel-labs/skills --skill find-skills -g
npx skills add https://github.com/anthropics/skills --skill skill-creator -g
```

使用 `AskUserQuestion` 让用户选择执行范围（4 条都装 / 只装缺失的 / 取消）。

⚠️ **来源权威**：仓库地址来自各项目官方 README，是唯一权威源，禁止修改或替换。

### 4. 顺序执行

逐条执行命令，**单条失败不中断**，记录结果到下表：

| # | 命令摘要 | 退出码 | stdout 关键信息 | stderr（如有） |
|:-:|:---------|:-------|:---------------|:--------------|
| 1 | `document-skills` |  |  |  |
| 2 | `ui-ux-pro-max` |  |  |  |
| 3 | `find-skills` |  |  |  |
| 4 | `skill-creator` |  |  |  |

⚠️ **`npx` 类工具可能无主交互**：若命令设计上需要交互（如选择版本），需加 `--yes` 或类似参数跳过人机对话，否则会卡死。如遇卡死，先 Ctrl+C 终止，然后单条重试。

### 5. 校验

```bash
# 列出全局已装技能
ls ~/.claude/skills/ 2>/dev/null
```

判定逻辑：

| 情况 | 行动 |
|:-----|:-----|
| 全部 4 类都在 | 输出"✅ 4 类基础技能安装完成，重启 Claude Code 后生效。" |
| 部分命中 | 列出未命中的，给出单独重试命令 |
| 全失败 | 检查 `ping github.com` + `npm config get registry`，提示用户先解决网络再重试 |

---

## 反模式（禁止）

- ❌ 不做现状检测直接装（可能覆盖用户自定义）
- ❌ 在用户未确认时强行执行（4 条命令全部联网下载，慢且不可逆）
- ❌ 忽略单条失败硬跑下一条后还报告"成功"（必须如实汇报）
- ❌ 修改任何 `npx skills add` 命令的源仓库（仓库是固定的权威来源）
- ❌ 把安装写到项目目录（必须全局安装到 `~/.claude/skills/`）
- ❌ 给用户"装好了"但未实际重启验证的命令列表（4 类技能的扫描是 `~/.claude/skills/`，不是 `node_modules/`）

---

## 边界（路由分流）

| 用户意图 | 路由到 |
|:---------|:-------|
| 装**项目级** mcpowers 规范 | `mcpowers-init`（语义不同：项目级 vs 环境级） |
| 找/搜索技能 | 用本技能装的 `find-skills` 直接调 |
| 创建新技能 | 用本技能装的 `skill-creator` 直接调 |
| 升级 mcpowers 自身 | README 维护指南场景 6 |

---

## 其他 AI 工具用户自助

本技能默认只装到 Claude Code 全局目录（`~/.claude/skills/`）。**任何兼容 Agent Skills 规范（SKILL.md 格式）的 AI 工具**用户，可通过 `npx skills add -a <agent>` 自助安装到对应工具目录。

### 已知支持的 agent（截至 v2.5.3）

| AI 工具 | `-a` 参数 | 安装目录 | SKILL.md 兼容 |
|:--------|:----------|:---------|:-------------|
| Claude Code | `claude-code` | `~/.claude/skills/`（本技能默认） | ✅ 已验证 |
| Cursor | `cursor` | `.cursor/skills/` | ✅ 已验证 |
| Cline | `cline` | 子目录扫描 | ✅ 已验证 |
| Roo Code | `roo` | 子目录扫描 | ✅ 已验证 |
| Trae / MarsCode | `trae` | `.trae/skills/` | ✅ 已验证 |
| OpenCode | `opencode` | `.opencode/skills/` | ⚠️ vercel-labs/skills 精选，但 SKILL.md 兼容未实测 |
| Codex CLI | `codex` | `.codex/skills/` | ⚠️ vercel-labs/skills 精选，但 SKILL.md 兼容未实测 |

> 完整 agent 列表（69+ 个，由 `vercel-labs/skills` 维护）见 [其 README 的 Supported Agents 段](https://github.com/vercel-labs/skills#supported-agents)。本表只列**已验证兼容 Agent Skills 规范（SKILL.md 格式）**或**官方精选**的 agent。

### 自助命令示例（Cursor 用户）

把 4 条 `npx skills add` 命令末尾加上 `-a <agent>`（`-g` 已加，与默认 Claude Code 命令一致）：

```bash
npx skills add appautomaton/document-skills -g -a cursor
npx skills add https://github.com/nextlevelbuilder/ui-ux-pro-max-skill --skill ui-ux-pro-max -g -a cursor
npx skills add https://github.com/vercel-labs/skills --skill find-skills -g -a cursor
npx skills add https://github.com/anthropics/skills --skill skill-creator -g -a cursor
```

### 不支持的工具

以下 AI 工具**不读 SKILL.md 格式**，本技能无法适配（请勿安装，会浪费磁盘）：

- Windsurf、JetBrains AI Assistant、GitHub Copilot、Cody、Zed —— 走自有 rules / instructions 机制，与 Agent Skills 规范不兼容
- Claude.ai 网页版 —— 部分支持，但需手动复制 `skills/*.md`（不是通过 `npx skills add` 装）

> **为什么不自动适配**：自动探测 + 多 `-a` 分发会装到用户不用的工具目录（YAGNI 反模式）。默认最小作用面 = 只管 Claude Code；其他工具用户在该工具的聊天框里跑本技能，或按上表自助。
