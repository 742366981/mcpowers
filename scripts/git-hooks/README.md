# mcpowers pre-commit hook（v2.9.0+）

> 解决"改了技能数/版本号等数字声明忘改其他地方"的漏改问题。

## 为什么需要

每次改 `plugin.json` 的 `version`、增删技能、改 SCENE_SKILLS 数组后，文档串里有 7+ 处数字声明需同步：

- `README.md` / `CLAUDE.md` 至少 3 处
- `skills/mcpowers/SKILL.md` 路由器本体（description + §4）
- 各 skill 的 `description` 字段（如有提及场景数）
- `mcpowers-shared/SKILL.md` 规范库入口（规范数）
- `.claude-plugin/plugin.json` + `marketplace.json`（3 处 version）

`scripts/check-readme-sync.sh` 已扩展为 9 类检查（v2.9.0 新增 #8 #9），但**只在 CLI 跑时才生效**。装上 pre-commit hook 后，**git commit 前自动跑**，漏改立刻在本地拦截，不推错到远端。

## 安装

**方式 1（推荐）· 一键脚本**：

```bash
bash scripts/git-hooks/install.sh
```

效果：`git config core.hooksPath scripts/git-hooks` —— 用 core.hooksPath 把 hooks 目录指向本仓库的 `scripts/git-hooks/`。

**方式 2（手动复制到 .git/hooks）**：

```bash
cp scripts/git-hooks/pre-commit-template.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit    # Windows 上可选
```

> 注意：`.git/hooks/` 是 git 本地目录，不会被 commit，跨机器需重装。推荐方式 1。

## hook 行为

每次 `git commit` 时，**自动按顺序**跑：

1. `bash scripts/check-readme-sync.sh` —— 9 类一致性
2. `bash tests/plugin-verify.sh` —— 插件结构 + frontmatter + 动态数校验

任一失败 → commit 被阻塞 → 失败原因打印到终端 → 改完重新 commit 即可。

## 卸载

```bash
git config --unset core.hooksPath
```

或恢复默认：

```bash
git config core.hooksPath .git/hooks
```

## 排查

- **hook 没生效**：先 `cat .git/config | grep hooksPath` 看当前值；为空说明装方式 2 后被方式 1 覆盖
- **hook 报错但不知道哪类失败**：hook 会保留两个校验脚本的完整输出，往上滚找 `✗`
- **想临时跳过 hook 单次提交**：`git commit --no-verify`（不推荐，会绕过所有校验）
