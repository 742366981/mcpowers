---
name: mcpowers-git-commit
description: 用户要"提交/commit"时触发。按 Git 规范执行：检查 .gitignore → 明确文件 → 类型前缀 → 立即 commit。覆盖所有代码/文档/配置变更。被 `mcpowers-feat` / `mcpowers-bugfix` 等场景技能在收尾时调用。
---

# mcpowers-git-commit（规范化 commit）

> 完全遵循 `mcpowers-shared/docs/技术规范/Git规范.md`。
> **核心**：每次操作后立即 commit，不攒 commit，不漏 commit。

---

## 编排

本技能为**元操作**，不编排方法层技能。直接执行 git commit。

| 步骤 | 调用对象 | 触发条件 |
|:-----|:---------|:---------|
| 1 | 规范（`Git规范.md`） | 必读 |
| 2 | `git add` + `git commit` | 用户确认后 |

**保护路径**：本技能触发后，所有 Write/Edit 操作的"## 编排"段视为已确认，不再二次询问。

**铁律**：不攒 commit、不漏 commit、代码和文档同 commit。

---

## 触发即执行

### 1. 加载规范
- Read `mcpowers-shared/docs/技术规范/Git规范.md`（**必读**）

### 2. 检查 .gitignore（HARD-GATE）

```bash
# 检查 .gitignore 是否存在
[ -f .gitignore ] || echo "❌ .gitignore 不存在，需要先创建"
```

- **不存在** → 按 Git 规范附录模板创建后再继续
- **存在** → 检查内容是否完整
  - 是否包含 `temp/`、`__pycache__/`、`.env`、`*.log` 等关键规则
  - 缺则补充

### 3. 查看变更

```bash
git status -s
```

**判断**：
- 无变更 → 提示"无变更可提交"，退出
- 有变更 → 继续

### 4. 明确指定文件（强制）
- ❌ 禁止 `git add .` / `git add *` / `git add -A`
- ✅ 明确指定要提交的文件：
  ```bash
  git add src/api/user.py
  git add docs/api.md
  git add README.md
  ```
- **逐项检查**每个文件是否应该提交（不应该是 .env、临时文件等）

### 5. 选择 commit 类型
按 `Git规范.md` 第 3 节：

| 类型 | 场景 | 示例 |
|:-----|:-----|:-----|
| `feat` | 新增功能 | `feat: 完成用户模块创建` |
| `fix` | 修复 bug | `fix: 修复登录错误` |
| `refactor` | 重构 | `refactor: 重构用户模块结构` |
| `docs` | 文档 | `docs: 更新 API 文档` |
| `config` | 配置 | `config: 调整数据库连接` |
| `test` | 测试 | `test: 添加用户模块单测` |
| `chore` | 杂项 | `chore: 清理临时文件` |

### 6. 生成 commit message

格式：
```
<类型>: <简短描述>

可选的详细说明（超过一行时使用）
```

**好的示例**：
- `feat: 完成用户模块模型、视图和 API 接口`
- `fix: 修复导入时字段获取错误的 bug`
- `docs: 更新 API 文档示例`

**差的示例（禁止）**：
- ❌ `update`（太模糊）
- ❌ `fix bug`（不完整）
- ❌ `changes`（不知道改了什么）

### 7. 执行 commit

```bash
git commit -m "<类型>: <描述>"
```

### 8. 验证
```bash
git log --oneline -1
```

确认 commit 已成功创建。

---

## 收尾报告

向用户报告：
- 提交了哪些文件
- commit message 内容
- 当前 HEAD hash

---

## 何时中断并询问用户

- 变更文件较多（> 10 个）→ 询问是否拆分为多个 commit
- 涉及敏感信息（看起来是 .env / 密钥）→ 警告并询问
- commit message 候选不止一个明显合适的类型 → 询问用户选哪个
- 当前在 main/master 分支 → 警告"建议在功能分支提交"

---

## 反模式（禁止）

- ❌ 跳过 .gitignore 检查
- ❌ `git add .` / `git add *`（必须明确文件）
- ❌ 一次 commit 多个独立任务（应拆分）
- ❌ 模糊的 commit message（"update"/"fix"/"changes"）
- ❌ 提交敏感信息（.env / 密钥 / 密码）
- ❌ 多个操作后才 commit（每个独立任务完成后立即 commit）
- ❌ 只 commit 代码不 commit 文档（代码和文档必须同 commit）

---

## 完成后自检清单

- [ ] .gitignore 已检查且完整
- [ ] 已明确指定要提交的文件（无 `git add .`）
- [ ] commit message 有类型前缀
- [ ] commit message 描述具体
- [ ] commit 已成功创建
- [ ] 报告已给用户
