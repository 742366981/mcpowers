---
title: 爬虫Hybrid逆向规范
type: tech-spec
applies_to: [crawler-reverse, hybrid]
priority: recommended
version: 2.14.0
last_updated: 2026-07-27-v2.14.0
description: uni-app / React Native / Cordova / Capacitor / 自定义 WebView / JSBridge 的三层定位（JS / Bridge / Native）与接管 WebView 调试端口的实操。接管 WebView / CDP / chrome inspect 是外部资源，按主册 §1.3 铁律不可关闭。与 `mcpowers-reverse-hybrid` 1:1 对应。
---

# 爬虫Hybrid逆向规范

> **本文档定位**：本规范是《爬虫分析规范》v2.14.0 起拆分出的 **Hybrid 逆向通用
> 方法论册**，与 `mcpowers-reverse-hybrid` 1:1 对应。
>
> - WebView JS 层逆向工具见《爬虫Web逆向规范》§2
> - Android / iOS 原生层逆向工具见《爬虫Android逆向规范》《爬虫IOS逆向规范》
> - 真实可用性验收见主《爬虫分析规范》§9.4
>
> **外部接管资源所有权**：接管 WebView / CDP 调试端口属于外部资源，按主《爬虫
> 分析规范》§1.3 铁律**不可关闭**。详见工具册 §3.5.1。

---

## §1. uni-app / React Native / Cordova / Capacitor 识别

Hybrid 容器按 JS 引擎 + Bridge 形态分四类：

| 容器 | JS 引擎 | 关键产物 | 关键文件 |
|:-----|:---------|:---------|:---------|
| **uni-app** | V8（默认）/ Webview（旧） | `app-plus` 资源 + `manifest.json` | `unpackage/` 目录 |
| **React Native** | Hermes / JSC | bundle.js / Hermes bytecode | `index.android.bundle` / `main.jsbundle` |
| **Cordova** | 系统 WebView | www/ 资源 | `www/index.html` + `cordova.js` |
| **Capacitor** | 系统 WebView | `assets/public/` | `assets/public/index.html` + `capacitor.js` |

**识别方法**：
1. 解包 APK / IPA 看 `assets/`、`www/`、`index.android.bundle`、`main.jsbundle` 特征
2. App 启动时 `chrome://inspect/#devices` 是否能看到 WebView / Chrome Custom Tabs
3. 关键字符串检索：`uni.` / `ReactNative` / `_cordovaNative` / `Capacitor.`

---

## §2. WebView / JSBridge 桥接回追

uni-app、React Native/Hermes、Cordova、Capacitor 和自定义 WebView/JSBridge
按**三层定位**：

### §2.1 JS 层

- bundle、模块加载、序列化、fetch/XHR 和参数拼装
- 工具与策略见《爬虫Web逆向规范》§2

### §2.2 Bridge 层

- 方法名 / 参数 / 返回 schema / 异步回调
- 线程与 session 绑定（RN bridge 在 native modules thread；uni-app 在 webview 主线程同步后 async 回调）
- 关键定位方法：
  - uni-app：搜 `uni.request` / `uni.getStorage`
  - RN：搜 `NativeModules.Xxx.methodName`
  - 自定义 JSBridge：搜 `window.<Bridge>.call(...)` 或 `WebViewJavascriptBridge`

### §2.3 Native 层

- 插件实现、系统能力、Keystore/Keychain、JNI/Swift/ObjC 加密
- 当 sign/token 在原生层生成时，转入 Android/iOS 专项（参见《爬虫Android
  逆向规范》《爬虫IOS逆向规范》）

### §2.4 接管 WebView 实操

> **关键提醒**：WebView 调试端口（`chrome://inspect`）属于用户外部资源，按工具册
> §3.5.1 + 主册 §1.3 铁律**只 attach 不关闭**。

```python
# chrome --remote-debugging-port=9222 --remote-allow-origins=*
# 用户启动 Chrome 主进程 + 安卓手机 USB 调试
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    # 复用用户 Chrome 主进程，不要关闭
    for ctx in browser.contexts:
        for page in ctx.pages:
            # page 是用户已打开的 WebView / 普通页面
            ...
```

**禁止**：
- ❌ 任务结束调用 `browser.close()`（违反主册 §1.3 铁律）
- ❌ 用 `page.close()` 关闭用户已经打开的调试入口

---

## §3. 与工具册 / 主册的关系

### §3.1 真实可用性验收（指向主册 §9.4）

Hybrid 模块的最终验收必须走主《爬虫分析规范》§9.4：
- 至少 3 组不同业务输入与真实请求对照
- 记录 JS/Bridge/Native 三层证据
- `verification-report.md` 最终状态 = **`PASS`** 才算 Hybrid 模块可用

### §3.2 跨专项指纹交接（指向主册 §10.9）

Hybrid 二级入口需产出 `01-target-profile/runtime-fingerprint.md`，包含证据路径、
运行时、核心逻辑候选层、置信度、主专项、辅助专项和未确认项。

### §3.3 与 Android / iOS 规范的引用

- 当 Bridge 调用的实现在原生层时，转入《爬虫Android逆向规范》或《爬虫IOS逆向
  规范》
- 优先 hook JNI / Keychain / Keystore 读取边界，而不是反编译整个 native 模块

---

## §4. 反模式

- ❌ 接管 WebView 后调用 `browser.close()` / `page.close()` / 关闭 chrome inspect
- ❌ 把整个 native 模块反编译（应优先 hook JNI 边界）
- ❌ 把 JS 层与 Native 层证据混在一起（必须按 §2.1-§2.3 三层分别记录）
- ❌ 假设所有 RN 用同一种 JS 引擎（Hermes 与 JSC 的 hook 路径不同）
- ❌ 假设所有 JSBridge 都是同步回调（uni-app / RN 都存在 async 跨线程）
- ❌ 实测少于 3 组不同输入就宣布算法还原成功
