---
name: mcpowers
description: "mcpowers 内部路由器（不直接面向用户触发，仅 L1 索引）。收到用户输入立即按强制分流表路由（feat/bugfix/refactor/optimize/deploy/requirement-change/init/git-*/brainstorm/plan/execute/tdd/code-review/subagent/prd/autoTest/api-contract/install-basics-skills/crawler-reverse/reverse-web/reverse-app/reverse-android/reverse-ios/reverse-flutter/reverse-hybrid/reverse-miniprogram/extract/min-module/sdk-design），禁止先调用本 skill 完整正文再判断。会话产物生成/接口候选排序/模块封装种子/目标接口候选→crawler-reverse。文档膨胀/治理顶层文档/历史教训归档/CHANGELOG 同步→进入维护模式（CLAUDE.md §6 维护指南）。完整路由表（32 行骨架）见「强制分流表」段；各技能 description 是 L1 语义匹配主依据。"
---

# mcpowers 路由器

> **核心思想**：单次对话只加载当前场景需要的技能，不预加载全部规范。
> 借鉴 superpowers 的 `using-superpowers` bootstrap 模式。

---

> 完整规范见 `mcpowers-shared/docs/AI操作规范.md`（按需 Read）。

---

## 1. 强制分流表（命中即调，禁止二次判断）

> **硬规则**：表中关键词命中**必须立即调**对应技能，**禁止**先调本 skill 思考一遍再路由。
> 多关键词同时命中时按表底"多意图裁决"段优先级处理。
> **完整自然语言变体**见每个技能自己的 `description`（L1 索引，本表只是路由表的"骨架"）。

根据用户意图关键词，路由到对应技能：

| 用户意图（关键词，骨架版） | 路由到 | 技能类型 | 详情见 |
|:--------------------------|:-------|:---------|:-------|
| 加 / 新增 / 做一个 / 实现 / 写个 / create / add feature / implement / feat | `mcpowers-feat` | 场景层 | `mcpowers-feat/SKILL.md` description |
| bug / 报错 / 不生效 / 异常 / 失败 / 崩了 / 挂了 / 闪退 / debug / fix / exception / 修一下 / 修个 bug | `mcpowers-bugfix` | 场景层 | `mcpowers-bugfix/SKILL.md` description |
| 需求改了 / 调整逻辑 / 改字段 / 改流程 / 调整业务规则 / change requirement | `mcpowers-requirement-change` | 场景层 | `mcpowers-requirement-change/SKILL.md` description |
| 重构 / 抽离 / 拆分 / 太乱 / 抽象 / 整理代码 / refactor / clean up | `mcpowers-refactor` | 场景层 | `mcpowers-refactor/SKILL.md` description |
| 慢 / 卡 / 性能 / 优化 / 查询慢 / 提速 / performance / optimize / perf | `mcpowers-optimize` | 场景层 | `mcpowers-optimize/SKILL.md` description |
| 部署 / 上线 / 发布 / 构建 / deploy / release / 推到生产 / 打 tag 发布 | `mcpowers-deploy` | 场景层 | `mcpowers-deploy/SKILL.md` description |
| 初始化 / 新项目 / 脚手架 / 搭建 / 从零开始 / init / bootstrap / scaffold | `mcpowers-init` | 场景层 | `mcpowers-init/SKILL.md` description |
| commit / 提交 / git commit / 提交一下 | `mcpowers-git-commit` | 场景层（Git） | `mcpowers-git-commit/SKILL.md` description |
| worktree / 分支隔离 / 并行工作区 / git worktree | `mcpowers-git-worktree` | 场景层（Git） | `mcpowers-git-worktree/SKILL.md` description |
| 回滚 / rollback / 撤销 / 恢复 / revert / reset / 回退 | `mcpowers-git-rollback` | 场景层（Git） | `mcpowers-git-rollback/SKILL.md` description |
| 清理分支 / 删除分支 / 整理分支 / clean branches / delete branch | `mcpowers-git-cleanBranches` | 场景层（Git） | `mcpowers-git-cleanBranches/SKILL.md` description |
| 写需求 / 写 PRD / 整理需求 / MRD / BRD / spec | `mcpowers-prd` | 方法层 | `mcpowers-prd/SKILL.md` description |
| 任务拆解 / 列计划 / 排期 / 规划 / plan / planning | `mcpowers-plan` | 方法层 | `mcpowers-plan/SKILL.md` description |
| 按计划执行 / 实施计划 / 开始执行 / execute / kick off / go | `mcpowers-execute` | 方法层 | `mcpowers-execute/SKILL.md` description |
| 审查 / 审一下 / review / 自审 / CR / PR review | `mcpowers-code-review` | 方法层 | `mcpowers-code-review/SKILL.md` description |
| TDD / 测试驱动 / 先写测试 / 红绿循环 / test first | `mcpowers-tdd` | 方法层 | `mcpowers-tdd/SKILL.md` description |
| 需求不清 / 想法模糊 / 不知道怎么开始 / brainstorm | `mcpowers-brainstorm` | 方法层 | `mcpowers-brainstorm/SKILL.md` description |
| 并行 / 多 agent / subagent / 复杂任务 / fan-out | `mcpowers-subagent` | 方法层 | `mcpowers-subagent/SKILL.md` description |
| 自动化测试 / 跑测试出报告 / bug 等级分类 / 哪一端的问题 / 自动化回归 / e2e / auto test / 跑 pytest / 跑 Playwright / 跑 DrissionPage / 跑 Selenium / 跑 Cypress | `mcpowers-autoTest` | 场景层 | `mcpowers-autoTest/SKILL.md` description |
| 前后端联调 / 接口对接 / API文档 / 自动生成接口规范 / 接口契约 / swagger / openapi / 接口文档怎么自动生成 / 前端怎么拿到接口类型 | `mcpowers-api-contract` | 场景层 | `mcpowers-api-contract/SKILL.md` description |
| 装基础技能 / 一键装基础 / 装上所有基础 / 装基础技能 / 装全部基础技能 / 全局安装基础技能 / npx skills add | `mcpowers-install-basics-skills` | 场景层 | `mcpowers-install-basics-skills/SKILL.md` description |
| 爬虫逆向 / 接口分析 / 抓包分析 / 加密参数还原 / 逆向工程 / RPC 逆向 / 纯协议 / 半自动化 / 纯自动化 / 一次性报文 / token 复用 / 并发稳定性 / 模块真实可用 / 目标类型不明 / 用户操作 + AI 抓包 / 用户操作 + AI 持续监控 / Web 接管用户 Chrome / 第一动作建目录 / 中文分析目录 / 工作区第一时间创建 | `mcpowers-crawler-reverse` | 场景层（统一入口） | `mcpowers-crawler-reverse/SKILL.md` description |
| 网站逆向 / Web JS 反混淆 / 浏览器抓包 / CDP 接管 / WASM / bb-browser | `mcpowers-reverse-web` | 场景层（专项） | `mcpowers-reverse-web/SKILL.md` description |
| APP 逆向但平台或运行时未知 / 先识别 App 技术栈 | `mcpowers-reverse-app` | 场景层（二级入口） | `mcpowers-reverse-app/SKILL.md` description |
| Android 逆向 / 安卓 / APK / AAB / Kotlin / Java / JNI / jadx / frida hook / LSPosed | `mcpowers-reverse-android` | 场景层（专项） | `mcpowers-reverse-android/SKILL.md` description |
| iOS 逆向 / 苹果 App / IPA / Mach-O / Swift / Objective-C / LLDB | `mcpowers-reverse-ios` | 场景层（专项） | `mcpowers-reverse-ios/SKILL.md` description |
| Flutter 逆向 / Dart AOT / libapp.so / App.framework / Platform Channel | `mcpowers-reverse-flutter` | 场景层（专项） | `mcpowers-reverse-flutter/SKILL.md` description |
| 混合 App 逆向 / uni-app / React Native / Cordova / Capacitor / WebView / JSBridge / Hermes | `mcpowers-reverse-hybrid` | 场景层（专项） | `mcpowers-reverse-hybrid/SKILL.md` description |
| 小程序逆向 / 小游戏 / 微信小程序 / 支付宝小程序 / 抖音小程序 / 百度小程序 / wxapkg | `mcpowers-reverse-miniprogram` | 场景层（专项） | `mcpowers-reverse-miniprogram/SKILL.md` description |
| 抽离公共模块 / 抽离通用能力 / 提取可复用组件 / 拆出独立库 / 爬虫逆向层剥离 / 抽成公共库 / 做成可调用脚本 / 模块化调用 / extract module / reusable library | `mcpowers-extract` | 场景层 | `mcpowers-extract/SKILL.md` description |
| 最小模块化 / 通用模块 / 零业务自包含 / 复制即用 / 跨项目可搬运 / 自包含四件套 / min-module / standalone module / self-contained | `mcpowers-min-module` | 场景层 | `mcpowers-min-module/SKILL.md` description |
| SDK 设计 / 封装领域 API / 业务封装库 / 客户端 SDK / 接口封装库 / SDK design / API wrapper / client library / health check / upstream vs client error | `mcpowers-sdk-design` | 场景层 | `mcpowers-sdk-design/SKILL.md` description |

---

## 2. 路由执行规则

### 2.1 触发顺序
1. **先识别意图** → 查路由表
2. **命中场景层** → 调对应场景技能（场景技能内部会按需调方法层技能）
3. **未命中** → 进入兜底流程

### 2.2 兜底流程（无明确意图时）
1. 提示可用技能清单（场景层 + 方法层）
2. 默认走 `mcpowers-brainstorm` 澄清需求
3. 澄清后再路由到对应场景

### 2.3 多意图时
- 拆分为多个任务，依次执行
- 第一个任务优先（用户后续可追加）

### 2.4 多意图裁决规则

当用户输入命中多个场景层技能时，按以下顺序裁决：

**优先级矩阵**（数字越小越优先）：

| 优先级 | 类别 | 说明 |
|:-------|:-----|:-----|
| 1 | 危险修复类 | `mcpowers-git-rollback`（回滚）压倒一切 |
| 2 | 元操作类 | `mcpowers-git-*` 4 个（commit/worktree/cleanBranches/rollback） |
| 3 | 修 bug 类 | `mcpowers-bugfix` 优先于 `mcpowers-feat` |
| 4 | 新增类 | `mcpowers-feat` > `mcpowers-refactor` > `mcpowers-optimize` |
| 5 | 部署 / 需求变更 | `mcpowers-deploy`、`mcpowers-requirement-change` |
| 6 | 初始化 | `mcpowers-init`（只在空仓库或新会话触发） |
| 7 | 方法层 | 由场景层按需编排，单独触发需用户明确指令 |

**冲突矩阵**（典型组合的裁决）：

| 用户输入 | 命中技能 | 裁决 |
|:---------|:---------|:-----|
| "修了 bug 后 commit" | bugfix + git-commit | 先 bugfix（Step 1-4），再 git-commit |
| "重构代码并加测试" | refactor + tdd | tdd 先补测试（铁律），再 refactor |
| "优化数据库查询并部署" | optimize + deploy | optimize 先，deploy 在用户确认后 |
| "初始化项目并 commit" | init + git-commit | init 完成，git-commit 收尾 |
| "改个字段后 commit" | requirement-change + git-commit | requirement-change 先，commit 收尾 |
| "部署出问题回滚" | deploy + rollback | rollback 优先（紧急修复类） |

**灰色地带处理**：
- 逆向关键词同时命中统一入口和平台专项 → **已明确的平台/运行时优先**；仅“App 逆向”但平台未知时走 `mcpowers-reverse-app`；载体也未知时走 `mcpowers-crawler-reverse`
- 逆向专项直接命中后只读取统一入口的公共前置/收尾合同，禁止再次调用统一入口分流，避免循环路由
- 用户说"加个功能顺便 commit" → 视为单一任务，`mcpowers-feat` 在 Step 8 自动调 `mcpowers-git-commit`，不拆
- 用户说"我也不知道要做什么" → 直接进 `mcpowers-brainstorm`，不查路由表
- 命中 ≥ 3 个意图 → 中断并调 AskUserQuestion，让用户选择先做哪个
- 关键词同时命中"重构"和"加功能" → 默认 `mcpowers-refactor`（行为不变优先），如行为变化则切 `mcpowers-feat`
- 关键词"抽离/拆分"同时命中 `refactor` 和 `extract` → 看**产物落点**：整理后**留在原项目**（原地改结构）→ `mcpowers-refactor`；抽成**独立可复用库/可调用脚本/跨项目沉淀**→ `mcpowers-extract`

---

## 3. 技能清单（按需 Read）

### 3.1 场景层（Layer 1）—— 用户输入直接命中
- `skills/mcpowers-feat/SKILL.md`
- `skills/mcpowers-bugfix/SKILL.md`
- `skills/mcpowers-refactor/SKILL.md`
- `skills/mcpowers-optimize/SKILL.md`
- `skills/mcpowers-deploy/SKILL.md`
- `skills/mcpowers-requirement-change/SKILL.md`
- `skills/mcpowers-init/SKILL.md`
- `skills/mcpowers-git-commit/SKILL.md`
- `skills/mcpowers-git-worktree/SKILL.md`
- `skills/mcpowers-git-rollback/SKILL.md`
- `skills/mcpowers-git-cleanBranches/SKILL.md`
- `skills/mcpowers-autoTest/SKILL.md`
- `skills/mcpowers-api-contract/SKILL.md`（v2.2.0 新增）
- `skills/mcpowers-install-basics-skills/SKILL.md`（v2.5.0 新增）
- `skills/mcpowers-crawler-reverse/SKILL.md`（v2.7.0 新增，v2.13.0 转为统一入口）
- `skills/mcpowers-reverse-web/SKILL.md`（v2.13.0 新增）
- `skills/mcpowers-reverse-app/SKILL.md`（v2.13.0 新增，App 二级入口）
- `skills/mcpowers-reverse-android/SKILL.md`（v2.13.0 新增）
- `skills/mcpowers-reverse-ios/SKILL.md`（v2.13.0 新增）
- `skills/mcpowers-reverse-flutter/SKILL.md`（v2.13.0 新增）
- `skills/mcpowers-reverse-hybrid/SKILL.md`（v2.13.0 新增）
- `skills/mcpowers-reverse-miniprogram/SKILL.md`（v2.13.0 新增）
- `skills/mcpowers-extract/SKILL.md`（v2.8.0 新增）
- `skills/mcpowers-min-module/SKILL.md`（v2.28.0 新增）
- `skills/mcpowers-sdk-design/SKILL.md`（v2.28.0 新增）

### 3.2 方法层（Layer 2）—— 被编排，也可单独触发
- `skills/mcpowers-brainstorm/SKILL.md`
- `skills/mcpowers-prd/SKILL.md`
- `skills/mcpowers-plan/SKILL.md`
- `skills/mcpowers-execute/SKILL.md`
- `skills/mcpowers-tdd/SKILL.md`
- `skills/mcpowers-code-review/SKILL.md`
- `skills/mcpowers-subagent/SKILL.md`

### 3.3 规范层（Layer 3）—— 资产库，按需 Read
- **入口**：`skills/mcpowers-shared/SKILL.md`（规范库入口 skill）
- **导航**：`skills/mcpowers-shared/mcpowers-spec-index/SKILL.md`（查"做什么 → 读哪个规范"）
- **规范文件**：`skills/mcpowers-shared/docs/技术规范/*.md`（31 个文件，原地保留；v2.6.0 新增 `日志规范.md`；v2.14.0 爬虫拆分为 7 册）

---

## 4. 独立运行

mcpowers 体系**完全独立**，不依赖任何外部技能：

- ✅ **Git 操作**：由 `mcpowers-git-*` 4 个自有技能处理（commit / worktree / rollback / cleanBranches）
- ✅ **规范文件**：`mcpowers-shared/docs/...` 路径不变
- ✅ **旧 `mcpowers-workflow` 已删除**：原 2142 行单体已拆解为路由器 + 场景/方法技能

只需安装 `skills/mcpowers/`（路由器）+ `skills/mcpowers-*`（32 个可路由技能）+ `skills/mcpowers-shared/`（规范库）三个层级即可完整使用。

---

**使用方式**：本路由器会在每次对话自动加载。AI 收到用户输入后，先查路由表命中场景技能，再由场景技能按需 Read 规范文件。不要一开始就 Read 所有规范（会爆上下文）。

---

## 5. 硬约束完整覆盖（4 个事件组 / 9 个脚本）

铁律从"软提示"升级为"硬约束"由以下 hooks 实现（详见 `hooks/README.md`）：

| 钩子 | 时机 | 对应铁律 | 退出码 |
|:-----|:-----|:---------|:-------|
| `SessionStart/startup` | 启动时 | 7 条必做 + 6 条禁止（铁律全文注入，v2.27.0+ 含 Python import 位置红线） | 0（注入） |
| `PreToolUse/Bash` | Bash 前 | 阻断 `rm -rf /` 等危险命令 | 2 = 阻断 / 0 = 放行 |
| `PreToolUse/Write` | Write 前 | 改前确认；接口相关文件变更时提示同步 API 文档（保护核心 4 目录） | 2 = 阻断 / 0 = 放行 |
| `PreToolUse/Write\|Edit\|MultiEdit` | 写/编辑前 | v2.26.0+ 重复函数检测（防过度抽象铁律）+ v2.27.0+ Python 局部 import 拦截（import 位置铁律；AST 检测，Write 视为覆盖、Edit/MultiEdit 仅 diff 新增违规）+ v2.27.4+ 规范 frontmatter 双字段强制声明（stability + last_breaking_change） | 2 = 命中 / 0 = 放行 |
| `PostToolUse/Write\|Edit\|MultiEdit` | 写完后 | 改完即 commit 提醒 | 0（仅提醒） |

**核心 4 目录保护**（PreToolUse/Write 范围）：`skills/mcpowers/`、`skills/mcpowers-shared/`、`hooks/`、`.claude-plugin/`——修改这些目录的 Write 调用会被阻断，触发 Claude Code CLI 的 confirm UI。

**无需手动配置**：v2.0 插件市场模式下，hooks 由 Claude Code 框架在调用前自动展开 `${CLAUDE_PLUGIN_ROOT}` 占位符定位脚本（**非环境变量**），跨平台零适配。本地开发模式解析为 `marketplaces/mcpowers`，GitHub 模式解析为 `cache/mcpowers/mcpowers/{version}/`，详见 `代码规范.md §最高铁律 · mcpowers 注入路径稳定性`。

---

## 6. mcpowers 自身维护（开发者模式）

> ⚠️ **当用户要修改 mcpowers 自身（不是用 mcpowers 改用户项目）时，本路由器识别"维护意图"并路由到对应流程。**

### 6.1 维护意图识别

用户说以下关键词时，进入"维护模式"——不调外部技能，直接读 `README.md` 的"## 维护指南"段执行：

| 维护意图（关键词） | 路由到 | 详见 README 场景 |
|:-------------------|:-------|:-----------------|
| 加/新增/写 规范、规范文件、spec | 维护模式场景 2 | 新增规范文件 |
| 删/移除 规范、规范文件 | 维护模式场景 3 | 删除规范文件 |
| 改/更新/补充 规范内容 | 维护模式场景 1 | 修改规范文件 |
| 加/新增/写 技能、场景 | 维护模式场景 4 | 新增场景技能 |
| 加/新增/写 hook、钩子 | 维护模式场景 5 | 新增 hook |
| 加/新增/写技能、场景（含 API契约场景技能） | 维护模式场景 4 | 新增场景技能 |
| 升级/git pull/更新版本 | 维护模式场景 6 | 升级流程 |
| 改铁律/改措辞/改禁止 | 维护模式场景 7 | 铁律双源同步 |
| 跑测试/校验/检查 | 直接执行 `bash tests/plugin-verify.sh && bash scripts/check-readme-sync.sh` | 自动化保障清单 |

### 6.2 维护模式默认流程

每次进入维护模式：

1. **先 Read** `README.md` 的"## 维护指南"段（已包含 7 个场景的完整步骤）
2. **按场景的 5 步操作**逐步执行
3. **改完必跑** `bash tests/plugin-verify.sh && bash scripts/check-readme-sync.sh`
4. **commit** 前再看一眼本节 6.3 的铁律

### 6.3 维护铁律

- ❌ **不**直接修改 `${CLAUDE_PLUGIN_ROOT}` 解析路径下的安装副本（插件系统会覆盖；本地开发模式是 `~/.claude/plugins/marketplaces/mcpowers/`，GitHub 模式是 `~/.claude/plugins/cache/mcpowers/mcpowers/{version}/`，**只读**，所有改动必须在仓库源目录进行）
- ❌ **不**跳过"自动化保障清单"里的 2 个脚本（commit 前必跑）
- ❌ **不**漏改 spec-index 查表（新增/删除规范时必查 `skills/mcpowers-shared/mcpowers-spec-index/SKILL.md`）
- ✅ **必**同步更新 frontmatter 的 `last_updated` 字段
- ✅ **必**保持铁律双源一致（先改 `mcpowers-shared/docs/AI操作规范.md` 再改 `hooks/session-start.sh`）
- ✅ **必**改完即 commit（沿用项目铁律第 3 条）
