# mcpowers

AI 辅助开发的标准化技能体系。

## 核心结构

| 目录 | 用途 |
|:-----|:-----|
| `mcpowers-workflow/` | 7 步法开发流程技能（唯一入口） |
| `mcpowers-shared/` | 技术规范库（供 workflow 引用） |

## 触发条件

`mcpowers-workflow` 技能在以下场景被触发：
- 新项目 / 开始开发 / 继续开发 / 继续项目 / 初始化项目
- 产品设计 / 需求分析 / PRD
- 需求变更 / 需求修改 / 加个功能 / 改个需求

## 规范体系

位于 `mcpowers-shared/docs/技术规范/`：
- **通用规范**：API、数据库、缓存、Git、代码(SOLID/KISS/DRY/YAGNI)、测试、部署等
- **技术锁规范**：Flask后端、Vue前端、爬虫

## 仓库地址

git@github.com:742366981/mcpowers.git

## 技能修改流程（重要）

修改本技能时，请遵循以下流程：

1. **先改本项目**：在当前工作目录下修改
2. **再安装到本地**：执行下面的安装命令同步到 `~/.claude/skills/`
3. **最后推送**：commit 并 push 到 git 仓库

**禁止**直接修改 `~/.claude/skills/` 下的技能源码（除非是临时调试）。

## 技能安装

修改技能源码后，执行以下命令安装到本地：

```bash
# 从当前目录安装技能
cp -r mcpowers-workflow ~/.claude/skills/
cp -r mcpowers-shared ~/.claude/skills/
```
