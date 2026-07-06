---
name: mcpowers-refactor
description: 用户要"重构/抽离/拆分/太乱/抽象/整理代码"时触发。保行为重构：先固化测试 → 小步改 → 每步验证。禁止"顺手优化"导致行为变化。
---

# mcpowers-refactor（重构）

> 借鉴自 superpowers（TDD 保护网思想）。
> **核心**：行为不变，只改结构。**没有测试保护网不做重构**。

---

## 触发即执行

### 1. 加载规范
- Read `mcpowers-shared/mcpowers-spec-index/SKILL.md`
- 加载：
  - `mcpowers-shared/docs/技术规范/代码规范.md`（**必读**，SOLID/KISS/DRY/YAGNI）
  - `mcpowers-shared/docs/技术规范/代码同步修改规范.md`（**必读**）
  - 对应栈规范

### 2. 评估测试覆盖（HARD-GATE）
- 检查目标代码**是否有测试**
- 测试覆盖**不足** → 调 `mcpowers-tdd` **先补测试**
- 测试覆盖足够 → 进入第 3 步
- **禁止**没有测试保护网就重构（改了不知道改没改对）

### 3. 识别重构目标
按代码异味分类：

| 代码异味 | 重构手法 |
|:---------|:---------|
| 长函数 | 提取函数 |
| 大类 | 拆分类 |
| 重复代码 | 提取公共部分 |
| 复杂条件 | 用多态 / 策略模式替换 |
| 紧耦合 | 依赖注入 / 接口隔离 |
| 神类（万能类） | 单一职责拆分 |
| 长参数列表 | 引入参数对象 |

### 4. 小步重构
- **每步改动都要小**（一个手法一次）
- 每步改动后**立即跑测试**
- 测试失败 → 立即回滚，不继续
- 测试通过 → 进入下一步

### 5. 完成后验证
- 全量测试通过
- 全量 lint / type check 通过
- 行为完全一致（外部接口、内部逻辑、边界情况）

---

## 重构 vs 修 bug / 加功能

| 场景 | 用什么技能 |
|:-----|:-----------|
| 改 bug | `mcpowers-bugfix` |
| 加新功能 | `mcpowers-feat` |
| 改需求 | `mcpowers-requirement-change` |
| 改结构不改行为 | `mcpowers-refactor`（本技能） |
| 修 bug 时顺手重构 | **禁止**（拆成两次：先 bugfix 后 refactor） |

---

## 反模式（禁止）

- ❌ 没测试就重构
- ❌ 重构时改行为（这是 bugfix 不是 refactor）
- ❌ 一步到位大改（应小步）
- ❌ 改完不跑测试
- ❌ 顺手"优化"无关代码
- ❌ 重构和加功能混在一起

---

## 收尾

- 调 `mcpowers-code-review` 自审
- 调 `mcpowers-git-commit` 提交
- commit 信息：`refactor(模块): 简要说明`（用 `refactor` 而非 `feat`/`fix`）
