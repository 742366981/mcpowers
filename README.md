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
mcpowers-shared/
├── docs/
│   ├── AI操作规范.md     # AI 操作总规范
│   ├── 技术规范/         # API、数据库、Git、代码规范等
│   ├── 产品设计/         # 产品设计规范
│   └── API文档/          # API 文档模板
└── tools/               # 工具脚本
```

### 规范路径

| 类型 | 路径 | 使用方式 |
|:-----|:-----|:---------|
| AI操作规范 | `~/.claude/skills/mcpowers-shared/docs/AI操作规范.md` | AI 操作总规范 |
| 技术规范 | `~/.claude/skills/mcpowers-shared/docs/技术规范/` | AI 直接读取 |
| 产品设计 | `~/.claude/skills/mcpowers-shared/docs/产品设计/` | AI 直接读取 |
| 项目文档 | 项目 `docs/` | 按需创建 |

> 注：规范由 AI 从技能目录直接读取，新项目通过开发环境规范自动创建配置

---

## 新项目初始化

新项目创建时，AI 会根据开发环境规范自动创建项目配置：

1. **触发**：说"开始开发"或"初始化项目"
2. **AI 自动执行**：
   - 创建 .gitignore
   - 创建语言特定文件（requirements.txt 等）
   - 创建虚拟环境脚本
   - **从模板创建 CLAUDE.md 和 AGENTS.md**（详见开发环境规范）

> 配置模板位于：`~/.claude/skills/mcpowers-shared/docs/技术规范/开发环境规范.md`

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
