# mcpowers

AI 辅助开发的标准化技能体系。**按场景拆分的轻量级技能组合**，借鉴 superpowers 设计。**完全独立运行**（含 Git 操作），不依赖任何外部技能。

## 核心结构

| 目录 | 用途 |
|:-----|:-----|
| `.claude-plugin/` | **插件市场元数据**（`marketplace.json` + `plugin.json`，由 Claude Code 插件系统读取） |
| `skills/mcpowers/` | **主入口路由器**（每次对话注入） |
| `skills/mcpowers-*` | **31 个可路由技能**（场景层 23 + 方法层 8，扁平化） |
| `skills/mcpowers-shared/` | 规范资产库（31 个技术规范 + `mcpowers-spec-index` 导航，v2.6.0 新增 `日志规范.md`；v2.14.0 爬虫拆分 7 册；v2.15.0 协作模式 B 工具化 `user-action-recorder.py`） |
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

### 历史教训（v2.9.5 强化单技能能力）

- **v2.9.5**：升级 `mcpowers-crawler-reverse` 时发现，单技能能力强化（新增 §2.7 弹窗检测 + §3.0 协作模式 + §3.4.5 置信度）也必须横跨**至少 6 类文件**同步：
  - 1 主技能 SKILL.md（description + 阶段 2 SOP 重构 + 阶段 4.5 强化 + 自检清单 + 反模式）
  - 1 共享规范文档（§2.5 + §2.7 + §3.0 + §3.4.5 + 附录 D）
  - 1 spec-index 查表（加 v2.9.5 子节链接）
  - 1 新增工具脚本（`popup-handler.py`，与字典库对应）
  - 2 顶层文档（CLAUDE.md + README.md 注释）
  - 3 版本文件（`plugin.json` + `marketplace.json` × 2）
- **结论**：**单技能强化 ≠ 单文件改动**。CLAUDE.md "文档同步约束" 提到的 6 类文件（`CLAUDE.md` + `README.md` + `SKILL.md` + `check-readme-sync.sh` + `plugin.json` + `marketplace.json`）是**底线**，还要算上共享规范和新增脚本。**凡是用户可见的能力变化，都必须按这个清单同步**。

### 历史教训（v2.10.0 集成第三方 CLI）

- **v2.10.0**：`bb-browser`（[epiral/bb-browser](https://github.com/epiral/bb-browser)）是首个被正式集成到爬虫逆向 SOP 的第三方 CLI / MCP server。外部工具接入不能只改主技能，必须同步维护 6 类文件：`CLAUDE.md`、`README.md`、`SKILL.md`、`scripts/check-readme-sync.sh` 校验边界、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`；同时还要同步共享规范 `last_updated` frontmatter、§2.5.5 详情页、spec-index 查表行、相关工具脚本的 docstring 注释（popup-handler.py 加 `DEFAULT_BB_BROWSER_PROBE` 提示常量）。
- **关键设计**：bb-browser 必须是**可选依赖**。未安装、daemon 未运行、adapter 未命中或版本不兼容时，v2.9.5 的 Chrome CDP + Playwright + popup-handler.py 原链路必须**完全可用**，不得把第三方 CLI 变成硬依赖；任何缺 bb-browser 就会失败的写法都是反模式。
- **关键经验**：技能 description 接近 1024c 时，必须**先压缩重复触发词和能力描述**（从长流程压缩为"骨架 / 口语 / 中英 / 边界"4 段式），再增加 `bb-browser`、`site adapter`、`MCP server`、`登录态保留` 等新触发词；实施前后都要用 Python 检查字符数，预算严格控制在 800c 以内，避免尾部高频词被截断。
- **关键工具设计**：`popup-handler.py` 的职责边界是 DOM 弹窗处理，**不引入 `probe_browser_daemon()` 函数**（避免引入 Node / subprocess 依赖），daemon 探测由 SKILL.md §2.0 SOP 层说明；脚本只新增 `DEFAULT_BB_BROWSER_PROBE` 提示常量声明职责边界。

### 历史教训（v2.11.1 bb-browser 实操补全）

- **v2.11.1**：v2.10.0 集成 bb-browser 后真实用户复盘发现 3 类实操缺失——**安装指引未指定安装位置与 Node 版本要求**、**daemon 与 Playwright 共享 Chrome CDP 的启动顺序与端口分配不明确**、**adapter 调用失败判定与结果合并规则缺失**。这 3 类问题属于 v2.10.0 文档化的「已知风险」未在 SOP 落地。
- **关键修复**：补 3 个子节——SKILL.md §2.5.5.0 安装与 MCP 配置（含双轨 fallback：全局 + 本地+npx，规避 Issue #6 SSL 错误）、§2.5.5.1 daemon + Playwright 共享 Chrome CDP 实操（含启动顺序、端口分配、4 步验证）、§2.0.5.1 adapter 失败判定与结果合并（含 4 类失败判定、调用日志格式、合并冲突优先级、api-inventory.md 加「来源」列）。
- **关键经验**：第三方 CLI 集成**不只是「可选用法 + 反模式」**，必须包含**完整实操链路**（安装 → 启动 → 验证 → 失败处理 → 结果合并）；任何「链接到 README 自己看」的写法都是反模式，因为用户复盘时不可能跳出去读外部文档。
- **版本策略**：v2.10.0 → v2.11.1 是 patch bump（文档完善 + bug fix），不是 minor（无新功能），符合 CLAUDE.md 版本管理规则。
- **docstring 注释同步**：popup-handler.py 的 `DEFAULT_BB_BROWSER_PROBE` 常量在 v2.11.1 中仍是「最小改动 + 职责声明」，不引入 daemon 探测代码（守住 YAGNI 边界）。

### 历史教训（v2.12.0 真实可用性验收门禁）

- **v2.12.0**：真实用户复盘发现，接口 `[🎯]`、≥ 3 组 sign 一致、单次 HTTP 200 和模块文件生成只能分别证明接口语义、算法或单次协议有效，**不能证明模块真的可用**；旧流程缺少阶段 5 → 6/7 的硬门禁，容易在重复调用、跨会话、一次性 token 或并发尚未验证时过早创建完整骨架。
- **关键修复**：新增 SKILL.md 阶段 1 交付形态确认（纯协议 / 半自动化 / 纯自动化），明确 RPC 只是阶段 4 的逆向实现方式；新增阶段 5.5 +《爬虫分析规范》§1.1/§9.4，强制从模块公开入口验证业务语义、至少 2 组输入/合计 ≥ 5 次、至少 2 个 session/冷启动、原报文重放、动态参数重生成、跨 session、TTL 和有界并发 2 → 5；统一产出 `verification-report.md`，只有 `PASS` 才能进入阶段 6/7。
- **生命周期分类**：关键状态必须归类为 `reusable` / `per-request` / `single-use-token` / `session-bound` / `time-bound` / `challenge-bound` / `unknown`；`unknown` 禁止冒充可复用，原报文无法重放不等于逆向失败，模块能按生命周期持续生成有效新报文才是关键。
- **YAGNI 边界**：轻量模块不引入 Session 池、代理池、Redis 队列或任务调度，但必须包含完成一次真实业务调用所需的最小 token/challenge/session 生命周期，或通过清晰接口显式注入；禁止把抓包临时 token/Cookie/nonce 写进常量。
- **安全边界**：并发仅做小规模 2 → 5 可用性验证，不做压力测试；出现 429、验证码增加、账号提示、目标异常或授权/条款边界时立即停止。
- **版本策略**：v2.11.1 → v2.12.0 是 minor bump，因为新增了用户可见的验收阶段、生命周期分类和并发门禁，不是纯文档修正。

### 历史教训（v2.13.0 逆向分层与浏览器所有权）

- **v2.13.0**：原 `mcpowers-crawler-reverse` 同时装载 Web、Android/iOS App、Flutter/Hybrid、小程序和公共验收，导致平台无关任务也加载全部工具链。现拆为统一入口 + Web + App 二级入口 + Android/iOS/Flutter/Hybrid/小程序 7 个专项；公共前置、阶段 5.5、生命周期和落地门禁仍由统一入口唯一维护。
- **分类原则**：先按载体，再按运行时；Kotlin/Java/JNI 归 Android，Swift/Objective-C 归 iOS，uni-app/RN/Cordova/Capacitor/WebView 归 Hybrid，单个平台小程序暂不继续平铺。专项只交标准证据，禁止复制公共验收或自行宣布 PASS。
- **浏览器所有权铁律**：通过 CDP/WebView/daemon 接管的 browser/context/page/tab 和外部 daemon 一律视为外部所有。正常收尾、异常和回退都不得 `browser.close()`、`context.close()`、关闭既有 page、kill 用户 Chrome 或 stop 外部 daemon；纯协议验收通过停止依赖并独立调用完成，绝不能为了测试而关闭用户本身的浏览器。
- **门禁**：`check-readme-sync.sh` 增至 12 类检查，新增 reverse 拓扑/公共合同与外部资源所有权断言，防止后续合并回单体或恢复危险清理逻辑。
- **版本策略**：新增 7 个用户可见场景技能与二级路由，`2.12.0 → 2.13.0` 为 minor bump。

### 历史教训（v2.14.0 爬虫分析规范拆分 7 册 + 1 配套）

- **v2.14.0**：原 `爬虫分析规范.md` 单文件 1710 行 / 81KB，§2 抓包与工具独占 584 行 / 34%，单一文件按需加载效率低；reverse 技能已按平台拆为 7 个专项，对应规范文档也应**按相同拓扑拆分**。
- **关键修复**：保持主《爬虫分析规范.md》为公共方法论（§1 流程/§3-§6 接口分析/§9.4 验收/§10.9 指纹交接/§11 风控），新增 7 个独立规范文件——`爬虫工具与抓包规范.md`（公共配套：抓包/自动化/CDP/弹窗字典/bb-browser/协议层）+ `爬虫Web逆向规范.md` + `爬虫Android逆向规范.md` + `爬虫IOS逆向规范.md` + `爬虫Flutter逆向规范.md` + `爬虫Hybrid逆向规范.md` + `爬虫小程序逆向规范.md`。
- **所有权铁律跨册落地**：§2.5.2.1「外部接管资源不可关闭」原文保留在主《爬虫分析规范》§1.3 作为唯一权威引文；实操步骤放工具册 §3.5.1；Web 逆向册、Hybrid 册、小程序册各自按需引用主册 §1.3；不允许各平台专项重复定义铁律。`check-readme-sync.sh` §12 OWNERSHIP_FILES 加入新册路径，仍校验 `外部接管资源不可关闭` 字符串。
- **跨文件职责边界**：工具册唯一维护抓包工具栈、CDP 接管、弹窗字典 8 类、bb-browser MCP；各平台专项只维护本平台逆向方法（脱壳/SSL Pinning/IPA/blutter/JSBridge 等）；主册只维护公共方法论；不允许相同内容在两个规范文件出现（包括章节级别）。
- **同步面**：本次横跨 25 个文件改动——1 主册瘦身 + 7 新增规范 + spec-index 查表/树/计数 + 8 reverse/统一入口 SKILL.md 编排表 + extract + 爬虫规范.md + popup-handler.py 4 处注释/print + CLAUDE.md + README.md + plugin.json + marketplace.json + check-readme-sync.sh §12；CI doc-sync.yml PROTECTED_PATHS 检测会强制要求 CLAUDE.md/README.md 同 PR 变化。
- **版本策略**：新增 7 册用户可见规范 = minor bump，`2.13.0 → 2.14.0`。

### 历史教训（v2.15.0 协作模式 B 工具化）

- **v2.15.0**：协作模式 B（用户操作 + AI 抓包）自 v2.9.5 起只有口头协议，无工具支撑；真实用户复盘发现 AI 自动化分析页面按钮操作耗时过长，期望"人操作 + AI 监控抓包 + 记录操作流 + 沉淀可重放脚本"。
- **关键设计**：选型 A-最小（5h）只做录制 + 重放，**不**做 AI 智能 selector、失败自愈、HAR diff、数据点标注（守 YAGNI，避免重复造 popup-handler 字典维护的轮子）。
- **关键技术约束**：Playwright `record_har_path` 在 `connect_over_cdp` 模式不可用（只对 `launch()` / `launch_persistent_context()` 创建的 context 生效），本模块手写 `page.on("request"/"response")` 落 JSONL 格式 HAR。
- **职责边界（DRY/SOLID）**：与 `popup-handler.py` 严格分工——popup-handler 主动查询 + 关闭弹窗；recorder 被动监听 + 落操作流。**不**在 recorder 内部调用 `cleanup_all()`（避免隐式副作用）。两个工具通过 SOP 串联：`cleanup_all()` → `start_recording()`。
- **资源所有权**：全程遵守 §1.3 铁律，**禁止** `browser.close()` / `context.close()` / `page.close()`；监听器通过 `page.remove_listener()` 注销（不靠进程结束清理）。
- **版本策略**：新增用户可见工具 + 协作模式 B 工具化 = minor bump `2.14.0 → 2.15.0`。
- **同步面**：本次横跨 8 类文件改动——1 新增工具 + 2 技能 SKILL.md（reverse-web §1.5 / 爬虫分析规范 §3.0.1 模式 B）+ 2 工具/抓包规范（frontmatter + 索引 + §8 全文 + §7.2 + 附录对应）+ 2 版本文件（plugin.json / marketplace.json）+ 2 维护文档（CLAUDE.md / README.md）。

### 历史教训（v2.17.0 模块产物封装形式标准化）

- **v2.17.0**：真实用户复盘（2026-07）发现模块产物**复用体验差**——逆向分析成功后的 `04-模块封装/{module}/client.py`（原 `functions.py`）调用方需要传 `token` / `cookie` / `sign` 等抓包临时参数（这些参数本应是模块内部生命周期管理的）；想测试模块还得跑 `verify.py` 验收脚本（启动成本高）；分析结论文档 + 子目录全英文（`ANALYSIS_PLAN.md` / `05-case-study.md` / `01-target-profile/` 等），后续用户理解成本高。
- **4 类核心修复**：
  - **类式封装**：`functions.py` → `client.py`，默认主入口类（除非纯算法/字典常量）。`ModuleClient` 提供 `build_request` / `do_request` / `parse_response` + `request_and_parse` 便捷方法。
  - **请求与解析分离**：`do_request` 只发请求返回原始 Response，`parse_response` 只解析响应。SRP 原则 + 单元测试可分别 mock。
  - **零前置参数调用**：业务调用方法只接收业务参数（`item_id` 等），token / cookie / sign / nonce / timestamp 模块内部按生命周期分类（`reusable` / `per-request` / `single-use-token` / `session-bound` / `time-bound` / `challenge-bound`）自洽生成。
  - **`quick_test.py` 手动验证入口**：每个模块必备 `if __name__ == "__main__":` 模式，禁止 `sys.argv` 传参；演示 3 类典型用法（业务要数据 / 业务要报文 / 业务要原始响应）。与 `verify.py`（阶段 5.5 真实可用性验收）、`test_*.py`（pytest 单元测试）三者职责分明。
- **顶层分析文件改中文**：`ANALYSIS_PLAN.md` → `分析计划.md`、`05-case-study.md` → `05-案例沉淀.md`（便于用户理解关键决策）。
- **v2.17.0 用户二次确认扩展**：**所有分析文件名 + 子目录强制中文**（不只是顶层），包括 `01-target-profile/` → `01-目标画像/`、`api-inventory.md` → `接口清单.md`、`verification-report.md` → `验收报告.md` 等。Python 模块名（`client.py` / `quick_test.py`）保留英文（PEP 8 + 工具链）。
- **关键决策**：
  - ✅ 类式 + 请求解析分离 + 零前置参数 + quick_test 都是**用户可见约束**，必须写进规范
  - ✅ extract 技能产物也必须遵循新约定（抽离后的模块复用体验同样关键）
  - ⚠️ 不强制改造 `popup-handler.py` / `user-action-recorder.py` 等工具脚本（它们是被别人调用的工具，不是项目级产物）
  - ✅ **v2.17.0 二次确认**：子目录 + 内部文件**全部强制中文**（不只是顶层推荐）
  - ⚠️ Python 模块名（`client.py` 等）保留英文（PEP 8 + 工具链兼容）
- **同步面**：本次横跨 8 个文件改动——1 主规范（《爬虫分析规范》§9.4.6 全段新增 6 小节）+ 1 crawler-reverse SKILL.md（§5 阶段 5 + §1 产物目录）+ 1 extract SKILL.md（§4 封装骨架 + 自检清单 + 反模式）+ 2 顶层维护文档（CLAUDE.md 历史教训 / README.md）+ 1 校验脚本（check-readme-sync.sh 新增 §13）+ 2 版本文件（plugin.json / marketplace.json）。**未**改动 5 个 reverse 专项 SKILL.md + popup-handler.py / user-action-recorder.py 注释（不在本次范围）。
- **版本策略**：新增 4 类用户可见约束（类式 + SRP + 零前置参数 + quick_test）+ 顶层文件改中文 = minor bump `2.16.0 → 2.17.0`。

### 历史教训（v2.18.0 DrissionPage 全场景默认化）

- **v2.18.0 真实用户复盘（2026-07-28）**：用户反馈"DrissionPage 自动化逆向分析能力更强、占用更低、代码量更少，希望默认优先用"——本质是分析/封装脚本的**代码量**痛点（链式 selector 比 Playwright 短 30~50%），不是工具能力短板。
- **关键修复（11 类文件改动）**：
  1. **规范主表**：《爬虫工具与抓包规范》§2.1 + §7.2 工具栈主表第一行从 Playwright 改为 **DrissionPage**，Playwright 降为 fallback 路径（Cloudflare / 海外 SPA / 复杂 Shadow DOM 场景）。
  2. **接管语法对照**：§2.1 新增接管语法对照表（`connect_over_cdp` → `ChromiumPage(addr_or_opts=ChromiumOptions().set_local_port(9222))`；`page.locator` → `page.ele('css:...')`；`page.on("request", ...)` → `page.listen.start()`）。
  3. **漏抓 7 层 DrissionPage 重新映射**：§3.5 接管粒度 L1/L2/L3 对应 DrissionPage API（`page.tab_ids` + `page.get_tab()` + `page.new_tab(url)`）；§3.6 早检测函数改 `find_target_tab_drissionpage`；§3.9 L3 反模式 `Target.createTarget` → `page.new_tab()` 不带 url；§3.9.4 新增 `ChromiumPage()` 无参反模式 + Chrome 136+ `set_user_data_path(...)` 必传。
  4. **popup-handler.py DrissionPage 适配**：`from DrissionPage import ChromiumPage`；`page.query_selector_all` → `page.eles('css:...')`；`el.is_visible()` → `el.states.is_displayed`；`el.inner_text()` → `el.text`；`page.screenshot()` → `page.get_screenshot()`；`page.wait_for_timeout(ms)` → `time.sleep(s)`。
  5. **user-action-recorder.py DrissionPage 适配**：监听 API 从 Playwright `page.on("request"/"response")` 回调模式改为 DrissionPage `page.listen.start()` + 后台 `_drission_listen_loop` 轮询模式（`page.listen.wait(timeout=0.5)`）；`page.evaluate` → `page.run_js`；`page.locator(sel).first` → `page.ele(f"css:{sel}", timeout=1)`；`page.mouse.wheel` → `page.actions.wheel`；新增 `_screenshot(page, path)` duck-type 封装。Playwright fallback 通过 `hasattr(page, "listen")` 探测自动分支。
  6. **8 reverse SKILL.md 工具栈**：crawler-reverse 铁律 #8 + 6 问自检 L3；reverse-web 编排表 + §1 外部资源所有权 + §2 URL/Method 实测要求 + 6 问自检 L3 全部 DrissionPage 化；reverse-app 加 v2.18.0 提示段（"若目标含浏览器/WebView 调试场景，浏览器自动化工具栈默认按统一入口 §2.1 切到 DrissionPage"）；6 个 App/小程序专项（android/ios/flutter/hybrid/miniprogram）**无 Web 自动化 API 引用**，DrissionPage 化在统一入口 §3.5/§3.6/§3.9 自然继承，无需逐个改。
  7. **check-readme-sync.sh §14 新增**：23 个 string 校验项（§2.1/§7.2 工具栈主表 + §3.5 接管粒度 + §3.6 早检测 + §3.9 漏抓 7 层 + §3.9.4 反模式 + Chrome 136+ user data dir + Chrome 150+ remote-allow-origins + popup-handler 4 项 + user-action-recorder 4 项 + crawler-reverse 2 项 + reverse-web 2 项 + README 1 项），防止后续修改回退。
  8. **CLAUDE.md 本段历史教训**。
  9. **README.md** 加 v2.18.0 DrissionPage 默认化章节。
  10. **plugin.json + marketplace.json × 2** version bump 2.17.0 → 2.18.0。
  11. **同步面**：本次横跨 18 文件 / ~1500 行（v2.18.0 比 v2.17.0 18 文件还多，但行数更多因为 popup-handler / user-action-recorder 全文件改写）。
- **关键决策（YAGNI 守边界）**：
  - ❌ **不**为 Chrome 150+ 兼容专门写 `chrome_starter.py` 工具脚本（用户手动加 `--remote-allow-origins=*` + `set_user_data_path` 在 SOP 中已明确，工具化 YAGNI）。
  - ❌ **不**为 popup-handler 8 类弹窗字典 200+ selector 写"自动迁移工具"（手工逐条改即可，工具化 YAGNI）。
  - ❌ **不**保留双实现（Playwright + DrissionPage 并存）的 wrapper 抽象层——duck typing `hasattr(page, "listen")` 已足够隔离，wrapper 抽象违反 KISS。
  - ✅ **保留 Playwright fallback 路径**（drissionpage 弱场景：Cloudflare Bot Management / 海外 SPA / 复杂 Shadow DOM / iframe 嵌套），duck-type 自动分支。
  - ✅ **保留 bb-browser + popup-handler + user-action-recorder 3 工具**（不重新造轮子）；DrissionPage 接管**同一用户 Chrome**（共用端口 9222），与 v2.10.0 bb-browser 共享 Chrome CDP 兼容。
- **关键风险**：
  - **Chrome 150+ 兼容未实测**：DrissionPage 接管**不自动**加 `--remote-allow-origins=*`，用户必须手动加；SOP §3.7 已明确但**真实接管链路 v2.18.0 还没实测**——需下个版本跑 1 次小验证。
  - **Chrome 136+ 独立 user data dir 必传**：DrissionPage 接管**不自动**处理独立用户目录，调用方必须在 `ChromiumOptions.set_user_data_path(...)` 显式指定；SOP §3.9.4 已明确但容易漏。
  - **DrissionPage 单点维护风险**：g1879 单人维护，API 突然变动可能影响 v2.18.0 全部模块；用 duck-type 隔离后影响面可控。
- **铁律新增**：`mcpowers-crawler-reverse/SKILL.md` 铁律 #8 改写——"bb-browser 不可用时完整回退 DrissionPage（v2.18.0 默认）/ Playwright + popup-handler.py"；§3.5 接管粒度新增"v2.18.0 反模式"`ChromiumPage()` 无参调用；§3.9.4 新增"v2.18.0 反模式"`ChromiumPage()` 静默新开窗口（等价旧 Playwright `launch()`）+ 漏 `set_user_data_path(...)`。
- **版本策略**：新增用户可见能力（DrissionPage 全场景默认 + 接管语法对照 + 漏抓 7 层重新映射 + 2 脚本 DrissionPage 适配 + 8 reverse SKILL 工具栈同步）= minor bump `2.17.0 → 2.18.0`。
- **同步面**：本次横跨 **18 文件 / ~1500 行 / 14/14 校验全绿**——1 主规范（《爬虫工具与抓包规范》§2.1/§2.5/§3.5/§3.6/§3.9.1/§3.9.2/§3.9.4/§7.2/§3.9 实战案例引用）+ 2 工具脚本（popup-handler.py / user-action-recorder.py 全文件改写）+ 1 校验脚本（check-readme-sync.sh §14 新增 23 校验项）+ 8 reverse SKILL.md（crawler-reverse + reverse-web + reverse-app 改动；6 个 App/小程序专项无引用）+ 2 顶层维护文档（CLAUDE.md / README.md）+ 2 版本文件（plugin.json / marketplace.json × 2）。

### 历史教训（v2.18.1 DrissionPage 反检测描述精准化 + Playwright fallback 补 rebrowser 提示）

- **v2.18.1 真实复盘**（commit eb638a8 → 用户反馈"上网确认"）：v2.18.0 §2.1/§7.2 主表第 1 行 DrissionPage 描述为"**内置接管浏览器 + 内置反检测**"——**与公开实测不符**。CSDN 2026-07 三大框架对比 / Python 爬虫三剑客对比（2026-04）等公开资料显示：DrissionPage 优势在 5秒盾/Turnstile **自动化通过率**，**反指纹能力（`navigator.webdriver` 泄露）反而弱于 Playwright + rebrowser / puppeteer-real-browser**。Playwright fallback 路径仅列 3 类场景也漏了 2 类（重度反指纹检测 / 复杂行为分析风控）。
- **关键修复**（3 处描述精准化 + 1 处实测参考链接）：
  1. **§2.1 主表第 1 行 DrissionPage 描述**："**接管便利性 + 国内站点适配**（5秒盾/Turnstile 自动化通过率优势）"+ "**重度反指纹场景需 [rebrowser-playwright-python](https://github.com/rebrowser/rebrowser-playwright-python) / puppeteer-real-browser 配合**（DrissionPage 仍泄露 `navigator.webdriver`）"。
  2. **§2.1 主表第 2 行 Playwright fallback 场景**：从 3 类（Cloudflare/海外 SPA/复杂 Shadow DOM）扩展到 **5 类**——新增 (4) 重度反指纹检测（需 rebrowser-playwright / puppeteer-real-browser 配合）/ (5) 复杂行为分析风控（2026 CF 行为序列/滑块轨迹/代理 IP 纯度）。
  3. **§7.2 主表**：同步 §2.1 两处变更。
  4. **§2.1 段头描述**："Playwright 降为 fallback 路径（DrissionPage 弱场景 5 类——Cloudflare Bot Management / 海外 SPA 复杂交互 / 复杂 Shadow DOM / iframe 嵌套 / 重度反指纹检测 / 复杂行为分析风控，详见 §2.1 主表）"。
  5. **§3.7 加 Chrome 136+ 独立 user data dir 实操代码 + 4 个实测参考链接**：[DrissionPage 官网连接浏览器](https://www.drissionpage.cn/browser_control/connect_browser/) + [Chrome 136 修复方案](https://blog.csdn.net/IHaoT/article/details/147920867) + [Chrome 浏览器启动参数大全](https://www.cnblogs.com/gurenyumao/p/14721035.html) + **v2.18.1 真实接管链路 1 次验证**（v2.18.0 缺失，下个真实场景实测）。
  6. **README.md v2.18.0 章节同步改**：主表第 1 行 DrissionPage 描述精准化 + Playwright fallback 5 类场景 + rebrowser 链接。
  7. **CLAUDE.md 本段历史教训**。
  8. **plugin.json + marketplace.json × 2** patch bump 2.18.0 → 2.18.1。
- **关键决策**：
  - ✅ **保留 v2.18.0 主要技术决策**（DrissionPage 默认 + Playwright fallback + duck type 双实现），只精准化描述，不撤回主决策。
  - ✅ **不引入 rebrowser / puppeteer-real-browser 作为新主工具**——YAGNI 守边界，仅在 fallback 路径作为提示。
  - ✅ **不重做 §14 校验项**——v2.18.0 的 23 个 string 校验与 v2.18.1 描述变更不冲突。
  - ❌ **不立即跑真实接管链路 1 次验证**——v2.18.1 仅修描述，不引入新 SOP 实测；真实接管验证留到下次真实项目。
- **关键风险**：
  - **真实接管链路仍未实测**：v2.18.0 缺真实接管实测，v2.18.1 仍缺——下次真实场景跑 1 次接管（用户启动 Chrome 加 `--remote-allow-origins=*` + 独立 user data dir + `set_local_port(9222)` + DrissionPage 接管）才允许声明实测通过。
  - **v2.18.0 已 commit + push**：v2.18.1 是 patch 修正，GitHub 上 v2.18.0 commit 仍带原描述（不可修改历史 commit）。下次 `/plugin install` 拉到 v2.18.1 即可，但已经拉到 v2.18.0 的用户需要 update。
- **铁律强化**："**未上网确认的事实禁止写进主表 description**"——v2.18.0 复盘发现仅靠工具官网 + 第三方博客还不够，需要 2026 实战对比 + 反指纹能力实测才能精准描述。后续新增工具描述前必须 1 次 WebSearch 验证。
- **版本策略**：精准化描述（不撤回主决策）+ 4 个参考链接 + 不新增工具 = patch bump `2.18.0 → 2.18.1`。
- **同步面**：本次横跨 **4 文件**——1 主规范（《爬虫工具与抓包规范》§2.1 段头 + §2.1/§7.2 主表 + §3.7 Chrome 136+ 独立 user data dir + 4 个参考链接）+ 1 README 章节（v2.18.0 主表 2 行精准化）+ 1 CLAUDE.md 历史教训（本段）+ 2 版本文件（plugin.json + marketplace.json × 2 patch bump）。

### 历史教训（v2.18.2 真实接管链路实测暴露 4 个 bug）

- **v2.18.2**：v2.18.1 §3.7 留下的"真实接管链路 1 次实测"任务，在用户主动验收驱动下落地。**关键发现：4 个真实 bug**——光看代码 + 文档自洽远远不够，必须真实接 Chrome 150+ + DrissionPage 接管才能完整验：
  1. **`user-action-recorder.py:506 duck-type bug**（最致命）——原 v2.18.0 写法 `if hasattr(page, "listen") and callable(getattr(page, "listen", None)):` 中 `callable()` 判断错误：DrissionPage 的 `page.listen` 是 **property 返回 Listener 实例**（`type(page.listen) == DrissionPage._units.listener.Listener`），实例不可 call → `callable(page.listen) == False` → 永远走 Playwright fallback 分支 → 调用 `page.on("request", ...)` → DrissionPage 没有 `page.on` 立刻 `AttributeError`。修复：去掉 `callable()` 判断，仅用 `hasattr(page, "listen")`（DrissionPage 有 `listen`，Playwright 没有，二选一唯一）。**影响**：DrissionPage 接管模式下 `start_recording()` 整个函数完全无法使用。
  2. **`stop_recording` 同样 duck-type bug**——和 Bug 1 同段逻辑，注销监听器分支也走错路径。同步修复。
  3. **`page.actions.wheel` API 误用**——v2.18.0 §2.1 接管语法对照表写 "page.mouse.wheel → page.actions.wheel"，实测 DrissionPage `type(page.actions) == Actions`，方法列表只有 `scroll/click/down/move/key_press/type/wait` 等，无 `wheel`；`page.mouse` 也不存在。正确映射：`page.mouse.wheel(0, dy)` (Playwright) → `page.actions.scroll(delta_y=dy, delta_x=0, on_ele=None)` (DrissionPage)。修复：`user-action-recorder.py:421` 改为 `page.actions.scroll(int(action.get("delta_y", 0)))`；同步同步 `check-readme-sync.sh` §14 校验项从 `page.actions.wheel` 改为 `page.actions.scroll`。
  4. **`popup-handler.py` POPUP_SELECTORS 漏配 notification**——实测 D.2 notification 在 8 类弹窗测试中分类默认 `unknown`，原因是字典漏配 `[id*="notification" i]` 和 `[class*="notification" i]` 两条 selector（其它 7 类都有，仅 notification 漏）。修复：补 2 行；同时 `check-readme-sync.sh` §14 新增 2 项校验。
- **顺带修复 2 个小 bug**：
  - **`stop_recording` 缺 HAR buffer flush** —— `page.on` 改 `listen` 后台线程结束时残留 buffer 直接丢。修复：在 stop 时强制 flush 一次 `handle._har_buffer`。
  - **`replay_actions` 缺防御性读取** —— 旧版硬假设 JSON 是 `{"actions": [...]}` 包装格式；空文件 `/ []` / 损坏 JSON 抛 `TypeError: list indices must be integers or slices, not str`。修复：try/except + 类型判断 + 双格式兼容（dict.actions 或 list）。
- **seen_elements 去重副作用不修（Bug 5）**：实测发现 `seen_elements` 按 element id 去重，但 selector 字段保留的是**先匹配**的 macro selector（不是后匹配的更精确的）。这导致含 `.popup` 通用类的弹窗总是由 `.popup` 行先匹配并占 seen。看似缺陷，**但真实站点不用通用 `.popup` 类名**（都用 `cookie-consent` / `gdpr-banner` / `notification-prompt` 等具体名），所以字典设计本身合理，**不改**（YAGNI 守边界）。
- **完整链路实测环境**（v2.18.2 后 v2.18.1 §3.7 SOP 完整跑通）：
  ```
  Chrome 150.0.7871.187 + --remote-allow-origins=* + --user-data-dir=<独立> + 9222
  + ChromiumOptions().set_local_port(9222).set_user_data_path(<独立>)
  + ChromiumPage(addr_or_opts=co)
  + page.listen.start()  # 接管模式真实可用（v2.18.0 Duck-type bug 修复后）
  + popup-handler 检测 8/8 + 分类 8/8（v2.18.2 notification 补配后）
  + user-action-recorder start/stop 接管模式真实可用
  + page.actions.scroll() 正确 API（v2.18.2 wheel→scroll 修复后）
  ```
- **关键经验**：
  - **代码读起来对 + 文档自洽 ≠ 真实可用**——v2.18.0 一行 `callable()` 误判接管模式整个失效，光看代码 review 无法暴露。
  - **`hasattr(page, "listen")` 优于 `hasattr + callable`**——property 返回的实例永远不 callable；duck-type 检测应只看属性存在与否，不应附加 callable 条件。
  - **DrissionPage API 名 ≠ Playwright** ——即使功能相同（wheel/scroll），API 名常常不一致；接管语法对照表必须**实测验证**，不能凭 Playwright 习惯推。
  - **字典覆盖率必须配套测试**——v2.9.5 上线 8 类弹窗字典后从未实测过 8 类全命中；v2.18.2 跑本地 HTML 测试页立刻暴露 D.2 notification 漏配。**新规范/新字典上线必须配套完整覆盖测试**。
- **铁律新增**：
  - **`scripts/check-readme-sync.sh` §14 新增 5 项校验**——`hasattr(page, "listen")` 检测 / `[class*="notification" i]` 补配 / `[id*="notification" i]` 补配 / `page.actions.scroll` 取代 `page.actions.wheel` / `_replay_one` docstring 改描述；防止后续修改回退 v2.18.2 修复。
  - **新工具/新接管语法 → **必跑** 1 次接管链路口令**：`DrissionPage 真接管 + Chrome 150+ + --remote-allow-origins=*` ——任何「读到 API 文档即可用」的认知都是反模式。
- **版本策略**：4 个用户可见 bug 修复 + 1 字典补配 + 2 小优化（防御 + flush）= minor bump **但**内含的具体功能没新增加，仍属于"接 v2.18.1 §3.7 SOP 实测任务落地"——按 CLAUDE.md 版本规则，bug fix + 字典补配 = patch bump `2.18.1 → 2.18.2`。
- **同步面**：本次横跨 **8 文件**：
  - 2 脚本修：`skills/mcpowers-crawler-reverse/scripts/user-action-recorder.py`（5 处修改：Bug 1+2+3+bug7）/ `popup-handler.py`（2 行字典补配）
  - 1 校验强化：`scripts/check-readme-sync.sh` §14 新增 5 个 string 校验（替换 wheel→scroll / 新增 hasattr + 2 个 notification 补配）
  - 2 顶层维护：`CLAUDE.md`（本段历史教训）+ `README.md`（v2.18.2 节）
  - 2 版本文件：`.claude-plugin/plugin.json` + `marketplace.json × 2` patch bump `2.18.1 → 2.18.2`
  - 1 真实接管链路留痕：`C:\Users\Administrator\AppData\Local\Temp\scraper_test\` 测试脚本与产物（**不**入库，YAGNI 守边界；下次用户撞坑时可直接复用）

### 历史教训（v2.19.0 逆向工作区与 Web 协作会话强制起手式 + 浏览器指纹一致性审计）

- **v2.19.0**：v2.18.2 修完 4 个 bug 后真实用户复盘发现**新的体系缺口**：
  - **缺口 A（执行顺序）**：AI 拿到目标后**不会第一时间落工作区**——目录结构只在 `01-目标画像/` 等描述里出现，但脚本不会自动创建；《分析计划.md》经常到结束才补，slug / 授权边界 / 目标类型都靠"约定"；用户不得不反复追问。
  - **缺口 B（网站逆向）**：Web 默认仍是 A「AI 全自动」，4 选 1 协作模式仍要求用户先决定，但 Chrome 150+ / 强校验表单场景下**用户操作 + AI 抓包才有效**。旧流程让 AI 反复自动点击，既抓不到关键 POST，又让用户被动等待。
  - **缺口 C（OS/浏览器实现）**：宿主 OS、Chrome 路径/版本、CDP 状态、Chrome 136+ 独立 user data dir、Chrome 150+ `--remote-allow-origins=*` 这些前置条件散落在 §3.1/§3.7/§3.9 多个小节，AI 实际使用时容易跳过；浏览器启动方式没有"按 OS 自动选路径"的脚本。
  - **缺口 D（指纹真实性）**：v2.18.0 描述 DrissionPage 时用过"接管便利性 + 内置反检测"等模糊表述，主《爬虫分析规范》也未规定 Web 任务的指纹门禁；AI 容易把"自动化通过率优势"误读成"反指纹"或"指纹真实"，进而继续驱动被风控的目标页。
  - **缺口 E（JS 证据）**：现有 `user-action-recorder.py` 只录操作 + HTTP 流量，没有 JS 运行时（脚本加载、fetch 调用栈、console.error、未处理 reject）的持续证据；AI 在 B 模式后只能看到"用户点了按钮 → 一次 POST"，看不到"为什么是这一次 POST"。
  - **缺口 F（代码注释）**：现有脚本大量英文注释（`# Playwright fallback`、`# DrissionPage: page.listen.stop()`），不利于后续维护者快速理解。

- **关键修复**（11 类文件改动）：
  1. **新增唯一公开起手工具** `skills/mcpowers-crawler-reverse/scripts/reverse-analysis-session.py`：
     - 公开 4 个子命令 `init / web-start / web-stop / status`；
     - 固定状态机 `WORKSPACE_READY → ENV_READY → BROWSER_READY → FINGERPRINT_READY → MONITORING → STOPPED`，
       写入 `会话状态.json`，越级或 session_id 不一致直接 `SessionError`；
     - `init` 第一时间幂等创建 `{slug}-crawler-reverse/`、4 个标准中文子目录（含 `01-目标画像/录制/会话-XXX/`）、
       《分析计划.md》和 `会话状态.json`；`05-案例沉淀.md` 必须等阶段 5.5 `PASS` 才生成；
     - `web-start` 内部按 OS 自动探测 Chrome 候选路径，必要时启动 task-owned 独立 profile 浏览器
       （`--remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=...`），
       然后跑 `audit_browser_fingerprint`；
     - 浏览器指纹报告分 `阻断 / 警告 / 不可本地证明` 三档：
       - **阻断**：`navigator.webdriver=true`、HeadlessChrome、UA 与 CDP 主版本矛盾、宿主 OS 与 `navigator.platform` 明显矛盾、关键 API 缺失；
       - **警告**：语言/locale 不一致、时区异常、屏幕/viewport 不合理、plugins/mimeTypes=0、Canvas 不稳定、WebGL 软件渲染；
       - **不可本地证明**：公网 IP/代理、TLS/JA3/JA4、服务端行为画像（必须保留 `unknown`）；
     - 串联 `popup-handler.cleanup_all()` → `user_action_recorder.start_recording()` → `start_js_monitor()`
       （注入 fetch/XHR/WebSocket 包覆 + console/error/unhandledrejection + 性能记录补采）→ 等用户操作 → `web-stop`
       flush 监听器 + 生成 `步骤证据索引.json`（按时间窗 1000ms 关联操作/HAR/JS 三份证据）；
     - 停止时**不关闭**任何外部资源——浏览器、context、page、tab 全部保留供用户继续检查。
  2. **JS 监控最小可用**（仅覆盖 4 类高价值通道）：
     - `<script>` URL、fetch/XHR/WebSocket、console.warn/error、`window.error`/`unhandledrejection`；
     - **不上**全局函数 Hook，**不保存整份源码**；每条事件 1000 字符上限、单次 flush 200 条、整体 5MB 上限；
     - 明确声明 ready 时间点之前已加载的脚本**只能拿 URL**（浏览器限制，**不是工具能力短板**）。
  3. **`user-action-recorder.py` 强化脱敏**（保持 3 个公开函数签名）：
     - DOM 层按 `type=password` / id / name / autocomplete / aria-label / placeholder 命中敏感词 → 直接 `***REDACTED***`；
     - HAR 层对 `Authorization` / `Cookie` / `Set-Cookie` / `X-CSRF-Token` 等 Header 与 form-urlencoded / JSON 敏感键统一脱敏；
     - 中文注释覆盖原 Playwright fallback / DrissionPage 段。
  4. **配套测试** `tests/reverse-analysis-session-verify.py`：9 类断言（slug + 工作区幂等、状态机越级、浏览器候选矩阵、指纹判定分级、证据关联、录制器脱敏、JS 监控脚本关键逻辑、中文注释、flush 上限）；接入 `tests/plugin-verify.sh` 第 7.5 段。
  5. **规范收敛**：
     - 《爬虫分析规范》§3.0.2 模式选择：Web 任务**不再先问 4 选 1**，直接由 `web-start` 收 B 模式；
     - 《爬虫工具与抓包规范》§2.1 接管语法对照表：删除"指纹伪装：DrissionPage 内置"，改为
       "**无内置反指纹**（DrissionPage 仍泄露 navigator.webdriver；重度反指纹需 Playwright + rebrowser / puppeteer-real-browser）"；
     - 《爬虫工具与抓包规范》§7.2 工具对照表：新增 `reverse-analysis-session.py` 行 + 末尾对应关系扩展到 4 行；
     - 《爬虫工具与抓包规范》新增 §8.6 JS 运行时持续监控 + §8.7 浏览器环境与指纹一致性审计；
     - 《爬虫Web逆向规范》头部声明 v2.19.0 起手式入口；
     - `mcpowers-spec-index` 第 1 段新增"逆向工作区与 Web 协作会话编排"查表行。
  6. **技能收敛**：
     - `skills/mcpowers/SKILL.md` 强制分流表追加"中文分析目录 / 工作区第一时间创建"等触发词；
     - `skills/mcpowers-crawler-reverse/SKILL.md` 公共前置合同新增 §0 第一时间建工作区 + 铁律 12/13 + 3 条 v2.19.0 反模式 + `资源所有权铁律` 重新声明；
     - `skills/mcpowers-reverse-web/SKILL.md` 编排表第 2 步改为 `reverse-analysis-session.py web-start` 唯一入口、§1.5 协作模式 B 描述改为"强制默认入口"、反模式新增 2 条 v2.19.0 项。
  7. **物理门禁**：`scripts/check-readme-sync.sh` 新增第 15 段，校验：必备文件 2 项 / 反模式残留检测（"DrissionPage 内置"必须从所有可见文件删除）/ crawler-reverse 第一动作声明 / reverse-web web-start 唯一入口 / 工具册 §8.6/§8.7 必含 / B 模式默认声明 / Web 册 v2.19.0 标注；现有 14 段全部不动。
  8. **CLAUDE.md + README.md**：本段历史教训 + README.md v2.19.0 节。
  9. **中文注释强制**：新增/修改 Python 区域的所有 docstring / 注释 / 提示语必须中文；ASCII 分隔线 `# ---` 显式豁免；测试脚本会扫 `^#\s*[\x00-\x7f]+$` 整行注释并断言必须含中文字符。
  10. **版本号三处一致**：`plugin.json` / `marketplace.json` 顶层 / `marketplace.json.plugins[0]` 全部 `2.18.2 → 2.19.0`。
  11. **历史教训可见性**：所有 v2.18.x 的真实接管链路 / Duck-type bug 修复**继续保留**作为前置，但 v2.19.0 显式声明这些修复不证明"指纹绝对真实"——反指纹是另一条对抗线，**禁止**把自动化通过率描述成反指纹。

- **关键决策（YAGNI 守边界）**：
  - ❌ **不**为 Chrome 150+ / 反指纹引入新工具脚本（`chrome_starter.py` / `rebrowser_helper.py`）——`web-start` 内部已经处理 OS 探测 + 参数拼装，工具化违反 KISS；
  - ❌ **不**为 JS 监控引入独立 `js_monitor.py`——它是 `reverse-analysis-session.py` 的子职责，按 §3.5 单一职责与 recorder / popup-handler 严格分工；
  - ❌ **不**为指纹检查引入外部 IP/TLS 服务（公网查询 API 风险 + YAGNI），unknown 状态必须显式标注；
  - ❌ **不**改 6 个 App/小程序专项的工具栈——它们继承统一入口 §0 / §1.3 公共合同即可；
  - ❌ **不**改 `popup-handler.py` 的 8 类弹窗字典（v2.18.2 已补齐 notification）；
  - ✅ **保留** v2.18.x 的 DrissionPage 接管语法 + bb-browser 可选增强 + Playwright fallback；
  - ✅ **保留** v2.17.0 的类式封装 + 零前置参数 + quick_test + 中文文件名；
  - ✅ **保留** 外部资源所有权铁律（用户 browser/context/page/tab 永不可关）。

- **关键风险与未实测项**：
  - **真实接管链路 v2.19.0 仍未跑**：本次只完成自测（9 类断言 + `tests/plugin-verify.sh` 第 7.5 段），
    `web-start` 在 Chrome 150+ + DrissionPage 接管模式下的真实端到端验证需要下次真实场景
    中由用户手动驱动；自检脚本明确**不**冒充实测通过。
  - **JS 监控基于页面 JS 包覆**：对某些 SRI + CSP 严格的页面，`page.run_js(JS_MONITOR_SCRIPT)`
    可能被拒绝注入；监控会失败但**不会**影响 popup-handler / recorder 主链路，AI 必须读
    `会话状态.json` 的 `fingerprint_status` 字段而非"我以为启动了"做判断。
  - **指纹审计 ≠ 反指纹**：本工具只能判断字段一致性与明显伪造；服务端行为画像、公网 IP、TLS
    指纹全部 `unknown`——AI 严禁把"本地 JS 检查通过"等同于"指纹真实"。
  - **公开状态机可能让 AI 误以为可以调用同一命令两次**：`web-start` 第二次调用会被状态机
    拒绝（已有 MONITORING 时 init 失败），AI 必须先 `web-stop` 才能再次启动。

- **铁律新增**：
  - `mcpowers-crawler-reverse/SKILL.md` 铁律 12/13 强制 `init → web-start → web-stop` + 指纹门禁；
  - 资源所有权铁律（铁律 6）从原"参考 §1.3 引用"改为本技能"重新声明"——AI 在 SKILL.md
    局部 Read 时不必再跨文件跳转。
- **版本策略**：用户可见新流程（init / web-start / web-stop）+ 新工具 + 指纹审计 + JS 监控 +
  录制器脱敏 + 中文注释 = minor bump `2.18.2 → 2.19.0`。
- **同步面**：本次横跨 **12 类文件**：
  - 1 新工具：`reverse-analysis-session.py`（~700 行，全部中文注释/docstring）；
  - 1 新测试：`tests/reverse-analysis-session-verify.py`；
  - 1 测试增强：`tests/plugin-verify.sh` 第 7.5 段调用新测试；
  - 1 校验强化：`scripts/check-readme-sync.sh` 第 15 段（约 50 行）；
  - 1 脚本加固：`user-action-recorder.py`（DOM/HAR/Body 脱敏 + 注释中文化，约 100 行新增）；
  - 3 SKILL.md：`mcpowers` / `mcpowers-crawler-reverse` / `mcpowers-reverse-web`；
  - 4 规范：《爬虫分析规范》/《爬虫工具与抓包规范》/《爬虫Web逆向规范》/ `mcpowers-spec-index`；
  - 2 顶层维护：`CLAUDE.md`（本段历史教训）/ `README.md`（v2.19.0 节）；
  - 3 版本文件：`plugin.json` + `marketplace.json`（顶层 + `plugins[0]`，三处一致）。

### 历史教训（v2.20.0 项目独立端口）

- **v2.20.0**：v2.19.0 把逆向起手式收敛为 `init → web-start → web-stop` 单状态机后，真实多任务并行场景暴露新的体系缺口：
  - **缺口 A（端口硬编码冲突）**：所有项目共享 `9222`，并行启动第二个 `web-start` 直接 `bind: address already in use`，用户必须手动 `--port` 才跑得通；与"AI 全自动接管"承诺相悖。
  - **缺口 B（端口与工作区未绑定）**：端口逻辑只在 CLI 默认值 9222 中隐含，《会话状态.json》只记录 `state / session_id / target / slug`，跨进程无法自动恢复端口；`web-stop` 后再 `web-start` 需要重新 `--port`，破坏了 `init` 的幂等性。
  - **缺口 C（DrissionPage `set_local_port(0)` 兼容性未确认）**：直接传 0 是否让 DrissionPage 自动探测 OS ephemeral 端口**未在所有 OS 上验证**，YAGNI 守边界，禁止在 v2.20.0 假设 DrissionPage 接管一定能 bind 0；改用纯 socket 层探测后再传给 DrissionPage。

- **关键修复**（8 类文件改动）：
  1. **新增 `pick_free_port(preferred, max_attempts=100) -> int`**（`reverse-analysis-session.py`）：
     - 优先级 1：`socket.bind(('127.0.0.1', 0))` → 拿 OS ephemeral 端口，立即关闭由调用方抢占；
     - 优先级 2：bind 0 失败 → 端口池 fallback `9222..9300`（`PORT_POOL_START / PORT_POOL_END` 常量）；
     - 超过 `max_attempts=100` 次仍冲突 → `SessionError("建议 --port 指定空闲端口")`；
     - SRP 单函数，`tests/reverse-analysis-session-verify.py` 第 10 类断言覆盖 6 个分支。
  2. **新增 `resolve_port(workspace, explicit_port)`**：三级优先级 `CLI explicit > JSON chrome_port > 重新分配`，
     `web-start` 统一通过此函数取端口，禁止调用方直接 `args.port`。
  3. **`init` 阶段决定端口并写入《会话状态.json》**：
     - `ensure_analysis_workspace` 末尾调用 `pick_free_port()` + `_write_state(..., chrome_port=port)`；
     - `web-start` 通过 `resolve_port` 读 JSON 中的端口，多项目并行互不冲突。
  4. **CLI 默认值语义改 None**：
     - `start_parser.add_argument("--port", default=None, ...)`；
     - `probe_cdp(port: int | None = None)` / `detect_host_environment(port: int | None = None)`；
     - None 触发"读 JSON → 缺失则 SessionError"。
  5. **`run_web_session` 状态机在 ENV_READY / BROWSER_READY 阶段写 `chrome_port` 字段**：
     确保 `web-stop` / `status` / 跨进程 web-start 都能读到一致端口。
  6. **规范文档占位符化**：
     - 《爬虫工具与抓包规范》§2.1 / §3.4 / §3.5 / §3.5.1 / §3.6 / §3.7 / §3.8 / §3.9 + **§3.7.1 新增端口独立分配 SOP** +
       §7.2 工具对照表 `reverse-analysis-session.py` 行扩展；
     - 《爬虫分析规范》§3.0.6 SOP 提炼 + §3.2 L2 坑；
     - 2 个 SKILL.md（L1 自检清单 + 接管预检 SOP）。
  7. **物理门禁 §16**：`scripts/check-readme-sync.sh` 新增第 16 段校验：
     `pick_free_port` 函数存在 / `PORT_POOL_START/END` 常量 / `chrome_port` 字段写入 /
     `probe_cdp` / `start_parser --port` 默认 None / 文档占位符 `<port>` 出现 /
     反向校验硬编码 `set_local_port(9222)` 必须为 0 处（保留反例/历史/端口池常量说明）；
     测试脚本同步新增第 10 类断言。
  8. **CLAUDE.md + README.md + 3 版本文件**：本段历史教训 + README.md v2.20.0 节 +
     `plugin.json` / `marketplace.json` 三处 `2.19.0 → 2.20.0`。

- **关键决策（YAGNI 守边界）**：
  - ❌ **不**拆出独立 `chrome-starter.py` / `port-manager.py` —— 端口是 `reverse-analysis-session.py`
    的子职责，按 §3.5 单一职责保持在原文件内；
  - ❌ **不**把端口池写成配置文件 —— `9222..9300` 是硬编码常量，足够覆盖 79 个项目并行场景；
  - ❌ **不**改 DrissionPage `set_local_port` 行为 —— 通过 `reverse-analysis-session.py` 在外部探测端口后传入，
    完全绕过 DrissionPage 0 端口兼容性未确认风险；
  - ❌ **不**改 `popup-handler.py` / `user-action-recorder.py` —— 它们不直接接触 CDP 端口；
  - ✅ **保留** v2.19.0 的 `_write_state` extra 字段机制 —— `chrome_port` 作为 schema 字段直接复用，
    不引入独立持久化层（DRY）；
  - ✅ **保留** 外部资源所有权铁律 + `_resource_document` 端口透传（仅把 `args.port` 改为本地变量 `port`）。

- **关键风险与未实测项**：
  - **真实并行场景 v2.20.0 仍未跑**：本次只完成自测（10 类断言 + `tests/plugin-verify.sh` 第 7.5 段 +
    `check-readme-sync.sh` §16 物理门禁），真实两个 `web-start` 并行 Chrome 互不冲突需要下次真实场景中由用户手动驱动；自检脚本明确**不**
    冒充实测通过。
  - **bind 0 在 Windows / macOS / Linux 全平台兼容**：CPython `socket.bind(('127.0.0.1', 0))`
    是 POSIX/Winsock 通用行为，理论上全平台支持；但若未来发现某些受限容器（如 Docker 默认网络）
    bind 0 失败，端口池 fallback 自动接管。
  - **端口冲突的语义边界**：bind 0 成功 ≠ 后续 `chrome.exe --remote-debugging-port=port` 一定成功，
    Chrome 启动与 OS socket 释放之间存在 ~1s TIME_WAIT；`pick_free_port` 立即关闭 socket 后
    Chrome 抢占同一端口的极小概率失败留给 Chrome 启动阶段兜底（当前 `launch_debug_browser`
    15s 探测循环自然消化）。

- **铁律新增**：
  - `mcpowers-crawler-reverse/SKILL.md` 铁律 14（v2.20.0）：端口必须由 `reverse-analysis-session.py init`
    自动分配，禁止全局共享 9222；
  - 端口与工作区一一对应，《会话状态.json》`chrome_port` 字段是唯一可信源。

- **版本策略**：minor bump `2.19.0 → 2.20.0`——新增端口独立能力 + 文档占位符化 + 物理门禁，
  用户可见行为变化（多项目可并行 + init 决定端口），符合 minor bump 语义。

- **同步面**：本次横跨 **8 类文件**：
  - 1 工具增强：`reverse-analysis-session.py`（新增 `pick_free_port` + `resolve_port` + `import socket` + 默认值 None 化，约 90 行新增 + 8 行修改）；
  - 1 测试增强：`tests/reverse-analysis-session-verify.py` 新增第 10 类断言（约 50 行）；
  - 1 校验强化：`scripts/check-readme-sync.sh` 新增第 16 段 + §14 `set_local_port(9222)` 校验改 `<port>` 占位符；
  - 4 规范：《爬虫工具与抓包规范》/《爬虫分析规范》 + 占位符 + 新增 §3.7.1；
  - 2 SKILL.md：`mcpowers-crawler-reverse` / `mcpowers-reverse-web` L1 自检清单 + 接管预检 SOP；
  - 2 顶层维护：`CLAUDE.md`（本段历史教训）/ `README.md`（v2.20.0 节）；
  - 3 版本文件：`plugin.json` + `marketplace.json`（顶层 + `plugins[0]`，三处 `2.19.0 → 2.20.0`）。

### 历史教训（v2.16.0 抓包失败 7 层诊断 + cURL 快速帮助）

- **v2.16.0**：真实用户复盘（2026-07）发现两个体系缺口——
  - **缺口 A**：抓包失败不是单点原因，而是 7 个相互叠加的坑。最关键的 3 个是：(1) Playwright/DrissionPage 默认只 attach 到顶层 page Target，SPA 内部 fetch 走了 worker/iframe 副 target → `Network.requestWillBeSent` 根本不发到主 session；(2) Chrome 150 起新增 `--remote-allow-origins` Origin 校验 → 任何非浏览器/扩展来源的 WebSocket 直连 9222 都会被 403 Forbidden；(3) AI 自己 `Target.createTarget` 拉起了新 tab，但最终在 attach 时挑中了自己创建的那个 tab（EAF22CC9AD995855B401），而不是用户 Chrome 自己的结果页 tab（4252F91C4CC929918E03），所以一直收不到 POST。
  - **缺口 B**：用户提供 cURL 时缺少快速帮助 SOP——cURL 是已知接口最高价值告知形式，但 §3.0.1 模式 C 只说"用户告知接口 → 直接录入"，没有 cURL 12 项快速帮助清单和 cURL → 代码转换 SOP。
- **关键修复**：
  - **A**：新增《爬虫工具与抓包规范》§3.9 漏抓诊断 7 层决策树 + §3.9.2 切换模式前 6 问自检（强门禁）；§3.7 Chrome 启动命令加 Chrome 150+ `--remote-allow-origins=*` 必传警告；§3.5/§3.6 新增"禁止 `Target.createTarget`"反模式；§1.1 加 HTTPS 解密验证清单（L4）；§1.1.1 新增抓包过滤器反向风险与请求类型可见性表（L5/L6）。
  - **B**：新增《爬虫分析规范》§3.0.7 cURL 12 项快速帮助清单（直接获得 6 项 + 快速验证 4 项 + 工具化增益 2 项 + 不包含 4 项）+ §3.0.8 cURL → 代码转换 SOP 提示；§3.0.1 模式 C 扩展支持 cURL 输入；§3.0.3 切换触发条件新增"用户贴 cURL"行。
  - **实战案例**：attach 真实 page target（4252F91C4CC929918E03）+ 不驱动表单 + 让用户手动点一次触发 POST → 1 秒内抓到 200 响应——Chrome 150+ 时代协作模式 B 已成为强校验表单场景的默认入口（§3.0.6）。
- **关键决策**：cURL 优化是**分析能力扩展**而非**新工具脚本**——❌ **不**引入独立 `curl_parser.py` 工具（YAGNI 守边界，避免 `DEFAULT_CURL_PARSER` 常量、模块 docstring、check-readme-sync 校验项等同步开销）；✅ AI 用 `python -c` + `curlconverter` 库在线转换（除非未来 ≥ 3 个不同项目都需要稳定 cURL 解析，再升级为独立工具）。
- **铁律新增**：`mcpowers-crawler-reverse/SKILL.md` 第 11 条铁律——"抓不到 ≠ 不存在"；`mcpowers-reverse-web/SKILL.md` 反模式节新增 3 条；§3.0 末尾反模式新增 5 条。
- **校验强化**：`scripts/check-readme-sync.sh` §10 增加 3 个 v2.16.0 字符串校验（`Chrome 150+` / `§3.9` / `§3.0.7`），确保后续修改不会误删新门禁。
- **版本策略**：新增用户可见能力（漏抓 7 层决策树 + cURL 快速帮助 + cURL → 代码 SOP）+ 跨多文件改动 + 强化阶段 2 强门禁 = minor bump `2.15.0 → 2.16.0`。
- **同步面**：本次横跨 11 个文件改动——2 主规范（爬虫工具与抓包规范 / 爬虫分析规范）+ 2 技能 SKILL.md（crawler-reverse / reverse-web）+ 2 工具脚本注释更新（popup-handler.py / user-action-recorder.py）+ 1 校验脚本（check-readme-sync.sh）+ 2 顶层维护文档（CLAUDE.md / README.md）+ 2 版本文件（plugin.json / marketplace.json）。**未**新增 `curl_parser.py` 独立工具脚本（YAGNI 守住）。

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

- **精准路由**：单入口路由器（`skills/mcpowers/`）+ 扁平化技能目录（31 个可路由技能），按意图关键词精准分流
- **方法复用**：TDD / Review / Plan / Brainstorm 等方法层技能被场景层按需编排
- **按需加载**：通过 `mcpowers-spec-index` 查表按需 Read 规范文件，避免爆上下文
- **铁律双约束**：软约束靠技能描述（`铁律` 段落 + `## 反模式（禁止）` ❌ 清单），硬约束靠 Claude Code hooks 物理阻断
- **资产零损耗**：31 个技术规范原地保留，路径不重组、不重命名
- **完全独立**：不依赖任何外部技能，Git 操作由 4 个 `mcpowers-git-*` 技能自包含
- **零安装脚本**：依赖 Claude Code 插件系统管理安装/卸载/升级，仓库零维护成本
