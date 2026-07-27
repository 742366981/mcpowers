---
name: mcpowers-reverse-web
description: "网站逆向 / Web JS反混淆 / 浏览器抓包 / CDP接管 → 触发本技能。口语：逆向这个网站、找sign生成、抓XHR/fetch、分析Webpack或WASM、接管已登录Chrome、bb-browser配合Playwright。中英：Web reverse/JavaScript deobfuscation/CDP/Playwright/WASM/RPC/site adapter。边界：未知目标→mcpowers-crawler-reverse；App→mcpowers-reverse-app；WebView容器→mcpowers-reverse-hybrid；已有网站爬虫报错→mcpowers-bugfix。流程：公共前置合同→Web证据链→公共收尾合同。"
---

# mcpowers-reverse-web（网站逆向）

> 面向网站、H5、浏览器 JavaScript/WASM 和 Web RPC。公共交付与验收由统一入口负责。

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-crawler-reverse` 公共前置合同 | 公共合同 | 直接命中本技能时必读 | 缺目标/授权/交付形态则中断 |
| 2 | `爬虫Web逆向规范.md` + `爬虫工具与抓包规范.md` §3 | 规范 | 必读 | 按 spec-index 重新定位 |
| 3 | Playwright-Python + CDP | 执行链 | 浏览器证据与动态触发 | 切换协作模式，不擅自 launch |
| 4 | bb-browser + popup-handler.py | 可选增强 | daemon/adapter 可用 | 回退 Playwright 原链路 |
| 5 | `mcpowers-crawler-reverse` 公共收尾合同 | 公共合同 | 专项证据交接后 | 缺证据则返回本技能补齐 |

**防循环**：只 Read 统一入口中的「公共前置合同」「公共收尾合同」，不得再次调用入口分流。

## Web 专项流程

### 1. 接管预检与资源所有权

1. 探测 bb-browser 状态；失败只记 unavailable。
2. 探测用户指定 CDP endpoint（默认示例 `localhost:9222`），列出 contexts/tabs。
3. 发现目标 tab 时询问接管既有 tab 或在用户 context 新开 tab；未发现时询问启动调试 Chrome、由任务创建隔离浏览器、协议直连或取消。
4. 写入资源清单：resource、origin（user/external/task）、owner、允许清理动作。

**外部接管资源不可关闭**：`connect_over_cdp` 得到的 browser、用户 context、既有 page/tab 和外部 daemon 全部视为 external；禁止 `browser.close()`、`context.close()`、关闭既有 page、kill Chrome。任务在用户 context 新开的 tab 默认保留，只有用户明确确认才能关闭。

### 1.5 用户操作录制（v2.15.0 新增，协作模式 B 工具支撑）

当用户切换到协作模式 B（"用户操作 + AI 抓包"，见《爬虫分析规范》§3.0.1）时，
先 `popup-handler.cleanup_all(page)` 清弹窗，再
`user_action_recorder.start_recording(page, output_dir=...)` 启动录制，让用户完成
关键操作后 `stop_recording()` 落 `user-actions.json` + `user-session.har.jsonl`。
重放可用 `replay_actions(page, actions_json_path, screenshot_each_step=True)` 验证。
详见《爬虫工具与抓包规范》§8。

**v2.16.0 实战提示**：Chrome 150+ 时代协作模式 B 已成为强校验表单场景的
**默认入口**——AI 必须 attach 用户真实 page target（如 `4252F91C4CC929918E03`），
**禁止**用 `Target.createTarget` 自己拉新 tab 后 attach；强校验表单场景
AI 不驱动表单，让用户手动点一次触发 POST，1s 内可抓到 200。详见
《爬虫分析规范》§3.0.6 Chrome 150+ 协作模式 B 实战案例与《爬虫工具与抓包规范》
§3.9.3 实战案例摘要。

注意：录制/重放全程遵守 §1 外部资源所有权铁律——禁止 `browser.close()` /
`context.close()` / `page.close()` / kill Chrome；监听器通过
`page.remove_listener()` 注销，不靠进程结束清理。

### 2. 页面与接口证据

- 先运行 popup-handler.py 清理可自动处理弹窗；登录墙、年龄验证和合规同意截图后询问。
- 根据协作模式触发目标业务动作，采集 XHR/fetch、调用栈、initiator、请求/响应和 Cookie 变化。
- bb-browser adapter 只提供站点导航和结构化线索；URL/Method/响应必须由 Playwright 或 `curl_cffi` 实测。
- `api-inventory.md` 标注来源和置信度；过滤 CDN、上报、字体、心跳。

### 3. JavaScript/WASM 逆向

按最小成本递进：

1. 搜索参数名、接口路径、固定前后缀和调用点。
2. XHR/fetch/关键函数断点或 Hook，记录真实入参与返回值。
3. 识别 bundle/chunk、动态加载、混淆、环境依赖和 WASM 边界。
4. 优先 Python 纯复现；失败再评估 Node 调原 JS；强依赖页面运行时才用受控 RPC。
5. 至少 3 组不同输入与页面结果对照，记录 timestamp/nonce/sign/token 变化线索。

### 4. 标准交接

按统一入口「专项证据交接合同」返回 Web 指纹、接口证据、逆向方式、3 组算法验证、状态线索、运行限制、模块输入和证据路径。不得在本技能内复制或执行公共验收结论。

## 反模式（禁止）

- ❌ 关闭用户 Chrome、既有 context/page/tab，或在异常处理里 kill 浏览器。
- ❌ 接管失败后静默 `launch()` / `browser.new_context()`。
- ❌ 为证明纯协议而关闭用户浏览器；应停止依赖并从模块入口独立调用。
- ❌ 外部 bb-browser daemon 异常时擅自 stop/restart。
- ❌ adapter 命中直接标 `[🎯]`，跳过网络实测。
- ❌ 读混淆代码死磕而不先 Hook 入参/出参。
- ❌ Python 复现失败就放弃 Node/RPC 候选。
- ❌ **v2.16.0 新增**：抓不到就静默切协作模式，不走《爬虫工具与抓包规范》§3.9 漏抓 7 层 6 问自检。
- ❌ **v2.16.0 新增**：`Target.createTarget` 拉新 tab（必须从 `user.contexts[i].pages` 中挑选真实 page target）。
- ❌ **v2.16.0 新增**：Chrome 启动命令漏 `--remote-allow-origins=*`（Chrome 150+ 会 403）。

## 完成后自检清单

- [ ] 已引用公共前置合同，目标、授权和交付形态明确。
- [ ] 所有资源已标 origin/owner；用户浏览器和既有 tabs 仍存活。
- [ ] bb-browser 不可用时原 Playwright/CDP 链路可独立运行。
- [ ] 核心接口有响应样本、来源和置信度。
- [ ] 核心算法已有 ≥3 组不同输入对照。
- [ ] 已按专项证据交接合同返回，并进入公共收尾合同。
- [ ] **v2.16.0 漏抓 7 层 6 问自检**（强门禁，阶段 2 抓包失败切模式前必走）：
  - ☐ L1：已用 `curl http://localhost:9222/json | jq` 列出所有 target，确认 worker/iframe/SW target 单独 attach？
  - ☐ L2：Chrome 启动命令已带 `--remote-allow-origins=*`？（Chrome 150+ 必传）
  - ☐ L3：是否走 `Target.createTarget` 拉了 tab？（必须从 `user.contexts[i].pages` 中挑选）
  - ☐ L4：DevTools Network 是否抓到 `(failed)` 空白请求？（若是，先解决证书/SSLKEYLOGFILE）
  - ☐ L5：DevTools Filter 是否启用了 Hide data URLs / Fetch-XHR 单选？（若是，先关闭）
  - ☐ L6：目标 API 是否走 WebSocket / SSE / sendBeacon / HTTP/3 / Cache 命中？（若是，切到对应 DevTools 标签）
  - 详见《爬虫工具与抓包规范》§3.9。
