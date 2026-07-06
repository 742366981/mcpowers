# mcpowers

AI 辅助开发的标准化技能体系。**按场景拆分的轻量级技能组合**，覆盖产品 → 开发 → 测试 → 部署全生命周期。借鉴 superpowers 设计：主入口路由器 + 场景触发 + 规范按需加载。**完全独立运行**，不依赖任何外部技能（含 Git 操作）。

---

## 设计理念

| 维度 | 旧版（已废弃） | 新版 |
|:-----|:---------------|:-----|
| 单次对话加载 | 2142 行全量 | ~150 行路由器 + 按需 ~200 行 |
| 触发方式 | 7 步法整体触发 | 精准路由到场景技能 |
| 规范加载 | 全量预加载 | 按需 Read（渐进式披露） |
| 维护成本 | 改一处要同步多处 | 规范资产零损耗，技能独立 |
| 实际使用率 | 低（太重） | 高（精准触发） |

> ⚠️ **v2 重构说明**：原 `mcpowers-workflow`（2142 行单体）已拆分为路由器 + 14 个场景/方法技能。详见 `mcpowers-workflow/SKILL.md`（已降级为重定向说明）。

---

## 技能结构

```
mcpowers/
├── mcpowers/                          # 主入口路由器（< 150 行，每次对话注入）
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

```bash
# 克隆仓库
git clone git@github.com:742366981/mcpowers.git ~/mcpowers

# 安装技能
cp -r ~/mcpowers/mcpowers ~/.claude/skills/
cp -r ~/mcpowers/skills ~/.claude/skills/
cp -r ~/mcpowers/mcpowers-shared ~/.claude/skills/
```

> mcpowers **完全独立**：Git 操作由自有 `mcpowers-git-*` 4 个技能处理，无需依赖任何外部技能。

---

## 核心原则

- **路由器轻量**：主入口只做路由，< 150 行
- **场景精准触发**：每个场景技能 < 200 行，`description` 描述精确
- **规范按需加载**：`mcpowers-spec-index` 提供"做什么 → 读哪个"的查表
- **方法复用**：TDD / Review / Plan 等不重复写，被场景层调用
- **铁律强制**：TDD 铁律（NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST）、Debug 铁律（NO FIXES WITHOUT ROOT CAUSE）
- **规范资产零损耗**：13+ 规范文件原地保留，路径不变

---

## 借鉴来源

- **superpowers**（https://github.com/obra/superpowers）：using-superpowers bootstrap 模式、brainstorming / TDD / debugging 铁律、code-review 流程

---

## 仓库地址

git@github.com:742366981/mcpowers.git
