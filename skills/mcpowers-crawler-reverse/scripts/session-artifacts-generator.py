"""
session-artifacts-generator.py — Web 会话派生产物自动生成器（v2.21.0 新增）

本工具由 `reverse-analysis-session.py web-stop` 在证据 flush 和步骤证据索引完成后自动
调用，把已停止会话的 HAR + 步骤证据转换为 3 类派生产物，供 AI 阶段 2 接手：

1. `02-接口分析/目标接口候选.md`：按六维评分（响应码 200 / 操作触发 / 业务 JSON 字段 /
   反爬特征 / 静态 vs 动态参数 / 重复次数）打分排序的前 10 名候选，含总分明细与
   lifecycle 分类。
2. `02-接口分析/响应样本/{rank}-{method}-{path}-{hash8}.json`：每个 top10 接口
   一个最大且能解析 JSON 的脱敏 preview，envelope 显式声明不代表完整响应体
   （HAR 现状仅 1024 字符 body_preview）。
3. `04-模块封装/{module}/client.py` 与 `quick_test.py`：v2.17.0 类式封装种子，
   仅在文件不存在时生成；含 build_request / do_request / parse_response /
   request_and_parse 四方法 + 业务方法零前置参数 + 6 类 lifecycle 标签占位。

公开 API：
- `run_artifacts_generation(workspace, session_dir) -> dict`：主入口，返回产物路径 +
  status + warnings。
- `ArtifactsGenerationError`：输入链路不完整或路径越界时抛出。

设计原则：
- v2.17.0：类式封装 + 请求/解析分离 + 零前置参数 + quick_test + 中文分析文件名。
- v2.18.0：仅消费 DrissionPage 默认接管产生的 HAR，不引入 Playwright codegen。
- v2.19.0：失败不破坏 web-stop 收尾，不关闭外部资源，STATE_STOPPED 仍正常写入。
- v2.20.0：不读取 / 重分配 / 覆盖 chrome_port。
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


# ----------------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------------

LIFECYCLE_LABELS: tuple[str, ...] = (
    "reusable",
    "per-request",
    "single-use-token",
    "session-bound",
    "time-bound",
    "challenge-bound",
)

# 静态资源后缀（被预过滤）
STATIC_SUFFIXES: tuple[str, ...] = (
    ".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".woff", ".woff2",
    ".ttf", ".ico", ".map", ".gif", ".webp",
)

# 埋点 / 心跳 / 健康检查关键字（按 path 包含判定）
NOISE_PATH_TOKENS: tuple[str, ...] = (
    "/log/", "/track", "/analytics", "/collect", "/beacon",
    "/health", "/ping", "/heartbeat", "/keepalive",
    "/favicon.ico",
)

# 业务 JSON 字段名（用于"业务 JSON 字段"维度评分）
BUSINESS_FIELD_NAMES: tuple[str, ...] = (
    "data", "list", "result", "records", "items",
    "detail", "content", "rows", "entries", "payload",
)

# 反爬 / challenge 关键字（用于"反爬特征"维度）
ANTI_BOT_TOKENS: tuple[str, ...] = (
    "captcha", "challenge", "turnstile", "verify", "recaptcha",
    "hcaptcha", "geetest", "gee", "slider", "turing",
)

# 疑似动态参数名（用于判定"静态 vs 动态参数"维度）
DYNAMIC_PARAM_TOKENS: tuple[str, ...] = (
    "ts", "timestamp", "_ts", "_t", "nonce", "sign", "token",
    "csrf", "xsrf", "request_id", "trace_id", "session_id",
    "sid", "uuid", "guid", "rnd", "rand", "cb", "cache_bust",
)

# 公开业务方法签名禁止作为必填参数的关键字（v2.17.0 零前置参数）
FORBIDDEN_PUBLIC_PARAMS: set[str] = {
    "token", "cookie", "sign", "nonce", "timestamp", "challenge",
    "csrf", "xsrf", "session_id", "captcha",
}

# v2.17.0 业务字段名集合（同 BUSINESS_FIELD_NAMES，保持兼容导出）
VALID_LIFECYCLE_LOCATIONS: tuple[str, ...] = ("header", "query", "body", "cookie")


# ----------------------------------------------------------------------------
# 异常
# ----------------------------------------------------------------------------

class ArtifactsGenerationError(RuntimeError):
    """会话派生产物无法生成时抛出的统一异常。"""


# ----------------------------------------------------------------------------
# 数据结构
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class EndpointKey:
    """接口归一化键：method + normalized_url。"""

    method: str
    normalized_url: str


@dataclass
class HarExchange:
    """单条请求/响应配对的轻量视图。"""

    request_index: int | None
    response_index: int | None
    timestamp: str
    method: str  # "UNKNOWN" 表示无法推断
    url: str
    request_headers: dict[str, str] = field(default_factory=dict)
    request_body: Any = None
    status: int | None = None
    response_headers: dict[str, str] = field(default_factory=dict)
    body_preview: str | None = None
    body_size: int = 0
    parsed_body: Any = None
    linked_steps: list[int] = field(default_factory=list)
    linked_action_types: list[str] = field(default_factory=list)

    @property
    def key(self) -> EndpointKey:
        return EndpointKey(method=self.method or "UNKNOWN", normalized_url=normalize_url(self.url))


@dataclass
class LifecycleField:
    """请求/响应中的动态字段，附 lifecycle 分类线索。"""

    name: str
    location: str  # header / query / body / cookie
    category: str  # LIFECYCLE_LABELS 之一
    evidence: str
    redacted: bool
    confidence: float


@dataclass
class EndpointCandidate:
    """聚合后的接口候选，喂给六维评分与 top10 排序。"""

    key: EndpointKey
    occurrences: int = 0
    status_200_count: int = 0
    trigger_steps: list[int] = field(default_factory=list)
    trigger_actions: list[str] = field(default_factory=list)
    business_fields: list[str] = field(default_factory=list)
    anti_bot_features: list[str] = field(default_factory=list)
    dynamic_parameters: list[str] = field(default_factory=list)
    static_parameters: list[str] = field(default_factory=list)
    lifecycle_fields: list[LifecycleField] = field(default_factory=list)
    exchanges: list[HarExchange] = field(default_factory=list)
    largest_sample: HarExchange | None = None
    score_breakdown: dict[str, int] = field(default_factory=dict)
    total_score: int = 0
    confidence: str = "low"  # high / medium / low / noise


# ----------------------------------------------------------------------------
# URL 归一化与高频过滤
# ----------------------------------------------------------------------------

def normalize_url(url: str) -> str:
    """把 URL 归一化为 method-key。

    规则：scheme + host（小写）+ path；query 参数按参数名排序；动态值替换为
    `{dynamic}`；删除 fragment。
    """

    if not url:
        return ""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or "/"
    # query 解析 + 按 key 排序 + 动态值替换
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    normalized_pairs: list[tuple[str, str]] = []
    for key, value in pairs:
        key_lower = key.lower()
        if key_lower in DYNAMIC_PARAM_TOKENS or _looks_like_dynamic_value(value):
            normalized_pairs.append((key, "{dynamic}"))
        else:
            normalized_pairs.append((key, value))
    normalized_pairs.sort(key=lambda item: item[0])
    query = urlencode(normalized_pairs)
    return urlunparse((parsed.scheme or "https", host, path, "", query, ""))


def _looks_like_dynamic_value(value: str) -> bool:
    """启发式判定单值是否像时间戳 / UUID / 长 token。"""

    if not value:
        return False
    if len(value) >= 16 and re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return True
    if re.fullmatch(r"\d{10,}", value):
        return True
    if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value, re.IGNORECASE):
        return True
    return False


def is_static_or_noise(url: str) -> bool:
    """判断 URL 是否属于静态资源 / 埋点 / 心跳 / 健康检查。"""

    if not url:
        return False
    parsed = urlparse(url)
    path_lower = (parsed.path or "").lower()
    if any(path_lower.endswith(suffix) for suffix in STATIC_SUFFIXES):
        return True
    if any(token in path_lower for token in NOISE_PATH_TOKENS):
        return True
    if parsed.scheme in {"data", "blob"}:
        return True
    return False


# ----------------------------------------------------------------------------
# HAR 与步骤证据读取
# ----------------------------------------------------------------------------

def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """读取 JSONL，跳过损坏行。"""

    entries: list[dict[str, Any]] = []
    if not path.exists():
        return entries
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            entries.append(value)
    return entries


def _read_json(path: Path, default: Any = None) -> Any:
    """读取 JSON 文件，缺失 / 损坏时返回 default。"""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _parse_body_preview(body_preview: str | None) -> tuple[Any, str]:
    """解析 body_preview，返回 (parsed_body_or_None, parse_status)。"""

    if not body_preview:
        return None, "missing"
    text = body_preview.strip()
    if not text:
        return None, "missing"
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
            return parsed, "parsed"
        except json.JSONDecodeError:
            return text[:1024], "preview-only"
    return text[:1024], "preview-only"


def _load_har_entries(session_dir: Path) -> list[HarExchange]:
    """加载 HAR JSONL 并按 FIFO 配对 request/response，构造 HarExchange 列表。"""

    raw_entries = _read_jsonl(session_dir / "user-session.har.jsonl")
    pending: dict[str, list[dict[str, Any]]] = defaultdict(list)
    exchanges: list[HarExchange] = []
    next_index = 0

    # 第一遍：按时间顺序累积
    for entry in raw_entries:
        kind = entry.get("kind")
        url = entry.get("url") or ""
        ts = entry.get("ts") or ""
        if kind == "request":
            exchange = HarExchange(
                request_index=next_index,
                response_index=None,
                timestamp=ts,
                method=str(entry.get("method") or "UNKNOWN").upper(),
                url=url,
                request_headers=dict(entry.get("headers") or {}),
                request_body=entry.get("post_data"),
                status=None,
                response_headers={},
                body_preview=None,
                body_size=0,
                parsed_body=None,
            )
            exchanges.append(exchange)
            next_index += 1
            pending[normalize_url(url)].append(exchange)
        elif kind == "response":
            url_key = normalize_url(url)
            matched_request = None
            if pending.get(url_key):
                matched_request = pending[url_key].pop(0)
            body_preview = entry.get("body_preview")
            parsed_body, parse_status = _parse_body_preview(body_preview)
            body_size = len(body_preview.encode("utf-8")) if body_preview else 0
            if matched_request is not None:
                matched_request.response_index = next_index
                matched_request.status = entry.get("status")
                matched_request.response_headers = dict(entry.get("headers") or {})
                matched_request.body_preview = body_preview
                matched_request.body_size = body_size
                matched_request.parsed_body = parsed_body if parse_status == "parsed" else None
                next_index += 1
            else:
                # response 没有配对的 request
                exchange = HarExchange(
                    request_index=None,
                    response_index=next_index,
                    timestamp=ts,
                    method="UNKNOWN",  # 后续由步骤证据补齐
                    url=url,
                    status=entry.get("status"),
                    response_headers=dict(entry.get("headers") or {}),
                    body_preview=body_preview,
                    body_size=body_size,
                    parsed_body=parsed_body if parse_status == "parsed" else None,
                )
                exchanges.append(exchange)
                next_index += 1
    return exchanges


def _load_step_evidence(session_dir: Path) -> list[dict[str, Any]]:
    """读取步骤证据索引。"""

    doc = _read_json(session_dir / "步骤证据索引.json", default={})
    if not isinstance(doc, dict):
        return []
    steps = doc.get("steps", [])
    return steps if isinstance(steps, list) else []


def _link_steps_to_exchanges(
    exchanges: list[HarExchange],
    steps: list[dict[str, Any]],
) -> None:
    """按 normalized_url 把步骤关联到 exchange。"""

    # 收集 step 网络事件（normalized_url → set of (step_index, action_type)）
    step_links: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for step_idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        action = step.get("action") or {}
        action_type = action.get("type") if isinstance(action, dict) else ""
        for entry in step.get("network") or []:
            url = entry.get("url") or ""
            if not url:
                continue
            step_links[normalize_url(url)].append((step_idx, action_type))

    for ex in exchanges:
        if is_static_or_noise(ex.url):
            continue
        url_key = normalize_url(ex.url)
        for step_idx, action_type in step_links.get(url_key, []):
            ex.linked_steps.append(step_idx)
            if action_type and action_type not in ex.linked_action_types:
                ex.linked_action_types.append(action_type)


def _backfill_method_from_steps(
    exchanges: list[HarExchange],
    steps: list[dict[str, Any]],
) -> None:
    """response 缺 method 时从步骤证据索引的 network.method 补齐。"""

    method_map: dict[str, str] = {}
    for step in steps:
        if not isinstance(step, dict):
            continue
        for entry in step.get("network") or []:
            url = entry.get("url") or ""
            method = entry.get("method")
            if url and method and url not in method_map:
                method_map[normalize_url(url)] = str(method).upper()

    for ex in exchanges:
        if ex.method == "UNKNOWN" or not ex.method:
            candidate = method_map.get(normalize_url(ex.url))
            if candidate:
                ex.method = candidate
            elif ex.request_headers or ex.request_body is not None:
                # 若 exchange 是从 request 配对而来但没显式 method，保留 UNKNOWN
                pass


# ----------------------------------------------------------------------------
# 候选聚合
# ----------------------------------------------------------------------------

def _aggregate_candidates(
    exchanges: list[HarExchange],
) -> dict[EndpointKey, EndpointCandidate]:
    """按 EndpointKey 聚合 exchange 列表。"""

    candidates: dict[EndpointKey, EndpointCandidate] = {}
    for ex in exchanges:
        if is_static_or_noise(ex.url):
            continue
        key = ex.key
        if key not in candidates:
            candidates[key] = EndpointCandidate(key=key)
        cand = candidates[key]
        cand.occurrences += 1
        if ex.status == 200:
            cand.status_200_count += 1
        for step_idx in ex.linked_steps:
            if step_idx not in cand.trigger_steps:
                cand.trigger_steps.append(step_idx)
        for action_type in ex.linked_action_types:
            if action_type and action_type not in cand.trigger_actions:
                cand.trigger_actions.append(action_type)
        cand.exchanges.append(ex)
    return candidates


def _extract_business_fields(cand: EndpointCandidate) -> None:
    """从 exchange.parsed_body 提取业务字段名。"""

    seen: set[str] = set()
    for ex in cand.exchanges:
        if not isinstance(ex.parsed_body, (dict, list)):
            continue
        _walk_keys(ex.parsed_body, BUSINESS_FIELD_NAMES, seen, depth=0, max_depth=4)
    cand.business_fields = sorted(seen)


def _walk_keys(
    node: Any,
    targets: tuple[str, ...],
    seen: set[str],
    depth: int,
    max_depth: int,
    keys_seen: set[int] | None = None,
) -> None:
    """递归收集匹配 targets 的字段名，受深度与 key 总数限制。"""

    if keys_seen is None:
        keys_seen = set()
    if depth > max_depth or len(keys_seen) > 200:
        return
    if isinstance(node, dict):
        for key, value in node.items():
            if id(key) in keys_seen:
                continue
            keys_seen.add(id(key))
            if isinstance(key, str) and key.lower() in targets and key.lower() not in seen:
                seen.add(key.lower())
            _walk_keys(value, targets, seen, depth + 1, max_depth, keys_seen)
    elif isinstance(node, list):
        for item in node[:50]:
            _walk_keys(item, targets, seen, depth + 1, max_depth, keys_seen)


def _extract_anti_bot_features(cand: EndpointCandidate) -> None:
    """从 URL / body 中提取反爬关键字。"""

    seen: set[str] = set()
    url_lower = cand.key.normalized_url.lower()
    for token in ANTI_BOT_TOKENS:
        if token in url_lower:
            seen.add(token)
    for ex in cand.exchanges:
        if isinstance(ex.parsed_body, dict):
            for key in ex.parsed_body.keys():
                if isinstance(key, str):
                    key_lower = key.lower()
                    for token in ANTI_BOT_TOKENS:
                        if token in key_lower and token not in seen:
                            seen.add(token)
    cand.anti_bot_features = sorted(seen)


def _extract_parameter_classes(cand: EndpointCandidate) -> None:
    """把 query 参数归类为动态 / 静态。"""

    parsed = urlparse(cand.key.normalized_url)
    dynamic: set[str] = set()
    static: set[str] = set()
    for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "{dynamic}":
            continue
        if key.lower() in DYNAMIC_PARAM_TOKENS:
            dynamic.add(key)
        else:
            static.add(key)
    cand.dynamic_parameters = sorted(dynamic)
    cand.static_parameters = sorted(static)


def _classify_lifecycle(cand: EndpointCandidate) -> None:
    """根据 headers / body / query 中字段名归类 lifecycle 字段。"""

    seen_fields: set[str] = set()
    lifecycle: list[LifecycleField] = []
    for ex in cand.exchanges:
        for header_name in ex.request_headers.keys():
            field_name = header_name.lower()
            if field_name in seen_fields:
                continue
            category = _classify_field(field_name, "header")
            if category:
                seen_fields.add(field_name)
                lifecycle.append(
                    LifecycleField(
                        name=field_name,
                        location="header",
                        category=category,
                        evidence=f"出现于请求 Header",
                        redacted=True,
                        confidence=0.6,
                    )
                )
        if isinstance(ex.parsed_body, dict):
            for key in ex.parsed_body.keys():
                if not isinstance(key, str):
                    continue
                field_name = key.lower()
                if field_name in seen_fields:
                    continue
                category = _classify_field(field_name, "body")
                if category:
                    seen_fields.add(field_name)
                    lifecycle.append(
                        LifecycleField(
                            name=field_name,
                            location="body",
                            category=category,
                            evidence=f"出现于请求 Body",
                            redacted=True,
                            confidence=0.6,
                        )
                    )
        for key in ex.request_body if isinstance(ex.request_body, dict) else []:
            field_name = str(key).lower()
            if field_name in seen_fields:
                continue
            category = _classify_field(field_name, "body")
            if category:
                seen_fields.add(field_name)
                lifecycle.append(
                    LifecycleField(
                        name=field_name,
                        location="body",
                        category=category,
                        evidence=f"出现于表单 Body",
                        redacted=True,
                        confidence=0.5,
                    )
                )
        for query_key in parse_qsl(urlparse(ex.url).query, keep_blank_values=True):
            field_name = query_key[0].lower()
            if field_name in seen_fields or field_name == "{dynamic}":
                continue
            category = _classify_field(field_name, "query")
            if category:
                seen_fields.add(field_name)
                lifecycle.append(
                    LifecycleField(
                        name=field_name,
                        location="query",
                        category=category,
                        evidence=f"出现于 query 参数",
                        redacted=True,
                        confidence=0.5,
                    )
                )
    cand.lifecycle_fields = lifecycle


def _classify_field(field_name: str, location: str) -> str | None:
    """把字段名映射到 lifecycle 类别。"""

    field_lower = field_name.lower()
    if field_lower in ("authorization", "cookie", "set-cookie", "x-csrf-token", "csrf-token",
                       "x-xsrf-token", "x-auth-token", "x-token", "session", "sessionid"):
        return "session-bound"
    if field_lower in ("nonce", "request_id", "requestid", "trace_id", "traceid"):
        return "per-request"
    if field_lower in ("timestamp", "ts", "_ts", "time", "expires", "ttl", "expire_at"):
        return "time-bound"
    if field_lower in ("captcha", "captcha_token", "challenge", "turnstile", "verify_token",
                       "recaptcha", "hcaptcha", "geetest", "gee", "slider", "turing"):
        return "challenge-bound"
    if field_lower in ("sign", "signature", "x-sign", "x-signature"):
        return "per-request"
    if field_lower in ("token", "access_token", "refresh_token"):
        return "single-use-token"
    if location == "header" and field_lower in ("user-agent", "accept-language", "x-platform"):
        return "reusable"
    return None


def _pick_largest_sample(cand: EndpointCandidate) -> None:
    """从 exchanges 选最大且优先解析的 body preview。"""

    candidates_pool = [ex for ex in cand.exchanges if ex.body_preview]
    if not candidates_pool:
        cand.largest_sample = None
        return

    def _rank(ex: HarExchange) -> tuple[int, int, int]:
        is_parsed = 1 if isinstance(ex.parsed_body, (dict, list)) else 0
        size = ex.body_size
        status_priority = 1 if ex.status == 200 else 0
        return (is_parsed, size, status_priority)

    candidates_pool.sort(key=_rank, reverse=True)
    cand.largest_sample = candidates_pool[0]


# ----------------------------------------------------------------------------
# 六维评分
# ----------------------------------------------------------------------------

SCORE_DIMENSIONS: tuple[tuple[str, int], ...] = (
    ("响应码 200", 20),
    ("操作触发", 25),
    ("业务 JSON 字段", 20),
    ("反爬特征", 10),
    ("静态 vs 动态参数", 15),
    ("重复次数", 10),
)


def score_candidate(cand: EndpointCandidate) -> None:
    """对单个候选做六维评分。"""

    breakdown: dict[str, int] = {}

    # 维度 1：响应码 200
    if cand.occurrences > 0 and cand.status_200_count == cand.occurrences:
        breakdown["响应码 200"] = 20
    elif cand.status_200_count > 0:
        breakdown["响应码 200"] = 15
    elif any((ex.status or 0) >= 200 and (ex.status or 0) < 300 for ex in cand.exchanges):
        breakdown["响应码 200"] = 10
    else:
        breakdown["响应码 200"] = 0

    # 维度 2：操作触发
    unique_steps = len(set(cand.trigger_steps))
    breakdown["操作触发"] = min(20, unique_steps * 5)
    if cand.trigger_actions and any(a in cand.trigger_actions for a in ("click", "fill", "press", "submit", "goto")):
        breakdown["操作触发"] = min(25, breakdown["操作触发"] + 5)

    # 维度 3：业务 JSON 字段
    breakdown["业务 JSON 字段"] = min(20, len(set(cand.business_fields)) * 4)

    # 维度 4：反爬特征（高分 = 无反爬；含 challenge 关键字则降分）
    if not cand.anti_bot_features:
        breakdown["反爬特征"] = 10
    elif any(t in cand.anti_bot_features for t in ("captcha", "challenge", "turnstile", "geetest", "gee")):
        breakdown["反爬特征"] = 0
    else:
        breakdown["反爬特征"] = 4

    # 维度 5：静态 vs 动态参数
    if cand.dynamic_parameters and cand.static_parameters:
        breakdown["静态 vs 动态参数"] = 13
    elif cand.dynamic_parameters and not cand.static_parameters:
        breakdown["静态 vs 动态参数"] = 10
    elif cand.static_parameters and not cand.dynamic_parameters:
        breakdown["静态 vs 动态参数"] = 5
    else:
        breakdown["静态 vs 动态参数"] = 0

    # 维度 6：重复次数
    if cand.occurrences >= 5:
        breakdown["重复次数"] = 10
    elif cand.occurrences == 3:
        breakdown["重复次数"] = 7
    elif cand.occurrences == 2:
        breakdown["重复次数"] = 5
    else:
        breakdown["重复次数"] = 2

    cand.score_breakdown = breakdown
    cand.total_score = sum(breakdown.values())

    # 置信度
    if cand.trigger_steps and cand.status_200_count > 0 and not cand.anti_bot_features:
        cand.confidence = "high"
    elif cand.trigger_steps:
        cand.confidence = "medium"
    elif cand.status_200_count > 0:
        cand.confidence = "low"
    else:
        cand.confidence = "noise"


def rank_candidates(candidates: dict[EndpointKey, EndpointCandidate]) -> list[EndpointCandidate]:
    """5 层稳定排序，返回前 10。"""

    for cand in candidates.values():
        score_candidate(cand)
    sorted_candidates = sorted(
        candidates.values(),
        key=lambda c: (
            -c.total_score,
            -len(c.trigger_steps),
            -c.status_200_count,
            -c.occurrences,
            c.key.method,
            c.key.normalized_url,
        ),
    )
    return [c for c in sorted_candidates if c.confidence != "noise"][:10]


# ----------------------------------------------------------------------------
# 报告与样本生成
# ----------------------------------------------------------------------------

def _escape_md(text: str) -> str:
    """把文本中的管道符与换行转义为 Markdown 表格安全形式。"""

    if text is None:
        return ""
    text = str(text).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    return text[:200]


def render_candidate_report(
    ranked: list[EndpointCandidate],
    workspace: Path,
    session_id: str,
    warnings: list[str],
) -> str:
    """渲染 Markdown 候选报告（top10 + 六维得分明细）。"""

    lines: list[str] = []
    lines.append(f"# 目标接口候选（top {len(ranked)}）")
    lines.append("")
    lines.append(f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}")
    lines.append(f"- 工作区：`{workspace}`")
    lines.append(f"- 会话 ID：`{session_id}`")
    lines.append("- 评分维度（满分 100）：响应码 200（20）+ 操作触发（25）+ 业务 JSON 字段（20）+ 反爬特征（10）+ 静态 vs 动态参数（15）+ 重复次数（10）")
    lines.append("")
    if not ranked:
        lines.append("> 未找到满足条件的业务候选。请检查：录制期间是否触发业务接口、HAR 是否包含目标域。")
        lines.append("")
    else:
        lines.append("| 排名 | 总分 | Method | URL | 200/总数 | 操作步骤 | 关键业务字段 | 动态参数 | 置信度 | 反爬特征 |")
        lines.append("|---:|---:|:---|:---|:---|:---|:---|:---|:---|:---|")
        for idx, cand in enumerate(ranked, start=1):
            url = _escape_md(cand.key.normalized_url)
            business_fields = "**, **".join(sorted(set(cand.business_fields))) if cand.business_fields else "—"
            business_fields = f"**{business_fields}**"
            dynamic_params = "**, **".join(cand.dynamic_parameters) if cand.dynamic_parameters else "—"
            dynamic_params = f"**{dynamic_params}**"
            actions = ", ".join(cand.trigger_actions[:3]) if cand.trigger_actions else "—"
            actions = _escape_md(actions)
            anti_bot = ", ".join(cand.anti_bot_features) if cand.anti_bot_features else "—"
            lines.append(
                f"| {idx} | {cand.total_score} | {cand.key.method} | {url} | "
                f"{cand.status_200_count}/{cand.occurrences} | {actions} | {business_fields} | "
                f"{dynamic_params} | {cand.confidence} | {anti_bot} |"
            )

        lines.append("")
        lines.append("## 六维评分明细")
        lines.append("")
        lines.append("| 排名 | 响应码 200 | 操作触发 | 业务 JSON 字段 | 反爬特征 | 静态 vs 动态参数 | 重复次数 | 总分 |")
        lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
        for idx, cand in enumerate(ranked, start=1):
            lines.append(
                f"| {idx} | {cand.score_breakdown.get('响应码 200', 0)} | "
                f"{cand.score_breakdown.get('操作触发', 0)} | "
                f"{cand.score_breakdown.get('业务 JSON 字段', 0)} | "
                f"{cand.score_breakdown.get('反爬特征', 0)} | "
                f"{cand.score_breakdown.get('静态 vs 动态参数', 0)} | "
                f"{cand.score_breakdown.get('重复次数', 0)} | "
                f"{cand.total_score} |"
            )

        lines.append("")
        lines.append("## lifecycle 分类")
        lines.append("")
        for idx, cand in enumerate(ranked, start=1):
            if not cand.lifecycle_fields:
                continue
            lifecycle_str = ", ".join(
                f"**{lf.category}**: `{lf.name}`" for lf in cand.lifecycle_fields[:5]
            )
            lines.append(f"- #{idx} `{cand.key.method} {cand.key.normalized_url}`：{lifecycle_str}")

    if warnings:
        lines.append("")
        lines.append("## 警告")
        for w in warnings:
            lines.append(f"- {w}")

    lines.append("")
    lines.append("> 注：本报告由 `session-artifacts-generator.py` 自动生成，候选为分析起点，不是已验证接口（`[🎯]`）或可交付模块（`PASS`）。")
    lines.append("")
    return "\n".join(lines)


def write_atomically(path: Path, content: str) -> None:
    """原子写入文件：临时文件 + os.replace。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(content, encoding="utf-8")
    os.replace(temporary_path, path)


def render_response_sample(
    cand: EndpointCandidate,
    rank: int,
    session_id: str,
) -> dict[str, Any]:
    """渲染单个接口的最大响应样本 envelope。"""

    sample = cand.largest_sample
    if sample is None:
        return {
            "endpoint": {"method": cand.key.method, "url": cand.key.normalized_url},
            "status": None,
            "captured_at": sample.timestamp if sample else "",
            "body_size": 0,
            "body_truncated": True,
            "parse_status": "missing",
            "parsed_body": None,
            "body_preview": None,
            "source_session": session_id,
            "note": "样本来自已脱敏 HAR body_preview，不代表完整响应体；当前无可用样本",
        }

    parsed = sample.parsed_body if isinstance(sample.parsed_body, (dict, list)) else None
    preview_text = sample.body_preview if not parsed else None
    return {
        "endpoint": {"method": cand.key.method, "url": cand.key.normalized_url},
        "status": sample.status,
        "captured_at": sample.timestamp,
        "body_size": sample.body_size,
        "body_truncated": sample.body_size >= 1024,
        "parse_status": "parsed" if parsed is not None else ("preview-only" if preview_text else "missing"),
        "parsed_body": parsed,
        "body_preview": preview_text,
        "source_session": session_id,
        "note": "样本来自已脱敏 HAR body_preview，不代表完整响应体；HAR 当前仅保存前 1024 字符预览",
    }


def _sanitize_filename_part(text: str) -> str:
    """清洗文件名字段为小写字母 / 数字 / 连字符，最长 ~100 字符。"""

    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return cleaned[:80] or "endpoint"


def render_sample_filename(rank: int, cand: EndpointCandidate) -> str:
    """生成响应样本文件名：`{rank:02d}-{method}-{path}-{hash8}.json`。"""

    parsed = urlparse(cand.key.normalized_url)
    path_part = _sanitize_filename_part(parsed.path.strip("/") or "root")
    method_part = cand.key.method.lower().replace("unknown", "unk")
    endpoint_hash = hashlib.sha256(f"{cand.key.method}|{cand.key.normalized_url}".encode("utf-8")).hexdigest()[:8]
    return f"{rank:02d}-{method_part}-{path_part}-{endpoint_hash}.json"


def write_response_samples(
    ranked: list[EndpointCandidate],
    workspace: Path,
    session_id: str,
    warnings: list[str],
) -> list[str]:
    """为每个 top10 候选写一个响应样本 envelope。"""

    sample_dir = workspace / "02-接口分析" / "响应样本"
    sample_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[str] = []
    for idx, cand in enumerate(ranked, start=1):
        envelope = render_response_sample(cand, idx, session_id)
        filename = render_sample_filename(idx, cand)
        path = sample_dir / filename
        write_atomically(path, json.dumps(envelope, ensure_ascii=False, indent=2))
        written_paths.append(str(path))
        if envelope["parse_status"] == "preview-only":
            warnings.append(f"样本 #{idx} `{cand.key.normalized_url}` 解析失败，仅保留预览字符串")
    return written_paths


# ----------------------------------------------------------------------------
# 模块封装种子（client.py / quick_test.py）
# ----------------------------------------------------------------------------

def _derive_module_name(ranked: list[EndpointCandidate], workspace: Path) -> str:
    """推导模块目录名。"""

    if ranked:
        first = ranked[0]
        parsed = urlparse(first.key.normalized_url)
        segments = [seg for seg in (parsed.path or "").split("/") if seg]
        if segments:
            candidate = segments[0]
        else:
            candidate = ""
    else:
        candidate = ""

    if not candidate:
        candidate = workspace.name.replace("-crawler-reverse", "")

    candidate = re.sub(r"[^a-z0-9_]+", "_", candidate.lower()).strip("_")
    if not candidate or not re.match(r"^[a-z_]", candidate):
        candidate = "generated_module"
    return candidate


def _class_to_pascal_case(name: str) -> str:
    """snake_case → PascalCase。"""

    parts = [p for p in re.split(r"[^a-zA-Z0-9]+", name) if p]
    if not parts:
        return "GeneratedClient"
    return "".join(part[:1].upper() + part[1:] for part in parts) + "Client"


def _method_name_from_url(url: str) -> str:
    """从 URL 推导业务方法名（snake_case）。"""

    parsed = urlparse(url)
    segments = [seg for seg in re.split(r"[^a-zA-Z0-9]+", parsed.path or "") if seg]
    if not segments:
        return "call_endpoint"
    name = "_".join(seg.lower() for seg in segments[-3:])
    return name or "call_endpoint"


def _extract_business_params(cand: EndpointCandidate) -> list[str]:
    """从 URL 与 body 抽取可作为业务方法参数的字段（剔除 lifecycle 敏感字段）。"""

    params: list[str] = []
    parsed = urlparse(cand.key.normalized_url)
    for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "{dynamic}":
            continue
        if key.lower() in FORBIDDEN_PUBLIC_PARAMS:
            continue
        if key.lower() in DYNAMIC_PARAM_TOKENS:
            continue
        params.append(key)
    for ex in cand.exchanges:
        if isinstance(ex.parsed_body, dict):
            for key in ex.parsed_body.keys():
                if not isinstance(key, str):
                    continue
                if key.lower() in FORBIDDEN_PUBLIC_PARAMS:
                    continue
                if key.lower() in DYNAMIC_PARAM_TOKENS:
                    continue
                if key not in params:
                    params.append(key)
    return params[:8]


def render_client_module(
    module_name: str,
    client_class: str,
    ranked: list[EndpointCandidate],
    warnings: list[str],
) -> str:
    """渲染 v2.17.0 类式 client.py 种子。"""

    lines: list[str] = []
    lines.append(f'"""\n{module_name}/client.py — v2.21.0 自动生成的类式封装种子（v2.17.0 约定）')
    lines.append("")
    lines.append("本文件由 `session-artifacts-generator.py` 自动生成，是分析起点不是已验证接口。")
    lines.append("所有 token / cookie / sign / nonce / timestamp / challenge / csrf / xsrf / session_id / captcha")
    lines.append("均归入 6 类 lifecycle 分类（reusable / per-request / single-use-token / session-bound /")
    lines.append("time-bound / challenge-bound），**禁止**写入业务方法必填参数。")
    lines.append("")
    lines.append("阶段 5.5 真实可用性验收（`verify.py` + `验收报告.md`）必须由 AI 主导完成，")
    lines.append("本种子通过 `PASS` 后才能进入阶段 6/7。")
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("import json")
    lines.append("import urllib.error")
    lines.append("import urllib.request")
    lines.append("from typing import Any")
    lines.append("")
    lines.append("")
    lines.append(f"class {client_class}:")
    lines.append("    \"\"\"v2.17.0 类式封装：build_request / do_request / parse_response / request_and_parse 四方法。\"\"\"")
    lines.append("")
    lines.append("    def __init__(self, base_url: str = \"\"):")
    lines.append("        self.base_url = base_url or \"https://example.com\"")
    lines.append("        # TODO（v2.17.0 lifecycle）：下面常量由 AI 在阶段 3 还原后填入真实值，")
    lines.append("        # 当前仅保留字段名与归类，**禁止**写入抓包临时值。")
    lines.append("        self._reusable_headers: dict[str, str] = {}  # reusable：固定 header / locale")
    lines.append("        self._per_request_keys: list[str] = []     # per-request：nonce / sign / request_id")
    lines.append("        self._single_use_tokens: dict[str, str] = {}  # single-use-token：access_token / refresh_token")
    lines.append("        self._session_state: dict[str, str] = {}     # session-bound：cookie / Authorization / session")
    lines.append("        self._time_bound: dict[str, str] = {}        # time-bound：timestamp / expires / ttl")
    lines.append("        self._challenge_bound: list[str] = []        # challenge-bound：captcha / challenge / verify")
    lines.append("")
    lines.append("    def _build_lifecycle_context(self) -> dict[str, Any]:")
    lines.append("        \"\"\"内部生命周期上下文构造器：仅返回字段名线索，不返回真实抓包值。\"\"\"")
    lines.append("        # TODO：AI 在阶段 3 还原后实现每个分类的获取 / 刷新逻辑")
    lines.append("        return {")
    lines.append("            \"reusable\": self._reusable_headers,")
    lines.append("            \"per_request_keys\": self._per_request_keys,")
    lines.append("            \"single_use_tokens\": self._single_use_tokens,")
    lines.append("            \"session_state\": self._session_state,")
    lines.append("            \"time_bound\": self._time_bound,")
    lines.append("            \"challenge_bound\": self._challenge_bound,")
    lines.append("        }")
    lines.append("")
    lines.append("    def build_request(self, action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:")
    lines.append("        \"\"\"构造请求：仅返回请求描述（URL / method / headers / body），不发送。\"\"\"")
    lines.append("        # TODO：AI 阶段 3 接入真实 endpoint 表与 lifecycle 注入")
    lines.append("        return {\"action\": action, \"params\": params or {}, \"context\": self._build_lifecycle_context()}")
    lines.append("")
    lines.append("    def do_request(self, request: dict[str, Any]) -> dict[str, Any]:")
    lines.append("        \"\"\"执行请求：仅返回原始响应体（脱敏 preview），不解析业务字段。\"\"\"")
    lines.append("        # TODO：AI 阶段 3 接入真实 transport（默认 urllib.request）")
    lines.append("        url = self.base_url")
    lines.append("        try:")
    lines.append("            with urllib.request.urlopen(url) as response:")
    lines.append("                body = response.read().decode(\"utf-8\", errors=\"replace\")[:1024]")
    lines.append("                return {\"status\": response.status, \"body\": body, \"preview\": True}")
    lines.append("        except urllib.error.URLError as exc:")
    lines.append("            return {\"status\": None, \"error\": str(exc), \"preview\": True}")
    lines.append("")
    lines.append("    def parse_response(self, response: dict[str, Any]) -> dict[str, Any]:")
    lines.append("        \"\"\"解析响应：仅提取业务字段，不做 transport 操作。\"\"\"")
    lines.append("        if not isinstance(response, dict):")
    lines.append("            return {}")
    lines.append("        body = response.get(\"body\")")
    lines.append("        if not body:")
    lines.append("            return {}")
    lines.append("        try:")
    lines.append("            return json.loads(body)")
    lines.append("        except json.JSONDecodeError:")
    lines.append("            return {\"raw\": body}")
    lines.append("")
    lines.append("    def request_and_parse(self, action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:")
    lines.append("        \"\"\"串联 build_request + do_request + parse_response 三个职责。\"\"\"")
    lines.append("        request = self.build_request(action, params)")
    lines.append("        response = self.do_request(request)")
    lines.append("        parsed = self.parse_response(response)")
    lines.append("        return {\"request\": request, \"response\": response, \"parsed\": parsed}")
    lines.append("")

    # 业务方法（high-trigger 候选 only）
    business_count = 0
    for cand in ranked:
        if cand.confidence != "high":
            continue
        # challenge-only 候选不生成普通业务方法
        if any(t in cand.anti_bot_features for t in ("captcha", "challenge", "turnstile", "geetest", "gee")):
            warnings.append(f"候选 `{cand.key.method} {cand.key.normalized_url}` 含 challenge 字段，跳过普通业务方法生成")
            continue
        business_count += 1
        method_name = _method_name_from_url(cand.key.normalized_url)
        params = _extract_business_params(cand)
        param_str = ", ".join(f"{p}: Any = None" for p in params) or ""
        param_str_self = f"self, {param_str}" if param_str else "self"
        lines.append(f"    def {method_name}({param_str_self}) -> Any:")
        lines.append(f"        \"\"\"调用候选接口：`{cand.key.method} {cand.key.normalized_url}`。")
        if cand.lifecycle_fields:
            lifecycle_note = "; ".join(f"{lf.category}: `{lf.name}`" for lf in cand.lifecycle_fields[:5])
            lines.append(f"        lifecycle 字段：{lifecycle_note}")
        lines.append("        \"\"\"")

        if params:
            build_params = "{**" + ", ".join(f"\"{p}\": {p}" for p in params) + "}"
        else:
            build_params = "{}"
        lines.append(f"        return self.request_and_parse(\"{method_name}\", {build_params})")
        lines.append("")

    if business_count == 0:
        lines.append("    # TODO：本会话未识别 high-trigger 业务候选，请在阶段 3 手工补充业务方法")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def render_quick_test(module_name: str, client_class: str) -> str:
    """渲染 quick_test.py 三类用法（v2.17.0）。"""

    return f'''"""
{module_name}/quick_test.py — v2.21.0 自动生成的手动验证入口（v2.17.0 三类用法）

本文件由 `session-artifacts-generator.py` 自动生成，是分析起点不是已验证接口。
演示三类典型用法：
1. 业务要数据：`request_and_parse`
2. 业务只要报文：`build_request`
3. 业务要原始响应：`do_request`

阶段 5.5 真实可用性验收（`verify.py` + `验收报告.md`）必须由 AI 主导完成，
本快速验证入口仅用于手工触发 smoke test。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from client import {client_class}  # noqa: E402


def _demo_three_usages() -> None:
    client = {client_class}()

    # 用法 1：业务要数据 —— request_and_parse
    print("[用法 1] request_and_parse")
    print("业务参数示例（请替换为真实业务参数）：")
    try:
        result = client.request_and_parse("placeholder_action", {{}})
        print(f"  → status={{result.get('response', {{}}).get('status')}}")
    except Exception as exc:  # noqa: BLE001
        print(f"  → 占位调用失败（正常，因为 endpoint 表未填）：{{type(exc).__name__}}: {{exc}}")

    # 用法 2：业务只要报文 —— build_request
    print("[用法 2] build_request")
    request = client.build_request("placeholder_action", {{}})
    print(f"  → 请求描述：{{request}}")

    # 用法 3：业务要原始响应 —— do_request
    print("[用法 3] do_request")
    response = client.do_request(request)
    print(f"  → 响应预览：{{response}}")


if __name__ == "__main__":
    _demo_three_usages()
'''


def write_module_seeds(
    workspace: Path,
    module_name: str,
    ranked: list[EndpointCandidate],
    warnings: list[str],
) -> tuple[Path, Path, list[str], list[str]]:
    """写 04-模块封装/{module}/client.py + quick_test.py；返回 (client_path, quick_test_path, created, preserved)。"""

    module_dir = workspace / "04-模块封装" / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    client_path = module_dir / "client.py"
    quick_test_path = module_dir / "quick_test.py"
    client_class = _class_to_pascal_case(module_name)
    created: list[str] = []
    preserved: list[str] = []

    if not client_path.exists():
        client_text = render_client_module(module_name, client_class, ranked, warnings)
        write_atomically(client_path, client_text)
        created.append(str(client_path))
    else:
        preserved.append(str(client_path))
        warnings.append(f"`client.py` 已存在（人工文件），保留不覆盖：{client_path}")

    if not quick_test_path.exists():
        quick_test_text = render_quick_test(module_name, client_class)
        write_atomically(quick_test_path, quick_test_text)
        created.append(str(quick_test_path))
    else:
        preserved.append(str(quick_test_path))
        warnings.append(f"`quick_test.py` 已存在（人工文件），保留不覆盖：{quick_test_path}")

    return client_path, quick_test_path, created, preserved


# ----------------------------------------------------------------------------
# 主入口
# ----------------------------------------------------------------------------

def _validate_inputs(workspace: Path, session_dir: Path) -> None:
    """输入校验：路径绝对化 + session_dir 必须位于 workspace/01-目标画像/录制/ 之下。"""

    workspace_abs = workspace.resolve()
    session_abs = session_dir.resolve()

    if not workspace_abs.is_dir():
        raise ArtifactsGenerationError(f"工作区不存在或不是目录：{workspace_abs}")

    expected_parent = (workspace_abs / "01-目标画像" / "录制").resolve()
    if expected_parent not in session_abs.parents:
        raise ArtifactsGenerationError(
            f"session_dir 越界：必须位于 {expected_parent} 之下，实际={session_abs}"
        )

    if not (session_abs / "步骤证据索引.json").exists():
        raise ArtifactsGenerationError(
            f"步骤证据索引不存在：{session_abs / '步骤证据索引.json'}；web-stop 顺序异常？"
        )


def run_artifacts_generation(
    workspace: str | Path,
    session_dir: str | Path,
) -> dict[str, Any]:
    """基于已停止会话的步骤证据和 HAR 生成接口候选、响应样本与模块封装种子。

    Args:
        workspace: 工作区路径（v2.19.0 init 阶段创建）。
        session_dir: 已停止会话目录（v2.19.0 web-stop 写入）。

    Returns:
        包含 status / module_name / client_path / quick_test_path /
        candidate_report_path / response_sample_paths / created_paths /
        preserved_paths / warnings。
    """

    workspace_path = Path(workspace)
    session_path = Path(session_dir)
    warnings: list[str] = []

    try:
        _validate_inputs(workspace_path, session_path)
    except ArtifactsGenerationError:
        raise

    # 读取证据
    steps = _load_step_evidence(session_path)
    exchanges = _load_har_entries(session_path)
    if not exchanges:
        warnings.append("HAR 没有任何条目，候选报告与样本可能为空")

    _link_steps_to_exchanges(exchanges, steps)
    _backfill_method_from_steps(exchanges, steps)

    # 聚合 + 评分
    candidates = _aggregate_candidates(exchanges)
    for cand in candidates.values():
        _extract_business_fields(cand)
        _extract_anti_bot_features(cand)
        _extract_parameter_classes(cand)
        _classify_lifecycle(cand)
        _pick_largest_sample(cand)
    ranked = rank_candidates(candidates)

    # 渲染产物
    session_id = session_path.name  # 会话-20260729-120000
    report_text = render_candidate_report(ranked, workspace_path, session_id, warnings)
    report_path = workspace_path / "02-接口分析" / "目标接口候选.md"
    write_atomically(report_path, report_text)

    sample_paths = write_response_samples(ranked, workspace_path, session_id, warnings)

    module_name = _derive_module_name(ranked, workspace_path)
    client_path, quick_test_path, created, preserved = write_module_seeds(
        workspace_path,
        module_name,
        ranked,
        warnings,
    )

    status = "generated" if (ranked and not warnings) else ("partial" if ranked else "skipped")
    return {
        "status": status,
        "module_name": module_name,
        "client_path": str(client_path),
        "quick_test_path": str(quick_test_path),
        "candidate_report_path": str(report_path),
        "response_sample_paths": sample_paths,
        "created_paths": created + [str(report_path)] + sample_paths,
        "preserved_paths": preserved,
        "warnings": warnings,
    }


# ----------------------------------------------------------------------------
# CLI（便于单独重跑或人工调试）
# ----------------------------------------------------------------------------

def main() -> int:
    """命令行入口：python session-artifacts-generator.py --workspace ... --session-dir ...。"""

    import argparse

    parser = argparse.ArgumentParser(description="Web 会话派生产物生成器（v2.21.0）")
    parser.add_argument("--workspace", required=True, help="分析工作区路径")
    parser.add_argument("--session-dir", required=True, help="已停止会话目录")
    args = parser.parse_args()

    try:
        result = run_artifacts_generation(args.workspace, args.session_dir)
    except ArtifactsGenerationError as exc:
        print(f"[派生产物] 失败：{exc}", file=__import__("sys").stderr)
        return 2

    print(f"[派生产物] 状态：{result['status']}")
    print(f"[派生产物] 模块：{result['module_name']}")
    print(f"[派生产物] client.py：{result['client_path']}")
    print(f"[派生产物] quick_test.py：{result['quick_test_path']}")
    print(f"[派生产物] 候选报告：{result['candidate_report_path']}")
    print(f"[派生产物] 响应样本：{len(result['response_sample_paths'])} 个")
    if result["preserved_paths"]:
        print(f"[派生产物] 已保留人工文件：{len(result['preserved_paths'])} 个")
    if result["warnings"]:
        print("[派生产物] 警告：")
        for w in result["warnings"]:
            print(f"  - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())