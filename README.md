# mcpowers

AI 辅助开发的标准化技能体系。**按场景拆分的轻量级技能组合**，覆盖产品 → 开发 → 测试 → 部署全生命周期。借鉴 superpowers 设计：主入口路由器 + 场景触发 + 规范按需加载。**完全独立运行**，不依赖任何外部技能（含 Git 操作）。

---

## 核心功能

mcpowers 提供 7 大核心能力，让 AI 像资深工程师一样按流程工作：

| # | 功能 | 说明 |
|:-:|:-----|:-----|
| 1 | **🎯 场景化技能路由** | 31 个技能（23 场景 + 8 方法）按用户意图关键词精准分流；逆向任务采用“统一入口 → 平台/运行时专项 → 统一验收”二级路由 |
| 2 | **📋 31 个技术规范**（v2.3.0 接口契约规范 + v2.6.0 `日志规范.md` + v2.14.0 爬虫拆分 7 册 + v2.15.0 协作模式 B 工具化 + v2.16.0 漏抓 7 层诊断 + cURL 快速帮助 + v2.17.0 模块产物封装形式标准化 + v2.18.0 浏览器自动化默认切 DrissionPage） | Flask/Vue/爬虫/API/数据库/缓存/部署/安全/版本管理/健康检查/自动化测试/日志等，按需加载避免爆上下文 |
| 3 | **🗂️ 19 类接口速查表**（v2.3.0 从 13 类扩到 19 类） | list/detail/create/update/delete/batch-delete/update-status/dict/dict-cascader/import/export/template/upload/bind-unbind/submit-task+progress+cancel-task/webhook/stream-sse，AI 写接口前必查（栈无关通用契约） |
| 4 | **🧪 方法论复用** | TDD 强制先写测试、Brainstorm 澄清需求、Plan 任务拆解、Code Review 铁律，被场景层按需编排 |
| 5 | **🛡️ 铁律双约束** | 软约束（技能描述里的 `铁律` + `## 反模式（禁止）` ❌ 清单）+ 硬约束（Claude Code hooks 物理阻断危险命令） |
| 6 | **🪝 4 个事件组 / 5 个 Hook 脚本** | SessionStart 注入铁律、PreToolUse(Bash) 阻断 `rm -rf /`、PreToolUse(Write) 保护核心目录并提示接口文档同步、PostToolUse 提醒提交 |
| 7 | **🔧 完全独立 Git 操作** | 内置 `commit / worktree / rollback / cleanBranches` 4 个 git 技能，无需依赖任何外部技能 |

### 1 句话总结

> **mcpowers = 借鉴 superpowers 方法论的骨架 + 自带 31 个技术规范的肉 + 中文友好的壳**（v2.3.0 接口契约规范 + v2.6.0 日志规范 + v2.14.0 爬虫拆分 7 册 + v2.17.0 模块产物封装形式 + 顶层文档中文 + v2.18.0 浏览器自动化 DrissionPage 全场景默认）
>
> 有规范时强制按规范写（保证代码可读性统一），无规范时退回通用方法论（保证任务能完成）。

---

## 设计理念

mcpowers 的核心理念：**让 AI 像资深工程师一样按流程工作，而不是拿到需求就写代码**。

- **精准路由**：单入口路由器 + 场景/方法分层，按意图关键词精准分流
- **方法复用**：TDD / Review / Plan / Brainstorm 等方法层技能被场景层按需编排
- **按需加载**：通过 `mcpowers-spec-index` 查表按需 Read 规范文件，避免爆上下文
- **铁律双约束**：软约束靠技能描述（`铁律` 段落 + `## 反模式（禁止）` ❌ 清单），硬约束靠 Claude Code hooks 物理阻断
- **编排显式化**：23 个场景技能统一带 `## 编排` 段，写明调谁、何时调、失败时
- **规范元数据化**：31 个核心规范带 YAML frontmatter（title/type/applies_to/priority/version），机器可查
- **骨架增强**：路由器轻量化、SessionStart 注入完整铁律、4 个事件组 / 5 个 Hook 脚本（SessionStart + PreToolUse(Bash/Write) + PostToolUse）、冒烟测试 + 同步校验脚本

---

## 技能结构

```
mcpowers/                              # 仓库根 = 插件根
├── .claude-plugin/                    # 插件市场元数据（Claude Code 插件系统读取）
│   ├── marketplace.json               # 市场清单（对外）
│   └── plugin.json                    # 插件清单（自身）
│
├── hooks/                             # Claude Code hooks 资产（铁律硬约束）
│   ├── hooks.json                     # SessionStart + PreToolUse + PostToolUse 配置
│   ├── README.md                      # Hooks 故障排查文档
│   ├── session-start.sh               # 启动时注入铁律摘要
│   ├── pre-bash-guard.sh              # 阻断 rm -rf / 等危险命令
│   ├── pre-write-confirm.sh           # 保护核心资产不可误删
│   ├── pre-write-confirm-api-hint.sh  # 接口变更时提示同步 API 文档
│   └── post-write-commit-reminder.sh  # 改完即 commit 提醒
│
├── skills/                            # 技能（扁平化：1 路由器 + 31 个可路由技能 + 1 规范库）
│   ├── mcpowers/                      # 主入口路由器（每次对话注入）
│   │
│   │ ── 场景层（23 个，用户输入直接命中）──
│   ├── mcpowers-feat/                 # 加功能
│   ├── mcpowers-bugfix/               # 修 bug
│   ├── mcpowers-refactor/             # 重构
│   ├── mcpowers-optimize/             # 性能优化
│   ├── mcpowers-deploy/               # 部署
│   ├── mcpowers-requirement-change/   # 需求变更
│   ├── mcpowers-init/                 # 项目初始化
│   ├── mcpowers-git-commit/           # 规范化 commit
│   ├── mcpowers-git-worktree/         # worktree 隔离
│   ├── mcpowers-git-rollback/         # 安全回滚
│   ├── mcpowers-git-cleanBranches/    # 清理分支
│   ├── mcpowers-autoTest/             # 自动化测试（v2.1.0 新增；v2.10.0 默认 Python + 项目证据优先选框架）
│   ├── mcpowers-api-contract/         # API 契约/前后端联调（v2.2.0 新增）
│   ├── mcpowers-install-basics-skills/# 全局一键装基础技能（v2.5.0 新增，4 条 npx skills add）
│   ├── mcpowers-crawler-reverse/      # 逆向统一入口（v2.13.0：公共前置合同 + 类型分流 + 公共验收/落地）
│   ├── mcpowers-reverse-web/          # 网站/H5/JS/WASM/CDP/bb-browser 逆向专项（外部浏览器不可关闭）
│   ├── mcpowers-reverse-app/          # App 二级判断入口（Android/iOS/Flutter/Hybrid 指纹分流）
│   ├── mcpowers-reverse-android/      # Android/Kotlin/Java/JNI/DEX/so 逆向专项
│   ├── mcpowers-reverse-ios/          # iOS/Swift/Objective-C/IPA/Mach-O 逆向专项
│   ├── mcpowers-reverse-flutter/      # Flutter/Dart AOT/Platform Channel 逆向专项
│   ├── mcpowers-reverse-hybrid/       # uni-app/RN/Cordova/Capacitor/WebView/JSBridge 专项
│   ├── mcpowers-reverse-miniprogram/  # 微信/支付宝/抖音/百度小程序与小游戏专项
│   ├── mcpowers-extract/              # 模块抽离（v2.8.0 新增，从已有项目抽离通用能力/逆向层为可复用库）
│   │
│   │ ── 方法层（8 个，被场景层调用）──
│   ├── mcpowers-doc-sync-install/     # 项目级 doc-sync 纪律安装（v2.9.0 新增，给已有项目注入校验+hook）
│   ├── mcpowers-brainstorm/           # 澄清需求
│   ├── mcpowers-prd/                  # 写 PRD
│   ├── mcpowers-plan/                 # 任务拆解
│   ├── mcpowers-execute/              # 执行计划
│   ├── mcpowers-tdd/                  # 强制 TDD
│   ├── mcpowers-code-review/          # 代码审查
│   ├── mcpowers-subagent/             # 子代理并行
│   │
│   └── mcpowers-shared/               # 规范资产库（24 技术规范 + 1 产品 + 1 铁律 + 2 模板 + 1 工具 + 2 启动脚本 + 5 API契约资产 v2.2.0；v2.3.0 接口契约规范覆盖通用层；v2.6.0 新增日志规范）
│       ├── SKILL.md                   # 入口（按需加载导航）
│       ├── mcpowers-spec-index/       # 规范导航（查表）
│       ├── scripts/                   # 启动脚本（Windows + POSIX 双版本）
│       │   ├── start_dev.sh           # Linux/macOS 启动
│       │   └── start_dev.ps1          # Windows 启动
│       ├── tools/
│       │   └── export_docs.py         # 文档导出工具
│       └── docs/
│           ├── AI操作规范.md          # 全局铁律
│           ├── 产品设计/
│           │   └── 产品设计规范.md
│           ├── 技术规范/              # 31 个技术规范（v2.3.0 新增接口契约规范；v2.6.0 新增日志规范；v2.14.0 爬虫拆分 7 册）
│           │   ├── 接口契约规范.md     # 🆕 v2.3.0 通用层（栈无关，19 类接口 + 简短 description + 结构化参数/响应）
│           │   ├── API规范.md
│           │   ├── Flask后端规范.md
│           │   ├── Vue前端规范.md
│           │   ├── 爬虫规范.md
│           │   ├── 爬虫分析规范.md        # v2.14.0 主册（公共方法论）
│           │   ├── 爬虫工具与抓包规范.md  # 🆕 v2.14.0 公共配套（抓包/自动化/浏览器运行时/弹窗字典/协议层/bb-browser）
│           │   ├── 爬虫Web逆向规范.md     # 🆕 v2.14.0 ↔ mcpowers-reverse-web
│           │   ├── 爬虫Android逆向规范.md # 🆕 v2.14.0 ↔ mcpowers-reverse-android
│           │   ├── 爬虫IOS逆向规范.md     # 🆕 v2.14.0 ↔ mcpowers-reverse-ios
│           │   ├── 爬虫Flutter逆向规范.md # 🆕 v2.14.0 ↔ mcpowers-reverse-flutter
│           │   ├── 爬虫Hybrid逆向规范.md  # 🆕 v2.14.0 ↔ mcpowers-reverse-hybrid
│           │   ├── 爬虫小程序逆向规范.md   # 🆕 v2.14.0 ↔ mcpowers-reverse-miniprogram
│           │   ├── 代码规范.md
│           │   ├── 数据库规范.md
│           │   ├── 缓存规范.md
│           │   ├── 定时任务规范.md
│           │   ├── 导入导出规范.md
│           │   ├── Git规范.md
│           │   ├── 部署规范.md
│           │   ├── 测试规范.md
│           │   ├── 开发环境规范.md
│           │   ├── 设计规范.md
│           │   ├── 文档编写规范.md
│           │   ├── 代码同步修改规范.md
│           │   ├── 细节记录规范.md
│           │   ├── 安全规范.md
│           │   ├── API版本管理规范.md
│           │   ├── 健康检查规范.md
│           │   ├── 自动化测试规范.md
│           │   └── 日志规范.md        # 🆕 v2.6.0 通用层（栈无关，7 类日志 + JSON 字段 + 大内容默认截断 + 脱敏黑名单）
│           ├── API文档/
│           │   ├── API文档模板.md
│           │   └── swagger_template.md
│           ├── API契约/   # 🆕 v2.2.0（4 份资产 + 复用 API文档 模板 + tools/export_docs.py）
│           │   ├── 集成方案对比.md
│           │   ├── 加密方案对比.md
│           │   ├── 前端对接流程.md
│           │   └── API测试自动生成.md
│           └── 工具参考/
│               └── 交互数据存档.md
│
├── tests/
│   └── plugin-verify.sh               # 插件结构验证（30+ 断言）
│
├── scripts/
│   └── check-readme-sync.sh           # README ↔ 仓库同步校验
│
├── CLAUDE.md
├── README.md
└── .gitignore
```

完整版本历史见 [`CHANGELOG.md`](CHANGELOG.md)；详细复盘见 [`docs/历史教训.md`](docs/历史教训.md)。

---

## 触发条件

`mcpowers` 主入口路由器会在每次对话自动加载，识别意图后路由到对应技能：

| 用户输入 | 路由到 |
|:---------|:-------|
| 加/新增/做一个 功能、页面、接口、模块 | `mcpowers-feat` |
| bug/报错/不生效/异常/失败/修一下 | `mcpowers-bugfix` |
| 重构/抽离/拆分/太乱/抽象 | `mcpowers-refactor` |
| 慢/卡/性能/优化/查询慢 | `mcpowers-optimize` |
| 部署/上线/发布/构建 | `mcpowers-deploy` |
| 需求改了/调整逻辑/加字段/改流程 | `mcpowers-requirement-change` |
| 初始化/新项目/脚手架/搭建 | `mcpowers-init` |
| 写需求/写 PRD/整理需求 | `mcpowers-prd` |
| 任务拆解/列计划/排期 | `mcpowers-plan` |
| 按计划执行/实施计划/开始执行 | `mcpowers-execute` |
| 审查/审一下/review/自审 | `mcpowers-code-review` |
| 写测试/TDD/单测 | `mcpowers-tdd` |
| 不清楚要做什么/需求不清 | `mcpowers-brainstorm` |
| 复杂任务/并行/多代理 | `mcpowers-subagent` |
| 自动化测试/跑测试出报告/bug等级分类/哪一端的问题/自动化回归/e2e/跑 pytest/跑 Playwright/跑 DrissionPage/跑 Selenium/跑 Cypress | `mcpowers-autoTest`（新增自动化默认 Python；先查项目证据，已有套件沿用） |
| 前后端联调/接口对接/API文档/自动生成接口规范/接口契约/swagger/openapi/前端怎么拿到接口类型 | `mcpowers-api-contract`（v2.2.0 新增） |
| 装基础技能/一键装基础/装上所有基础/装全部基础技能/全局安装基础技能/npx skills add | `mcpowers-install-basics-skills`（v2.5.0 新增） |
| 爬虫逆向/接口分析/抓包分析/加密参数还原/RPC逆向/纯协议/半自动化/纯自动化/一次性报文/token复用/并发稳定性/模块真实可用/目标类型不明 | `mcpowers-crawler-reverse`（统一入口，v2.13.0 分层） |
| 网站逆向/Web JS反混淆/浏览器抓包/CDP接管/WASM/bb-browser | `mcpowers-reverse-web` |
| App逆向但平台或运行时未知/识别App技术栈 | `mcpowers-reverse-app`（二级入口） |
| Android逆向/安卓/APK/AAB/Kotlin/Java/JNI/jadx/frida hook/LSPosed | `mcpowers-reverse-android` |
| iOS逆向/苹果App/IPA/Mach-O/Swift/Objective-C/LLDB | `mcpowers-reverse-ios` |
| Flutter逆向/Dart AOT/libapp.so/App.framework/Platform Channel | `mcpowers-reverse-flutter` |
| 混合App逆向/uni-app/React Native/Cordova/Capacitor/WebView/JSBridge/Hermes | `mcpowers-reverse-hybrid` |
| 小程序逆向/小游戏/微信小程序/支付宝小程序/抖音小程序/百度小程序/wxapkg | `mcpowers-reverse-miniprogram` |
| 抽离公共模块/抽离通用能力/提取可复用组件/拆出独立库/爬虫逆向层剥离/抽成公共库/做成可调用脚本/模块化调用 | `mcpowers-extract`（v2.8.0 新增） |
| 装项目级文档同步纪律/给现有项目加 doc-sync/一键安装校验+hook/安装 .doc-sync-rules | `mcpowers-doc-sync-install`（v2.9.0 新增） |
| commit/提交 | `mcpowers-git-commit` |
| worktree/分支隔离/并行工作区 | `mcpowers-git-worktree` |
| 回滚/rollback/撤销/恢复 | `mcpowers-git-rollback` |
| 清理分支/删除分支/整理分支 | `mcpowers-git-cleanBranches` |

---

## 快速安装

### 一键安装（Claude Code 插件市场）

mcpowers v2.0+ 已改造为 [Claude Code 官方插件市场](https://docs.claude.com/en/docs/claude-code/plugins) 格式。**零脚本安装**，由 Claude Code 插件系统管理：

```bash
# 1. 添加市场源（GitHub 公开仓库）
/plugin marketplace add https://github.com/742366981/mcpowers

# 2. 安装插件
/plugin install mcpowers@mcpowers

# 3. 重启 Claude Code
```

**安装内容**（由插件系统自动部署）：
- ✅ 1 个主入口路由器（`mcpowers`）
- ✅ 31 个场景/方法技能（23 场景 + 8 方法）
- ✅ 31 个技术规范（`mcpowers-shared`，v2.6.0 新增日志规范；v2.14.0 爬虫拆分 7 册；v2.15.0 协作模式 B 工具化 `user-action-recorder.py`；v2.16.0 抓包失败 7 层诊断 + cURL 12 项快速帮助；v2.17.0 模块产物封装形式 + 顶层文档中文；v2.18.0 浏览器自动化 DrissionPage 全场景默认 + 漏抓 7 层 DrissionPage 重新映射 + popup-handler / user-action-recorder DrissionPage 适配）
- ✅ 4 个 Hook 事件组 / 5 个 Hook 脚本（自动注册，无需改 `settings.json`）

> **两种触发方式并存**：① **自然语言自动路由**（说「加个功能」自动命中 `mcpowers-feat`）；② **斜杠直接调用**（`/mcpowers-feat`）。

### 升级

**更新由 `.claude-plugin/plugin.json` 的 `version` 字段触发**——version 不变，`Update now` 或重装都不会拉取新版。Claude Code **不会自动**检测 GitHub 新版本。

升级方式（用户视角）：

```bash
# 方式 1：推荐（在 Claude Code 内执行）
/plugin
# → 选 mcpowers → Update now

# 方式 2：完全重装
/plugin uninstall mcpowers@mcpowers
/plugin install mcpowers@mcpowers
```

> 💡 **维护者**：改完代码必须按顺序做完整套，缺一不可：
> 1. **bump version**（`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` 两处同步）
> 2. `bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh` 全绿
> 3. `git commit && git push`
> 4. 用户才能 `Update now` 拉到新版。

### 卸载

```bash
/plugin uninstall mcpowers@mcpowers
# 可选：从市场源中移除
/plugin marketplace remove https://github.com/742366981/mcpowers
```

### 验证安装

1. 重启 Claude Code
2. 直接说"加个用户登录接口"，AI 应自动调 `mcpowers-feat`
3. 输入 `/mcpowers-feat` 也可直接触发

---

## Hooks 行为

mcpowers 通过 `hooks/hooks.json` 声明 4 个 Claude Code Hook 事件组，并调用 5 个脚本，由插件系统自动注册（**无需修改 `settings.json`**），让铁律从"软提示"升级为"硬约束"。

| 钩子 | 触发时机 | 作用 |
|:-----|:---------|:-----|
| `SessionStart` | 每次 Claude Code 启动 | 注入路由器铁律摘要（改前确认 / TDD 先行 / 改完即 commit 等），AI 每轮对话开始就知道 mcpowers 流程 |
| `PreToolUse (Bash)` | 每次执行 Bash 命令前 | 阻断 `rm -rf /`、`git push --force main` 等危险操作 |
| `PreToolUse (Write)` | 每次 Write 文件前 | `pre-write-confirm.sh` 保护核心资产；`pre-write-confirm-api-hint.sh` 在接口相关文件变更时提示同步 API 文档 |
| `PostToolUse (Write/Edit/MultiEdit)` | 每次修改后 | 改完即 commit 提醒（仅在已暂存且工作区干净时触发） |

> Hooks 通过 `${CLAUDE_PLUGIN_ROOT}` 环境变量定位脚本，跨平台零适配（Windows / macOS / Linux 统一）。

### 故障排查与详细说明

见 [`hooks/README.md`](hooks/README.md)：

- Hooks 资产位置和升级机制
- 误伤正常命令时如何调整白名单
- 误伤正常文件写入时如何调整受保护路径

---

## 支持的 AI 工具

mcpowers 走 **Claude Code 插件市场格式**（`.claude-plugin/marketplace.json`），不同 AI 工具的支持情况如下：

| AI 工具 | 支持状态 | 安装方式 | 说明 |
|:--------|:--------:|:---------|:-----|
| **Claude Code** | ✅ **完全支持** | `/plugin install mcpowers@mcpowers` | 路由器 + 31 个可路由技能 + 24 技术规范 + 4 个 Hook 事件组 / 5 个脚本全功能 |
| **Cursor** | 🟡 理论支持 | 在 Cursor 插件市场加载 `.claude-plugin/` | ⚠️ 未实测，Cursor 兼容 Claude Code 插件规范 |
| **Codex CLI** | 🟡 理论支持 | 复制 `skills/` 到 Codex skills 目录 | ⚠️ 未实测，规范 + 技能可读，hooks 需手动配置 |
| **OpenCode** | 🟡 理论支持 | `opencode.json` 引用本仓库 | ⚠️ 未实测，通过 git 引用，自动加载 |
| **GitHub Copilot CLI** | 🟡 理论支持 | `/plugin install` 同 Claude Code | ⚠️ 未实测 |
| **Gemini CLI** | 🟡 理论支持 | 通过插件市场加载 | ⚠️ 未实测 |
| **Claude.ai 网页版** | ⚠️ 部分支持 | 手动复制 `skills/*.md` | 路由器可读，hooks 不可用 |
| 其他 AI 工具 | ⚠️ 规范可用 | 手动复制 `skills/mcpowers-shared/docs/*.md` | 规范是纯 Markdown 通用 |

> **声明**：除 Claude Code 外，其他 AI 工具的支持情况基于其官方文档推测，**未经实测验证**。如发现兼容性问题欢迎提 Issue。

### 工具特定说明

#### Claude Code（主推）

- 完整支持 4 个 Hook 事件组 / 5 个脚本（`SessionStart` + `PreToolUse(Bash/Write)` + `PostToolUse`）
- 路由器自动加载，用户输入自然语言路由到对应技能
- 安装命令（**分两步执行，不要用 `&&` 串联**——`&&` 会让 Claude Code 把 install 部分也拼进 marketplace URL，导致 git clone 失败）：

  ```bash
  /plugin marketplace add https://github.com/742366981/mcpowers
  /plugin install mcpowers@mcpowers
  ```

#### Cursor

- Cursor 已支持 Claude Code 插件格式
- 通过 Cursor 的插件市场加载 `.claude-plugin/marketplace.json`
- 差异：Cursor 用 `~/.cursor/skills/` 而非 `~/.claude/skills/`，路径自动转换

#### Codex CLI / OpenCode / GitHub Copilot CLI

- 复制 `skills/` 目录到对应工具的 skills 根目录
- 例如 Codex：`cp -r skills/ ~/.codex/skills/`
- hooks 需参照各工具文档手动配置（mcpowers 的 hooks 是 Claude Code 特有）

### 规范层（通用）

`mcpowers-shared/docs/技术规范/*.md` 是**纯 Markdown 文档**，可以被任何能读取文件的 AI 工具直接使用——不依赖任何特定 IDE 或插件机制。

---

## 借鉴来源

mcpowers 的设计参考了以下优秀项目：

| 项目 | 借鉴内容 |
|:-----|:---------|
| [**obra/superpowers**](https://github.com/obra/superpowers) | using-superpowers bootstrap 模式、brainstorming / TDD / debugging 铁律、code-review 流程、specs 规范导航思想 |
| [**jnMetaCode/superpowers-zh**](https://github.com/jnMetaCode/superpowers-zh) | 中文社区翻译版，部分技能描述借鉴中文措辞与本土化表达 |

**与 superpowers 一致**：本项目方法论借鉴 superpowers，安装机制也对齐——同样走 Claude Code 插件市场。

---

## 维护指南

mcpowers 的设计目标是**让维护者能低成本演进**：基于 superpowers / superpowers-zh 思想 + 你自己的规范文件。下面是高频维护场景的操作清单。

### 文档同步规则（强制）

凡是新增、删除、重命名或调整技能体系的能力、路由、编排、规范、Hook、目录结构、安装方式或版本号，必须在同一变更中同步检查并更新 `CLAUDE.md` 与 `README.md`。

- 新增场景技能：同步主路由器、技能树、触发条件表、`SCENE_SKILLS`、技能版本和验证结果
- 新增方法技能：同步技能总数、技能树、路由说明和验证结果
- 新增规范或 Hook：同步规范/Hook 清单、对应维护文档和结构校验
- 修改插件版本：同步 `.claude-plugin/plugin.json` 与 `.claude-plugin/marketplace.json`

禁止只修改 `skills/`、`hooks/` 或插件元数据而不检查两份维护文档。纯规范正文修订至少运行同步检查；凡影响用户可见能力或体系结构的修订必须实际更新两份文档。

---

### 场景 1：修改某个规范文件的内容

**步骤**（1 分钟）：

1. 直接编辑 `mcpowers-shared/docs/技术规范/<name>规范.md`
2. 更新文件顶部 frontmatter 的 `last_updated: <今天日期>`
3. 跑 `bash scripts/check-readme-sync.sh` 确认通过

**同步要求**：如果修改影响规范清单、适用范围或用户可见行为，必须同步检查 `CLAUDE.md` 和 README；仅正文措辞或 `last_updated` 变更时，至少运行同步检查。

---

### 场景 2：新增一个规范文件

**步骤**（5 步，约 10 分钟）：

| # | 文件 | 改动 |
|:-:|:-----|:-----|
| 1 | `mcpowers-shared/docs/技术规范/<新规范名>规范.md` | **新建**，顶部插入 frontmatter 模板（见下方） |
| 2 | `mcpowers-shared/mcpowers-spec-index/SKILL.md` 第 12-33 行查表 | **加一行**："任务/文件类型" → "必读规范" |
| 3 | `README.md` 技能结构图的 `mcpowers-shared/docs/技术规范/` 块、`CLAUDE.md` 规范数量 | **各加一处**，保持用户文档和维护规则一致 |
| 4 | 跑 `bash scripts/check-readme-sync.sh` | **必须通过**（不通过 = 漏改了某处） |
| 5 | `git add . && git commit -m "docs(specs): 新增 <X>规范"` | 提交 |

**frontmatter 模板**（必填 6 字段）：

```markdown
---
title: <规范名>
type: tech-spec
applies_to: [<适用栈1>, <适用栈2>]
priority: required   # required / recommended / reference
version: 1.0
last_updated: 2026-07-08
---

# <规范名>

正文...
```

**字段说明**：
- `title`：与文件名（去掉 `.md`）保持一致
- `type`：固定 `tech-spec`（产品类用 `product-spec`，全局规则用 `global-rule`）
- `applies_to`：数组，例 `[Flask后端]` / `[所有]` / `[涉及缓存]` / `[Flask后端, Vue前端]`（多栈组合：规范同时覆盖前后端）
- `priority`：`required` = 必读基线 / `recommended` = 推荐 / `reference` = 参考

---

### 场景 3：删除一个规范文件

**步骤**（5 步反向，约 5 分钟）：

| # | 文件 | 改动 |
|:-:|:-----|:-----|
| 1 | `rm mcpowers-shared/docs/技术规范/<X>规范.md` | 删除文件 |
| 2 | `mcpowers-shared/mcpowers-spec-index/SKILL.md` 查表 | **删一行** |
| 3 | `README.md` 技能结构图、`CLAUDE.md` 规范数量 | **各删一处**，保持用户文档和维护规则一致 |
| 4 | `bash scripts/check-readme-sync.sh` | 必须通过 |
| 5 | 跑 `bash tests/plugin-verify.sh` 确认 ≥31 个规范断言仍通过（v2.14.0 后规范数为 31，阈值已更新；新规范添加到 ≥28 时需要更新 plugin-verify 的断言阈值） |  |

---

### 场景 4：新增一个场景技能

**步骤**（约 15 分钟）：

1. 创建 `skills/mcpowers-<name>/SKILL.md`
2. **复制 mcpowers-feat 的 "## 编排" 模板**（最完整的版本），修改表格内容
3. 在 `skills/mcpowers/SKILL.md` 路由表（## 1 段）**加一行**："触发关键词" → `mcpowers-<name>`
4. `CLAUDE.md` 的核心结构、触发条件和技能分类**同步更新**
5. `README.md` 触发条件表（## 触发条件 段）**加一行**
6. `README.md` 技能结构图的 `skills/` 块**加一行**并更新技能统计
7. 如果是场景层技能，更新 `scripts/check-readme-sync.sh` 的 `SCENE_SKILLS`
8. bump `.claude-plugin/plugin.json`、marketplace 插件条目和顶层市场版本
9. 先跑 `bash scripts/check-readme-sync.sh`，再跑 `bash tests/plugin-verify.sh`

---

### 场景 5：新增一个 Claude Code hook

**步骤**（约 20 分钟）：

1. 创建 `hooks/<hook-name>.sh`，头部加 `#!/usr/bin/env bash`，可执行
2. `hooks/hooks.json` 追加对应事件段（不动现有段）
3. `CLAUDE.md` 和 `README.md` 同步更新 Hook 事件组/脚本清单及维护说明
4. `skills/mcpowers/SKILL.md` "## 5. 硬约束完整覆盖" 表**加一行**（如新增事件组）或补充对应脚本
5. `hooks/README.md` 加一段说明
6. `tests/plugin-verify.sh` 补充脚本存在性或行为断言
7. `bash tests/plugin-verify.sh` 跑过（确认 hooks 资产可被发现）

**hooks.json 模板**（根据事件类型选一种）：

```json
{
  "matcher": "Bash",        // 或 "Write" / "Write|Edit"
  "hooks": [
    {
      "type": "command",
      "command": "bash \"__HOOKS_DIR__/<hook-name>.sh\""
    }
  ]
}
```

---

### 场景 6：升级（仅维护者视角）

**用户视角**（绝大多数安装者）：必须主动 `Update now`（或重装），下次启动 Claude Code 才会加载新版本。详见上方「升级」段。

**维护者视角**（本仓库开发者）：推送上游改动

```bash
# 1. 改完代码 + bump version（详见上方「升级」段）
# 2. 提交并推送到 GitHub
git add -A
git commit -m "..."
git push origin master

# 3. 用户在 Claude Code 内执行 `/plugin` → Update now 才会拉到新版
```

---

### 场景 7：铁律措辞更新

**铁律有 2 处**（**必须保持一致**）：

1. `hooks/session-start.sh` —— SessionStart 启动时输出
2. 路由器 SKILL.md 历史上引用过（提交 `1ad2ac9` 移除：铁律迁移到 SessionStart hook）；权威源始终是 `mcpowers-shared/docs/AI操作规范.md`

**修改步骤**：
1. 先改 `mcpowers-shared/docs/AI操作规范.md`（权威源）
2. 再改 `hooks/session-start.sh` 的对应条目
3. 跑 `bash hooks/session-start.sh` 确认输出正确

---

## 自动化保障清单

| 工具 | 用途 | 跑法 |
|:-----|:-----|:-----|
| `tests/plugin-verify.sh` | 插件结构验证 | `bash tests/plugin-verify.sh`（30+ 断言） |
| `scripts/check-readme-sync.sh` | 校验 README ↔ 实际状态 | `bash scripts/check-readme-sync.sh`（12 类断言：清单、frontmatter、编排、版本、description、数字、引用、逆向拓扑、公共合同、浏览器所有权） |
| `bash hooks/session-start.sh` | 验证铁律输出正确 | `bash hooks/session-start.sh`，看输出是否完整 |
| `.github/workflows/doc-sync.yml` | **CI 物理门禁**（v2.5.2+） | PR 涉及技能体系变化时自动跑，CLAUDE.md/README.md 未同步则红 X |

**建议**：每次 commit 前按以下顺序跑 2 个脚本：先发现文档清单问题，再验证插件结构。

```bash
bash scripts/check-readme-sync.sh && bash tests/plugin-verify.sh
```

### CI 物理门禁说明（v2.5.2+）

`.github/workflows/doc-sync.yml` 把"AI 自觉同步文档"升级为"合并前硬阻止"：

- **触发条件**：PR 涉及 `skills/`、`hooks/`、`.claude-plugin/`、`scripts/`、`tests/`、`skills/mcpowers-shared/docs/` 任意路径变化
- **运行校验**：自动跑 `check-readme-sync.sh`（12 类断言）+ `plugin-verify.sh`（37 类断言）
- **变更联动**：检测到技能体系变更时，要求 `CLAUDE.md` 或 `README.md` 至少有一个变化，否则 PR 标记失败
- **目标**：完全消除"改了技能忘了改文档"的人工遗漏

**示例 PR 红 X 提示**：

```text
❌ 检测到技能体系变更但 CLAUDE.md/README.md 未同步

变更的受保护路径：
skills/<新场景技能>/SKILL.md
skills/mcpowers/SKILL.md

按 CLAUDE.md「文档同步约束（强制）」规则，必须在同一变更中同步更新：
  - CLAUDE.md（维护规则、技能分类、触发映射）
  - README.md（用户功能说明、技能树、触发条件）
```

---

## 维护陷阱（容易踩的坑）

| 坑 | 现象 | 预防 |
|:---|:-----|:-----|
| ① 改了场景技能调用的方法层，忘了同步"## 编排"段 | 调用关系对不上 | 修改方法层时，**grep 反查**：`grep -r "mcpowers-<被改名>" skills/` |
| ② 忘了更新 `last_updated` | 规范过期无感知 | 写个 git pre-commit hook（见下方） |
| ③ frontmatter 字段填错粒度 | 路由不准确 | 严格按 frontmatter 模板填，参考 `mcpowers-spec-index` 查表行 |
| ④ 路由器铁律 vs session-start.sh 双源不一致 | 铁律"精神分裂" | 永远先改 AI操作规范.md（权威源），再同步 hooks |
| ⑤ superpowers 上游升级未同步 | 设计理念漂移 | 定期访问 https://github.com/obra/superpowers 查更新 |

**可选：git pre-commit hook**（自动跑 check-readme-sync）：

```bash
# .git/hooks/pre-commit
#!/usr/bin/env bash
bash scripts/check-readme-sync.sh || {
  echo "✗ README 同步校验失败，请先修复再 commit"
  exit 1
}
```

---

## 仓库地址

git@github.com:742366981/mcpowers.git
