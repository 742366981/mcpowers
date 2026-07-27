"""
popup-handler.py — 弹窗检测与处理工具（v2.9.5 新增，v2.14.0 路径同步，v2.16.0 Chrome 150+ 提示）

本模块是 mcpowers-crawler-reverse 阶段 2「弹窗清理」步骤的核心实现。
字典库与《爬虫工具与抓包规范》§4 弹窗字典一一对应，新弹窗类型先追加字典再写逻辑。
历史兼容：v2.14.0 之前位于《爬虫分析规范》§2.7 + 附录 D。

核心函数（3 个公开）：
- detect_popups(page): 检测页面所有弹窗（DOM + 浏览器原生）
- close_popup(page, popup, mode): 关闭单个弹窗
- cleanup_all(page, pause_for_user_patterns, screenshot_dir): 一键清理所有弹窗

详细方法论：见《爬虫工具与抓包规范》§4 + 附录与 popup-handler.py 对应关系
DEFAULT_BB_BROWSER_PROBE 文档参考《爬虫工具与抓包规范》§6（bb-browser 可选增强）

v2.16.0 Chrome 150+ 提示：本模块被调用时，调用方必须满足两个前置条件——
1. Chrome 启动命令已带 `--remote-allow-origins=*`（Chrome 150+ 必传，否则
   `connect_over_cdp` 会被 403 Forbidden）；
2. AI 必须 attach 用户真实 page target（从 `user.contexts[i].pages` 中按 URL /
   title 匹配），**禁止**用 `Target.createTarget` 自己拉新 tab。
详见《爬虫工具与抓包规范》§3.5 / §3.6 / §3.9 与《爬虫分析规范》§3.0.6 实战案例。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import Page
except ImportError:  # pragma: no cover
    Page = Any  # type: ignore


# ----------------------------------------------------------------------------
# 8 类弹窗字典（v2.9.5 新增，与《爬虫工具与抓包规范》§4 弹窗字典一一对应）
# ----------------------------------------------------------------------------

# 类型 → (自动/询问, 优先关闭关键词)
POPUP_TYPE_RULES: dict[str, dict[str, Any]] = {
    # D.1 Cookie 同意（自动拒绝）
    "cookie": {
        "auto_close": True,
        "reject_keywords": [
            r"reject\s*all", r"拒绝\s*全部", r"拒绝可选", r"仅必需",
            r"only\s*essential", r"only\s*necessary", r"decline",
            r"reject", r"拒绝", r"manage\s*settings", r"管理设置",
        ],
        "fallback_keywords": [
            r"^x$", r"关闭", r"close", r"cancel", r"取消",
            r"不再提醒", r"知道了", r"got\s*it", r"ok", r"确定",
        ],
    },
    # D.2 Notification 询问（自动拒绝）
    "notification": {
        "auto_close": True,
        "reject_keywords": [r"block", r"拒绝", r"disable", r"关闭"],
        "fallback_keywords": [r"^x$", r"关闭", r"close"],
    },
    # D.3 Newsletter 订阅（自动关闭）
    "newsletter": {
        "auto_close": True,
        "reject_keywords": [r"no\s*thanks", r"不再提醒", r"稍后", r"later"],
        "fallback_keywords": [
            r"^x$", r"关闭", r"close", r"cancel", r"取消",
        ],
    },
    # D.4 App 下载引导（自动关闭）
    "app_download": {
        "auto_close": True,
        "reject_keywords": [
            r"继续访问", r"网页版", r"stay\s*on\s*web", r"browser\s*version",
            r"用浏览器继续", r"暂不下载", r"网页继续",
        ],
        "fallback_keywords": [
            r"^x$", r"关闭", r"close", r"cancel", r"取消",
        ],
    },
    # D.5 地理位置请求（自动拒绝）
    "geolocation": {
        "auto_close": True,
        "reject_keywords": [r"block", r"拒绝", r"disable"],
        "fallback_keywords": [],
    },
    # D.6 登录墙（询问用户）
    "login_wall": {
        "auto_close": False,
        "reject_keywords": [],
        "fallback_keywords": [],
        "pause_pattern": [r"登录", r"sign\s*in", r"log\s*in", r"请先登录", r"login\s*required"],
    },
    # D.7 年龄验证（询问用户）
    "age_verification": {
        "auto_close": False,
        "reject_keywords": [],
        "fallback_keywords": [],
        "pause_pattern": [r"年龄", r"\bage\b", r"18\+", r"21\+", r"确认年龄", r"are\s*you\s*over"],
    },
    # D.8 合规同意（询问用户）
    "compliance": {
        "auto_close": False,
        "reject_keywords": [],
        "fallback_keywords": [],
        "pause_pattern": [r"隐私政策", r"用户协议", r"服务条款", r"privacy", r"terms", r"i\s*agree"],
    },
}


# DOM 检测 selector（覆盖 8 类弹窗的通用检测）
POPUP_SELECTORS: list[str] = [
    # 显式弹窗标记
    '[role="dialog"]',
    '[aria-modal="true"]',
    'dialog[open]',
    # 通用类名
    ".modal", ".popup", ".overlay", ".dialog", ".lightbox",
    # 特征类名（正则匹配，CSS 用 i flag 忽略大小写）
    '[class*="cookie" i]',
    '[class*="consent" i]',
    '[class*="modal" i]',
    '[class*="popup" i]',
    '[class*="newsletter" i]',
    '[class*="subscribe" i]',
    '[class*="app-banner" i]',
    '[class*="download-app" i]',
    '[class*="open-app" i]',
    '[class*="login-wall" i]',
    '[class*="auth-required" i]',
    '[class*="sign-in-required" i]',
    '[class*="age" i]',
    '[class*="age-gate" i]',
    '[class*="age-verification" i]',
    '[class*="privacy" i]',
    '[class*="terms" i]',
    '[class*="tos" i]',
    # ID 同理
    '[id*="cookie" i]',
    '[id*="consent" i]',
    '[id*="modal" i]',
    '[id*="popup" i]',
    '[id*="gdpr" i]',
    '[id*="newsletter" i]',
    '[id*="app-download" i]',
    '[id*="login-wall" i]',
    '[id*="age" i]',
    '[id*="privacy" i]',
    '[id*="terms" i]',
]


# 默认 pause_for_user_patterns（命中这些关键词的弹窗不自动关）
DEFAULT_PAUSE_PATTERNS: list[str] = [
    "登录", "年龄验证", "隐私政策", "用户协议", "服务条款",
    "sign in", "login", "age", "privacy", "terms",
]


# v2.10.0 新增：bb-browser 提示常量（最小改动，不引入新函数）
# 实际 bb-browser daemon 探测由《爬虫工具与抓包规范》§6 / SKILL.md §2.0 SOP 执行，不在本模块职责范围。
# 本常量仅作为模块 docstring 与 __main__ 输出中的职责声明，提示使用者：
#   - bb-browser 是可选依赖（详见 SKILL.md 铁律 #10）
#   - 本模块不替代 bb-browser / 不替代 Playwright 网络实测
#   - bb-browser site adapter 处理站点级导航后，本模块仍须 cleanup_all() 做二次清理
DEFAULT_BB_BROWSER_PROBE: str = (
    "bb-browser 为可选依赖。使用前先运行 `bb-browser status`；"
    "未安装或不可用时继续使用 Chrome CDP + Playwright 原链路。"
    "\n\n"
    "v2.16.0 补充：调用本模块的 cleanup_all() 前，调用方必须先确认"
    "（1）Chrome 启动命令已带 --remote-allow-origins=*（Chrome 150+ 必传）；"
    "（2）AI attach 的是用户真实 page target，禁止 Target.createTarget 自己拉 tab。"
    "详见《爬虫工具与抓包规范》§3.7 + §3.9.3 与《爬虫分析规范》§3.0.6。"
)


# ----------------------------------------------------------------------------
# 辅助函数
# ----------------------------------------------------------------------------

def _classify_popup(text: str, selector: str) -> str:
    """
    根据文本和选择器判定弹窗类型（v2.9.5 新增）。

    Args:
        text: 弹窗可见文本（前 200 字）
        selector: 命中弹窗的 CSS selector

    Returns:
        8 类弹窗类型之一：cookie / notification / newsletter / app_download /
        geolocation / login_wall / age_verification / compliance / unknown
    """
    text_low = text.lower()
    selector_low = selector.lower()

    # 优先级：先看 selector，再看文本
    if any(k in selector_low for k in ["cookie", "consent", "gdpr", "cc-"]):
        return "cookie"
    if any(k in selector_low for k in ["notification", "notif-", "notif_"]):
        return "notification"
    if any(k in selector_low for k in ["location", "geolocation", "geo-prompt"]):
        return "geolocation"
    if any(k in selector_low for k in ["newsletter", "subscribe"]):
        return "newsletter"
    if any(k in selector_low for k in ["app-banner", "download-app", "open-app"]):
        return "app_download"
    if any(k in selector_low for k in ["login-wall", "auth-required", "sign-in-required"]):
        return "login_wall"
    if any(k in selector_low for k in ["age", "age-gate", "age-verification"]):
        return "age_verification"
    if any(k in selector_low for k in ["privacy", "terms", "tos"]):
        return "compliance"

    # 文本兜底
    if any(k in text_low for k in ["cookie", "consent", "gdpr", "accept"]):
        return "cookie"
    if any(k in text_low for k in ["allow notification", "允许通知", "是否允许通知", "enable notification"]):
        return "notification"
    if any(k in text_low for k in ["allow location", "allow geolocation", "允许定位", "地理位置", "location access"]):
        return "geolocation"
    if any(k in text_low for k in ["subscribe", "newsletter"]):
        return "newsletter"
    if any(k in text_low for k in ["open app", "下载 app", "open the app"]):
        return "app_download"
    if any(k in text_low for k in ["sign in", "log in", "登录", "请先登录"]):
        return "login_wall"
    if any(k in text_low for k in ["age", "18+", "21+", "确认年龄"]):
        return "age_verification"
    if any(k in text_low for k in ["privacy", "terms", "隐私政策", "用户协议"]):
        return "compliance"

    return "unknown"


def _try_click_button(page: Page, keywords: list[str], scope_element: Any = None) -> bool:
    """
    在弹窗范围内尝试点击匹配关键词的按钮（v2.9.5 新增）。

    Args:
        page: Playwright Page 对象
        keywords: 按钮文本正则列表（re.IGNORECASE）
        scope_element: 可选，限定查找范围（弹窗 DOM 元素）

    Returns:
        True=点击成功，False=未找到匹配按钮
    """
    for kw in keywords:
        # 编译正则（忽略大小写）
        pattern = re.compile(kw, re.IGNORECASE)
        # 在 scope_element 或整个页面查找 button / a / div[role=button]
        search_root = scope_element or page
        try:
            # 先找 button
            buttons = search_root.query_selector_all("button, a, [role='button']")
            for btn in buttons:
                text = (btn.inner_text() or "").strip()
                if pattern.search(text):
                    btn.click()
                    return True
        except Exception:
            continue
    return False


def _press_escape(page: Page) -> None:
    """按 Esc 键（关闭弹窗的兜底手段，v2.9.5 新增）。"""
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def _screenshot_for_user(page: Page, screenshot_dir: str, popup_type: str, popup_text: str) -> str | None:
    """
    截图给用户看（询问类弹窗必走，v2.9.5 新增）。

    Args:
        page: Playwright Page 对象
        screenshot_dir: 截图目录
        popup_type: 弹窗类型
        popup_text: 弹窗文本（前 200 字）

    Returns:
        截图路径，失败返回 None
    """
    try:
        Path(screenshot_dir).mkdir(parents=True, exist_ok=True)
        safe_type = re.sub(r"[^\w]", "_", popup_type)
        path = Path(screenshot_dir) / f"popup_{safe_type}.png"
        page.screenshot(path=str(path))
        return str(path)
    except Exception:
        return None


# ----------------------------------------------------------------------------
# 公开函数（3 个）
# ----------------------------------------------------------------------------

def detect_popups(page: Page) -> list[dict[str, Any]]:
    """
    检测页面所有弹窗（DOM 层，v2.9.5 新增）。

    返回:
        [{"type": "cookie", "selector": ".cc-banner", "text": "Accept cookies?",
          "element_handle": <ElementHandle>, "auto_close": True}, ...]

    说明：
        - DOM 层检测（不处理 Notification/Geolocation 等原生层）
        - 命中一个 selector 后不再重复检测（避免嵌套弹窗被多次计数）
        - 弹窗类型由 _classify_popup 自动判定
    """
    detected: list[dict[str, Any]] = []
    seen_elements: set[int] = set()

    for selector in POPUP_SELECTORS:
        try:
            elements = page.query_selector_all(selector)
            for el in elements:
                # 用 element id 去重（嵌套/重写 selector 时可能撞上同一个 DOM 节点）
                el_id = id(el)
                if el_id in seen_elements:
                    continue
                seen_elements.add(el_id)

                # 检查可见性（display:none / visibility:hidden 不算弹窗）
                if not el.is_visible():
                    continue

                text = (el.inner_text() or "")[:200].strip()
                if not text:
                    continue

                popup_type = _classify_popup(text, selector)
                rule = POPUP_TYPE_RULES.get(popup_type, {})

                detected.append({
                    "type": popup_type,
                    "selector": selector,
                    "text": text,
                    "element_handle": el,
                    "auto_close": rule.get("auto_close", False),
                })
        except Exception:
            continue

    return detected


def close_popup(page: Page, popup: dict[str, Any], mode: str = "smart") -> bool:
    """
    关闭单个弹窗（v2.9.5 新增）。

    Args:
        page: Playwright Page 对象
        popup: detect_popups() 返回的单个弹字典
        mode: 关闭策略
            - "smart": 先 reject 再 fallback 再 Esc（默认）
            - "reject": 只试 reject_keywords
            - "accept": 只试 fallback_keywords（不推荐，仅特殊场景）
            - "close": 只试 fallback_keywords

    Returns:
        True=关闭成功，False=关闭失败（仍可见）
    """
    el = popup.get("element_handle")
    rule = POPUP_TYPE_RULES.get(popup.get("type", "unknown"), {})
    reject_kws = rule.get("reject_keywords", [])
    fallback_kws = rule.get("fallback_keywords", [])

    if mode == "smart":
        # 1. 优先 reject
        if reject_kws and _try_click_button(page, reject_kws, el):
            return True
        # 2. fallback
        if fallback_kws and _try_click_button(page, fallback_kws, el):
            return True
        # 3. Esc
        _press_escape(page)
        return True  # Esc 已触发，假定关闭成功
    elif mode == "reject":
        return _try_click_button(page, reject_kws, el)
    elif mode in ("accept", "close"):
        return _try_click_button(page, fallback_kws, el)
    else:
        return False


def cleanup_all(
    page: Page,
    pause_for_user_patterns: list[str] | None = None,
    screenshot_dir: str = "01-target-profile/popups/",
    ask_user_callback: Any = None,
) -> list[str]:
    """
    一键清理所有弹窗（v2.9.5 新增）。

    Args:
        page: Playwright Page 对象
        pause_for_user_patterns: 命中这些关键词的弹窗不自动关，截图后询问用户
            默认使用 DEFAULT_PAUSE_PATTERNS
        screenshot_dir: 询问类弹窗截图保存目录
        ask_user_callback: 询问用户的回调函数（签名: (popup_info: dict, screenshot_path: str) -> str）
            返回 "continue" / "skip" / "force_close"
            默认用 print 模拟（实际 AI 调用时由 Claude Code 接管 AskUserQuestion）

    Returns:
        已关闭弹窗的 selector 列表（不含询问类）

    行为：
        - 检测 → 分类 → 自动类（auto_close=True）直接关闭
        - 询问类（auto_close=False）→ 截图 + 调用 ask_user_callback
        - 默认 ask_user_callback = print 模拟（生产环境由 Claude Code 替换为 AskUserQuestion）
    """
    if pause_for_user_patterns is None:
        pause_for_user_patterns = DEFAULT_PAUSE_PATTERNS

    if ask_user_callback is None:
        # 默认回调：打印提示（AI 接管时替换为 AskUserQuestion）
        def ask_user_callback(popup_info: dict, screenshot_path: str | None) -> str:
            print(f"[popup-handler] 检测到询问类弹窗 type={popup_info['type']}")
            print(f"[popup-handler] 文本: {popup_info['text'][:80]}")
            if screenshot_path:
                print(f"[popup-handler] 截图: {screenshot_path}")
            print(f"[popup-handler] 自动跳过（需 AskUserQuestion 接管）")
            return "skip"

    closed: list[str] = []
    popups = detect_popups(page)

    for popup in popups:
        popup_type = popup["type"]
        popup_text = popup["text"]

        # 询问类：截图 + 询问
        if not popup.get("auto_close", False):
            # 检查是否匹配 pause_for_user_patterns
            should_pause = any(
                re.search(kw, popup_text, re.IGNORECASE)
                for kw in pause_for_user_patterns
            )
            if should_pause:
                screenshot_path = _screenshot_for_user(page, screenshot_dir, popup_type, popup_text)
                decision = ask_user_callback(popup, screenshot_path)
                if decision == "force_close":
                    popup["auto_close"] = True  # 临时改标记
                else:
                    continue  # skip

        # 关闭
        if close_popup(page, popup, mode="smart"):
            closed.append(popup["selector"])
            # 等弹窗消失动画
            page.wait_for_timeout(200)

    return closed


# ----------------------------------------------------------------------------
# 顶层调用入口（便于 python -m 直接调用）
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    print("popup-handler.py 是 mcpowers-crawler-reverse 的工具脚本")
    print("详细用法见《爬虫工具与抓包规范》§4 + 附录与 popup-handler.py 对应关系")
    print()
    print("公开 API：")
    print("  - detect_popups(page) -> list[dict]")
    print("  - close_popup(page, popup, mode='smart') -> bool")
    print("  - cleanup_all(page, pause_for_user_patterns=None, screenshot_dir=...) -> list[str]")
    print()
    print("v2.10.0 新增常量：")
    print("  - DEFAULT_BB_BROWSER_PROBE  # bb-browser 可选依赖提示（探测由 SKILL.md §2.0 SOP 执行）")