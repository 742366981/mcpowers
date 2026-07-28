---
title: 爬虫Web逆向规范
type: tech-spec
applies_to: [crawler-reverse, web]
priority: recommended
version: 2.19.0
last_updated: 2026-07-28-v2.19.0
description: Web JS 反混淆、补环境、算法复现与正确性校验的方法论；与 `mcpowers-reverse-web` 1:1 对应。与《爬虫工具与抓包规范》§3 浏览器复用配合使用抓包；以《爬虫分析规范》§9.4 模块真实可用性验收收尾。Web 逆向必读；非 Web 任务不读。
---

# 爬虫Web逆向规范

> **本文档定位**：本规范是《爬虫分析规范》v2.14.0 起拆分出的 **Web 逆向专用册**，
> 与 `mcpowers-reverse-web` 1:1 对应。
>
> - 公共方法论（接口分析 / 反爬评估 / 验证码与风控 / 真实可用性验收）
>   见主《爬虫分析规范.md》。
> - 抓包 / CDP 接管 / bb-browser 等运行时复用见《爬虫工具与抓包规范.md》§3+§6。
> - 工具与脚本角色边界（adapter / Playwright / popup-handler）见工具册 §6.1。
> - **v2.19.0 新增**：Web 任务固定起手式见工具册 §8.6 / §8.7 与
>   `reverse-analysis-session.py`（init → web-start → web-stop）。
>
> **外部接管资源所有权铁律**：本规范的 §2 涉及接管用户 Chrome 时必须遵守主《爬虫
> 分析规范》§1.3 铁律——**外部接管资源不可关闭**。

---

## 0. 索引

| 章 | 内容 | 关联规范 |
|:---|:-----|:---|
| §1 | 加密参数定位（关键字 / 断点 / 调用栈 / Hook） | — |
| §2 | Web JS 逆向（混淆 / 反混淆 / 补环境 / 算法还原） | 《爬虫工具与抓包规范》§3 |
| §3 | 参数还原与复现（校验流程 / 工程化产出 / 边界情况） | 《爬虫分析规范》§9.4 |
| §4 | 跨端指纹（Web + Hybrid 共有 JS/Bridge 处理要点） | 《爬虫Hybrid逆向规范》 |

---

## §1. 加密参数定位

> **目标**：找到目标加密参数（如 `sign`）到底由哪个 JS 函数生成。

### §1.1 关键字搜索（**第一手**）

在 JS 源码（Sources 面板 / 静态资源 / 反混淆后代码）中搜索：
- `sign`、`signature`、`encrypt`、`encryptData`、`aes`、`md5`、`rsa`、
  `hmac`、`sha`、`base64`
- 自定义头名：`x-sign`、`x-token`、`x-ticket`

**技巧**：
- 用正则：`(sign|signature|encrypt).{0,20}=`
- 全局搜索（Ctrl+Shift-F）
- 同时搜索 Network 里的请求体

### §1.2 XHR/Fetch 断点

1. Sources 面板 → 目标接口 URL 行打断点
2. 触发请求 → 浏览器自动停在断点
3. 看右侧 Call Stack，从断点往上跟栈 → 找到计算 sign 的函数

### §1.3 调用栈回溯

从请求触发点反向追溯：
- Network → Initiator 列（看是哪个 JS 触发的）
- Sources → Call Stack（多层调用）
- 在每层打 console.log，看 sign 值何时被计算

### §1.4 Hook 定位（**对混淆代码最有效**）

```javascript
// 注入到目标页面，Hook 常见加密函数
// 保存到 03-逆向攻坚/钩子/web-hook.js
const oldAES = window.CryptoJS.AES.encrypt;
window.CryptoJS.AES.encrypt = function(...args) {
    console.log('[HOOK AES]', JSON.stringify(args));
    debugger;  // 自动断点
    return oldAES.apply(this, args);
};
```

**注入方式**：
- Charles/Fiddler 替换响应（Map Local / Map Remote）
- mitmproxy response injector（`response.replace(...)`）
- Chrome Snippets（仅临时调试）

---

## §2. Web JS 逆向

### §2.1 混淆类型识别与还原

| 混淆类型 | 特征 | 应对 |
|:---------|:-----|:-----|
| **变量混淆** | `var _0x123abc = ...` | 重命名（VSCode + babel 插件） |
| **控制流平坦化** | switch-case 循环 | AST 反混淆（`babel/parser` + `traverse` + `generator`） |
| **字符串加密** | `"\\x65\\x6e\\x63"` | Hook `String.fromCharCode` / console.log 输出 |
| **死代码注入** | 大段永不执行的代码 | AST 静态分析剔除 |
| **自定义 VM** | 自解释字节码 | 极难，需 1-2 周分析 |

### §2.2 AST 反混淆思路

工具链（**首选**）：
```bash
npm install @babel/parser @babel/traverse @babel/generator @babel/types
```

基本流程：
1. `parser.parse(code)` → AST
2. `traverse(ast, visitor)` → 遍历节点（重命名变量、删除死代码）
3. `generator.generate(ast)` → 新代码

**现成工具**：
- `obfuscator-io-deobfuscator`（通用 obfuscator.io 反混淆）
- `js-deobfuscator`（基础还原）

### §2.3 补环境（**Node.js 执行原始 JS 时的常见障碍**）

> **核心问题**：原始 JS 在浏览器里有 `window` / `document` / `navigator`，
> Node 里没有 → 需补全。

**工具栈**：

| 工具 | 用途 |
|:-----|:-----|
| **vm2** | Node.js 沙箱（**首选**，安全 + 兼容） |
| **jsdom** | DOM 模拟（处理 window/document） |
| **canvas**（Node 包） | 模拟 Canvas API（Canvas 指纹场景） |
| 自写 stub | 兜底方案，按报错信息补全缺失对象 |

**常用补全对象**：`window`、`document`、`navigator`、`location`、
`localStorage`、`canvas`、`WebGL`、`AudioContext`、`screen`

**技巧**：先用浏览器跑一次，把所有用到的浏览器 API 输出到文件，再在 Node 里 stub。

### §2.4 算法还原与复现

**路径 A：Python 纯复现**（**推荐**，性能好、不依赖 Node）：

| 算法 | Python 库 |
|:-----|:---------|
| AES / DES / RSA | `pycryptodome` |
| 哈希 MD5/SHA | `hashlib` |
| HMAC | `hmac` 模块 |
| 国密 SM2/SM3/SM4 | `gmssl` |

**路径 B：Node/execjs 直接调用原始 JS**（最快但有运行时依赖）：
- `pip install PyExecJS2` 或 `subprocess` 调 `node script.js`
- 缺点：性能差、部署需 Node 环境

### §2.5 正确性校验（**铁律**）

- 取浏览器实际请求的 **≥ 3 个不同 sign 值**
- 用复现算法生成同样 sign，与抓包结果对比
- **必须 ≥ 3 组样本通过**，否则算法还原错误
- 详见 `mcpowers-crawler-reverse/SKILL.md` 阶段 4 自检清单

---

## §3. 参数还原与复现

> §2.4 已详述 Python/Node 双路径。本节强调**正确性校验流程**与**工程化产出**。
>
> §3.3 的模块真实可用性验收由主《爬虫分析规范》§9.4 统一维护，不在本册重复。

### §3.1 还原结果校验流程（**强制**）

```
抓包拿 5 组不同入参的 sign 值（标记 sign_real_1 ~ 5）
        ↓
用复现算法生成 sign_repro_1 ~ 5
        ↓
对比：sign_real_X == sign_repro_X ?
        ↓
  全等 → 还原成功（标记 ≥ 3 组）
  任意不等 → 算法还原错误，重新分析
```

### §3.2 工程化产出

- **代码位置**：`{slug}-crawler-reverse/04-模块封装/{module}/client.py`
- **接口形式**：纯函数（输入参数 → 返回 sign 值），无副作用
- **依赖管理**：`requirements.txt` 列出加密库（`pycryptodome`、`gmssl` 等）

### §3.3 边界情况

| 情况 | 表现 | 应对 |
|:-----|:-----|:-----|
| **时间戳依赖** | sign 与请求时间相关 | 算法接受 `_ts` 参数，复现时传当前时间 |
| **nonce 依赖** | sign 含一次性随机串 | 算法接受 `nonce` 参数，复现时生成新 nonce |
| **加密 Body** | 整个请求体是密文 | 复现加密逻辑（更复杂，需看 §2 算法） |
| **多 sign** | 一个请求有多个 sign 参数 | 逐一还原，每个独立验证 |

### §3.4 模块真实可用性验收（指向主册 §9.4）

**Web 任务的最终验收必须**走主《爬虫分析规范》§9.4：
1. 串行重复与冷启动（≥ 2 组输入 / 合计 ≥ 5 次 / ≥ 2 个 session）
2. 报文生命周期矩阵（原报文重放 / 动态参数重生成 / 跨 session 重放 / TTL）
3. 有界并发稳定性（2 → 5 递增，发现共享状态污染立即停止）
4. `验收报告.md` 最终状态 = **`PASS`** 才算 Web 模块可用

> 详见主《爬虫分析规范》§9.4，本册不重复列举；只声明 Web 逆向产物必须满足此门禁。

---

## §4. 跨端指纹（Web + Hybrid 共有的 JS / Bridge 处理要点）

> 当目标 Web 页面同时包含 Hybrid / WebView 容器（uni-app、RN、Capacitor），需要
> 区分 JS 层、Bridge 层、Native 层三个位置的入参/出参。

### §4.1 JS 层

- 复现 JS 业务逻辑（拼装、序列化、fetch/XHR）
- 注意：JSBridge 调用与原生 fetch 混在同一栈中，需用 Source Map 或控制流区分
- 单元测试样例：复现入参 → 调用 bridge → 在原生侧验证返回

### §4.2 Bridge 层

- 方法名 / 参数 / 返回 schema / 异步回调
- 线程与 session 绑定（hybrid 容器一般在主线程执行，但部分 RN 库在 worker thread）
- 关键：定位"JS 调用 bridge"还是"Native 主动回调 JS"——前者是参数生成路径，
  后者是状态推送

### §4.3 Native 层

- 当 bridge 调用仅传参而返回 sign/token 时，必须进入 Native 层
- Android/iOS 工具链：见《爬虫Android逆向规范》《爬虫IOS逆向规范》
- 优先 hook JNI / Keychain / Keystore 的读取边界而不是反编译整个 native 模块

### §4.4 与 Web / Hybrid 专职规范的协作

- 本规范仅讲"JS 层 + 部分 Bridge"的策略
- 完整 Bridge 与 Native 定位见《爬虫Hybrid逆向规范》§2
- 主逆向量在 Native 时直接转入 Android/iOS 专项

---

## §5. 与 Web/工具规范的引用关系

| 场景 | 主入口 | 必读章节 |
|:---|:---|:---|
| 浏览器抓包分析 | 工具册 §3（CDP 接管） | §3.1, §3.4, §3.5.1 |
| 弹窗处理 | 工具册 §4（弹窗字典） | §4.1, §4.4, §4.7-§4.14 |
| 协议直连替代浏览器 | 工具册 §5（协议层框架） | §5 curl_cffi |
| bb-browser 站点增强 | 工具册 §6 | §6.0, §6.1, §6.2 |
| Web JS 混淆还原 | 本规范 §2.1-§2.2 | §2.1, §2.2 |
| Node 补环境 | 本规范 §2.3 | §2.3 |
| 算法复现与校验 | 本规范 §3 | §3.1, §3.2 |
| 模块真实可用性 | 主册 §9.4 | 主册 §9.4 |
| 跨端 JS 处理 | 本规范 §4 + 《爬虫Hybrid逆向规范》§2 | 协作 |
