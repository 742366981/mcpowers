# mcpowers

AI 辅助开发的标准化技能体系，提供完整的开发流程规范和技术标准。

---

## 技能列表

| 技能 | 触发词 | 用途 |
|:-----|:-------|:-----|
| `mcpowers-workflow` | 新项目 / 开始开发 / 初始化项目 | 7 步法开发流程 |
| `mcpowers-flask-dev` | Flask 项目 / Flask 后端 / Python 后端 | Flask 后端规范 |
| `mcpowers-vue-dev` | Vue 项目 / Vue 前端 / 前端项目 | Vue 3 前端规范 |
| `mcpowers-crawler-dev` | 爬虫项目 / 爬虫开发 / 数据采集 | 爬虫开发规范 |

---

## 快速安装

```bash
# 克隆仓库
git clone git@github.com:742366981/mcpowers.git ~/mcpowers

# 安装所有技能
for skill in mcpowers-workflow mcpowers-flask-dev mcpowers-vue-dev mcpowers-crawler-dev; do
  cp -r ~/mcpowers/$skill ~/.claude/skills/
done
```

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

### 规范路径

| 类型 | 路径 | 使用方式 |
|:-----|:-----|:---------|
| 技术规范 | `~/mcpowers/docs/技术规范/` | AI 直接读取 |
| 产品设计 | `~/mcpowers/docs/产品设计/` | AI 直接读取 |
| 项目文档 | 项目 `docs/` | 按需创建 |

> 注：规范由 AI 从技能目录直接读取，不复制到项目

---

## 新项目初始化

```bash
# 1. 复制项目模板
cp ~/mcpowers/CLAUDE.md ~/你的项目/

# 2. 在项目中开始开发
cd ~/你的项目
# 说"开始开发"触发工作流
```

---

## 规范清单

### 通用规范
| 规范 | 用途 |
|:-----|:-----|
| API规范.md | API 设计 |
| 数据库规范.md | 数据库设计 |
| 缓存规范.md | 缓存使用 |
| 定时任务规范.md | 定时任务 |
| 部署规范.md | 项目部署 |
| Git规范.md | Git 使用 |
| 开发环境规范.md | 项目初始化 |
| 代码同步修改规范.md | 变更同步 |
| 代码规范.md | 代码质量（SOLID/KISS/DRY/YAGNI） |
| 设计规范.md | 文档编写 |
| 测试规范.md | 测试 |
| 细节记录规范.md | 细节记录 |
| 文档编写规范.md | 文档标准 |
| 导入导出规范.md | 导入导出 |

### 技术锁规范
| 规范 | 适用项目 |
|:-----|:---------|
| Flask后端规范.md | Flask 后端 |
| Vue前端规范.md | Vue 前端 |
| 爬虫规范.md | 爬虫 |
