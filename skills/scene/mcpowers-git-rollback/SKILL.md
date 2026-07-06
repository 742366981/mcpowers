---
name: mcpowers-git-rollback
description: 用户要"回滚/rollback/撤销/恢复"时触发。安全回滚代码版本，区分 `git revert`（保留历史，**安全**）和 `git reset`（改历史，**危险**）。默认推荐 revert，避免破坏共享历史。
---

# mcpowers-git-rollback（安全回滚）

> 借鉴 superpowers `finishing-a-development-branch` 的回滚决策。
> **核心**：默认用 `revert`（安全），用 `reset` 前必须确认。

---

## 触发即执行

### 1. 加载规范
- Read `mcpowers-shared/docs/技术规范/Git规范.md`

### 2. 识别回滚目标

询问用户：
- 回滚到哪个版本？（commit hash / HEAD~N / 分支名 / tag）
- 范围：单个 commit / 连续多个 / 整个分支
- 是否已推送到远程？

未明确 → 列出最近 20 个 commit 让用户选：
```bash
git log --oneline -20
```

### 3. 决策：revert vs reset

**HARD-GATE：未确认前禁止执行 reset --hard**

```
决策树：
该 commit 已推送到共享分支？
├── 是 → 必须用 revert（不能用 reset，会破坏他人历史）
└── 否 →
    ├── 仅在个人本地分支？ → 可选 reset
    └── 已分享给团队？ → 用 revert
```

| 场景 | 推荐方式 | 命令 |
|:-----|:---------|:-----|
| **已推送到共享分支** | `revert` | `git revert <commit>` |
| **未推送的本地 commit** | `revert`（更安全） | `git revert <commit>` |
| **未推送且确认要丢弃** | `reset` | `git reset <commit>` |
| **彻底回到某个旧版本（不保留中间）** | `reset --hard` | **危险**，需二次确认 |
| **回滚 merge commit** | `revert -m 1` | `git revert -m 1 <merge-commit>` |

### 4. 执行回滚

#### 方式 A：revert（推荐，安全）
```bash
# 1. 确认当前状态
git status

# 2. 创建一个反向 commit
git revert <commit-hash>

# 3. 如果有冲突：
#    - 解决冲突
#    - git add <冲突文件>
#    - git revert --continue

# 4. 推送到远程
git push
```

**revert 的优势**：
- ✅ 保留完整历史
- ✅ 不破坏他人已拉取的代码
- ✅ 团队协作安全
- ✅ 可以回滚的"回滚"（revert the revert）

#### 方式 B：reset（危险）
```bash
# 1. 确认当前状态
git status

# 2. soft reset（保留改动在暂存区）
git reset --soft <commit-hash>

# 3. mixed reset（保留改动在工作区，默认）
git reset <commit-hash>

# 4. hard reset（丢弃所有改动，**最危险**）
git reset --hard <commit-hash>

# 5. 强制推送到远程（**仅限个人分支**）
git push --force
```

**reset 的风险**：
- ❌ 改写历史
- ❌ 已推送会导致他人代码冲突
- ❌ --hard 会丢失未提交改动
- ❌ --force-with-lease 也可能丢 commit

### 5. 验证
```bash
git log --oneline -10
git status
```

确认回滚生效，工作区干净。

---

## 危险操作确认（**强制**）

执行 `reset --hard` 或 `push --force` **前**必须二次确认：

```
⚠️ 危险操作检测！
操作类型：git reset --hard
目标 commit：abc1234
影响范围：
  - 丢弃 commit abc1234 之后的所有改动（包括未推送的）
  - 强制推送可能影响其他协作者
风险评估：
  - 未提交的代码将永久丢失
  - 已推送会破坏团队历史

请确认是否继续？[需要明确的"是"、"确认"、"继续"]
```

---

## 何时中断并询问用户

- 回滚目标不明确 → 列出最近 commit 让用户选
- 该 commit 已推送到 main/master → 强制使用 revert
- 用户要求 reset --hard → 二次确认
- revert 后产生冲突 → 引导用户解决冲突
- 不确定是否影响他人 → 询问协作情况

---

## 反模式（禁止）

- ❌ 在共享分支直接 reset --hard（破坏他人历史）
- ❌ 在未确认的情况下 push --force
- ❌ 回滚不写 commit message（revert 必须说明原因）
- ❌ 频繁 reset --hard（应反思 commit 策略）
- ❌ 回滚后不验证（直接 commit 下一个任务）

---

## 完成后自检清单

- [ ] 回滚方式已选型（revert vs reset）
- [ ] 危险操作已二次确认
- [ ] 命令已正确执行
- [ ] git log 显示回滚生效
- [ ] 冲突已解决
- [ ] 已推送到远程（如需要）
- [ ] 报告已给用户（含新旧 HEAD hash）
