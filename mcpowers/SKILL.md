---
name: mcpowers
description: mcpowers 技能体系总入口。每次对话自动注入，识别用户意图后路由到对应的场景/方法技能，避免加载过重的工作流。覆盖产品→开发→测试→部署全生命周期。
---

# mcpowers 路由器

> **核心思想**：单次对话只加载当前场景需要的技能，不预加载全部规范。
> 借鉴 superpowers 的 `using-superpowers` bootstrap 模式。

---

## 0. 全局硬约束（强制红线）

> ⚠️ **AI 每次响应前必须自检，违反任何一条视为不合格**。

### 必须做
1. **修改前**先分析影响、询问用户确认
2. **修改时**遵守 `mcpowers-shared/docs/技术规范/代码同步修改规范.md`
3. **完成时**立即 commit（禁止多个独立任务后才 commit）
4. **接口开发**先写 docstring，再写实现
5. **代码注释**完整（函数 docstring + 类注释 + 复杂逻辑注释）
6. **临时文件**放 `temp/` 目录，用完即删
7. **改完同步**更新 README / 文档（代码和文档必须同 commit）

### 禁止做
1. ❌ 未经用户确认直接修改任何代码/文档
2. ❌ 先写代码后补文档
3. ❌ 只 commit 代码不 commit 文档
4. ❌ 多处重复定义同一内容
5. ❌ 在项目根目录创建临时文件
6. ❌ 违反 SOLID/KISS/DRY/YAGNI 原则

完整规范见 `mcpowers-shared/docs/AI操作规范.md`，**仅在需要时按需 Read**。

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
