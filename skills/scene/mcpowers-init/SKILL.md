---
name: mcpowers-init
description: 用户要"初始化/新项目/搭脚手架/新建工程"时触发。新项目从 0 到 1 落地，老项目接入 mcpowers 规范体系。
---

# mcpowers-init（项目初始化）

> 借鉴自旧 7 步法 Step 0（新项目初始化）。
> **目标**：让新/老项目都有完整的规范基线，AI 能按规范协作。

---

## 触发即执行

### 1. 识别项目类型

| 类型 | 识别方式 |
|:-----|:---------|
| **全新项目** | 目录为空 / 只有 README |
| **存量项目** | 已有代码、git 仓库 |
| **存量项目接入 mcpowers** | 有代码但没有规范文件 |

### 2. 加载规范
- Read `mcpowers-shared/mcpowers-spec-index/SKILL.md`
- 加载：
  - `mcpowers-shared/docs/技术规范/开发环境规范.md`（**必读**）
  - `mcpowers-shared/docs/技术规范/文档编写规范.md`（**必读**）
  - `mcpowers-shared/docs/AI操作规范.md`（**必读**）
  - 对应栈规范（识别出技术栈后）

### 3. 与用户确认
问清楚：
- 项目名
- 技术栈（Python/Flask？Vue？爬虫？）
- 部署目标（Linux？Docker？K8s？）
- 数据库（MySQL？PostgreSQL？MongoDB？）
- 缓存（Redis？）
- 是否需要 CI/CD

### 4. 创建基础文件（全新项目）

| 文件 / 目录 | 用途 |
|:------------|:-----|
| `README.md` | 项目说明 |
| `CLAUDE.md` | AI 项目配置（自动加载） |
| `AGENTS.md` | 其他 AI 工具配置（内容同 CLAUDE.md） |
| `.gitignore` | Git 忽略规则 |
| `requirements.txt` 或 `pyproject.toml` | Python 依赖 |
| `package.json` | Node 依赖 |
| `docs/` | 文档目录（按规范结构） |
| `tests/` | 测试目录 |
| `.env.example` | 环境变量示例（不提交真值） |

### 5. 接入 mcpowers 规范（所有项目类型）
- 把 `mcpowers-shared/docs/` 软链或复制到项目 `docs/`
- 在 `CLAUDE.md` 顶部加：
  ```markdown
  ## 加载规范
  本项目遵循 mcpowers 规范体系：
  - 路由器：mcpowers 主入口（自动注入）
  - 规范索引：mcpowers-spec-index（按需 Read）
  - 规范文件：docs/技术规范/*.md
  ```
- 提示用户安装 mcpowers 系列技能到 `~/.claude/skills/`

### 6. 老项目接入（存量项目）
除上述外，**额外**：
- [ ] 评估现有代码与规范的差距
- [ ] 列出现状清单：
  ```
  ## 现状
  - 后端：Flask 2.0
  - 数据库：MySQL 8.0
  - 缓存：Redis 6
  - 部署：Docker
  - 测试覆盖：30%
  - 文档：缺失
  ```
- [ ] 制定改造计划（哪些规范先落地）
- [ ] 渐进式落地（不要一次大改）

### 7. 验证
- [ ] 项目结构清晰
- [ ] 基础文件齐全
- [ ] 规范文件可访问
- [ ] AI 能正常加载（用简单问题测试）

---

## 标准目录结构

```
项目根/
├── CLAUDE.md
├── README.md
├── AGENTS.md
├── .gitignore
├── .env.example
├── requirements.txt
├── package.json
├── docs/
│   ├── 原始需求/        # 用户原始需求
│   ├── 需求文档/        # 结构化 PRD
│   ├── 设计文档/        # 架构 / 概要设计
│   ├── 计划/            # 实施计划
│   ├── 细节记录/        # 重要决策、问题排查
│   ├── 技术规范/        # 软链到 mcpowers-shared/docs/技术规范
│   └── 接口文档/        # API 文档
├── src/ 或 app/         # 源代码
├── tests/               # 测试
├── temp/                # 临时文件（gitignore）
└── scripts/             # 脚本
```

---

## 反模式（禁止）

- ❌ 不问用户就用默认栈
- ❌ 老项目一次性大改
- ❌ 不写 `CLAUDE.md`（AI 无法加载项目级配置）
- ❌ 把 `.env` 提交到 git
- ❌ 不建 `temp/` 目录（临时文件乱放）
- ❌ 不建 `docs/` 目录（文档无处放）

---

## 完成后

- 调 `mcpowers-code-review` 自审
- 调 `mcpowers-git-commit` 提交（initial commit）
- 给用户完整的"项目现状清单"
