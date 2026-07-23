---
name: mcpowers-crawler-reverse
description: "爬虫逆向 / 加密参数还原 / 抓包分析 / 逆向工程 / JS 反混淆 / APP 逆向 / frida hook / SSL Pinning → 触发本技能。口语：帮我逆向这个网站,这个app怎么抓,sign怎么算,加密怎么破,JS被混淆了,我想爬X但有加密,请求参数看不懂,反爬太严了,滑块过不去,验证码怎么办,风控太严,指纹伪装,接管浏览器,默认 Python,Playwright,curl_cffi,DrissionPage,seleniumbase。English: reverse engineering, deobfuscation, frida hook, signature, mitmproxy, charles, fiddler, ssl pinning。能力：分析阶段 Playwright-Python 默认 + 指纹防御 + curl_cffi；封装阶段 DrissionPage/seleniumbase/Playwright 三选一（按用户场景选）；遇滑块/风控自研解决→接管本机浏览器（CDP attach）→不得开新窗口；每标定接口必须实测验证。边界：搭爬虫骨架→mcpowers-init；爬虫出bug→mcpowers-bugfix；性能优化→mcpowers-optimize。流程：输入URL/App→产物目录{slug}-crawler-reverse→接口分析→评估是否逆向→轻量封装→沉淀案例→联动init落地。"
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

**执行要点**（**详细方法论见规范 §1-6**）：
1. **抓包**：Web → DevTools / mitmproxy / Charles；APP → mitmproxy + 证书 + SSL Pinning 绕过（详见规范 §2 + §10.2）
2. **自动化分析**：用 **Playwright-Python**（默认启用 `playwright-stealth` 绕过 `navigator.webdriver` 等指纹）模拟用户行为触发懒加载接口（详见规范 §2.3）
3. **实测验证**（铁律 #9）：每标定一个核心接口后**必须用 `curl_cffi` / `Playwright` 实测一次**（带真实 header/cookie/参数），响应样本落到 `02-interfaces/responses/{slug}.json`；**禁止凭接口名/路径段/参数名在 `api-inventory.md` 直接写结论**
4. **过滤冗余**：剔除 CDN/上报/字体/心跳等（详见规范 §3.1）
5. **风控识别**：识别 sign/token/fingerprint 等关键参数 + L1-L5 难度分级（详见规范 §4.6 + §6.1）

**产出**（落到 `02-interfaces/`）：
- `api-inventory.md` —— 接口清单（URL、Method、参数、响应字段、是否加密、**风控难度 L1-L5**）
- `requests/` —— **核心业务接口的抓包样本**（curl / HAR 格式，**仅保留核心，去重**）
- `responses/` —— 关键接口的响应样本（**脱敏后**）
- `anti-crawl-eval.md` —— 反爬强度评估结论（限频 / UA / Cookie / 验证码 / 风控 + **L 等级**）
- `filter-rules.md` —— 冗余请求过滤规则（用于后续自动化抓包脚本）

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
3. **接管本机浏览器**（铁律 #8）：以上都失败时 `chrome --remote-debugging-port=9222` + `playwright.chromium.connect_over_cdp("http://localhost:9222")` 接入用户本机 Chrome，**不开新窗口**

**产出**（落到 `03-reverse/`，追加）：
- `anti-bypass-notes.md` —— 指纹策略 + 验证码解决过程 + 接管记录（含命令、响应、验证 ≥ 3 组）

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

---

## 完成后自检清单

### 接口分析阶段
- [ ] `01-target-profile/` 已填写（域名/包名/IP 段/技术栈指纹）
- [ ] **抓包已自动化**（Playwright 或 mitmproxy 脚本，非纯人工）
- [ ] **冗余请求已过滤**（CDN/上报/字体/心跳已剔除，`02-interfaces/filter-rules.md` 已写）
- [ ] `02-interfaces/api-inventory.md` 完整（URL/Method/参数/响应/加密判定）
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

---

## 工具与手法

> **v2.7.0 设计**：工具速查表与具体手法已统一收纳到《爬虫分析规范》各章节，避免与技能编排重复。**用本技能时按需 Read 规范对应章节即可**：
>
> | 关注点 | 读规范的哪一段 |
> |:-------|:--------------|
> | 抓包/代理/自动化/设备框架/浏览器复用/协议层 | §2 抓包与工具 + §2.4 设备与运行时框架 + §2.5 浏览器复用策略（v2.9.3）+ §2.6 协议层请求框架（v2.9.3） |
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