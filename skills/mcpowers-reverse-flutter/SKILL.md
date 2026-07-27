---
name: mcpowers-reverse-flutter
description: "Flutter逆向 / Dart AOT分析 / libapp.so与App.framework / Platform Channel → 触发本技能。口语：这个App是Flutter怎么逆向、Dart签名逻辑在哪、分析libapp.so、抓Platform Channel、Flutter绕Pinning。中英：Flutter reverse/Dart AOT/snapshot/libapp.so/App.framework/Platform Channel。边界：仅Android外壳→mcpowers-reverse-android；仅iOS外壳→mcpowers-reverse-ios；uni-app/RN→mcpowers-reverse-hybrid；平台未知→mcpowers-reverse-app。流程：公共前置合同→Flutter分层证据→公共收尾合同。"
---

# mcpowers-reverse-flutter（Flutter 逆向）

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-crawler-reverse` 公共前置合同 | 公共合同 | 直接命中 | 缺授权/目标则中断 |
| 2 | `爬虫Flutter逆向规范.md` | 规范 | 必读 | 保持版本/层级 unknown |
| 3 | `爬虫Android逆向规范.md` / `爬虫IOS逆向规范.md` | 辅助规范 | 需要外壳、证书或原生桥接证据 | 只引用平台方法，不递归调用专项 |
| 4 | `mcpowers-crawler-reverse` 公共收尾合同 | 公共合同 | Flutter 证据交接后 | 缺证据返回补齐 |

**防循环**：只 Read 公共合同；需要 Android/iOS 外壳证据时只读取规范对应章节，不递归调用其他逆向专项。

## Flutter 专项流程

### 1. 指纹与版本画像

记录 Android/iOS 外壳、Flutter/Dart 指纹、`libapp.so`/`App.framework`、snapshot/资源清单、ABI/架构、引擎版本线索和目标动作。工具选择必须基于实际版本与产物证据。

### 2. 先判断核心逻辑层

| 层级 | 证据 | 后续 |
|:-----|:-----|:-----|
| Dart AOT | 参数生成与业务调用位于 Dart 侧 | 追踪 Dart 函数、对象和网络调用 |
| Platform Channel | Dart 只传参，Native 返回 sign/token | 记录 channel/method/schema，转 Android/iOS 辅助 |
| Native 外壳 | 网络/加密完全在 Java/Kotlin/Swift/ObjC/JNI | 对应原生专项为主 |
| 混合 | 两侧共同生成状态 | 分别取证并建立调用时序 |

### 3. 网络、动态值与验证

先采集真实请求和业务动作，再在 Dart 网络层、序列化、Platform Channel 或 Native 边界定位动态参数。Pinning 绕过必须对应实际网络栈；禁止套用原生模板后直接宣布成功。至少 3 组不同输入验证 sign/token 与真实请求一致。

### 4. 标准交接

按统一入口「专项证据交接合同」返回 Flutter/引擎指纹、核心逻辑层、接口证据、Dart/Channel/Native 逆向方式、算法对照、状态线索、版本限制、模块输入和证据路径。

## 资源边界

设备、App 进程、调试服务均记录 owner；涉及 DevTools、WebView 或浏览器时，外部接管资源不可关闭，不停止用户已有 Chrome、标签页或 daemon。

## 反模式（禁止）

- ❌ 看到 Flutter 外壳就假定所有逻辑都在 Dart。
- ❌ 不识别引擎/产物版本就照搬固定地址或工具输出。
- ❌ 忽略 Platform Channel，只在 `libapp.so` 中盲搜。
- ❌ 原生证书绕过模板未验证网络栈就宣布 Pinning 已解决。
- ❌ 在本技能复制公共阶段 5.5 或宣布交付 PASS。

## 完成后自检清单

- [ ] 已引用公共前置合同。
- [ ] Flutter 指纹、版本线索与核心逻辑层有证据。
- [ ] Dart/Channel/Native 调用边界和 schema 已记录。
- [ ] 至少 3 组输入完成真实请求对照。
- [ ] 已按证据合同交接到公共收尾合同。
