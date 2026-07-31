---
name: mcpowers-crawler-reverse
description: "逆向统一入口 / 目标类型判断 / 抓包与加密还原 / 交付验收 / 会话产物生成 → 触发本技能。口语：帮我看看这个目标怎么逆向、不确定是网站还是App、做成纯协议或自动化、模块必须真的可用、会话停止后自动生成接口候选和模块种子。中英：reverse engineering/target triage/protocol/RPC/lifecycle/usability verification/session artifacts/candidate ranking/module seed。边界：明确网站→mcpowers-reverse-web；未知App→mcpowers-reverse-app；明确Android/iOS/Flutter/Hybrid/小程序→对应专项；已有爬虫修复→mcpowers-bugfix。流程：公共前置合同→专项证据→公共收尾合同。"
---

# mcpowers-crawler-reverse（逆向统一入口）

> **定位**：只负责公共合同、目标分流、证据汇总与真实可用性验收。平台工具链由 `mcpowers-reverse-*` 专项负责。
> **目标**：把陌生目标的逆向结果沉淀为可复用、可验证、可回溯的轻量模块。

---

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-brainstorm` | 方法 | URL/包名/平台/目标动作不明确 | 中断并逐项澄清 |
| 2 | `爬虫分析规范.md` + 命中平台配套规范（Web/Android/iOS/Flutter/Hybrid/小程序/工具与抓包） | 规范 | 必读公共章节与命中平台章节 | 中断，提示加载失败 |
| 3 | `mcpowers-reverse-*` | 场景 | 完成目标类型判断后 | 保留已收集证据并重新判断 |
| 4 | `爬虫规范.md` | 规范 | 阶段 5 轻量封装 | 提示按需加载 |
| 5 | `mcpowers-code-review` | 方法 | 模块封装和验收报告完成 | Critical 必须修复 |
| 6 | `mcpowers-init` / `mcpowers-feat` / `mcpowers-extract` | 场景 | 阶段 7 经用户选择 | 未选择则不跳转 |
| 6.5 | `session-artifacts-generator.py`（v2.21.0 嵌入） | 工具 | Web 任务 `web-stop` 正常收尾自动调用（详见铁律 #15 + 《爬虫工具与抓包规范》§8.8） | 失败隔离：`artifacts_generation.status=failed` + 中文告警，STOPPED 仍写入，浏览器存活 |

**防循环规则**：专项技能直接命中时，只 Read 并执行本技能的「公共前置合同」和「公共收尾合同」，不得再次调用本技能做平台分流。

## 铁律

1. **先侦察后逆向**：能明文构造就不进入加密逆向。
2. **先确认交付形态**：纯协议、半自动化、纯自动化的验收条件不同。
3. **专项只交证据，不宣布可交付**：只有公共阶段 5.5 能给出最终状态。
4. **结果必须实测**：算法至少 3 组样本；模块还需重复、生命周期、跨会话和有界并发证据。
5. **合规优先**：授权、robots.txt、服务条款和法律边界不清时先询问；越界即停。
6. **资源所有权铁律（v2.19.0 重新声明，v2.21.3 加分类边界）——外部接管资源不可关闭**：

   按所有权把浏览器/CDP 资源分成 2 类，关闭权限不同：

   | 类别 | 范围 | 关闭权限 |
   |:-----|:-----|:---------|
   | **external/user-owned** | 用户 Chrome / 用户 context / 已有 page / 已有 tab / 用户 daemon / frida-server / LSPosed | **任何阶段不可 close / kill / stop**——含启动、接管、监控、收尾、异常、回退 |
   | **task-owned** | reverse-analysis-session.py 创建的 Chrome / 临时 CDP 端口 / 调试用 user-data-dir；web_monitor_template.py 一次性 Chromium | finally 段允许 close / quit |

   任何阶段（启动、接管、监控、收尾、异常、回退）都不得 `browser.close()` / `context.close()` /
   关闭既有 page / kill 用户 Chrome / 擅自 stop 外部 daemon；收尾与回退只能
   停止使用/断开客户端；`reverse-analysis-session.py web-stop` 自身也保持
   浏览器存活。
7. **资源所有权必须显式记录**：任务创建的资源写明 owner、创建方式和清理权限；用户 Chrome 中新开的标签页默认保留，仅在用户明确确认后清理。
8. **bb-browser 是可选增强**：不可用时完整回退 DrissionPage（v2.18.0 默认）/ Playwright + popup-handler.py，不得中断主链路。
9. **真实可用才落地**：`验收报告.md` 为 `PASS` 后才能进入阶段 6/7。
10. **RPC 是逆向实现方式，不是最终交付形态**。
11. **抓不到 ≠ 不存在**：阶段 2 抓包失败必须先走《爬虫工具与抓包规范》§3.9
    漏抓 7 层 6 问自检，**禁止**直接把"抓不到"等同于"接口不存在"；cURL 是
    已知接口最高价值告知，§3.0.1 模式 C 必须按 §3.0.7 12 项快速帮助清单
    最大化利用，并按 §3.0.8 SOP 在线转换为 Python 代码实测。
12. **Web 默认进入“用户操作 + AI 持续监控”**（v2.19.0）：拿到目标 URL 后
    第一动作是 `reverse-analysis-session.py web-start`；固定顺序
    `工作区 → 宿主环境与浏览器实现 → 浏览器资源所有权 → 指纹一致性审计 →
    接管/打开 → 弹窗清理 → 启动录制 + JS 监控 → 等用户操作 → web-stop`。
    **禁止**先自由分析 A 模式、绕开指纹门禁、让 AI 反复自动点击。
13. **浏览器指纹只做“一致性审计”，不证明绝对真实**（v2.19.0）：
    `navigator.webdriver=true`、HeadlessChrome、UA 与 CDP 主版本矛盾、宿主 OS
    与 `navigator.platform` 明显矛盾、关键 API 缺失属**阻断项**，命中即拒绝继续；
    警告项（语言/locale、屏幕/viewport、Canvas 抖动、WebGL 软件渲染等）允许
    继续但必须写入 `01-目标画像/浏览器指纹报告.json`；
    公网 IP/代理、TLS/JA3/JA4、服务端行为画像**无法由本地 JS 证明**，必须保留
    `unknown`，**禁止**在工具描述或对用户话术中宣称 DrissionPage "内置反指纹"，
    也不得把"接管便利性 + 国内站点自动化通过率优势"包装成反指纹能力。
14. **v2.20.0**：端口必须由 `reverse-analysis-session.py init` 自动分配，禁止全局共享 9222；端口与工作区一一对应，《会话状态.json》`chrome_port` 字段是唯一可信源。
15. **v2.21.0**：Web `web-stop` 完成证据 flush 和步骤证据索引后，**必须**调用 `session-artifacts-generator.py` 生成接口候选、响应样本和模块封装种子；生成的种子**不得**标记为 `[🎯]` 或 `PASS`，且**不得**覆盖已有人工 `client.py` / `quick_test.py`；派生产物失败不破坏 STOPPED 与外部浏览器存活（v2.19.0 铁律 #6）。

---

## 触发即执行（统一入口 → 专项 → 统一收尾）

## 公共前置合同

### 0. 第一时间创建工作区（v2.19.0 起强制）

> 拿到目标标识（URL / 包名 / AppID / 稳定名称）后**第一个动作**必须调用：
>
> ```bash
> python skills/mcpowers-crawler-reverse/scripts/reverse-analysis-session.py init \
>   --target "https://example.com/path" \
>   --parent . \
>   --target-type web \
>   --authorization "自测授权" \
>   --deliverable "待确认"
> ```
>
> 该命令是**幂等**的：已有工作区只复用不覆盖；同一 slug 复用同一目录。
> 工作区包含 4 个标准中文子目录（`01-目标画像/`、`02-接口分析/`、`03-逆向攻坚/`、`04-模块封装/`）、
> `分析计划.md` 与《会话状态.json》。`05-案例沉淀.md` 必须等阶段 5.5 `PASS` 后才生成。
>
> 不得先做"AI 自由分析"再补目录；不得把目录结构、slug、授权、目标类型、交付形态留给
> "之后再补"。

### 1. 目标画像与交付形态

**输入至少包含一项**：URL、App 包名、IPA/APK 路径、小程序 AppID/名称、应用名或明确平台。

> **v2.16.0 新增输入形式**：用户提供目标接口的 **cURL 命令** 也算合法输入——
> 按《爬虫分析规范》§3.0.1 模式 C + §3.0.7 cURL 12 项快速帮助 + §3.0.8
> cURL → 代码转换 SOP 处理（不直接录入即用 `python -c` + `curlconverter`
> 生成 Python 代码实测）。cURL 不包含响应体 / 端口 / TLS 指纹 / 中间产物，
> 仍需询问用户。

**目标画像必须记录**：

- 目标标识与授权范围
- URL / 包名 / Bundle ID / AppID
- 目标业务动作和成功语义
- 已知登录态、账号、设备、地区和网络前提
- 初步载体与运行时判断，未知项标 `unknown`

**slug 规则**：URL 取主域前缀；App 优先包名/Bundle ID 业务段；小程序优先平台 + AppID/名称；中文名用拼音或稳定英文别名。冲突时询问用户。

### 最终交付形态（必须在阶段 1 确认）

> RPC 是阶段 4 的逆向方式，不是第四种交付形态。三种最终交付形态固定为：纯协议 / 半自动化 / 纯自动化。

| 形态 | 定义 | 最终约束 |
|:-----|:-----|:---------|
| **纯协议** | Python + `curl_cffi` 独立生成参数并完成业务请求 | 不依赖浏览器/App/RPC 运行时 |
| **半自动化** | 自动化/RPC 处理登录、验证码、challenge、sign/token；协议层完成核心请求 | 状态可刷新、隔离、过期恢复 |
| **纯自动化** | 浏览器/App 自动完成完整业务动作和数据提取 | 从自动化公开入口验收完整业务 |

默认顺序：纯协议优先；算法无法稳定剥离时降为半自动化；强依赖页面/App 交互时才选择纯自动化。改变形态必须重新确认验收契约。

**产物目录**：

```text
{slug}-crawler-reverse/
├── 01-目标画像/                    # 目标画像 + 运行时指纹
├── 02-接口分析/                    # 接口清单 + 反爬评估 + 响应样本
├── 03-逆向攻坚/                    # 算法还原 + 钩子 + 抓包样本
├── 04-模块封装/                    # 内部 client.py + quick_test.py + verify.py + 验收报告
├── 05-案例沉淀.md
└── 分析计划.md
```

`分析计划.md` 写明目标、授权边界、slug、交付形态、目标类型、专项技能、
候选逆向方式和验收契约草案。**v2.17.0 起子目录 + 内部文件全部强制中文**，
详见《爬虫分析规范》§9.4.6.5。

### 2. 目标类型判断与路由

| 已确认指纹 | 路由 |
|:-----------|:-----|
| 网站、H5、浏览器页面、Web JS/WASM | `mcpowers-reverse-web` |
| App 但平台/运行时未知 | `mcpowers-reverse-app` |
| APK/AAB、Android、Java/Kotlin/JNI | `mcpowers-reverse-android` |
| IPA、iOS、Swift/Objective-C、Mach-O | `mcpowers-reverse-ios` |
| Flutter、Dart AOT、`libapp.so`、`App.framework` | `mcpowers-reverse-flutter` |
| uni-app、React Native、Cordova、Capacitor、WebView/JSBridge | `mcpowers-reverse-hybrid` |
| 微信/支付宝/抖音/百度小程序或小游戏 | `mcpowers-reverse-miniprogram` |

目标同时命中多个运行时，不猜唯一答案：先由 App 入口识别核心逻辑层，再按证据调用一个主专项，必要时引用其他专项作为辅助。

### 3. 通用接口证据要求

专项执行前后都必须遵守：

- 核心接口结论必须有 DrissionPage（v2.18.0 默认）/ Playwright（fallback）、`curl_cffi`、代理抓包、Hook 或运行时观测证据。
- `接口清单.md` 至少包含 URL/动作、Method、来源、置信度、动态参数、业务语义和响应样本。
- `[🎯]` 仅代表接口语义已实测，不代表模块可重复、跨会话或并发可用。
- 阶段结束前 `[❓]` 必须转为 `[🎯]` / `[⚠️]` 或删除。
- 敏感样本脱敏；临时 token、Cookie、nonce、challenge 不得写入常量。

### 4. 专项证据交接合同

每个 `mcpowers-reverse-*` 专项必须返回同一结构：

1. **target_fingerprint**：载体、OS、运行时、包/页面证据和置信度。
2. **interface_evidence**：核心接口/动作、来源、样本路径和业务断言。
3. **reverse_method**：无需逆向 / Python 复现 / Node 执行 / RPC / Hook / Native 分析。
4. **algorithm_verification**：至少 3 组不同输入的对照结果；不适用时说明原因。
5. **state_clues**：timestamp、nonce、sign、token、Cookie、challenge 的生命周期线索。
6. **platform_limits**：设备、账号、地区、版本、壳、宿主或工具限制。
7. **module_inputs**：进入阶段 5 所需的稳定常量、生成逻辑、状态接口和公开业务动作。
8. **evidence_paths**：`01-目标画像/`、`02-接口分析/`、`03-逆向攻坚/` 下的证据索引。

证据不完整时返回缺口，不得用平台专项的“成功”替代公共阶段 5.5。

### 4.1 RPC 逆向方式

RPC 适用于函数强依赖浏览器/App 运行时、直接抠代码或补环境成本过高的场景。最小链路：受控本地服务 → 目标运行时注册明确 action → 按 `group/name` 隔离账号/设备/session → 参数调用 → 结果进入协议层或验证证据。

必须验证：健康检查、断线重连上限、超时、schema、脱敏、重启恢复和并发隔离。RPC endpoint 只绑定本机或受控内网；优先受控 action，禁止把任意 execjs 作为默认接口。

---

## 公共收尾合同

### 5. 模块化封装

产出可独立 import 的轻量模块，完成一次真实业务调用必需的最小 token/challenge/session 生命周期必须实现或通过清晰接口注入。

**封装形式（v2.17.0 起强制）**：模块产物默认以**类（class）** 形式封装——
除非类无法满足（如纯算法、字典常量）。详细约定见《爬虫分析规范》§9.4.6，
本节只描述骨架与边界。

```text
04-模块封装/{module}/
├── __init__.py          # 暴露主入口类（from .client import ModuleClient）
├── client.py            # 模块入口类（v2.17.0 起替代 functions.py）
├── constants.py         # 稳定常量（不含抓包临时值）
├── README.md            # 模块公开 API + 业务用例
├── quick_test.py        # 手动快速验证（if __name__ == "__main__"）
├── test_*.py            # pytest 单元测试（可选）
├── verify.py            # 阶段 5.5 真实可用性验收脚本
└── 验收报告.md
```

**4 类核心约束**（详见《爬虫分析规范》§9.4.6）：

1. **类式封装**：默认 `client.py` 入口类，提供 `build_request` /
   `do_request` / `parse_response` + `request_and_parse` 便捷方法。
2. **请求与解析分离**：`do_request` 只发请求返回原始 Response，
   `parse_response` 只解析响应，`request_and_parse` 串行调用两者。
3. **零前置参数调用**：业务调用方法只接收业务参数（item_id 等），
   token / cookie / sign / nonce / timestamp 模块内部自动生成。
4. **`quick_test.py` 必备**：手动快速验证入口，禁止 `sys.argv` 传参。

**运行态存储边界**：半自动化/RPC 状态与抓包样本、稳定常量分离；记录类型、生成/过期时间、账号/session/设备绑定和刷新方式；原子写入、默认 Git 忽略、日志脱敏。禁止引入 Session 池、Redis 队列、调度器等当前交付不需要的设施。

**浏览器安全边界**：纯协议验证不是关闭用户 Chrome，而是停止调用浏览器/App/RPC 参数生成链路，在外部资源保持存活且未被修改的前提下，从模块公开入口独立完成业务。

**顶层分析文件命名（v2.17.0 起强制中文）**：`ANALYSIS_PLAN.md` → `分析计划.md`、
`05-case-study.md` → `05-案例沉淀.md`、子目录 `01-target-profile/` → `01-目标画像/` 等。
**所有分析文件名 + 子目录强制中文**（详见《爬虫分析规范》§9.4.6.5）。
子目录 + 内部文件保持英文（避免破坏现有引用）。

### 5.5 真实可用性验收

> `client.py` 已生成、HTTP 200、单次业务成功或 3 组 sign 一致，都不等于可交付。`verify.py` 必须真实执行，且 `验收报告.md` 最终为 `PASS`。

#### 5.5.1 验收契约

报告先写清：公开入口、业务输入、核心业务动作、业务成功断言、运行前提、目标会话/TTL/并发。用户要求的动作未实现，不得缩小测试范围宣布成功。

#### 5.5.2 按交付形态验收

- **纯协议**：停止依赖浏览器/App/RPC 的参数生成链路后独立运行；用户已有浏览器保持运行，禁止为了测试而关闭。
- **半自动化**：自动化/RPC 只处理确认过的难点；状态可刷新、隔离并从过期/断线恢复。
- **纯自动化**：公开自动化入口完成完整业务动作和数据提取，不需要人工复制报文。

#### 5.5.3 串行、冷启动与生命周期

- 至少 2 组不同业务输入，合计连续调用 ≥5 次。
- 至少 2 个独立 session 或冷启动环境。
- 执行原报文重放、动态参数重生成、跨 session 对照和合理 TTL 复测。
- 每个关键状态必须归类：`reusable`、`per-request`、`single-use-token`、`session-bound`、`time-bound`、`challenge-bound` 或 `unknown`。
- `unknown` 禁止冒充可复用；若影响验收契约则不能 PASS。

#### 5.5.4 有界并发

按并发 **2 → 5** 递增，只发送足以发现状态污染的小批量请求；分别覆盖同输入和不同输入。记录业务成功数、401/403/429/5xx、验证码、P50/P95、session 策略和失败原因。出现 429、验证码增加、账号安全提示、目标异常或授权边界时立即停止。

#### 5.5.5 判定

| 状态 | 条件 | 后续 |
|:-----|:-----|:-----|
| `PASS` | 业务、重复、生命周期、跨会话/时效和目标并发均有证据 | 可进入阶段 6/7 |
| `CONDITIONAL` | 功能可用但有未被契约接受的限制或关键状态未知 | 调整契约并补测 |
| `FAIL` | 核心业务失败、无法持续生成有效报文或状态污染 | 返回接口/逆向/封装阶段 |

`验收报告.md` 至少包含测试环境、验收契约、串行结果、生命周期矩阵、并发结果、停止原因、限制、最终状态和证据路径。`CONDITIONAL` 不能靠口头确认变成 `PASS`。

### 6. 案例沉淀

仅 `PASS` 后生成 `05-案例沉淀.md`，记录目标、平台指纹、接口、动态参数、定位过程、还原方案、可复用入口、生命周期和关键决策。是否追加到《爬虫分析规范》附录 C 必须询问用户；同意后同步更新规范 `last_updated`。

### 7. 落地决策

仅当 `验收报告.md` 最终状态为 `PASS` 时展示：

- 完整爬虫项目 → `mcpowers-init`
- 基于轻量模块继续开发 → `mcpowers-feat`
- 仅保留轻量产物 → 结束
- 提炼为跨项目公共库 → `mcpowers-extract`

路径冲突时不得覆盖已有资产。

---

## 反模式（禁止）

- ❌ 入口继续承载所有平台工具细节，导致拆分名存实亡。
- ❌ 专项复制公共阶段 5.5 或自行宣布模块可交付。
- ❌ 不做载体/运行时识别就按用户口头技术栈硬套工具。
- ❌ 单次成功、HTTP 200 或 3 组 sign 一致就宣布模块可用。
- ❌ 临时 token/Cookie/nonce/challenge 写进 `constants.py`。
- ❌ 无界并发或把可用性验证做成压力测试。
- ❌ **关闭用户本身的浏览器**：接管资源无论成功、异常还是收尾都不可 close/kill。
- ❌ 接管失败时静默 `launch()` 或 `browser.new_context()`。
- ❌ 外部 daemon 异常时擅自 stop/restart；应标记 unavailable 并回退。
- ❌ 把 RPC 当最终交付形态或暴露公网。
- ❌ **v2.16.0 新增**：阶段 2 抓包失败直接切 B/C/D，**未走**《爬虫工具与抓包规范》§3.9.2 漏抓 7 层 6 问自检——必须先按铁律 #11 排除 7 层漏抓根因再切协作模式。
- ❌ **v2.19.0 新增**：绕过 `reverse-analysis-session.py` 直接"AI 自由分析"。任何逆向任务必须先调 `init` 落工作区与《分析计划.md》，Web 任务再依次 `web-start` → 等用户操作 → `web-stop`，不得先分析再补目录。
- ❌ **v2.19.0 新增**：在浏览器指纹存在阻断项（`navigator.webdriver=true`、UA 含 HeadlessChrome、UA 与 CDP 主版本矛盾、宿主 OS 与 navigator.platform 明显矛盾、关键 API 缺失）时仍继续目标业务操作。
- ❌ **v2.19.0 新增**：把 DrissionPage 的"自动化通过率优势"或"接管便利性"包装成"内置反指纹检测"。自动化通过率与反指纹是两件事，不得混说。
- ❌ **v2.21.0 新增**：`web-stop` 后跳过 `session-artifacts-generator.py` 自动调用，直接"AI 自由整理 HAR"——必须经生成器生成目标接口候选 + 响应样本 + 模块种子，AI 阶段 2 在此基础上展开。
- ❌ **v2.21.0 新增**：把 `session-artifacts-generator.py` 自动生成的 `client.py` / `quick_test.py` 直接标 `[🎯]` 或 `PASS`——生成器产物是分析种子，**不是**阶段 5.5 真实可用性验收通过。
- ❌ **v2.21.0 新增**：把 `02-接口分析/响应样本/*.json` 的 `body_preview` 字段当作完整响应 body——HAR 当前仅前 1024 字符预览，envelope 已声明 `body_truncated` 与 "不代表完整响应体"，必须按提示理解。
- ❌ **v2.21.0 新增**：把 `session-artifacts-generator.py` 业务方法中的 token / cookie / sign / nonce / timestamp / challenge / csrf / xsrf / session_id / captcha 作为必填参数——必须归入 6 类 lifecycle 分类，业务方法保持零前置参数。

## 完成后自检清单

- [ ] 已执行公共前置合同并记录最终交付形态。
- [ ] 目标已路由到唯一主专项；多运行时辅助关系有证据。
- [ ] 专项按标准证据交接合同返回，无 `[❓]` 遗留。
- [ ] 外部 browser/context/page/tab/daemon 所有权已记录且未关闭。
- [ ] 纯协议测试通过停止依赖完成，用户 Chrome 保持运行。
- [ ] 模块无临时状态硬编码，运行态存储边界明确。
- [ ] `verify.py` 已真实执行，生命周期与并发证据完整。
- [ ] `验收报告.md` 最终为 `PASS` 后才进入阶段 6/7。
- [ ] 已询问案例沉淀与落地方式。
- [ ] 已运行 `bash scripts/check-readme-sync.sh` 与 `bash tests/plugin-verify.sh`。
- [ ] **v2.21.0 派生产物门禁**（Web 任务必走）：
  - ☐ `web-stop` 后《会话状态.json》含 `artifacts_generation` 字段且 `status` ∈ {`generated`, `partial`, `skipped`}；如为 `failed` 必须有脱敏错误信息并人工重跑生成器
  - ☐ `02-接口分析/目标接口候选.md` 已生成或已记录失败原因；top10 含 high-trigger 业务候选
  - ☐ `02-接口分析/响应样本/*.json` 每接口 1 个 envelope，envelope 含 `parse_status` + `body_truncated` + "不代表完整响应体" 声明
  - ☐ `04-模块封装/{module}/client.py` 与 `quick_test.py` 存在；自动生成的种子**未**被当作 `[🎯]` / `PASS`
  - ☐ 自动生成的 `client.py` 业务方法零前置参数（无 token / cookie / sign 等敏感参数），含 6 类 lifecycle 标签至少 4 类
- [ ] **v2.16.0 漏抓 7 层 6 问自检**（强门禁，阶段 2 抓包失败切模式前必走，**v2.18.0 DrissionPage 化，v2.20.0 端口独立**）：
  - ☐ L1：已用 `curl http://localhost:<port>/json | jq` 列出所有 target，确认 worker/iframe/SW target 单独 attach？（`v2.20.0` 起 `<port>` 取自《会话状态.json》`chrome_port` 字段，由 `reverse-analysis-session.py init` 自动分配）
  - ☐ L2：Chrome 启动命令已带 `--remote-allow-origins=*`？（Chrome 150+ 必传）
  - ☐ L3：是否走 `Target.createTarget` / `page.new_tab()` 不带 url 拉了 tab？（**v2.18.0 DrissionPage 化**——必须从 `page.tab_ids` 中按 URL / title 挑选真实 page target）
  - ☐ L4：DevTools Network 是否抓到 `(failed)` 空白请求？（若是，先解决证书/SSLKEYLOGFILE）
  - ☐ L5：DevTools Filter 是否启用了 Hide data URLs / Fetch-XHR 单选？（若是，先关闭）
  - ☐ L6：目标 API 是否走 WebSocket / SSE / sendBeacon / HTTP/3 / Cache 命中？（若是，切到对应 DevTools 标签；DrissionPage 用 `page.listen.start('ws://...')` 监听 WS）
  - 详见《爬虫工具与抓包规范》§3.9。
