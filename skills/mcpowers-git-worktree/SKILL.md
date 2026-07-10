---
name: mcpowers-git-worktree
description: |
  我要并行开发两个分支 / 想在不同目录同时改 / 切分支太麻烦了 / 帮我用 worktree / 在新目录开一个新分支 → 触发本技能。

  也覆盖："并行开发"、"分支隔离"、"独立工作区"、"git worktree"、"多分支并行"、"新目录开发"、"开 worktree"、"另一个分支开发"、"worktree 一下"、"隔离分支"。

  利用 Git worktree 在不同目录并行开发多个分支，避免频繁切换。覆盖 create / list / switch / remove 四种操作。
---

# mcpowers-git-worktree（worktree 隔离开发）

> 借鉴 superpowers `using-git-worktrees`。
> **核心**：worktree 让多分支并行开发互不干扰。

---

## 编排

本技能为**元操作**，不编排方法层技能。直接执行 git worktree 子命令。

| 步骤 | 调用对象 | 触发条件 |
|:-----|:---------|:---------|
| 1 | `git worktree <subcmd>` | 用户确认子命令（create/list/switch/remove） |

**保护路径**：本技能触发后，所有 Write/Edit 操作的"## 编排"段视为已确认，不再二次询问。

**铁律**：删除 worktree 前必须确认无未提交变更；禁止"用 worktree 改完忘了合并"。

---

## 触发即执行

### 1. 加载规范
- Read `mcpowers-shared/docs/技术规范/Git规范.md`

### 2. 识别操作类型

根据用户输入识别：

| 用户说 | 操作 |
|:-------|:-----|
| "建个 worktree" / "新建工作区" | **create** |
| "看看有哪些 worktree" | **list** |
| "切换到 xxx worktree" | **switch** |
| "删除 worktree" / "清理" | **remove** |

未明确 → 列出选项让用户选。

---

## 操作 1：create（创建 worktree）

### 用途
- 隔离开发：在大改动时不污染当前分支
- 并行开发：同时维护多个功能分支
- AI 多任务：AI 可以同时在多个 worktree 处理不同任务

### 步骤

1. **确认当前状态**
   ```bash
   git status
   # 确保无未提交变更（提示用户先 commit）
   ```

2. **创建 worktree**
   ```bash
   # 方式 A：基于现有分支创建新 worktree
   git worktree add ../<project>-<branch> <branch>

   # 方式 B：基于现有分支创建新分支 + 新 worktree
   git worktree add -b <new-branch> ../<project>-<new-branch> <base-branch>

   # 方式 C：基于具体 commit 创建
   git worktree add -b <new-branch> ../<project>-<new-branch> <commit-sha>
   ```

3. **验证**
   ```bash
   git worktree list
   ```

4. **进入新 worktree 工作**
   ```bash
   cd ../<project>-<new-branch>
   ```

### 命名规范
- 目录名：`<项目名>-<分支名>` 或 `<分支名>`
- 分支名：`feat/xxx`、`fix/xxx`、`refactor/xxx` 等

---

## 操作 2：list（列出 worktree）

```bash
git worktree list
```

输出格式：
```
/path/to/main            abc1234 [main]
/path/to/feature-xyz     def5678 [feat/xyz]
```

向用户报告当前所有 worktree 状态。

---

## 操作 3：switch（切换 worktree）

注意：**worktree 不是用来"切换"的**，每个 worktree 绑定一个分支。

如需"切换"到其他 worktree 工作：
```bash
# 在文件管理器中打开
open ../<project>-<branch>   # macOS
explorer.exe ../<project>-<branch>  # Windows
code ../<project>-<branch>   # VS Code

# 或在终端 cd
cd ../<project>-<branch>
```

如需在**当前目录**切换分支（不是 worktree 概念）：
```bash
git checkout <branch>
```

---

## 操作 4：remove（删除 worktree）

### 普通删除（分支已合并）
```bash
git worktree remove ../<project>-<branch>
```

### 强制删除（分支未合并，会丢改动）
```bash
git worktree remove --force ../<project>-<branch>
```

### 清理悬空 worktree 记录
```bash
git worktree prune
```

### 删除分支本身
```bash
git branch -d <branch>      # 已合并
git branch -D <branch>      # 强制
```

---

## 何时中断并询问用户

- 当前有未提交变更 → 提示先 commit
- 要删除有未提交改动的 worktree → 警告并确认
- 不确定要建在哪个目录下 → 询问
- 基于哪个分支创建 → 询问

---

## 反模式（禁止）

- ❌ 在 worktree 里 clone（worktree 不是独立仓库）
- ❌ 在 worktree 里再 worktree（嵌套）
- ❌ 删除 worktree 时丢未提交改动（先 commit 或备份）
- ❌ 长期维护大量 worktree（应定期清理）
- ❌ 在 main/master 上直接 worktree（应基于 feat/fix 分支）

---

## 完成后自检清单

- [ ] 操作类型已确认（create/list/switch/remove）
- [ ] 命令已正确执行
- [ ] git worktree list 输出符合预期
- [ ] 报告已给用户（含路径、分支、状态）
