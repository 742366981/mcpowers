---
name: mcpowers-init
description: "新项目 / 脚手架 / 项目初始化 / 帮我搭个新项目 / 从零开始 → 触发本技能。口语：我要开/起/建个项目、帮起/建个项目、新建工程/仓库/项目、创建项目/仓库/工程、搭脚手架/搭新项目/搭工程、立项、从零开始/0 开始/从头开始、做新项目/全新项目、空白项目、初始化项目、接入 mcpowers/老项目接入/把 mcpowers 加到这个项目、搞个 demo/demo 项目。中英：init, bootstrap, scaffold, create project, new project, from scratch, greenfield, kickoff。新项目从 0 到 1，老项目接入 mcpowers 规范。"
---

# mcpowers-init（项目初始化）

> **mcpowers 自身设计**，基于 `开发环境规范.md` + `AI操作规范.md`。
> **目标**：让新/老项目都有完整的规范基线，AI 能按规范协作。

---

## 编排

本技能按顺序调用以下方法层技能 + 规范：

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | 规范组（`开发环境规范` + 栈规范） | 规范 | 必读 | 提示加载 |
| 2 | 项目类型识别 | 内联 | 必走 | 不识别则中断 |
| 3 | 标准化目录结构 | 内联 | 按项目类型 | 不可缺 |
| 4 | `mcpowers-code-review` | 方法 | 初始化完成 | 验证脚手架完整 |
| 5 | `mcpowers-git-commit` | 场景 | 自审通过 | 阻断提交 |

**保护路径**：`mcpowers-shared/`、`mcpowers/`、`hooks/` 三个目录的写操作触发前确认。

**铁律**：禁止跳过规范基线（哪怕 demo 也要带基线）；禁止不识别项目类型硬套模板。

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
  - **`mcpowers-shared/docs/技术规范/日志规范.md`（v2.6.0+ 必读）** —— 注入日志基础设施的源头
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
| **`utils/loggings.py`**（v2.6.0+ 必建） | 日志封装类（按 `日志规范.md §3` + `Flask后端规范.md §6.1`） |
| **`utils/request_log.py`**（v2.6.0+ Flask 必建） | 全局请求日志中间件（按 `日志规范.md §3.3` request 类型字段 + `Flask后端规范.md §5.2`） |
| **`log/`**（v2.6.0+ 必建） | 日志输出目录（按 `日志规范.md §7.2` 文件命名与轮转规范） |

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
- [ ] **日志基础设施已注入（v2.6.0+）**
  - [ ] `utils/loggings.py` 已建（日志封装类，按 `日志规范.md §3` 字段约定）
  - [ ] `utils/request_log.py` 已建（Flask 全局请求日志中间件，按 `日志规范.md §3.3` request 类型字段）
  - [ ] `log/` 目录已建（按 `日志规范.md §7.2` 文件命名与轮转规范）
  - [ ] 设计文档已在"系统架构"章节声明日志类型 + 字段 + 大内容策略（按 `日志规范.md §9`）
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
