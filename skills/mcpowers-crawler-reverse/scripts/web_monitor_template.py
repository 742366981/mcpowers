"""
web_monitor_template.py — 标准化 Web 浏览器监控模板（v2.21.2 新增）

本工具把浏览器访问 URL 的全过程固化为可复用模板：监听网络请求/响应、读取
Console/Cookies/Storage、截图、输出 result.json + screenshot.json。供 Web 逆向
/ 抓包分析 / 浏览器行为取证场景直接调用，避免从零写 DrissionPage 配置时踩 7
类常见坑（监听启动时机、循环退出、响应体判空、postData 保护、Console 超时、
ChromiumOptions 配置、截图风控容错）。

公开契约：
- create_browser(headless=False) → 启动一个 Chromium 浏览器实例
- monitor(url, output_dir='.', headless=False, max_packets=200) →
  访问 URL、循环捕获网络请求/响应、读取 Console/Cookies/Storage、截图、输出
  result.json + screenshot.png

资源所有权铁律：本工具通过 DrissionPage 启动的浏览器实例在 monitor 退出时统
一 close()。如需接管用户已有的 Chrome，请使用专门的协作会话编排工具而非
本工具。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from DrissionPage import Chromium, ChromiumOptions

__all__ = ["create_browser", "monitor"]

# 默认监听循环上限：捕获多少个网络包后自动停止（无论是否还有流量）
DEFAULT_MAX_PACKETS = 200
# 单次 listen.wait 超时（秒）：超时即视为流量已停
LISTEN_WAIT_TIMEOUT = 1.0
# Console 日志轮询超时（秒）：避免无限等待
CONSOLE_STEPS_TIMEOUT = 2.0
# POST body 截断长度（字符）：防止超长 base64 / 文件上传把 result.json 撑爆
POST_DATA_PREVIEW_CHARS = 500
# Response body 截断长度（字符）
RESPONSE_BODY_PREVIEW_CHARS = 300


def create_browser(headless: bool = False) -> Chromium:
    """创建并返回一个 Chromium 浏览器实例。

    显式构造 ChromiumOptions() 而非直接 Chromium()：保留 set_local_port /
    set_user_data_path / set_proxy 等可扩展点，便于后续按场景调整。

    Args:
        headless: 是否无头模式（默认 False，便于观察；CI 验证可改 True）。

    Returns:
        Chromium 实例。调用方负责在不再使用时 close() 释放资源。
    """
    options = ChromiumOptions()
    if headless:
        # 不同 DrissionPage 版本的 headless 参数名可能不同；用 set_argument
        # 显式传入 --headless 以保证跨版本兼容
        options.set_argument("--headless")
    return Chromium(addr_or_opts=options)


def monitor(
    url: str,
    output_dir: str | Path = ".",
    headless: bool = False,
    max_packets: int = DEFAULT_MAX_PACKETS,
) -> dict[str, Any]:
    """监控浏览器访问 URL 的完整过程，输出 result.json + screenshot.png。

    标准流程：

    1. 创建浏览器
    2. tab.listen.start() ← **必须在 get() 之前**，否则初始请求抓不到
    3. tab.get(url, timeout=30) + tab.wait(2) 等待页面稳定
    4. 循环 max_packets 次 tab.listen.wait(timeout=1)，无包则 break
    5. 读取 tab.console / tab.cookies / localStorage / sessionStorage
    6. 输出 result.json + screenshot.png

    Args:
        url: 目标 URL。
        output_dir: 产物输出目录（默认当前目录）。自动 mkdir -p。
        headless: 是否无头模式。
        max_packets: 监听循环上限（默认 200）。

    Returns:
        dict 形如：
            {
                "timestamp": ISO8601,
                "url": 实际访问的最终 URL,
                "title": 页面标题,
                "packets_count": 捕获请求数,
                "api_packets": [URL 含 webapi 的请求子集],
                "post_packets": [POST/PUT/DELETE 请求子集],
                "all_packets": [所有请求],
                "console_logs": [{level, text}],
                "cookies": {name: value},
                "storage": {localStorage: {...}, sessionStorage: {...}},
            }
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    browser = create_browser(headless=headless)
    try:
        tab = browser.latest_tab

        # ===== 关键顺序：listen.start() 必须在 get() 之前 =====
        tab.listen.start()

        tab.get(url, timeout=30)
        tab.wait(2)

        print(f"URL: {tab.url}")
        print(f"Title: {tab.title}")

        # ===== 循环捕获（无包时 break，避免无限等待）=====
        packets: list[dict[str, Any]] = []
        for _ in range(max_packets):
            packet = tab.listen.wait(timeout=LISTEN_WAIT_TIMEOUT)
            if not packet:
                break
            req = packet.request
            res = packet.response

            item: dict[str, Any] = {
                "method": req.method,
                "url": req.url,
                "type": req.resourceType,
                "status": res.status if res else None,
                "headers": dict(req.headers) if req.headers else {},
            }
            # ===== 异常路径保护：postData 可能为 None，部分请求无 postData =====
            try:
                pd = req.postData
                if pd:
                    item["postData"] = str(pd)[:POST_DATA_PREVIEW_CHARS]
            except Exception:
                pass
            # ===== 异常路径保护：res.body 可能为 None，直接 .body 会抛 NoneType =====
            try:
                if res and res.body:
                    item["responseBody"] = str(res.body)[:RESPONSE_BODY_PREVIEW_CHARS]
            except Exception:
                pass
            packets.append(item)

        print(f"捕获到 {len(packets)} 个请求")

        # ===== Console 日志（设超时，避免阻塞）=====
        console_logs: list[dict[str, str]] = []
        try:
            for msg in tab.console.steps(timeout=CONSOLE_STEPS_TIMEOUT):
                console_logs.append({"level": msg.level, "text": msg.text})
        except Exception:
            pass

        # ===== Cookies / Storage =====
        # ===== 异常路径保护：cookies 可能为空 / 抛错（无 cookies 的页面） =====
        try:
            cookies = tab.cookies()
        except Exception:
            cookies = []
        # localStorage / sessionStorage 通过 run_js 取 JSON 字符串
        # ===== 异常路径保护：run_js 在 JS 执行失败时（如目标页未完整加载）抛 JavaScriptError =====
        try:
            local_storage = tab.run_js("return JSON.stringify(localStorage)")
        except Exception:
            local_storage = None
        try:
            session_storage = tab.run_js("return JSON.stringify(sessionStorage)")
        except Exception:
            session_storage = None

        result: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "url": tab.url,
            "title": tab.title,
            "packets_count": len(packets),
            "api_packets": [p for p in packets if "webapi" in p["url"].lower()],
            "post_packets": [
                p for p in packets if p["method"] in ["POST", "PUT", "DELETE"]
            ],
            "all_packets": packets,
            "console_logs": console_logs,
            "cookies": {c["name"]: c["value"] for c in cookies},
            "storage": {
                "localStorage": json.loads(local_storage) if local_storage else {},
                "sessionStorage": (
                    json.loads(session_storage) if session_storage else {}
                ),
            },
        }

        result_path = out / "result.json"
        with result_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # ===== 截图风控容错：部分网站有反爬，截图可能失败 =====
        screenshot_path = out / "screenshot.png"
        try:
            tab.get_screenshot(path=str(screenshot_path))
        except Exception:
            pass

        return result
    finally:
        # 关闭本工具创建的浏览器，释放资源
        browser.quit()


if __name__ == "__main__":
    # 示例调用：把 URL 替换为目标网站
    # 实际使用时建议把 output_dir 改为你想存放产物的目录
    import sys

    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        # 默认占位 URL（请替换为实际目标）
        target_url = "https://httpbin.org/anything"

    result = monitor(target_url, output_dir=".")
    print(f"\n最终 URL: {result['url']}")
    print(f"Title: {result['title']}")
    print(f"Packets: {result['packets_count']}")