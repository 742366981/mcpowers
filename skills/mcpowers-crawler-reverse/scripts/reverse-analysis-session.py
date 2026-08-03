"""
reverse-analysis-session.py — 逆向分析工作区与 Web 协作会话编排工具（v2.19.0 新增）

本工具把逆向任务起手式固定为可执行状态机，避免 AI 自由拼接步骤：

1. 第一动作创建标准中文分析目录和《分析计划.md》；
2. Web 任务自动识别宿主 OS、浏览器路径/版本和 CDP 状态；
3. 打开目标站前执行浏览器环境与指纹一致性审计；
4. 默认进入“用户操作 + AI 持续监控”，并复用 popup-handler.py 与
   user-action-recorder.py；
5. 停止时关联操作、网络和 JS 运行时证据。

公开命令：
- init：初始化任意逆向目标的工作区；
- web-start：启动 Web 协作会话，命令会持续运行直到收到停止信号；
- web-stop：请求当前会话正常停止并落盘；
- status：查看当前会话状态。

资源所有权铁律：通过 CDP 接管的 browser/context/page/tab 均不可关闭。本工具即使
启动了 task-owned 浏览器，也默认保留浏览器供用户继续检查，不调用 close/kill。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import re
import shutil
import signal
import socket  # v2.20.0：pick_free_port 用 socket.bind(('127.0.0.1', 0)) 探测 OS ephemeral 端口
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable
from urllib.parse import urlparse


# ----------------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------------

STATE_WORKSPACE_READY = "WORKSPACE_READY"
STATE_ENV_READY = "ENV_READY"
STATE_BROWSER_READY = "BROWSER_READY"
STATE_FINGERPRINT_READY = "FINGERPRINT_READY"
STATE_MONITORING = "MONITORING"
STATE_STOPPED = "STOPPED"
STATE_FAILED = "FAILED"

STATE_ORDER: tuple[str, ...] = (
    STATE_WORKSPACE_READY,
    STATE_ENV_READY,
    STATE_BROWSER_READY,
    STATE_FINGERPRINT_READY,
    STATE_MONITORING,
    STATE_STOPPED,
)

WORKSPACE_DIRS: tuple[str, ...] = (
    "01-目标画像/弹窗截图",
    "01-目标画像/录制",
    "02-接口分析/响应样本",
    "03-逆向攻坚/钩子",
    "04-模块封装",
)

SENSITIVE_KEY_RE = re.compile(
    r"password|passwd|pwd|token|secret|api[-_]?key|access[-_]?key|authorization|"
    r"cookie|session|csrf|xsrf|credit[-_]?card|card[-_]?number|cvv|身份证|卡号|密码|令牌",
    re.IGNORECASE,
)

MAX_JS_EVENT_CHARS = 1000
MAX_JS_EVENTS_PER_FLUSH = 200
MAX_JS_LOG_BYTES = 5 * 1024 * 1024
EVIDENCE_WINDOW_MS = 1000

JS_MONITOR_SCRIPT = r"""
() => {
  if (window.__reverseAnalysisMonitorInstalled) return true;
  window.__reverseAnalysisMonitorInstalled = true;
  window.__reverseAnalysisBuffer = [];
  window.__reverseAnalysisRate = {second: 0, count: 0};

  const safeText = (value, maxLength = 1000) => {
    let text = '';
    try {
      if (value instanceof Error) text = value.stack || value.message || String(value);
      else if (typeof value === 'string') text = value;
      else text = JSON.stringify(value);
    } catch (_) {
      text = String(value);
    }
    return text.slice(0, maxLength);
  };

  const pushEvent = (type, data = {}) => {
    const now = Date.now();
    const second = Math.floor(now / 1000);
    if (window.__reverseAnalysisRate.second !== second) {
      window.__reverseAnalysisRate = {second, count: 0};
    }
    if (window.__reverseAnalysisRate.count >= 20) return;
    window.__reverseAnalysisRate.count += 1;
    const buffer = window.__reverseAnalysisBuffer;
    if (buffer.length >= 1000) buffer.shift();
    buffer.push({ts_ms: now, type, ...data});
  };

  for (const entry of performance.getEntriesByType('resource')) {
    if (entry.initiatorType === 'script') {
      pushEvent('script-existing', {url: safeText(entry.name, 500), note: '已加载脚本只能拿到 URL，源码内容无法在 ready 时间点之前补采'});
    }
  }

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.initiatorType === 'script') {
          pushEvent('script-load', {url: safeText(entry.name, 500)});
        }
      }
    });
    observer.observe({type: 'resource', buffered: true});
    window.__reverseAnalysisPerformanceObserver = observer;
  } catch (_) {}

  window.addEventListener('error', (event) => {
    pushEvent('window-error', {
      message: safeText(event.message),
      source: safeText(event.filename, 500),
      line: event.lineno || null,
      column: event.colno || null,
      stack: safeText(event.error),
    });
  }, true);

  window.addEventListener('unhandledrejection', (event) => {
    pushEvent('unhandled-rejection', {reason: safeText(event.reason)});
  }, true);

  for (const level of ['warn', 'error']) {
    const original = console[level];
    if (typeof original !== 'function') continue;
    console[level] = function(...args) {
      pushEvent(`console-${level}`, {message: safeText(args)});
      return original.apply(this, args);
    };
  }

  if (typeof window.fetch === 'function') {
    const originalFetch = window.fetch;
    window.fetch = function(input, init = {}) {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      const method = init.method || (input && input.method) || 'GET';
      pushEvent('fetch-call', {
        method: safeText(method, 20),
        url: safeText(url, 500),
        stack: safeText(new Error().stack, 700),
      });
      return originalFetch.apply(this, arguments).then((response) => {
        pushEvent('fetch-result', {
          method: safeText(method, 20),
          url: safeText(url, 500),
          status: response.status,
        });
        return response;
      }, (error) => {
        pushEvent('fetch-error', {
          method: safeText(method, 20),
          url: safeText(url, 500),
          error: safeText(error),
        });
        throw error;
      });
    };
  }

  if (typeof XMLHttpRequest !== 'undefined') {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {
      this.__reverseAnalysisMeta = {method: method || 'GET', url: String(url || '')};
      return originalOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function() {
      const meta = this.__reverseAnalysisMeta || {method: 'GET', url: ''};
      pushEvent('xhr-call', {
        method: safeText(meta.method, 20),
        url: safeText(meta.url, 500),
        stack: safeText(new Error().stack, 700),
      });
      this.addEventListener('loadend', () => {
        pushEvent('xhr-result', {
          method: safeText(meta.method, 20),
          url: safeText(meta.url, 500),
          status: this.status,
        });
      }, {once: true});
      return originalSend.apply(this, arguments);
    };
  }

  if (typeof WebSocket !== 'undefined' && WebSocket.prototype.send) {
    const originalWebSocketSend = WebSocket.prototype.send;
    WebSocket.prototype.send = function(data) {
      pushEvent('websocket-send', {
        url: safeText(this.url, 500),
        data_length: typeof data === 'string' ? data.length : (data && data.byteLength) || null,
        stack: safeText(new Error().stack, 700),
      });
      return originalWebSocketSend.apply(this, arguments);
    };
  }

  return true;
}
"""

FINGERPRINT_SCRIPT = r"""
() => {
  const result = {
    webdriver: navigator.webdriver === true,
    user_agent: navigator.userAgent || '',
    platform: navigator.platform || '',
    language: navigator.language || '',
    languages: Array.from(navigator.languages || []),
    locale: '',
    timezone: '',
    timezone_offset: new Date().getTimezoneOffset(),
    hardware_concurrency: navigator.hardwareConcurrency || null,
    device_memory: navigator.deviceMemory || null,
    plugins_count: navigator.plugins ? navigator.plugins.length : null,
    mime_types_count: navigator.mimeTypes ? navigator.mimeTypes.length : null,
    screen: {
      width: screen.width,
      height: screen.height,
      avail_width: screen.availWidth,
      avail_height: screen.availHeight,
      color_depth: screen.colorDepth,
      pixel_depth: screen.pixelDepth,
    },
    viewport: {
      inner_width: window.innerWidth,
      inner_height: window.innerHeight,
      outer_width: window.outerWidth,
      outer_height: window.outerHeight,
      device_pixel_ratio: window.devicePixelRatio,
    },
    ua_ch: null,
    webgl: {vendor: null, renderer: null},
    canvas_stable: null,
    notification_permission: typeof Notification === 'undefined' ? null : Notification.permission,
    api_presence: {
      fetch: typeof fetch === 'function',
      xhr: typeof XMLHttpRequest !== 'undefined',
      websocket: typeof WebSocket !== 'undefined',
      performance: typeof performance !== 'undefined',
      crypto_subtle: !!(window.crypto && window.crypto.subtle),
    },
  };

  try {
    const options = Intl.DateTimeFormat().resolvedOptions();
    result.locale = options.locale || '';
    result.timezone = options.timeZone || '';
  } catch (_) {}

  try {
    if (navigator.userAgentData) {
      result.ua_ch = {
        brands: Array.from(navigator.userAgentData.brands || []),
        mobile: navigator.userAgentData.mobile,
        platform: navigator.userAgentData.platform || '',
      };
    }
  } catch (_) {}

  try {
    const canvas = document.createElement('canvas');
    canvas.width = 220;
    canvas.height = 30;
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(4, 4, 80, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('reverse-analysis-fingerprint', 8, 7);
    const first = canvas.toDataURL();
    const second = canvas.toDataURL();
    result.canvas_stable = first === second;
  } catch (_) {}

  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      if (ext) {
        result.webgl.vendor = gl.getParameter(ext.UNMASKED_VENDOR_WEBGL);
        result.webgl.renderer = gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
      } else {
        result.webgl.vendor = gl.getParameter(gl.VENDOR);
        result.webgl.renderer = gl.getParameter(gl.RENDERER);
      }
    }
  } catch (_) {}

  return result;
}
"""


# ----------------------------------------------------------------------------
# 数据结构与通用辅助函数
# ----------------------------------------------------------------------------

@dataclass
class RuntimeMonitorHandle:
    """JS 运行时监控句柄。"""

    page: Any
    output_path: Path
    running: bool = True
    flush_thread: threading.Thread | None = None
    write_lock: threading.Lock = field(default_factory=threading.Lock)
    dropped_events: int = 0


class SessionError(RuntimeError):
    """逆向会话无法继续时抛出的统一异常。"""


class FingerprintBlockedError(SessionError):
    """浏览器指纹存在阻断项时抛出的异常。"""


def _now_iso() -> str:
    """返回带时区的当前时间。"""

    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def _session_id() -> str:
    """生成用于中文会话目录的本地时间编号。"""

    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def _atomic_write_json(path: Path, data: Any) -> None:
    """原子写入 JSON，避免状态文件只写到一半。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def _read_json(path: Path, default: Any = None) -> Any:
    """读取 JSON；文件不存在或损坏时返回默认值。"""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _redact_data(value: Any, key: str = "") -> Any:
    """递归脱敏字典、列表和文本中的敏感字段。"""

    if key and SENSITIVE_KEY_RE.search(key):
        return "***REDACTED***"
    if isinstance(value, dict):
        return {str(k): _redact_data(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_data(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_data(item) for item in value]
    if isinstance(value, str):
        text = value[:MAX_JS_EVENT_CHARS]
        return SENSITIVE_KEY_RE.sub("***", text)
    return value


def _load_tool_module(filename: str, module_name: str) -> ModuleType:
    """按文件路径加载同目录工具，兼容现有带连字符的脚本名。"""

    module_path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise SessionError(f"无法加载工具脚本：{module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def derive_slug(target: str, explicit_slug: str | None = None) -> str:
    """从 URL/标识推导稳定 slug，并阻断路径穿越。"""

    if explicit_slug:
        candidate = explicit_slug.strip().lower()
    else:
        parsed = urlparse(target if "://" in target else f"//{target}")
        hostname = (parsed.hostname or "").lower()
        if hostname:
            labels = [label for label in hostname.split(".") if label and label != "www"]
            candidate = labels[0] if labels else ""
        else:
            candidate = target.strip().lower()
            if any("一" <= char <= "鿿" for char in candidate):
                raise SessionError("中文目标名无法稳定转成 slug，请显式传入 --slug 英文别名")
            candidate = re.sub(r"[^a-z0-9_-]+", "-", candidate).strip("-_")

    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", candidate):
        raise SessionError(
            "slug 只允许 1-64 位小写字母、数字、连字符或下划线，且必须以字母或数字开头"
        )
    if candidate in {".", ".."} or ".." in candidate:
        raise SessionError("slug 不允许包含路径穿越片段")
    return candidate


def _state_path(workspace: Path) -> Path:
    """返回会话状态文件路径。"""

    return workspace / "会话状态.json"


def _write_state(
    workspace: Path,
    state: str,
    session_id: str | None,
    **extra: Any,
) -> dict[str, Any]:
    """写入状态并校验固定阶段顺序。"""

    if state not in (*STATE_ORDER, STATE_FAILED):
        raise SessionError(f"未知会话状态：{state}")

    current = _read_json(_state_path(workspace), {}) or {}
    current_state = current.get("state")
    current_session = current.get("session_id")

    if state in {STATE_FAILED, STATE_STOPPED}:
        if current_state not in STATE_ORDER or current_session != session_id:
            raise SessionError(
                f"无法进入 {state}：当前={current_state!r}，session_id={current_session!r}"
            )
    elif state == STATE_WORKSPACE_READY:
        if current_state == STATE_MONITORING and current_session != session_id:
            raise SessionError("已有 Web 会话正在监控，必须先执行 web-stop")
    else:
        # ENV_READY 之前的状态统一为 WORKSPACE_READY（首个非初始状态）。
        if state == STATE_ENV_READY:
            previous_state = STATE_WORKSPACE_READY
        else:
            expected_index = STATE_ORDER.index(state)
            previous_state = STATE_ORDER[expected_index - 1]
        if current_state != previous_state or current_session != session_id:
            raise SessionError(
                f"状态不可越级：当前={current_state!r}，进入 {state} 前必须为 {previous_state}"
            )

    document = {
        "state": state,
        "session_id": session_id,
        "updated_at": _now_iso(),
        **extra,
    }
    _atomic_write_json(_state_path(workspace), document)
    return document


def ensure_analysis_workspace(
    target: str,
    parent_dir: str | Path = ".",
    explicit_slug: str | None = None,
    target_type: str = "unknown",
    authorization: str = "待确认",
    deliverable: str = "待确认",
) -> Path:
    """第一动作创建标准分析工作区；已有资产只复用，不覆盖。"""

    slug = derive_slug(target, explicit_slug)
    parent = Path(parent_dir).expanduser().resolve()
    workspace = (parent / f"{slug}-crawler-reverse").resolve()
    if workspace.parent != parent:
        raise SessionError("工作区路径越过指定父目录")

    workspace.mkdir(parents=True, exist_ok=True)
    for relative_dir in WORKSPACE_DIRS:
        (workspace / relative_dir).mkdir(parents=True, exist_ok=True)

    plan_path = workspace / "分析计划.md"
    if not plan_path.exists():
        plan_path.write_text(
            "\n".join(
                [
                    "# 分析计划",
                    "",
                    "## 初始信息",
                    "",
                    f"- 目标：`{target}`",
                    f"- slug：`{slug}`",
                    f"- 授权边界：{authorization}",
                    f"- 目标类型：{target_type}",
                    "- 宿主 OS：`unknown`",
                    "- 目标运行时：`unknown`",
                    f"- 最终交付形态：{deliverable}",
                    f"- 创建时间：{_now_iso()}",
                    "- 当前阶段：工作区已创建，待环境识别",
                    "",
                    "## 待补证据",
                    "",
                    "- [ ] 宿主环境与浏览器资源清单",
                    "- [ ] 浏览器指纹一致性报告",
                    "- [ ] 用户操作、网络与 JS 运行时证据",
                    "- [ ] 接口清单与响应样本",
                    "- [ ] 交付形态与验收契约确认",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    if not _state_path(workspace).exists():
        # v2.20.0：init 阶段决定端口并写入《会话状态.json》
        # 让 web-start 不需要重新探测；多项目并行时各自工作区拥有独立端口。
        port = pick_free_port()
        _write_state(
            workspace,
            STATE_WORKSPACE_READY,
            None,
            target=target,
            slug=slug,
            chrome_port=port,
        )
    return workspace


def create_recording_session(workspace: Path) -> tuple[str, Path]:
    """创建不覆盖历史证据的中文录制会话目录。"""

    base_id = _session_id()
    session_id = base_id
    session_dir = workspace / "01-目标画像" / "录制" / f"会话-{session_id}"
    suffix = 1
    while session_dir.exists():
        session_id = f"{base_id}-{suffix:02d}"
        session_dir = workspace / "01-目标画像" / "录制" / f"会话-{session_id}"
        suffix += 1
    session_dir.mkdir(parents=True)
    return session_id, session_dir


# ----------------------------------------------------------------------------
# 宿主环境、浏览器和 CDP 探测
# ----------------------------------------------------------------------------

def browser_candidates(system_name: str, environment: dict[str, str] | None = None) -> list[str]:
    """按宿主 OS 返回 Chromium 系浏览器候选路径。

    不读环境变量：默认 Windows 安装路径硬编码 + pathlib.Path.home() 派生用户目录。
    `environment` 参数仅作为外部测试注入点，函数内部不读取 `os.environ`。
    """

    if system_name == "Windows":
        # Windows 默认安装位置（硬编码 + pathlib fallback，替代原先读 os.environ）
        env = environment or {}
        roots = [
            env.get("PROGRAMFILES", str(Path("C:/Program Files"))),
            env.get("PROGRAMFILES(X86)", str(Path("C:/Program Files (x86)"))),
            env.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")),
        ]
        relative_paths = [
            "Google/Chrome/Application/chrome.exe",
            "Chromium/Application/chrome.exe",
            "Microsoft/Edge/Application/msedge.exe",
        ]
        return [
            str(Path(root) / relative)
            for root in roots
            if root
            for relative in relative_paths
        ]
    if system_name == "Darwin":
        return [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    if system_name == "Linux":
        names = (
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "microsoft-edge",
        )
        return [path for name in names if (path := shutil.which(name))]
    return []


def _find_windows_browser_from_registry() -> str | None:
    """在 Windows 注册表中查找浏览器路径；其他系统直接返回 None。"""

    if platform.system() != "Windows":
        return None
    try:
        import winreg
    except ImportError:
        return None

    keys = (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
    )
    hives = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
    for hive in hives:
        for key_name in keys:
            try:
                with winreg.OpenKey(hive, key_name) as key:
                    value, _ = winreg.QueryValueEx(key, None)
                    if value and Path(value).is_file():
                        return str(Path(value))
            except OSError:
                continue
    return None


def _browser_version(browser_path: str | None) -> str | None:
    """读取浏览器版本，失败时返回 None。"""

    if not browser_path:
        return None
    try:
        completed = subprocess.run(
            [browser_path, "--version"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        text = (completed.stdout or completed.stderr or "").strip()
        return text or None
    except (OSError, subprocess.SubprocessError):
        return None


def _major_version(version_text: str | None) -> int | None:
    """从浏览器版本文本中提取主版本号。"""

    if not version_text:
        return None
    match = re.search(r"(?:Chrome|Chromium|Edge|Edg)/?\s*(\d+)|\b(\d+)\.", version_text)
    if not match:
        return None
    return int(match.group(1) or match.group(2))


# v2.20.0：端口独立分配算法
# 优先级：socket.bind 0（OS ephemeral）→ 端口池 fallback 9222..9300。
# 单函数可单测：详见 tests/reverse-analysis-session-verify.py 第 10 类断言。
PORT_POOL_START = 9222
PORT_POOL_END = 9300


def _try_bind(port: int) -> bool:
    """在 127.0.0.1:port 上尝试 bind；返回是否成功。Windows / macOS / Linux 共用。"""

    sock: socket.socket | None = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port))
        sock.listen(1)
        return True
    except OSError:
        return False
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass


def pick_free_port(preferred: int | None = None, max_attempts: int = 100) -> int:
    """探测一个空闲端口并返回。

    优先级：
      1. preferred 非空 → 直接尝试 1 次；
      2. socket.bind(('127.0.0.1', 0)) 让 OS 分配 ephemeral 端口 → 立即关闭由调用方抢占；
      3. 端口池 fallback PORT_POOL_START..PORT_POOL_END（9222..9300），每个 +1 探测；
      4. max_attempts 次仍未找到 → 抛 SessionError 让用户 --port。

    副作用：bind 0 后立即 close socket；调用方需注意 Chrome 抢占时可能遇到 ~1s
    TIME_WAIT（OS 释放 socket 后立刻 bind 同一端口的极小概率失败，留给 Chrome 启动
    阶段兜底；launch_debug_browser 的 15s 探测循环会自然消化）。
    """

    if preferred is not None:
        if _try_bind(preferred):
            return preferred
        raise SessionError(f"指定端口 {preferred} 已被占用")

    # 策略 1：bind 0（OS ephemeral）
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
    except OSError:
        # 某些受限环境不允许 bind 0 → 走端口池 fallback
        pass

    # 策略 2：端口池 fallback
    pool = list(range(PORT_POOL_START, PORT_POOL_END + 1))
    attempts = 0
    for port in pool:
        if attempts >= max_attempts:
            break
        attempts += 1
        if _try_bind(port):
            return port

    raise SessionError(
        f"端口冲突：{PORT_POOL_START}..{PORT_POOL_END} 共 {len(pool)} 个端口全部占用，"
        f"且 OS ephemeral 端口分配失败。请显式 --port 指定空闲端口后重试"
    )


def resolve_port(
    workspace: Path,
    explicit_port: int | None = None,
) -> int:
    """解析 CDP 端口：explicit_port 优先；否则从《会话状态.json》读 chrome_port；缺失则分配新端口并回写。

    三级优先级：
      1. explicit_port 非 None → 直接返回；
      2. JSON 中 chrome_port 存在且 1..65535 → 返回；
      3. 缺失 → 调 pick_free_port() 分配新端口 + _write_state 回写（保持 init / web-start 幂等）。
    """

    if explicit_port is not None:
        return explicit_port
    state = _read_json(_state_path(workspace), {}) or {}
    stored = state.get("chrome_port")
    if isinstance(stored, int) and 1 <= stored <= 65535:
        return stored
    # 未分配：当场分配 + 回写（保持 init / web-start 之间幂等）
    port = pick_free_port()
    current_state = state.get("state") or STATE_WORKSPACE_READY
    current_session = state.get("session_id")
    _write_state(
        workspace,
        current_state,
        current_session,
        chrome_port=port,
    )
    return port


def probe_cdp(port: int | None = None, timeout: float = 2.0) -> dict[str, Any]:
    """探测 Chrome CDP 版本和所有 target。port=None 时调用方必须后续传入显式端口。"""

    if port is None:
        raise SessionError("未找到端口配置，请先 init（reverse-analysis-session.py init）")
    result: dict[str, Any] = {
        "available": False,
        "port": port,
        "version": None,
        "browser_major": None,
        "websocket_debugger_url": None,
        "tabs": [],
        "error": None,
    }
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/json/version",
            timeout=timeout,
        ) as response:
            version_doc = json.loads(response.read())
        result["available"] = True
        result["version"] = version_doc.get("Browser")
        result["browser_major"] = _major_version(result["version"])
        result["websocket_debugger_url"] = version_doc.get("webSocketDebuggerUrl")
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        result["error"] = str(exc)
        return result

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/json",
            timeout=timeout,
        ) as response:
            tabs = json.loads(response.read())
        if isinstance(tabs, list):
            result["tabs"] = tabs
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        result["error"] = f"版本端点可用，但 target 列表读取失败：{exc}"
    return result


def detect_host_environment(port: int | None = None) -> dict[str, Any]:
    """识别宿主 OS、浏览器实现和 CDP 能力。port=None 时调用方必须传入 init 阶段已分配的端口。"""

    system_name = platform.system()
    candidates = browser_candidates(system_name)
    registry_browser = _find_windows_browser_from_registry()
    if registry_browser:
        candidates.insert(0, registry_browser)

    existing_candidates = [path for path in dict.fromkeys(candidates) if Path(path).is_file()]
    browser_path = existing_candidates[0] if existing_candidates else None
    cdp = probe_cdp(port)
    version_text = cdp.get("version") or _browser_version(browser_path)
    browser_major = cdp.get("browser_major") or _major_version(version_text)

    return {
        "detected_at": _now_iso(),
        "host_os": system_name or "unknown",
        "host_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "browser_candidates": existing_candidates,
        "browser_path": browser_path,
        "browser_version": version_text,
        "browser_major": browser_major,
        "chrome_136_profile_requirement": "required" if (browser_major or 0) >= 136 else "not_applicable",
        "chrome_150_origin_requirement": "required" if (browser_major or 0) >= 150 else "not_applicable",
        "cdp": cdp,
    }


def launch_debug_browser(
    browser_path: str,
    workspace: Path,
    port: int,
) -> dict[str, Any]:
    """按固定参数启动 task-owned 调试浏览器；浏览器默认保留。"""

    profile_dir = workspace / "01-目标画像" / "浏览器配置"
    profile_dir.mkdir(parents=True, exist_ok=True)
    command = [
        browser_path,
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile_dir}",
        "about:blank",
    ]

    creation_flags = 0
    if platform.system() == "Windows":
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
    )

    deadline = time.monotonic() + 15
    cdp = probe_cdp(port)
    while not cdp["available"] and time.monotonic() < deadline:
        time.sleep(0.5)
        cdp = probe_cdp(port)
    if not cdp["available"]:
        raise SessionError("浏览器已启动但 15 秒内未检测到 CDP，请检查安全软件和启动参数")

    return {
        "pid": process.pid,
        "command": command,
        "profile_dir": str(profile_dir),
        "cdp": cdp,
    }


def _target_domain(target_url: str) -> str:
    """从目标 URL 提取域名。"""

    parsed = urlparse(target_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SessionError("Web 目标必须是完整 http:// 或 https:// URL")
    return parsed.hostname.lower()


def connect_target_tab(
    target_url: str,
    port: int,
    profile_dir: str | None,
    browser_owner: str,
) -> tuple[Any, Any, str, bool]:
    """接管真实目标 tab；不存在时只创建带明确 URL 的 about:blank 任务 tab。"""

    try:
        from DrissionPage import ChromiumOptions, ChromiumPage
    except ImportError as exc:
        raise SessionError("未安装 DrissionPage，无法执行 Web 默认接管链路") from exc

    options = ChromiumOptions().set_local_port(port)
    if profile_dir:
        options.set_user_data_path(profile_dir)
    browser = ChromiumPage(addr_or_opts=options)
    domain = _target_domain(target_url)

    for tab_id in browser.tab_ids:
        try:
            tab = browser.get_tab(tab_id)
            if getattr(tab, "tab_type", "page") == "page" and domain in (tab.url or "").lower():
                return browser, tab, "external/user" if browser_owner == "external/user" else "task", True
        except Exception:
            continue

    if browser_owner == "task":
        for tab_id in browser.tab_ids:
            try:
                tab = browser.get_tab(tab_id)
                if getattr(tab, "tab_type", "page") == "page" and (tab.url or "") in {"", "about:blank"}:
                    return browser, tab, "task", False
            except Exception:
                continue

    tab = browser.new_tab("about:blank")
    return browser, tab, "task-in-user-context", False


# ----------------------------------------------------------------------------
# 浏览器指纹一致性审计
# ----------------------------------------------------------------------------

def _ua_major(user_agent: str) -> int | None:
    """从 UA 中读取 Chrome/Edge 主版本。"""

    match = re.search(r"(?:Chrome|Edg)/(\d+)", user_agent or "")
    return int(match.group(1)) if match else None


def evaluate_fingerprint(
    raw: dict[str, Any],
    host_os: str,
    browser_major: int | None,
) -> dict[str, Any]:
    """把原始浏览器字段判定为阻断项、警告项和 unknown 项。"""

    blocking: list[str] = []
    warnings: list[str] = []
    unknown: list[str] = [
        "公网 IP/代理出口与地理位置一致性未使用外部服务验证",
        "TLS/JA3/JA4 无法由页面 JavaScript 或普通 CDP 本地证明",
        "服务端行为画像与账号信誉只能在目标业务响应中继续观察",
    ]

    user_agent = str(raw.get("user_agent") or "")
    browser_platform = str(raw.get("platform") or "")
    if raw.get("webdriver") is True:
        blocking.append("navigator.webdriver=true，自动化控制特征已暴露")
    if "HeadlessChrome" in user_agent:
        blocking.append("User-Agent 包含 HeadlessChrome")

    ua_major = _ua_major(user_agent)
    if browser_major and ua_major and browser_major != ua_major:
        blocking.append(f"UA 主版本 {ua_major} 与 CDP 浏览器主版本 {browser_major} 不一致")

    os_checks = {
        "Windows": ("win",),
        "Darwin": ("mac",),
        "Linux": ("linux", "x11"),
    }
    expected_platforms = os_checks.get(host_os)
    if expected_platforms and not any(item in browser_platform.lower() for item in expected_platforms):
        blocking.append(f"宿主 OS={host_os} 与 navigator.platform={browser_platform!r} 明显不一致")

    api_presence = raw.get("api_presence") or {}
    missing_apis = [name for name, present in api_presence.items() if not present]
    if missing_apis:
        blocking.append(f"关键浏览器 API 缺失：{', '.join(missing_apis)}")

    language = str(raw.get("language") or "").lower()
    locale = str(raw.get("locale") or "").lower()
    if language and locale and language.split("-")[0] != locale.split("-")[0]:
        warnings.append(f"navigator.language={language} 与 Intl locale={locale} 不一致")

    if raw.get("plugins_count") == 0:
        warnings.append("navigator.plugins 数量为 0，需结合浏览器版本确认")
    if raw.get("mime_types_count") == 0:
        warnings.append("navigator.mimeTypes 数量为 0，需结合浏览器版本确认")
    if raw.get("canvas_stable") is False:
        warnings.append("同一会话两次 Canvas 结果不一致，可能存在随机扰动")

    renderer = str((raw.get("webgl") or {}).get("renderer") or "")
    if re.search(r"swiftshader|llvmpipe|software", renderer, re.IGNORECASE):
        warnings.append(f"WebGL 使用软件渲染器：{renderer}")

    screen = raw.get("screen") or {}
    viewport = raw.get("viewport") or {}
    if not screen.get("width") or not screen.get("height"):
        warnings.append("屏幕宽高缺失或为 0")
    if not viewport.get("inner_width") or not viewport.get("inner_height"):
        warnings.append("页面 viewport 宽高缺失或为 0")
    if (viewport.get("device_pixel_ratio") or 0) <= 0:
        warnings.append("devicePixelRatio 缺失或不合理")
    if (raw.get("hardware_concurrency") or 0) <= 0:
        warnings.append("hardwareConcurrency 缺失或不合理")

    status = "BLOCKED" if blocking else ("WARN" if warnings else "PASS_WITH_UNKNOWNS")
    return {
        "checked_at": _now_iso(),
        "status": status,
        "blocking": blocking,
        "warnings": warnings,
        "unknown": unknown,
        "raw": _redact_data(raw),
        "statement": "本报告只验证字段一致性，不证明浏览器指纹绝对真实。",
    }


def audit_browser_fingerprint(
    page: Any,
    host_environment: dict[str, Any],
) -> dict[str, Any]:
    """采集并评估当前浏览器环境与指纹。"""

    try:
        raw = page.run_js(FINGERPRINT_SCRIPT) or {}
    except Exception as exc:
        raise SessionError(f"浏览器指纹采集失败：{exc}") from exc
    if not isinstance(raw, dict):
        raise SessionError("浏览器指纹脚本未返回字典")
    return evaluate_fingerprint(
        raw,
        str(host_environment.get("host_os") or "unknown"),
        host_environment.get("browser_major"),
    )


# ----------------------------------------------------------------------------
# JS 运行时持续监控
# ----------------------------------------------------------------------------

def _normalize_js_event(event: dict[str, Any]) -> dict[str, Any]:
    """规范化、截断并脱敏单条 JS 运行时事件。"""

    ts_ms = int(event.get("ts_ms") or 0)
    timestamp = (
        datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        .astimezone()
        .isoformat(timespec="milliseconds")
        if ts_ms > 0
        else _now_iso()
    )
    normalized = {
        "timestamp": timestamp,
        "ts_ms": ts_ms,
        "type": str(event.get("type") or "unknown")[:80],
    }
    for key, value in event.items():
        if key in {"timestamp", "ts_ms", "type"}:
            continue
        normalized[str(key)] = _redact_data(value, str(key))
    return normalized


def _pull_js_events(page: Any) -> list[dict[str, Any]]:
    """从页面缓冲区拉取一批 JS 运行时事件。"""

    try:
        events = page.run_js(
            "() => { const buffer = window.__reverseAnalysisBuffer || []; "
            "window.__reverseAnalysisBuffer = []; return buffer; }"
        ) or []
    except Exception:
        return []
    if not isinstance(events, list):
        return []
    return [event for event in events[:MAX_JS_EVENTS_PER_FLUSH] if isinstance(event, dict)]


def _append_js_events(handle: RuntimeMonitorHandle, events: list[dict[str, Any]]) -> None:
    """在大小上限内把 JS 事件追加到 JSONL。"""

    if not events:
        return
    with handle.write_lock:
        current_size = handle.output_path.stat().st_size if handle.output_path.exists() else 0
        if current_size >= MAX_JS_LOG_BYTES:
            handle.dropped_events += len(events)
            return
        lines = [json.dumps(_normalize_js_event(event), ensure_ascii=False) for event in events]
        encoded = ("\n".join(lines) + "\n").encode("utf-8")
        remaining = MAX_JS_LOG_BYTES - current_size
        if len(encoded) > remaining:
            handle.dropped_events += len(events)
            return
        with handle.output_path.open("ab") as file:
            file.write(encoded)


def _js_flush_loop(handle: RuntimeMonitorHandle) -> None:
    """每秒拉取并落盘 JS 事件，直到会话停止。"""

    while handle.running:
        _append_js_events(handle, _pull_js_events(handle.page))
        time.sleep(1)
    _append_js_events(handle, _pull_js_events(handle.page))


def start_js_monitor(page: Any, output_dir: Path) -> RuntimeMonitorHandle:
    """注入最小 JS 监控器并启动后台 flush。"""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "js-runtime.jsonl"
    if output_path.exists():
        output_path.unlink()
    try:
        page.run_js(JS_MONITOR_SCRIPT)
    except Exception as exc:
        raise SessionError(f"JS 运行时监控注入失败：{exc}") from exc

    handle = RuntimeMonitorHandle(page=page, output_path=output_path)
    handle.flush_thread = threading.Thread(
        target=_js_flush_loop,
        args=(handle,),
        daemon=True,
        name="reverse-analysis-js-monitor",
    )
    handle.flush_thread.start()
    return handle


def stop_js_monitor(handle: RuntimeMonitorHandle) -> str:
    """停止 JS 监控、flush 剩余事件并返回产物路径。"""

    handle.running = False
    if handle.flush_thread is not None:
        handle.flush_thread.join(timeout=3)
        handle.flush_thread = None
    _append_js_events(handle, _pull_js_events(handle.page))
    return str(handle.output_path.resolve())


# ----------------------------------------------------------------------------
# 操作、网络和 JS 证据关联
# ----------------------------------------------------------------------------

def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """读取 JSONL，忽略空行和损坏行。"""

    entries: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    entries.append(value)
    except OSError:
        pass
    return entries


def _timestamp_ms(value: Any) -> int | None:
    """把 ISO 时间或数字时间转换为毫秒。"""

    if isinstance(value, (int, float)):
        return int(value)
    if not value:
        return None
    try:
        return int(datetime.fromisoformat(str(value)).timestamp() * 1000)
    except (ValueError, TypeError):
        return None


def build_step_evidence_index(session_dir: Path) -> Path:
    """按时间窗关联操作、网络和 JS 证据。"""

    actions_path = session_dir / "user-actions.json"
    har_path = session_dir / "user-session.har.jsonl"
    js_path = session_dir / "js-runtime.jsonl"
    actions_doc = _read_json(actions_path, {}) or {}
    actions = actions_doc.get("actions", []) if isinstance(actions_doc, dict) else []
    har_entries = _read_jsonl(har_path)
    js_entries = _read_jsonl(js_path)

    steps: list[dict[str, Any]] = []
    for action in actions if isinstance(actions, list) else []:
        if not isinstance(action, dict):
            continue
        action_ts = _timestamp_ms(action.get("timestamp"))
        if action_ts is None:
            continue
        network_matches: list[dict[str, Any]] = []
        for index, entry in enumerate(har_entries):
            entry_ts = _timestamp_ms(entry.get("ts"))
            if entry_ts is not None and abs(entry_ts - action_ts) <= EVIDENCE_WINDOW_MS:
                network_matches.append(
                    {
                        "index": index,
                        "kind": entry.get("kind"),
                        "method": entry.get("method"),
                        "url": entry.get("url"),
                        "status": entry.get("status"),
                    }
                )
                if len(network_matches) >= 50:
                    break

        js_matches: list[dict[str, Any]] = []
        for index, entry in enumerate(js_entries):
            entry_ts = _timestamp_ms(entry.get("ts_ms") or entry.get("timestamp"))
            if entry_ts is not None and abs(entry_ts - action_ts) <= EVIDENCE_WINDOW_MS:
                js_matches.append(
                    {
                        "index": index,
                        "type": entry.get("type"),
                        "url": entry.get("url"),
                        "message": entry.get("message"),
                    }
                )
                if len(js_matches) >= 50:
                    break

        steps.append(
            {
                "step": action.get("step"),
                "timestamp": action.get("timestamp"),
                "action": {
                    "type": action.get("type"),
                    "selectors": action.get("selectors", []),
                    "key": action.get("key"),
                },
                "network": network_matches,
                "js_runtime": js_matches,
            }
        )

    index_path = session_dir / "步骤证据索引.json"
    _atomic_write_json(
        index_path,
        {
            "generated_at": _now_iso(),
            "window_ms": EVIDENCE_WINDOW_MS,
            "artifacts": {
                "actions": str(actions_path),
                "network": str(har_path),
                "js_runtime": str(js_path),
            },
            "steps": steps,
            "note": "只做时间窗关联；接口语义和关键函数结论仍需实测。",
        },
    )
    return index_path


# ----------------------------------------------------------------------------
# Web 会话编排
# ----------------------------------------------------------------------------

def _resource_document(
    browser_owner: str,
    tab_owner: str,
    port: int,
    launch_info: dict[str, Any] | None,
) -> dict[str, Any]:
    """生成外部资源所有权清单。"""

    resources = [
        {
            "resource": f"Chrome CDP :{port}",
            "origin_owner": browser_owner,
            "allowed": ["attach", "读取 tabs", "经确认操作页面"],
            "cleanup": "停止使用；禁止关闭/kill 浏览器",
        },
        {
            "resource": "目标 page/tab",
            "origin_owner": tab_owner,
            "allowed": ["读取", "用户操作期间监控"],
            "cleanup": "默认保留；禁止 page.close()",
        },
    ]
    if launch_info:
        resources.append(
            {
                "resource": "独立 user-data-dir",
                "origin_owner": "task",
                "path": launch_info.get("profile_dir"),
                "cleanup": "默认保留供复盘，不自动删除",
            }
        )
    return {"recorded_at": _now_iso(), "resources": resources}


def _wait_for_stop(stop_path: Path, requested: threading.Event) -> None:
    """等待 web-stop 或进程信号，期间不驱动用户页面。"""

    while not stop_path.exists() and not requested.is_set():
        time.sleep(0.5)


def run_web_session(args: argparse.Namespace) -> Path:
    """执行固定 Web 起手状态机并持续监控到停止。"""

    # 第一动作必须落工作区，禁止在此之前探测浏览器或访问目标站。
    workspace = ensure_analysis_workspace(
        target=args.url,
        parent_dir=args.parent,
        explicit_slug=args.slug,
        target_type="web",
        authorization=args.authorization,
        deliverable=args.deliverable,
    )
    session_id, session_dir = create_recording_session(workspace)
    _write_state(
        workspace,
        STATE_WORKSPACE_READY,
        session_id,
        target=args.url,
        workspace=str(workspace),
        session_dir=str(session_dir),
    )

    recorder_handle: Any = None
    js_handle: RuntimeMonitorHandle | None = None
    monitoring_started = False
    requested = threading.Event()
    stop_path = session_dir / ".停止监控"
    browser_owner = "external/user"
    launch_info: dict[str, Any] | None = None

    def request_stop(_signum: int, _frame: Any) -> None:
        """收到终止信号时请求正常 flush，不直接结束进程。"""

        requested.set()

    previous_sigint = signal.signal(signal.SIGINT, request_stop)
    previous_sigterm = signal.signal(signal.SIGTERM, request_stop)

    try:
        # v2.20.0：三级优先级解析端口（CLI explicit > JSON chrome_port > 重新分配并回写）
        port = resolve_port(workspace, args.port)
        host_environment = detect_host_environment(port)
        _atomic_write_json(workspace / "01-目标画像" / "宿主环境报告.json", host_environment)
        _write_state(
            workspace,
            STATE_ENV_READY,
            session_id,
            session_dir=str(session_dir),
            chrome_port=port,
            environment_report="01-目标画像/宿主环境报告.json",
        )

        if not host_environment["cdp"]["available"]:
            browser_path = host_environment.get("browser_path")
            if not browser_path:
                raise SessionError("未检测到可用 Chromium 系浏览器，无法自动打开目标站")
            launch_info = launch_debug_browser(browser_path, workspace, port)
            browser_owner = "task"
            host_environment["cdp"] = launch_info["cdp"]
            host_environment["browser_version"] = launch_info["cdp"].get("version")
            host_environment["browser_major"] = launch_info["cdp"].get("browser_major")
            host_environment["selected_method"] = "按宿主 OS 启动 task-owned 独立浏览器"
            host_environment["launch_command"] = launch_info["command"]
            _atomic_write_json(workspace / "01-目标画像" / "宿主环境报告.json", host_environment)
        else:
            host_environment["selected_method"] = "接管现有用户 Chrome CDP"
            _atomic_write_json(workspace / "01-目标画像" / "宿主环境报告.json", host_environment)

        browser, page, tab_owner, target_already_open = connect_target_tab(
            target_url=args.url,
            port=port,
            profile_dir=launch_info.get("profile_dir") if launch_info else None,
            browser_owner=browser_owner,
        )
        _atomic_write_json(
            workspace / "01-目标画像" / "资源清单.json",
            _resource_document(browser_owner, tab_owner, port, launch_info),
        )
        _write_state(
            workspace,
            STATE_BROWSER_READY,
            session_id,
            session_dir=str(session_dir),
            chrome_port=port,
            browser_owner=browser_owner,
            tab_owner=tab_owner,
            target_already_open=target_already_open,
        )

        fingerprint_report = audit_browser_fingerprint(page, host_environment)
        _atomic_write_json(
            workspace / "01-目标画像" / "浏览器指纹报告.json",
            fingerprint_report,
        )
        _write_state(
            workspace,
            STATE_FINGERPRINT_READY,
            session_id,
            session_dir=str(session_dir),
            fingerprint_status=fingerprint_report["status"],
        )
        if fingerprint_report["blocking"]:
            raise FingerprintBlockedError(
                "浏览器指纹存在阻断项，已停止目标业务操作："
                + "；".join(fingerprint_report["blocking"])
            )

        if not target_already_open:
            page.get(args.url)

        popup_handler = _load_tool_module("popup-handler.py", "mcpowers_popup_handler")
        popup_handler.cleanup_all(
            page,
            screenshot_dir=str(workspace / "01-目标画像" / "弹窗截图"),
        )

        recorder = _load_tool_module("user-action-recorder.py", "mcpowers_user_action_recorder")
        recorder_handle = recorder.start_recording(page, output_dir=str(session_dir))
        js_handle = start_js_monitor(page, session_dir)
        monitoring_started = True
        _write_state(
            workspace,
            STATE_MONITORING,
            session_id,
            session_dir=str(session_dir),
            ready_at=_now_iso(),
            message="监控已就绪：请由用户在浏览器中完成目标操作，AI 只持续采集证据。",
        )
        print(f"[逆向会话] 工作区：{workspace}")
        print(f"[逆向会话] 会话目录：{session_dir}")
        print("[逆向会话] 监控已就绪，请在浏览器中完成目标操作。")
        print(f"[逆向会话] 完成后执行：python \"{Path(__file__).resolve()}\" web-stop --workspace \"{workspace}\"")
        sys.stdout.flush()

        _wait_for_stop(stop_path, requested)

        js_path = stop_js_monitor(js_handle)
        js_handle = None
        actions_path = recorder.stop_recording(recorder_handle)
        recorder_handle = None
        index_path = build_step_evidence_index(session_dir)

        # v2.21.0：派生产物生成（必须在 build_step_evidence_index 之后、STOPPED 写入之前）
        # 失败隔离：捕获所有异常，不破坏 STOPPED 与浏览器存活（v2.19.0 铁律 #6）。
        artifacts_status: dict[str, Any] = {"status": "skipped", "error": "未运行"}
        artifacts_generator: Any = None
        try:
            artifacts_generator = _load_tool_module(
                "session-artifacts-generator.py",
                "mcpowers_session_artifacts_generator",
            )
        except Exception as load_exc:  # noqa: BLE001
            print(f"[逆向会话] 派生产物生成器加载失败：{type(load_exc).__name__}: {load_exc}")
        if artifacts_generator is not None:
            try:
                artifacts_result = artifacts_generator.run_artifacts_generation(workspace, session_dir)
                artifacts_status = {
                    "status": artifacts_result.get("status", "unknown"),
                    "module_name": artifacts_result.get("module_name"),
                    "client_path": artifacts_result.get("client_path"),
                    "quick_test_path": artifacts_result.get("quick_test_path"),
                    "candidate_report_path": artifacts_result.get("candidate_report_path"),
                    "response_sample_paths": artifacts_result.get("response_sample_paths", []),
                    "created_paths": artifacts_result.get("created_paths", []),
                    "preserved_paths": artifacts_result.get("preserved_paths", []),
                    "warnings": artifacts_result.get("warnings", []),
                }
                print(f"[逆向会话] 派生产物生成：{artifacts_status['status']}")
                if artifacts_status.get("warnings"):
                    for warning in artifacts_status["warnings"]:
                        print(f"[逆向会话] 派生产物警告：{warning}")
            except Exception as gen_exc:  # noqa: BLE001
                artifacts_status = {
                    "status": "failed",
                    "error_type": type(gen_exc).__name__,
                    "error": str(gen_exc),
                }
                print(f"[逆向会话] 派生产物生成失败：{type(gen_exc).__name__}: {gen_exc}")

        _write_state(
            workspace,
            STATE_STOPPED,
            session_id,
            session_dir=str(session_dir),
            stopped_at=_now_iso(),
            actions_path=actions_path,
            har_path=str((session_dir / "user-session.har.jsonl").resolve()),
            js_runtime_path=js_path,
            evidence_index_path=str(index_path.resolve()),
            artifacts_generation=artifacts_status,
            browser_still_running=True,
        )
        return workspace
    except Exception as exc:
        if js_handle is not None:
            try:
                stop_js_monitor(js_handle)
            except Exception:
                pass
        if recorder_handle is not None:
            try:
                recorder = _load_tool_module(
                    "user-action-recorder.py",
                    "mcpowers_user_action_recorder_cleanup",
                )
                recorder.stop_recording(recorder_handle)
            except Exception:
                pass
        if monitoring_started:
            try:
                build_step_evidence_index(session_dir)
            except Exception:
                pass
        _write_state(
            workspace,
            STATE_FAILED,
            session_id,
            session_dir=str(session_dir),
            failed_at=_now_iso(),
            error_type=type(exc).__name__,
            error=str(exc),
            browser_still_running=True,
        )
        raise
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
        signal.signal(signal.SIGTERM, previous_sigterm)


def request_web_stop(workspace: str | Path) -> Path:
    """向当前 MONITORING 会话写入正常停止信号。"""

    workspace_path = Path(workspace).expanduser().resolve()
    state = _read_json(_state_path(workspace_path), {}) or {}
    if state.get("state") != STATE_MONITORING:
        raise SessionError(f"当前状态不是 MONITORING：{state.get('state')!r}")
    session_dir = Path(str(state.get("session_dir") or "")).resolve()
    expected_parent = (workspace_path / "01-目标画像" / "录制").resolve()
    if expected_parent not in session_dir.parents:
        raise SessionError("会话目录不属于当前工作区")
    stop_path = session_dir / ".停止监控"
    _atomic_write_json(
        stop_path,
        {
            "requested_at": _now_iso(),
            "reason": "用户操作完成，请正常停止并落盘",
        },
    )
    return stop_path


def print_status(workspace: str | Path) -> dict[str, Any]:
    """读取并打印当前会话状态。"""

    workspace_path = Path(workspace).expanduser().resolve()
    state = _read_json(_state_path(workspace_path), None)
    if not isinstance(state, dict):
        raise SessionError("未找到有效的《会话状态.json》")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return state


# ----------------------------------------------------------------------------
# 命令行入口
# ----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""

    parser = argparse.ArgumentParser(description="逆向分析工作区与 Web 协作会话编排工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="第一时间创建标准分析工作区")
    init_parser.add_argument("--target", required=True, help="URL、包名、AppID 或稳定目标名")
    init_parser.add_argument("--parent", default=".", help="工作区父目录")
    init_parser.add_argument("--slug", help="稳定英文 slug；中文目标必须显式提供")
    init_parser.add_argument("--target-type", default="unknown", help="web/app/android/ios 等")
    init_parser.add_argument("--authorization", default="待确认", help="授权边界摘要")
    init_parser.add_argument("--deliverable", default="待确认", help="纯协议/半自动化/纯自动化")

    start_parser = subparsers.add_parser("web-start", help="启动用户操作 + AI 持续监控会话")
    start_parser.add_argument("--url", required=True, help="完整目标 URL")
    start_parser.add_argument("--parent", default=".", help="工作区父目录")
    start_parser.add_argument("--slug", help="稳定英文 slug")
    start_parser.add_argument("--port", type=int, default=None, help="Chrome CDP 端口；缺省从《会话状态.json》读 chrome_port（v2.20.0 init 阶段自动分配）")
    start_parser.add_argument("--authorization", default="待确认", help="授权边界摘要")
    start_parser.add_argument("--deliverable", default="待确认", help="最终交付形态")

    stop_parser = subparsers.add_parser("web-stop", help="正常停止当前 Web 监控会话")
    stop_parser.add_argument("--workspace", required=True, help="分析工作区路径")

    status_parser = subparsers.add_parser("status", help="查看当前会话状态")
    status_parser.add_argument("--workspace", required=True, help="分析工作区路径")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 主入口。"""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            workspace = ensure_analysis_workspace(
                target=args.target,
                parent_dir=args.parent,
                explicit_slug=args.slug,
                target_type=args.target_type,
                authorization=args.authorization,
                deliverable=args.deliverable,
            )
            print(f"[逆向会话] 工作区已创建：{workspace}")
        elif args.command == "web-start":
            workspace = run_web_session(args)
            print(f"[逆向会话] 会话已正常停止：{workspace}")
        elif args.command == "web-stop":
            stop_path = request_web_stop(args.workspace)
            print(f"[逆向会话] 已请求正常停止：{stop_path}")
        elif args.command == "status":
            print_status(args.workspace)
        return 0
    except SessionError as exc:
        print(f"[逆向会话] 失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
