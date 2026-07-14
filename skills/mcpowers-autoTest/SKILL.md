---
name: mcpowers-autoTest
description: "自动化测试 / 跑测试出报告 / bug 等级分类 → 触发本技能。口语：自动化测试、E2E、UI 自动化、接口自动化、全栈测试、出测试报告、bug 分级、哪一端的问题、自动化回归。中英：auto test, automated testing, e2e test, test report, bug classification, regression。边界：单测 RED-GREEN→`mcpowers-tdd`；bug 修复后单次验证→`mcpowers-bugfix` Step 5。流程：识别范围→跑测→生成二维分类报告→推荐路由→人审→修复→循环。"
---

# mcpowers-autoTest（自动化测试）

> **核心**：测试 → 二维分类报告 → 推荐修复路由 → 人审 → 修复 → 再测 → 循环
>
> **与 mcpowers-tdd / mcpowers-bugfix 的关系**：本技能用于**专门的自动化测试套件**（含全栈 web 项目的端到端测试），产出结构化报告 + 修复循环。单测循环走 `mcpowers-tdd`；bug 修复后单次验证走 `mcpowers-bugfix` Step 5。

---

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| Step 1 | 识别测试范围 | 内部 | 用户输入含"自动化测试"类关键词 | 询问用户 |
| Step 2 | 跑测试 | 内部 | 范围明确后 | 中断并报告 |
| Step 3 | 解析失败 | 内部 | 测试有失败用例 | 输出"全过"并结束 |
| Step 4 | 生成报告 | 读 `自动化测试规范.md §4` | - | 输出空报告 |
| Step 5 | 推荐修复路由 | 内部 | 报告生成后 | 默认 `mcpowers-bugfix` |
| Step 6 | 人审 | 等待 | 用户确认 | 用户可改路由 |
| Step 7 | 调用修复技能 | 路由结果 | 用户确认 | 中断 |
| Step 8 | 再测 | 回到 Step 2 | 修复完成 | 循环 ≤ 3 次 |
| Step 9 | 收尾 | 调 `mcpowers-git-commit` | 全过 | 输出报告 |

---

## 触发即执行（7 步强制流程）

### Step 1：识别测试范围

| 测试类型 | 工具栈 | 触发词 |
|:---------|:-------|:-------|
| Web UI 自动化 | Playwright | "UI 测试"、"E2E 测试"、"浏览器自动化" |
| API 自动化 | pytest + requests | "接口自动化"、"API 测试" |
| 全栈 E2E | Playwright + API 双层 | "全栈测试"、"前后端联调" |

> 💡 用户不指定时，按项目结构自动选（Flask+Vue 项目默认全栈）

### Step 2：跑测试

读取 `mcpowers-shared/mcpowers-spec-index/SKILL.md` → 加载规范：
- `自动化测试规范.md` §1 工具选型 + §2 命名约定
- `测试规范.md` §5 测试执行 + §5.1 覆盖率目标

按命名约定执行：`at_*.py`（pytest）/ `at_*.spec.ts`（Playwright）

### Step 3：解析失败用例

按 `自动化测试规范.md §4.2` 字段提取：test_id / error_message / stack_trace / file_location

### Step 4：生成二维分类报告（强制）

按 `自动化测试规范.md §4` JSON schema 输出：
- `severity`：P0 / P1 / P2 / P3（按 §3.1 判定）
- `owner`：frontend / backend / database / config / cache / thirdparty / infra / unknown（按 §3.3 规则）

**铁律**：失败用例**必须**有 owner 字段；无法判断时标 `unknown` 并标红等待人审

### Step 5：推荐修复路由

按 `自动化测试规范.md §5.1` 路由表自动推荐，输出 Markdown 摘要（§4.3 模板）供人审

### Step 6：人审路由

列出所有报告 + 推荐路由，等待用户选择：

- ✅ 接受 AI 推荐 → 自动调用
- 🔄 改路由 → 用户指定
- ⏸ 暂停 → 暂不修复
- ❌ 终止 → 退出循环

### Step 7：循环再测

修复后回到 Step 2 重新跑测试，直到全过或达到修复上限（3 次）或用户中断。

---

## 何时中断并询问用户

- 测试范围不明（Web UI vs API vs 全栈）
- owner 无法判断（标 `unknown`）
- 失败用例 > 10 个（建议分批）
- 修复循环已达 3 次
- 路由冲突（一条失败横跨多端）

## 反模式（禁止）

- ❌ 不生成结构化报告直接给修复建议
- ❌ 跳过严重度判断
- ❌ owner 标 `unknown` 后直接推荐 `mcpowers-bugfix`
- ❌ 一次性修完所有 bug 不再测
- ❌ 在生产数据库跑自动化测试
- ❌ 绕过"AI 推荐 → 人审"两步强行自动调用

## 完成后自检清单

- [ ] 报告 JSON schema 完整（每条失败有 `severity` + `owner`）
- [ ] 严重度判断有依据（不是瞎标）
- [ ] 路由推荐有证据（错误位置 → owner）
- [ ] 人审后调用对应技能
- [ ] 修复后重新跑测试（循环闭合）
- [ ] 测试数据按 §7 清理（test_/tmp_/at_ 前缀）

---

## 附录：相关文档

| 文档 | 位置 |
|:-----|:-----|
| 自动化测试规范 | `mcpowers-shared/docs/技术规范/自动化测试规范.md` |
| 测试规范 | `mcpowers-shared/docs/技术规范/测试规范.md` |
| 规范索引 | `mcpowers-shared/mcpowers-spec-index/SKILL.md` |
| bug 修复 | `mcpowers-bugfix/SKILL.md` |
| TDD | `mcpowers-tdd/SKILL.md` |