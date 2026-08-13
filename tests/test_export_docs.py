#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""export_docs.py 表格排版错乱防护 — 单元测试 (v2.1+ 精简版)

覆盖两类核心防护:
  1. _md_cell_safe() 4 步走(规范 / 不可见字符 / Markdown 转义 / 危险结构)
  2. _scan_xss_risk() 严重风险阻断命中

设计原则(YAGNI):
- 8-12 个核心用例覆盖 80% 真实场景,不在边界枚举上过度堆砌
- 不依赖 Flask / pytest 框架 —— 仅用 stdlib unittest + 直接 import 模块
- 路径注入:把 tools 目录加进 sys.path 后直接 import export_docs
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


# 把 tools 目录加进 path,直接 import 模块
TOOLS_DIR = Path(__file__).resolve().parent.parent / 'skills' / 'mcpowers-shared' / 'tools'
sys.path.insert(0, str(TOOLS_DIR))

import export_docs  # noqa: E402


class TestMdCellSafeNormalize(unittest.TestCase):
    """_md_cell_safe 第 1 步:规范化(None / dict / list / 非 str / 前后空白)"""

    def test_none_returns_empty_string(self):
        self.assertEqual(export_docs._md_cell_safe(None), '')

    def test_dict_serialized_to_json(self):
        self.assertEqual(export_docs._md_cell_safe({'a': 1}), '{"a": 1}')

    def test_list_serialized_to_json(self):
        self.assertEqual(export_docs._md_cell_safe([1, 2, 3]), '[1, 2, 3]')

    def test_int_coerced_to_string(self):
        self.assertEqual(export_docs._md_cell_safe(42), '42')

    def test_strip_leading_trailing_whitespace(self):
        self.assertEqual(export_docs._md_cell_safe('  hello  '), 'hello')


class TestMdCellSafeInvisibleChars(unittest.TestCase):
    """_md_cell_safe 第 2 步:不可见字符清理"""

    def test_nbsp_to_regular_space(self):
        # NBSP   → 常规空格
        self.assertEqual(export_docs._md_cell_safe('a b'), 'a b')

    def test_zwsp_removed(self):
        # ZWSP ​ → 删除
        self.assertEqual(export_docs._md_cell_safe('hello​world'), 'helloworld')

    def test_bom_removed(self):
        # BOM ﻿ → 删除
        self.assertEqual(export_docs._md_cell_safe('﻿hello'), 'hello')

    def test_mixed_invisible_chars(self):
        # 多个不可见字符混合
        self.assertEqual(
            export_docs._md_cell_safe('a b​c﻿d'),
            'a bcd',
        )


class TestMdCellSafeMarkdownEscape(unittest.TestCase):
    """_md_cell_safe 第 3 步:Markdown 转义(反斜杠 / `|` / 换行)"""

    def test_pipe_escaped(self):
        # 单元格里的 | 必须转义为 \|,否则破坏列数
        self.assertEqual(export_docs._md_cell_safe('hello|world'), 'hello\\|world')

    def test_newline_to_br(self):
        # \n → <br>(GFM 表格内换行标准)
        self.assertEqual(export_docs._md_cell_safe('line1\nline2'), 'line1<br>line2')

    def test_crlf_to_br(self):
        self.assertEqual(export_docs._md_cell_safe('line1\r\nline2'), 'line1<br>line2')

    def test_backslash_escaped(self):
        # 反斜杠 → 双反斜杠(避免与 | 的转义冲突)
        self.assertEqual(export_docs._md_cell_safe('a\\b'), 'a\\\\b')

    def test_pipe_and_newline_combined(self):
        # 真实场景:description 含 | 与 \n
        result = export_docs._md_cell_safe('枚举: A|B|C\n详情')
        self.assertIn('\\|', result)
        self.assertIn('<br>', result)


class TestMdCellSafeDangerStruct(unittest.TestCase):
    """_md_cell_safe 第 4 步:危险结构防御(HTML / 表格分隔行 / 列表 / 标题)"""

    def test_html_tag_stripped(self):
        # <b> 等非白名单 HTML 标签被剥离
        self.assertEqual(export_docs._md_cell_safe('<b>strong</b> text'), 'strong text')

    def test_br_tag_preserved(self):
        # <br> 是 GFM 表格换行的标准,白名单保留
        self.assertEqual(export_docs._md_cell_safe('see <br>here'), 'see <br>here')

    def test_table_separator_replaced(self):
        # |--- / |:--: 等冒充分隔行的模式 → 顺号
        result = export_docs._md_cell_safe('---|---')
        self.assertIn('—', result)
        self.assertNotIn('|', result)

    def test_list_prefix_stripped(self):
        # 行首 - item 列表前缀 → 空格
        result = export_docs._md_cell_safe('- item').strip()
        self.assertEqual(result, 'item')

    def test_ordered_list_prefix_stripped(self):
        result = export_docs._md_cell_safe('1. item').strip()
        self.assertEqual(result, 'item')

    def test_heading_prefix_stripped(self):
        result = export_docs._md_cell_safe('## title').strip()
        self.assertEqual(result, 'title')

    def test_code_fence_removed(self):
        # 内嵌代码块围栏 ```python → 单 `
        result = export_docs._md_cell_safe('示例: ```python\nprint(1)\n```')
        self.assertNotIn('```', result)


class TestScanXssRisk(unittest.TestCase):
    """_scan_xss_risk 严重风险检测"""

    def _make_spec(self, description: str) -> dict:
        return {
            'paths': {
                '/x': {
                    'post': {
                        'tags': ['A'],
                        'summary': 's',
                        'description': description,
                        'parameters': [],
                        'responses': {'200': {}},
                    }
                }
            }
        }

    def test_clean_description_no_violation(self):
        spec = self._make_spec('normal description without xss')
        self.assertEqual(export_docs._scan_xss_risk(spec), [])

    def test_script_tag_detected(self):
        spec = self._make_spec('<script>alert(1)</script>')
        violations = export_docs._scan_xss_risk(spec)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0][1], 'POST')
        self.assertIn('script 标签', violations[0][2])

    def test_iframe_tag_detected(self):
        spec = self._make_spec('iframe 注入: <iframe src="evil.com"></iframe>')
        violations = export_docs._scan_xss_risk(spec)
        self.assertEqual(len(violations), 1)
        self.assertIn('iframe 标签', violations[0][2])

    def test_javascript_url_detected(self):
        spec = self._make_spec('点击 [here](javascript:alert(1))')
        violations = export_docs._scan_xss_risk(spec)
        self.assertEqual(len(violations), 1)
        self.assertIn('javascript', violations[0][2])

    def test_event_handler_detected(self):
        spec = self._make_spec('onclick 处理器: onclick="alert(1)"')
        violations = export_docs._scan_xss_risk(spec)
        self.assertEqual(len(violations), 1)
        self.assertIn('事件处理器', violations[0][2])

    def test_data_html_url_detected(self):
        spec = self._make_spec('data url: data:text/html,<script>alert(1)</script>')
        violations = export_docs._scan_xss_risk(spec)
        self.assertGreaterEqual(len(violations), 1)

    def test_clean_spec_with_complex_description(self):
        # 含 `|` 和换行符的正常 description 不应误报
        spec = self._make_spec('枚举: A|B|C\n详情说明')
        self.assertEqual(export_docs._scan_xss_risk(spec), [])


class TestMdCellSafeEndToEnd(unittest.TestCase):
    """_md_cell_safe 真实场景:组合多个破坏源"""

    def test_word_copied_text_with_nbsp_and_pipes(self):
        # 从 Word 拷贝的文本常常含 NBSP + `|`
        result = export_docs._md_cell_safe('  用户角色: 管理员|编辑|访客  ')
        # NBSP → 空格,首尾空白 strip, | 转义
        self.assertEqual(result, '用户角色: 管理员\\|编辑\\|访客')

    def test_multiline_description_with_html(self):
        result = export_docs._md_cell_safe('参数说明\n详见 <b>文档</b>')
        # \n → <br>, <b> 剥离
        self.assertEqual(result, '参数说明<br>详见 文档')

    def test_complex_markdown_injection(self):
        # 模拟 description 同时含 |、\n、表格分隔行、HTML 标签
        result = export_docs._md_cell_safe(
            '详情:\n| col1 | col2 |\n| --- | --- |\n<b>text</b>'
        )
        # 不应含连续的 |--- 模式(分隔行冒充)
        self.assertNotIn('|---', result)
        # <b> 已剥离
        self.assertNotIn('<b>', result)
        # 换行 → <br>
        self.assertIn('<br>', result)


if __name__ == '__main__':
    unittest.main()
