---
title: 爬虫IOS逆向规范
type: tech-spec
applies_to: [crawler-reverse, ios]
priority: recommended
version: 2.14.0
last_updated: 2026-07-27-v2.14.0
description: iOS IPA / Mach-O / Swift / Objective-C 通用逆向方法（不涵盖 Flutter App.framework）。与 `mcpowers-reverse-ios` 1:1 对应。外部接管资源（调试设备 / frida iOS / SSH 隧道）按主册 §1.3 铁律不可关闭；不再依赖已经退役的越狱通道时优先用 corellium 等授权环境。
---

# 爬虫IOS逆向规范

> **本文档定位**：本规范是《爬虫分析规范》v2.14.0 起拆分出的 **iOS 逆向通用方法
> 论册**，与 `mcpowers-reverse-ios` 1:1 对应。
>
> - iOS 抓包链路（iOS 系统代理 / SSL Pinning）见本规范 §2
> - 真实可用性验收见主《爬虫分析规范》§9.4
> - 跨端指纹交接见主《爬虫分析规范》§10.9
>
> **外部接管资源所有权**：调试设备 SSH / frida iOS attach / 越狱环境守护进程
> 都视为外部接管资源，按主《爬虫分析规范》§1.3 铁律不得 stop/kill；不再依赖
> 已经退役的越狱通道时，优先使用 corellium 等授权环境。

---

## §1. IPA 结构与 Mach-O

iOS 不复用 Android 的 DEX/jadx 路线。先记录 IPA/Bundle ID/版本/架构、Mach-O
加密状态、签名与 entitlements、越狱或授权调试条件，再决定静态或动态分析：

1. **Info.plist、加载库、字符串、Objective-C runtime 和 Swift 符号**用于建立调用候选
2. 需要解密镜像时先确认授权环境和产物哈希，**不能假设用户具备砸壳条件**
3. 网络证据从系统代理、`NSURLSession`/第三方网络库和 Pinning 位置递进
4. 优先在请求构造、签名函数、Keychain / 状态读取和系统网络 API 边界观测入参/出参
5. 至少 3 组不同业务输入与真实请求对照，并记录 iOS/设备/签名版本限制

---

## §2. iOS SSL Pinning 绕过

**症状**：iOS 设置了系统代理后，APP 仍不信任 / 直接拒绝连接。

**绕过方案**（**按优先级选**）：

| 优先级 | 方案 | 适用 |
|:-------|:-----|:-----|
| 1 | **frida iOS + SSL Bypass 脚本**（**推荐首选**） | 大多数 APP |
| 2 | objection iOS（`ios sslpinning disable`） | objection 支持时 |
| 3 | 越狱 + SSLKillSwitch3 | 兼容老版本越狱环境 |
| 4 | 重新签名 + Frida Gadget | 不越狱的最后方案 |

**frida iOS SSL Bypass 关键 Hook 点**：
```javascript
// 保存到 03-逆向攻坚/钩子/ios-ssl-bypass.js
// 1. NSURLSession delegate
// 2. SecTrustEvaluate 强制返回 true
// 3. AFNetworking / Alamofire 的安全模块（按需）
```

**关键提醒**：iOS 的 SSL Pinning 位置比 Android 复杂（`NSURLSession`、
`CFNetwork`、第三方网络库各自有 Pinning），需要按栈逐层 Hook。

---

## §3. 静态分析（Hopper / Ghidra）

| 工具 | 用途 |
|:-----|:-----|
| **Hopper Disassembler**（**首选**，商业） | ARM64 / ARMv7 反汇编，ObjC 类结构清晰 |
| **Ghidra** | NSA 开源，备选 |
| class-dump / class-dump-z | 头文件导出 |
| MachOView | Mach-O 文件结构查看 |
| strings / nm / otool | 命令行初探 |

**关键搜索**：
- 函数名（`sign`、`encrypt`、`aes`、`md5`、`hmac`、`sha`）
- 字符串特征（密钥 / IV / 错误信息）
- 加密类（`CCCrypt`、`Security` framework、`CryptoSwift`）

**Objective-C runtime 重点**：
- `+ (NSData *)sign:(NSData *)input` 类方法
- Swift 关键函数签名（参数标签 + 返回类型）

---

## §4. 动态分析（Frida iOS）

**环境**：越狱设备 / corellium / Frida Gadget 重签名

**Hook 网络请求**：
```javascript
// 保存到 03-逆向攻坚/钩子/ios-network-hook.js
// Hook NSURLSession 的 dataTaskWithRequest:completionHandler:
// 拿到最终请求体
```

**Hook 加密函数**：
```javascript
// 类似 Android，但 Objective-C 用 objc_msgSend / class_getMethodImplementation
// Swift 函数要先找到符号
```

**执行**：
```bash
# iOS 12+
frida -U -f com.target.app -l ios-sign-hook.js --no-pause
```

**关闭 / 状态**：
- 任务结束只 `frida-disconnect`，**不 kill frida server**
- 卸载自注入 Gadget 时确认签名未对外暴露

---

## §5. 与工具册 / 主册的关系

### §5.1 抓包链路

iOS 抓包默认走 HTTP 代理 + 系统信任证书。详见《爬虫工具与抓包规范》§1.2（L2 HTTPS + L3 SSL Pinning）。

### §5.2 真实可用性验收（指向主册 §9.4）

iOS 模块的最终验收必须走主《爬虫分析规范》§9.4：
- 至少 3 组不同业务输入与真实请求对照
- 记录 iOS/设备/签名版本限制
- `验收报告.md` 最终状态 = **`PASS`** 才算 iOS 模块可用

### §5.3 跨专项指纹交接（指向主册 §10.9）

iOS 二级入口需产出 `01-目标画像/运行时指纹.md`，包含证据路径、
运行时、核心逻辑候选层、置信度、主专项、辅助专项和未确认项。指纹冲突时保持
`unknown` 并设计最小验证。

---

## §6. 反模式

- ❌ 假设用户具备越狱条件
- ❌ 跳过 SSL Pinning 绕过直接抓包
- ❌ 假定所有 Pinning 在同一层（NSURLSession / CFNetwork / 第三方库各自独立）
- ❌ kill frida iOS server / SSH 关闭调试设备
- ❌ 砸壳后用 Swift 反射代替 frida hook
- ❌ 实测少于 3 组不同输入就宣布算法还原成功
