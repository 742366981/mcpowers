"""
user-action-recorder.py — 用户操作录制与重放工具（v2.15.0 新增，v2.18.0 DrissionPage 适配）

本模块是 mcpowers-crawler-reverse 协作模式 B（"用户操作 + AI 抓包"）的工具支撑。
补充 popup-handler.py 不覆盖的"操作流录制 + 重放"维度，不重复弹窗检测与接管预检。
历史兼容：v2.15.0 之前为口头协议，无工具支撑（见《爬虫分析规范》§3.0.1 模式 B）。

核心函数（3 个公开）：
- start_recording(page, output_dir): 启动录制（v2.18.0 起 DrissionPage 用 listen.start() + 后台轮询线程）
- stop_recording(handle) -> str: 停止录制并落 user-actions.json + user-session.har.jsonl
- replay_actions(page, actions_json_path, screenshot_each_step=False) -> dict: 重放已录制操作

详细方法论：见《爬虫工具与抓包规范》§8（用户操作录制与重放）
DEFAULT_USER_ACTION_RECORDER 文档参考《爬虫工具与抓包规范》§8.0（边界声明）

设计原则：
- 遵守外部资源所有权铁律（主《爬虫分析规范》§1.3）：禁止 browser.close() / context.close() / page.close()；
  监听器注销不靠进程结束清理（v2.18.0 DrissionPage 用 `page.listen.stop()`；Playwright fallback 用 `page.remove_listener()`）。
- 不替代 popup-handler.py（弹窗清理）和 bb-browser（站点级结构化操作）；按 SOP 串联：
  popup-handler.cleanup_all() → start_recording() → 用户操作 → stop_recording() → replay_actions()。
- **v2.18.0 DrissionPage 化**：DrissionPage 接管模式下没有 Playwright `record_har_path` 参数，
  本模块手写 `page.listen.start()` + 后台轮询 `page.listen.wait(timeout=0.5)` 落 JSONL 格式 HAR。
  Playwright fallback 保留 `page.on("request"/"response")` 模式（duck typing 自动分支）。

v2.16.0 Chrome 150+ 实战案例（真实用户复盘 2026-07）：强校验表单场景，
AI 必须 attach 用户真实 page target（如 `4252F91C4CC929918E03`），**禁止**用
`Target.createTarget` 自己拉新 tab 后 attach；强校验表单 AI 不驱动表单，让用户
手动点一次触发 POST，1s 内可抓到 200。详见《爬虫分析规范》§3.0.6 实战案例
与《爬虫工具与抓包规范》§3.9.3 实战案例摘要。
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from DrissionPage import ChromiumPage as _DrissionPage_ChromiumPage  # v2.18.0 默认类型
    Page = _DrissionPage_ChromiumPage  # type: ignore
    Request = Any  # DrissionPage DataPacket 与 Playwright Request 字段不同，运行时 duck-type
    Response = Any
except ImportError:  # pragma: no cover
    try:
        from playwright.sync_api import Page, Request, Response  # Playwright fallback
    except ImportError:
        Page = Any  # type: ignore
        Request = Any  # type: ignore
        Response = Any  # type: ignore


# ----------------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------------

# v2.15.0 新增：边界声明常量（仿 DEFAULT_BB_BROWSER_PROBE 模式）
# 实际 HAR 录制与资源所有权遵守由 start_recording/stop_recording 强制执行；
# 本常量仅作为模块 docstring 与 __main__ 输出中的职责声明，提示使用者。
DEFAULT_USER_ACTION_RECORDER: str = (
    "user-action-recorder 仅在 Playwright `connect_over_cdp` 接管已运行用户 Chrome 场景下使用：\n"
    "  - Playwright `record_har_path` 参数在 `connect_over_cdp` 模式不可用，本模块手写 page.on('request'/'response') 落 JSONL；\n"
    "  - 录制/重放全程遵守外部资源所有权铁律：禁止 browser.close() / context.close() / page.close() / kill 用户 Chrome；\n"
    "  - 本模块不替代 popup-handler.py（弹窗清理）也不替代 bb-browser（站点级结构化操作），仅做操作流 + 网络关联录制；\n"
    "  - 录制前应先跑 popup-handler.py 的 cleanup_all() 清弹窗，避免 popup 操作污染录制序列。\n"
    "\n"
    "v2.16.0 补充：start_recording() 调用前，调用方必须先确认（1）Chrome 启动命令\n"
    "已带 --remote-allow-origins=*（Chrome 150+ 必传）；（2）page 参数是 attach 的\n"
    "用户真实 page target，禁止 Target.createTarget 自己拉 tab。强校验表单场景\n"
    "AI 不驱动表单，让用户手动点一次触发 POST。详见《爬虫工具与抓包规范》§3.9.3\n"
    "与《爬虫分析规范》§3.0.6。"
)

# 脱敏黑名单（v1 仅脱敏，不加密）
SENSITIVE_KEYWORDS: list[str] = [
    "password", "passwd", "pwd",
    "token", "secret", "apikey", "api_key", "access_key",
    "cookie", "session", "csrf", "xsrf",
    "信用卡", "卡号", "cvv", "身份证",
]

# 5 类录制操作（v2.15.0 不做 hover/drag/drop/select/right-click，留给 v2.16.0 B-务实）
SUPPORTED_ACTION_TYPES: tuple[str, ...] = ("click", "fill", "press", "scroll", "goto")

# selector 优先级（重放时按顺序尝试）
SELECTOR_PRIORITY_ATTRS: tuple[str, ...] = (
    "data-testid", "id", "name", "aria-label", "placeholder",
)

# triggers 弱关联时间窗（毫秒）—— 操作时间 ± 500ms 内的网络请求归并到 action.triggers
TRIGGER_TIME_WINDOW_MS: int = 500

# 注入到页面的 JS 监听器（捕获 click / input / keydown / scroll）
_INJECT_LISTENERS_JS: str = """
() => {
  if (window.__userActionRecorderInstalled) return;
  window.__userActionRecorderInstalled = true;
  window.__userActionBuffer = [];

  // click
  document.addEventListener('click', (e) => {
    const t = e.target;
    window.__userActionBuffer.push({
      ts: Date.now(), type: 'click',
      tag: t.tagName, id: t.id || null, name: t.name || null,
      data_testid: t.getAttribute('data-testid') || null,
      aria_label: t.getAttribute('aria-label') || null,
      placeholder: t.getAttribute('placeholder') || null,
      text: (t.innerText || '').slice(0, 80),
      css: _cssPath(t),
    });
  }, true);

  // input / fill（v2.19.0 强化：DOM 层按字段属性命中即写 ***REDACTED***）
  const __isSensitiveField = (el) => {
    if (!el || el.nodeType !== 1) return false;
    if ((el.getAttribute('type') || '').toLowerCase() === 'password') return true;
    const attrs = [
      el.id, el.name,
      el.getAttribute('autocomplete'),
      el.getAttribute('aria-label'),
      el.getAttribute('placeholder'),
    ];
    const re = /password|passwd|pwd|token|secret|api[-_]?key|信用卡|卡号|身份证|otp|验证码/i;
    return attrs.some((value) => value && re.test(String(value)));
  };
  document.addEventListener('input', (e) => {
    const t = e.target;
    const raw = t.value;
    const value = __isSensitiveField(t) ? '***REDACTED***' : raw;
    window.__userActionBuffer.push({
      ts: Date.now(), type: 'fill',
      tag: t.tagName, id: t.id || null, name: t.name || null,
      data_testid: t.getAttribute('data-testid') || null,
      aria_label: t.getAttribute('aria-label') || null,
      placeholder: t.getAttribute('placeholder') || null,
      value: value,
      redacted: __isSensitiveField(t),
      css: _cssPath(t),
    });
  }, true);

  // keydown
  document.addEventListener('keydown', (e) => {
    window.__userActionBuffer.push({ts: Date.now(), type: 'press', key: e.key});
  }, true);

  // scroll（节流：每 200ms 一次）
  let _lastScroll = 0;
  document.addEventListener('scroll', () => {
    const now = Date.now();
    if (now - _lastScroll < 200) return;
    _lastScroll = now;
    window.__userActionBuffer.push({ts: now, type: 'scroll', delta_y: window.scrollY});
  }, true);

  // CSS 路径生成（从元素向上构造唯一路径，最长 5 层）
  function _cssPath(el) {
    const parts = [];
    let cur = el;
    while (cur && parts.length < 5 && cur.nodeType === 1) {
      let part = cur.tagName.toLowerCase();
      if (cur.id) { part = '#' + cur.id; parts.unshift(part); break; }
      if (cur.className && typeof cur.className === 'string') {
        const cls = cur.className.trim().split(/\\s+/).slice(0, 2).join('.');
        if (cls) part += '.' + cls;
      }
      parts.unshift(part);
      cur = cur.parentElement;
    }
    return parts.join(' > ');
  }
}
"""


# ----------------------------------------------------------------------------
# 自定义异常
# ----------------------------------------------------------------------------

class RecorderReplayError(Exception):
    """重放失败时抛出的异常（v2.15.0 v1 不做自愈，必抛）。"""
    def __init__(self, step_idx: int, reason: str, action: dict | None = None) -> None:
        self.step_idx = step_idx
        self.reason = reason
        self.action = action
        super().__init__(f"重放 step={step_idx} 失败: {reason}")


# ----------------------------------------------------------------------------
# 数据类
# ----------------------------------------------------------------------------

@dataclass
class ActionRecord:
    """单步操作记录（内存中维护，定期 flush 到 user-actions.json）。"""
    step: int
    timestamp: str
    type: str
    selectors: list[str]
    value: str | None = None
    url: str | None = None
    key: str | None = None
    delta_y: int | None = None
    triggers: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RecorderHandle:
    """录制器句柄——start_recording 返回，stop_recording 接收。"""
    page: Page
    output_dir: str
    actions: list[ActionRecord] = field(default_factory=list)
    har_path: str = ""
    actions_path: str = ""
    _running: bool = False
    _flush_thread: threading.Thread | None = None
    _req_listener: Any = None
    _res_listener: Any = None
    _action_counter: int = 0
    _har_buffer: list[str] = field(default_factory=list)
    _har_lock: threading.Lock = field(default_factory=threading.Lock)
    _actions_lock: threading.Lock = field(default_factory=threading.Lock)


# ----------------------------------------------------------------------------
# 辅助函数
# ----------------------------------------------------------------------------

def _redact_value(value: str | None) -> str | None:
    """按 SENSITIVE_KEYWORDS 脱敏（v2.19.0 起仅作为值内容兜底；DOM 层已按属性判定）。"""
    if value is None or not value:
        return value
    # 兜底匹配：值内容本身含敏感词时强制脱敏（DOM 注入失败/外部 action 也覆盖）
    for kw in SENSITIVE_KEYWORDS:
        if kw.lower() in value.lower():
            return "***REDACTED***"
    return value


_HEADER_SENSITIVE_KEYS: tuple[str, ...] = (
    "authorization",
    "cookie",
    "set-cookie",
    "x-csrf-token",
    "csrf-token",
    "x-xsrf-token",
    "x-api-key",
    "apikey",
    "x-auth-token",
    "x-token",
)


def _redact_headers(headers: Any) -> dict[str, str]:
    """对请求/响应 Headers 做大小写不敏感的敏感字段脱敏。"""

    if not headers:
        return {}
    try:
        items = dict(headers).items()
    except Exception:
        try:
            items = list(headers)
        except Exception:
            return {}
    safe: dict[str, str] = {}
    for key, value in items:
        normalized = str(key or "").lower()
        if normalized in _HEADER_SENSITIVE_KEYS or SENSITIVE_KEYWORDS and any(
            kw.lower() in normalized
            for kw in SENSITIVE_KEYWORDS
        ):
            safe[str(key)] = "***REDACTED***"
        else:
            text = str(value) if value is not None else ""
            if any(kw.lower() in text.lower() for kw in SENSITIVE_KEYWORDS) and "token" in normalized:
                safe[str(key)] = "***REDACTED***"
            else:
                safe[str(key)] = text
    return safe


def _redact_post_data(post_data: Any) -> Any:
    """对请求体/表单/JSON 内的敏感字段统一脱敏。"""

    if post_data is None:
        return None
    if isinstance(post_data, (bytes, bytearray)):
        try:
            text = post_data.decode("utf-8", errors="replace")
        except Exception:
            return "***BINARY***"
        return _redact_post_data(text)
    if isinstance(post_data, str):
        # form-urlencoded 风格字段也走敏感键判定
        if "=" in post_data and "&" in post_data and "\n" not in post_data:
            parts: list[str] = []
            for segment in post_data.split("&"):
                if "=" not in segment:
                    parts.append(segment)
                    continue
                key, _, value = segment.partition("=")
                if any(kw in key.lower() for kw in SENSITIVE_KEYWORDS) or key.lower() in _HEADER_SENSITIVE_KEYS:
                    parts.append(f"{key}=***REDACTED***")
                else:
                    parts.append(segment)
            return "&".join(parts)[:2000]
        return _redact_value(post_data)
    return post_data


def _redact_body_preview(body: str | None) -> str | None:
    """对响应体预览按敏感键做粗粒度清洗，避免敏感字段直显。"""

    if body is None:
        return None
    cleaned = body[:1024]
    for kw in SENSITIVE_KEYWORDS:
        cleaned = re.sub(
            rf'("{re.escape(kw)}"\s*:\s*)"[^"]*"',
            r'\1"***"',
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            rf'({re.escape(kw)}\s*[:=]\s*)([^\s,&;{{}}]+)',
            r'\1***',
            cleaned,
            flags=re.IGNORECASE,
        )
    return cleaned


def _css_path_fallback(el: Any) -> str:
    """Python 端兜底：从 ElementHandle 推导 CSS 路径（DOM 监听器未注入时使用）。"""
    try:
        # 优先用元素自身属性拼接
        attrs = el.evaluate(
            "(node) => ({tag: node.tagName.toLowerCase(), id: node.id, "
            "cls: (node.className && typeof node.className === 'string') ? node.className : '', "
            "data_testid: node.getAttribute('data-testid')})"
        )
        tag = attrs.get("tag", "div")
        if attrs.get("id"):
            return f"#{attrs['id']}"
        if attrs.get("data_testid"):
            return f"[data-testid='{attrs['data_testid']}']"
        cls = (attrs.get("cls") or "").strip().split()[:2]
        if cls:
            return f"{tag}.{'.'.join(cls)}"
        return tag
    except Exception:
        return "body"


def _selector_candidates(action: dict[str, Any]) -> list[str]:
    """从录制时的 selectors 列表中按优先级重排序（v1 硬编码优先级）。"""
    selectors = action.get("selectors", []) or []
    # 录制时已按优先级排序，重放时按原顺序尝试
    return [s for s in selectors if s]


def _link_triggers(
    actions: list[ActionRecord],
    har_entries: list[dict[str, Any]],
    window_ms: int = TRIGGER_TIME_WINDOW_MS,
) -> None:
    """弱关联：把每条网络请求归并到时间窗内最近的 action.triggers（v1 不做语义解析）。"""
    # 收集 action 时间戳（毫秒）
    action_ts: list[tuple[int, int]] = []  # (ts_ms, action_index)
    for i, a in enumerate(actions):
        try:
            ts_ms = int(datetime.fromisoformat(a.timestamp).timestamp() * 1000)
        except Exception:
            continue
        action_ts.append((ts_ms, i))

    for entry in har_entries:
        if entry.get("kind") != "response":
            continue  # 只关联响应（请求↔响应合并在客户端做）
        try:
            entry_ts = int(datetime.fromisoformat(entry["ts"]).timestamp() * 1000)
        except Exception:
            continue
        # 找时间窗内最近的 action
        best_idx = -1
        best_delta = window_ms + 1
        for ts_ms, idx in action_ts:
            delta = abs(entry_ts - ts_ms)
            if delta <= window_ms and delta < best_delta:
                best_delta = delta
                best_idx = idx
        if best_idx >= 0:
            actions[best_idx].triggers.append({
                "url": entry.get("url", ""),
                "method": entry.get("method", ""),
                "status": entry.get("status"),
            })


def _flush_loop(handle: RecorderHandle) -> None:
    """后台 flush 线程（daemon=True，进程结束自动退出，v2.15.0 简化）。"""
    while handle._running:
        time.sleep(1.0)
    # handle._running 置 False 后最后一次落 HAR buffer
    with handle._har_lock:
        if handle._har_buffer:
            with open(handle.har_path, "a", encoding="utf-8") as f:
                f.write("\n".join(handle._har_buffer) + "\n")
            handle._har_buffer.clear()


def _har_append(handle: RecorderHandle, kind: str, payload: Any) -> None:
    """把 request/response 追加到 har buffer（线程安全）。

    **v2.18.0 DrissionPage 适配**：DrissionPage 的 DataPacket 属性名为
    `url` / `method` / `headers` / `post_data` / `status` / `body`，与 Playwright
    `Request` / `Response` 大体一致（duck type 即可）。响应体 `body` 在 DrissionPage
    是 `response.body`（bytes），Playwright 是 `response.body()`（方法）—— 已用
    `callable(payload.body)` 兼容。
    """
    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds"),
        "kind": kind,
    }
    if kind == "request":
        entry["url"] = payload.url
        entry["method"] = payload.method
        try:
            entry["headers"] = _redact_headers(payload.headers)
        except Exception:
            entry["headers"] = {}
        try:
            entry["post_data"] = _redact_post_data(payload.post_data)
        except Exception:
            entry["post_data"] = None
    elif kind == "response":
        entry["url"] = payload.url
        entry["status"] = payload.status
        try:
            entry["headers"] = _redact_headers(payload.headers)
        except Exception:
            entry["headers"] = {}
        # 响应体过大时不落（避免 HAR 爆盘；只标记 status）
        # v2.18.0 兼容 DrissionPage response.body（属性）与 Playwright response.body()（方法）
        # v2.19.0 增加：响应体预览按敏感键再次脱敏，避免 Cookie/token 出现在 body_preview。
        try:
            body = payload.body() if callable(payload.body) else payload.body
            if body is not None and len(body) < 1024 * 64:  # 64KB 阈值
                if isinstance(body, bytes):
                    preview = body[:1024].decode("utf-8", errors="replace")
                else:
                    preview = str(body)[:1024]
                entry["body_preview"] = _redact_body_preview(preview)
        except Exception:
            pass

    line = json.dumps(entry, ensure_ascii=False)
    with handle._har_lock:
        handle._har_buffer.append(line)
        # 每 50 条落盘一次（减少 IO）
        if len(handle._har_buffer) >= 50:
            with open(handle.har_path, "a", encoding="utf-8") as f:
                f.write("\n".join(handle._har_buffer) + "\n")
            handle._har_buffer.clear()


def _drission_listen_loop(handle: RecorderHandle) -> None:
    """v2.18.0 DrissionPage HAR 录制后台线程：用 page.listen.wait(timeout=0.5) 轮询。

    替代 Playwright `page.on("request"/"response")` 回调模式。
    DrissionPage 的 listen API 是阻塞的（wait() 会等下一个匹配包），故用轮询 + 短 timeout
    实现非阻塞采集，循环到 handle._running = False 退出。
    """
    page = handle.page
    while handle._running:
        try:
            # DrissionPage: page.listen.wait(timeout=0.5) 返回 DataPacket 或 None
            pkt = page.listen.wait(timeout=0.5)
        except Exception:
            pkt = None
        if pkt is None:
            continue
        # 区分 request / response：DrissionPage DataPacket 有 .is_request 属性
        try:
            if getattr(pkt, "is_request", True):
                _har_append(handle, "request", pkt)
            else:
                _har_append(handle, "response", pkt)
        except Exception:
            continue
    # handle._running 置 False 后最后一次落 HAR buffer
    with handle._har_lock:
        if handle._har_buffer:
            with open(handle.har_path, "a", encoding="utf-8") as f:
                f.write("\n".join(handle._har_buffer) + "\n")
            handle._har_buffer.clear()


def _replay_one(page: Page, action: dict[str, Any]) -> None:
    """重放单步操作（按 selector 优先级匹配）。**v2.18.0 DrissionPage 适配**：
    `page.locator(sel).first` + `loc.count()` + `loc.is_visible()` 改为
    `page.ele('css:sel', timeout=1)` + `el.states.is_displayed`。
    **`page.mouse.wheel()` 改为 `page.actions.scroll(delta_y, delta_x)`**（v2.18.2
    修正：DrissionPage `page.actions.wheel` 不存在，正确 API 为
    `page.actions.scroll(delta_y=0, delta_x=0, on_ele=None)`，签名见
    `DrissionPage._units.actions.Actions.scroll`；`page.mouse` 在 DrissionPage
    ChromiumPage 上也不存在）。
    `page.evaluate()` 改为 `page.run_js()`（DrissionPage 也有 page.evaluate，但
    推荐 page.run_js 以保持与官方文档一致）。
    """
    action_type = action.get("type")
    if action_type not in SUPPORTED_ACTION_TYPES:
        raise RecorderReplayError(
            step_idx=action.get("step", -1),
            reason=f"不支持的操作类型: {action_type}",
            action=action,
        )

    if action_type == "goto":
        url = action.get("url")
        if not url:
            raise RecorderReplayError(step_idx=action["step"], reason="goto 操作缺少 url", action=action)
        page.get(url)  # v2.18.0 DrissionPage 化：page.get(url) 替代 page.goto(url, timeout=...)
        return

    if action_type == "press":
        # DrissionPage 与 Playwright 都支持 page.keyboard.press(key)
        page.keyboard.press(action.get("key", ""))
        return

    if action_type == "scroll":
        # v2.18.2 修正：DrissionPage `page.actions.scroll(delta_y, delta_x)`（不是 `wheel`）
        page.actions.scroll(int(action.get("delta_y", 0)))
        return

    # click / fill：需要 selector 匹配
    selectors = _selector_candidates(action)
    if not selectors:
        raise RecorderReplayError(
            step_idx=action["step"],
            reason="缺少 selector 列表",
            action=action,
        )

    matched_el = None
    for sel in selectors:
        try:
            # v2.18.0 DrissionPage 化：page.ele('css:sel', timeout=1) 替代
            # 老版 Playwright 的 page.locator(sel).first + loc.count() + loc.is_visible
            # DrissionPage ele() 不存在或不可见时抛异常，需 try/except
            el = page.ele(f"css:{sel}", timeout=1)
            if el and el.states.is_displayed:
                matched_el = el
                break
        except Exception:
            continue

    if matched_el is None:
        raise RecorderReplayError(
            step_idx=action["step"],
            reason=f"selector 全失效: {selectors}",
            action=action,
        )

    if action_type == "click":
        matched_el.click()  # DrissionPage 与 Playwright 同名 click()
    elif action_type == "fill":
        value = action.get("value", "")
        # v2.18.0 DrissionPage 化：el.input(value) 替代 el.fill(value, timeout=3000)
        matched_el.input(value)


# ----------------------------------------------------------------------------
# 公开函数（3 个）
# ----------------------------------------------------------------------------

def start_recording(
    page: Page,
    output_dir: str = "01-目标画像/录制/",
) -> RecorderHandle:
    """
    启动录制（v2.15.0 新增，v2.18.0 DrissionPage 适配）。

    Args:
        page: DrissionPage ChromiumPage 对象（v2.18.0 默认）/ Playwright Page（fallback）
        output_dir: 录制文件输出目录（自动 mkdir）

    Returns:
        RecorderHandle（dataclass 句柄）—— 传给 stop_recording() 用于定位状态

    行为（**v2.18.0 DrissionPage 化**）：
        - HAR 监听：DrissionPage 走 `page.listen.start()` + 后台轮询线程
          `_drission_listen_loop`（callable wait 模式）；Playwright fallback 走
          `page.on("request"/"response")` 回调模式（duck type 探测）
        - 注入 DOM 监听器：DrissionPage 用 `page.run_js()`，Playwright 用 `page.evaluate()`
          （duck type 兼容）
        - 启动后台 flush 线程（防进程崩溃丢失）
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    har_path = str(Path(output_dir) / "user-session.har.jsonl")
    actions_path = str(Path(output_dir) / "user-actions.json")

    # 清空旧文件（避免和历史录制混淆）
    for p in (har_path, actions_path):
        if Path(p).exists():
            Path(p).unlink()

    handle = RecorderHandle(
        page=page,
        output_dir=output_dir,
        har_path=har_path,
        actions_path=actions_path,
        _running=True,
    )

    # 1) HAR 监听——v2.18.0 DrissionPage 化（v2.18.2 修 duck-type bug）
    # DrissionPage 走 page.listen.start() + 后台轮询；Playwright 走 page.on() 回调
    # v2.18.2 修复：DrissionPage 的 `page.listen` 是 property（返回 Listener 实例），
    # `callable(page.listen)` 永远为 False。原 v2.18.0 写法 `callable(...)` 会误入 Playwright
    # fallback 分支并触发 DrissionPage 没有的 `page.on()` AttributeError。正确判断仅看 `hasattr`：
    if hasattr(page, "listen"):
        # DrissionPage 接管模式
        try:
            page.listen.start()  # 监听所有请求/响应
        except Exception:
            pass
        handle._flush_thread = threading.Thread(
            target=_drission_listen_loop, args=(handle,), daemon=True, name="user-action-drission-listen"
        )
        handle._flush_thread.start()
    else:
        # Playwright fallback 路径
        def _on_request(req: Request) -> None:
            _har_append(handle, "request", req)

        def _on_response(res: Response) -> None:
            _har_append(handle, "response", res)

        handle._req_listener = _on_request
        handle._res_listener = _on_response
        page.on("request", _on_request)
        page.on("response", _on_response)
        handle._flush_thread = threading.Thread(
            target=_flush_loop, args=(handle,), daemon=True, name="user-action-flush"
        )
        handle._flush_thread.start()

    # 2) 注入 DOM 监听器（首次失败也不阻塞，主链路仍是 HAR）
    # v2.18.0 DrissionPage 化：DrissionPage 用 page.run_js()；Playwright 用 page.evaluate()
    try:
        if hasattr(page, "run_js"):
            page.run_js(_INJECT_LISTENERS_JS)
        else:
            page.evaluate(_INJECT_LISTENERS_JS)
    except Exception:
        pass

    return handle


def stop_recording(handle: RecorderHandle) -> str:
    """
    停止录制并落盘（v2.15.0 新增，v2.18.0 DrissionPage 适配）。

    Args:
        handle: start_recording() 返回的 RecorderHandle

    Returns:
        actions_json_path: 落盘后的 user-actions.json 绝对路径

    行为（**v2.18.0 DrissionPage 化**）：
        - 注销监听器：DrissionPage 用 `page.listen.stop()`；Playwright 用 `page.remove_listener()`
        - 停止后台线程（2s join timeout）
        - 拉取 DOM 监听器 buffer（DrissionPage 用 `page.run_js()`，Playwright 用 `page.evaluate()`）
        - 把 RecorderHandle.actions 序列化为 user-actions.json（含 triggers 弱关联）
    """
    handle._running = False
    if handle._flush_thread is not None:
        handle._flush_thread.join(timeout=2.0)
        handle._flush_thread = None

    # 注销监听器——v2.18.0 DrissionPage 化（v2.18.2 修 duck-type bug，匹配 start_recording）
    if hasattr(handle.page, "listen"):
        # DrissionPage 默认接管模式，停止 page.listen 监听
        try:
            handle.page.listen.stop()
        except Exception:
            pass
    else:
        # Playwright fallback 路径：用 page.remove_listener 注销
        if handle._req_listener is not None:
            try:
                handle.page.remove_listener("request", handle._req_listener)
            except Exception:
                pass
        if handle._res_listener is not None:
            try:
                handle.page.remove_listener("response", handle._res_listener)
            except Exception:
                pass

    # v2.18.2 关键修复：flush 剩余 HAR buffer（避免 stop 时丢包或留半行 JSON）
    with handle._har_lock:
        if getattr(handle, "_har_buffer", None):
            with open(handle.har_path, "a", encoding="utf-8") as f:
                if handle._har_buffer:
                    f.write("\n".join(handle._har_buffer) + "\n")
                handle._har_buffer.clear()

    # 拉取 DOM 监听器 buffer（注入的 click/fill/press/scroll）
    # v2.18.0 DrissionPage 化：DrissionPage 用 page.run_js()，Playwright 用 page.evaluate()
    try:
        if hasattr(handle.page, "run_js"):
            dom_actions: list[dict[str, Any]] = handle.page.run_js(
                "() => { const buf = window.__userActionBuffer || []; "
                "window.__userActionBuffer = []; return buf; }"
            ) or []
        else:
            dom_actions = handle.page.evaluate(
                "() => { const buf = window.__userActionBuffer || []; "
                "window.__userActionBuffer = []; return buf; }"
            ) or []
    except Exception:
        dom_actions = []

    # 把 DOM 事件转成 ActionRecord
    for raw in dom_actions:
        if raw.get("type") not in SUPPORTED_ACTION_TYPES:
            continue
        handle._action_counter += 1
        selectors: list[str] = []
        for attr in SELECTOR_PRIORITY_ATTRS:
            v = raw.get(attr)
            if v:
                if attr == "id":
                    selectors.append(f"#{v}")
                elif attr == "data_testid":
                    selectors.append(f"[data-testid='{v}']")
                else:
                    selectors.append(f"[{attr}='{v}']")
        if raw.get("css"):
            selectors.append(raw["css"])
        if raw.get("text") and raw["type"] == "click":
            # text 作为最后兜底（仅 click 类型用 :has-text）
            safe_text = re.sub(r"[^\w一-龥\s]", "", raw["text"])[:40].strip()
            if safe_text:
                selectors.append(f":has-text('{safe_text}')")

        ts_ms = int(raw.get("ts", 0))
        ts_iso = (
            datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            .astimezone()
            .isoformat(timespec="milliseconds")
        )
        value = raw.get("value")
        action = ActionRecord(
            step=handle._action_counter,
            timestamp=ts_iso,
            type=raw["type"],
            selectors=selectors,
            value=_redact_value(value),
            key=raw.get("key"),
            delta_y=raw.get("delta_y"),
        )
        handle.actions.append(action)

    # 弱关联 triggers：读 HAR 全文，按时间窗归并
    har_entries: list[dict[str, Any]] = []
    if Path(handle.har_path).exists():
        with open(handle.har_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    har_entries.append(json.loads(line))
                except Exception:
                    continue
    _link_triggers(handle.actions, har_entries)

    # 落盘 user-actions.json
    doc: dict[str, Any] = {
        "version": "1.0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "page_url": handle.page.url,
        "actions": [
            {
                "step": a.step,
                "timestamp": a.timestamp,
                "type": a.type,
                "selectors": a.selectors,
                "value": a.value,
                "url": a.url,
                "key": a.key,
                "delta_y": a.delta_y,
                "triggers": a.triggers,
            }
            for a in handle.actions
        ],
    }
    with open(handle.actions_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    return str(Path(handle.actions_path).resolve())


def replay_actions(
    page: Page,
    actions_json_path: str,
    screenshot_each_step: bool = False,
) -> dict[str, Any]:
    """
    重放已录制操作（v2.15.0 新增）。

    Args:
        page: Playwright Page 对象（用户接管 Chrome 的 page）
        actions_json_path: user-actions.json 路径
        screenshot_each_step: 是否每步截图（默认 False；True 时输出 02-step-{i:03d}.png）

    Returns:
        {
            "total": int,         # 总步数
            "success": int,       # 成功步数
            "failed": int,        # 失败步数
            "failed_steps": [int, ...],  # 失败步骤索引（从 0 开始）
            "duration_s": float,
        }

    行为：
        - selector 按录制时优先级顺序匹配
        - 任一步失败：抛 RecorderReplayError（v1 不做自愈，符合 YAGNI）
    """
    # v2.18.2 防御性读取：文件不存在 / JSON 损坏 / 缺 `actions` 键 → 返回空结果而非崩溃
    actions: list[dict[str, Any]] = []
    try:
        raw = json.loads(Path(actions_json_path).read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("actions"), list):
            actions = raw["actions"]
        elif isinstance(raw, list):
            actions = raw
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    result: dict[str, Any] = {
        "total": len(actions),
        "success": 0,
        "failed": 0,
        "failed_steps": [],
        "duration_s": 0.0,
    }
    t0 = time.monotonic()
    for i, action in enumerate(actions):
        try:
            _replay_one(page, action)
            result["success"] += 1
        except RecorderReplayError:
            result["failed"] += 1
            result["failed_steps"].append(i)
            if screenshot_each_step:
                try:
                    # v2.18.0 DrissionPage 化：page.get_screenshot() 替代 page.screenshot()
                    _screenshot(page, f"02-step-{i:03d}-FAILED.png")
                except Exception:
                    pass
            raise  # v1 必抛（不做自愈）
        except Exception as e:
            result["failed"] += 1
            result["failed_steps"].append(i)
            raise RecorderReplayError(step_idx=i, reason=str(e), action=action) from e

        if screenshot_each_step:
            try:
                # v2.18.0 DrissionPage 化：page.get_screenshot() 替代 page.screenshot()
                _screenshot(page, f"02-step-{i:03d}.png")
            except Exception:
                pass

    result["duration_s"] = time.monotonic() - t0
    return result


def _screenshot(page: Page, path: str) -> None:
    """截图 duck-type 封装：DrissionPage 用 `page.get_screenshot(path=...)`，
    Playwright 用 `page.screenshot(path=...)`。**v2.18.0 DrissionPage 适配**。"""
    if hasattr(page, "get_screenshot") and callable(getattr(page, "get_screenshot", None)):
        page.get_screenshot(path=path)
    else:
        page.screenshot(path=path)


# ----------------------------------------------------------------------------
# 顶层调用入口（便于 python -m 直接调用）
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    print("user-action-recorder.py 是 mcpowers-crawler-reverse v2.15.0 新增、v2.18.0 DrissionPage 适配的工具脚本")
    print("详细用法见《爬虫工具与抓包规范》§8（用户操作录制与重放）")
    print()
    print("公开 API：")
    print("  - start_recording(page, output_dir='01-目标画像/录制/') -> RecorderHandle")
    print("  - stop_recording(handle) -> str  # 返回 user-actions.json 绝对路径")
    print("  - replay_actions(page, actions_json_path, screenshot_each_step=False) -> dict")
    print()
    print("v2.18.0 DrissionPage 接管示例：")
    print("  from DrissionPage import ChromiumPage, ChromiumOptions")
    print("  page = ChromiumPage(addr_or_opts=ChromiumOptions().set_local_port(9222))")
    print("  handle = start_recording(page)")
    print("  # ... 用户操作 ...")
    print("  stop_recording(handle)")
    print()
    print("v2.15.0 新增常量：")
    print("  - DEFAULT_USER_ACTION_RECORDER  # 边界声明（v2.18.0 改为 DrissionPage listen.start() 模式）")
    print("  - SUPPORTED_ACTION_TYPES  # 5 类操作：click / fill / press / scroll / goto")
    print("  - SELECTOR_PRIORITY_ATTRS  # selector 优先级：data-testid > id > name > aria-label > placeholder")
    print("  - SENSITIVE_KEYWORDS  # 脱敏黑名单（password / token / cookie 等）")
    print("  - TRIGGER_TIME_WINDOW_MS  # 弱关联时间窗 ±500ms")
    print()
    print("SOP 串联：popup-handler.cleanup_all() -> start_recording() -> 用户操作 -> ")
    print("         stop_recording() -> replay_actions() 可选")
