# mcpowers

AI 辅助开发的标准化技能体系，提供完整的开发流程规范和技术标准。

---

## 技能列表

| 技能 | 触发词 | 用途 |
|:-----|:-------|:-----|
| `mcpowers-workflow` | 新项目 / 开始开发 | 7 步法开发流程 |
| `mcpowers-flask-dev` | Flask 项目 / Python 后端 | Flask 后端规范 |
| `mcpowers-vue-dev` | Vue 项目 / 前端开发 | Vue 3 前端规范 |
| `mcpowers-crawler-dev` | 爬虫项目 / 数据采集 | 爬虫开发规范 |

---

## 规范体系

```
docs/
├── 技术规范/
│   ├── 通用规范/     # API、数据库、Git、代码规范等
│   └── 技术锁规范/   # Flask、Vue、爬虫专项规范
└── 产品设计/
    └── 产品设计规范.md
```

---

## 使用方式

1. 安装技能到 `~/.claude/skills/`
2. 在项目中创建 `CLAUDE.md`（参考模板）
3. 开发时说"开始开发"触发工作流

---

## 规范路径

- 技术规范：`~/mcpowers/docs/技术规范/`
- 产品设计：`~/mcpowers/docs/产品设计/`

> 注：规范由 AI 从技能目录直接读取，不复制到项目
