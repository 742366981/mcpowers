---
name: mcpowers
description: mcpowers 技能体系总入口。每次对话自动注入，识别用户意图后路由到对应的场景/方法技能，避免加载过重的工作流。覆盖产品→开发→测试→部署全生命周期。
---

# mcpowers 路由器

> **核心思想**：单次对话只加载当前场景需要的技能，不预加载全部规范。
> 借鉴 superpowers 的 `using-superpowers` bootstrap 模式。

---

> 铁律已由 SessionStart hook 自动注入，详见会话启动时的 `[mcpowers] 铁律` 段。
> 完整规范见 `mcpowers-shared/docs/AI操作规范.md`（按需 Read）。

---

## 1. 场景路由表

根据用户意图关键词，路由到对应技能：

| 用户意图（关键词） | 路由到 | 技能类型 |
|:-------------------|:-------|:---------|
| 加/新增/做一个 功能、页面、接口、模块 | `mcpowers-feat` | 场景层 |
| bug/报错/不生效/异常/失败/修一下 | `mcpowers-bugfix` | 场景层 |
| 重构/抽离/拆分/太乱/抽象 | `mcpowers-refactor` | 场景层 |
| 慢/卡/性能/优化/查询慢 | `mcpowers-optimize` | 场景层 |
| 部署/上线/发布/构建 | `mcpowers-deploy` | 场景层 |
| 需求改了/调整逻辑/加字段/改流程 | `mcpowers-requirement-change` | 场景层 |
| 初始化/新项目/脚手架/搭建 | `mcpowers-init` | 场景层 |
| 写需求/写 PRD/整理需求 | `mcpowers-prd` | 方法层 |
| 任务拆解/列计划/排期 | `mcpowers-plan` | 方法层 |
| 按计划执行/实施计划/开始执行 | `mcpowers-execute` | 方法层 |
| 审查/审一下/review/自审 | `mcpowers-code-review` | 方法层 |
| 写测试/TDD/单测 | `mcpowers-tdd` | 方法层 |
| 不清楚要做什么/需求不清 | `mcpowers-brainstorm` | 方法层 |
| 复杂任务/并行/多代理 | `mcpowers-subagent` | 方法层 |
| commit/提交 | `mcpowers-git-commit` | 场景层（Git） |
| worktree/分支隔离/并行工作区 | `mcpowers-git-worktree` | 场景层（Git） |
| 回滚/rollback/撤销/恢复 | `mcpowers-git-rollback` | 场景层（Git） |
| 清理分支/删除分支/整理分支 | `mcpowers-git-cleanBranches` | 场景层（Git） |

---

## 2. 路由执行规则

### 2.1 触发顺序
1. **先识别意图** → 查路由表
2. **命中场景层** → 调对应场景技能（场景技能内部会按需调方法层技能）
3. **未命中** → 进入兜底流程

### 2.2 兜底流程（无明确意图时）
1. 提示可用技能清单（场景层 + 方法层）
2. 默认走 `mcpowers-brainstorm` 澄清需求
3. 澄清后再路由到对应场景

### 2.3 多意图时
- 拆分为多个任务，依次执行
- 第一个任务优先（用户后续可追加）

### 2.4 多意图裁决规则

当用户输入命中多个场景层技能时，按以下顺序裁决：

**优先级矩阵**（数字越小越优先）：

| 优先级 | 类别 | 说明 |
|:-------|:-----|:-----|
| 1 | 危险修复类 | `mcpowers-git-rollback`（回滚）压倒一切 |
| 2 | 元操作类 | `mcpowers-git-*` 4 个（commit/worktree/cleanBranches/rollback） |
| 3 | 修 bug 类 | `mcpowers-bugfix` 优先于 `mcpowers-feat` |
| 4 | 新增类 | `mcpowers-feat` > `mcpowers-refactor` > `mcpowers-optimize` |
| 5 | 部署 / 需求变更 | `mcpowers-deploy`、`mcpowers-requirement-change` |
| 6 | 初始化 | `mcpowers-init`（只在空仓库或新会话触发） |
| 7 | 方法层 | 由场景层按需编排，单独触发需用户明确指令 |

**冲突矩阵**（典型组合的裁决）：

| 用户输入 | 命中技能 | 裁决 |
|:---------|:---------|:-----|
| "修了 bug 后 commit" | bugfix + git-commit | 先 bugfix（Step 1-4），再 git-commit |
| "重构代码并加测试" | refactor + tdd | tdd 先补测试（铁律），再 refactor |
| "优化数据库查询并部署" | optimize + deploy | optimize 先，deploy 在用户确认后 |
| "初始化项目并 commit" | init + git-commit | init 完成，git-commit 收尾 |
| "改个字段后 commit" | requirement-change + git-commit | requirement-change 先，commit 收尾 |
| "部署出问题回滚" | deploy + rollback | rollback 优先（紧急修复类） |

**灰色地带处理**：
- 用户说"加个功能顺便 commit" → 视为单一任务，`mcpowers-feat` 在 Step 8 自动调 `mcpowers-git-commit`，不拆
- 用户说"我也不知道要做什么" → 直接进 `mcpowers-brainstorm`，不查路由表
- 命中 ≥ 3 个意图 → 中断并调 AskUserQuestion，让用户选择先做哪个
- 关键词同时命中"重构"和"加功能" → 默认 `mcpowers-refactor`（行为不变优先），如行为变化则切 `mcpowers-feat`

---

## 3. 技能清单（按需 Read）

### 3.1 场景层（Layer 1）—— 用户输入直接命中
- `skills/scene/mcpowers-feat/SKILL.md`
- `skills/scene/mcpowers-bugfix/SKILL.md`
- `skills/scene/mcpowers-refactor/SKILL.md`
- `skills/scene/mcpowers-optimize/SKILL.md`
- `skills/scene/mcpowers-deploy/SKILL.md`
- `skills/scene/mcpowers-requirement-change/SKILL.md`
- `skills/scene/mcpowers-init/SKILL.md`
- `skills/scene/mcpowers-git-commit/SKILL.md`
- `skills/scene/mcpowers-git-worktree/SKILL.md`
- `skills/scene/mcpowers-git-rollback/SKILL.md`
- `skills/scene/mcpowers-git-cleanBranches/SKILL.md`

### 3.2 方法层（Layer 2）—— 被编排，也可单独触发
- `skills/method/mcpowers-brainstorm/SKILL.md`
- `skills/method/mcpowers-prd/SKILL.md`
- `skills/method/mcpowers-plan/SKILL.md`
- `skills/method/mcpowers-execute/SKILL.md`
- `skills/method/mcpowers-tdd/SKILL.md`
- `skills/method/mcpowers-code-review/SKILL.md`
- `skills/method/mcpowers-subagent/SKILL.md`

### 3.3 规范层（Layer 3）—— 资产库，按需 Read
- **导航**：`mcpowers-shared/mcpowers-spec-index/SKILL.md`（查"做什么 → 读哪个规范"）
- **规范文件**：`mcpowers-shared/docs/技术规范/*.md`（13+ 个文件，原地保留）

---

## 4. 独立运行

mcpowers 体系**完全独立**，不依赖任何外部技能：

- ✅ **Git 操作**：由 `mcpowers-git-*` 4 个自有技能处理（commit / worktree / rollback / cleanBranches）
- ✅ **规范文件**：`mcpowers-shared/docs/...` 路径不变
- ✅ **旧 `mcpowers-workflow` 已删除**：原 2142 行单体已拆解为路由器 + 16 个场景/方法技能

只需安装 `mcpowers/` + `skills/` + `mcpowers-shared/` 三个目录即可完整使用。

---

**使用方式**：本路由器会在每次对话自动加载。AI 收到用户输入后，先查路由表命中场景技能，再由场景技能按需 Read 规范文件。不要一开始就 Read 所有规范（会爆上下文）。

---

## 5. 硬约束完整覆盖（4 个 hooks）

铁律从"软提示"升级为"硬约束"由以下 hooks 实现（详见 `hooks/README.md`）：

| 钩子 | 时机 | 对应铁律 | 退出码 |
|:-----|:-----|:---------|:-------|
| `SessionStart/startup` | 启动时 | 7 条必做 + 6 条禁止（铁律全文注入） | 0（注入） |
| `PreToolUse/Bash` | Bash 前 | 阻断 `rm -rf /` 等危险命令 | 2 = 阻断 / 0 = 放行 |
| `PreToolUse/Write` | Write 前 | 改前确认（仅保护核心 3 目录） | 2 = 阻断 / 0 = 放行 |
| `PostToolUse/Write\|Edit\|MultiEdit` | 写完后 | 改完即 commit 提醒 | 0（仅提醒） |

**核心 3 目录保护**（PreToolUse/Write 范围）：`mcpowers-shared/`、`mcpowers/`、`hooks/`——修改这些目录的 Write 调用会被阻断，触发 Claude Code CLI 的 confirm UI。

**安全逃生**：安装时用 `bash install.sh --no-hooks` 跳过 hooks 注册。

---

## 6. mcpowers 自身维护（开发者模式）

> ⚠️ **当用户要修改 mcpowers 自身（不是用 mcpowers 改用户项目）时，本路由器识别"维护意图"并路由到对应流程。**

### 6.1 维护意图识别

用户说以下关键词时，进入"维护模式"——不调外部技能，直接读 `README.md` 的"## 维护指南"段执行：

| 维护意图（关键词） | 路由到 | 详见 README 场景 |
|:-------------------|:-------|:-----------------|
| 加/新增/写 规范、规范文件、spec | 维护模式场景 2 | 新增规范文件 |
| 删/移除 规范、规范文件 | 维护模式场景 3 | 删除规范文件 |
| 改/更新/补充 规范内容 | 维护模式场景 1 | 修改规范文件 |
| 加/新增/写 技能、场景 | 维护模式场景 4 | 新增场景技能 |
| 加/新增/写 hook、钩子 | 维护模式场景 5 | 新增 hook |
| 升级/git pull/更新版本 | 维护模式场景 6 | 升级流程 |
| 改铁律/改措辞/改禁止 | 维护模式场景 7 | 铁律双源同步 |
| 跑测试/校验/检查 | 直接执行 `bash tests/install-smoke.sh && bash scripts/check-readme-sync.sh` | 自动化保障清单 |

### 6.2 维护模式默认流程

每次进入维护模式：

1. **先 Read** `README.md` 的"## 维护指南"段（已包含 7 个场景的完整步骤）
2. **按场景的 5 步操作**逐步执行
3. **改完必跑** `bash tests/install-smoke.sh && bash scripts/check-readme-sync.sh`
4. **commit** 前再看一眼本节 6.3 的铁律

### 6.3 维护铁律

- ❌ **不**直接修改 `~/.claude/skills/` 下的 symlink 内容（symlink 模式下改了无效）
- ❌ **不**跳过"自动化保障清单"里的 2 个脚本（commit 前必跑）
- ❌ **不**漏改 spec-index 查表（新增/删除规范时必查 `mcpowers-shared/mcpowers-spec-index/SKILL.md`）
- ✅ **必**同步更新 frontmatter 的 `last_updated` 字段
- ✅ **必**保持铁律双源一致（先改 `mcpowers-shared/docs/AI操作规范.md` 再改 `hooks/session-start.sh`）
- ✅ **必**改完即 commit（沿用项目铁律第 3 条）
