---
name: mcpowers-doc-sync-install
description: "装项目级文档同步纪律 / 给现有项目加 doc-sync / 一键安装校验+hook / 安装 .doc-sync-rules → 触发本技能。口语：给这个项目装上纪律,装文档同步,装doc-sync,装同步检查,一键配置纪律,加预提交,加pre-commit hook,装mcpowers项目检查,装好校验。English: install doc sync,add project discipline,setup .doc-sync-rules,configure check-doc-sync,project-level enforcement。边界：装 npx 全局基础技能→mcpowers-install-basics-skills；从零搭骨架阶段顺便装→mcpowers-init；只想装个脚本不接项目→直接复制 templates/ 不需本技能。流程：识别项目类型→选 flask/vue/crawler/generic 预设→注入脚本+yml+pre-commit→跑一次证明无 FAIL。"
---

# mcpowers-doc-sync-install（项目级 doc-sync 纪律安装）

> **v2.9.0 L2 用户项目纪律** —— 把"代码改了什么就同步什么文档"的硬性校验塞进用户项目。
> **何时用**：拿到一个已有项目（不是从 mcpowers-init 来的），想让它接 mcpowers 的纪律，从此 AI 改完代码必须在 commit 前证明"文档也对得上"。

---

## 这是什么 / 不是什么的对比

| 维度 | mcpowers-install-basics-skills | mcpowers-init | **mcpowers-doc-sync-install（本技能）** |
|:--|:--|:--|:--|
| 输入 | 用户已有任意项目 | 空目录 / 想从零搭 | 用户已有任意项目 |
| 装什么 | 装 npx 全局外部技能（document-skills 等） | 整套项目骨架（routes/models/scripts 全套） | 装 1 个校验器脚本 + 1 个 .doc-sync-rules.yml + 1 个 pre-commit hook |
| 产物体量 | 全局 `~/.claude/skills/` | `app/` + `tests/` + `docs/` + `utils/` 等 | `scripts/check-doc-sync.sh` + `.doc-sync-rules.yml` + `.git/hooks/pre-commit` |
| 涉及 commit hook | ❌ | ❌（init 不写 hook） | ✅（核心：让每次 commit 自动跑） |

---

## 编排

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:--|:--|:--|:--|:--|
| 1 | `mcpowers-brainstorm` | 方法 | 项目类型无法 heuristic 识别（4 类型都没匹配） | 中断回问用户 |
| 2 | `scripts/templates/project-doc-sync-check.sh` | 模板资产 | 必读 + 必复制 | 模板不存在则中断 |
| 3 | `scripts/templates/project-doc-sync-rules.{flask,vue,crawler,generic}.yml` | 模板资产 | 按项目类型选 1 个 | 模板缺失则用 generic 兜底 |
| 4 | `mcpowers-git-commit` | Git | 收尾（可选） | — |

**铁律**：
1. **不覆盖已有文件** —— 用户项目里若已有 `scripts/check-doc-sync.sh` / `.doc-sync-rules.yml` / `.git/hooks/pre-commit`，先 AskUserQuestion 问"覆盖 / 备份后覆盖 / 跳过本步"
2. **presets 是 default，rules 用户可改** —— 装的是模板，rules 一周内应被用户定制
3. **不偷偷装 hook** —— 默认给 ".git/hooks/pre-commit" 写入，但必须告知用户并可在阶段 4 让用户跳过
4. **跑一次证明无 FAIL** —— 装完必须 bash scripts/check-doc-sync.sh，且结果通过（用户项目当前已存在的不一致要分清是"已有漏改"还是"装出新问题"）

---

## 触发即执行（4 阶段）

### 阶段 1 · 识别项目类型（heuristic，失败则回问）

按以下优先级探测：

| 信号 | 判定 |
|:--|:--|
| `app/` 或 `application/` 目录下 `*.py` 含 `from flask import` 或 `@app.route` | **flask** |
| `src/router/` 下存在 `*.ts` 含 `createRouter` 或 `path:` | **vue** |
| `requirements.txt` 含 `scrapy/playwright/requests-html/pyppeteer` 或有 `crawlers/` 目录 | **crawler** |
| 都没命中 | 进入 `AskUserQuestion` 让用户选 |

```bash
# 简化版 heuristic 脚本
if grep -rq "from flask import" app 2>/dev/null; then type=flask
elif grep -rq "createRouter\|createWebHashHistory" src/router 2>/dev/null; then type=vue
elif [ -d crawlers ] || grep -q "scrapy\|playwright" requirements.txt 2>/dev/null; then type=crawler
else echo "无法自动识别，请 AskUserQuestion"; fi
```

**关键**：识别完后再 `AskUserQuestion` 1 次确认，避免误判（用户可能既有 Flask 又有 Vue）。

### 阶段 2 · 复制模板 + 改写为 `.doc-sync-rules.yml`

```bash
mkdir -p scripts
cp "${CLAUDE_PLUGIN_ROOT}/scripts/templates/project-doc-sync-check.sh" scripts/check-doc-sync.sh
chmod +x scripts/check-doc-sync.sh
cp "${CLAUDE_PLUGIN_ROOT}/scripts/templates/project-doc-sync-rules.<type>.yml" .doc-sync-rules.yml
```

`${CLAUDE_PLUGIN_ROOT}` 是 Claude Code 框架在工具调用时自动展开的占位符（**非环境变量**，是钩子配置层的字符串替换，AI 在 Claude Code 会话里跑 bash 时会被解析为当前激活的 mcpowers 插件根目录，例如 `~/.claude/plugins/cache/mcpowers/mcpowers/2.26.2/`）。本技能触发的 cp 命令由 AI 执行，不是用户手动跑，所以展开机制是闭环的。

### 阶段 3 · 注入 pre-commit hook（可选，但默认开）

`AskUserQuestion`：
- A：注入并启用（推荐）—— git commit 自动跑 scripts/check-doc-sync.sh
- B：注入但仅手动跑 —— 文件在 `.git/hooks/pre-commit` 但先不自动触发
- C：不装 hook —— 用户自己用其他方式触发

注入逻辑：

```bash
cat > .git/hooks/pre-commit << 'HOOK_EOF'
#!/usr/bin/env bash
set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -f "$REPO_ROOT/scripts/check-doc-sync.sh" ]; then
    bash "$REPO_ROOT/scripts/check-doc-sync.sh" || {
        echo "✗ doc-sync 校验失败，commit 中止"
        exit 1
    }
fi
HOOK_EOF
chmod +x .git/hooks/pre-commit
```

> **Windows / 已装 mcpowers 自身 hook 的项目**：注意 `.git/hooks/pre-commit` 一次只能放 1 个脚本。如果项目已有 pre-commit（如 mcpowers 自己的），**不能覆盖**，要 `cat >> .git/hooks/pre-commit` 追加并在文件末尾判断。**这种情况必须 AskUserQuestion**。

### 阶段 4 · 验证（必须跑一次）

```bash
bash scripts/check-doc-sync.sh
```

**期望**：通过。

**如果 FAIL**：仔细区分两类原因：
- **(α) 装出前就有漏改**（比如 Flask 已有 `@app.route('/foo')` 但 docs/api.md 没提）→ 不是装的问题，提示用户手动补 docs 或先用 `enabled=false` 临时禁用那一条规则
- **(β) 模板与项目类型不匹配** → 重新 AskUserQuestion 选类型，或让用户改 `.doc-sync-rules.yml`

---

## 与现有 4 个技能的边界

- **mcpowers-install-basics-skills**：装 **npx 全局技能**，不动项目文件，不装 hook。语义完全不同。
- **mcpowers-init**：从 0 搭骨架，会让项目自带完整 routes/models/scripts。本技能是给**已有项目**补纪律。
- **mcpowers-feat/bugfix/refactor**：场景层，用于**改代码**。本技能不修代码，只装规则。
- **mcpowers-git-commit**：收尾提交。本技能装好后调它做收尾，但本质不冲突。

**避免重复触发**：用户在 init 阶段选项目类型时已默认装了纪律，本技能不要重复跑。

---

## 反模式（禁止）

- ❌ 覆盖用户已有的 `scripts/check-doc-sync.sh` / `.doc-sync-rules.yml` / `.git/hooks/pre-commit`（先 AskUserQuestion）
- ❌ 装完不告知用户 hook 已生效就离开（用户会被突然拦的 commit 吓到）
- ❌ 把 mcpowers 自身 hook 模板装进用户项目（用户项目不该有 `.claude-plugin/`）
- ❌ 装完不跑一次 `bash scripts/check-doc-sync.sh`（必须证明通过）
- ❌ 装 generic preset 但项目是 Flask/Vue/爬虫（选错类型等于没装）
- ❌ 用错模板（脚本里第 87-89 行 hard-coded "RULE_START / RULE_END" 格式，不要替换为 yaml 真解析）
- ❌ 把 `.doc-sync-rules.yml` 当 yml 严格解析（当前是极简 DSL，不要引入 yq 依赖）

---

## 完成后自检清单

- [ ] 项目类型已 AskUserQuestion 确认（不要只信 heuristic）
- [ ] `scripts/check-doc-sync.sh` 已存在且 +x
- [ ] `.doc-sync-rules.yml` 已存在（来自对应预设）
- [ ] `.doc-sync-rules.yml` **已根据项目实际布局调整**（preset 是默认，code_dir / doc_file 路径要匹配）
- [ ] pre-commit hook 状态已与用户确认（A/B/C 三选一明确）
- [ ] 若选了 A：`.git/hooks/pre-commit` 已写入或追加成功
- [ ] 若项目已有 pre-commit：用了 `>>` 追加，没覆盖原内容
- [ ] **已跑一次 `bash scripts/check-doc-sync.sh` 验证**
- [ ] 失败时的 FAIL 类别已区分（α 已有漏改 / β 模板不匹配），并告知用户下一步
- [ ] 跑过 `bash scripts/check-readme-sync.sh` 通过（确认没顺手破坏 mcpowers 自身）

---

## 关联技能

- **上游**：`mcpowers-brainstorm`（项目类型识别失败时）
- **同级**（语义相近）：
  - `mcpowers-install-basics-skills` —— 装 npx 全局技能，不动项目
  - `mcpowers-init` —— 从 0 起搭骨架时同步装
- **下游**：`mcpowers-git-commit`（装完可能想立刻 commit）

---

## 资产路径速查

| 资产 | 路径（相对 mcpowers 根） |
|:--|:--|
| 校验器模板 | `scripts/templates/project-doc-sync-check.sh` |
| Flask preset | `scripts/templates/project-doc-sync-rules.flask.yml` |
| Vue preset | `scripts/templates/project-doc-sync-rules.vue.yml` |
| Crawler preset | `scripts/templates/project-doc-sync-rules.crawler.yml` |
| Generic preset | `scripts/templates/project-doc-sync-rules.generic.yml` |
