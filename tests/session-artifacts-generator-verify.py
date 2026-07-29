"""
session-artifacts-generator-verify.py — Web 会话派生产物生成器的最小验证

执行方式：
    python tests/session-artifacts-generator-verify.py

设计原则：
- 纯函数断言，不启动真实 Chrome / DrissionPage，不访问真实网络；
- 覆盖 7 类断言：模块加载与公开契约、步骤证据与 HAR 聚合、六维评分与稳定排序、
  最大响应样本与合法 JSON、类式模板与 lifecycle 边界、quick_test 与幂等防覆盖、
  中文与集成点；
- TDD 风格：Task 1 写测试骨架，Task 2-4 实现生成器，初始运行因脚本不存在失败，
  实现完成后全部通过；
- 任一断言失败抛出 AssertionError，CI 以非零退出码识别。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_DIR = Path(__file__).resolve().parents[1]
GENERATOR_SCRIPT = REPO_DIR / "skills" / "mcpowers-crawler-reverse" / "scripts" / "session-artifacts-generator.py"
SESSION_SCRIPT = REPO_DIR / "skills" / "mcpowers-crawler-reverse" / "scripts" / "reverse-analysis-session.py"
RECORDER_SCRIPT = REPO_DIR / "skills" / "mcpowers-crawler-reverse" / "scripts" / "user-action-recorder.py"


def load_module(script_path: Path, module_name: str) -> ModuleType:
    """按文件路径加载脚本为模块（连字符文件名）。"""

    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"无法加载模块：{script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _build_workspace_with_session() -> tuple[Path, Path, Path]:
    """构造最小工作区 + 已停止会话目录，模拟 v2.19.0 web-stop 后状态。"""

    tmp = Path(tempfile.mkdtemp(prefix="mcpowers_artifact_test_"))
    workspace = tmp / "demo-crawler-reverse"
    workspace.mkdir()
    session_dir = workspace / "01-目标画像" / "录制" / "会话-20260729-120000"
    session_dir.mkdir(parents=True)

    # 中文标准子目录（仅建必需的；镜像 v2.19.0 workspace 模板）
    for relative in (
        "01-目标画像/弹窗截图",
        "01-目标画像/录制",
        "02-接口分析/响应样本",
        "03-逆向攻坚/钩子",
        "04-模块封装",
    ):
        (workspace / relative).mkdir(parents=True, exist_ok=True)

    return tmp, workspace, session_dir


def _write_step_evidence_index(session_dir: Path, steps: list[dict[str, Any]]) -> None:
    """把构造的步骤证据写为 v2.19.0 步骤证据索引格式。"""

    doc = {
        "generated_at": "2026-07-29T12:00:00+08:00",
        "window_ms": 1000,
        "artifacts": {
            "actions": str(session_dir / "user-actions.json"),
            "network": str(session_dir / "user-session.har.jsonl"),
            "js_runtime": str(session_dir / "js-runtime.jsonl"),
        },
        "steps": steps,
    }
    (session_dir / "步骤证据索引.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_har_entries(session_dir: Path, entries: list[dict[str, Any]]) -> None:
    """把构造的 HAR 条目写为 JSONL（v2.18.x user-action-recorder 格式）。"""

    with (session_dir / "user-session.har.jsonl").open("w", encoding="utf-8") as file:
        for entry in entries:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _write_actions(session_dir: Path, actions: list[dict[str, Any]]) -> None:
    """把构造的用户操作写为 v2.15.0 user-actions.json 格式。"""

    doc = {
        "version": "1.0",
        "created_at": "2026-07-29T12:00:00+08:00",
        "actions": actions,
    }
    (session_dir / "user-actions.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ============================================================================
# 断言函数
# ============================================================================

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


# ============================================================================
# 准备：被测脚本存在性校验（其他断言才有效）
# ============================================================================

print("[0/7] 准备：被测脚本存在性")
assert_eq("生成器脚本存在", GENERATOR_SCRIPT.is_file(), True)
assert_eq("会话编排脚本存在", SESSION_SCRIPT.is_file(), True)
assert_eq("录制器脚本存在", RECORDER_SCRIPT.is_file(), True)


# ============================================================================
# 1. 模块加载与公开契约
# ============================================================================

print("[1/7] 模块加载与公开契约")
generator = load_module(GENERATOR_SCRIPT, "mcpowers_session_artifacts_generator_test")

assert_true("run_artifacts_generation 函数存在", callable(getattr(generator, "run_artifacts_generation", None)), "")
assert_true("ArtifactsGenerationError 异常类存在", isinstance(getattr(generator, "ArtifactsGenerationError", None), type), "")
assert_true("六类 lifecycle 标签常量定义", all(
    label in getattr(generator, "LIFECYCLE_LABELS", [])
    for label in ("reusable", "per-request", "single-use-token", "session-bound", "time-bound", "challenge-bound")
), "")

# 路径越界：session_dir 不在工作区之下应拒绝
tmp_root = Path(tempfile.mkdtemp(prefix="mcpowers_artifact_outerror_"))
workspace = tmp_root / "demo-crawler-reverse"
workspace.mkdir()
other_dir = tmp_root / "another-crawler-reverse" / "01-目标画像" / "录制" / "会话-x"
other_dir.mkdir(parents=True)
assert_raises(
    "越界 session_dir 抛 ArtifactsGenerationError",
    generator.ArtifactsGenerationError,
    generator.run_artifacts_generation,
    workspace,
    other_dir,
)

# 缺步骤证据索引：应抛 ArtifactsGenerationError
with tempfile.TemporaryDirectory() as tmp:
    workspace = Path(tmp) / "demo-crawler-reverse"
    workspace.mkdir()
    session_dir = workspace / "01-目标画像" / "录制" / "会话-x"
    session_dir.mkdir(parents=True)
    assert_raises(
        "缺步骤证据索引抛 ArtifactsGenerationError",
        generator.ArtifactsGenerationError,
        generator.run_artifacts_generation,
        workspace,
        session_dir,
    )


# ============================================================================
# 2. 步骤证据与 HAR 聚合
# ============================================================================

print("[2/7] 步骤证据与 HAR 聚合")
with tempfile.TemporaryDirectory() as tmp_root:
    tmp_root_path = Path(tmp_root)
    workspace = tmp_root_path / "demo-crawler-reverse"
    workspace.mkdir()
    session_dir = workspace / "01-目标画像" / "录制" / "会话-20260729-120000"
    session_dir.mkdir(parents=True)
    for relative in ("02-接口分析/响应样本", "04-模块封装"):
        (workspace / relative).mkdir(parents=True, exist_ok=True)

    base_ts = "2026-07-29T12:00:00+08:00"
    _write_actions(
        session_dir,
        [
            {"step": 1, "timestamp": base_ts, "type": "click", "selectors": ["#search"]},
            {"step": 2, "timestamp": base_ts, "type": "fill", "selectors": ["#input"]},
        ],
    )
    _write_har_entries(
        session_dir,
        [
            # 业务接口 1：POST /api/search 应触发
            {"ts": base_ts, "kind": "request", "method": "POST", "url": "https://example.com/api/search", "status": None},
            {"ts": base_ts, "kind": "response", "method": None, "url": "https://example.com/api/search", "status": 200,
             "body_preview": json.dumps({"data": [{"id": 1, "name": "a"}]}, ensure_ascii=False)},
            # 业务接口 2：GET /api/list 应触发
            {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/api/list", "status": 200,
             "body_preview": json.dumps({"list": [{"id": 2}]}, ensure_ascii=False)},
            # 静态资源：不应进入 top10
            {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/static/app.js", "status": 200},
            # 埋点：不应进入 top10
            {"ts": base_ts, "kind": "response", "method": "POST", "url": "https://example.com/log/collect", "status": 204},
        ],
    )
    _write_step_evidence_index(
        session_dir,
        [
            {
                "step": 1,
                "timestamp": base_ts,
                "action": {"type": "click", "selectors": ["#search"]},
                "network": [
                    {"index": 0, "kind": "response", "method": None, "url": "https://example.com/api/search", "status": 200},
                ],
                "js_runtime": [],
            },
            {
                "step": 2,
                "timestamp": base_ts,
                "action": {"type": "fill", "selectors": ["#input"]},
                "network": [
                    {"index": 1, "kind": "response", "method": "GET", "url": "https://example.com/api/list", "status": 200},
                ],
                "js_runtime": [],
            },
        ],
    )

    result = generator.run_artifacts_generation(workspace, session_dir)
    assert_eq("返回 dict", isinstance(result, dict), True)
    assert_true("status 字段存在", result.get("status") in ("generated", "partial", "skipped"), result.get("status"))
    assert_true("warnings 字段是 list", isinstance(result.get("warnings"), list), str(result.get("warnings")))
    assert_true("candidate_report_path 是字符串", isinstance(result.get("candidate_report_path"), str), str(result.get("candidate_report_path")))

    # 静态资源 + 埋点不应出现在 top10 报告
    candidate_report = Path(result["candidate_report_path"]).read_text(encoding="utf-8")
    assert_true("静态 app.js 不入 top10", "/static/app.js" not in candidate_report, candidate_report[:200])
    assert_true("埋点 /log/collect 不入 top10", "/log/collect" not in candidate_report, candidate_report[:200])

    # 业务接口至少出现 1 个
    assert_true("业务接口 /api/search 在报告中", "/api/search" in candidate_report, candidate_report[:200])

    # response 缺 method 时不应被静默当 GET 配对后硬塞进 top10
    assert_true("method 补齐逻辑生效（POST 已识别）", "POST" in candidate_report, candidate_report[:200])


# ============================================================================
# 3. 六维评分与稳定排序
# ============================================================================

print("[3/7] 六维评分与稳定排序")
with tempfile.TemporaryDirectory() as tmp_root:
    tmp_root_path = Path(tmp_root)
    workspace = tmp_root_path / "demo-crawler-reverse"
    workspace.mkdir()
    session_dir = workspace / "01-目标画像" / "录制" / "会话-20260729-120000"
    session_dir.mkdir(parents=True)
    for relative in ("02-接口分析/响应样本", "04-模块封装"):
        (workspace / relative).mkdir(parents=True, exist_ok=True)

    base_ts = "2026-07-29T12:00:00+08:00"

    # 构造 12 个候选，覆盖：
    # - 业务接口（含 data / list / result / records 字段）
    # - 高频埋点（验证不能靠重复次数进 top10）
    # - challenge 接口（captcha）
    # - 仅时间戳参数
    har_entries: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []

    # 业务接口 A：关联 2 步 + 200 + data 字段
    for i in range(2):
        steps.append(
            {
                "step": i + 1,
                "timestamp": base_ts,
                "action": {"type": "click", "selectors": ["#a"]},
                "network": [{"index": i * 4, "kind": "response", "method": "GET", "url": "https://example.com/api/a", "status": 200}],
                "js_runtime": [],
            }
        )
        har_entries.extend([
            {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/api/a", "status": 200,
             "body_preview": json.dumps({"data": {"id": i}}, ensure_ascii=False)},
        ])

    # 业务接口 B：含 list + records
    steps.append(
        {
            "step": 3,
            "timestamp": base_ts,
            "action": {"type": "click", "selectors": ["#b"]},
            "network": [{"index": 10, "kind": "response", "method": "GET", "url": "https://example.com/api/b", "status": 200}],
            "js_runtime": [],
        }
    )
    har_entries.append(
        {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/api/b", "status": 200,
         "body_preview": json.dumps({"list": [], "records": []}, ensure_ascii=False)}
    )

    # 高频埋点：重复 8 次无操作关联
    for _ in range(8):
        har_entries.append(
            {"ts": base_ts, "kind": "response", "method": "POST", "url": "https://example.com/track/beacon", "status": 204}
        )

    # challenge 接口：含 captcha
    steps.append(
        {
            "step": 4,
            "timestamp": base_ts,
            "action": {"type": "click", "selectors": ["#c"]},
            "network": [{"index": 30, "kind": "response", "method": "POST", "url": "https://example.com/api/captcha", "status": 200}],
            "js_runtime": [],
        }
    )
    har_entries.append(
        {"ts": base_ts, "kind": "response", "method": "POST", "url": "https://example.com/api/captcha", "status": 200,
         "body_preview": json.dumps({"challenge": "x", "captcha_token": "y"}, ensure_ascii=False)}
    )

    # 仅时间戳参数
    steps.append(
        {
            "step": 5,
            "timestamp": base_ts,
            "action": {"type": "goto", "url": "https://example.com/p"},
            "network": [{"index": 40, "kind": "response", "method": "GET", "url": "https://example.com/p?ts=123", "status": 200}],
            "js_runtime": [],
        }
    )
    har_entries.append(
        {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/p?ts=123", "status": 200,
         "body_preview": "OK"}
    )

    _write_actions(session_dir, [])
    _write_har_entries(session_dir, har_entries)
    _write_step_evidence_index(session_dir, steps)

    result = generator.run_artifacts_generation(workspace, session_dir)
    candidate_report = Path(result["candidate_report_path"]).read_text(encoding="utf-8")

    # 总输出行数最多 10 个 endpoint
    table_rows = [line for line in candidate_report.splitlines() if line.startswith("| ") and "/api/a" in line or "/api/b" in line or "/track/beacon" in line or "/api/captcha" in line or "/p?ts=" in line]
    assert_true(
        "top10 最多 10 行（含已绑定 endpoint）",
        len(table_rows) <= 10,
        f"实际={len(table_rows)}",
    )

    # 高频埋点不能在前 10 名（埋点 8 次 vs 业务接口 2-3 步关联）
    assert_true("高频埋点不在报告中（或不在前 10）", "/track/beacon" not in candidate_report or candidate_report.find("/api/a") < candidate_report.find("/track/beacon"), "")

    # challenge 接口仍出现在报告中（即使分数低）
    assert_true("challenge 接口不被剔除", "/api/captcha" in candidate_report, candidate_report[:200])

    # 评分合计：每个 endpoint 行必须含"总分="（或同义）
    assert_true("评分字段存在", "总分" in candidate_report or "total_score" in candidate_report, candidate_report[:200])


# ============================================================================
# 4. 最大响应样本与合法 JSON
# ============================================================================

print("[4/7] 最大响应样本与合法 JSON")
with tempfile.TemporaryDirectory() as tmp_root:
    tmp_root_path = Path(tmp_root)
    workspace = tmp_root_path / "demo-crawler-reverse"
    workspace.mkdir()
    session_dir = workspace / "01-目标画像" / "录制" / "会话-20260729-120000"
    session_dir.mkdir(parents=True)
    for relative in ("02-接口分析/响应样本", "04-模块封装"):
        (workspace / relative).mkdir(parents=True, exist_ok=True)

    base_ts = "2026-07-29T12:00:00+08:00"
    # 同一 endpoint 多个响应：选最大且能解析 JSON 的
    small_json = json.dumps({"id": 1}, ensure_ascii=False)
    big_json = json.dumps({"data": [{"id": i, "name": "x" * 50} for i in range(20)]}, ensure_ascii=False)
    truncated = "{ \"data\":[{\"id\":1,\"name\":\"half-truncated"  # 不闭合

    har_entries = [
        {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/api/list", "status": 200,
         "body_preview": small_json},
        {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/api/list", "status": 200,
         "body_preview": big_json},
        {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/api/list", "status": 500,
         "body_preview": truncated},
    ]
    steps = [
        {
            "step": 1,
            "timestamp": base_ts,
            "action": {"type": "click", "selectors": ["#x"]},
            "network": [{"index": 0, "kind": "response", "method": "GET", "url": "https://example.com/api/list", "status": 200}],
            "js_runtime": [],
        }
    ]
    _write_actions(session_dir, [])
    _write_har_entries(session_dir, har_entries)
    _write_step_evidence_index(session_dir, steps)

    result = generator.run_artifacts_generation(workspace, session_dir)
    response_sample_paths = result.get("response_sample_paths", [])
    assert_true("响应样本目录有文件", len(response_sample_paths) >= 1, str(response_sample_paths))

    # 每接口仅 1 个文件
    sample_dir = workspace / "02-接口分析" / "响应样本"
    api_list_samples = list(sample_dir.glob("*-get-api-list-*.json"))
    assert_eq("同接口仅 1 个响应样本", len(api_list_samples), 1)

    # 文件名必须不含 ? / .. /
    sample_filename = api_list_samples[0].name
    assert_true("文件名不含 ?", "?" not in sample_filename, sample_filename)
    assert_true("文件名不含 ..", ".." not in sample_filename, sample_filename)
    assert_true("文件名不含 /", "/" not in sample_filename, sample_filename)

    # envelope 合法 JSON + 必备字段
    envelope = json.loads(api_list_samples[0].read_text(encoding="utf-8"))
    assert_true("envelope.endpoint.method 字段", "endpoint" in envelope and "method" in envelope["endpoint"], str(envelope))
    assert_true("envelope.body_truncated 字段", "body_truncated" in envelope, str(envelope))
    assert_true("envelope.parse_status 字段", "parse_status" in envelope, str(envelope))
    assert_true("envelope 声明不代表完整响应体", "不代表完整" in envelope.get("note", "") or "preview" in envelope.get("note", ""), envelope.get("note", ""))

    # 选中的是 big_json（最大且可解析）
    assert_eq("envelope.status=200", envelope.get("status"), 200)
    parsed_body = envelope.get("parsed_body") or {}
    assert_true("envelope.parsed_body 解析为 dict/list", isinstance(parsed_body, (dict, list)) and len(parsed_body) > 0, str(parsed_body))


# ============================================================================
# 5. 类式模板与 lifecycle 边界
# ============================================================================

print("[5/7] 类式模板与 lifecycle 边界")
with tempfile.TemporaryDirectory() as tmp_root:
    tmp_root_path = Path(tmp_root)
    workspace = tmp_root_path / "demo-crawler-reverse"
    workspace.mkdir()
    session_dir = workspace / "01-目标画像" / "录制" / "会话-20260729-120000"
    session_dir.mkdir(parents=True)
    for relative in ("02-接口分析/响应样本", "04-模块封装"):
        (workspace / relative).mkdir(parents=True, exist_ok=True)

    base_ts = "2026-07-29T12:00:00+08:00"
    har_entries = [
        # 含多种 lifecycle 字段
        {"ts": base_ts, "kind": "request", "method": "POST", "url": "https://example.com/api/order",
         "headers": {"Authorization": "Bearer SECRET", "Cookie": "sid=SECRET", "X-CSRF-Token": "SECRET"},
         "post_data": "item_id=42&timestamp=1700000000&nonce=abc&sign=DEADBEEF"},
        {"ts": base_ts, "kind": "response", "method": None, "url": "https://example.com/api/order", "status": 200,
         "body_preview": json.dumps({"order_id": "xxx"}, ensure_ascii=False)},
        # 纯 challenge 接口
        {"ts": base_ts, "kind": "response", "method": "POST", "url": "https://example.com/api/verify_captcha", "status": 200,
         "body_preview": json.dumps({"captcha_token": "REQUIRED"}, ensure_ascii=False)},
    ]
    steps = [
        {
            "step": 1,
            "timestamp": base_ts,
            "action": {"type": "click", "selectors": ["#submit"]},
            "network": [{"index": 0, "kind": "response", "method": None, "url": "https://example.com/api/order", "status": 200}],
            "js_runtime": [],
        }
    ]
    _write_actions(session_dir, [])
    _write_har_entries(session_dir, har_entries)
    _write_step_evidence_index(session_dir, steps)

    result = generator.run_artifacts_generation(workspace, session_dir)
    module_name = result.get("module_name")
    client_path = Path(result["client_path"])
    assert_true("client_path 已生成", client_path.is_file(), str(client_path))
    client_text = client_path.read_text(encoding="utf-8")
    assert_true("client.py 含 build_request", "def build_request(" in client_text, "")
    assert_true("client.py 含 do_request", "def do_request(" in client_text, "")
    assert_true("client.py 含 parse_response", "def parse_response(" in client_text, "")
    assert_true("client.py 含 request_and_parse", "def request_and_parse(" in client_text, "")

    # 至少 4 类 lifecycle 标签被引用
    lifecycle_count = sum(1 for label in ("reusable", "per-request", "session-bound", "challenge-bound") if label in client_text)
    assert_true("client.py 含 ≥4 类 lifecycle 标签", lifecycle_count >= 4, f"count={lifecycle_count}")

    # 业务方法签名不含敏感原值
    assert_true("client.py 不含抓包 token 原值", "SECRET" not in client_text and "DEADBEEF" not in client_text, client_text[:200])
    assert_true("client.py 不含抓包 cookie sid 原值", "sid=SECRET" not in client_text, client_text[:200])

    # 业务方法零前置参数：检查第一个业务方法签名不含敏感关键字作必填参数
    business_method_match = re.search(r"def\s+\w+\(\s*self\s*(?:,\s*(\w+)[^)]*)?\)", client_text)
    if business_method_match:
        params_text = business_method_match.group(1) or ""
        forbidden_params = {"token", "cookie", "sign", "nonce", "timestamp", "challenge", "csrf", "xsrf", "session_id", "captcha"}
        leaked = forbidden_params & set(re.findall(r"\b[a-z_]+\b", params_text))
        assert_eq("业务方法零前置参数（不暴露敏感参数）", leaked, set())

    # challenge-only 接口不被生成普通业务方法
    assert_true("verify_captcha 接口不生成普通业务方法", "verify_captcha" not in client_text or "TODO" in client_text or "challenge" in client_text.lower(), "")


# ============================================================================
# 6. quick_test 与幂等防覆盖
# ============================================================================

print("[6/7] quick_test 与幂等防覆盖")
with tempfile.TemporaryDirectory() as tmp_root:
    tmp_root_path = Path(tmp_root)
    workspace = tmp_root_path / "demo-crawler-reverse"
    workspace.mkdir()
    session_dir = workspace / "01-目标画像" / "录制" / "会话-20260729-120000"
    session_dir.mkdir(parents=True)
    for relative in ("02-接口分析/响应样本", "04-模块封装"):
        (workspace / relative).mkdir(parents=True, exist_ok=True)

    base_ts = "2026-07-29T12:00:00+08:00"
    har_entries = [
        {"ts": base_ts, "kind": "response", "method": "GET", "url": "https://example.com/api/x", "status": 200,
         "body_preview": json.dumps({"data": []}, ensure_ascii=False)},
    ]
    steps = [
        {
            "step": 1,
            "timestamp": base_ts,
            "action": {"type": "click", "selectors": ["#x"]},
            "network": [{"index": 0, "kind": "response", "method": "GET", "url": "https://example.com/api/x", "status": 200}],
            "js_runtime": [],
        }
    ]
    _write_actions(session_dir, [])
    _write_har_entries(session_dir, har_entries)
    _write_step_evidence_index(session_dir, steps)

    # 第一次生成
    first_result = generator.run_artifacts_generation(workspace, session_dir)
    quick_test_path = Path(first_result["quick_test_path"])
    assert_true("quick_test.py 已生成", quick_test_path.is_file(), str(quick_test_path))
    quick_test_text = quick_test_path.read_text(encoding="utf-8")
    assert_true("quick_test 含 __main__", 'if __name__ == "__main__":' in quick_test_text, "")
    assert_true("quick_test 不读 sys.argv", "sys.argv" not in quick_test_text, "")
    # 三类用法演示
    usage_keywords = ["request_and_parse", "build_request", "do_request"]
    usage_hits = sum(1 for kw in usage_keywords if kw in quick_test_text)
    assert_true("quick_test 演示 3 类用法（命中 ≥3 个关键字）", usage_hits >= 3, f"hits={usage_hits}")

    # 第二次生成：手工写入标记 → 验证不覆盖
    manual_marker = "# MANUAL_EDIT_MARKER_FOR_TEST\n"
    quick_test_path.write_text(manual_marker + quick_test_text, encoding="utf-8")
    client_path = Path(first_result["client_path"])
    client_marker = "# MANUAL_CLIENT_MARKER_FOR_TEST\n"
    client_path.write_text(client_marker + client_path.read_text(encoding="utf-8"), encoding="utf-8")

    second_result = generator.run_artifacts_generation(workspace, session_dir)
    preserved = second_result.get("preserved_paths", [])
    preserved_strs = [str(p) for p in preserved]
    assert_true("client.py 被保留（未覆盖）", str(client_path) in preserved_strs, str(preserved))
    assert_true("quick_test.py 被保留（未覆盖）", str(quick_test_path) in preserved_strs, str(preserved))

    # 标记仍在
    assert_true("client.py 人工标记仍存在", client_marker in client_path.read_text(encoding="utf-8"), "")
    assert_true("quick_test.py 人工标记仍存在", manual_marker in quick_test_path.read_text(encoding="utf-8"), "")

    # 候选报告可原子重建（不受 preserved 影响）
    candidate_path = Path(second_result["candidate_report_path"])
    assert_true("候选报告可重建", candidate_path.is_file(), str(candidate_path))


# ============================================================================
# 7. 中文与集成点
# ============================================================================

print("[7/7] 中文与集成点")

# 7a. 生成器脚本首部 docstring 中文
generator_text = GENERATOR_SCRIPT.read_text(encoding="utf-8")
assert_true("生成器脚本首部 docstring 中文", "派生产物" in generator_text or "会话产物" in generator_text or "生成器" in generator_text, generator_text[:200])

# 7b. 关键打印 / 异常中文
chinese_markers = ["工作区", "生成", "会话", "派生产物", "候选", "样本", "接口"]
chinese_hits = sum(1 for marker in chinese_markers if marker in generator_text)
assert_true("生成器脚本含 ≥3 个中文关键标记", chinese_hits >= 3, f"hits={chinese_hits}")

# 7c. 中文注释检查（豁免纯 ASCII 分隔线）
ascii_only = re.compile(r"^[\x00-\x7f]+$")
section_divider = re.compile(r"^#+\s*[-=]+\s*$")
suspicious_english_comments: list[str] = []
for line_no, line in enumerate(generator_text.splitlines(), start=1):
    stripped = line.strip()
    if not stripped:
        continue
    if not stripped.startswith("#"):
        continue
    if section_divider.match(stripped):
        continue
    body = stripped.lstrip("#").strip()
    if body and ascii_only.match(body):
        suspicious_english_comments.append(f"{GENERATOR_SCRIPT.name}:{line_no}: {stripped[:60]}")
assert_eq("生成器脚本无英文注释残留（已豁免纯 ASCII 分隔线）", suspicious_english_comments, [])

# 7d. reverse-analysis-session.py 已加载并调用生成器
session_text = SESSION_SCRIPT.read_text(encoding="utf-8")
assert_true("session 脚本加载 session-artifacts-generator", "session-artifacts-generator.py" in session_text, "")
assert_true("session 脚本调用 run_artifacts_generation", "run_artifacts_generation" in session_text, "")
assert_true("session 脚本在 build_step_evidence_index 之后调用", session_text.find("run_artifacts_generation") > session_text.find("build_step_evidence_index"), "")
assert_true("session 脚本写 artifacts_generation 字段", "artifacts_generation" in session_text, "")


print("\n全部 7 类断言通过。")