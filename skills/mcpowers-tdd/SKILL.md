---
name: mcpowers-tdd
description: 写代码 / 修 bug 时强制 TDD 循环：先写失败的测试 → 写最少的代码使测试通过 → 重构。被 `mcpowers-feat` / `mcpowers-bugfix` 调用。
---

# mcpowers-tdd（强制 TDD）

> 借鉴自 superpowers `test-driven-development`。
> **铁律**：NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST（没失败的测试，不写生产代码）。

---

## 触发即执行（RED-GREEN-REFACTOR 循环）

### Step 1：RED（写失败的测试）
1. 想清楚要测试什么行为
2. 写一个**最简单**的失败测试
3. **运行测试，确认它失败**（看到红色 / FAIL）
4. 失败原因要符合预期（"功能未实现"，而不是"测试代码写错"）

**禁止**：
- ❌ 没看到测试失败就写实现
- ❌ 一次性写 10 个测试再开始
- ❌ 测试写得过于复杂（一个测试测一个行为）

### Step 2：GREEN（写最少代码使测试通过）
1. 写**最少**的代码使测试通过
2. **禁止**在 GREEN 阶段做"顺手优化"
3. **运行测试，确认它通过**（看到绿色 / PASS）
4. 禁止看到绿就跳到下一项，先看测试是否真的覆盖了行为

### Step 3：REFACTOR（清理）
1. 测试通过后，重构代码（不改行为）
2. 重构后**再跑一遍测试**，确保还是绿的
3. 重构要点：
   - 消除重复（DRY）
   - 提升可读性
   - 改善命名
   - 抽离小函数

### 循环
对每个行为：RED → GREEN → REFACTOR → 下一个行为

---

## 加载规范
- Read `mcpowers-shared/mcpowers-spec-index/SKILL.md`
- 加载：
  - `mcpowers-shared/docs/技术规范/测试规范.md`（**必读**）
  - `mcpowers-shared/docs/技术规范/代码规范.md`（SOLID/KISS/DRY/YAGNI）

---

## Bug 修复专用流程

修 bug 时：
1. **先写一个能复现 bug 的失败测试**（这就是 RED）
2. 看到测试失败（确认能复现）
3. 修代码使测试通过（GREEN）
4. 重构（如有需要）

这样保证 bug 不会回归。

---

## 反模式（禁止）

- ❌ 先写实现再补测试（不是 TDD）
- ❌ 测试代码写得很复杂（无法判断失败原因）
- ❌ 多个行为塞一个测试
- ❌ 看到测试通过就跳过 REFACTOR
- ❌ 测试覆盖率造假（mock 掉所有真实逻辑）

---

## 何时跳过 TDD

- 纯 UI 调整（颜色、文案、布局）
- 配置文件调整
- 文档修改
- 紧急 hotfix（**仍要补测试**，但可后补）

> **注意**：跳过 TDD 是例外，**不是常态**。每次跳过要说明理由。
