---
name: mcpowers-reverse-android
description: "Android逆向 / APK与AAB分析 / Kotlin Java JNI / Frida Hook → 触发本技能。口语：逆向安卓App、jadx看不到业务代码、绕SSL Pinning、找Kotlin签名函数、Hook so、应用加固脱壳。中英：Android reverse/APK/AAB/DEX/Kotlin/JNI/Frida/objection/LSPosed。边界：平台未知→mcpowers-reverse-app；Flutter指纹→mcpowers-reverse-flutter；uni-app/RN/WebView→mcpowers-reverse-hybrid；iOS→mcpowers-reverse-ios。流程：公共前置合同→Android证据链→公共收尾合同。"
---

# mcpowers-reverse-android（Android 逆向）

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-crawler-reverse` 公共前置合同 | 公共合同 | 直接命中 | 缺授权/目标则中断 |
| 2 | `爬虫Android逆向规范.md` + `爬虫工具与抓包规范.md` §1.2/§2.3 | 规范 | 必读 | 按证据补环境信息 |
| 3 | `爬虫Flutter逆向规范.md` / `爬虫Hybrid逆向规范.md` | 辅助规范 | 发现跨端指纹 | 停止 Android 深挖并返回重新分流证据 |
| 4 | `mcpowers-crawler-reverse` 公共收尾合同 | 公共合同 | Android 证据交接后 | 缺证据返回补齐 |

**防循环**：只 Read 公共合同，不再次调用统一入口分流；发现 Flutter/Hybrid 指纹时返回重新分流证据，不递归调用其他逆向专项。

## Android 专项流程

### 1. 环境与复杂度画像

记录 APK/AAB 来源、包名/版本、ABI、min/target SDK、签名、加固/壳、root/模拟器条件和目标动作。进入脱壳、Pinning 绕过或 Native 分析前告知成本与授权边界。

### 2. 抓包递进

按最小侵入顺序验证：系统代理与用户证书 → App 网络栈/证书策略 → SSL Pinning 定位与受控 Hook。抓不到包不能直接等同“无接口”或“算法失败”。保留原请求、响应和 App 业务状态对照。

### 3. 静态与动态定位

1. jadx/apktool 识别入口、网络栈、拦截器、参数生成和 Native 声明。
2. 有壳时先记录壳证据，再选择授权环境中的脱壳方法；禁止把壳代码当业务代码。
3. 优先 Hook 关键函数入参/出参、OkHttp/网络拦截点和 JNI 边界。
4. 只有 Java/Kotlin 层无法解释证据时进入 so 分析；记录符号、调用链、ABI 与版本绑定。
5. 至少 3 组不同业务输入验证 sign/token 与真实请求一致。

### 4. Kotlin/Java/JNI 边界

Kotlin 不单独成技能：协程、编译器生成类和 metadata 是 Android 静态定位细节；最终仍以 DEX/JVM、Android Framework、网络栈和 JNI 证据判断核心逻辑层。

### 5. 标准交接

按统一入口「专项证据交接合同」返回 Android 指纹、接口证据、Hook/静态/Native 方法、算法对照、状态线索、设备与版本限制、模块输入和证据路径。

## 资源与安全边界

设备、模拟器、App 进程、frida-server/调试服务均记录 owner；不停止用户已有设备或调试服务。若链路涉及 WebView/CDP，外部接管资源不可关闭，并转用 Hybrid/Web 的所有权规则。

## 反模式（禁止）

- ❌ 未识别壳就把 jadx 结果当业务全貌。
- ❌ 未排查 SSL Pinning 就宣布抓包失败。
- ❌ 直接读深度混淆代码，不先 Hook 真实入参/出参。
- ❌ Java/Kotlin 证据足够时仍过早进入 so 层。
- ❌ 把设备绑定 token/Cookie 写成稳定常量。
- ❌ 在本技能复制公共阶段 5.5 或宣布交付 PASS。

## 完成后自检清单

- [ ] 已引用公共前置合同，授权与成本已确认。
- [ ] 包、壳、网络栈、运行时与核心逻辑层有证据。
- [ ] Hook/算法至少 3 组输入对照。
- [ ] 设备、账号、版本和 session 限制已记录。
- [ ] 已按证据合同交接到公共收尾合同。
