---
name: mcpowers-git-cleanBranches
description: 用户要"清理分支/删除分支/整理分支"时触发。清理已合并分支和远程已删的跟踪分支。**默认 dry-run 模式**（只列出待删分支，不实际删除），防止误删。
---

# mcpowers-git-cleanBranches（清理无用分支）

> **核心**：默认 dry-run（只列待删），确认后才删除。防误删是第一原则。

---

## 编排

本技能为**元操作**，不编排方法层技能。直接执行 git branch 命令。

| 步骤 | 调用对象 | 触发条件 |
|:-----|:---------|:---------|
| 1 | `git branch -d`（已合并） | dry-run 列出后用户确认 |
| 2 | `git branch -D`（未合并） | 用户明确选 -D（需二次确认） |
| 3 | `git remote prune` | 同步远程已删分支 |

**保护路径**：本技能触发后，所有 Write/Edit 操作的"## 编排"段视为已确认，不再二次询问。

**铁律**：默认 dry-run（只列不删）；禁止不区分已合并/未合并直接 -D。

---

## 触发即执行

### 1. 加载规范
- Read `mcpowers-shared/docs/技术规范/Git规范.md`

### 2. 拉取最新远程信息

```bash
git fetch -p
```

`fetch -p` 会清理远程已删除的跟踪分支。

### 3. 列出待清理分支（dry-run 模式）

#### 类别 A：本地已合并分支
```bash
# 列出已合并到 main 的本地分支（排除 main/master/develop）
git branch --merged main | grep -vE '^\s*(\*|main|master|develop)$'
```

#### 类别 B：远程已删的本地跟踪分支
```bash
# 找出远程已删但本地还跟踪的分支
git branch -vv | grep ': gone]' | awk '{print $1}'
```

#### 类别 C：未合并的本地分支
```bash
# 列出未合并的分支（**需用户特别确认才能删**）
git branch --no-merged main
```

### 4. 输出清理报告

向用户展示：

```
## 清理分支报告

### A. 本地已合并分支（可安全删除）
- feat/user-auth（合并到 main，3 周前）
- fix/login-bug（合并到 main，1 周前）
- docs/api-update（合并到 main，昨天）

### B. 远程已删的跟踪分支（可安全删除）
- feat/old-feature（远程已删）
- chore/deprecated（远程已删）

### C. 未合并的本地分支（**需确认**）
- feat/wip-experiment（未合并，含 5 个未推送 commit）
- refactor/draft（未合并）

总计：5 个可安全删除，2 个需确认
```

### 5. 询问删除策略

询问用户：
- 删除 A + B（安全，推荐）？
- 删除 C（未合并，需逐一确认）？
- 全部跳过？
- 指定要删的分支？

### 6. 执行删除

#### 删 A（已合并）
```bash
# 安全删除
git branch -d feat/user-auth
git branch -d fix/login-bug
```

#### 删 B（远程已删）
```bash
# 安全删除
git branch -d feat/old-feature
```

或批量：
```bash
git branch -vv | grep ': gone]' | awk '{print $1}' | xargs git branch -d
```

#### 删 C（未合并）
```bash
# 强制删除（**需用户对每个分支逐一确认**）
git branch -D feat/wip-experiment
```

#### 删远程分支（可选）
```bash
# 删远程分支（**慎用**，影响他人）
git push origin --delete <branch>
```

### 7. 验证
```bash
git branch -a
git fetch -p
```

确认清理生效。

---

## 危险操作确认

执行 `branch -D`（强制删除未合并）前：
```
⚠️ 危险操作！
分支 feat/wip-experiment 未合并到任何分支
包含 5 个未推送 commit
删除将**永久丢失**这些 commit

请确认是否继续？[需要明确的"是"、"确认"、"继续"]
```

执行 `push --delete`（删远程分支）前：
```
⚠️ 危险操作！
删除远程分支 feat/xxx 会影响其他协作者
其他人的 fork 和 clone 仍会保留该分支，但不便追踪

请确认是否继续？[需要明确的"是"、"确认"、"继续"]
```

---

## 保留规则（强制）

**以下分支永远不删**：
- ❌ `main` / `master`
- ❌ `develop`（如果用 Git Flow）
- ❌ 当前所在分支
- ❌ 用户在配置文件中标记为保护的分支

**未合并分支不删除非**：
- 用户明确指定
- 用户明确知道会丢 commit
- 二次确认完成

---

## 何时中断并询问用户

- 待删分支包含未合并 commit → 警告
- 远程分支删除 → 二次确认
- 当前在要删的分支上 → 提示先切换
- 待删分支超过 20 个 → 分批确认

---

## 反模式（禁止）

- ❌ 跳过 dry-run 直接删除
- ❌ 删 main / master / develop
- ❌ 删未合并分支不确认
- ❌ 删远程分支不通知团队
- ❌ 用 `git branch | xargs git branch -D`（太暴力）
- ❌ 删之前不打 tag 备份（重要分支可先 `git tag backup/<name>`）

---

## 完成后自检清单

- [ ] 已 fetch -p（远程信息最新）
- [ ] 已分三类列待删分支
- [ ] dry-run 报告已给用户
- [ ] 删除策略已确认
- [ ] 危险操作已二次确认
- [ ] 命令已正确执行
- [ ] git branch -a 验证清理生效
- [ ] 报告已给用户
