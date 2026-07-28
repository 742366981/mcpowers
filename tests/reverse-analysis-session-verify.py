"""
reverse-analysis-session-verify.py — 逆向会话编排工具与录制器脱敏的最小验证

执行方式：
    python tests/reverse-analysis-session-verify.py

设计原则：
- 纯函数断言，不启动真实 Chrome / DrissionPage；
- 覆盖 slug 校验、工作区幂等、状态机越级拒绝、浏览器候选矩阵、指纹判定
  分级、步骤证据关联、敏感字段脱敏与中文注释 9 类断言；
- 任一断言失败抛出 AssertionError，CI 以非零退出码识别。
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_DIR = Path(__file__).resolve().parents[1]
SESSION_SCRIPT = REPO_DIR / "skills" / "mcpowers-crawler-reverse" / "scripts" / "reverse-analysis-session.py"
RECORDER_SCRIPT = REPO_DIR / "skills" / "mcpowers-crawler-reverse" / "scripts" / "user-action-recorder.py"

assert SESSION_SCRIPT.is_file(), f"缺少脚本：{SESSION_SCRIPT}"
assert RECORDER_SCRIPT.is_file(), f"缺少脚本：{RECORDER_SCRIPT}"


def load_module(script_path: Path, module_name: str) -> ModuleType:
    """按文件路径加载脚本为模块。"""

    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"无法加载模块：{script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


session = load_module(SESSION_SCRIPT, "mcpowers_reverse_session_test")
recorder = load_module(RECORDER_SCRIPT, "mcpowers_user_action_recorder_test")


def assert_eq(label: str, actual: Any, expected: Any) -> None:
    """断言相等并打印。"""

    if actual != expected:
        raise AssertionError(f"{label}：实际={actual!r}，期望={expected!r}")
    print(f"  ✓ {label}")


def assert_true(label: str, condition: bool, hint: str = "") -> None:
    """断言为真。"""

    if not condition:
        raise AssertionError(f"{label}（{hint}）")
    print(f"  ✓ {label}")


def assert_raises(label: str, exc_type: type[BaseException], fn: Any, *args: Any, **kwargs: Any) -> None:
    """断言抛出指定异常。"""

    try:
        fn(*args, **kwargs)
    except exc_type:
        print(f"  ✓ {label}")
        return
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"{label}：抛出非预期异常 {type(exc).__name__}: {exc}") from exc
    raise AssertionError(f"{label}：未抛出任何异常")


# ----------------------------------------------------------------------------
# 1. slug 与工作区幂等
# ----------------------------------------------------------------------------

print("[1/9] slug 与工作区幂等")
slug = session.derive_slug("https://example.com/path?x=1")
assert_eq("URL 推导 slug", slug, "example")
assert_raises("路径穿越 slug 拒绝", session.SessionError, session.derive_slug, "https://x.com", explicit_slug="../etc")
assert_raises("非法 slug 字符拒绝", session.SessionError, session.derive_slug, "https://x.com", explicit_slug="A B")

with tempfile.TemporaryDirectory() as tmp:
    workspace = session.ensure_analysis_workspace(
        target="https://example.com/",
        parent_dir=tmp,
        authorization="自测授权",
    )
    assert_true("工作区已创建", workspace.is_dir(), str(workspace))
    assert_true("《分析计划.md》已存在", (workspace / "分析计划.md").is_file())
    assert_true("中文子目录已创建", (workspace / "01-目标画像" / "弹窗截图").is_dir())
    assert_true("中文录制子目录已创建", (workspace / "01-目标画像" / "录制").is_dir())
    assert_true("《05-案例沉淀.md》必须未生成（阶段 5.5 前不得出现）", not (workspace / "05-案例沉淀.md").exists())

    state_doc = json.loads((workspace / "会话状态.json").read_text(encoding="utf-8"))
    assert_eq("初次进入 WORKSPACE_READY", state_doc["state"], session.STATE_WORKSPACE_READY)
    assert_true("slug 已落状态", state_doc.get("slug") == "example", state_doc.get("slug"))

    workspace_second = session.ensure_analysis_workspace(
        target="https://example.com/other",
        parent_dir=tmp,
        authorization="自测授权",
    )
    assert_eq("同一 slug 复用工作区", workspace_second.resolve(), workspace.resolve())


# ----------------------------------------------------------------------------
# 2. 状态机越级拒绝
# ----------------------------------------------------------------------------

print("[2/9] 状态机越级拒绝")
with tempfile.TemporaryDirectory() as tmp:
    workspace = session.ensure_analysis_workspace(target="https://demo.com/", parent_dir=tmp)

    assert_raises(
        "越级进入 BROWSER_READY 失败",
        session.SessionError,
        session._write_state,
        workspace,
        session.STATE_BROWSER_READY,
        "sess-1",
    )

    # 写一个与会话一致的 WORKSPACE_READY，再推进到 ENV_READY。
    session._write_state(workspace, session.STATE_WORKSPACE_READY, "sess-1")
    session._write_state(workspace, session.STATE_ENV_READY, "sess-1")
    assert_raises(
        "用不同 session_id 进入 FINGERPRINT_READY 失败",
        session.SessionError,
        session._write_state,
        workspace,
        session.STATE_FINGERPRINT_READY,
        "sess-2",
    )

    # 已有 MONITORING 旧 session，新的 init 必须失败
    session._write_state(workspace, session.STATE_BROWSER_READY, "sess-1")
    session._write_state(workspace, session.STATE_FINGERPRINT_READY, "sess-1")
    session._write_state(workspace, session.STATE_MONITORING, "sess-1")
    assert_raises(
        "在 MONITORING 时 init 失败",
        session.SessionError,
        session._write_state,
        workspace,
        session.STATE_WORKSPACE_READY,
        None,
    )


# ----------------------------------------------------------------------------
# 3. 浏览器候选路径矩阵
# ----------------------------------------------------------------------------

print("[3/9] 浏览器候选路径矩阵")
windows_env = {
    "PROGRAMFILES": str(Path("C:/Program Files")),
    "PROGRAMFILES(X86)": str(Path("C:/Program Files (x86)")),
    "LOCALAPPDATA": str(Path("C:/Users/test/AppData/Local")),
}
windows_candidates = session.browser_candidates("Windows", windows_env)
assert_true("Windows 含 Chrome 候选", any("chrome.exe" in c for c in windows_candidates))
assert_true("Windows 含 Edge 候选", any("msedge.exe" in c for c in windows_candidates))

linux_candidates = session.browser_candidates("Linux", {})
assert_true("Linux 候选为列表", isinstance(linux_candidates, list))

darwin_candidates = session.browser_candidates("Darwin", {})
assert_true("macOS 含 Chrome 候选", any("Google Chrome" in c for c in darwin_candidates))

unknown_candidates = session.browser_candidates("Plan9", {})
assert_eq("未知 OS 候选为空", unknown_candidates, [])


# ----------------------------------------------------------------------------
# 4. 指纹判定分级
# ----------------------------------------------------------------------------

print("[4/9] 浏览器指纹一致性审计分级")
host_environment = {
    "host_os": "Windows",
    "browser_major": 150,
}
fingerprint_blocking = session.evaluate_fingerprint(
    {
        "webdriver": True,
        "user_agent": "HeadlessChrome/150.0.0.0",
        "platform": "Win32",
        "language": "zh-CN",
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai",
        "api_presence": {
            "fetch": True,
            "xhr": True,
            "websocket": True,
            "performance": True,
            "crypto_subtle": True,
        },
        "screen": {"width": 1920, "height": 1080},
        "viewport": {"inner_width": 1920, "inner_height": 1080, "device_pixel_ratio": 1.0},
        "hardware_concurrency": 16,
        "plugins_count": 5,
        "mime_types_count": 10,
        "canvas_stable": True,
        "webgl": {"renderer": "ANGLE (Intel)"},
    },
    "Windows",
    150,
)
assert_eq("阻断项命中 → BLOCKED", fingerprint_blocking["status"], "BLOCKED")
assert_true("阻断项包含 webdriver", any("webdriver" in item for item in fingerprint_blocking["blocking"]))
assert_true("阻断项包含 HeadlessChrome", any("HeadlessChrome" in item for item in fingerprint_blocking["blocking"]))

fingerprint_warning = session.evaluate_fingerprint(
    {
        "webdriver": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "platform": "Win32",
        "language": "zh-CN",
        "locale": "en-US",
        "timezone": "Asia/Shanghai",
        "api_presence": {
            "fetch": True,
            "xhr": True,
            "websocket": True,
            "performance": True,
            "crypto_subtle": True,
        },
        "screen": {"width": 1920, "height": 1080},
        "viewport": {"inner_width": 1920, "inner_height": 1080, "device_pixel_ratio": 1.0},
        "hardware_concurrency": 16,
        "plugins_count": 0,
        "mime_types_count": 0,
        "canvas_stable": False,
        "webgl": {"renderer": "ANGLE (Intel, Intel(R) UHD Graphics)"},
    },
    "Windows",
    150,
)
assert_eq("警告项命中 → WARN", fingerprint_warning["status"], "WARN")
assert_true("警告项包含语言不一致", any("不一致" in item for item in fingerprint_warning["warnings"]))
assert_true("警告项包含 plugins=0", any("plugins" in item for item in fingerprint_warning["warnings"]))


# ----------------------------------------------------------------------------
# 5. 步骤证据关联
# ----------------------------------------------------------------------------

print("[5/9] 步骤证据关联")
with tempfile.TemporaryDirectory() as tmp:
    session_dir = Path(tmp)
    (session_dir / "user-actions.json").write_text(
        json.dumps(
            {
                "version": "1.0",
                "created_at": "2026-07-28T10:00:00+08:00",
                "actions": [
                    {
                        "step": 1,
                        "timestamp": "2026-07-28T10:00:01+08:00",
                        "type": "click",
                        "selectors": ["#submit"],
                    },
                    {
                        "step": 2,
                        "timestamp": "2026-07-28T10:00:05+08:00",
                        "type": "fill",
                        "selectors": ["#search"],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with (session_dir / "user-session.har.jsonl").open("w", encoding="utf-8") as file:
        file.write(
            json.dumps(
                {
                    "ts": "2026-07-28T10:00:01.500+08:00",
                    "kind": "response",
                    "url": "https://example.com/api",
                    "method": "POST",
                    "status": 200,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        file.write(
            json.dumps(
                {
                    "ts": "2026-07-28T10:00:20+08:00",
                    "kind": "response",
                    "url": "https://example.com/other",
                    "method": "GET",
                    "status": 200,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    with (session_dir / "js-runtime.jsonl").open("w", encoding="utf-8") as file:
        file.write(
            json.dumps(
                {
                    "ts_ms": int(
                        time.mktime(time.strptime("2026-07-28 10:00:01", "%Y-%m-%d %H:%M:%S"))
                    )
                    * 1000,
                    "type": "fetch-call",
                    "url": "https://example.com/api",
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    index_path = session.build_step_evidence_index(session_dir)
    assert_true("索引文件已生成", index_path.is_file())
    index_doc = json.loads(index_path.read_text(encoding="utf-8"))
    assert_eq("步骤数=2", len(index_doc["steps"]), 2)
    step_one = index_doc["steps"][0]
    assert_eq("第 1 步关联 1 条网络响应", len(step_one["network"]), 1)
    assert_eq("第 1 步关联 1 条 JS 事件", len(step_one["js_runtime"]), 1)
    step_two = index_doc["steps"][1]
    assert_eq("第 2 步无网络响应关联", len(step_two["network"]), 0)


# ----------------------------------------------------------------------------
# 6. 录制器脱敏
# ----------------------------------------------------------------------------

print("[6/9] 录制器脱敏")
redacted_value = recorder._redact_value("Authorization=Bearer abc123 token=secret")
assert_eq("值内容含 token 脱敏", redacted_value, "***REDACTED***")

redacted_form = recorder._redact_post_data("username=alice&password=secret123&token=xyz")
assert_true("表单密码字段脱敏", "password=***REDACTED***" in redacted_form, redacted_form)
assert_true("表单 token 字段脱敏", "token=***REDACTED***" in redacted_form, redacted_form)

redacted_headers = recorder._redact_headers(
    {
        "Authorization": "Bearer abc",
        "Cookie": "sid=abc",
        "X-CSRF-Token": "xyz",
        "Content-Type": "application/json",
    }
)
assert_eq("Authorization header 脱敏", redacted_headers["Authorization"], "***REDACTED***")
assert_eq("Cookie header 脱敏", redacted_headers["Cookie"], "***REDACTED***")
assert_eq("CSRF token header 脱敏", redacted_headers["X-CSRF-Token"], "***REDACTED***")
assert_eq("Content-Type 保留", redacted_headers["Content-Type"], "application/json")

redacted_body = recorder._redact_body_preview('{"password":"abc","name":"alice","token":"xyz"}')
assert_true("JSON body 密码脱敏", '"password":"***"' in redacted_body, redacted_body)
assert_true("JSON body token 脱敏", '"token":"***"' in redacted_body, redacted_body)
assert_true("JSON body 普通字段保留", '"name":"alice"' in redacted_body, redacted_body)


# ----------------------------------------------------------------------------
# 7. JS 监控脚本片段校验
# ----------------------------------------------------------------------------

print("[7/9] JS 监控脚本关键逻辑")
assert_true("fetch 包覆存在", "const originalFetch = window.fetch" in session.JS_MONITOR_SCRIPT)
assert_true("XHR open/send 包覆存在", "XMLHttpRequest.prototype.open" in session.JS_MONITOR_SCRIPT)
assert_true("WebSocket send 包覆存在", "WebSocket.prototype.send" in session.JS_MONITOR_SCRIPT)
assert_true("console.warn/error 包覆存在", "console[level] = function" in session.JS_MONITOR_SCRIPT)
assert_true("window.error 监听存在", "window.addEventListener('error'" in session.JS_MONITOR_SCRIPT)
assert_true("unhandledrejection 监听存在", "unhandledrejection" in session.JS_MONITOR_SCRIPT)
assert_true("performance.getEntriesByType('resource') 补采", "performance.getEntriesByType('resource')" in session.JS_MONITOR_SCRIPT)
assert_true("ready 时间点声明", "ready 时间点之前补采" in SESSION_SCRIPT.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------
# 8. 中文注释/docstring/日志
# ----------------------------------------------------------------------------

print("[8/9] 中文注释/docstring/日志")
session_text = SESSION_SCRIPT.read_text(encoding="utf-8")
recorder_text = RECORDER_SCRIPT.read_text(encoding="utf-8")
assert_true("会话脚本首部 docstring 中文", "逆向分析工作区与 Web 协作会话编排工具" in session_text)
assert_true("会话脚本 print 中文", "工作区已创建" in session_text and "会话已正常停止" in session_text)
assert_true("会话脚本显式资源所有权声明", "资源所有权铁律" in session_text and "不可关闭" in session_text)
assert_true("录制脚本 input/fill 强化段含中文注释", "DOM 层按字段属性命中即写 ***REDACTED***" in recorder_text)
assert_true("录制脚本含中文日志标签", "必须使用中文" in recorder_text or "兜底匹配" in recorder_text)

ascii_only = re.compile(r"^[\x00-\x7f]+$")
section_divider = re.compile(r"^#+\s*[-=]+\s*$")
suspicious_english_comments: list[str] = []
for script in (SESSION_SCRIPT, RECORDER_SCRIPT):
    for line_no, line in enumerate(script.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("#"):
            continue
        if section_divider.match(stripped):
            continue
        body = stripped.lstrip("#").strip()
        if body and ascii_only.match(body):
            suspicious_english_comments.append(f"{script.name}:{line_no}: {stripped[:60]}")
assert_eq("无英文注释残留（已豁免纯 ASCII 分隔线）", suspicious_english_comments, [])


# ----------------------------------------------------------------------------
# 9. JS 监控器 flush 上限
# ----------------------------------------------------------------------------

print("[9/9] JS 监控器 flush 上限")
assert_eq("单次 flush 事件上限=200", session.MAX_JS_EVENTS_PER_FLUSH, 200)
assert_eq("单条事件字符上限=1000", session.MAX_JS_EVENT_CHARS, 1000)
assert_eq("JS 日志总字节上限=5MiB", session.MAX_JS_LOG_BYTES, 5 * 1024 * 1024)
assert_eq("证据关联时间窗=1000ms", session.EVIDENCE_WINDOW_MS, 1000)


print("\n全部 9 类断言通过。")
