# mcpowers

AI 辅助开发的标准化技能体系。**按场景拆分的轻量级技能组合**，借鉴 superpowers 设计。**完全独立运行**（含 Git 操作），不依赖任何外部技能。

## 核心结构

| 目录 | 用途 |
|:-----|:-----|
| `.claude-plugin/` | **插件市场元数据**（`marketplace.json` + `plugin.json`，由 Claude Code 插件系统读取） |
| `skills/mcpowers/` | **主入口路由器**（< 150 行，每次对话注入） |
| `skills/mcpowers-*` | **18 个技能**（场景层 11 + 方法层 7，扁平化） |
| `skills/mcpowers-shared/` | 规范资产库（21 个规范文件 + `mcpowers-spec-index` 导航） |
| `hooks/` | Claude Code hooks 资产（4 个 hook + `hooks.json`） |
| `tests/` | 插件结构验证（`plugin-verify.sh`） |
| `scripts/` | 工具脚本（`check-readme-sync.sh`） |

## 触发条件

`mcpowers` 主入口路由器在每次对话自动加载，识别用户意图后路由到对应技能：

- **加功能/新增接口/做页面** → `mcpowers-feat`
- **修 bug/报错/不生效** → `mcpowers-bugfix`
- **重构/抽离/拆分** → `mcpowers-refactor`
- **性能优化/查询慢** → `mcpowers-optimize`
- **部署/上线/发布** → `mcpowers-deploy`
- **需求变更/调整逻辑/加字段** → `mcpowers-requirement-change`
- **新项目/初始化/脚手架** → `mcpowers-init`
- **写需求/PRD/文档** → `mcpowers-prd`
- **任务拆解/列计划** → `mcpowers-plan`
- **按计划执行/实施计划/开始执行** → `mcpowers-execute`
- **代码审查/自审** → `mcpowers-code-review`
- **写测试/TDD** → `mcpowers-tdd`
- **需求不清/澄清** → `mcpowers-brainstorm`
- **复杂任务/并行** → `mcpowers-subagent`
- **commit/提交** → `mcpowers-git-commit`
- **worktree/分支隔离** → `mcpowers-git-worktree`
- **回滚/撤销** → `mcpowers-git-rollback`
- **清理分支** → `mcpowers-git-cleanBranches`

## 规范体系

位于 `mcpowers-shared/docs/技术规范/`：
- **通用规范**：API、数据库、缓存、Git、代码(SOLID/KISS/DRY/YAGNI)、测试、部署等
- **技术锁规范**：Flask后端、Vue前端、爬虫

**按需加载**：场景/方法层技能不预加载规范，而是通过 `mcpowers-spec-index` 查表（"做什么 → 读哪个规范"）按需 Read。

## 仓库地址

git@github.com:742366981/mcpowers.git

## 技能修改流程（重要）

修改本技能时，请遵循以下流程：

1. **先改本项目**：在当前工作目录下修改
2. **插件市场模式无需重装**：直接重启 Claude Code 即可生效（除非是首次安装）
3. **最后推送**：commit 并 push 到 git 仓库

**禁止**直接修改 `${CLAUDE_PLUGIN_ROOT}` 下的安装副本（插件市场模式下改了会被覆盖）。所有修改在源码仓库根目录进行。

## 技能安装（首次/重装）

通过 Claude Code 插件市场：

```bash
/plugin marketplace add https://github.com/742366981/mcpowers
/plugin install mcpowers@mcpowers
```

本地开发模式（指向本地路径）：

```bash
/plugin marketplace add /d/document/my/workspace/mcpowers
/plugin install mcpowers@mcpowers
```

## 设计维度

- **精准路由**：单入口路由器（`skills/mcpowers/`）+ 扁平化技能目录（18 个），按意图关键词精准分流
- **方法复用**：TDD / Review / Plan / Brainstorm 等方法层技能被场景层按需编排
- **按需加载**：通过 `mcpowers-spec-index` 查表按需 Read 规范文件，避免爆上下文
- **铁律双约束**：软约束靠技能描述（`铁律` 段落 + `## 反模式（禁止）` ❌ 清单），硬约束靠 Claude Code hooks 物理阻断
- **资产零损耗**：21+ 规范文件原地保留，路径不重组、不重命名
- **完全独立**：不依赖任何外部技能，Git 操作由 4 个 `mcpowers-git-*` 技能自包含
- **零安装脚本**：依赖 Claude Code 插件系统管理安装/卸载/升级，仓库零维护成本
