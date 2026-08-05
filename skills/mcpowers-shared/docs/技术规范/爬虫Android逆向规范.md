---
title: 爬虫Android逆向规范
type: tech-spec
applies_to: [crawler-reverse, android]
priority: recommended
version: 2.14.0
last_updated: 2026-07-27-v2.14.0
description: Android APK 的脱壳 / SSL Pinning 绕过 / 静态分析 / 动态分析 / so 层分析通用方法。与 `mcpowers-reverse-android` 1:1 对应。iOS 单独见《爬虫IOS逆向规范》；Flutter / Hybrid / 小程序的 Android 外壳分析也读本规范但只处理外壳与原生桥接证据。外部接管资源（LSPosed 注入 / frida attach / 调试 USB）按主册 §1.3 铁律不可关闭。
stability: evolving
last_breaking_change: v2.14.0
---

# 爬虫Android逆向规范

> **本文档定位**：本规范是《爬虫分析规范》v2.14.0 起拆分出的 **Android 逆向通用
> 方法论册**，与 `mcpowers-reverse-android` 1:1 对应。
>
> - 工具与运行时（设备框架 / LSPosed / frida 链路）见《爬虫工具与抓包规范》§2.3。
> - 真实可用性验收（≥ 3 组样本 / 生命周期 / 并发）见主《爬虫分析规范》§9.4。
> - 跨端入口与指纹交接协议见主《爬虫分析规范》§1.2 / §10.9。
>
> **外部接管资源所有权**：本规范的 frida attach / LSPosed 注入 / 调试 USB
> 都视为外部接管资源，按主《爬虫分析规范》§1.3 铁律不得 stop/kill。

---

## §1. 脱壳（**加固 APP 的第一道坎**）

**判断是否加固**：解压 APK 看 `lib/` 目录有无 `libexec.so`、`libjiagu.so`、
`libDexHelper.so` 等。

**脱壳工具**（按强度选择）：

| 工具 | 用途 |
|:-----|:-----|
| **FRIDA-DEXDump**（**通用首选**） | 基于 frida 运行时 dump dex |
| **FART**（**ART 主动调用 + 脱壳**） | 处理 ART 优化后的 dex（**加固方案较优时用**） |
| BlackDex | 360 加固专用 |
| DexHunter / drizzledumper | 老版本方案 |

**脱壳产物**：纯 dex 文件 → 用 jadx 反编译看源码。

---

## §2. SSL Pinning 绕过（**抓到包的关键**）

**症状**：APP 装了证书，但抓包工具全是 `Tunnel to ...` 或 `SSL handshake failed`。

**绕过方案**（**按优先级选**）：

| 优先级 | 方案 | 适用 |
|:-------|:-----|:-----|
| 1 | **frida + objection**（**推荐首选**，免改包） | 大多数 APP |
| 2 | frida 自写脚本（更灵活） | objection 不支持时 |
| 3 | **justtrustme**（Xposed/LSPosed 模块） | 需 root + Xposed/LSPosed 环境 |
| 4 | 重新打包（终极方案） | 所有方案都失效时 |

**objection 一键绕过**：

```bash
objection -g com.target.app explore
# 在 objection REPL 里执行：
android sslpinning disable
```

**frida 自写 SSL Bypass**：

```javascript
// 保存到 03-逆向攻坚/钩子/ssl-bypass.js
Java.perform(function() {
    var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
    TrustManagerImpl.verifyChain.implementation = function() { return []; };
});
```

**iOS SSL Pinning 绕过**：详见《爬虫IOS逆向规范》§2（与本节流程类似但工具不同）。

---

## §3. 静态分析（看代码，不运行）

| 工具 | 用途 |
|:-----|:-----|
| **jadx / jadx-gui**（**首选**） | dex 反编译，可读性最好 |
| apktool | APK 解包，看资源、清单、smali |
| dex2jar + jd-gui | jadx 不支持时备选 |
| Android Studio | 官方 IDE，自带 APK Analyzer |

**关键搜索**：与 Web 逆向类似（`sign`、`encrypt`、`aes`、`token`、
`x-sign`、`x-ticket`、`hmac`）

**关键关注类**：
- 加密类：`javax.crypto.*`、自定义 `XxxUtil`、`CryptoUtils`
- 网络类：`OkHttpClient`、`Retrofit`、`Interceptor`、`Request.Builder`
- 风控类：`DeviceFingerprint`、`RiskControl`、`FingerprintCollector`

---

## §4. 动态分析（frida Hook）—— **最有效手段**

**安装 frida-server**：root 设备 + 推送 frida-server + 启动

**Hook 加密函数**（**核心**，直接拿到入参/出参）：

```javascript
// 保存到 03-逆向攻坚/钩子/app-sign-hook.js
Java.perform(function() {
    var EncryptUtil = Java.use('com.target.app.utils.EncryptUtil');
    EncryptUtil.sign.implementation = function(input) {
        var result = this.sign(input);  // 原始调用
        console.log('[HOOK sign] input=' + input + ' output=' + result);
        return result;
    };
});
```

**执行**：`frida -U -f com.target.app -l app-sign-hook.js --no-pause`

**Hook 网络请求**：Hook OkHttp 的 `Interceptor`/`RealInterceptorChain`，
**直接拿到最终请求体**（无需反编译 sign 生成逻辑）

**Hook native 层**：so 文件里的 `JNI_OnLoad`、加密函数，需 IDA/Ghidra 配合

**脱壳后 Hook**：用 FRIDA-DEXDump 脱壳后，Hook 完整源码里看到的加密函数

---

## §5. so 层分析（**极难**，仅当 Java 层没找到时）

| 工具 | 用途 |
|:-----|:-----|
| **Ghidra** | NSA 开源，**首选** |
| IDA Pro | 商业级，业界权威 |
| `strings` / `objdump` | so 文件初步探查 |
| `nm` / `readelf` | 导出符号表 |

**基本流程**：`strings` 搜索 → `objdump` 看导出函数 → IDA/Ghidra 静态分析 →
frida Hook native 验证

**替代方案**：直接 frida Hook JNI 入口，把入参/出参 dump 出来，
**算法分析工作量大幅降低**

---

## §6. 与工具册 / 主册的关系

### §6.1 调试链路组装

参见《爬虫工具与抓包规范》§2.3：root 设备 + Magisk + LSPosed + frida-server +
justtrustme / TrustUserCerts + PC 端 mitmproxy。

### §6.2 通用 APP 方法不涵盖的平台

- **iOS 平台**：详见《爬虫IOS逆向规范》
- **Flutter APP 的 Dart 层**：详见《爬虫Flutter逆向规范》
- **uni-app / RN / WebView 的 JS / Bridge 层**：详见《爬虫Hybrid逆向规范》
- **微信 / 支付宝 / 抖音 / 百度小程序**：详见《爬虫小程序逆向规范》

### §6.3 真实可用性验收（指向主册 §9.4）

Android 模块的最终验收必须走主《爬虫分析规范》§9.4：
- 至少 3 组不同业务输入与真实请求对照
- 记录 Android/包名/版本/架构/签名版本限制
- `验收报告.md` 最终状态 = **`PASS`** 才算 Android 模块可用

### §6.4 跨专项指纹交接（指向主册 §10.9）

Android 二级入口需产出 `01-目标画像/运行时指纹.md`，包含证据路径、
OS/包格式、运行时、核心逻辑候选层、置信度、主专项、辅助专项和未确认项。
指纹冲突时保持 `unknown` 并设计最小验证，不得同时展开全部工具链。

---

## §7. 反模式

- ❌ 跳过脱壳直接静态分析加固 APP（看到的是壳的字节码，不是真实业务）
- ❌ 跳过 SSL Pinning 绕过就抓包（抓到的是空或错误响应）
- ❌ 让 frida attach 整个进程后再 `frida -k ... -K` kill 进程
  （违反主册 §1.3 铁律）
- ❌ 不记录 owner 就 stop/restart daemon 或 frida-server
- ❌ 实测少于 3 组不同输入就宣布算法还原成功
- ❌ 把 so 层分析作为默认入口（应优先 Java 层 Hook）
