# mcpowers

AI 辅助开发的标准化技能体系。**按场景拆分的轻量级技能组合**，借鉴 superpowers 设计。**完全独立运行**（含 Git 操作），不依赖任何外部技能。

## 核心结构

| 目录 | 用途 |
|:-----|:-----|
| `.claude-plugin/` | **插件市场元数据**（`marketplace.json` + `plugin.json`，由 Claude Code 插件系统读取） |
| `skills/mcpowers/` | **主入口路由器**（每次对话注入） |
| `skills/mcpowers-*` | **24 个可路由技能**（场景层 16 + 方法层 8，扁平化） |
| `skills/mcpowers-shared/` | 规范资产库（24 个技术规范 + `mcpowers-spec-index` 导航，v2.6.0 新增 `日志规范.md`） |
| `hooks/` | Claude Code hooks 资产（4 个事件组 / 5 个脚本 + `hooks.json`） |
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
- **自动化测试/E2E/测试报告** → `mcpowers-autoTest`
- **前后端联调/API契约/接口文档** → `mcpowers-api-contract`
- **安装基础技能/一键装基础** → `mcpowers-install-basics-skills`
- **爬虫逆向/加密参数还原/抓包分析/逆向工程/JS反混淆/APP逆向/frida hook/SSL Pinning/爬虫被加密/帮我逆向这个网站** → `mcpowers-crawler-reverse`
- **抽离公共模块/抽离通用能力/提取可复用组件/拆出独立库/爬虫逆向层剥离/抽成公共库/做成可调用脚本/模块化调用** → `mcpowers-extract`
- **装项目级文档同步纪律/给现有项目加 doc-sync/一键安装校验+hook/安装 .doc-sync-rules** → `mcpowers-doc-sync-install`
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

### 文档同步约束（强制）

凡是新增、删除、重命名或调整技能体系的能力、路由、编排、规范、Hook、目录结构、安装方式或版本号，必须在同一变更中同步检查并更新：

- `CLAUDE.md`：维护规则、技能分类、触发映射、数量和验证流程
- `README.md`：用户功能说明、技能树、触发条件、安装和维护指南
- `skills/mcpowers/SKILL.md`：主路由器和技能清单
- `scripts/check-readme-sync.sh`：技能/规范清单和场景技能检查
- `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`：插件版本和市场元数据

新增场景技能时，还必须把技能加入 `SCENE_SKILLS`，并确认其包含 `## 编排` 段。禁止只修改 `skills/` 目录而不更新上述文档和校验项。纯规范正文修订至少运行同步检查；凡影响用户可见能力或体系结构的修订必须同步更新两份文档。

#### CI 物理门禁（v2.5.2+）

`.github/workflows/doc-sync.yml` 在 PR 涉及 `skills/`、`hooks/`、`.claude-plugin/`、`scripts/`、`tests/`、规范变化时自动跑：
- `bash scripts/check-readme-sync.sh`（7 类一致性：技能/规范清单、frontmatter、场景编排、版本号、description ≤800c、文档数字声明）
- `bash tests/plugin-verify.sh`（插件结构 + Hook 行为 + 事件组数 = 4 + 引用脚本存在）
- 检查 CLAUDE.md 或 README.md 是否在同一 PR 中变化（**未变化则 PR 红 X**，从"AI 自觉"升级为"合并前硬阻止"）

本地开发可选装 pre-commit hook（参考 README 末尾的 `.git/hooks/pre-commit` 示例）。


## Skill Description 编写规范（强制）

Claude Code 通过 L1 索引（每个 skill 的 `description` 字段）做语义匹配。**这是触发灵敏度的唯一可调旋钮**。

### 硬约束

| 项 | 要求 | 后果 |
|:---|:-----|:-----|
| **字符硬上限** | 1024 字符 | 超过会被 Claude Code 截断，**尾部触发词全部失效** |
| **字符安全预算** | ≤ 800 字符 | 保留 ~20% 余量，防误判 |
| **格式** | 单行紧凑（YAML 字符串在一行内） | 多行 `\|` 字面量块浪费 30%+ 字符预算 |

### 4 段式内容（用 `；` `，` 分隔）

```yaml
# ✅ 推荐
description: "骨架1 / 骨架2 / 骨架3 → 触发本技能。口语：xxx,xxx。中英：xxx,xxx。边界：邻技能1→A；邻技能2→B。流程一句话。"

# ❌ 禁止
description: |
  骨架触发
  
  口语：xxx      # ← 多行浪费 30%+ 字符预算
```

每段作用：
1. **骨架触发**（3-5 个最高频词） → 一眼命中
2. **口语变体**（30-50 个口语/倒装/省略） → 长尾覆盖
3. **中英混输**（3-8 个英文术语） → 兼容开发场景
4. **边界防误触发**（指向最相似邻技能） → 防止串技能

### 修改 description 后必跑检查

```bash
python -c "import os, re
for f in sorted(os.listdir('skills')):
  p = os.path.join('skills', f, 'SKILL.md')
  if not os.path.isfile(p): continue
  c = open(p, encoding='utf-8').read()
  m = re.search(r'^---\n(.*?)\n---', c, re.DOTALL)
  if not m: continue
  d = re.search(r'description:\s+(.+?)\s*$', m.group(1), re.MULTILINE)
  if not d: continue
  print(f'{f}: {len(d.group(1))}c {\"⚠\" if len(d.group(1))>800 else \"✓\"}')"
```

任一文件 > 800c → **立刻压缩**，**不要等截断问题出现再修**。

### 历史教训（v2.0.3 → v2.0.4）

- **v2.0.3**：一次 description 大改版用 `|` 多行块，**3 个文件超 1024c 被截断**（code-review 1091c / brainstorm 1050c / bugfix 1027c），尾部"出错了"、"闪退"、"帮我审"等高频触发词全部失效。
- **v2.0.4**：全部改为单行紧凑版，**L1 description 总预算从 ~9000c 降到 5986c（-34%）**，**0 个文件超 800c**。

### 历史教训（v2.6.0 新增顶层规范）

- **v2.6.0**：新增 `日志规范.md` 时，只改 `mcpowers-spec-index` 查表 + CLAUDE.md/README.md 数字声明**不够**。还必须同步改造至少 5 个相关编排：
  - `mcpowers-init`：注入日志基础设施（`utils/loggings.py` + `utils/request_log.py` + `log/` 目录）
  - `mcpowers-feat`：常见规范组合 + 架构设计阶段必读 + 完成后自检清单
  - `mcpowers-bugfix`：调查方法加"按 `request_id` / `trace_id` 串联日志"
  - `mcpowers-deploy`：上线 checklist 加"日志收集方案 + 大内容策略 + 轮转保留"
  - 否则规范进了体系但**不触发**，等于没加。
- **结论**：新增顶层规范是**横跨 9+ 文件**的改动（1 新规范 + 1 spec-index + 5 技能编排 + 2 文档 + 2 版本文件），不能省任何一处。

### 反模式（禁止）

- ❌ 多行 `|` 字面量块（截断风险首要元凶）
- ❌ 单段长句无结构（LLM 难以切片做语义匹配）
- ❌ 触发词与边界说明混在一起（混淆 L1 匹配方向）
- ❌ 单个 description < 100 字符（覆盖太窄，命中率低）
- ❌ 不区分近义技能（refactor / bugfix / requirement-change 极易串技能）

## 版本管理（强制）

**Claude Code 插件市场以 `plugin.json` 的 `version` 字段为唯一更新触发器**。version 不变，用户（包括你自己）的 Update now / `/plugin install` 都不会拉取新版。

### 修改技能体系后必须做

1. **bump version**：修改 `.claude-plugin/plugin.json` 的 `version` 字段
   - 修复 bug / 小改 → patch：`2.0.0` → `2.0.1`
   - 新增技能 / 功能 → minor：`2.0.0` → `2.1.0`
   - 破坏性改动 → major：`2.0.0` → `3.0.0`
2. **同步市场元数据**：`.claude-plugin/marketplace.json` 的 `plugins[0].version` 必须与 `plugin.json.version` 一致；当前单插件市场的顶层 `version` 也保持同一发布版本，避免元数据漂移。
3. **验证后再提交**：先运行 `bash scripts/check-readme-sync.sh`，再运行 `bash tests/plugin-verify.sh`。
4. **commit + push**：版本号和代码改动放在同一个 commit（或分两个 commit 都行，但必须一起 push）
5. **不要**用任何 hack 方式绕过 version 机制（删缓存、自建更新脚本等都禁止）

用户收到新版只需：
- `/plugin` → 选 mcpowers → `Update now`
- 或 `/plugin uninstall mcpowers@mcpowers` → `/plugin install mcpowers@mcpowers`

两种方式都需要先 bump version 才能生效。

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

- **精准路由**：单入口路由器（`skills/mcpowers/`）+ 扁平化技能目录（24 个可路由技能），按意图关键词精准分流
- **方法复用**：TDD / Review / Plan / Brainstorm 等方法层技能被场景层按需编排
- **按需加载**：通过 `mcpowers-spec-index` 查表按需 Read 规范文件，避免爆上下文
- **铁律双约束**：软约束靠技能描述（`铁律` 段落 + `## 反模式（禁止）` ❌ 清单），硬约束靠 Claude Code hooks 物理阻断
- **资产零损耗**：24 个技术规范原地保留，路径不重组、不重命名
- **完全独立**：不依赖任何外部技能，Git 操作由 4 个 `mcpowers-git-*` 技能自包含
- **零安装脚本**：依赖 Claude Code 插件系统管理安装/卸载/升级，仓库零维护成本
