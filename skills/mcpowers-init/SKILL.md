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
| 5+ | `mcpowers-doc-sync-install`（联动） | 方法 | v2.9.1+ 步骤 3 用户选「是」 | 不阻断（仅纪律装配） |

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
- **是否需要装 doc-sync 纪律（v2.9.1+ 新增）**：让接口/路由/数据表/环境变量改了忘同步文档时，`git commit` 自动被拦。AskUserQuestion 三选一：
  - **A · 启用拦截**（全新项目默认）→ init 末尾自动接管 commit；改路由/表结构忘了同步文档会立刻被拦
  - **B · 仅手动跑**（存量项目默认）→ 装脚本和规则但**默认不接管 commit**；提供 enable / disable 便利脚本；用于清理存量漏改期间过渡
  - **C · 不装纪律** → 仅依赖 L3 AI 自觉层（用户后续也可单独调 `mcpowers-doc-sync-install` 补装）
  - **AI 智能默认**：依据步骤 1 识别结果预选默认档（全新项目→A；存量项目→B），用户改默认也接受

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

### 5+ 联动安装 doc-sync 纪律（v2.9.1+ 新增 · 与用户零摩擦）

**目标**：用户只说一次「初始化新项目」，纪律按项目类型智能就位——不再需要事后主动调 `mcpowers-doc-sync-install`。

**触发**：依据步骤 3 选择的档位（A / B / C）分别执行。

#### 共同前置（A / B 都要做）

**复用 init 步骤 1 的项目类型识别结果**（flask / vue / crawler / generic）：

```bash
mkdir -p scripts
cp "${CLAUDE_PLUGIN_ROOT}/scripts/templates/project-doc-sync-check.sh" "scripts/check-doc-sync.sh"
chmod +x scripts/check-doc-sync.sh
cp "${CLAUDE_PLUGIN_ROOT}/scripts/templates/project-doc-sync-rules.<type>.yml" ".doc-sync-rules.yml"
```

#### 选项 A · 启用物理拦截（全新项目默认）

适用：全新项目，目录基本为空，无存量漏改风险。

**接管式 hook 写入**：

```bash
cat > .git/hooks/pre-commit << 'HOOK_EOF'
#!/usr/bin/env bash
set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -f "$REPO_ROOT/scripts/check-doc-sync.sh" ]; then
    bash "$REPO_ROOT/scripts/check-doc-sync.sh" || {
        echo "✗ doc-sync 校验失败，commit 中止"
        exit 1
    }
fi
HOOK_EOF
chmod +x .git/hooks/pre-commit
```

**验证**：`bash scripts/check-doc-sync.sh` 必须 PASS（全新项目通常通过）。

**预期产物**：
- `scripts/check-doc-sync.sh`
- `.doc-sync-rules.yml`
- `.git/hooks/pre-commit`（**接管 commit**，FAIL 则 exit 1）

#### 选项 B · 仅手动跑 + 手动启用（存量项目默认）

适用：存量项目接入，已有代码可能存在 α 类漏改（规则列出的接口 / 路由 / 数据表 / 环境变量但文档未提）。

**为什么不直接接管**：存量项目装上接管式 hook 后，**首次 commit 几乎必被拦**，用户会被突然拦截吓到且不知如何应对——这是 L2 设计要规避的反模式。

**正确做法**：装好脚本和规则，提供 enable / disable 便利脚本，**不接管 commit**：

```bash
# enable 脚本（用户清理完存量漏改后手动启用）
cat > scripts/enable-doc-sync-hook.sh << 'ENABLE_EOF'
#!/usr/bin/env bash
# 启用 doc-sync commit 拦截（给存量项目清理期结束后手动启用）
set -e
HOOK=".git/hooks/pre-commit"
if [ -f "$HOOK" ] && grep -q "check-doc-sync.sh" "$HOOK"; then
    echo "✓ doc-sync hook 已启用，无需操作"
    exit 0
fi
if [ -f "$HOOK" ]; then
    echo "✗ $HOOK 已存在但不是 doc-sync hook，请手动合并或备份后重试"
    exit 1
fi
cat > "$HOOK" << 'INNER_EOF'
#!/usr/bin/env bash
set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -f "$REPO_ROOT/scripts/check-doc-sync.sh" ]; then
    bash "$REPO_ROOT/scripts/check-doc-sync.sh" || { echo "✗ doc-sync 校验失败，commit 中止"; exit 1; }
fi
INNER_EOF
chmod +x "$HOOK"
echo "✓ doc-sync 拦截已启用（git commit 现在会跑 check-doc-sync.sh）"
ENABLE_EOF
chmod +x scripts/enable-doc-sync-hook.sh

# disable 脚本（用户临时有事要跳过拦截）
cat > scripts/disable-doc-sync-hook.sh << 'DISABLE_EOF'
#!/usr/bin/env bash
# 临时关闭 doc-sync commit 拦截（保留脚本，可随时重新启用）
HOOK=".git/hooks/pre-commit"
if [ ! -f "$HOOK" ]; then
    echo "✓ hook 本来就不存在，无需操作"
    exit 0
fi
if ! grep -q "check-doc-sync.sh" "$HOOK"; then
    echo "✓ hook 不是 doc-sync 类型，不动它"
    exit 0
fi
rm "$HOOK"
echo "✓ doc-sync 拦截已关闭（要重新启用：bash scripts/enable-doc-sync-hook.sh）"
DISABLE_EOF
chmod +x scripts/disable-doc-sync-hook.sh
```

**验证**：`bash scripts/check-doc-sync.sh` 跑一次，**不管 PASS / FAIL 都告知用户**：
- PASS（存量项目当前已合规）→ 主动询问"要不要现在启用拦截？"
- FAIL（典型场景）→ 给 α 类漏改修复指引（见下方「失败处理」）

**预期产物**：
- `scripts/check-doc-sync.sh`
- `.doc-sync-rules.yml`
- `scripts/enable-doc-sync-hook.sh`
- `scripts/disable-doc-sync-hook.sh`
- **不创建** `.git/hooks/pre-commit`（commit 不被接管）

#### 选项 C · 不装纪律

跳过整个 5+ 联动，仅依赖 L3 AI 自觉层。

#### 失败处理（α 类已有漏改）

A 或 B 模式跑 `bash scripts/check-doc-sync.sh` FAIL 时：

1. **不要重试 hook 注入**——FAIL 是预期（存量项目常有 α 类漏改）
2. **给用户清晰指引**：
   ```
   ⚠️ doc-sync 规则发现 N 处 FAIL
   原因：α 类已有漏改（项目原本就有的接口/路由/表结构，docs/ 未对应提及）
   处置（任选其一）：
   - 临时禁用：编辑 .doc-sync-rules.yml 把对应 rule 的 `enabled: true` 改为 `enabled: false`
   - 永久修复：补齐 docs/ 中对应内容，再重跑 bash scripts/check-doc-sync.sh
   - 存量项目推荐用 B 模式（不接管 commit），等补齐后切换到 A
   ```
3. **绝不让 hook 直接 exit 1**——α 漏改不是 init 应承担的责任

**铁律**：
- ✅ 步骤 3 选项**只问一次**（按项目类型 AI 预选默认），不重复问
- ✅ 全新项目默认 A（无存量风险）；存量项目默认 B（避免突然被拦）
- ✅ A 模式必须先验证 PASS 才算完成；B 模式不强求 PASS（告知即可）
- ❌ 不接管式地"装上 hook 然后让用户首次 commit 被拦"——这是最常见的设计反模式
- ✅ 例外：用户对存量项目**首次**想补纪律，仍可单独调 `mcpowers-doc-sync-install`（该技能主要面向存量场景）

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
- [ ] **doc-sync 纪律已联动（v2.9.1+ 必检）**
  - [ ] **选了 A**：`scripts/check-doc-sync.sh` 存在且 `+x`；`bash scripts/check-doc-sync.sh` 跑通（全新项目应 PASS）；`.git/hooks/pre-commit` 已写入且内容含 `check-doc-sync.sh` 引用
  - [ ] **选了 B**：`scripts/check-doc-sync.sh` 存在且 `+x`；`scripts/enable-doc-sync-hook.sh` 和 `scripts/disable-doc-sync-hook.sh` 都存在且 `+x`；`.git/hooks/pre-commit` **不存在**或不含 `check-doc-sync.sh` 接管；FAIL 项已按 α 漏改指引告知用户
  - [ ] **选了 C**：在"项目现状清单"明确告知用户纪律未装 + 提供后续补救入口（`mcpowers-doc-sync-install` / `bash scripts/enable-doc-sync-hook.sh` 如适用）
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
- **告知纪律状态（v2.9.1+ 必做）**：
  - **选了 A**：告知「已装 doc-sync **物理拦截**：此后改路由/数据表/环境变量忘了同步文档，`git commit` 会被自动拦截；临时跳过可用 `git commit --no-verify`；永久关闭：`bash scripts/disable-doc-sync-hook.sh`」
  - **选了 B**：告知「已装 doc-sync 但**不接管 commit**——先跑 `bash scripts/check-doc-sync.sh` 看 FAIL 项，按提示补 docs；补齐后 `bash scripts/enable-doc-sync-hook.sh` 启用拦截；临时跳过可用 `git commit --no-verify`」
  - **选了 C**：告知「未装 doc-sync 纪律：当前只靠 AI 自觉层同步文档；后续想装可单独调 `mcpowers-doc-sync-install`」
