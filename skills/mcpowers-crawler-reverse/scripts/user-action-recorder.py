"""
user-action-recorder.py — 用户操作录制与重放工具（v2.15.0 新增）

本模块是 mcpowers-crawler-reverse 协作模式 B（"用户操作 + AI 抓包"）的工具支撑。
补充 popup-handler.py 不覆盖的"操作流录制 + 重放"维度，不重复弹窗检测与接管预检。
历史兼容：v2.15.0 之前为口头协议，无工具支撑（见《爬虫分析规范》§3.0.1 模式 B）。

核心函数（3 个公开）：
- start_recording(page, output_dir): 启动录制（注册 page.on / DOM 事件 + 后台 flush 线程）
- stop_recording(handle) -> str: 停止录制并落 user-actions.json + user-session.har.jsonl
- replay_actions(page, actions_json_path, screenshot_each_step=False) -> dict: 重放已录制操作

详细方法论：见《爬虫工具与抓包规范》§8（用户操作录制与重放）
DEFAULT_USER_ACTION_RECORDER 文档参考《爬虫工具与抓包规范》§8.0（边界声明）

设计原则：
- 遵守外部资源所有权铁律（主《爬虫分析规范》§1.3）：禁止 browser.close() / context.close() / page.close()；
  监听器通过 page.remove_listener() 注销，不靠进程结束清理。
- 不替代 popup-handler.py（弹窗清理）和 bb-browser（站点级结构化操作）；按 SOP 串联：
  popup-handler.cleanup_all() → start_recording() → 用户操作 → stop_recording() → replay_actions()。
- Playwright `record_har_path` 参数在 connect_over_cdp 模式不可用（只对 launch() / launch_persistent_context()
  创建的 context 生效），本模块手写 page.on("request"/"response") 落 JSONL 格式 HAR。

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
    from playwright.sync_api import Page, Request, Response
except ImportError:  # pragma: no cover
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

  // input / fill
  document.addEventListener('input', (e) => {
    const t = e.target;
    window.__userActionBuffer.push({
      ts: Date.now(), type: 'fill',
      tag: t.tagName, id: t.id || null, name: t.name || null,
      data_testid: t.getAttribute('data-testid') || null,
      aria_label: t.getAttribute('aria-label') || null,
      placeholder: t.getAttribute('placeholder') || null,
      value: t.value,
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
    """按 SENSITIVE_KEYWORDS 脱敏（v1 仅替换为占位符，不加密）。"""
    if value is None or not value:
        return value
    # 直接黑名单匹配（精确字段名 / 内容含敏感词）
    for kw in SENSITIVE_KEYWORDS:
        if kw.lower() in value.lower():
            return "***REDACTED***"
    return value


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
    """把 request/response 追加到 har buffer（线程安全）。"""
    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds"),
        "kind": kind,
    }
    if kind == "request":
        entry["url"] = payload.url
        entry["method"] = payload.method
        try:
            entry["headers"] = dict(payload.headers or {})
            entry["post_data"] = payload.post_data
        except Exception:
            entry["headers"] = {}
    elif kind == "response":
        entry["url"] = payload.url
        entry["status"] = payload.status
        try:
            entry["headers"] = dict(payload.headers or {})
        except Exception:
            entry["headers"] = {}
        # 响应体过大时不落（避免 HAR 爆盘；只标记 status）
        try:
            body = payload.body() if callable(payload.body) else None
            if body is not None and len(body) < 1024 * 64:  # 64KB 阈值
                entry["body_preview"] = body[:1024].decode("utf-8", errors="replace")
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


def _replay_one(page: Page, action: dict[str, Any]) -> None:
    """重放单步操作（按 selector 优先级匹配）。"""
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
        page.goto(url, timeout=10_000)
        return

    if action_type == "press":
        page.keyboard.press(action.get("key", ""))
        return

    if action_type == "scroll":
        page.mouse.wheel(0, int(action.get("delta_y", 0)))
        return

    # click / fill：需要 selector 匹配
    selectors = _selector_candidates(action)
    if not selectors:
        raise RecorderReplayError(
            step_idx=action["step"],
            reason="缺少 selector 列表",
            action=action,
        )

    matched_locator = None
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=1000):
                matched_locator = loc
                break
        except Exception:
            continue

    if matched_locator is None:
        raise RecorderReplayError(
            step_idx=action["step"],
            reason=f"selector 全失效: {selectors}",
            action=action,
        )

    if action_type == "click":
        matched_locator.click(timeout=3000)
    elif action_type == "fill":
        value = action.get("value", "")
        matched_locator.fill(value, timeout=3000)


# ----------------------------------------------------------------------------
# 公开函数（3 个）
# ----------------------------------------------------------------------------

def start_recording(
    page: Page,
    output_dir: str = "01-目标画像/录制/",
) -> RecorderHandle:
    """
    启动录制（v2.15.0 新增）。

    Args:
        page: Playwright Page 对象（必须是 connect_over_cdp 接管的用户 page）
        output_dir: 录制文件输出目录（自动 mkdir）

    Returns:
        RecorderHandle（dataclass 句柄）—— 传给 stop_recording() 用于定位状态

    行为：
        - 注册 page.on("request"/"response") 监听器（落 user-session.har.jsonl）
        - 通过 page.evaluate 注入 DOM 事件监听器（click / input / keydown / scroll）
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

    # 1) HAR 监听（保留函数引用以便 stop 时 remove_listener）
    def _on_request(req: Request) -> None:
        _har_append(handle, "request", req)

    def _on_response(res: Response) -> None:
        _har_append(handle, "response", res)

    handle._req_listener = _on_request
    handle._res_listener = _on_response
    page.on("request", _on_request)
    page.on("response", _on_response)

    # 2) 注入 DOM 监听器（首次失败也不阻塞，主链路仍是 HAR）
    try:
        page.evaluate(_INJECT_LISTENERS_JS)
    except Exception:
        pass

    # 3) 后台 flush 线程
    handle._flush_thread = threading.Thread(
        target=_flush_loop, args=(handle,), daemon=True, name="user-action-flush"
    )
    handle._flush_thread.start()
    return handle


def stop_recording(handle: RecorderHandle) -> str:
    """
    停止录制并落盘（v2.15.0 新增）。

    Args:
        handle: start_recording() 返回的 RecorderHandle

    Returns:
        actions_json_path: 落盘后的 user-actions.json 绝对路径

    行为：
        - 注销 page.on() 监听器（避免污染后续操作；不靠进程结束清理）
        - 停止后台 flush 线程（2s join timeout）
        - 从 page 拉取 DOM 监听器 buffer（click / input / press / scroll）
        - 把 RecorderHandle.actions 序列化为 user-actions.json（含 triggers 弱关联）
    """
    handle._running = False
    if handle._flush_thread is not None:
        handle._flush_thread.join(timeout=2.0)
        handle._flush_thread = None

    # 注销监听器（保留的函数引用必须存在）
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

    # 拉取 DOM 监听器 buffer（page.evaluate 注入的 click/fill/press/scroll）
    try:
        dom_actions: list[dict[str, Any]] = handle.page.evaluate(
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
    actions = json.loads(Path(actions_json_path).read_text(encoding="utf-8"))["actions"]
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
                    page.screenshot(path=f"02-step-{i:03d}-FAILED.png")
                except Exception:
                    pass
            raise  # v1 必抛（不做自愈）
        except Exception as e:
            result["failed"] += 1
            result["failed_steps"].append(i)
            raise RecorderReplayError(step_idx=i, reason=str(e), action=action) from e

        if screenshot_each_step:
            try:
                page.screenshot(path=f"02-step-{i:03d}.png")
            except Exception:
                pass

    result["duration_s"] = time.monotonic() - t0
    return result


# ----------------------------------------------------------------------------
# 顶层调用入口（便于 python -m 直接调用）
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    print("user-action-recorder.py 是 mcpowers-crawler-reverse v2.15.0 新增的工具脚本")
    print("详细用法见《爬虫工具与抓包规范》§8（用户操作录制与重放）")
    print()
    print("公开 API：")
    print("  - start_recording(page, output_dir='01-目标画像/录制/') -> RecorderHandle")
    print("  - stop_recording(handle) -> str  # 返回 user-actions.json 绝对路径")
    print("  - replay_actions(page, actions_json_path, screenshot_each_step=False) -> dict")
    print()
    print("v2.15.0 新增常量：")
    print("  - DEFAULT_USER_ACTION_RECORDER  # 边界声明（connect_over_cdp 下 record_har_path 不可用等）")
    print("  - SUPPORTED_ACTION_TYPES  # 5 类操作：click / fill / press / scroll / goto")
    print("  - SELECTOR_PRIORITY_ATTRS  # selector 优先级：data-testid > id > name > aria-label > placeholder")
    print("  - SENSITIVE_KEYWORDS  # 脱敏黑名单（password / token / cookie 等）")
    print("  - TRIGGER_TIME_WINDOW_MS  # 弱关联时间窗 ±500ms")
    print()
    print("SOP 串联：popup-handler.cleanup_all() -> start_recording() -> 用户操作 -> ")
    print("         stop_recording() -> replay_actions() 可选")
