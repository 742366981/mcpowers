# mcpowers

AI 辅助开发的标准化技能体系。**按场景拆分的轻量级技能组合**，借鉴 superpowers 设计。**完全独立运行**（含 Git 操作），不依赖任何外部技能。

## 核心结构

| 目录 | 用途 |
|:-----|:-----|
| `.claude-plugin/` | **插件市场元数据**（`marketplace.json` + `plugin.json`，由 Claude Code 插件系统读取） |
| `skills/mcpowers/` | **主入口路由器**（每次对话注入） |
| `skills/mcpowers-*` | **31 个可路由技能**（场景层 23 + 方法层 8，扁平化） |
| `skills/mcpowers-shared/` | 规范资产库（31 个技术规范 + `mcpowers-spec-index` 导航，v2.6.0 新增 `日志规范.md`；v2.14.0 爬虫拆分 7 册；v2.15.0 协作模式 B 工具化 `user-action-recorder.py`；v2.22.0 Flask/爬虫日志实现层对齐 `日志规范.md`——按 type 分文件、禁止按级别切文件；v2.23.1 docker-compose 启动命令统一：`up -d --force-recreate`、`--build` 不带 `--force-recreate`、stop/down 区分停止与删除） |
| `hooks/` | Claude Code hooks 资产（4 个事件组 / 7 个脚本 + `hooks.json`；v2.26.0+ 含 `pre-write-check-duplicate.sh` 重复函数检测；v2.27.0+ 含 `pre-write-check-import.sh` Python 局部 import 拦截） |
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
- **自动化测试/E2E/测试报告/跑 pytest/跑 Playwright/跑 DrissionPage/跑 Selenium/跑 Cypress** → `mcpowers-autoTest`（新增自动化默认 Python；先查项目证据，已有套件沿用）
- **前后端联调/API契约/接口文档** → `mcpowers-api-contract`
- **安装基础技能/一键装基础** → `mcpowers-install-basics-skills`
- **爬虫逆向/接口分析/抓包分析/加密参数还原/RPC逆向/纯协议/半自动化/纯自动化/一次性报文/token复用/并发稳定性/模块真实可用/目标类型不明** → `mcpowers-crawler-reverse`（统一入口）
- **网站逆向/Web JS反混淆/浏览器抓包/CDP接管/WASM/bb-browser** → `mcpowers-reverse-web`
- **App逆向但平台或运行时未知/识别App技术栈** → `mcpowers-reverse-app`（二级入口）
- **Android逆向/安卓/APK/AAB/Kotlin/Java/JNI/jadx/frida hook/LSPosed** → `mcpowers-reverse-android`
- **iOS逆向/苹果App/IPA/Mach-O/Swift/Objective-C/LLDB** → `mcpowers-reverse-ios`
- **Flutter逆向/Dart AOT/libapp.so/App.framework/Platform Channel** → `mcpowers-reverse-flutter`
- **混合App逆向/uni-app/React Native/Cordova/Capacitor/WebView/JSBridge/Hermes** → `mcpowers-reverse-hybrid`
- **小程序逆向/小游戏/微信小程序/支付宝小程序/抖音小程序/百度小程序/wxapkg** → `mcpowers-reverse-miniprogram`
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

**自动化选型基线**：新增自动化默认使用 Python + pytest；先检查项目已有测试文件、依赖、配置和 CI/脚本证据；已有非 Python 套件沿用原框架，未知框架不得凭 AI 熟悉度引入。

**日志分文件基线**：按业务 type 分文件（`biz.log` / `audit.log` / `request.log` / …），**级别是 JSON 的 `level` 字段，不是文件名后缀**；禁止 `xxx_info.log` / `xxx_error.log` 这类按级别切文件（会拆散同一 `request_id` 的链路）；ERROR+ 仅以**聚合流**形式额外落一份 `error.log`。详见 `日志规范.md §7.2` + `Flask后端规范.md §6.0`。

**本技能禁止使用环境变量（v2.25.0+ 全栈适用最高铁律）**：仓库所有 .py / .sh / .js / .ts 源文件以及应用本规范的所有项目代码**一律禁止**读环境变量——Python 禁 `os.environ.*` / `os.getenv` / `from os import environ`；Shell 禁 `echo "$XXX"` / `${XXX}` 从外部环境读；JS/TS 运行时禁 `process.env.*` / `dotenv.config()`。配置统一走**文件 + 加载器**或**命令行参数**；OS 探测（浏览器路径、用户目录）走 `pathlib.Path.home()` + 已知路径硬编码 + `shutil.which()` 组合。唯一允许的例外：`hooks.json` 的 `${CLAUDE_PLUGIN_ROOT}` 与 Docker Compose YAML 的 `environment:` 字段（这两处不进入 mcpowers 代码运行时）。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 「最高铁律 · 本技能禁止使用环境变量」段；栈级落地见 `Flask后端规范.md §4.1` / `Vue前端规范.md` / `爬虫工具与抓包规范.md`。

**复用优先于二次抽象（v2.26.0+ 全栈适用铁律）**：写新函数 / 新类 / 新模块前必须先扫仓库 + SDK + 通用模块是否已有等价实现——禁止「明明 SDK 已有，又包一层」的二次抽象。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §6.1.1。物理兜底：`hooks/pre-write-check-duplicate.sh` 在 `PreToolUse(Write|Edit|MultiEdit)` 时检测新增 `def` / `function` / `func` / `fn` 与仓库已有同名定义冲突，命中则弹 Claude Code confirm UI（exit 2）。审查门禁：`mcpowers-code-review` 增 R1-R7 Critical 反模式表（未扫仓库就写 wrapper / 二次抽象仅一行调用 / 命名冲突 / 跨项目搬运不复用 / 抽象类单实现 / 公共函数零调用方 / 绕过 `utils/loggings.py` 自写清理）。方法层落地：`mcpowers-feat` 触发即执行 10 步中新增「## 2.5 已有资产扫描」强制步骤（PR 描述必填扫描清单）。

**日志免压缩窗口（v2.26.0+ 强制基线）**：日志文件轮转后**不立即** gzip——保留最近 N 天的轮转文件为明文（默认 7 天，`keep_recent_uncompressed_days = 7`，可配 `0` 表示立即压缩）；超过窗口的轮转文件才压缩为 `.gz`；超过保留期的 `.gz` 文件清理。详见 [`日志规范.md`](skills/mcpowers-shared/docs/技术规范/日志规范.md) §7.2 + §7.3「轮转 → 清理 → 压缩时序」4 阶段；栈级落地见 `Flask后端规范.md §6.3` 的 `compress_old_logs` / `purge_old_logs` 双函数（爬虫项目复用同一对函数，详见 `爬虫规范.md §12.3`）。

**mcpowers 注入路径稳定性（v2.27.1+ 全栈适用铁律）**：mcpowers 注入到用户项目的内容（CLAUDE.md 段、`utils/loggings.py`、`.doc-sync-rules.yml`、`.git/hooks/pre-commit`、模板等）**禁止**含物理路径字面值——`~/.claude/plugins/cache/mcpowers/mcpowers/{version}/...`（升级即失效）、`~/.claude/plugins/marketplaces/mcpowers/...`（本地开发模式才是这条，与 GitHub 模式混用会解析错）、`~/.claude/skills/mcpowers-shared/...`（v2.0+ 已废弃）、自定义占位符如 `<mcpowers>`。AI 引用规范**只写抽象路径**（如 `mcpowers-shared/docs/技术规范/Flask后端规范.md §6.3`）；AI 在 Claude Code 会话里跑 bash 需要物理路径时用 `${CLAUDE_PLUGIN_ROOT}/...`（Claude Code 框架在调用工具前自动展开的字符串占位符，**不是 shell / Python 进程环境变量**；AI 在源文件运行时**读不到**它）；**不**提议"软链 mcpowers-shared/docs 到项目 docs/"。**安装方式决定物理路径**：① 本地开发模式（`/plugin marketplace add <本地仓库路径>`）→ `${CLAUDE_PLUGIN_ROOT}` = `~/.claude/plugins/marketplaces/mcpowers`（**不带版本号**）；② GitHub 插件市场模式（`marketplace add https://...` + install）→ `${CLAUDE_PLUGIN_ROOT}` = `~/.claude/plugins/cache/mcpowers/mcpowers/{version}/`（**带版本号**）。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 「最高铁律 · mcpowers 注入路径稳定性」段。

**Python import 顶层（v2.27.0+ 全栈适用铁律）**：Python 文件的 `import` / `from ... import ...` 必须位于模块级导入区，按标准库、第三方、本项目模块分组；函数、方法、类体、条件块、装饰器内部禁止局部 import。局部 import 仅在循环依赖或真正可选依赖时可例外，且必须写明原因并由用户确认；禁止以"延迟加载 / 按需使用 / 性能优化"作为默认理由。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)「Python import 位置规范」段。物理兜底：`hooks/pre-write-check-import.sh`（含 `check_python_import_placement.py`）在 `PreToolUse(Write|Edit|MultiEdit)` 时 AST 检测新增的局部 import，命中则弹 Claude Code confirm UI（exit 2）；Write 视为覆盖、Edit/MultiEdit 仅 diff 新增违规。规范层落地：`mcpowers-feat` / `mcpowers-tdd` / `mcpowers-code-review` 已在自检清单与审查维度加 import 位置检查，`mcpowers-code-review` 增 R8 反模式条目与「v2.27.0+ Python import 位置扫描 Quick-Check」grep 两条。

**注入物版本号写死禁令（v2.27.3+ 全栈适用铁律）**：mcpowers 注入到用户项目的内容（CLAUDE.md 段、`utils/loggings.py`、`.doc-sync-rules.yml`、`.git/hooks/pre-commit`、`.doc-sync-check.sh` 模板、`user-action-recorder.py` 等）**禁止**硬编码 mcpowers 版本号字面值（`v{major}.{minor}.{patch}` / `{version}/` / `cache/mcpowers/mcpowers/{version}/`）；注入物必须描述为"对应 mcpowers 最新版本的纪律"，后续访问永远指向最新版本。版本演进历史只允许出现在 `.claude-plugin/*.json` / `CHANGELOG.md` / `docs/历史教训.md`。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)「最高铁律 · mcpowers 注入路径稳定性 §注入物版本号写死禁令」。

**运行时版本访问白名单（v2.27.4+ 全栈适用铁律）**：上条禁的是"注入物硬编码版本号"。本条允许的是"AI 运行时访问历史版本"——AI 在 Claude Code 工具调用层 `ls ~/.claude/plugins/cache/mcpowers/mcpowers/` 发现用户已装的旧版本 → `Read` 读该版本规范（version 是运行时发现，**不**是预先硬编码）；项目根存在 `.mcpowers-version: v{major}.{minor}.{patch}` 时 AI 默认读该版本；用户显式指定"按 v{major}.{minor}.{patch} 规范写"时 AI 按指令读历史版本。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)「最高铁律 · mcpowers 注入路径稳定性 §运行时版本访问白名单」。

**规范稳定性分级 + CHANGELOG 强制破坏声明（v2.27.4+ 全栈适用铁律）**：所有 31 份规范 frontmatter 必须声明 `stability: stable|evolving|deprecated` + `last_breaking_change: v{major}.{minor}.{patch}`；AI 读取规范后必读这两个字段决定行为（stable 假设跨 minor 兼容 / evolving 升级时主动查 CHANGELOG / deprecated 不写新代码）。每次 mcpowers 发布的 `CHANGELOG.md` 必须含 `### Breaking Changes` 段（哪怕标"无"），作为用户升级兼容性的**唯一权威索引**。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)「最高铁律 · mcpowers 注入路径稳定性 §CHANGELOG 强制破坏声明段」；方法层落地：`mcpowers-code-review` 增 R9 stability 审查维度 + 审查动作清单第 6 项。

**终态交付基线**：文档与代码注释只描述当前状态，不保留历史演进痕迹（"原为 xxx" / "已废弃" / 变更历史章节）与参考来源指代（"参考 xxx 文档"）；变更历史只允许出现在 `CHANGELOG.md` 与 README「最近变更」。详见 `文档编写规范.md §9` + `代码规范.md §11.3`。

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

新增工具脚本时（如 `skills/<技能>/scripts/<新工具>.py`），还必须把脚本路径加到对应规范文档的 §工具对照表 / §字典库对应关系（参考《爬虫工具与抓包规范》§7.2 / 末尾附录）+ 顶层维护文档引用（参考 v2.15.0 `user-action-recorder.py` 的 8 类同步）。

#### CI 物理门禁（v2.5.2+）

`.github/workflows/doc-sync.yml` 在 PR 涉及 `skills/`、`hooks/`、`.claude-plugin/`、`scripts/`、`tests/`、规范变化时自动跑：
- `bash scripts/check-readme-sync.sh`（12 类一致性：技能/规范清单、frontmatter、场景编排、版本号、description ≤800c、文档数字、引用、逆向分层拓扑、公共合同、浏览器所有权门禁）
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

### 反模式（禁止）

- ❌ 多行 `|` 字面量块（截断风险首要元凶）
- ❌ 单段长句无结构（LLM 难以切片做语义匹配）
- ❌ 触发词与边界说明混在一起（混淆 L1 匹配方向）
- ❌ 单个 description < 100 字符（覆盖太窄，命中率低）
- ❌ 不区分近义技能（refactor / bugfix / requirement-change 极易串技能）
- ❌ 在本文件复制 `docs/历史教训.md` 或 `CHANGELOG.md` 内容（v2.21.1+ 强制；仅允许 1 行相对链接）

> **历史归档**：完整版本复盘（v2.0.3 → 当前）见 [`docs/历史教训.md`](docs/历史教训.md)。
> **用户视角变更**：见 [`CHANGELOG.md`](CHANGELOG.md)。

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

- **精准路由**：单入口路由器（`skills/mcpowers/`）+ 扁平化技能目录（31 个可路由技能），按意图关键词精准分流
- **方法复用**：TDD / Review / Plan / Brainstorm 等方法层技能被场景层按需编排
- **按需加载**：通过 `mcpowers-spec-index` 查表按需 Read 规范文件，避免爆上下文
- **铁律双约束**：软约束靠技能描述（`铁律` 段落 + `## 反模式（禁止）` ❌ 清单），硬约束靠 Claude Code hooks 物理阻断
- **资产零损耗**：31 个技术规范原地保留，路径不重组、不重命名
- **完全独立**：不依赖任何外部技能，Git 操作由 4 个 `mcpowers-git-*` 技能自包含
- **零安装脚本**：依赖 Claude Code 插件系统管理安装/卸载/升级，仓库零维护成本
