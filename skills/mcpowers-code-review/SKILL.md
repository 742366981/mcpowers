---
name: mcpowers-code-review
description: "code review / 代码审查 / 帮我审一下 / CR / review / 帮我看看这段代码 → 触发本技能。口语：帮我 review 一下这段/帮我审一下/审一下这段/审一下代码、帮我 CR 一下、检视一下、看看有没有问题/有没有 bug/代码质量怎么样/有没有问题/OK 吗/有什么问题、代码健康度怎么样、帮我把把关/过一遍、过一下代码、PR 要提交了/我要提 PR/提 MR 前帮我审、合并到 main 前帮我审、自审一下/自查/再审一遍、再帮我审一遍。中英：review, CR, PR review, MR review, code review, peer review, self-review。边界：完整测试→`mcpowers-tdd`；排查特定 bug→`mcpowers-bugfix`；性能审查→`mcpowers-optimize`。多维并行审查，Critical 阻塞提交。"
---

# mcpowers-code-review（代码审查）

> 借鉴自 superpowers `requesting-code-review`。
> **核心**：早审、常审、用独立视角审（不继承作者偏见）。

---

## 触发即执行

### 1. 加载规范
- Read `mcpowers-shared/mcpowers-spec-index/SKILL.md`
- 加载：
  - `mcpowers-shared/docs/技术规范/代码规范.md`（**必读**，SOLID/KISS/DRY/YAGNI，含 §Python import 位置规范——所有 import 必须位于模块顶部）
  - 对应栈规范（Flask / Vue / 爬虫）
  - 涉及 API → `API规范.md`
  - 涉及 DB → `数据库规范.md`
  - 涉及缓存 → `缓存规范.md`

### 2. 多维并行审查
启动**多个独立审查者**（子代理），每个专注一个维度：

| 维度 | 关注点 |
|:-----|:-------|
| **正确性** | 逻辑是否正确？边界条件？异常处理？ |
| **规范** | 是否符合代码规范？命名？注释？格式？注释是否残留历史演进/参考来源痕迹（代码规范 §11.3）？Python import 是否全部位于模块顶部（代码规范 §Python import 位置规范）？ |
| **安全** | SQL 注入？XSS？权限校验？敏感信息泄露？ |
| **性能** | N+1 查询？大循环？阻塞操作？ |
| **可维护性** | 是否易读？是否易测试？是否易扩展？ |
| **测试覆盖** | 核心逻辑是否有测试？边界是否有测试？ |

### 3. 问题分级

| 级别 | 含义 | 处理 |
|:-----|:-----|:-----|
| **Critical** | 阻塞性问题：bug、安全漏洞、数据丢失风险 | **必须立即修复**，不修复不能合并 |
| **Important** | 重要问题：性能、规范违反、可维护性 | 评估后决定修不修，建议修 |
| **Minor** | 小问题：命名、注释、格式 | 可后续优化，不阻塞 |
| **Nit** | 吹毛求疵：纯风格偏好 | 可忽略 |

### 4. 输出审查报告
```markdown
# Code Review 报告

## 概览
- 审查范围：哪些文件
- 审查维度：6 维
- 问题统计：Critical X / Important Y / Minor Z

## Critical（必须修）
### CR-1: SQL 注入风险
- 文件：api/user.py:42
- 问题：`f"SELECT * FROM user WHERE id = {user_id}"`
- 建议：使用参数化查询

## Important（建议修）
...

## Minor（可选）
...
```

### 5. 修复
- Critical → 立即修
- Important → 修或记录为后续任务
- Minor / Nit → 可后续优化

---

## 何时触发

- 任务完成后（**强制**）
- PR 创建前（**强制**）
- 合并到 main 前（**强制**）
- 用户主动要求"审一下"

---

## 反模式（禁止）

- ❌ 自我审查（无独立视角）
- ❌ 只看 diff 不看上下文
- ❌ Critical 问题放行
- ❌ 给出无证据的质疑（"我觉得这里有问题"）
- ❌ 接受表演性认同（"你写得很棒"）—— 审查要有具体证据

### 「过度抽象 / 重复代码」反模式（v2.26.0+ 强制）

> 对齐 `代码规范.md §6.1.1 复用优先于二次抽象`。命中以下任一 → **Critical 阻塞合并**。

| # | 反模式 | 违反后果 |
|:-:|:-------|:---------|
| **R1** | ❌ **未先扫仓库/SKD/通用模块就写 wrapper**：`class MyHttpClient: def get(...): return requests.get(...)` 这种一行转发的「抽象」 | 引入不必要层；新人维护成本翻倍；测试无法隔离底层行为 |
| **R2** | ❌ **二次抽象仅一行调用底层**（如 `def send_email(...): EmailService.get().send(...)`） | 抽象成本（多一层阅读）> 收益（去掉一句 `.get()`）；违反 YAGNI |
| **R3** | ❌ **函数/类命名与 SDK / 公共模块已有定义冲突且非有意扩充**：SDK 有 `parse_url`，本仓库写 `parse_url_v2` 同名同义 | 应该提 PR 改 SDK 或复用；并存等于重复定义 |
| **R4** | ❌ **跨项目搬运同名函数但不复用**：A 项目有 `validate_phone` → B 项目再写一个 `validate_phone` | 应该提到 `common/validators.py` 跨项目共享 |
| **R5** | ❌ **抽象类（ABC / Protocol）只有一个具体实现**，第 2 个实现至今没出现 | 提前抽象；等到第 2 个实现再抽（YAGNI） |
| **R6** | ❌ **新写公共函数但仓库内零调用方**（dead-on-arrival） | 违反 YAGNI；先写私有函数，等真有 3+ 调用方再升公共 |
| **R7** | ❌ **业务代码绕过 `utils/loggings.py` 单独写清理/轮转逻辑**：自己写 `for f in glob('*.log.*'): os.system(f'gzip {f}')` | 与框架清理函数双跑；窗口语义模糊；详见 `日志规范.md §7.3` |
| **R8** | ❌ **Python 函数/方法/类/条件块内部出现 `import` 或 `from … import`**（局部 import）：包括 `if TYPE_CHECKING` 放在函数内、`try/except ImportError` 写在函数体里 | 违反代码规范 §Python import 位置规范；物理门禁 `pre-write-check-import.sh` 会阻断；只有循环依赖或真正可选依赖且写明原因并由用户确认才可放行 |
| **R9** | ❌ **未声明 stability / last_breaking_change 就改规范 frontmatter**（v2.27.4+）：新增 / 删除 / 重命名规范章节必须同步声明 `stability: stable|evolving|deprecated` + `last_breaking_change: v{major}.{minor}.{patch}`；破坏性变更还必须在 CHANGELOG Breaking Changes 段列出 | 违反代码规范 §CHANGELOG 强制破坏声明段；用户升级时无法判断兼容性；AI 引用规范时无法判断是否需主动提示风险 |
| **R10** | ❌ **重复检测 hook 未区分「真重复」与「合法重名」**（v2.28.2+ 已修复）：v2.27.5 之前 hook 仅按函数名命中就 block，v2.27.6~v2.28.1 走 4 类启发式分级（命名空间 / 签名 / 绑定方法 / 单行透传）——**两者都用启发式打补丁，源头是「跨文件同名默认视为重复」**。v2.28.2+ 回归极简：跨文件同名默认放行（Python import 是模块级作用域），仅「同文件重名（真 bug）」+「单行透传 wrapper（gold standard 二次包装）」两类 block | 审查时若看到 R10 旧行为（跨文件同名默认 block，或 4 类启发式降级），CR 阻塞要求升级 hook 到 v2.28.2+ |
| **R11** | ❌ **控制台日志级别未紧凑打印 / StreamHandler 未显式指定 stdout**（v2.28.4+）：`CONSOLE_FORMAT` 含 `%(levelname)-8s` 等宽度填充 → 终端输出 `[INFO   ]` 带多余空格；或 `logging.StreamHandler()` 不传 `stream` → 默认走 stderr → PyCharm / IntelliJ 给所有日志整体染红。两者违反 `日志规范.md §7.5` | 控制台 formatter 必须用 `%(levelname)s`（无宽度）或 `%(levelname).1s`（首字母极简）；StreamHandler 必须显式 `stream=sys.stdout`；CR 看到 `[INFO   ]` 或 PyCharm 染红即阻塞，要求改回 `%(levelname)s` + `stream=sys.stdout` |

**审查动作清单**（每个 PR 必跑）：

1. **diff 内每个新 `def` 都过一遍**：用本仓库内置搜索命令找到仓库内同名 def，对照 PRD 看是否重复引入
2. **新增 wrapper 类/管理器** 必须有明确职责（参数映射 / 批量调用 / 异常归一三选一），其他情况直接调底层
3. **新增文件超过 100 行 且 ≥ 50% 是「call through」** → Critical，向作者追问「为什么这一层要存在」
4. **同名函数跨文件出现 ≥ 2 次** → 看是否真有共性：若只是业务模块各自实现（hook 默认放行），放过；若属真重复（多个 utils/a.py + utils/b.py 重复同一逻辑），提 `mcpowers-extract` 抽离公共模块
5. **Python 文件完整扫描 + diff 扫描局部 import**：以全文件 AST 视角检查 `FunctionDef` / `AsyncFunctionDef` / `ClassDef` 体内是否新增 `import` / `from … import`；diff 中任意缩进 import 行（`+` 行）均视为新增违规；只有循环依赖或真正可选依赖且写明原因才可放行
6. **v2.27.4+ 规范 stability 自检**：diff 涉及 `skills/mcpowers-shared/docs/技术规范/*.md` 任何文件时，检查 frontmatter 是否声明 `stability` + `last_breaking_change`；破坏性变更是否在 PR 描述里列出 CHANGELOG Breaking Changes 条目

---

## v2.26.0+ 复用扫描 Quick-Check（review 必跑）

> 审查者收到 PR 后 30 秒内可执行的 3 条扫描命令：

```bash
# 1. diff 内新增/修改过的 def（看有无重名）
git diff main...HEAD -U0 | grep -E "^\+[[:space:]]*(async[[:space:]]+)?(def|function|func|fn)[[:space:]]+" | sort -u
# 2. 仓库内同名 def（看是否已有）
rg --type py "def\s+${候选名}\b" . | grep -v "^${自身文件}:"
# 3. SDK / common 是否有等价接口
rg --type py "(class|def)\s+${候选关键词}\b" common/ sdk/ utils/ shared/
```

> 三条都「未命中仓库已有」 → 通过；任一命中 → Critical 阻塞。

## v2.27.0+ Python import 位置扫描 Quick-Check（review 必跑）

> 对齐代码规范 §Python import 位置规范。审查者收到 PR 后必须执行的 2 条扫描命令：

```bash
# 1. diff 内新增的缩进 import 行（只看 + 行；- 行不查）
git diff main...HEAD -U0 | grep -E "^\+[[:space:]]+(import[[:space:]]+[A-Za-z_]|from[[:space:]]+[A-Za-z_.]+[[:space:]]+import)" | sort -u
# 2. 仓库所有 .py 文件的缩进 import（确认全文件现状）
rg --type py -n '^( +|\t+)(import|from\s+[^ ]+\s+import)' .
```

> 命令 1 命中 → Critical 阻塞，必须改为模块级导入；命令 2 仅作为全文件盘点依据，不直接阻塞但应纳入修复计划。

## v2.28.2+ 单行透传 Quick-Check（review 必跑）

> 对齐 `代码规范.md §6.1.1` v2.28.2 补充段。v2.28.2+ hook 已简化：跨文件同名默认放行，只有「同文件重名」+「单行透传 wrapper」两类 block。**hook 自动处理这 2 类，review 主要是兜底扫描**——单行透传 wrapper 是 hook 唯一仍在拦截的跨文件二次包装信号（gold standard）。

```bash
# 单行透传扫描：函数体仅一行 `return <已有函数>(...)` 的二次包装
# （hook 已自动拦截，但 review 仍要扫一遍兜底——防止 hook 配置丢失 / 受保护路径漏过）
git diff main...HEAD -U0 | rg -U "(?:async\s+)?(?:def|function|func|fn)\s+\w+\s*\([^)]*\)\s*:\s*\n\s*return\s+\w[\w.]*\s*\("
# 或全文件视角（审查时优先用 diff 视角）
rg --type py -U "def\s+\w+\s*\([^)]*\)\s*:\s*\n\s*return\s+\w[\w.]*\s*\(" .
```

> 命令命中 → Critical 阻塞——这是最经典的二次包装，无论同/不同命名空间都必须复用底层。
> **跨文件同名（非单行透传）已不再由 hook / review 强制拦截**——属业务模块各自实现，是否抽离由作者按需提 `mcpowers-extract`（见上方审查动作清单第 4 条）。

## v2.28.4+ 控制台日志级别紧凑 + stdout Quick-Check（review 必跑）

> 对齐 `日志规范.md §7.5` + `Flask后端规范.md §6.1` 控制台实现层。审查者收到 PR 后必须执行的 2 条扫描命令：

```bash
# 1. diff 内控制台 formatter 是否含 %(levelname)-Ns 宽度填充（命中即违规，应为 %(levelname)s）
git diff main...HEAD -U0 | rg "%\(levelname\)-[0-9]+s"

# 2. diff 内 StreamHandler() 是否显式传 stream=sys.stdout（未传即违规）
git diff main...HEAD -U0 | rg "StreamHandler\(\s*\)" | rg -v "stream="
```

> 命令 1 命中 → Critical 阻塞——formatter 字符串里 `%(levelname)-Ns` 宽度填充会输出 `[INFO   ]` 带填充空格；要求改回 `%(levelname)s`（无宽度）或 `%(levelname).1s`（首字母极简）。（注：`colorlog.ColoredFormatter(reset=True)` 只控制 ANSI 颜色重置，**不**控制 levelname 宽度——宽度由 format 字符串决定。）
>
> 命令 2 命中 → Critical 阻塞——Python `logging.StreamHandler()` 默认 `sys.stderr`，PyCharm / IntelliJ 会把 stderr 整体染红，即使日志级别是 INFO / DEBUG；必须显式 `stream=sys.stdout`。


## 审查后

- 修复完成 → 再审一次
- 整体通过 → 调 `mcpowers-git-commit` 提交
