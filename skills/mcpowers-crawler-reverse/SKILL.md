---
name: mcpowers-crawler-reverse
description: "骨架触发：爬虫逆向/接口分析/抓包/加密参数还原/JS反混淆/APP逆向/frida/SSL Pinning/接管浏览器/弹窗/人机协作，或 bb-browser/site adapter/MCP server/接管浏览。口语变体：帮我逆向网站或 App、sign 怎么算、请求参数看不懂、反爬/滑块/验证码/风控、接管我的 Chrome、登录态保留、your browser is the API。中英混输：reverse engineering/deobfuscation/signature/CDP attach/takeover browser/popup/API discovery/bb-browser。边界：默认 Python+Playwright+curl_cffi，优先复用本机 Chrome；bb-browser 为可选依赖，未安装保留原链路；项目骨架→mcpowers-init，已有爬虫修复→mcpowers-bugfix。"
---

# mcpowers-crawler-reverse（爬虫逆向分析）

> **mcpowers 自身设计**，基于 `爬虫分析规范.md` + `爬虫规范.md`（v1.0）。
> **核心**：把「陌生目标 + 加密参数」从一次性的逆向尝试，沉淀为可复用、可工程化、可回溯的方法库。

---

## 编排

本技能按顺序调用以下方法层技能 + 规范：

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-brainstorm` | 方法 | 输入不明确（URL/App 缺失） | 中断并回问用户 |
| 2 | `爬虫分析规范.md` | 规范 | **必读** | 中断，提示加载失败 |
| 3 | `爬虫规范.md` | 规范 | 阶段 5 轻量封装时 | 提示按需加载 |
| 4 | `mcpowers-plan` | 方法 | 阶段 2/4 > 3 步 | 跳过（不强制） |
| 5 | `mcpowers-code-review` | 方法 | 阶段 5 封装完成 | Critical 必须修复 |
| 6 | `mcpowers-init` | 场景 | **阶段 7 联动**（用户选择落地为完整项目） | 用户未选择则跳过 |

**保护路径**（PreToolUse(Write) hook 强制确认）：`mcpowers-shared/`、`mcpowers/`、`hooks/` 三个目录的写操作触发前确认。本技能的产物目录在工作区根，不在保护路径内。

**铁律**：
1. **先侦察后逆向**（能明文构造就不逆向）—— `爬虫分析规范.md` 第一部分先做完再决定是否进入第二部分
2. **逆向结果必须可验证**（多样本交叉验证 ≥ 3 组）
3. **合规优先** —— 逆向前必读目标站 robots.txt / 服务条款 / 法律法规，越界即停
4. **产物归档必须规范** —— `{slug}-crawler-reverse/` 命名，不散落工作区
5. **沉淀优于一次性** —— 阶段 6 强制沉淀案例到《爬虫分析规范》附录 C
6. **默认 Python + 分阶段选框架**（v2.9.3 新增，**v2.9.4 细化**）：
   - Python 是默认语言（除非用户明确指定 JS/Go/其他）
   - **分析阶段（§2-4）固定 Playwright-Python**（stealth + CDP attach，CDP 完整、stealth 生态最成熟）
   - **封装阶段（§5）让用户在 3 个框架中选**（`AskUserQuestion` 必问）：
     - **Playwright-Python**：海外项目 + 复杂交互 + 工程化（默认）
     - **DrissionPage**：国产、**内置接管浏览器 + 内置反检测**、对国内站点（小红书/抖音/淘宝/1688）适配好
     - **seleniumbase**：UC Mode（undetected-chromedriver）成熟 + 国外生态 + 需要 Selenium 兼容性时
   - 协议请求（不走浏览器的 API 直连）默认 **`curl_cffi.requests`**，**禁止裸用 `requests`**（TLS 指纹一秒被风控识别）
7. **主动风控防御 + 主动解决验证码**（v2.9.3 新增）—— 代码本身默认开启 **`playwright-stealth`** + UA/视口/时区合理随机 + 行为模式伪装（随机滚动、随机点击间隔、模拟鼠标轨迹）+ Cookie 持久化；遇滑块/点选/图形验证码**主动解决**（轨迹模拟 + OpenCV 缺口识别 / 打码平台 / 行为轨迹拟合），**不得以"难以绕过"为由中断**
8. **复用本机浏览器，不开新窗口**（v2.9.3 新增）—— 自动化默认用 `playwright.chromium.connect_over_cdp("http://localhost:9222")` 接入用户已启动的本机 Chrome（`chrome --remote-debugging-port=9222`），**禁止每次新开 Playwright 窗口**；唯一例外：用户明确说"无 GUI 自动化"或"协议直连"
9. **接口分析必须实测验证**（v2.9.3 新增）—— 在 `api-inventory.md` 写「这个 URL 是干嘛的 / 这个参数是加密的 / 这个响应字段是用户数据」等结论前，**必须用 `curl_cffi` / `Playwright` 实测一次**（带抓到的真实 header/cookie/参数），并保存响应样本到 `02-interfaces/responses/{slug}.json`；**禁止凭接口名/参数名/字段名凭空判断**；唯一例外：用户已明确告知所有核心内容
10. **bb-browser 是可选依赖**（v2.10.0 新增）—— 只有 `bb-browser status` 可用、daemon 正常且目标站点命中 site adapter 时，才启用 bb-browser CLI / MCP / adapter；未安装、daemon 异常、adapter 未覆盖或版本不兼容时，**必须完整保留 v2.9.5 的 Chrome CDP + Playwright + popup-handler.py 原链路**，**不得把第三方 CLI 变成硬依赖**

**与 `mcpowers-feat` 的边界**：
- `mcpowers-feat` 是「按规范在已有项目加功能」，不涉及陌生目标分析
- 本技能是「分析陌生目标 + 产出可复用产物」，阶段 5 之后可衔接 `mcpowers-feat`/`mcpowers-init` 落地业务项目

---

## 触发即执行（7 阶段）

### 1. 目标画像 + 产物目录初始化

**输入校验**：
- 用户必须提供至少 1 项：URL / App 包名 / IPA 路径 / 应用名（中文名）
- 输入模糊（"帮我爬 X"无 X）→ 中断，调 `mcpowers-brainstorm` 澄清

**slug 计算规则**（**必走**，由 `AskUserQuestion` 让用户确认）：
- URL → 主域名前缀小写：`jd.com` → `jd`，`github.com` → `github`，`bilibili.com` → `bilibili`
- App → 包名前缀小写：`com.douyin.android` → `douyin`，`com.taobao.taobao` → `taobao`，`com.xingin.xhs` → `xingin`（保留 `xhs` 也可，让用户选）
- 中文应用名 → 转拼音或英文别名（`小红书` → `xiaohongshu`，`抖音` → `douyin`），让用户确认

**产物目录初始化**：在工作区根创建：

```
{slug}-crawler-reverse/
├── 01-target-profile/      # 目标画像（站点/App 信息）
├── 02-interfaces/          # 接口分析（第一部分产物）
├── 03-reverse/             # 逆向攻坚（第二部分产物，加密时才需要）
├── 04-modules/             # 模块化封装（最终可复用产物）
├── 05-case-study.md        # 案例报告（按《爬虫分析规范》附录 C 格式）
└── ANALYSIS_PLAN.md        # 本次分析的总体方案（首阶段输出）
```

**Read 必读规范**：
- `mcpowers-shared/docs/技术规范/爬虫分析规范.md`（**必读全文**，方法论核心）
- `mcpowers-shared/docs/技术规范/爬虫规范.md`（**阶段 5 时必读**，模块化封装骨架）
- 按需：`mcpowers-shared/docs/技术规范/日志规范.md`（如涉及大量请求日志）

**输出**：`ANALYSIS_PLAN.md`（总体方案：目标说明、slug、预期阶段、可逆向/不可逆向判定预估）

---

### 2. 接口分析（按《爬虫分析规范》§1-6）

**适用范围**：必走，无论是否需要逆向都要先做。

> **v2.9.5 重构**：阶段 2 拆分为 5 个子步骤，**前置预检 → 协作模式选择 → 弹窗清理 → 抓包分析 → 接口识别带置信度**。每一步都有明确的产品 SOP，**不再"打开就抓"**。

#### 2.0 前置预检（v2.9.5 新增，v2.10.0 增强 bb-browser 探测，按规范 §2.5.1-2.5.5）

**核心原则**：AI 接到任务后的**第一个动作**是探测接管能力，**不假设接管、不擅自开新窗口**。

**执行步骤**：

1. **先探测 bb-browser（v2.10.0 新增）**：执行 `bb-browser status`，探测 CLI 是否已安装、daemon 是否运行、当前 CDP 状态
   - 探测失败 / 命令不存在 / 不可用 → 标记为「bb-browser unavailable」，**继续执行原链路，不得报错中断**
   - 探测成功 → 记录 adapter 可用列表，继续步骤 2
2. 检测 `localhost:9222` 端口（脚本见 §2.5.1）
3. 检测到 → 列出当前所有 tabs，识别是否已含目标域（脚本见 §2.5.3）
4. 检测到目标域 → AskUserQuestion 3 选 1：接管现有 tab / 新开 tab / 重新开浏览器
   - **若 bb-browser 命中目标站点 adapter**，提示"可优先用 bb-browser <site> <action> 触发后再接管"
5. 未检测到 → AskUserQuestion 4 选 1（§2.5.4）：
   - A. 启动 Chrome 调试模式（提供 Windows/macOS/Linux 命令）
   - B. 让 AI 开新浏览器窗口（无登录态，仅适合简单静态页）
   - C. 协议直连（curl_cffi，无 GUI）
   - D. 取消本次任务

> **bb-browser 优先级**：bb-browser 是增强型站点操作工具，**不替代 Chrome CDP 接管**。bb-browser 可用时优先使用其站点适配能力；CDP 接管仍须遵循 §2.5.1-§2.5.4。

**详细方法论**：见规范 §2.5.1 / §2.5.2 / §2.5.3 / §2.5.4 + §2.5.5（v2.10.0 新增 bb-browser 集成策略）。

#### 2.0.5 协作模式选择（v2.9.5 新增，v2.10.0 增强 adapter 优先，按规范 §3.0）

**核心原则**：AI 抓不到时**主动切换模式**，**不把"找不到"等同于"不存在"**。

**AskUserQuestion 必走**（4 选 1，阶段 2 第一个动作前）：

```
> 请问使用哪种协作模式分析接口？
> - A. AI 全自动抓包（默认，AI 跑 Playwright 模拟触发；**v2.10.0 新增** bb-browser 命中 site adapter 时优先调用）
> - B. 用户操作 + AI 抓包（适合登录态场景：你操作我看）
> - C. 用户告知接口（如果你已知目标 URL / 参数）
> - D. AI 引导用户到指定页面（适合不清楚目标位置的场景）
```

**模式 A 的 bb-browser 增强（v2.10.0 新增）**：

- bb-browser 可用且目标站点有 adapter → **优先调用 adapter** 获取结构化业务线索
- adapter 仅提供业务线索，**不替代抓包和实测验证**（adapter 返回的 URL / 参数 / 响应仍须经 Playwright / `curl_cffi` 验证）
- adapter 不支持 / 调用失败 / 结果不完整 → **无缝回退**到 Playwright 自动化触发
- bb-browser 与 Playwright 必须连接**同一用户 Chrome / CDP 会话**，禁止新建独立浏览器上下文

**模式切换触发条件**（详细见规范 §3.0.3）：
- A 模式下连续 3 次未识别核心接口 → 暂停，切到 B/C/D
- 用户主动说"我直接告诉我" → 切到 C
- 阶段 2 自检发现 [❓] > 3 → 暂停，切到 B 让用户操作触发

#### 2.0.5.1 bb-browser adapter 失败判定与结果合并（v2.11.1 新增）

bb-browser adapter 调用是 v2.10.0 的"结构化线索"，但 v2.10.0 未明确**失败如何判定、结果如何与 Playwright 实测合并**。本节补全。

**adapter 调用失败判定（4 类）**：

| 失败类型 | 判定标准 | 处理 |
|:---------|:---------|:-----|
| **超时** | `bb-browser site <site> <action>` 单次调用 > **30s** 未返回 | 标记 `[adapter-timeout]`，回退 Playwright |
| **命令不存在** | bb-browser status 显示 daemon running，但 site 命令报 `command not found` | 标记 `[adapter-not-covered]`，目标站点无 adapter |
| **返回 None / 空结构** | adapter 返回 JSON 解析后 `data == None` 或 `len(data) == 0` | 标记 `[adapter-empty]`，adapter 不可用，回退 Playwright |
| **结构不匹配** | adapter 返回字段缺 `url` / `method` / `params` 中任一关键字段 | 标记 `[adapter-malformed]`，记录原始响应到 `01-target-profile/bb-browser-calls.log`，回退 Playwright |

**调用日志格式（必落，v2.11.1 新增）**：

每次 adapter 调用必须记录到 `01-target-profile/bb-browser-calls.log`：

```log
[2026-07-24T10:23:45+08:00] adapter=twitter/search action="AI agent" status=success duration=2.3s urls=3
[2026-07-24T10:24:12+08:00] adapter=twitter/user-detail action="@openai" status=timeout duration=30.0s urls=0
[2026-07-24T10:24:43+08:00] adapter=twitter/user-detail action="@openai" status=malformed duration=1.8s urls=0 raw={"error":"..."}
```

**结果合并规则（adapter ↔ Playwright 实测冲突时）**：

| 维度 | 优先级 | 理由 |
|:-----|:-------|:-----|
| **URL 路径** | **Playwright 实测优先** | 实测拿到真实响应样本，置信度可升 `[🎯]` |
| **HTTP Method** | **Playwright 实测优先** | 同上 |
| **加密参数位置** | **adapter 优先** | adapter 知道站点逻辑，能定位 sign/token 字段 |
| **selector / XPath** | **adapter 优先** | adapter 返回的是站点维护者认可的稳定 selector |
| **业务语义标注** | **adapter 优先** | adapter 自带站点业务模型 |

**api-inventory.md 加「来源」列（v2.11.1 新增）**：

```markdown
| # | URL | Method | 置信度 | 来源 | 加密参数 | 业务含义 | 响应样本 |
|:--|:----|:-------|:-------|:-----|:---------|:---------|:---------|
| 1 | /api/v1/user/profile | GET | [🎯] | Playwright | 无 | 用户资料 | responses/user-profile.json |
| 2 | /api/v1/feed | GET | [⚠️] | adapter | sign | 信息流 | （未实测） |
| 3 | /api/v1/tweet/post | POST | [⚠️] | adapter+Playwright | sign+token | 发推 | responses/tweet-post.json |
```

**来源取值**：`adapter` / `Playwright` / `curl_cffi` / `adapter+Playwright`（合并验证后）

**反模式（v2.11.1 新增）**：

- ❌ **adapter 调用无日志** —— 必须落 `01-target-profile/bb-browser-calls.log`，否则无法事后复盘
- ❌ **adapter URL 与 Playwright 实测 URL 不一致时直接信 adapter** —— 冲突时**实测优先**（§2.0.5.1 合并规则）
- ❌ **adapter 失败 4 类判定任一未检查就继续** —— 必须先判定状态再决定 fallback
- ❌ **api-inventory.md 无「来源」列** —— 无法区分「adapter 推测」与「Playwright 实测」

---

#### 2.1 弹窗清理（v2.9.5 新增，v2.10.0 增强 bb-browser 协同，按规范 §2.7）

**核心原则**：进入页面后**第一件事**是清理弹窗；**抓到弹窗内接口 ≠ 抓到核心业务接口**。

**执行步骤**：

```python
from scripts.popup_handler import cleanup_all

page = browser.contexts[0].pages[0]
closed = cleanup_all(
    page,
    pause_for_user_patterns=["登录", "年龄验证", "隐私政策", "用户协议"],
    screenshot_dir="01-target-profile/popups/",
)
```

**8 类弹窗分级**（详细字典见规范 §2.7.1 + 附录 D）：
- **D.1-D.5 自动处理**：Cookie 同意 / Notification / Newsletter / App 下载引导 / 地理位置
- **D.6-D.8 询问用户**：登录墙 / 年龄验证 / 合规同意（截图 + AskUserQuestion）

**bb-browser 协同（v2.10.0 新增）**：

bb-browser 的 site adapter 通常已处理常见**登录前引导 / 站点初始化页 / 公开内容入口**。若 adapter 返回页面已就绪，仍必须调用 `popup-handler.py cleanup_all()` 做二次清理；adapter 未覆盖、调用失败或页面仍存在弹窗时，完全按 D.1-D.8 原流程处理。

bb-browser **不替代** `popup-handler.py`：
- adapter 负责**站点级导航 / 内容入口 / 结构化操作**
- `popup-handler.py` 负责**通用 DOM 弹窗 / 浏览器原生权限 / 合规询问**
- **登录墙、年龄验证、隐私协议仍必须截图并询问用户**，禁止自动确认

**禁止**：
- ❌ 跳过弹窗直接抓包（抓到的是弹窗接口不是真实业务）
- ❌ 自动接受所有 Cookie（GDPR 合规风险）
- ❌ 自动登录（合规 + 隐私风险）
- ❌ 用 bb-browser 替代 popup-handler.py 跳过通用弹窗清理（v2.10.0 新增）

#### 2.2 抓包与自动化分析（v2.9.4 原有，v2.10.0 增强 bb-browser 触发）

**执行要点**（**详细方法论见规范 §1-6**）：
1. **抓包**：Web → DevTools / mitmproxy / Charles；APP → mitmproxy + 证书 + SSL Pinning 绕过（详见规范 §2 + §10.2）
2. **自动化分析**（**v2.10.0 增强 bb-browser 并行**）：
   - bb-browser 可用 + 命中 site adapter → **优先通过 adapter 触发目标站点动作 / 定位实体 / 进入业务页面**
   - 同时用 **Playwright-Python**（默认启用 `playwright-stealth` 绕过 `navigator.webdriver` 等指纹）模拟用户行为触发懒加载接口（详见规范 §2.3）
   - bb-browser 与 Playwright **必须连接同一用户 Chrome / CDP 会话**，禁止分别创建新的浏览器上下文
   - adapter 不可用 / 未命中 → 保持原 Playwright 自动化路径
3. **实测验证**（铁律 #9 + **v2.10.0 增强**）：每标定一个核心接口后**必须用 `curl_cffi` / `Playwright` 实测一次**（带真实 header/cookie/参数），响应样本落到 `02-interfaces/responses/{slug}.json`；**禁止凭接口名/路径段/参数名在 `api-inventory.md` 直接写结论**；**adapter 命中仅是结构化线索，不能跳过实测**
4. **过滤冗余**：剔除 CDN/上报/字体/心跳等（详见规范 §3.1）
5. **风控识别**：识别 sign/token/fingerprint 等关键参数 + L1-L5 难度分级（详见规范 §4.6 + §6.1）

> bb-browser 负责**高层站点操作和结构化线索**，Playwright 负责**CDP 会话内的底层网络证据**；两者必须共享同一用户 Chrome 上下文。

#### 2.3 接口识别带置信度（v2.9.5 新增，按规范 §3.4.5）

**核心原则**：每个标定接口必须带置信度标记，**让用户一眼看出哪些是实测的、哪些是猜的**。

**3 档置信度**：

| 置信度 | 含义 | 触发条件 | 标记 |
|:-------|:-----|:---------|:-----|
| **🎯 高** | 已实测，对照过响应 | §3.4 实测流程已走完，响应样本已保存（**v2.10.0 增强**：bb-browser site adapter 命中 + Playwright / `curl_cffi` 实测验证后也满足条件） | `[🎯]` |
| **⚠️ 中** | 路径/参数匹配但未实测 | 命中 §3.2 特征但未实测（**v2.10.0 增强**：adapter 返回但未实测只能标 `[⚠️]`，不能直接升 `[🎯]`） | `[⚠️]` |
| **❓ 低** | 仅凭名字推断 | 路径含关键词但完全未实测 | `[❓]` |

**收敛铁律**（v2.9.5 新增）：阶段 2 结束前所有 `[❓]` **必须转 `[🎯]` 或删除**，不允许把 `[❓]` 留在最终 `api-inventory.md`。

**api-inventory.md 模板**（v2.9.5 新增"置信度"列）：

```markdown
| # | URL | Method | 置信度 | 加密参数 | 业务含义 | 响应样本 |
|:--|:----|:-------|:-------|:---------|:---------|:---------|
| 1 | /api/v1/user/profile | GET | [🎯] | 无 | 用户资料 | responses/user-profile.json |
| 2 | /api/v1/feed | GET | [⚠️] | sign | 信息流 | （未实测） |
| 3 | /api/v1/cheap-shot | POST | [❓] | ? | （猜的） | - |
```

**产出**（落到 `02-interfaces/`）：
- `api-inventory.md` —— 接口清单（URL、Method、参数、响应字段、是否加密、**风控难度 L1-L5**、**置信度 🎯/⚠️/❓** v2.9.5 新增列）
- `requests/` —— **核心业务接口的抓包样本**（curl / HAR 格式，**仅保留核心，去重**）
- `responses/` —— 关键接口的响应样本（**脱敏后**）
- `anti-crawl-eval.md` —— 反爬强度评估结论（限频 / UA / Cookie / 验证码 / 风控 + **L 等级**）
- `filter-rules.md` —— 冗余请求过滤规则（用于后续自动化抓包脚本）

#### 2.5.5.0 bb-browser 安装与 MCP 配置（v2.11.1 新增）

bb-browser 安装与 MCP 接入是 v2.10.0 缺失的实操环节，本节补全。

**前置要求**：
- **Node.js ≥ 18**（bb-browser 是 ESM 模块，Issue #10 报告 < 18 时 daemon 启动失败）
- 网络可访问 `registry.npmjs.org`（postinstall 拉原生二进制需要）

**安装方式（双轨 fallback）**：

| 方式 | 命令 | 适用场景 |
|:-----|:-----|:---------|
| **A. 全局安装（推荐）** | `npm install -g bb-browser` | 网络通畅，默认首选 |
| **B. 本地 + npx（fallback）** | `npm install bb-browser && npx bb-browser ...` | 全局安装 SSL 错误（Issue #6：raw.githubusercontent.com 443 被墙）时 |

**已知安装/启动 bug（v2.11.1 文档化）**：

| 问题 | 现象 | 触发条件 | 处理 |
|:-----|:-----|:---------|:-----|
| `Cannot find package '@bb-browser/daemon'` | daemon 启动失败（Issue #10） | tsup 打包 bug，daemon 子包未正确 bundle | 升级到 0.11.6+；或 `npm rebuild bb-browser` |
| `Failed to connect to raw.githubusercontent.com:443` | 安装 postinstall 失败（Issue #6） | 网络环境拦截原生二进制下载 | 切到方案 B（本地 + npx） |

**MCP server 配置（接入 Claude Code）**：

```json
{
  "mcpServers": {
    "bb-browser": {
      "command": "bb-browser",
      "args": ["daemon", "--mcp"]
    }
  }
}
```

> 写入 `~/.claude/mcp_servers.json` 后重启 Claude Code。**全局安装**用 `"command": "bb-browser"`；**本地安装**用 `"command": "npx", "args": ["bb-browser", "daemon", "--mcp"]`。

**daemon 默认端口**：
- `localhost:9001`（bb-browser daemon）
- `localhost:9222`（Playwright 用户 Chrome CDP）
- **两端口独立，**不冲突**；daemon 启动后无需额外配置端口。

**验证步骤**：

```bash
# 1. CLI 可用性
bb-browser --version   # 应输出 0.11.6+

# 2. daemon 启动状态
bb-browser status       # 应输出 daemon running

# 3. adapter 列表
bb-browser site --list  # 列出 35+ 可用 adapter

# 4. MCP endpoint 联通（可选）
curl http://localhost:9001/mcp -X POST -d '{}'  # 应返回 MCP 协议响应
```

**任一步失败** → 视为「bb-browser unavailable」，按铁律 #10 回退 v2.9.5 原链路。

---

#### 2.5.5 bb-browser 集成策略（v2.10.0 新增，按规范 §2.5.5）

bb-browser（[epiral/bb-browser](https://github.com/epiral/bb-browser)）是可选增强依赖，**不是本技能的硬依赖**。安装后可通过 CLI、MCP server 和 site adapter 提供**站点级导航、结构化内容读取及常见操作**；未安装、daemon 未运行、目标站点未适配或版本不兼容时，**必须完整回退 v2.9.5 的 Chrome CDP + Playwright + popup-handler.py 链路**。

**安装**：

```bash
npm install bb-browser
```

**接管预检阶段先运行**：

```bash
bb-browser status
```

命令可用且 daemon 正常时，**优先使用 adapter**；需要 MCP 时按 bb-browser CLI 帮助启动：

```bash
bb-browser daemon --mcp
```

**已知 adapter 覆盖**：GitHub、Twitter/X、Reddit、V2EX，以及其他 35+ 平台；**实际可用列表必须以当前安装版本输出为准**。**国内站点或未覆盖项目需自写 adapter**，不得假设所有站点均受支持。

**与 §2.5.1 接管预检协作**：

- 先检查 `bb-browser status`
- 再检查 `localhost:9222` 和目标 tab（§2.5.3 早检测）
- bb-browser 与 Playwright **应连接同一用户 Chrome / CDP 会话**
- 与 §2.5.2 接管粒度一致，**优先 L2 已打开目标 tab**，其次 L3 在用户 context 新开 tab，**禁止新建独立 context**

**与 §2.7 弹窗协同**：

- adapter 通常可处理登录前导航或公开入口，**但不替代 `popup-handler.py`**
- 仍须先清理 D.1-D.5 弹窗；D.6-D.8 **必须截图并询问用户**

**置信度联动（v2.10.0 增强）**：

- adapter 命中后，**接口线索还要由 Playwright / `curl_cffi` 实测并保存响应**
- 验证通过后置信度自动升为 `[🎯]`（详见 §2.3 表格）
- adapter 命中但未实测 → 只能标 `[⚠️]`，**不得直接升 `[🎯]`**

**职责边界**：

- **adapter**：站点级导航 / 内容入口 / 结构化操作
- **Playwright**：CDP 会话内的网络实测 / DevTools 抓包 / 浏览器自动化
- **`popup-handler.py`**：通用 DOM 弹窗 / 浏览器原生权限 / 合规询问

---

#### 2.5.5.1 bb-browser + Playwright 共享 Chrome CDP 实操（v2.11.1 新增）

bb-browser daemon 与 Playwright `connect_over_cdp` 共享同一用户 Chrome 是 v2.10.0 缺失的实操细节。本节明确启动顺序、端口分配、异常接管与验证步骤。

**启动顺序（严格，不可乱序）**：

```bash
# 第 1 步：用户先启动 Chrome 调试模式（铁律 #8 前置）
# Windows
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\ChromeProfile"
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
# Linux
google-chrome --remote-debugging-port=9222

# 第 2 步：启动 bb-browser daemon（占用 9001 端口，不影响 9222）
bb-browser daemon --mcp &

# 第 3 步：Playwright attach 同一 Chrome（9222 端口）
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://localhost:9222')
    ctx = browser.contexts[0]  # 复用用户 context（铁律 #8）
    page = ctx.pages[0]
    print('attached:', page.url)
"
```

**端口分配（互不冲突）**：

| 端口 | 占用方 | 作用 |
|:-----|:-------|:-----|
| `9222` | 用户 Chrome | CDP endpoint（Playwright `connect_over_cdp` 目标） |
| `9001` | bb-browser daemon | MCP endpoint + adapter 调用入口 |
| 其他（9002+） | bb-browser adapter | 多 adapter 并行时占用 |

**daemon 异常时 Playwright 接管顺序**：

```bash
# 1. 检测 daemon 是否健康
curl http://localhost:9001/health  # 5xx / 无响应 → 异常

# 2. daemon 异常时，先尝试重启
bb-browser daemon stop
bb-browser daemon --mcp &

# 3. 重启失败 → 完全回退 v2.9.5（铁律 #10）
#    此时只靠 Playwright + popup-handler.py，bb-browser 标记为 unavailable
```

**共享 Chrome CDP 验证（必走，4 步全部通过）**：

```bash
# 验证 1：Chrome 9222 端口存活
curl http://localhost:9222/json/version | grep "webSocketDebuggerUrl"

# 验证 2：bb-browser 9001 端口存活
curl http://localhost:9001/health

# 验证 3：两者能看到同一 tabs 列表
curl http://localhost:9222/json | jq '.[].url'         # Chrome tabs
curl http://localhost:9001/tabs | jq '.[].url'         # daemon 视角 tabs

# 验证 4：Playwright 能 attach 且复用用户 context
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp('http://localhost:9222')
    print('contexts:', len(b.contexts), 'pages:', sum(len(c.pages) for c in b.contexts))
    # 期望：contexts=1（用户已有），pages≥1（用户已开 tabs）
"
```

**4 步任一失败** → bb-browser 与 Playwright 未真正共享 Chrome，**禁止**进入 §2.0.5 模式 A 的 bb-browser 增强流程，强制回退纯 Playwright 链路。

**反模式（v2.11.1 新增）**：

- ❌ **daemon 未启动就调用 adapter 命令** —— 必须 `bb-browser status` 确认 daemon running 再调
- ❌ **Playwright `browser.new_context()` 新建独立 context** —— 违反铁律 #8，daemon 视角下看不到该 context
- ❌ **daemon 异常时反复重启超过 3 次** —— 第 4 次直接回退，不再尝试
- ❌ **共享验证 4 步未全部通过就启用 adapter** —— 4 步任一失败 = 未真正共享 = 走原链路

---

### 3. 决策点 · 是否进入逆向

| 反爬评估结果 | 走向 |
|:------------|:-----|
| **可直采**（明文 + 无强反爬） | 跳过阶段 4，直接进入阶段 5 |
| **简单处理**（编码/固定密钥） | 跳过阶段 4 主体，直接进入阶段 5，编码逻辑在阶段 5 一并封装 |
| **需逆向**（动态签名 / 加密 / 混淆） | 进入阶段 4 |

**强制要求**：无论是否进入逆向，`02-interfaces/api-inventory.md` 和 `anti-crawl-eval.md` 都必须完整产出。

---

### 4. 逆向攻坚（按《爬虫分析规范》§7-11）—— 仅需逆向时执行

**App 类前置复杂度评估**（**铁律**）：进入 APP 逆向前必告知用户：
- 需 frida + 脱壳工具 + SSL Pinning 绕过（如有）
- 预计耗时：简单 sign = 1-2 天；RSA/AES + so 层 = 1-2 周；深度混淆 + 设备指纹 = 数周+
- 成本评估：是否值得投入？或考虑替代方案（人工打码/购买数据/官方 API）？

**执行要点**（**详细方法论见规范 §7-11**）：
- **Web JS 逆向**（规范 §7-9）：关键字搜索 → XHR 断点 → Hook 定位 → 混淆识别（5 类 + AST）→ 补环境（vm2/jsdom）→ **路径 A：Python 纯复现（默认首选，用 `pycryptodome` / `hashlib` / `hmac` / `gmssl`，不依赖 Node）** → 路径 A 失败才走 **路径 B：Node 调用原始 JS（`PyExecJS2` / `subprocess` 调 `node script.js`）** → **≥ 3 组样本校验**
- **APP 逆向**（规范 §10）：**脱壳**（FRIDA-DEXDump/FART）→ **SSL Pinning 绕过**（objection 首选 / frida 自写 / justtrustme）→ 静态分析（jadx）→ frida Hook（最有效）→ so 层（Ghidra，极难）
- **风控与验证码**（规范 §11，铁律 #7）：L1-L5 难度分级 + 验证码类型应对（**AI 主动解决，不得建议人工**）+ 设备指纹模拟（默认已开 `playwright-stealth`）

**产出**（落到 `03-reverse/`）：
- `algo-restore.md` —— **加密算法还原报告**（定位过程 + 算法说明 + 验证结果，覆盖 Web/APP 全部路径）
- `restored-js/` —— 还原后的 JS 片段（Web 逆向）
- `hooks/` —— frida hook 脚本（**Web + APP 全套**，含 SSL Bypass）
- `verification.md` —— **≥ 3 组样本交叉验证记录**（不同输入值的还原结果对比）
- `app-unpack-notes.md`（**仅 APP 类**）—— 脱壳 + SSL Pinning 绕过的完整操作记录

**正确性铁律**：
- ❌ 不得只验证 1 组样本就声称还原成功
- ❌ 不得跳过验证直接进入阶段 5
- ❌ APP 逆向不得跳过 SSL Pinning 绕过就声称"逆向失败"（极可能是 pin 问题，不是算法问题）
- ❌ 不得在没拿到 ≥ 3 组 sign 值的情况下声称算法已还原

### 4.5 风控/滑块专项（v2.9.3 新增）

**触发条件**：`02-interfaces/anti-crawl-eval.md` 命中 **L3+ 风控**，或阶段 2 抓包发现滑块/点选/图形验证码。

**三步走（递进，不得跳级）**：

1. **指纹防御**（默认已开，无需额外动作）：`playwright-stealth` + UA/视口/时区随机化 + 行为伪装 + Cookie 持久化
2. **AI 主动解决验证码**（铁律 #7）：滑块 → 轨迹模拟 + OpenCV 缺口识别；点选 → OCR 识别 + 行为轨迹拟合；图形验证码 → OCR + 打码平台；**不得以"难以绕过"中断**
3. **接管本机浏览器**（铁律 #8 + v2.9.5 §2.5 完整 SOP）：
   - **前置预检**：检测 `localhost:9222` 端口（§2.5.1，AI 接到任务第一个动作）
   - **接入**：`p.chromium.connect_over_cdp("http://localhost:9222")`
   - **复用 context**：`browser.contexts[0]`（保留登录态，**禁止 `browser.new_context()`**）
   - **早检测**：识别目标域是否已在用户的 tabs 中（§2.5.3，主动提示接管现有 tab）
   - **接管粒度**：按 L1 整个浏览器 / L2 特定 tab / L3 新开 tab（保留 cookie）分级选择（§2.5.2）
   - **接管后第一件事**：清理弹窗（§2.7，popup-handler.py `cleanup_all()`）
   - **验证**：列出当前 tabs 让用户确认接管正确

**产出**（落到 `03-reverse/`，追加）：
- `anti-bypass-notes.md` —— 指纹策略 + 验证码解决过程 + 接管记录（含命令、响应、验证 ≥ 3 组）+ **接管粒度 + 早检测结果**（v2.9.5 新增）

**何时升级到 §5**：三步走中**第 2 步（AI 主动解决）或第 3 步（接管浏览器）至少走通 1 步**，能拿到 ≥ 3 组实测数据（**第 1 步指纹防御默认已开，不算"走通"**）

---

### 5. 模块化封装（轻量版）

**封装目标**：产出可独立 `import` 复用的纯函数模块，**严格遵循《爬虫规范》命名/分层规范**（即使不是完整骨架）。

**自动化框架选型**（v2.9.4 新增，**`AskUserQuestion` 必问**）：

> 分析阶段（§2-4）固定用 **Playwright-Python**；封装阶段（§5）按目标场景让用户选框架：

| 框架 | 核心优势 | 核心劣势 | **何时选** |
|:-----|:---------|:---------|:-----------|
| **Playwright-Python** | CDP 完整、API 现代、Python 生态最广、stealth 生态成熟 | 国内社区相对小、接管浏览器需手动 `connect_over_cdp` | **海外项目 + 复杂交互 + 工程化**（默认） |
| **DrissionPage** | 国产、**内置接管浏览器**、**内置反检测**（无需 stealth）、对国内站点适配好 | 海外生态弱 | **国内项目**（小红书/抖音/淘宝/1688）+ 快速接管用户本机 Chrome |
| **seleniumbase** | UC Mode（undetected-chromedriver）成熟、国外生态、自带 CDP 工具 | 基于 Selenium 老旧、API 兼容性差 | **需要 Selenium 兼容 + UC 反检测的海外项目** |

**示例问法**（必走）：

> 请问封装阶段用哪个自动化框架？
> - A. Playwright-Python（默认，海外项目 + 复杂交互）
> - B. DrissionPage（国内项目，内置接管 + 反检测）
> - C. seleniumbase（需要 Selenium 兼容 + UC 反检测）

**产出**（落到 `04-modules/{module}/`）：

```
04-modules/{module}/
├── __init__.py              # 暴露对外可复用接口
├── functions.py             # 核心函数（可独立 import）
├── constants.py             # 常量（Redis Key、URL 模板、Header 模板）
├── README.md                # 使用说明：哪些函数可独立复用 + 复用示例
└── verify.py                # 复用前的快速验证脚本
```

**规范遵循**：
- 命名：`crawl_functions.py` 风格统一（小写 + 下划线 + `crawl_` 前缀可省略）
- 目录分层：`apps/{module}/` 模式保留，便于后续 `mcpowers-init` 升级为完整骨架
- 注释：每个函数 docstring 5 字段齐全（按 `接口契约规范.md`，即使不是接口也按此标准）

**何时升级为完整骨架**：
- 用户在阶段 7 选择「落地为完整项目」时 → `mcpowers-init` 调用，**自动把** `04-modules/{module}/functions.py` **复制到** `apps/{module}/crawl_functions.py`，并按《爬虫规范》§2.4 补全其余 6 个文件

**不封装的内容**（YAGNI）：
- ❌ 不写 `crawl_wrappers.py` / `crawl_loggers.py` / `crawl_retry_conditions.py` 等需要工程骨架支撑的文件
- ❌ 不写 Session/代理/指纹管理（属于 `mcpowers-init` 范畴）
- ❌ 不写 Redis 队列/任务调度（属于 `mcpowers-init` 范畴）

---

### 6. 沉淀案例（v2.7.0 铁律）

**强制要求**：阶段 5 完成后**必须**沉淀案例，不可跳过。

**产出**：
- `05-case-study.md`（按《爬虫分析规范》附录 C 格式）
- 章节：目标 / 加密参数 / 定位过程 / 还原方案 / 可复用代码入口 / 关键决策点

**沉淀到体系**（**v2.7.0 新增联动**）：
- `AskUserQuestion` 让用户确认：是否把案例追加到 `skills/mcpowers-shared/docs/技术规范/爬虫分析规范.md` 附录 C？
- 用户同意 → 本次变更必须同步更新：
  1. `爬虫分析规范.md` 附录 C 追加 1 条
  2. `爬虫分析规范.md` frontmatter `last_updated` 更新
  3. 跑 `bash scripts/check-readme-sync.sh` 确认通过
- 用户拒绝 → 仅留本地 `05-case-study.md`，不污染规范

**v2.6.0 历史教训对应**：避免「规范进了体系但不触发」（案例必须沉淀，否则下次遇到同类还要重新逆向）。

---

### 7. 落地决策（联动 `mcpowers-init` / `mcpowers-feat` / `mcpowers-extract`）

**`AskUserQuestion` 询问**：

| 选项 | 触发链路 |
|:-----|:---------|
| **A. 落地为完整爬虫项目** | 跳 `mcpowers-init`，传入 `04-modules/{module}/` 路径，让 init 按《爬虫规范》生成完整骨架 + 自动 copy `functions.py` 到 `apps/{module}/crawl_functions.py` |
| **B. 继续二次开发** | 跳 `mcpowers-feat`，基于 `04-modules/` 加业务功能 |
| **C. 仅保留轻量产物** | 结束，建议用户把 `{slug}-crawler-reverse/` 加入 git 自管理 |
| **D. 提炼逆向层为跨项目公共库** | 跳 `mcpowers-extract`，把 `04-modules/` 里的逆向层（sign/加解密/hook/补环境）提炼为独立可 import 模块 + CLI 脚本，供同类站点/同厂加密的其他项目反复复用 |

**不主动跳的依据**：v2.6.0 YAGNI 教训 —— 不在 description 写死跳转，避免破坏本技能触发灵敏度。

---

## 何时中断并询问用户

- 输入不明确（"帮我爬 X"但 X 未指定 → `mcpowers-brainstorm`）
- 加密类型无法判断（需要更多请求样本）
- **APP 逆向**：超过简单 sign 阈值 → 主动告知成本，让用户决策是否继续
- **风控对抗**：识别到 L5 风控引擎（服务端实时决策）→ 主动告知难以绕过，建议降级方案
- **脱壳失败**：通用脱壳工具无效，可能用了小众加固 → 询问用户是否有该厂商脱壳工具线索
- **SSL Pinning 绕过失败**：所有通用方案都失效 → 询问用户是否接受重新打包方案
- 涉及合规风险（robots.txt 禁止 / 需登录他人账号 / 涉及个人信息）
- 阶段 5 封装粒度有歧义（"封装哪些函数"边界不清）
- **联动 init 时**：目标路径冲突（已存在同名项目）

---

## 反模式（禁止）

- ❌ 不做侦察直接逆向（违反 KISS，浪费时间）
- ❌ **不自动化分析，依赖人工抓包** —— 业务接口往往需要触发特定交互才出现，必须用 Playwright/mitmproxy 脚本化（见规范 §2.3）
- ❌ **不过滤冗余请求** —— 抓包结果含大量 CDN/上报/字体，必须按规范 §3.1 规则过滤
- ❌ **不做风控识别直接逆向** —— 风控参数是反爬核心，必须按规范 §4.6 + §6.1 列出 L1-L5 难度等级
- ❌ **APP 逆向跳过 SSL Pinning 绕过** —— 抓不到包 90% 是 pin 问题，不是算法问题
- ❌ **APP 逆向跳过脱壳** —— 加固 APP 直接 jadx 看的是壳代码，不是业务代码
- ❌ **混淆代码不 Hook 直接读** —— 用 Hook 看入参/出参比读混淆代码快 10 倍
- ❌ **Python 复现失败就放弃** —— 路径 A 失败时**必须**走路径 B（Node 调用原始 JS），不得因"Python 复现困难"就跳过
- ❌ 逆向结果不验证（参数还原错误导致全量数据报废）
- ❌ 一次性逆向所有参数（先验证核心参数，正确后再扩）
- ❌ 产物目录散落在工作区不按 `{slug}-crawler-reverse/` 命名（违反 DRY，下次找不回）
- ❌ 阶段 5 不按《爬虫规范》命名/分层（违反规范一致性）
- ❌ 逆向成功后不沉淀案例（违反"案例库归档约定"，v2.6.0 历史教训）
- ❌ 轻量封装写成完整骨架（YAGNI 违反，重复 `mcpowers-init` 工作）
- ❌ 联动 init 时强行覆盖已有项目（破坏用户已有资产）
- ❌ **默认开新浏览器窗口**（v2.9.3 新增）—— 必须 `connect_over_cdp` 复用用户本机 Chrome，禁止每次新开 Playwright 窗口
- ❌ **裸用 `requests` 直连 API**（v2.9.3 新增）—— TLS 指纹（JA3）一秒被风控识别，必须用 `curl_cffi.requests` 等带 TLS 指纹的框架
- ❌ **自动化代码不开启指纹伪装**（v2.9.3 新增）—— `navigator.webdriver` / WebGL / canvas 指纹一眼穿帮，必须默认开启 `playwright-stealth`
- ❌ **遇到滑块/验证码就建议人工**（v2.9.3 新增）—— 必须 AI 主动解决（轨迹模拟 / OpenCV / OCR / 打码平台）
- ❌ **用 Node 作为默认语言**（v2.9.3 新增）—— Python 优先，Node 仅作 §4 路径 B 的 fallback
- ❌ **凭接口名/参数名/字段名在 `api-inventory.md` 凭空写结论**（v2.9.3 新增）—— 必须用 `curl_cffi` / `Playwright` 实测一次并留响应样本到 `02-interfaces/responses/`
- ❌ **跳过接管预检，直接 `connect_over_cdp`**（v2.9.5 新增）—— 必须先检测 `localhost:9222`，未检测到时 AskUserQuestion 4 选 1 让用户选择启动方式，**禁止擅自 `launch()`**
- ❌ **跳过弹窗清理直接抓包**（v2.9.5 新增）—— Cookie/Notification/App 下载引导等弹窗会遮挡真实业务，抓到的是弹窗接口而非核心业务接口；必须先 `popup-handler.py cleanup_all()`
- ❌ **自动登录 / 自动确认年龄 / 自动同意合规条款**（v2.9.5 新增）—— 登录墙 / 年龄验证 / 合规同意三类弹窗必须截图后 AskUserQuestion，**绝不自动点**，避免合规风险和误登录
- ❌ **协作模式不切换就死磕**（v2.9.5 新增）—— A 模式连续 3 次未识别核心接口必须暂停切到 B/C/D，**禁止"找不到就算不存在"**
- ❌ **`api-inventory.md` 留 `[❓]` 低置信度条目**（v2.9.5 新增）—— 阶段 2 结束前所有 `[❓]` 必须转 `[🎯]`（实测）或 `[⚠️]`（明确无意义）或删除
- ❌ **未检测 `bb-browser status` 就假设 adapter 可用**（v2.10.0 新增）—— 必须先探测 CLI / daemon；未安装 / 不可用 / 不兼容时回退 v2.9.5 原链路，**禁止**"看到 github 就直接调 bb-browser"
- ❌ **把 bb-browser 当成 popup-handler.py / Playwright 的替代品**（v2.10.0 新增）—— adapter 负责**站点级操作**，Playwright 负责**网络实测**，`popup-handler.py` 负责**通用弹窗与合规询问**，三者职责不可混用
- ❌ **adapter 命中后跳过实测直接标 `[🎯]`**（v2.10.0 新增）—— adapter 仅提供结构化线索，必须经 Playwright / `curl_cffi` 实测验证后才能升 `[🎯]`，**禁止** adapter 命中 = 自动高置信度

---

## 完成后自检清单

### 接口分析阶段
- [ ] `01-target-profile/` 已填写（域名/包名/IP 段/技术栈指纹）
- [ ] **v2.9.5 接管预检已完成**（§2.5.1 检测 `localhost:9222` + 早检测目标 tab）
- [ ] **v2.9.5 协作模式已选**（§3.0.2 AskUserQuestion 4 选 1，用户选了哪种模式）
- [ ] **v2.9.5 弹窗已清理**（§2.7 `cleanup_all()`，D.6-D.8 询问类已截图+询问）
- [ ] **抓包已自动化**（Playwright 或 mitmproxy 脚本，非纯人工）
- [ ] **冗余请求已过滤**（CDN/上报/字体/心跳已剔除，`02-interfaces/filter-rules.md` 已写）
- [ ] `02-interfaces/api-inventory.md` 完整（URL/Method/参数/响应/加密判定/**置信度 🎯/⚠️/❓** v2.9.5 新增列）
- [ ] **`❓` 已收敛**（v2.9.5 新增：阶段 2 结束前所有 `[❓]` 必须转 `[🎯]` 或删除）
- [ ] `02-interfaces/anti-crawl-eval.md` 已写（限频/UA/Cookie/验证码/风控）
- [ ] **风控参数已识别**（sign/token/fingerprint 等，含 L1-L5 难度等级判定）

### 逆向攻坚阶段（如执行了逆向）
- [ ] Web：`03-reverse/web-sign-restore.md` 含定位过程 + 算法说明 + ≥ 3 组样本验证
- [ ] Web：`03-reverse/web-hooks/` 含浏览器 Hook 脚本
- [ ] APP：`03-reverse/app-unpack-notes.md` 含脱壳 + SSL Pinning 绕过记录
- [ ] APP：`03-reverse/hooks/` 含 frida 脚本（加密函数 Hook + SSL Bypass）
- [ ] `03-reverse/verification.md` 含 ≥ 3 组样本交叉验证
- [ ] **≥ 3 组 sign 复现值与抓包结果一致**（不是 1-2 组，是 3+）

### 封装与沉淀
- [ ] `04-modules/{module}/functions.py` 函数 docstring 5 字段齐全
- [ ] `04-modules/{module}/README.md` 含复用示例（≥ 2 个 import 用例）
- [ ] `05-case-study.md` 已写（含目标/参数/定位/方案/可复用代码入口/关键决策点）
- [ ] **`05-case-study.md` 已询问用户是否沉淀到《爬虫分析规范》附录 C**
- [ ] **如选择沉淀**：本次 commit 已同步更新 `爬虫分析规范.md` 附录 C + frontmatter `last_updated`

### 联动与收尾
- [ ] 阶段 7 联动决策已与用户确认（A/B/C 三选一）
- [ ] **如选择 A**：已确认目标路径无冲突，再跳 `mcpowers-init`
- [ ] 跑过 `bash scripts/check-readme-sync.sh` 通过

### v2.9.3 新增 · 策略与防御自检

- [ ] **默认 Python**（非 Node/JS）
- [ ] **分析阶段用 Playwright-Python**（非 Selenium/裸 Playwright-Node）
- [ ] **封装阶段已 `AskUserQuestion` 让用户选框架**（DrissionPage / seleniumbase / Playwright-Python 三选一）
- [ ] **协议请求用 `curl_cffi`**（非裸 `requests`）
- [ ] **已开启 `playwright-stealth` 指纹伪装**（分析阶段默认开；DrissionPage/seleniumbase 默认内置反检测，无需手动装 stealth）
- [ ] **行为模式已随机化**（滚动/点击/鼠标轨迹）
- [ ] **遇验证码/滑块已主动解决**（非"建议人工"）
- [ ] **浏览器接管用 CDP attach**（DrissionPage 内置接管 / Playwright `connect_over_cdp`）（非新开窗口）
- [ ] **`api-inventory.md` 中每个标定的核心接口都有 `02-interfaces/responses/` 下的实测响应样本**（非凭空判断）

### v2.9.5 新增 · 接管 + 弹窗 + 协作 + 置信度自检

- [ ] **接管预检已执行**（§2.5.1 `probe_chrome_cdp()` 返回 `available: True/False`，未检测到时给了 4 选 1 AskUserQuestion）
- [ ] **早检测已提示**（如目标 tab 已在用户浏览器中，§2.5.3 主动给了 3 选 1 AskUserQuestion）
- [ ] **接管粒度已选**（§2.5.2 L1 整个浏览器 / L2 特定 tab / L3 新开 tab）
- [ ] **`connect_over_cdp` 用了用户 context**（`browser.contexts[0]`，**禁止 `browser.new_context()`**）
- [ ] **弹窗已清理**（`cleanup_all()` 调用，D.6-D.8 询问类已截图 + 询问用户，未自动点）
- [ ] **协作模式已选**（§3.0.2 AskUserQuestion 4 选 1 阶段 2 开头已问）
- [ ] **`❓` 已收敛**（阶段 2 结束前 `api-inventory.md` 中无 `[❓]` 条目，全部转 `[🎯]` 或 `[⚠️]` 或删除）
- [ ] **模式切换点已记录**（如果 A 模式 3 次失败切到 B/C/D，已在 `01-target-profile/` 记录切换原因）
- [ ] **`api-inventory.md` 模板有"置信度"列**（v2.9.5 模板：🎯/⚠️/❓ 三档 + 响应样本列）

### v2.10.0 新增 · bb-browser 集成自检

- [ ] **已执行 `bb-browser status`**（v2.10.0 必走），并记录 `installed` / `running` / `unavailable` 状态
- [ ] **目标站点有 adapter 时已优先调用**（`bb-browser <site> <action>`）；未命中时已回退 Playwright 原链路
- [ ] **bb-browser 与 Playwright 使用同一 Chrome CDP 用户 context**（**禁止** `browser.new_context()` / 分别创建独立浏览器）
- [ ] **adapter 提供的接口线索已经过 Playwright / `curl_cffi` 实测**，并保存响应样本到 `02-interfaces/responses/`
- [ ] **bb-browser 未安装 / daemon 异常时**，v2.9.5 接管、弹窗、协作和置信度流程**仍可独立完成**，无任何中断

### v2.11.1 新增 · bb-browser 实操自检

- [ ] **Chrome CDP 共享验证 4 步全部通过**（§2.5.5.1：9222 + 9001 双端口存活 + tabs 一致 + Playwright attach 复用 `browser.contexts[0]`）
- [ ] **adapter 调用日志已保存**（`01-target-profile/bb-browser-calls.log`，每条记录时间戳 + adapter 名 + action + 状态 + 耗时 + urls 数量）
- [ ] **`api-inventory.md` 已加「来源」列**（取值 `adapter` / `Playwright` / `curl_cffi` / `adapter+Playwright`，可区分结构化线索 vs 实测证据）
- [ ] **adapter 失败 4 类判定已检查**（超时 / 命令不存在 / 返回空结构 / 字段不匹配），任一未检查 = 流程不合规
- [ ] **daemon 异常重启未超过 3 次**（v2.11.1 硬上限：第 4 次直接回退，不再尝试）

---

## 工具与手法

> **v2.7.0 设计**：工具速查表与具体手法已统一收纳到《爬虫分析规范》各章节，避免与技能编排重复。**用本技能时按需 Read 规范对应章节即可**：
>
> | 关注点 | 读规范的哪一段 |
> |:-------|:--------------|
> | 抓包/代理/自动化/设备框架/浏览器复用/协议层 | §2 抓包与工具 + §2.4 设备与运行时框架 + §2.5 浏览器复用策略（v2.9.3 + **§2.5.5 bb-browser 集成 v2.10.0**）+ §2.6 协议层请求框架（v2.9.3） |
> | 过滤冗余/筛选核心接口 | §3 接口定位与筛选 |
> | 请求结构/Header/风控参数识别 | §4 请求结构分析（含 §4.6 风控参数） |
> | 反爬难度 L1-L5 评估 | §6 反爬强度评估（含 §6.1 L 分级） |
> | 加密定位/Hook/混淆识别 | §7 加密参数定位 + §8 Web JS 逆向 |
> | 算法复现/补环境/正确性校验 | §8.3-8.5 补环境与复现 + §9 参数还原 |
> | 脱壳/SSL Pinning/frida/so | §10 APP 逆向（含 5 子节） |
> | 验证码/设备指纹/风控 | §11 验证码与风控应对 |
> | 完整工具清单 | 附录 A（含 A.1-A.8） |

---

## 关联技能

- **上游**：`mcpowers-brainstorm`（输入不清时）/ `mcpowers-prd`（先写需求）
- **下游**：
  - `mcpowers-init`（阶段 7 选项 A，落地完整骨架）
  - `mcpowers-feat`（阶段 7 选项 B，二次开发）
  - `mcpowers-extract`（阶段 7 选项 D，把逆向层提炼为跨项目公共库）
  - `mcpowers-code-review`（阶段 5 自审）
  - `mcpowers-git-commit`（提交前）
- **同级**（易混淆）：
  - `mcpowers-init` —— 本技能的「落地」目标，职责不同
  - `mcpowers-feat` —— 在已有项目加功能，不做陌生目标分析
  - `mcpowers-bugfix` —— 已有爬虫出问题时的修复
  - `mcpowers-optimize` —— 已有爬虫性能优化