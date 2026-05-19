# mcpowers

AI 开发流程技能体系，提供标准化的项目开发规范和工作流程。

## 包含技能

| 技能 | 说明 | 触发词 |
|:-----|:-----|:-------|
| mcpowers-workflow | 核心工作流程 + 通用规范 | AI开发、流程、规范 |
| mcpowers-flask-dev | Flask 后端专项规范 | Flask、flask |
| mcpowers-vue-dev | Vue 3 前端专项规范 | Vue、vue、Vue3 |
| mcpowers-crawler-dev | Python 爬虫专项规范 | 爬虫、crawler |

## 安装

```bash
# 克隆到 Claude Code 技能目录
git clone <仓库地址> ~/.claude/skills/mcpowers
```

## 使用方式

在 Claude Code 对话中描述需求，技能会自动加载：

```
"用 Flask 开发一个用户管理模块"
"Vue 项目需要权限管理"
"要抓取某网站数据"
```

## 规范体系

- **通用规范**：API、数据库、Git、代码、测试等
- **技术锁规范**：Flask、Vue、爬虫等专项规范

## 更新日志

- 2026-05-19: 初始版本
