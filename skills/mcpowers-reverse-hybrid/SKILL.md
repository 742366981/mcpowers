---
name: mcpowers-reverse-hybrid
description: "混合App逆向 / uni-app与React Native / WebView JSBridge / Hermes → 触发本技能。口语：逆向uni-app、RN包怎么看、WebView里找sign、分析JSBridge、Cordova或Capacitor接口在哪。中英：hybrid reverse/uni-app/React Native/Cordova/Capacitor/WebView/JSBridge/Hermes。边界：普通网站→mcpowers-reverse-web；纯Android Native→mcpowers-reverse-android；纯iOS Native→mcpowers-reverse-ios；Flutter→mcpowers-reverse-flutter。流程：公共前置合同→JS/Bridge/Native分层→公共收尾合同。"
---

# mcpowers-reverse-hybrid（混合 App 逆向）

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-crawler-reverse` 公共前置合同 | 公共合同 | 直接命中 | 缺授权/目标则中断 |
| 2 | `爬虫分析规范.md` Hybrid 章节 | 规范 | 必读 | 保持框架 unknown |
| 3 | `爬虫分析规范.md` Web / Android / iOS 章节 | 辅助规范 | 核心逻辑落在 JS 或 Native | 只引用对应方法，不递归调用专项 |
| 4 | `mcpowers-crawler-reverse` 公共收尾合同 | 公共合同 | Hybrid 证据交接后 | 缺证据返回对应层补齐 |

**防循环**：只 Read 公共合同；需要 Web/Android/iOS 方法时只读规范对应章节，不递归调用其他逆向专项。

## Hybrid 专项流程

### 1. 框架与层级识别

识别 uni-app、React Native/Hermes、Cordova、Capacitor、WebView/WKWebView、自定义 JSBridge 证据。记录 bundle/资源路径、Bridge 名称、Native 插件、网络请求发起层和目标动作。

### 2. 三层定位

1. **JS 层**：bundle、模块加载、序列化、参数拼装、fetch/XHR。
2. **Bridge 层**：方法名、参数/返回 schema、异步回调、线程和 session 绑定。
3. **Native 层**：插件实现、系统能力、Keychain/Keystore、JNI/Swift/ObjC 加密。

先定位真实请求由哪一层发出，再选择主专项；禁止三层同时漫无目标展开。

### 3. WebView/CDP 所有权

**外部接管资源不可关闭**：接管用户浏览器、WebView 调试 endpoint、context/page、既有标签页或外部 daemon 时，一律记录为 external；不得调用关闭/kill。任务创建的调试页默认保留，只有用户明确确认后清理。无法接管时询问替代方式，不静默新建独立浏览器环境。

### 4. 验证与交接

至少 3 组输入对照 JS → Bridge → Native → 请求的动态值和时序。按统一入口「专项证据交接合同」返回框架指纹、主逻辑层、接口证据、逆向方式、算法对照、状态绑定、平台限制、模块输入和证据路径。

## 反模式（禁止）

- ❌ 把 uni-app/RN 一律当普通网页，只看 JS 不看 Bridge。
- ❌ 一律当 Native，只 Hook 系统 API 不检查 bundle。
- ❌ 接管 WebView/CDP 后关闭用户浏览器、context、既有 page 或 daemon。
- ❌ Bridge 参数未记录 schema/时序就直接封装 RPC。
- ❌ 在本技能复制公共阶段 5.5 或宣布交付 PASS。

## 完成后自检清单

- [ ] 已引用公共前置合同。
- [ ] 框架指纹和 JS/Bridge/Native 主逻辑层有证据。
- [ ] 外部 WebView/CDP/浏览器资源保持存活。
- [ ] Bridge schema、时序与 session 绑定已记录。
- [ ] 至少 3 组输入完成端到端对照。
- [ ] 已按证据合同交接到公共收尾合同。
