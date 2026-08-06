# CHANGELOG

> 用户视角的版本变更历史。详细复盘见 [`docs/历史教训.md`](docs/历史教训.md)。
>
> 模板：每个版本 3–8 条 4 段式条目（新增 / 修复 / 调整 / 风险）。
> 维护规则：每次 release 追加到顶部 `[Unreleased]` 下方；不再修改历史版本。

## [Unreleased]

- 待发布

## v2.27.5 - 2026-08-06

### Breaking Changes

- 无。仅减少重复函数 Hook 对 `main()` 入口惯例的误报，不改变其他同名函数检测行为。

- **修复**：`hooks/check_duplicate_function.py` 豁免 Python 模块入口惯例 `main()`，避免独立脚本因共享入口命名而被误判为重复实现。
- **调整**：重复函数 Hook 提示改为准确指向 Claude Code confirm UI，不再暗示检测器自身提供 Y/N 交互。
- **风险**：仅减少入口函数误报；其他公共函数仍按原规则检测。插件版本号 2.27.4 → 2.27.5。

## v2.27.4 - 2026-08-05

### Breaking Changes

- 无。3 条新铁律均为新增约束层（运行时版本访问白名单 / 规范稳定性分级 / CHANGELOG 强制破坏声明），不改动已有行为。
- v2.27.3 注入物版本号写死禁令同样不破坏：v2.27.4 在其基础上增补运行时例外条款，明确"运行时访问历史版本"合法，与原禁令互补。

- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §最高铁律·mcpowers 注入路径稳定性 增「运行时版本访问白名单（v2.27.4+ 全栈适用）」——明确区分"注入物禁硬编码版本号"（v2.27.3+）与"AI 运行时访问历史版本"（v2.27.4+）是两条铁律不冲突；3 种合法访问方式：①AI 主动 `ls ~/.claude/plugins/cache/mcpowers/mcpowers/` 发现用户已装旧版本后 `Read` 读该版本规范 ②项目根存在 `.mcpowers-version: v{major}.{minor}.{patch}` 标记时默认读该版本 ③用户显式"按 v{major}.{minor}.{patch} 规范写"。
- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §最高铁律·mcpowers 注入路径稳定性 增「CHANGELOG 强制破坏声明段（v2.27.4+ 全栈适用）」——每次发布 `CHANGELOG.md` **必须**含 `### Breaking Changes` 段（哪怕标"无"），作为用户升级兼容性的唯一权威索引；mcpowers 仓库自身禁止"minor bump + 破坏性变更"——破坏性变更必须 bump major。
- **新增**：31 份规范 frontmatter 全部增 `stability: stable|evolving|deprecated` + `last_breaking_change: v{major}.{minor}.{patch}` 字段——按 §代码规范.md 稳定性分级铁律 AI 读规范后必读这 2 个字段决定行为（stable 假设跨 minor 兼容 / evolving 升级时主动查 CHANGELOG Breaking Changes / deprecated 不写新代码）；**stability 元数据禁止写回用户项目 CLAUDE.md / 注入物**。
- **新增**：[`AI操作规范.md`](skills/mcpowers-shared/docs/AI操作规范.md) Step 1-4.5「检查规范稳定性分级」——AI 读取每个规范后必读 frontmatter 的 stability + last_breaking_change，按 3 档分别采取不同行为；用户的 `.mcpowers-version` 冻结标记**优先于**最新版 stability。
- **新增**：[`mcpowers-code-review/SKILL.md`](skills/mcpowers-code-review/SKILL.md) 增 R9 反模式条目——未声明 stability / last_breaking_change 就改规范 frontmatter 视为 Critical；审查动作清单增第 6 项"v2.27.4+ 规范 stability 自检"。
- **调整**：[`CLAUDE.md`](CLAUDE.md) 顶层铁律指针段增 3 条 v2.27.4 新铁律（运行时版本访问白名单 / 规范稳定性分级 / CHANGELOG 强制破坏声明）+ 补回 v2.27.3 注入物版本号写死禁令指针（v2.27.3 release 时漏写指针）；[`README.md`](README.md) 核心功能表 §2 / §5 同步标注 v2.27.4。
- **风险**：0 行为变更对外；本次纯规范 / 元数据 / 指针层新增；CI 门禁 `bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh` 验证；插件版本号 2.27.3 → 2.27.4。

## v2.27.3 - 2026-08-05

- **修复**：5 份 doc-sync 注入物模板（[`scripts/templates/project-doc-sync-rules.{generic,flask,vue,crawler}.yml`](scripts/templates/) + [`scripts/templates/project-doc-sync-check.sh`](scripts/templates/project-doc-sync-check.sh)）头部 `v2.9.0 L2 项目级纪律（由 mcpowers-doc-sync-install 注入）` 硬编码版本号违反 v2.26.2+ 「mcpowers 注入路径稳定性」铁律——升级时模板内残留旧版本号。统一改为「本文件对应 mcpowers 最新版本的纪律 / 后续访问必须始终读取 mcpowers 最新版本（不写具体版本号，跨升级永久适用）」正向框架。
- **修复**：[`mcpowers-doc-sync-install/SKILL.md`](skills/mcpowers-doc-sync-install/SKILL.md) §阶段 2 注释里的 `~/.claude/plugins/cache/mcpowers/mcpowers/2.26.2/` 硬编码示例路径违反 v2.26.2+ 注入路径稳定性铁律——改为 `${CLAUDE_PLUGIN_ROOT}/scripts/templates/...` 抽象 + 「框架层字符串替换自动展开为 mcpowers 最新版本对应的物理路径」说明。
- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §最高铁律·mcpowers 注入路径稳定性 增「注入物版本号写死禁令（v2.27.3+ · 全栈适用）」5 条强制条款：①禁止硬编码 mcpowers 版本号 ②必须描述为"对应 mcpowers 最新版本" ③禁止以"注入时刻的版本"为说明基准 ④版本演进历史只允许出现在 `.claude-plugin/*.json` / `CHANGELOG.md` / `docs/历史教训.md` ⑤物理兜底：注入脚本以本规范为唯一来源。
- **调整**：[`CLAUDE.md`](CLAUDE.md) 顶层铁律指针段同步标注 v2.27.3 新增的「注入物版本号写死禁令」；`README.md` §维护指南 增 1 行 v2.27.3 修复条目。
- **风险**：0 行为变更对外；本次纯文档级路径字面值修正 + 1 段铁律新增；CI 门禁 20+41 项验证（`bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh`）；插件版本号 2.27.2 → 2.27.3。

## v2.26.2 - 2026-08-04

- **修复**：[`mcpowers-init/SKILL.md`](skills/mcpowers-init/SKILL.md) §5 安装指引——"提示用户安装到 `~/.claude/skills/`" 改为 v2.0+ 唯一安装机制 `Claude Code 插件市场`（`/plugin marketplace add ... && /plugin install ...`）；§5 软链提议改为"**不软链不复制**，AI 按 mcpowers-spec-index 按需 Read"，避免软链指向带版本号 cache 路径、mcpowers 升级后失效；§5 注入的 CLAUDE.md「加载规范」段同步改为"按需 Read，**不**复制不软链"以消除内部矛盾。
- **修复**：[`mcpowers-doc-sync-install/SKILL.md`](skills/mcpowers-doc-sync-install/SKILL.md) §阶段 2 的 `<mcpowers>` 自定义占位符改用 `${CLAUDE_PLUGIN_ROOT}`，AI 在 Claude Code 会话里跑 cp 时框架自动展开；同时改"从环境变量读"措辞为"**Claude Code 框架在工具调用时自动展开的占位符（**非环境变量**）**"，避免与 v2.25.0 最高铁律"禁止使用环境变量"产生语感冲突。
- **修复**：[`开发环境规范.md`](skills/mcpowers-shared/docs/技术规范/开发环境规范.md) §2 给 `${CLAUDE_PLUGIN_ROOT}` 加脚注：说明是框架层字符串替换非环境变量、mcpowers-shared/docs/ 部分是稳定路径仅插件根目录带版本号。
- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 新增「最高铁律 · mcpowers 注入路径稳定性（强制 · 全栈适用 · v2.26.2+）」段——3 类禁行字面值（`cache/mcpowers/mcpowers/{version}/...` / `~/.claude/skills/mcpowers-shared/...` / 自定义占位符如 `<mcpowers>`）+ 3 条配套铁律（不软链、不装旧路径、AI 引用规范只用抽象路径）。
- **风险**：0 行为变更对外；本次纯文档级路径字面值修正 + 1 段铁律新增；CI 门禁 20+41 项验证（`bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh`）；插件版本号 2.26.1 → 2.26.2。

## v2.26.1 - 2026-08-04

- **修复**：[`开发环境规范.md`](skills/mcpowers-shared/docs/技术规范/开发环境规范.md) §2 + [`AI操作规范.md`](skills/mcpowers-shared/docs/AI操作规范.md) 10 处 + [`hooks/session-start.sh`](hooks/session-start.sh) 启动横幅——所有指向 `~/.claude/skills/mcpowers-shared/` 的旧路径改用 `${CLAUDE_PLUGIN_ROOT}` 占位符，与 `hooks/hooks.json` 既有惯例对齐；插件版本号同步 `2.26.0 → 2.26.1`。
- **调整**：[`AI操作规范.md` Step 1-1](skills/mcpowers-shared/docs/AI操作规范.md) 由 `ls ${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/docs/技术规范/*.md` 扫描改为 `Read mcpowers-spec-index.md` 索引（按 CLAUDE.md 既有"按需 Read"协议，bash 中 `${CLAUDE_PLUGIN_ROOT}` 不会被展开、`ls` 实际不可执行，原协议与现实不符）；[`mcpowers-spec-index/SKILL.md`](skills/mcpowers-shared/mcpowers-spec-index/SKILL.md) 删除"安装到 `~/.claude/skills/` 后调整相对路径"的过时提示行（plugin 整体安装机制下该用法不存在）。
- **风险**：0 行为变更对外；本次仅修正路径字面值与一处协议命令演示，不改动技能触发条件、路由表、技能/规范数量。

## v2.26.0 - 2026-08-03

- **新增**：[`日志规范.md §7.3`](skills/mcpowers-shared/docs/技术规范/日志规范.md) 新增「轮转 → 清理 → 压缩时序」——4 阶段强顺序：①轮转产生 `app.log.YYYY-MM-DD` ②保留 N 天原文件（默认 7 天，`keep_recent_uncompressed_days = 7`） ③超过窗口的轮转文件 `.gz` 压缩 ④超过保留期的 `.gz` 文件清理；§7.2 同时新增「免压缩窗口」配置项。
- **新增**：[`Flask后端规范.md §6.3`](skills/mcpowers-shared/docs/技术规范/Flask后端规范.md) `compress_old_logs()` + `purge_old_logs()` 两个工具函数落地免压缩窗口与 `.gz` 清理；`_file_handler()` `use_gzip=False` 由清理函数接管压缩时机；新增 `LOG_KEEP_UNCOMPRESSED` 配置项（默认 7）。
- **新增**：[`爬虫规范.md §12.3`](skills/mcpowers-shared/docs/技术规范/爬虫规范.md) 爬虫项目日志维护强制复用 Flask 的 `compress_old_logs` / `purge_old_logs`，新增 `daily_log_maintenance` 调度示例。
- **新增**：[`代码规范.md §6.1.1`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 新增「复用优先于二次抽象（强制 · 防过度设计）」段——6 条反模式黑名单（R1-R6）+ 3 条 bash 自检命令 + 3 类 wrapper 合理论证场景（参数映射 / 批量调用 / 异常归一）。
- **新增**：`hooks/check_duplicate_function.py` + `hooks/pre-write-check-duplicate.sh`——`PreToolUse(Write|Edit|MultiEdit)` 钩子，检测新增 `def` / `function` / `func` / `fn` 与仓库已有同名函数冲突；命中走 Claude Code confirm UI（exit 2）。同时保护 `skills/mcpowers-shared/` / `skills/mcpowers*/SKILL.md` 等白名单不被自身打扰。
- **新增**：[`mcpowers-feat/SKILL.md`](skills/mcpowers-feat/SKILL.md) 触发即执行 10 步中插入「## 2.5 已有资产扫描」强制步骤——PR 描述必填「已有资产扫描结果」清单（含 SDK / common / utils / shared 同名扫描），3 条 `rg` 自检命令；不填不允许进入第 3 步。
- **新增**：[`mcpowers-code-review/SKILL.md`](skills/mcpowers-code-review/SKILL.md) 「## 反模式（禁止）」段新增「过度抽象 / 重复代码 R1-R7」Critical 阻塞表 + 30 秒复用扫描 Quick-Check 3 条 `rg` 命令。
- **调整**：[`hooks/hooks.json`](hooks/hooks.json) `PreToolUse` 新增 `Edit|MultiEdit` 匹配器，注册 `pre-write-check-duplicate.sh`（之前仅在 `Write` 上）。
- **风险**：0 行为变更对外；日志免压缩窗口仅对启用新配置的项目生效，老项目沿用立即 gzip；钩子失败兜底放行（`try/except` 捕获所有异常 → exit 0），不会阻断正常 Write/Edit。

## v2.25.0 - 2026-08-03

- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 新增「最高铁律 · 本技能禁止使用环境变量（强制 · 全栈适用）」段——仓库所有 .py / .sh / .js / .ts 源文件以及应用本规范的所有项目代码**一律禁止**读环境变量；Python 禁 `os.environ.*` / `os.getenv`，Shell 禁 `$XXX` 从外部环境读，JS/TS 运行时禁 `process.env.*` / `dotenv.config()`；唯一允许例外 `hooks.json` 的 `${CLAUDE_PLUGIN_ROOT}` 与 docker-compose `environment:` 字段。
- **新增**：[`Flask后端规范.md §4.1`](skills/mcpowers-shared/docs/技术规范/Flask后端规范.md) 改为「指向代码规范」短引用段，明确栈级落地走 `Config.get()` / `Config.items()`。
- **新增**：[`CLAUDE.md`](CLAUDE.md) 「## 规范体系」段插入「本技能禁止使用环境变量」基线段（强约束措辞）。
- **新增**：[`README.md`](README.md) 第 14 行表格 + 第 228 行段落同步 v2.25.0 摘要。
- **修复**：[`reverse-analysis-session.py:578`](skills/mcpowers-crawler-reverse/scripts/reverse-analysis-session.py) `browser_candidates()` 函数删除 `dict(os.environ)` 探测 Windows 浏览器路径的违规源——改为 `environment` 参数作为可选测试注入点（外部测试 `tests/reverse-analysis-session-verify.py` 仍可传 `windows_env` 模拟），函数内部硬编码 `C:/Program Files` / `C:/Program Files (x86)` + `pathlib.Path.home() / "AppData" / "Local"` 作默认 root，业务调用方无需传任何环境探测参数。
- **风险**：0 行为变更对外；OS 浏览器路径仅覆盖 Windows 默认安装位置，非标安装用户仍走 `_find_windows_browser_from_registry()` 注册表探测；本仓库 `import os` 在 `os.replace()` 文件重命名场景保留（不算违规）。

## v2.21.3 - 2026-07-31

- **调整**：铁律 #6 加资源所有权分类（v2.21.3）——`external/user-owned`（不可关闭）vs `task-owned`（finally 可关闭）；明确 `web_monitor_template.py` 属于 task-owned，finally 段 `browser.quit()` 不再与铁律 #6 冲突。
- **调整**：《爬虫工具与抓包规范》§8 章节标题从「用户操作录制与重放脚本」改为「Web 浏览器协作会话工具链」——章节实际承载范围（录制 + JS 监控 + 指纹审计 + 派生产物）已超出原标题语义。
- **新增**：《爬虫工具与抓包规范》§8.8.8「完整 body 获取路径」——临时方案走 §3.0.1 模式 C + §3.0.7 cURL 12 项清单（不受 1024 字符预览限制）；长期方案 `reverse-analysis-session.py --save-full-body`（v2.22+ 待办）。
- **调整**：`mcpowers-reverse-android/ios/flutter/hybrid` 4 个 App 专项 SKILL.md 加 v2.21.3 权威源声明——8 项证据交接合同以 `mcpowers-crawler-reverse/SKILL.md` §4 为唯一权威源，本节不再重复定义。
- **风险**：0 行为变更，纯文档同步；CI 门禁 20+41 项全过。

## v2.21.2 - 2026-07-31

- **新增**：`skills/mcpowers-crawler-reverse/scripts/web_monitor_template.py`——标准化 Web 浏览器监控模板（开箱即用，内置 7 类"配置正确性"防御 + run_js JS 异常保护）。供 Web 逆向 / 抓包分析 / 浏览器行为取证场景直接 `from web_monitor_template import monitor` 调用，避免 AI 从零写 DrissionPage 配置时踩坑。
- **修复**：`tab.cookies()` / `tab.run_js(...)` 缺 try/except 保护——目标页 JS 执行失败时整个 monitor 会抛致命异常（自验证暴露的真实 bug）。修复后 `monitor()` 在异常路径下也能正常返回 `result.json`。
- **调整**：《爬虫工具与抓包规范》§7.2 工具对照表新增 `web_monitor_template.py` 行（明确边界：不替代 `reverse-analysis-session.py web-start` 的工作区 + 协作会话 + 派生产物状态机）。
- **风险**：本工具关闭自身创建的浏览器（finally 段），不接管用户已有 Chrome；如需接管外部 Chrome 请使用专门的协作会话编排工具。

## v2.21.1 - 2026-07-29

- **调整**：治理 `CLAUDE.md` / `README.md` 顶层文档膨胀——`CLAUDE.md` 由 622 行收敛至 ~200 行（删除 13 个历史教训段），`README.md` 由 908 行收敛至 ~600 行（删除 7 个版本发布段）。
- **新增**：[`docs/历史教训.md`](docs/历史教训.md) 只读归档，承载 v2.0.3 → 当前版本完整复盘。
- **新增**：[`CHANGELOG.md`](CHANGELOG.md) 用户视角版本变更历史（顶层文档 4 段式）。
- **调整**：CI 门禁新增 3 段——`scripts/check-readme-sync.sh` §18 根文档结构门禁（禁止 `### 历史教训（v` / 禁止 `### vX.Y.Z`）、§19 根文档尺寸门禁（CLAUDE.md ≤ 350 行 / 35,000 字符，README.md ≤ 650 行 / 50,000 字符）、§20 单一权威源门禁（关键短语在根文档出现即告警）。
- **调整**：`.github/workflows/doc-sync.yml` DOCS_CHANGED 判定扩展为 4 文件（CLAUDE.md / README.md / CHANGELOG.md / docs/历史教训.md）至少一改。

## v2.21.0 - 2026-07-28

- **新增**：`session-artifacts-generator.py`——Web `web-stop` 自动派生产物（`02-接口分析/目标接口候选.md` + 响应样本 envelope + v2.17.0 类式 `client.py` / `quick_test.py` 种子）。
- **新增**：《爬虫分析规范》§3.11 App 录制选型调研（三方案对照矩阵 + v2.22+ 选型门槛）。
- **调整**：CI 门禁 `check-readme-sync.sh` §17 + `plugin-verify.sh` §7.6 同步新增。
- **风险**：真实并行场景 + 真实接管链路仍未跑；HAR body_preview 1024 字符上限；自动 lifecycle 分类是线索；真实 top10 排名仍需人工确认。

## v2.20.0 - 2026-07-27

- **新增**：`reverse-analysis-session.py` 端口独立分配（`pick_free_port` + 端口池 9222..9300 fallback + 100 次上限 SessionError）。
- **调整**：多项目可并行 web-start 互不冲突；端口与工作区一一对应，《会话状态.json》`chrome_port` 字段是唯一可信源。
- **调整**：《爬虫工具与抓包规范》§3.7.1 新增端口独立分配 SOP；`set_local_port(9222)` 全部占位符化为 `<port>`。
- **风险**：DrissionPage `set_local_port(0)` 兼容性未确认（绕开方式：外部 socket 探测后传入）。

## v2.19.0 - 2026-07-26

- **新增**：`reverse-analysis-session.py`——`init / web-start / web-stop / status` 单状态机强制起手式（WORKSPACE_READY → ENV_READY → BROWSER_READY → FINGERPRINT_READY → MONITORING → STOPPED）。
- **新增**：浏览器指纹一致性审计（`audit_browser_fingerprint`，分阻断 / 警告 / 不可本地证明 三档）。
- **新增**：JS 运行时持续监控（4 类高价值通道：script URL / fetch / XHR / WebSocket / console.error / unhandledrejection / 性能补采）。
- **调整**：`user-action-recorder.py` 强化脱敏（DOM / HAR / Body 三层）。
- **调整**：Python 注释 / docstring / 提示语强制中文。
- **风险**：真实接管链路 v2.19.0 仍未跑；JS 监控对 SRI + CSP 严格页面可能注入失败。

## v2.18.2 - 2026-07-25

- **修复**：`user-action-recorder.py:506` duck-type 致命 bug（`callable(page.listen)` 误判 → 接管模式完全不可用）。
- **修复**：`user-action-recorder.py:421` `page.actions.wheel` API 误用（DrissionPage 无此方法，应为 `page.actions.scroll`）。
- **修复**：`popup-handler.py` POPUP_SELECTORS 漏配 notification（补 2 行 selector）。
- **调整**：`replay_actions` 防御性读取 + `stop_recording` flush HAR buffer。
- **铁律**：新工具 / 新接管语法必须 1 次接管链路口令实测通过才能上线。

## v2.18.1 - 2026-07-25

- **调整**：《爬虫工具与抓包规范》§2.1/§7.2 DrissionPage 描述精准化（删除"内置反检测"，改为"接管便利性 + 国内站点适配"）。
- **新增**：4 个实测参考链接（[DrissionPage 官网](https://www.drissionpage.cn/browser_control/connect_browser/) + Chrome 136 修复方案 + Chrome 启动参数 + 真实接管链路留痕）。
- **调整**：Playwright fallback 路径从 3 类扩展到 5 类（新增重度反指纹检测 + 复杂行为分析风控）。
- **铁律**：未上网确认的事实禁止写进主表 description。

## v2.18.0 - 2026-07-24

- **调整**：浏览器自动化默认从 Playwright 切换为 **DrissionPage**（接管便利性 + 代码量少 30~50% + 国内站点适配）。
- **新增**：《爬虫工具与抓包规范》§2.1 接管语法对照表（`connect_over_cdp` → `ChromiumPage(addr_or_opts=ChromiumOptions().set_local_port(9222))` 等）。
- **新增**：《爬虫工具与抓包规范》§3.5/§3.6/§3.9 漏抓 7 层 DrissionPage 重新映射。
- **调整**：`popup-handler.py` / `user-action-recorder.py` 全文件 DrissionPage 适配（duck-type `hasattr(page, "listen")` 自动分支）。
- **风险**：Chrome 150+ `--remote-allow-origins=*` 必传；Chrome 136+ 独立 user data dir 必传。

## v2.17.0 - 2026-07-22

- **调整**：模块产物封装形式标准化——`functions.py` → `client.py` 类式封装 + `do_request` / `parse_response` 分离 + 零前置参数业务方法 + `quick_test.py` 必备。
- **调整**：分析文件命名强制中文（`01-目标画像/` / `02-接口分析/` / `03-逆向攻坚/` / `04-模块封装/` / `接口清单.md` / `验收报告.md` 等）。
- **新增**：《爬虫分析规范》§9.4.6 全段 6 小节（类式 / SRP / 零前置参数 / quick_test / 中文命名 / extract 同步）。
- **风险**：自动生成种子**不**作为阶段 5.5 PASS 替代，必须人工验证。

## v2.16.0 - 2026-07-20

- **新增**：《爬虫工具与抓包规范》§3.9 漏抓诊断 7 层决策树 + §3.9.2 切换模式前 6 问自检。
- **新增**：《爬虫分析规范》§3.0.7 cURL 12 项快速帮助清单 + §3.0.8 cURL → 代码转换 SOP 提示。
- **调整**：Chrome 150+ `--remote-allow-origins=*` 必传警告。
- **铁律**：`mcpowers-crawler-reverse/SKILL.md` 铁律 11——"抓不到 ≠ 不存在"。

## v2.15.0 - 2026-07-18

- **新增**：`user-action-recorder.py` 协作模式 B 工具（录制 + 重放，~5h 最小可用版）。
- **调整**：与 `popup-handler.py` 严格分工——popup-handler 主动清理；recorder 被动监听。
- **铁律**：全程遵守 §1.3 浏览器所有权——禁止 `browser.close()` / `context.close()` / `page.close()`。

## v2.14.0 - 2026-07-15

- **新增**：《爬虫分析规范》拆分 7 册 + 1 配套（`爬虫工具与抓包规范.md` + 6 个平台专项）。
- **调整**：`§1.3 外部接管资源不可关闭` 主册为唯一权威源；各册按需引用，不重复定义。
- **风险**：跨册改动面大（25 文件同步），CI 物理门禁强制要求 CLAUDE.md/README.md 同 PR 变化。

## v2.13.0 - 2026-07-12

- **调整**：逆向 7 专项拆分（统一入口 + Web + App 二级入口 + Android / iOS / Flutter / Hybrid / 小程序）。
- **新增**：`浏览器所有权铁律`——通过 CDP/WebView/daemon 接管的 browser/context/page/tab 一律视为外部所有，永不可关闭。
- **调整**：`check-readme-sync.sh` 增至 12 类检查（新增 reverse 拓扑 / 公共合同 / 外部资源所有权断言）。

## v2.12.0 - 2026-07-10

- **新增**：SKILL.md 阶段 5.5 真实可用性验收（业务语义 + ≥ 2 组输入 / 合计 ≥ 5 次 + 跨 session + 原报文重放 + 动态参数重生成 + 有界并发 2 → 5）。
- **新增**：生命周期 7 分类（`reusable` / `per-request` / `single-use-token` / `session-bound` / `time-bound` / `challenge-bound` / `unknown`）。
- **调整**：统一产出 `verification-report.md`，只有 `PASS` 才能进入阶段 6/7。
- **风险**：并发仅做小规模可用性验证，不做压力测试；遇 429 / 验证码 / 账号提示立即停止。

## v2.11.1 - 2026-07-08

- **新增**：bb-browser 完整实操链路（§2.5.5.0 安装与 MCP 配置 + §2.5.5.1 daemon + Playwright 共享 Chrome CDP + §2.0.5.1 adapter 失败判定与结果合并）。
- **铁律**：第三方 CLI 集成必须包含完整实操链路（安装 → 启动 → 验证 → 失败处理 → 结果合并）。

## v2.10.0 - 2026-07-05

- **新增**：`bb-browser`（[epiral/bb-browser](https://github.com/epiral/bb-browser)）第三方 CLI / MCP server 集成。
- **铁律**：第三方 CLI 必须是可选依赖；缺 bb-browser 时 v2.9.5 Chrome CDP + Playwright + popup-handler.py 原链路必须完全可用。

## v2.9.5 - 2026-07-02

- **新增**：`mcpowers-crawler-reverse` §2.7 弹窗检测（8 类弹窗字典）+ §3.0 协作模式 + §3.4.5 置信度。
- **新增**：`popup-handler.py`（与字典库对应）。
- **铁律**：单技能能力强化 ≠ 单文件改动；6 类文件同步是底线。

## v2.6.0 - 2026-06-25

- **新增**：`日志规范.md`（7 类日志 + JSON 字段 + 大内容默认截断 + 脱敏黑名单）。
- **调整**：`mcpowers-init` 注入日志基础设施（`utils/loggings.py` + `utils/request_log.py` + `log/` 目录）。

## v2.0.3 → v2.0.4

- **修复**：description 多行 `|` 字面量块导致 3 个文件超 1024c 被截断（code-review / brainstorm / bugfix）。
- **调整**：全部改为 4 段式单行紧凑版，L1 description 总预算从 ~9000c 降到 5986c（-34%），0 个文件超 800c。
