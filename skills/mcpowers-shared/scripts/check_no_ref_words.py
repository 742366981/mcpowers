#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mcpowers 通用零引用字眼检测（v4.3.0+ 智能二分判定）

被以下脚本共享调用:
  - hooks/pre-write-check-no-ref-words.sh（PreToolUse 硬门禁）
  - hooks/post-write-check-doc-content.sh（PostToolUse 软门禁兜底）
  - hooks/post-write-check-no-ref-words.sh（v4.3.0 重命名后版本）
  - swagger-lint-helper.py check_no_reference_words()（v4.0.1 接口零引用，未来可复用本模块）
  - export_docs.py check_no_reference_words_spec()（v4.0.1 接口零引用 spec 端，未来可复用本模块）

设计动机（v4.3.0+）:
  接口文档（docstring / spec / md）v4.0.1/v4.0.2 已覆盖;但代码注释 / 配置文件 / 函数 docstring 中文段
  仍会出现「参考《代码规范》§11.3」「按规范要求校验」「参考 utils/security.py」等指向其他文档的字眼,
  让 IDE 里看注释的读者困惑:到底是哪个规范?我点哪里看?

  本模块实现智能二分判定:
    1. 边界豁免（YAML 字段名行 / Issue 编号 / 占位符）→ 直接放行
    2. 外部权威（RFC/PEP/W3C/OWASP/ISO/IEEE/公认作者/官方文档 URL）→ 放行
    3. 内部规范名（含别名）→ 拦截（标记"内部规范"类）
    4. 项目内代码文件路径 → 拦截（标记"实现跳转"类）
    5. 项目内 .md 文档名（非白名单）→ 拦截（标记"项目说明跳转"类）
    6. 「按规范/根据规范/遵守规范/按照规范」无外部前缀 → 拦截（标记"画蛇添足"类）
    7. 兜底 → 拦截（标记"画蛇添足兜底"类）

使用方式:
    from check_no_ref_words import scan_content, scan_line, is_path_whitelisted

    # 整文件扫描(返回 list[Violation])
    violations = scan_content(content, file_path, file_ext='.py')
    for v in violations:
        print(v.line_no, v.level, v.category, v.message)

    # 单行扫描
    level, category, message = scan_line("参考《代码规范》§11.3 命名", line_no=5)

    # 路径白名单检查
    if is_path_whitelisted("tests/test_foo.py"):
        # 跳过整个文件
        ...

退出码:
    本模块不直接退出;由调用方根据 violations 决定 exit code

共享常量（3 个文件）:
    - _forbidden_ref_words.txt    22 字眼 + 4 口语化补充
    - _internal_spec_docs.txt     33 份规范 + 别名
    - _external_authority.txt     3 类外部权威 pattern
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


# ============== 常量加载 ==============

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "docs" / "_assets"

# 22 字眼 + 4 口语化补充
_FORBIDDEN_REF_WORDS_FILE = _ASSETS_DIR / "_forbidden_ref_words.txt"
# 33 份规范 + 别名
_INTERNAL_SPEC_DOCS_FILE = _ASSETS_DIR / "_internal_spec_docs.txt"
# 3 类外部权威 pattern
_EXTERNAL_AUTHORITY_FILE = _ASSETS_DIR / "_external_authority.txt"


def _load_list(file_path: Path, skip_comment_prefix: str = "#") -> list[str]:
    """从共享常量文件加载非空非注释行。

    Args:
        file_path: 常量文件绝对路径
        skip_comment_prefix: 注释前缀（默认 #）

    Returns:
        过滤后的行列表（已 strip）

    Raises:
        FileNotFoundError: 常量文件不存在（由调用方决定是否放行）
    """
    if not file_path.exists():
        raise FileNotFoundError(f"共享常量文件不存在: {file_path}")
    lines: list[str] = []
    for raw in file_path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith(skip_comment_prefix):
            continue
        lines.append(stripped)
    return lines


def _load_external_authority_patterns() -> list[re.Pattern[str]]:
    """从 _external_authority.txt 加载外部权威 regex pattern。

    跳过所有注释段（以 # 开头的行）+ 非 pattern 段（含"==="分隔符 / "命中优先级"等元说明）。
    仅加载纯 regex pattern 行（无空格或纯 ASCII regex 字符）。

    Returns:
        编译后的 re.Pattern 列表
    """
    if not _EXTERNAL_AUTHORITY_FILE.exists():
        return []
    patterns: list[re.Pattern[str]] = []
    for raw in _EXTERNAL_AUTHORITY_FILE.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # 跳过元说明段（含中文 / 段落标记 / 优先级说明）
        if any(marker in stripped for marker in ("===", "优先级", "放行示例", "拦截示例",
                                                  "命中案例", "命中段", "命中 ", "developers.mozilla")):
            continue
        # 仅编译看起来像 regex 的行（含 . * + ? [ ] ( ) { } | ^ $ \ 等）
        if not any(c in stripped for c in r".*+?[](){}|^\\"):
            continue
        try:
            patterns.append(re.compile(stripped, re.IGNORECASE))
        except re.error:
            # 单条 pattern 错误不阻断整体加载
            continue
    return patterns


# 模块级缓存（避免每次调用都读文件）
_FORBIDDEN_WORDS_CACHE: list[str] | None = None
_INTERNAL_SPECS_CACHE: list[str] | None = None
_INTERNAL_SPECS_LOWER_CACHE: list[str] | None = None
_EXTERNAL_AUTHORITY_CACHE: list[re.Pattern[str]] | None = None
_INTERNAL_CODE_FILE_PATTERN = re.compile(
    r"\b([a-zA-Z_][a-zA-Z0-9_/]*\.(py|sh|js|ts|jsx|tsx|go|java|rs|yaml|yml|json|toml|ini|conf))\b"
)
_INTERNAL_MD_PATTERN = re.compile(
    r"\b([A-Za-z0-9_一-龥][A-Za-z0-9_\-一-龥]*\.md)\b"
)
_GITHUB_USER_REPO_PATTERN = re.compile(
    r"https?://github\.com/[A-Za-z0-9_\-]+/[A-Za-z0-9_\-\.]+(/[\w\-./%?#=&]*)?"
)
_ISSUE_NUMBER_PATTERN = re.compile(r"#\d{2,}")
_YAML_FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*\s*:\s*$")
_INDUSTRY_AUTHORITY_PREFIX_PATTERN = re.compile(
    r"(按|根据|遵守|遵循|按照)\s*(行业|国家|国际|全球|业界)\s*(规范|标准|约定)"
)
_UNBOUNDED_SPEC_PHRASE_PATTERN = re.compile(
    r"(按|根据|遵守|遵循|按照)\s*(本项目|团队|内部|本仓库)?\s*(规范|标准|约定|铁律)"
)
_PYTHON_DOCSTRING_TRIPLE_PATTERN = re.compile(r'"""[\s\S]*?"""', re.MULTILINE)
_PYTHON_DOCSTRING_TRIPLE_SINGLE_PATTERN = re.compile(r"'''[\s\S]*?'''", re.MULTILINE)


# 路径白名单（命中放行整个文件）
_PATH_WHITELIST_DIRS: tuple[str, ...] = (
    "tests/", "test/", "__tests__/",
    "fixtures/", "testdata/", "test_data/", "mocks/",
    "examples/", "demo/", "samples/",
    "templates/", "template/", "scaffolds/",
    "docs/历史教训/",
)
_PATH_WHITELIST_FILES: tuple[str, ...] = (
    "CHANGELOG.md",
    # v4.6.3+ 顶层导航文档（索引型,非输出型）—— v4.0.2 §9.5 场景化判定模型中作为「索引型文档」
    # 允许指向其他规范章节；v4.3.0「CLAUDE.md/README.md 无例外」决策与 §9.5 立场冲突,
    # v4.6.3 兜底段（git commit）首次执行暴露此冲突,回归 §9.5 索引型豁免。
    "CLAUDE.md",
    "README.md",
    "AGENTS.md",
)
_PATH_WHITELIST_SUBSTRINGS: tuple[str, ...] = (
    "mcpowers-spec-index", "API契约", "接口契约", "迁移", "migration", "Migration", "migrate",
    "deprecation", "Deprecation", "DEPRECATED",
    "历史教训",
)

# v4.6.3+ 规范术语名豁免（精确子串命中整行放行）
# 设计动机：v4.3.0 引入的「代码/配置零引用」铁律名本身含禁用字眼,无差别扫描会破坏术语一致性；
# 兜底段（git commit）首次执行暴露这一冲突——必须豁免规范术语名（含 R15/R16/R17 三层铁律名）。
# 加新铁律时同时把铁律名加到这里，保持 SSOT（单一权威源）。
_TERM_EXCEPTIONS: frozenset[str] = frozenset({
    "代码/配置零引用铁律",
    "代码/配置零引用智能二分判定",
    "代码/配置零引用智能二分",
    "R17 零引用",
    "R17 代码/配置零引用",
    "R15 接口零引用",
    "R16 .md 零引用",
})


def _get_forbidden_words() -> list[str]:
    """懒加载禁用字眼清单。"""
    global _FORBIDDEN_WORDS_CACHE
    if _FORBIDDEN_WORDS_CACHE is None:
        _FORBIDDEN_WORDS_CACHE = _load_list(_FORBIDDEN_REF_WORDS_FILE)
    return _FORBIDDEN_WORDS_CACHE


def _get_internal_specs() -> tuple[list[str], list[str]]:
    """懒加载内部规范名清单（含别名），返回 (原始列表, lower 后列表)。"""
    global _INTERNAL_SPECS_CACHE, _INTERNAL_SPECS_LOWER_CACHE
    if _INTERNAL_SPECS_CACHE is None:
        specs = _load_list(_INTERNAL_SPEC_DOCS_FILE)
        _INTERNAL_SPECS_CACHE = specs
        _INTERNAL_SPECS_LOWER_CACHE = [_normalize_token(s) for s in specs]
    return _INTERNAL_SPECS_CACHE, _INTERNAL_SPECS_LOWER_CACHE


def _get_external_authority_patterns() -> list[re.Pattern[str]]:
    """懒加载外部权威 regex pattern 列表。"""
    global _EXTERNAL_AUTHORITY_CACHE
    if _EXTERNAL_AUTHORITY_CACHE is None:
        _EXTERNAL_AUTHORITY_CACHE = _load_external_authority_patterns()
    return _EXTERNAL_AUTHORITY_CACHE


# ============== 数据结构 ==============

@dataclass
class Violation:
    """单条违规记录。

    Attributes:
        line_no: 行号（1-indexed;跨行结构如 docstring 报起始行）
        level: 严重级别 — 'ERROR'（硬门禁阻断）/ 'WARNING'（软门禁提示）
        category: 违规分类 — 'internal_spec' / 'internal_code' / 'internal_md' /
            'unbounded_spec' / 'fallback' 五类
        word: 命中的禁用字眼（如「参考」）
        message: 人类可读的违规说明
    """
    line_no: int
    level: str
    category: str
    word: str
    message: str


# ============== 工具函数 ==============

def _normalize_token(text: str) -> str:
    """规范化 token 用于别名匹配：小写化 + 去书名号 + 去空格 + 去横线。"""
    return (
        text.lower()
        .replace("《", "")
        .replace("》", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def _normalize_line(line: str) -> str:
    """规范化行文本用于别名匹配（与 _normalize_token 一致）。"""
    return _normalize_token(line)


def _is_yaml_field_name_line(line: str) -> bool:
    """判断是否为 YAML 字段名行（形如 `key:` 末尾冒号且无 value）。

    YAML 字段名是结构标记，不是字眼，应放行。
    但 `description: 参考 RFC 7519` 这种带 value 的不视为纯字段名行，仍需判定。
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    return bool(_YAML_FIELD_NAME_PATTERN.match(stripped))


def _is_obvious_external_url(token: str, line: str) -> bool:
    """判断行内出现的 token 是否明显是外部 URL 的一部分（如 docs.python.org 等）。

    Args:
        token: 行内匹配到的代码文件名（如 'asyncio.html'）
        line: 完整行文本

    Returns:
        True 表示该 token 属于外部 URL 片段,不应视为内部代码文件引用
    """
    idx = line.find(token)
    if idx < 0:
        return False
    prefix = line[max(0, idx - 60):idx].lower()
    external_url_markers = (
        "https://", "http://", "://",
        "docs.python.org", "developer.mozilla.org",
        "vuejs.org", "react.dev", "nodejs.org",
        "go.dev", "rust-lang.org", "kotlinlang.org",
        "dev.mysql.com", "redis.io", "postgresql.org",
    )
    return any(marker in prefix for marker in external_url_markers)


# ============== 单行检测 ==============

def scan_line(line: str, line_no: int = 0) -> list[Violation]:
    """扫描单行文本，返回该行所有违规（一般 0 或 1 条）。

    Args:
        line: 单行文本（不含行号）
        line_no: 行号（仅用于 Violation 记录;0 表示不报告行号）

    Returns:
        该行的 Violation 列表;空 list = 合规

    Side Effects:
        无
    """
    if not line or not line.strip():
        return []

    # 第 1 步：边界豁免检查
    if _is_yaml_field_name_line(line):
        return []  # YAML 字段名行（key: 末尾冒号且无 value）放行
    if _ISSUE_NUMBER_PATTERN.search(line) and len(line.strip()) <= 20:
        # GitHub Issue 编号（短行）放行
        return []
    if "${CLAUDE_PLUGIN_ROOT}" in line:
        return []
    # v4.6.3+ 规范术语名豁免（v4.3.0 引入的「代码/配置零引用」铁律名等术语本身含禁用字眼,整行命中即放行）
    # 规范化行后子串匹配(去书名号/空格/横线)——避免「「代码/配置零引用」铁律」被全角符号阻断
    line_normalized_for_terms = _normalize_line(line)
    if any(term in line_normalized_for_terms for term in _TERM_EXCEPTIONS):
        return []

    # 第 2 步：是否含禁用字眼
    line_lower = line.lower()
    hit_word: str | None = None
    for word in _get_forbidden_words():
        if word.lower() in line_lower:
            hit_word = word
            break
    if hit_word is None:
        return []  # 不含禁用字眼 → 合规

    # 第 3 步：智能二分判定
    category, level, message = _classify(line, hit_word)
    if category == "external_authority":
        return []  # 外部权威 → 放行

    violations: list[Violation] = [Violation(
        line_no=line_no,
        level=level,
        category=category,
        word=hit_word,
        message=message,
    )]
    return violations


def _classify(line: str, hit_word: str) -> tuple[str, str, str]:
    """智能二分判定违规分类。

    Args:
        line: 原始行文本
        hit_word: 命中的禁用字眼

    Returns:
        (category, level, message) 三元组
        category='external_authority' 时表示放行
    """
    # 优先级 1:外部权威 pattern 命中 → 放行
    for pat in _get_external_authority_patterns():
        if pat.search(line):
            return (
                "external_authority",
                "INFO",
                f"命中外部权威 pattern {pat.pattern},放行",
            )

    # 优先级 2:「按/根据/遵守/遵循/按照 + 行业/国家/国际/全球 + 规范/标准」→ 外部权威放行
    if _INDUSTRY_AUTHORITY_PREFIX_PATTERN.search(line):
        return (
            "external_authority",
            "INFO",
            "命中「行业/国家/国际/全球 + 规范/标准」前缀,视为外部权威放行",
        )

    # 优先级 3:内部规范名精确命中 → 内部规范类
    internal_specs, internal_specs_lower = _get_internal_specs()
    for spec in internal_specs:
        if spec in line:
            return (
                "internal_spec",
                "ERROR",
                f"行内命中内部规范文档《{spec}》(v4.3.0+ 代码/配置零引用铁律)"
                f"——注释应直接说明当前做法,不指向其他文档",
            )

    # 优先级 4:内部规范别名命中（lower 匹配,容忍空格/书名号差异）
    line_normalized = _normalize_line(line)
    for spec_lower in internal_specs_lower:
        if spec_lower and spec_lower in line_normalized:
            return (
                "internal_spec",
                "ERROR",
                f"行内命中内部规范别名《{spec_lower}》(v4.3.0+ 智能二分)"
                f"——口语化命中同样拦截,直接说明当前做法",
            )

    # 优先级 5:项目内代码文件路径命中 → 实现跳转类
    code_match = _INTERNAL_CODE_FILE_PATTERN.search(line)
    if code_match and not _is_obvious_external_url(code_match.group(0), line):
        return (
            "internal_code",
            "ERROR",
            f"行内命中项目内代码文件《{code_match.group(0)}》(v4.3.0+)"
            f"——注释应说明该文件做什么,不指向具体文件让读者跳转",
        )

    # 优先级 6:GitHub 个人/组织仓库（非公认组织白名单） → 拦截
    github_match = _GITHUB_USER_REPO_PATTERN.search(line)
    if github_match:
        return (
            "internal_code",
            "ERROR",
            f"行内命中 GitHub 仓库《{github_match.group(0)}》(v4.3.0+)"
            f"——非公认官方文档链接,直接说明当前做法",
        )

    # 优先级 7:项目内 .md 文档名命中 → 项目说明跳转类
    md_match = _INTERNAL_MD_PATTERN.search(line)
    if md_match:
        md_name = md_match.group(0)
        if md_name.lower() in ("claude.md", "readme.md", "agents.md"):
            return (
                "internal_md",
                "ERROR",
                f"行内命中项目说明文档《{md_name}》(v4.3.0+ 用户决策:CLAUDE.md/README.md 无例外)"
                f"——注释应自洽,不指向说明文档",
            )
        return (
            "internal_md",
            "ERROR",
            f"行内命中项目内 .md 文档《{md_name}》(v4.3.0+)"
            f"——直接说明当前做法,不指向其他文档",
        )

    # 优先级 8:无外部权威前缀的画蛇添足短语 → 画蛇添足类
    unbounded_match = _UNBOUNDED_SPEC_PHRASE_PATTERN.search(line)
    if unbounded_match:
        return (
            "unbounded_spec",
            "ERROR",
            f"行内含「{unbounded_match.group(0)}」无外部权威前缀(v4.3.0+)"
            f"——删掉字眼后意思不变,视为画蛇添足",
        )

    # 优先级 9:兜底拦截
    return (
        "fallback",
        "ERROR",
        f"行内含禁用字眼「{hit_word}」但既不指向外部权威也不指向内部规范(v4.3.0+ 兜底)"
        f"——删除字眼,直接陈述结论",
    )


# ============== 整文件扫描 ==============

def scan_content(
    content: str,
    file_path: str = "",
    file_ext: str = "",
) -> list[Violation]:
    """扫描整文件内容,返回所有违规行。

    Args:
        content: 文件完整文本（已 Read 的内容）
        file_path: 文件路径（用于路径白名单判定 + 报告）
        file_ext: 文件扩展名（含点,如 '.py';若为空从 file_path 自动提取）

    Returns:
        Violation 列表;空 list = 合规

    Side Effects:
        无
    """
    if not content:
        return []

    # 路径白名单:命中放行整个文件
    if file_path and is_path_whitelisted(file_path):
        return []
    # self-reference 豁免:detector 自身源文件(术语名集合/错误消息模板必然含禁用字眼,
    # 是 v4.3.0 智能二分判定的 SSOT 定义所在——必须自包含,不视为违规)
    if file_path and Path(file_path).resolve() == Path(__file__).resolve():
        return []

    # 自动提取扩展名
    if not file_ext and file_path:
        file_ext = Path(file_path).suffix.lower()

    # .py 文件需特殊处理 docstring（避免整段 docstring 中的字眼被多次报告）
    if file_ext == ".py":
        return _scan_python_content(content, file_path)
    return _scan_generic_content(content, file_path)


def _scan_generic_content(content: str, file_path: str) -> list[Violation]:
    """通用文件逐行扫描（.sh / .js / .ts / .go / .java / .rs / .yaml / .yml / .json 等）。

    Args:
        content: 文件完整文本
        file_path: 文件路径（仅用于报告）

    Returns:
        Violation 列表
    """
    violations: list[Violation] = []
    for line_no, line in enumerate(content.splitlines(), 1):
        violations.extend(scan_line(line, line_no=line_no))
    return violations


def _scan_python_content(content: str, file_path: str) -> list[Violation]:
    """Python 文件扫描:特殊处理 docstring 三引号块（避免字眼在长 docstring 中重复报告）。

    Args:
        content: 文件完整文本
        file_path: 文件路径（仅用于报告）

    Returns:
        Violation 列表
    """
    violations: list[Violation] = []
    masked_content, docstring_ranges = _mask_python_docstrings(content)

    for line_no, line in enumerate(masked_content.splitlines(), 1):
        line_violations = scan_line(line, line_no=line_no)
        for v in line_violations:
            # 若该行落在 docstring 块内,降级为 WARNING
            if any(start <= line_no <= end for start, end in docstring_ranges):
                v = Violation(
                    line_no=v.line_no,
                    level="WARNING",
                    category=v.category,
                    word=v.word,
                    message=v.message + "（docstring 内降级为 WARNING）",
                )
            violations.append(v)

    return violations


def _mask_python_docstrings(content: str) -> tuple[str, list[tuple[int, int]]]:
    """将 Python 三引号 docstring 块替换为占位行,记录原始行号范围。

    Args:
        content: 完整 Python 文件内容

    Returns:
        (masked_content, docstring_ranges) 元组
        masked_content: docstring 块被替换为同长度空行的文本
        docstring_ranges: [(start_line, end_line), ...] 列表
    """
    ranges: list[tuple[int, int]] = []
    masked = content

    for pattern in (_PYTHON_DOCSTRING_TRIPLE_PATTERN, _PYTHON_DOCSTRING_TRIPLE_SINGLE_PATTERN):
        for match in pattern.finditer(content):
            block = match.group(0)
            start_line = content[:match.start()].count("\n") + 1
            end_line = start_line + block.count("\n")
            ranges.append((start_line, end_line))
            replacement = "\n" * block.count("\n")
            masked = masked.replace(block, replacement, 1)

    return masked, ranges


# ============== 路径白名单 ==============

def is_path_whitelisted(file_path: str) -> bool:
    """判断文件路径是否在路径白名单内（命中即整个文件放行）。

    Args:
        file_path: 文件相对路径（POSIX 或 Windows 均可;内部自动规范化）

    Returns:
        True = 在白名单内,跳过扫描;False = 不在白名单,需扫描

    Side Effects:
        无
    """
    if not file_path:
        return False

    normalized = file_path.replace("\\", "/")

    for dir_prefix in _PATH_WHITELIST_DIRS:
        if normalized.startswith(dir_prefix) or f"/{dir_prefix}" in normalized:
            return True

    file_name = normalized.rsplit("/", 1)[-1]
    if file_name in _PATH_WHITELIST_FILES:
        return True

    for substring in _PATH_WHITELIST_SUBSTRINGS:
        if substring in normalized:
            return True

    return False


# ============== CLI 入口 ==============

def main() -> int:
    """CLI 入口:从 stdin 读 content + file_path,从 argv 读 --level。

    使用方式:
        echo '{"file_path":"foo.py","content":"..."}' | python check_no_ref_words.py --level=ERROR

    Returns:
        退出码:0 = 合规;2 = 有 ERROR 级违规(触发 confirm UI);1 = 自身错误
    """
    parser = argparse.ArgumentParser(
        description="mcpowers 通用禁用字眼检测（v4.3.0+ 智能二分）"
    )
    parser.add_argument(
        "--level",
        choices=("ERROR", "WARNING", "INFO"),
        default="ERROR",
        help="违规阈值级别:ERROR=阻断;WARNING=提示;INFO=仅记录",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出违规列表",
    )
    args = parser.parse_args()

    try:
        raw = sys.stdin.read()
        if not raw:
            return 0
        payload = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return 1

    # 兼容 Claude Code hook 嵌套结构:{"tool_name":"Write","tool_input":{"file_path":"...","content":"..."}}
    # 同时支持简单结构:{"file_path":"...","content":"..."}（便于单测 / 调试）
    if "tool_input" in payload and isinstance(payload["tool_input"], dict):
        payload = payload["tool_input"]

    file_path = payload.get("file_path", "")
    # v4.5.2+ 兼容 Edit/MultiEdit 三种工具的 stdin JSON 形状:
    #   Write:      {"file_path":"...","content":"..."}
    #   Edit:       {"file_path":"...","old_string":"...","new_string":"..."}
    #   MultiEdit:  {"file_path":"...","edits":[{"old_string":"...","new_string":"..."}, ...]}
    # 优先走 Write 的 content 字段(原行为不变);否则 Edit 的 new_string;否则 MultiEdit 拼接所有 edits[*].new_string。
    # 任何一种都无法抽出可扫描内容 → content 留空 → main() 后续 return 0 放行(与原行为一致)。
    if "content" in payload and isinstance(payload["content"], str):
        content = payload["content"]
    elif "new_string" in payload and isinstance(payload["new_string"], str):
        content = payload["new_string"]
    elif "edits" in payload and isinstance(payload["edits"], list):
        parts = [
            e["new_string"]
            for e in payload["edits"]
            if isinstance(e, dict) and isinstance(e.get("new_string"), str)
        ]
        content = "\n".join(parts)
    else:
        # 兜底:直传 {"file_path":"...","content":"..."} 的单测场景
        content = payload.get("content", "")

    if not content:
        return 0

    violations = scan_content(content, file_path=file_path)
    has_blocking = any(v.level == "ERROR" for v in violations)

    if args.json:
        output = {
            "file_path": file_path,
            "violations": [
                {
                    "line_no": v.line_no,
                    "level": v.level,
                    "category": v.category,
                    "word": v.word,
                    "message": v.message,
                }
                for v in violations
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for v in violations:
            print(f"  ❌ [{v.category}] L{v.line_no}: {v.message}", file=sys.stderr)

    if args.level == "ERROR" and has_blocking:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())