---
title: 爬虫Flutter逆向规范
type: tech-spec
applies_to: [crawler-reverse, flutter]
priority: recommended
version: 2.14.0
last_updated: 2026-07-27-v2.14.0
description: Flutter Dart AOT snapshot、libapp.so / App.framework、Platform Channel 桥接回追的方法论；与 `mcpowers-reverse-flutter` 1:1 对应。Android / iOS 外壳与原生桥接证据保留引用本规范主册对应章节；本规范不重复叙述通用方法。
stability: evolving
last_breaking_change: v2.14.0
---

# 爬虫Flutter逆向规范

> **本文档定位**：本规范是《爬虫分析规范》v2.14.0 起拆分出的 **Flutter 逆向通用
> 方法论册**，与 `mcpowers-reverse-flutter` 1:1 对应。
>
> - Dart AOT snapshot 还原工具（blutter / darlk / reFlutter）见本规范 §2
> - 真实可用性验收见主《爬虫分析规范》§9.4
> - 跨端指纹交接见主《爬虫分析规范》§10.9

---

## §1. Dart AOT snapshot 与 `libapp.so` / `App.framework`

Flutter 先判断核心逻辑位于 **Dart AOT**、**Platform Channel** 还是 **Native 外壳**：

| 证据 | 主分析层 | 辅助专项 |
|:-----|:---------|:---------|
| Dart snapshot、`libapp.so`/`App.framework` 中的业务与网络逻辑 | Dart AOT | Android/iOS 仅处理外壳 |
| Dart 只传参，channel 返回 sign/token | Platform Channel | 对应 Android/iOS 定位插件实现 |
| 请求和加密完全在 Java/Kotlin/Swift/ObjC/JNI | Native | 对应原生专项为主 |
| 两侧共同生成状态 | 混合 | 记录调用时序、schema 和 session 绑定 |

**工具与地址选择必须基于实际引擎/产物版本**。禁止看见 Flutter 外壳就假定全部
逻辑在 Dart，也禁止忽略 Platform Channel 直接盲搜 Native。

---

## §2. blutter / darlk / reFlutter 工具链

| 工具 | 用途 | 平台 |
|:-----|:-----|:-----|
| **blutter** | Dart AOT 反汇编（Android `libapp.so`） | Android |
| **darlk** | Dart AOT 反汇编（iOS `App.framework`） | iOS |
| **reFlutter** | 替换 snapshot + Hook 拦截 | Android/iOS |
| Dart snapshots decompiler（[tchés]） | 通用 snapshot 还原 | Android/iOS |

**典型工作流**：
1. 备份原始 `libapp.so` / `App.framework`
2. 用 `blutter` / `darlk` 跑出反汇编产物（汇编 / 函数签名 / 类名）
3. 找到网络请求相关函数（如 `http.Client.post`、`dio.post`）
4. Hook 该函数，输入业务入参，dump 出真实 request / response

**关键注意点**：
- Dart 函数符号在 AOT 中已经被混淆，需要根据调用栈 + 参数推断
- 部分业务在 isolate 中运行，需要找到对应的 isolate id 后再 hook
- Platform Channel 的 channel 名是明文的，可以直接定位

---

## §3. Platform Channel 桥接回追

当 Dart 业务把 sign / token 生成转嫁给原生层：

1. **定位 channel 名**：搜 `MethodChannel('xxx')` / `EventChannel('xxx')` /
   `BasicMessageChannel`，channel 名一般与业务模块同名
2. **定位原生插件实现**：Android 在 `MainActivity` / 自定义 `FlutterPlugin`；
   iOS 在 `AppDelegate` / 自定义 `FlutterPlugin`
3. **Hook 原生侧**：frida Hook Java/Kotlin/Swift/ObjC 的 method handler，
   拿到 dart 调用传参 + 原生返回结果
4. **判断哪层生成动态值**：如果动态值在原生层生成，把逆向重心转入
   Android/iOS 专项（参见《爬虫Android逆向规范》《爬虫IOS逆向规范》）

---

## §4. 与 Android / iOS 规范的引用关系

| Flutter 任务 | 主入口 | 必读章节 |
|:---|:---|:---|
| Dart AOT 还原（Android） | 本规范 §2（blutter） | §2, §3（channel） |
| Dart AOT 还原（iOS） | 本规范 §2（darlk） | §2, §3（channel） |
| Flutter Java/Kotlin 层 | 《爬虫Android逆向规范》 | §3 静态 + §4 动态 |
| Flutter Swift/ObjC 层 | 《爬虫IOS逆向规范》 | §3 静态 + §4 动态 |
| 网络抓包 | 《爬虫工具与抓包规范》§1.2 + SSL Pinning 处理 | 各专项 §2 |
| 真实可用性验收 | 主《爬虫分析规范》§9.4 | 主册 §9.4 |
| 跨端指纹交接 | 主《爬虫分析规范》§10.9 | 主册 §10.9 |

---

## §5. 反模式

- ❌ 看见 Flutter 外壳就假定全部逻辑在 Dart AOT（实际可能在 Platform Channel / 原生侧）
- ❌ 忽略 Platform Channel 直接盲搜 Native
- ❌ 假设所有 Flutter 应用都用同一套 AOT 工具链（必须查产物哈希 + 引擎版本）
- ❌ 用 Dart 反射代替 frida hook 拿运行时常量
- ❌ 未确认 Dart isolate 就 hook 业务函数（多个 isolate 时参数串线）
- ❌ 实测少于 3 组不同输入就宣布算法还原成功
