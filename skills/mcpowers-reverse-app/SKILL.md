---
name: mcpowers-reverse-app
description: "App逆向入口 / 移动端类型判断 / Native与跨端识别 → 触发本技能。口语：帮我逆向这个App、不知道是Android还是Flutter、先看看用了什么框架、抓不到包怎么判断。中英：mobile app reverse/runtime fingerprint/APK/IPA/native/Flutter/hybrid。边界：明确Android→mcpowers-reverse-android；明确iOS→mcpowers-reverse-ios；Flutter→mcpowers-reverse-flutter；uni-app/RN/WebView→mcpowers-reverse-hybrid；小程序→mcpowers-reverse-miniprogram。流程：公共前置合同→App指纹→专项路由→公共收尾合同。"
---

# mcpowers-reverse-app（App 二级判断入口）

> 只负责 App 载体和运行时识别，不承载 Android/iOS/Flutter/Hybrid 的完整逆向 SOP。

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-crawler-reverse` 公共前置合同 | 公共合同 | 直接命中本技能 | 缺目标/授权则中断 |
| 2 | `爬虫分析规范.md` App 指纹矩阵 | 规范 | 必读 | 保持 unknown，不猜测 |
| 3 | `mcpowers-reverse-android` | 场景 | APK/AAB、DEX、Java/Kotlin/JNI | 记录阻塞证据 |
| 4 | `mcpowers-reverse-ios` | 场景 | IPA、Mach-O、Swift/Objective-C | 记录阻塞证据 |
| 5 | `mcpowers-reverse-flutter` | 场景 | Dart/Flutter AOT 指纹 | 由 Android/iOS 外壳辅助 |
| 6 | `mcpowers-reverse-hybrid` | 场景 | uni-app/RN/Cordova/Capacitor/WebView | 按 JS/Bridge/Native 分层 |
| 7 | `mcpowers-crawler-reverse` 公共收尾合同 | 公共合同 | 下游证据交接后 | 缺证据则回到识别/专项 |

**防循环**：本技能调用明确专项；专项不得再调用本技能。直接命中时只 Read 统一入口公共合同。

## App 指纹识别

### 1. 最小输入

记录安装包/应用路径、包名或 Bundle ID、版本、OS、设备环境、授权范围、目标业务动作。没有安装包时可基于运行中应用和抓包证据识别，但置信度必须标明。

### 2. 识别矩阵

| 证据 | 主路由 | 辅助关系 |
|:-----|:-------|:---------|
| APK/AAB + DEX/AndroidManifest | Android | 遇 Flutter/Hybrid 指纹后改主路由 |
| IPA + Mach-O/Info.plist | iOS | 遇 Flutter/Hybrid 指纹后改主路由 |
| Dart snapshot、`libapp.so`、`App.framework` | Flutter | Android/iOS 处理外壳与环境 |
| JS bundle、Hermes、WebView、JSBridge、uni-app/RN 标识 | Hybrid | Web 分析 JS，Android/iOS 分析 Bridge/Native |
| 证据冲突或不足 | 保持 `unknown` | 继续静态清单与运行时观测 |

### 3. 决策记录

`01-target-profile/runtime-fingerprint.md` 至少写：证据路径、结论、置信度、核心逻辑可能所在层、主专项、辅助专项、未确认项和下一步最小验证。

### 4. 标准交接

本技能负责交接 `target_fingerprint` 与路由理由；命中的下游专项必须继续补齐统一入口「专项证据交接合同」要求的其余 7 项，最终以完整 8 项合同回到公共收尾。

## 资源边界

涉及浏览器/WebView/CDP 时继承统一入口规则：外部接管资源不可关闭；设备、模拟器、App 进程和调试服务也要记录所有权，未经用户授权不得停止其已有环境。

## 反模式（禁止）

- ❌ 只凭文件名或用户口述认定运行时。
- ❌ Android 外壳里发现 `libapp.so` 后仍按纯 Kotlin 路线死磕。
- ❌ uni-app/RN 只按 Web 或只按 Native 单层分析。
- ❌ 在入口复制四个专项的完整工具链。
- ❌ 下游专项完成算法验证后直接宣布模块可交付。

## 完成后自检清单

- [ ] 已引用公共前置合同。
- [ ] 指纹结论有文件/运行时证据和置信度。
- [ ] 已选择一个主专项，辅助专项关系明确。
- [ ] unknown 未伪装成确定结论。
- [ ] 下游按标准证据合同交接并回到公共收尾合同。
