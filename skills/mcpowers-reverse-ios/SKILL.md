---
name: mcpowers-reverse-ios
description: "iOS逆向 / IPA与Mach-O分析 / Swift Objective-C / Frida LLDB → 触发本技能。口语：逆向苹果App、分析IPA、Swift签名函数在哪、砸壳、绕iOS SSL Pinning、看Keychain或网络请求。中英：iOS reverse/IPA/Mach-O/Swift/Objective-C/LLDB/Frida/Keychain。边界：平台未知→mcpowers-reverse-app；Flutter→mcpowers-reverse-flutter；WKWebView/跨端→mcpowers-reverse-hybrid；Android→mcpowers-reverse-android。流程：公共前置合同→iOS证据链→公共收尾合同。"
---

# mcpowers-reverse-ios（iOS 逆向）

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-crawler-reverse` 公共前置合同 | 公共合同 | 直接命中 | 缺授权/目标则中断 |
| 2 | `爬虫分析规范.md` iOS 章节 | 规范 | 必读 | 保持未知并补证据 |
| 3 | `爬虫分析规范.md` Flutter / Hybrid 章节 | 辅助规范 | 发现跨端指纹 | 停止 iOS 深挖并返回重新分流证据 |
| 4 | `mcpowers-crawler-reverse` 公共收尾合同 | 公共合同 | iOS 证据交接后 | 缺证据返回补齐 |

**防循环**：只 Read 公共合同，不再次调用统一入口分流；发现 Flutter/Hybrid 指纹时返回重新分流证据，不递归调用其他逆向专项。

## iOS 专项流程

### 1. 环境画像

记录 IPA/安装来源、Bundle ID、版本、架构、签名/entitlements、加密状态、越狱或授权调试条件、目标动作。不能确认砸壳或调试条件时保持 `unknown`，不虚构可用命令。

### 2. 网络与运行时证据

从系统代理/受控设备证书开始，结合 App 网络栈证据判断 Pinning。记录 NSURLSession/第三方网络库、请求构造、Keychain/本地状态和业务响应。绕过失败不能直接等同算法失败。

### 3. 静态与动态定位

1. 检查 Info.plist、Mach-O、加载库、Objective-C runtime/Swift 符号和字符串线索。
2. 需要解密镜像时先确认授权环境和产物哈希，再进行后续静态分析。
3. 优先在请求构造、签名函数、加解密边界和系统网络 API 处动态观测。
4. Native 深入分析前先证明高层运行时无法解释参数。
5. 至少 3 组不同输入对照动态值与真实请求。

### 4. 标准交接

按统一入口「专项证据交接合同」返回 iOS 指纹、接口与运行时证据、逆向方式、算法对照、Keychain/session/设备状态线索、环境限制、模块输入和证据路径。

## 资源与安全边界

设备、App 进程、调试服务和代理环境都记录 owner；不得停止用户已有设备会话或调试服务。涉及 WKWebView/CDP 时，外部接管资源不可关闭，按 Hybrid/Web 所有权规则处理。

## 反模式（禁止）

- ❌ 未确认镜像是否加密就依赖静态伪代码下结论。
- ❌ 未排查 Pinning/网络栈就声称没有接口。
- ❌ 把越狱/签名条件假设为用户已具备。
- ❌ 把 Swift 符号缺失等同不可逆向，不做动态边界观测。
- ❌ 在本技能复制公共阶段 5.5 或宣布交付 PASS。

## 完成后自检清单

- [ ] 已引用公共前置合同，授权设备和调试条件明确。
- [ ] Bundle、Mach-O、运行时和核心逻辑层结论有证据。
- [ ] 动态/算法结果至少 3 组输入对照。
- [ ] 设备、签名、系统版本和 session 限制已记录。
- [ ] 已按证据合同交接到公共收尾合同。
