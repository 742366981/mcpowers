---
name: mcpowers-crawler-reverse
description: "逆向统一入口 / 目标类型判断 / 抓包与加密还原 / 交付验收 → 触发本技能。口语：帮我看看这个目标怎么逆向、不确定是网站还是App、做成纯协议或自动化、模块必须真的可用。中英：reverse engineering/target triage/protocol/RPC/lifecycle/usability verification。边界：明确网站→mcpowers-reverse-web；未知App→mcpowers-reverse-app；明确Android/iOS/Flutter/Hybrid/小程序→对应专项；已有爬虫修复→mcpowers-bugfix。流程：公共前置合同→专项证据→公共收尾合同。"
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

**防循环规则**：专项技能直接命中时，只 Read 并执行本技能的「公共前置合同」和「公共收尾合同」，不得再次调用本技能做平台分流。

## 铁律

1. **先侦察后逆向**：能明文构造就不进入加密逆向。
2. **先确认交付形态**：纯协议、半自动化、纯自动化的验收条件不同。
3. **专项只交证据，不宣布可交付**：只有公共阶段 5.5 能给出最终状态。
4. **结果必须实测**：算法至少 3 组样本；模块还需重复、生命周期、跨会话和有界并发证据。
5. **合规优先**：授权、robots.txt、服务条款和法律边界不清时先询问；越界即停。
6. **外部接管资源不可关闭**：接管的用户 browser/context/page、既有标签页和外部 daemon 一律视为外部所有；收尾、异常和回退只能停止使用/断开客户端，禁止 `browser.close()`、`context.close()`、关闭既有 page、kill 用户 Chrome 或擅自 stop 外部 daemon。
7. **资源所有权必须显式记录**：任务创建的资源写明 owner、创建方式和清理权限；用户 Chrome 中新开的标签页默认保留，仅在用户明确确认后清理。
8. **bb-browser 是可选增强**：不可用时完整回退 Playwright/CDP + popup-handler.py，不得中断主链路。
9. **真实可用才落地**：`verification-report.md` 为 `PASS` 后才能进入阶段 6/7。
10. **RPC 是逆向实现方式，不是最终交付形态**。
11. **抓不到 ≠ 不存在**：阶段 2 抓包失败必须先走《爬虫工具与抓包规范》§3.9
    漏抓 7 层 6 问自检，**禁止**直接把"抓不到"等同于"接口不存在"；cURL 是
    已知接口最高价值告知，§3.0.1 模式 C 必须按 §3.0.7 12 项快速帮助清单
    最大化利用，并按 §3.0.8 SOP 在线转换为 Python 代码实测。

---

## 触发即执行（统一入口 → 专项 → 统一收尾）

## 公共前置合同

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
├── 01-target-profile/
├── 02-interfaces/
├── 03-reverse/
├── 04-modules/
├── 05-case-study.md
└── ANALYSIS_PLAN.md
```

`ANALYSIS_PLAN.md` 写明目标、授权边界、slug、交付形态、目标类型、专项技能、候选逆向方式和验收契约草案。

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

- 核心接口结论必须有 Playwright、`curl_cffi`、代理抓包、Hook 或运行时观测证据。
- `api-inventory.md` 至少包含 URL/动作、Method、来源、置信度、动态参数、业务语义和响应样本。
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
8. **evidence_paths**：`01-target-profile/`、`02-interfaces/`、`03-reverse/` 下的证据索引。

证据不完整时返回缺口，不得用平台专项的“成功”替代公共阶段 5.5。

### 4.1 RPC 逆向方式

RPC 适用于函数强依赖浏览器/App 运行时、直接抠代码或补环境成本过高的场景。最小链路：受控本地服务 → 目标运行时注册明确 action → 按 `group/name` 隔离账号/设备/session → 参数调用 → 结果进入协议层或验证证据。

必须验证：健康检查、断线重连上限、超时、schema、脱敏、重启恢复和并发隔离。RPC endpoint 只绑定本机或受控内网；优先受控 action，禁止把任意 execjs 作为默认接口。

---

## 公共收尾合同

### 5. 模块化封装

产出可独立 import 的轻量模块，完成一次真实业务调用必需的最小 token/challenge/session 生命周期必须实现或通过清晰接口注入。

```text
04-modules/{module}/
├── __init__.py
├── functions.py
├── constants.py
├── README.md
├── verify.py
└── verification-report.md
```

**运行态存储边界**：半自动化/RPC 状态与抓包样本、稳定常量分离；记录类型、生成/过期时间、账号/session/设备绑定和刷新方式；原子写入、默认 Git 忽略、日志脱敏。禁止引入 Session 池、Redis 队列、调度器等当前交付不需要的设施。

**浏览器安全边界**：纯协议验证不是关闭用户 Chrome，而是停止调用浏览器/App/RPC 参数生成链路，在外部资源保持存活且未被修改的前提下，从模块公开入口独立完成业务。

### 5.5 真实可用性验收

> `functions.py` 已生成、HTTP 200、单次业务成功或 3 组 sign 一致，都不等于可交付。`verify.py` 必须真实执行，且 `verification-report.md` 最终为 `PASS`。

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

`verification-report.md` 至少包含测试环境、验收契约、串行结果、生命周期矩阵、并发结果、停止原因、限制、最终状态和证据路径。`CONDITIONAL` 不能靠口头确认变成 `PASS`。

### 6. 案例沉淀

仅 `PASS` 后生成 `05-case-study.md`，记录目标、平台指纹、接口、动态参数、定位过程、还原方案、可复用入口、生命周期和关键决策。是否追加到《爬虫分析规范》附录 C 必须询问用户；同意后同步更新规范 `last_updated`。

### 7. 落地决策

仅当 `verification-report.md` 最终状态为 `PASS` 时展示：

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

## 完成后自检清单

- [ ] 已执行公共前置合同并记录最终交付形态。
- [ ] 目标已路由到唯一主专项；多运行时辅助关系有证据。
- [ ] 专项按标准证据交接合同返回，无 `[❓]` 遗留。
- [ ] 外部 browser/context/page/tab/daemon 所有权已记录且未关闭。
- [ ] 纯协议测试通过停止依赖完成，用户 Chrome 保持运行。
- [ ] 模块无临时状态硬编码，运行态存储边界明确。
- [ ] `verify.py` 已真实执行，生命周期与并发证据完整。
- [ ] `verification-report.md` 最终为 `PASS` 后才进入阶段 6/7。
- [ ] 已询问案例沉淀与落地方式。
- [ ] 已运行 `bash scripts/check-readme-sync.sh` 与 `bash tests/plugin-verify.sh`。
- [ ] **v2.16.0 漏抓 7 层 6 问自检**（强门禁，阶段 2 抓包失败切模式前必走）：
  - ☐ L1：已用 `curl http://localhost:9222/json | jq` 列出所有 target，确认 worker/iframe/SW target 单独 attach？
  - ☐ L2：Chrome 启动命令已带 `--remote-allow-origins=*`？（Chrome 150+ 必传）
  - ☐ L3：是否走 `Target.createTarget` 拉了 tab？（必须从 `user.contexts[i].pages` 中挑选）
  - ☐ L4：DevTools Network 是否抓到 `(failed)` 空白请求？（若是，先解决证书/SSLKEYLOGFILE）
  - ☐ L5：DevTools Filter 是否启用了 Hide data URLs / Fetch-XHR 单选？（若是，先关闭）
  - ☐ L6：目标 API 是否走 WebSocket / SSE / sendBeacon / HTTP/3 / Cache 命中？（若是，切到对应 DevTools 标签）
  - 详见《爬虫工具与抓包规范》§3.9。
