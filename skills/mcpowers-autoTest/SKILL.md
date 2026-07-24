---
name: mcpowers-autoTest
description: "自动化测试 / 自动化回归 / E2E / UI 自动化 / 接口自动化 / 测试报告与 bug 分类 → 触发本技能。口语：跑自动化、跑回归、跑 UI、跑接口、跑全栈、出报告、分级、定位哪一端。中英：auto test, automated testing, E2E, regression, Playwright, DrissionPage, Selenium, pytest, Cypress。默认：新增自动化用 Python + pytest；先查项目测试文件、依赖、配置、CI，再沿用已有框架；无证据才选 Python 默认。边界：单测 RED-GREEN→`mcpowers-tdd`；bug 修复后单次验证→`mcpowers-bugfix` Step 5；OpenAPI/spec 生成→`mcpowers-api-contract`；性能方案→`mcpowers-optimize`。流程：证据侦察→选范围与框架→跑测→报告→路由→人审→修复→再测。"
---

# mcpowers-autoTest（自动化测试）

> **核心**：证据侦察 → 选范围与框架 → 测试 → 二维分类报告 → 推荐修复路由 → 人审 → 修复 → 再测 → 循环
>
> **与 mcpowers-tdd / mcpowers-bugfix 的关系**：本技能用于**已有或明确要运行的自动化测试套件**（含全栈 Web 项目的端到端测试），产出结构化报告 + 修复循环。新增单测的 RED-GREEN 循环走 `mcpowers-tdd`；bug 修复后最小一次验证走 `mcpowers-bugfix` Step 5；完整自动化回归仍走本技能。

---

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| Step 0 | 项目证据侦察 | 内部 | 进入本技能后 | 证据不足时询问，不猜框架 |
| Step 1 | 识别测试范围与框架 | 内部 | 证据清单完成后 | 范围或框架冲突时询问 |
| Step 2 | 跑测试 | 内部 | 范围与命令明确后 | 中断并报告环境/命令错误 |
| Step 3 | 解析失败 | 内部 | 有失败用例 | 进入 Step 4；无失败则输出“全过”并进入 Step 9 |
| Step 4 | 生成报告 | 读 `自动化测试规范.md §4` | 有失败用例 | 输出空报告并标记报告生成失败 |
| Step 5 | 推荐修复路由 | 内部 | 报告生成后 | 默认暂停，等待人审 |
| Step 6 | 人审 | 等待 | 报告和推荐路由已列出 | 用户可改路由、暂停或终止 |
| Step 7 | 调用修复技能 | 路由结果 | 用户确认后 | 中断并保留报告 |
| Step 8 | 再测 | 回到 Step 2 | 修复完成后 | 循环 ≤ 3 次 |
| Step 9 | 收尾 | 用户确认后可调 `mcpowers-git-commit` | 全过且用户确认提交 | 输出报告，不擅自提交 |

---

## 触发即执行（9 步强制流程）

### Step 0：项目证据侦察（强制）

> **铁律**：AI 不得仅凭自身熟悉度选择框架。先读项目证据；没有证据时才使用 Python 默认方案。

按以下顺序检查，优先读取已有测试的真实入口，不创建第二套测试体系：

1. **用户要求**：明确指定的语言、框架、测试命令最高优先。
2. **已有测试套件**：测试文件、公共 fixture、配置文件、CI 测试步骤。
3. **依赖和脚本**：`requirements*.txt`、`pyproject.toml`、`pytest.ini`、`package.json`、锁文件、`Makefile`、`scripts/`。
4. **项目技术栈**：仅作为无测试证据时的辅助判断，不能单独决定框架。

证据分级：

| 级别 | 证据 | 行为 |
|:-----|:-----|:-----|
| 🎯 已确认 | 现有测试导入、配置文件、CI/脚本已有执行命令 | 沿用该框架 |
| ⚠️ 高概率 | 依赖或运行脚本存在，但没有对应测试文件 | 可推荐，执行前向用户展示依据 |
| ❓ 默认 | 没有框架证据 | 采用 Python 默认，并等待用户确认创建/安装 |

**选择优先级**：用户明确指定 > 已有测试套件 > 项目证据推断 > Python 默认。执行已有测试时不迁移；新增测试时优先扩展项目已有体系，只有用户明确要求才另起语言或框架。

### Step 1：识别测试范围与框架

#### 1.1 功能自动化范围

| 测试类型 | Python 默认组合 | 证据或显式指定时的适配 | 触发词 |
|:---------|:-----------------|:-----------------------|:-------|
| Web UI 自动化 | `pytest + Playwright-Python` | `pytest + DrissionPage`（已有依赖/导入、浏览器接管或国内站点）；Selenium-Python、Playwright-Node、Cypress 沿用已有套件或用户指定 | UI 测试、E2E、浏览器自动化、页面回归 |
| API 自动化 | `pytest + requests` | 异步场景用 `pytest-asyncio + httpx/aiohttp`；已有 unittest、Robot、Supertest 等沿用 | 接口自动化、API 测试、接口回归 |
| 全栈 E2E | Python API + `Playwright-Python` | 按项目已有 API/UI 框架分层执行，不强行统一 | 全栈测试、前后端联调、业务链路回归 |

#### 1.2 专项工具识别（明确要求或项目已有时执行）

| 专项 | Python 优先工具 | 其他工具 | 边界 |
|:-----|:----------------|:---------|:-----|
| OpenAPI 契约 / Fuzz | Schemathesis | Dredd / Newman | 方案生成走 `mcpowers-api-contract`，本技能负责汇总报告 |
| 移动端 | Appium-Python-Client | Detox / Maestro / Appium 其他语言绑定 | 需要明确设备/模拟器环境 |
| 性能测试 | Locust | k6 / JMeter | 压测方案与性能优化走 `mcpowers-optimize` |

专项测试未明确范围、报告格式或环境时，先询问，不把它们静默套入当前 `webui/api/fullstack` 报告。

> **DrissionPage 选择规则**：用户明确指定、项目已有 DrissionPage 依赖/导入/fixture，或明确要求接管本机浏览器、测试国内站点时优先；普通新建 Web UI 测试无上述证据时仍默认 Playwright-Python。

#### 1.3 执行前推荐卡片（强制）

跑测或创建测试前，先输出：

```text
## 自动化测试框架推荐
- 测试范围：Web UI / API / 全栈
- 语言：Python
- 测试运行器：pytest
- 浏览器驱动或 HTTP 客户端：Playwright-Python / DrissionPage / requests
- 选择依据：具体文件、依赖、配置或 CI 命令
- 置信度：🎯 已确认 / ⚠️ 高概率 / ❓ 默认
- 执行命令：项目现有命令或拟执行命令
- 回退方案：证据冲突时暂停并询问，不自动换框架
```

未确认依赖是否安装时，不得擅自安装；先报告缺失项并等待用户确认。

### Step 2：跑测试

读取 `mcpowers-shared/mcpowers-spec-index/SKILL.md` → 按查表加载：

- `自动化测试规范.md` §1 工具选型、§2 命名约定
- `测试规范.md` §5 测试执行、§7.1.1 测试数据生命周期
- 涉及 OpenAPI/spec 时加载 `API契约/API测试自动生成.md`

**命名与发现规则**：

- Python + pytest 默认使用 `test_*.py` 或 `*_test.py`，逻辑测试 ID 使用 `at_{module}_{seq}`。
- 项目已经配置 `at_*.py` 时沿用其 `pytest` 配置，不擅自重命名。
- Node/TypeScript 只有选中已有或用户指定的 Node 套件时，使用 `*.spec.ts` / `*.test.ts`。

**命令选择**：优先使用 Step 0 发现的项目命令；无明确命令时才使用以下 Python 默认：

- **API 自动化**：`python -m pytest tests/at_api/ -v --tb=short --junitxml=reports/at_junit.xml`
- **Web UI - Playwright-Python**：`python -m pytest tests/at_e2e/ -v --tb=short --junitxml=reports/at_junit.xml`
- **Web UI - DrissionPage**：`python -m pytest tests/at_e2e/ -v --tb=short --junitxml=reports/at_junit.xml`
- **全栈 E2E**：先运行 API 准备数据，再按已确认的 Python 或项目原生 UI 命令验证；不默认执行 `npx playwright`。
- **Node/TypeScript 套件**：仅在 Step 0 确认后运行 `npx playwright test`、`npx cypress run` 等项目原生命令。
- **报告位置**：`reports/auto_test_{YYYYMMDD}_{HHMMSS}.json`（规范 §2 命名约定）。

### Step 3：解析失败用例

- 有失败用例：按 `自动化测试规范.md §4.2` 提取 `test_id / error_message / stack_trace / file_location`，进入 Step 4。
- 无失败用例：输出“全过”摘要，跳过报告修复循环，进入 Step 9。
- 命令、依赖或环境失败：标记为环境失败，不伪装成业务 bug，先报告并询问。

### Step 4：生成二维分类报告（强制）

按 `自动化测试规范.md §4` JSON schema 输出：

- `severity`：P0 / P1 / P2 / P3（按 §3.1 判定）
- `owner`：frontend / backend / database / config / cache / thirdparty / infra / unknown（按 §3.3 规则）
- `tool_stack`：使用明确名称，如 `pytest`、`playwright-python`、`drissionpage`、`requests`，不把客户端误写成测试框架。

**铁律**：失败用例必须有 `owner`；无法判断时标 `unknown` 并标红等待人审。

### Step 5：推荐修复路由

按 `自动化测试规范.md §5.1` 路由表推荐，输出 Markdown 摘要（§4.3 模板）供人审。OpenAPI/spec 生成问题回到 `mcpowers-api-contract`；性能问题回到 `mcpowers-optimize`；普通代码缺陷才推荐 `mcpowers-bugfix`。

### Step 6：人审路由

列出所有报告、证据和推荐路由，等待用户选择：

- ✅ 接受 AI 推荐 → 单条调用
- ✅✅ 批量接受（同 owner 一次性）→ 10+ 失败时推荐
- 🔄 改路由 → 用户指定
- ⏸ 暂停 → 暂不修复
- ❌ 终止 → 退出循环

### Step 7：调用修复技能

仅在人审确认后调用对应技能；未知 owner、第三方依赖、基础设施问题不得直接调用 `mcpowers-bugfix`。

### Step 8：循环再测

修复后回到 Step 2，直到全过、用户中断或达到 3 次修复上限。

### Step 9：收尾

输出最终报告、测试命令、选型证据、清理结果和未解决项。只有用户明确确认提交时，才调用 `mcpowers-git-commit`。

---

## 何时中断并询问用户

- 用户指定框架与项目已有套件冲突，且未说明要迁移
- 测试范围不明（Web UI、API、全栈或专项测试）
- 找不到框架证据且需要创建/安装测试套件
- 测试套件不存在（已有项目补基础设施走 `mcpowers-feat`；全新项目走 `mcpowers-init`）
- 依赖未安装、命令不可用或测试运行超时
- owner 无法判断（标 `unknown`）
- 失败用例 > 10 个（建议分批）
- 修复循环已达 3 次
- 路由冲突或一条失败横跨多端

## 反模式（禁止）

- ❌ 不做项目证据侦察，凭 AI 熟悉度选框架
- ❌ 新增自动化默认使用 Node/TypeScript，绕过 Python 默认规则
- ❌ 已有 Cypress/Node Playwright/Selenium 套件时，未经确认另建第二套
- ❌ 把 `requests`、`httpx`、`aiohttp` 当成测试运行器
- ❌ 不生成结构化报告直接给修复建议
- ❌ 跳过严重度判断
- ❌ owner 标 `unknown` 后直接推荐 `mcpowers-bugfix`
- ❌ 一次性修完所有 bug 不再测
- ❌ 在生产数据库跑自动化测试
- ❌ 未确认依赖就自动安装或修改项目配置
- ❌ 绕过“AI 推荐 → 人审”两步强行自动调用

## 完成后自检清单

- [ ] 已读取项目测试文件、依赖、配置和 CI/脚本证据
- [ ] 推荐卡片列出语言、运行器、驱动、证据、置信度和命令
- [ ] 新增自动化无明确证据时使用 Python + pytest
- [ ] DrissionPage 仅在用户指定或项目证据满足条件时使用
- [ ] 报告 JSON schema 完整（每条失败有 `severity` + `owner`）
- [ ] `tool_stack` 使用明确的运行器/驱动/客户端名称
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
| API 测试自动生成 | `mcpowers-shared/docs/API契约/API测试自动生成.md` |
| 规范索引 | `mcpowers-shared/mcpowers-spec-index/SKILL.md` |
| bug 修复 | `mcpowers-bugfix/SKILL.md` |
| TDD | `mcpowers-tdd/SKILL.md` |
| API 契约 | `mcpowers-api-contract/SKILL.md` |
| 性能优化 | `mcpowers-optimize/SKILL.md` |
