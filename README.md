# mcpowers

AI 辅助开发的标准化技能体系。**按场景拆分的轻量级技能组合**，覆盖产品 → 开发 → 测试 → 部署全生命周期。借鉴 superpowers 设计：主入口路由器 + 场景触发 + 规范按需加载。**完全独立运行**，不依赖任何外部技能（含 Git 操作）。

---

## 设计理念

mcpowers 的核心理念：**让 AI 像资深工程师一样按流程工作，而不是拿到需求就写代码**。

- **精准路由**：单入口路由器 + 场景/方法分层，按意图关键词精准分流
- **方法复用**：TDD / Review / Plan / Brainstorm 等方法层技能被场景层按需编排
- **按需加载**：通过 `mcpowers-spec-index` 查表按需 Read 规范文件，避免爆上下文
- **铁律双约束**：软约束靠技能描述（`铁律` 段落 + `## 反模式（禁止）` ❌ 清单），硬约束靠 Claude Code hooks 物理阻断
- **编排显式化**：11 个场景技能统一带 `## 编排` 段，写明调谁、何时调、失败时
- **规范元数据化**：18 个核心规范带 YAML frontmatter（title/type/applies_to/priority/version），机器可查
- **骨架增强**：路由器瘦身（105 行）、SessionStart 注入完整铁律、3 类 hooks（SessionStart + PreToolUse(Bash/Write) + PostToolUse）、冒烟测试 + 同步校验脚本

---

## 技能结构

```
mcpowers/
├── mcpowers/                          # 主入口路由器（< 150 行，每次对话注入）
│
├── hooks/                             # Claude Code hooks 资产（铁律硬约束）
│   ├── hooks.json                     # SessionStart + PreToolUse(Bash) 配置
│   ├── session-start.sh               # 启动时注入铁律摘要
│   └── pre-bash-guard.sh              # 阻断 rm -rf / 等危险命令
│
├── skills/
│   ├── scene/                         # 场景层（11 个，用户输入直接命中）
│   │   ├── mcpowers-feat/             # 加功能
│   │   ├── mcpowers-bugfix/           # 修 bug
│   │   ├── mcpowers-refactor/         # 重构
│   │   ├── mcpowers-optimize/         # 性能优化
│   │   ├── mcpowers-deploy/           # 部署
│   │   ├── mcpowers-requirement-change/  # 需求变更
│   │   ├── mcpowers-init/             # 项目初始化
│   │   ├── mcpowers-git-commit/       # 规范化 commit
│   │   ├── mcpowers-git-worktree/     # worktree 隔离
│   │   ├── mcpowers-git-rollback/     # 安全回滚
│   │   └── mcpowers-git-cleanBranches/  # 清理分支
│   │
│   └── method/                        # 方法层（7 个，被场景层调用）
│       ├── mcpowers-brainstorm/       # 澄清需求
│       ├── mcpowers-prd/              # 写 PRD
│       ├── mcpowers-plan/             # 任务拆解
│       ├── mcpowers-execute/          # 执行计划
│       ├── mcpowers-tdd/              # 强制 TDD
│       ├── mcpowers-code-review/      # 代码审查
│       └── mcpowers-subagent/         # 子代理并行
│
├── mcpowers-shared/                   # 规范资产库（保留不变）
│   ├── mcpowers-spec-index/           # 规范导航（< 100 行，查表）
│   └── docs/                          # 20+ 规范文件
│       ├── AI操作规范.md
│       ├── 产品设计/产品设计规范.md
│       └── 技术规范/
│           ├── API规范.md
│           ├── Flask后端规范.md
│           ├── Vue前端规范.md
│           ├── 爬虫规范.md
│           ├── 爬虫分析规范.md
│           ├── 代码规范.md
│           ├── 数据库规范.md
│           ├── 缓存规范.md
│           ├── 定时任务规范.md
│           ├── 导入导出规范.md
│           ├── Git规范.md
│           ├── 部署规范.md
│           ├── 测试规范.md
│           ├── 开发环境规范.md
│           ├── 设计规范.md
│           ├── 文档编写规范.md
│           ├── 代码同步修改规范.md
│           └── 细节记录规范.md
│
├── tests/                             # 冒烟测试（install-smoke.sh）
├── scripts/                           # 工具脚本（check-readme-sync.sh）
├── CLAUDE.md
├── README.md
└── .gitignore
```

---

## 触发条件

`mcpowers` 主入口路由器会在每次对话自动加载，识别意图后路由到对应技能：

| 用户输入 | 路由到 |
|:---------|:-------|
| 加/新增/做一个 功能、页面、接口、模块 | `mcpowers-feat` |
| bug/报错/不生效/异常/失败/修一下 | `mcpowers-bugfix` |
| 重构/抽离/拆分/太乱/抽象 | `mcpowers-refactor` |
| 慢/卡/性能/优化/查询慢 | `mcpowers-optimize` |
| 部署/上线/发布/构建 | `mcpowers-deploy` |
| 需求改了/调整逻辑/加字段/改流程 | `mcpowers-requirement-change` |
| 初始化/新项目/脚手架/搭建 | `mcpowers-init` |
| 写需求/写 PRD/整理需求 | `mcpowers-prd` |
| 任务拆解/列计划/排期 | `mcpowers-plan` |
| 按计划执行/实施计划/开始执行 | `mcpowers-execute` |
| 审查/审一下/review/自审 | `mcpowers-code-review` |
| 写测试/TDD/单测 | `mcpowers-tdd` |
| 不清楚要做什么/需求不清 | `mcpowers-brainstorm` |
| 复杂任务/并行/多代理 | `mcpowers-subagent` |
| commit/提交 | `mcpowers-git-commit` |
| worktree/分支隔离/并行工作区 | `mcpowers-git-worktree` |
| 回滚/rollback/撤销/恢复 | `mcpowers-git-rollback` |
| 清理分支/删除分支/整理分支 | `mcpowers-git-cleanBranches` |

---

## 快速安装

### 一键安装（推荐，symlink 模式，参考 superpowers）

```bash
# 1. 克隆仓库
git clone git@github.com:742366981/mcpowers.git ~/mcpowers
cd ~/mcpowers

# 2. 运行安装脚本
bash install.sh            # macOS / Linux / Git Bash on Windows
# 或 Windows PowerShell:
.\install.ps1
```

**安装内容**：
- ✅ 1 个主入口路由器（`mcpowers`）
- ✅ 18 个场景/方法技能（`mcpowers-feat` 等）
- ✅ 规范库（`mcpowers-shared/docs/`）

> **两种触发方式并存**：① **自然语言自动路由**（说「加个功能」自动命中 `mcpowers-feat`）；② **斜杠直接调用**（`/mcpowers-feat`）。本技能不额外注册 `~/.claude/commands/` 下的传统命令文件，避免命令重名冲突。

**symlink 模式的好处**（superpowers 风格）：
- 📝 编辑源文件后**立即生效**（无需重装）
- 🔄 升级 = `git pull`（无需重装）
- 💾 仓库本身就是 source of truth

> mcpowers **完全独立**：Git 操作由自有 `mcpowers-git-*` 4 个技能处理，无需依赖任何外部技能。

### 手动安装（不用脚本）

```bash
# macOS / Linux / Git Bash
mkdir -p ~/.claude/skills
cp -r mcpowers ~/.claude/skills/
cp -r skills/scene/* skills/method/* ~/.claude/skills/
cp -r mcpowers-shared ~/.claude/skills/

# Windows PowerShell（等价命令）
```

### 升级

```bash
cd ~/mcpowers
git pull
# symlink 模式：升级完成，无需重装
# copy 模式（如安装时用了 --copy / -Copy）：重新跑 install.sh
```

### 卸载

```bash
bash uninstall.sh         # macOS / Linux / Git Bash
# 或 Windows:
.\uninstall.ps1
# 跳过确认：bash uninstall.sh --yes   /   .\uninstall.ps1 -Yes
```

### 验证安装

装完后：

1. **重启 Claude Code**
2. 直接说"加个用户登录接口"，AI 应自动调 mcpowers-feat
3. 路径应是 `~/.claude/skills/mcpowers-feat/SKILL.md`（无 `skills/skills/`）

### 安装后目录结构

```
~/.claude/
├── settings.json                       # hooks 自动注册（含 _mcpowers_marker）
└── skills/                              # Claude Code 扫描根
    ├── mcpowers/                        # 路由器 + hooks 资产
    │   ├── SKILL.md
    │   └── hooks/                       # symlink 到本仓库 hooks/
    │       ├── hooks.json
    │       ├── session-start.sh
    │       └── pre-bash-guard.sh
    ├── mcpowers-feat/SKILL.md           # 18 个技能扁平
    ├── mcpowers-bugfix/SKILL.md
    ├── mcpowers-brainstorm/SKILL.md
    ├── ... (15 more)
    └── mcpowers-shared/                 # 规范库
        ├── SKILL.md
        ├── mcpowers-spec-index/SKILL.md
        └── docs/...
```

> 无 `~/.claude/commands/mcpowers/` —— 本技能不注册传统命令文件，但技能本身支持斜杠调用（`/mcpowers-feat`），也可自然语言自动触发。

### Windows PowerShell 执行策略

首次运行 `.\install.ps1` 若被拦截，先执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

或绕过策略：

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

---

## Hooks 行为

mcpowers 安装时会自动在 `~/.claude/settings.json` 注册两个 Claude Code hooks，让铁律从"软提示"升级为"硬约束"。

| 钩子 | 触发时机 | 作用 |
|:-----|:---------|:-----|
| `SessionStart` | 每次 Claude Code 启动 | 注入路由器铁律摘要（改前确认 / TDD 先行 / 改完即 commit 等），AI 每轮对话开始就知道 mcpowers 流程 |
| `PreToolUse (Bash)` | 每次执行 Bash 命令前 | 阻断 `rm -rf /`、`git push --force main` 等危险操作 |

### 跳过 hooks 安装

不需要 hooks 的用户可以：

```bash
bash install.sh --no-hooks      # macOS / Linux / Git Bash
.\install.ps1 -NoHooks          # Windows PowerShell
```

跳过安装后 `~/.claude/settings.json` 不会被修改；卸载时也不会清理（因为没有 mcpowers 标记）。

### 故障排查与详细说明

见 [`hooks/README.md`](hooks/README.md)：

- Hooks 资产位置和升级机制
- 跨平台说明（依赖 Git Bash / WSL）
- 误伤正常命令时如何调整白名单
- 卸载失败的恢复方法

---

## 借鉴来源

- **superpowers**（https://github.com/obra/superpowers）：using-superpowers bootstrap 模式、brainstorming / TDD / debugging 铁律、code-review 流程

---

## 仓库地址

git@github.com:742366981/mcpowers.git
