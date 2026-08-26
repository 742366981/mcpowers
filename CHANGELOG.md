# CHANGELOG

> 用户视角的版本变更历史。详细复盘见 [`docs/历史教训.md`](docs/历史教训.md)。
>
> 模板：每个版本 3–8 条 4 段式条目（新增 / 修复 / 调整 / 风险）。
> 维护规则：每次 release 追加到顶部 `[Unreleased]` 下方；不再修改历史版本。

## [Unreleased]

## v4.6.3 - 2026-08-26

> 🎯 **核心定位**：用户报告 mcpowers hooks 系统三大痛点——① Hooks 让 AI 写内容变慢 ② Hooks 触发 confirm UI 阻塞全自动化流程 ③ Hooks 封闭集字眼表 vs AI 同义词池无限（这场对抗 hook 永远输，例如 22 字眼可被「遵循/依照/依据/依照...」等同义词无限绕开）。本次 v4.6.3 做最小化改造：**① 把 22 字眼硬门禁从 PreToolUse Write/Edit/MultiEdit 迁移到 `pre-bash-guard.sh` 的 git commit 兜底段**（开发期不拦截，提交时一次性扫暂存区所有变更文件 → ERROR 违规累计即阻断）**② 把 duplicate 函数检测的跨文件扫描 lazy 化**（仅命中同文件重名或单行透传 wrapper 候选时才跨文件 walk，普通 Edit 不再全仓 walk）——保留铁律威慑但不阻塞 AI 写作流。

### Breaking Changes

- **`hooks.json` 移除了 `pre-write-check-no-ref-words.sh` 在 PreToolUse Write/Edit|MultiEdit 的硬门禁注册**——v4.6.3 之前用户在 Claude Code 编辑每个文件都会被 confirm UI 阻塞（22 字眼命中即 exit 2），全自动 / CI / 后台场景下整个流程卡死。v4.6.3 起 Write/Edit/MultiEdit 不再触发字眼硬门禁，改为 `pre-bash-guard.sh` 在 `git commit` 时扫暂存区所有变更文件做兜底（仅命中 ERROR 级别违规才 exit 2）。**对存量项目的影响**：开发期拦截消失，提交时仍会拦截——本质上是把拦截点从「每写一行」推迟到「提交前一次」，不影响铁律本身。**升级建议**：无需改动用户项目代码；如需保留开发期即时提醒，依赖 `post-write-check-no-ref-words.sh` 软门禁（exit 0 stderr 提示，不阻塞）。
- **`check_duplicate_function.py` hook_main() 检测算法变更**——v2.28.2~v4.6.2 期间每次 Edit 都对仓库内每个候选函数做 `git grep -n` 全仓扫描（500ms~2s/次）。v4.6.3 改为 lazy 化：① 仅扫同文件内重名（`count_in_source(new_str, name) >= 2` → 必拦）② 仅当 `is_one_line_wrapper(new_str, name) == True` 时才跨文件扫描 wrapper 的调用目标 ③ 其他跨文件同名场景直接放行（不再 walk）。**对存量项目的影响**：检测行为更精确——以前 wrapper 候选未触发时也会 walk 浪费时间，现在按需触发。**升级建议**：无需改动。
- **`skills/mcpowers-shared/scripts/check_no_ref_words.py` 修订 v4.3.0「CLAUDE.md/README.md 无例外」决策**——v4.6.3 兜底段（`pre-bash-guard.sh` git commit）首次执行即暴露 v4.3.0 设计的 2 类冲突：① **术语名冲突**：v4.3.0 引入的「代码/配置零引用铁律」术语本身含禁用字眼「引用」，无差别扫描破坏术语一致性（CLAUDE.md / README.md / `scripts/check-readme-sync.sh` 等大量行因含「零引用铁律」术语名被 fallback 拦截）② **类型冲突**：CLAUDE.md / README.md 本质是 v4.0.2 §9.5 文档铁律定义的「参考型文档」（功能是「指向具体规范章节」），v4.3.0 决策把它们当「输出型」严格拦截——与 §9.5 场景化决策模型直接冲突。v4.6.3 修订：① 加 `_TERM_EXCEPTIONS` 精确子串豁免集合（`代码/配置零引用铁律` / `代码/配置零引用智能二分判定` / `R17 零引用` / `R15 接口零引用` / `R16 .md 零引用` 等 v4.3.0+ 引入的规范术语名）——命中整行放行；② 把 `CLAUDE.md` / `README.md` / `AGENTS.md` 加入 `_PATH_WHITELIST_FILES` 路径白名单——回归 v4.0.2 §9.5「参考型文档豁免」立场。**对存量项目的影响**：用户的 CLAUDE.md / README.md 不再被 22 字眼硬门禁拦截——这是 v4.6.3 的设计预期（CLAUDE.md / README.md 自有 `post-write-check-doc-content.sh` 软门禁兜底）。**升级建议**：无需改动用户项目代码；如需保留原 v4.3.0 严格拦截行为，可手动从 `check_no_ref_words.py` 移除白名单条目。

### 新增

- **`hooks/pre-bash-guard.sh` v4.6.3+ git commit 字眼兜底段**：在原危险命令黑名单（`rm -rf /` / `dd if=` / fork 炸弹等）之外，新增 git commit 兜底——检测命令以 `git commit ` 或 `git commit` 开头时（任何选项组合，含 `-m` / `-a` / `-S` 等），从暂存区 (`git diff --cached --name-only --diff-filter=ACMR`) 逐文件 `git show ":<file>"` 拿到变更后内容，喂给共享 `check_no_ref_words.py --level=ERROR`，任何 ERROR 级违规累计即 `exit 2` 阻断提交 + stderr 输出违规摘要 + 修复建议。性能：每暂存文件启一次 Python 子进程（~100ms），常规 commit 5-10 文件 2 秒内完成，对比原 PreToolUse Edit 每行触发 ~50ms × 10 次 = 500ms 反而更快。
- **`tests/plugin-verify.sh §7.9` v4.6.3 回归测试段 T22/T23**：用 `mktemp -d` 创建隔离 git 仓库，T22 验证「暂存区含禁用字眼文件 + git commit → exit 2」（含真实 Python 检测器调用 + Windows 兼容 PY_BASH 探测），T23 验证「暂存区全干净 + git commit → exit 0」——防未来退化（pre-bash-guard.sh git commit 段必须真实跑检测器不能放空）。

### 修复

- **`hooks/pre-write-check-no-ref-words.sh` 改为 no-op stub**（仅保留 `exit 0` + 1 行最小注释避免被自身字眼检测命中）——v4.6.3 之前用户在 Edit 文档时仍会被自身脚本的注释触发（"PreToolUse:Edit hook error: ❌ [fallback] 行内含禁用引用字眼「引用」"），实测反馈「硬门禁对文档字眼 + 代码注释字眼相关都不生效，新增和编辑都没有拦截」根因。no-op stub + 入口从 hooks.json 移除 = 双重保险。
- **`hooks/hooks.json` PreToolUse Write/Edit|MultiEdit matcher 移除 `pre-write-check-no-ref-words.sh` 注册**：v4.6.3 之前 Edit|MultiEdit matcher 仍残留注册导致每 Edit 都跑检测器 + 仍触发 confirm UI；v4.6.3 起完全从 matcher 摘除。`PostToolUse Write|Edit|MultiEdit matcher` 的 `post-write-check-no-ref-words.sh` 软门禁保留（开发期 stderr 提示不阻塞）。

### 调整

- **`hooks/check_duplicate_function.py` hook_main() 检测算法 lazy 化**：把「先 git_grep_duplicate 扫仓库再判定 wrapper」改为「先本地判定 wrapper 候选才跨文件扫」，普通 Edit 性能从 500ms~2s 降到 < 50ms。**算法流程**：① `count_in_source(new_str, name) >= 2` → 同文件重名（必拦）② `is_one_line_wrapper(new_str, name) == True` → 跨文件扫 wrapper 调用对象 `cross_hits`，命中即拦 ③ 都不满足 → 直接放行（不再跨文件扫描拿 hits）。这是 v2.28.2「跨文件同名默认放行」原则的进一步优化——彻底告别启发式分级和强制 walk。
- **`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` version bump 4.6.2 → 4.6.3**（patch bump：v4.6.3 主要是 hooks 行为调整，不引入新能力但有 Breaking Changes——按 CLAUDE.md 铁律 patch bump 已足）。
- **`CLAUDE.md` 最高铁律段（hooks/ 目录表 + 代码/配置零引用铁律·智能二分判定段）**：两处 `pre-write-check-no-ref-words.sh` 描述改为「v4.6.3+ 22 字眼门禁迁移：从 PreToolUse Write/Edit/MultiEdit 硬门禁迁移到 `pre-bash-guard.sh` 的 git commit 兜底扫描」+ 加「**迁移动机**（用户决策 D 续·两大痛点）：① 22 字眼封闭集 vs AI 同义词池无限——这场对抗 hook 永远输；② 每 Edit 一行就被 confirm UI 阻塞，全自动 / CI / 后台场景下整个流程卡住。**迁移后行为**：开发期不被拦截（AI 可任意写），git commit 提交时一次性兜底扫描（提交是真要交付的时刻，被打断反而合理）」段。
- **`README.md` 行 18 + 行 320**：两处 no-ref-words 描述同步改为 v4.6.3+ 迁移说明；行 320 加「v4.6.3+ duplicate 函数检测 lazy 化」说明。

### 风险

- **存量项目含禁用字眼的代码/配置文件不会被开发期拦截**：v4.6.3 之前用户编辑含字眼的 .py 文件会立刻被 confirm UI 阻断；v4.6.3 起不再阻断，直到 `git commit` 时才统一兜底扫描。**潜在风险**：开发期单文件大量新增字眼不会即时反馈，需等 commit 才知道。**缓解**：`post-write-check-no-ref-words.sh` 软门禁仍跑（exit 0 stderr 提示「行内含禁用字眼」，不阻塞），开发期温和提醒仍在；如需绝对严格，可手动 `python3 skills/mcpowers-shared/scripts/check_no_ref_words.py --level=ERROR <file>` 自查。
- **`check_duplicate_function.py` lazy 化的边界**：当前实现仅扫「单行透传 wrapper」场景，**多行 wrapper / 带类型注解的 wrapper / 含条件分支的 wrapper** 暂不识别为 wrapper 候选——会被当作「跨文件同名」放行。这是 v2.28.2 「跨文件同名默认放行」原则的延伸，多行 wrapper 是否算「二次抽象」属于设计判断而非真 bug，不在 v4.6.3 拦截范围。**升级建议**：如需扩展，编辑 `check_duplicate_function.py:is_one_line_wrapper()` 函数加更多 AST 模式。
- **`pre-bash-guard.sh` git commit 兜底的 Python 探测**：Windows 默认只有 `python` 命令（无 `python3` 软链接），脚本内做了 `for cand in python python3 py; do` 三轮探测 + `import sys; sys.exit(0)` 真验证，避免用 `command -v` 误判（如 Git Bash 安装了 Python 但 PATH 异常）。**潜在风险**：若用户 Python 环境损坏（`python -c "import sys"` 失败），git commit 兜底段会被静默跳过——日志无任何提示。**缓解**：建议项目根 `.mcpowers-version` 旁加 `.mcpowers-python-ok` 标记文件自查，或人工 `python -c "import sys"` 测试。

---

## v4.6.2 - 2026-08-26

> 🎯 **核心定位**：v4.6.1 后用真实 Windows CMD 跑模板实测，**发现 3 个 v4.6.1 没暴露的真实硬伤**（用户实测反馈"感觉还是有问题"）：① UTF-8 BOM 让 CMD 双击 bat 报「不是内部或外部命令」（debug3/4 可重现）② `chcp 65001` 切换 UTF-8 代码页破坏 cmd 的 PATHEXT，导致 `call activate.bat` 裸名也失败（debug3 无 chcp 成功、debug4 加 chcp 后失败，100% 可重现）③ §25.5 模板清单列写错（`call activate.bat` → `call .\activate.bat`）。本次 v4.6.2 把 §3.3.4 R2 / R5 措辞收紧 + 4 个模板 `activate.bat` → `.\activate.bat` + AI 操作规范 Step 0 加 bug 复现命令。**所有 mcpowers 生成的 `.bat` 必须按 v4.6.2 写法**，保证 Windows CMD 双击直接跑通。

### Breaking Changes

无（纯规范正文修订 + 模板微调；用户项目按 v4.6.1 写法生成的 bat 在 `chcp 65001` 环境下会失败——但 v4.6.1 才发布 1 天内，存量项目按 v4.6.2 重写即可）。

### 新增

无（v4.6.2 是纯 bug 修复版，不引入新能力）。

### 修复

- **`开发环境规范.md §3.3.4 R2`「编码处理」措辞收紧**：明确**禁止**源文件 UTF-8 BOM——CMD 双击 bat 时首 3 字节 `EF BB BF` 会被视为命令名前缀，导致"不是内部或外部命令"（即使 bat 文件就在当前目录）。原 v4.6.1 措辞"源文件用 UTF-8 BOM 编码避免双重解码异常"是错的——bat 文件不需要 BOM（BOM 是 UTF-8 文本编辑器的产物，CMD 不识别），加了反而破坏 bat 调用链。**验证方法**：`xxd venv_windows.bat | head -1` 显示 `00000000: efbb bf40 ...` → 删 BOM 后 `xxd` 显示 `00000000: 4065 6368 ...` → bat 可被 cmd 正常调用。
- **`开发环境规范.md §3.3.4 R5`「activate 写法」升级为 `call .\activate.bat`**：v4.6.1 写 `call activate.bat`（裸名 + .bat 扩展名），实测在 `chcp 65001 > nul` 之后**必失败**——`chcp 65001` 切换 UTF-8 代码页会破坏 cmd 的 PATHEXT 列表，导致裸名 `activate.bat` 在当前目录存在也报"不是内部或外部命令"。改用显式相对路径 `.\activate.bat` 绕过 PATHEXT 解析，100% 可重现验证通过。`debug3.bat` 无 `chcp 65001` → `call activate.bat` 成功；`debug4.bat` 加 `chcp 65001` → `call activate.bat` 失败；统一改 `call .\activate.bat` 后两个 bat 都成功。
- **`开发环境规范.md §3.3.3` venv_windows.bat 模板**：step 3 `call activate.bat` → `call .\activate.bat`。
- **`爬虫规范.md §25` 4 个模板（§25.1 一键启动 / §25.2 一键关闭 / §25.3 {module}_windows / §25.4 update_windows）**：3 处 `call activate.bat`（§25.1/§25.3/§25.4 各自的 activate）统一改 `call .\activate.bat`。
- **`爬虫规范.md §25` 6 条铁律段**：R2 措辞同步加「禁止源文件 UTF-8 BOM」段（CMD 双击 bat 时 BOM 视为命令名前缀）；R5 措辞同步加「必须 `call .\activate.bat` 显式相对路径——`chcp 65001` 切换 UTF-8 代码页后会破坏 cmd 的 PATHEXT，导致裸名 `activate.bat` 报『不是内部或外部命令』，实测 100% 可重现」段。
- **`爬虫规范.md §25.5` 模板清单表**：2 处 `call activate.bat` 描述同步改 `call .\activate.bat`。

### 调整

- **`AI操作规范.md` Step 0 执行流程 2.3 项 .bat 铁律段**：在「禁止沿用旧模板 `call activate`」之后追加「禁止裸名 `call activate.bat`（v4.6.2+ 改 `call .\activate.bat`）+ 禁止源文件 UTF-8 BOM（v4.6.2+ 必须纯 ASCII 字节流；`xxd 你的bat.bat | head -1` 应显示 `4065 6368 ...` 而非 `efbb bf40 ...`）」。
- **`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` version bump 4.6.1 → 4.6.2**（patch bump：纯 bug 修复，无破坏性变更）。

### 风险

- **存量项目按 v4.6.1 模板生成的 bat**：在 `chcp 65001` 环境下 `call activate.bat` 100% 失败——建议按 v4.6.2 重写。批量修复命令：`rg -l "call activate\\.bat" 你的项目/` 找含旧写法的 bat → 替换为 `call .\\activate.bat`；`xxd 你的bat.bat | head -1 | grep efbbbf` 找含 BOM 的 bat → 用 Python `data = data.lstrip(b'\\xef\\xbb\\xbf'); open(p, 'wb').write(data)` 删 BOM。
- **chcp 65001 仍可能影响其他 cmd 内置命令的 PATHEXT 解析**：除 activate.bat 外，理论上 `pip.exe` / `python.exe` 等**带 .exe 扩展名的命令不受影响**（PATHEXT 优先 .exe），但若 bat 内有其他 `call <script>.bat` 同模式写法，需同步改为 `call .\script.bat`。**统一规范**：v4.6.2+ 任何 `call` 后跟 `.bat` / `.cmd` 都必须加 `.\` 前缀。
- **`call .\<file>.bat` 的可移植性**：在 Windows CMD 100% 工作；但 PowerShell 不识别 `.\` 前缀（PowerShell 用 `& .\file.ps1`），所以 mcpowers 生成的 bat 仅保证 CMD 兼容性——PowerShell 用户请用 PowerShell 语法（R1 铁律：CMD 优先，不强求 PowerShell 兼容）。

---

## v4.6.1 - 2026-08-26

> 🎯 **核心定位**：修复 `开发环境规范.md §3.3.3` venv_windows.bat 模板在 Windows CMD 默认 GBK 下中文乱码 + `call activate` 依赖 PATHEXT 在 PowerShell 标签失败 + 无错误处理失败仍继续跑后续步骤的 3 类硬伤；新增 §3.3.4「Windows .bat 编写规范」6 条铁律 + 爬虫规范 §25「Windows .bat 编写规范」4 类典型模板（一键启动 / 一键关闭 / `{module}_windows.bat` / `update_windows.bat`）；AI 操作规范 Step 0 加 .bat 铁律提示。所有 mcpowers 生成的 `.bat` 一律按 §3.3.4 铁律实现，确保 Windows CMD 双击直接跑通。

### Breaking Changes

无（纯规范正文修订 + 模板扩展；用户项目不受影响——旧 bat 文件仍可保留运行，但建议按新版 §3.3.4 重写以保证 CMD 兼容性）。

### 新增

- **`开发环境规范.md §3.3.4`「Windows .bat 编写规范（总章·全栈适用铁律）」**：6 条铁律确保 Windows CMD 双击直接跑通——
  - **R1 CMD 优先**：禁用 PowerShell 独占语法（`Activate.ps1` / `$env:` / `-File` / `Set-ExecutionPolicy`）
  - **R2 编码处理**：含中文 echo / 中文路径 → 首行 `chcp 65001 > nul` + 源文件 UTF-8 BOM；纯英文可省
  - **R3 不写中文 echo**（强烈推荐）：进度统一英文 `echo [1/5] ...` 彻底回避 R2
  - **R4 路径双引号**：含空格必须 `"..."`，参数不裹进引号
  - **R5 activate 写法**：必须 `call activate.bat`（CMD 自动解析 PATHEXT）；禁 `activate` / `Activate.ps1`
  - **R6 错误处理**：每步 `|| goto :error`，失败立即停，末尾 `:error` 段 + `pause` + `exit /b 1`
  - 配套两种风格范式：**A 多行 + 错误处理 + 暂停**（venv 创建 / 启动服务 / 看日志）/ **B 单行 `&&` 链式**（CI / 无人值守 / 工具脚本）；附 4 行风格选择指南
- **爬虫规范 §25「Windows .bat 编写规范」**：4 类典型 bat 模板全部按 §3.3.4 铁律实现——
  - **`windows_cmd/一键启动.bat`**（§25.1）：A 多行 + 末尾 `pause`，激活 venv + `python -u main.py %*`，窗口常驻看实时输出
  - **`windows_cmd/一键关闭.bat`**（§25.2）：A 多行无 `:error`（关闭场景无进程可杀 = 正常分支），`taskkill /F /IM python.exe /T`
  - **`windows_cmd/{module}_windows.bat`**（§25.3）：A 多行 + 末尾 `pause`，启动单模块 + `%*` 覆盖参数（默认线程数 5）
  - **`windows_cmd/update_windows.bat`**（§25.4）：A 多行 + 错误处理，`git pull` + `pip install -U pip` + `pip install -r requirements_windows.txt`
  - **§25.5 模板落地清单表**总结 5 类文件的风格 / 关键命令 / 备注

### 修复

- **`开发环境规范.md §3.3.3` venv_windows.bat 模板重写**：旧模板 `call activate`（依赖 PATHEXT，Windows Terminal 默认 PowerShell 标签失败）+ 中文 echo（GBK 默认 CMD 必乱码）+ 无错误处理（venv 创建失败仍继续 `cd` 进不存在的目录）。新模板用 `call activate.bat` 显式指定 + 全部进度 echo 英文 + 每步 `|| goto :error` + 路径加双引号 + 末尾 `pause` + `:error` 段 + `exit /b 1`——CMD 双击直接能跑通。

### 调整

- **`爬虫规范.md §24` 末尾**「详见 `开发环境规范.md §4.4`」改为「同 §4.4（docker-compose 启动/重启/重部署三态）」：去掉"详见"画蛇添足字眼（v4.0.2+ 文档编写铁律 §9.5 场景化判定：上下文已引用 §4.4，重复指向属输出型删字眼场景）。
- **`AI操作规范.md` Step 0 新项目初始化**：执行流程 2.3 项加 `.bat 编写铁律要求`（"按 §3.3.4 6 条铁律：CMD 优先 / 编码处理 / 不写中文 echo / 路径双引号 / `call activate.bat` / 错误处理"），末尾加 ⚠️ 提示"禁止沿用旧模板 `call activate` + 中文 echo + 无错误处理写法"——AI 初始化项目时自动按新铁律生成 bat。

### 风险

- **存量项目含旧版 venv_windows.bat**：建议按 §3.3.4 重写——具体表现为：双击 .bat 弹出窗口后中文乱码 / `Activate.ps1` 报错 / 失败步骤继续跑后续命令。
- **存量项目含旧版 `windows_cmd/` 下 4 类 bat**：建议按 §25 模板重写，理由同上。
- **frontmatter stability 标注**：`开发环境规范.md` stability 仍是 `evolving`（v2.27.3 之后章节扩展）；`爬虫规范.md` stability 仍是 `stable`（§25 是纯新增章节，未修改任何旧章节内容，符合 stable "跨 minor 兼容"承诺）。

---

## v4.6.0 - 2026-08-25

> 🎯 **核心定位**：新增 **FastAPI 后端规范 v1.0**——1:1 镜像 `Flask后端规范.md` v1.2 的 22 章节结构（§0 接口速查 / §1 目录结构 / §2 路径 / §3 应用工厂 / §4 配置 / §5 中间件 / §6 日志 / §7 异常 / §8 错误码 / §9 响应 / §10 认证 / §11 OpenAPI 文档 / §12-§19 各专项 / §20 检查清单 / §附录 A/B / §21 Docker / §22 v4.5.x 铁律），框架绑定部分替换为 FastAPI 原生实现（`lifespan` / `Depends` / `APIRouter` / `Pydantic` + 原生 OpenAPI）。规范库 32 → 33 份。

### Breaking Changes

无。FastAPI 规范是新增资产，未影响 Flask / Vue / 爬虫等现有栈规范；现有项目不受影响。

### 新增

- **`skills/mcpowers-shared/docs/技术规范/FastAPI后端规范.md`（v1.0 / 1961 行）**：22 章节完整镜像 `Flask后端规范.md` 章节框架，框架绑定部分替换：
  - **目录结构**：`apps/` → `app/` + 增 `schemas/`（Pydantic BaseModel 集）+ `services/`
  - **应用工厂**：`create_app()` + `@asynccontextmanager async def lifespan(app)`
  - **中间件**：`BaseHTTPMiddleware` 子类 + `dispatch()` 替代 `@app.before_request` / `teardown_appcontext`
  - **认证**：`Depends(get_current_user)` + `HTTPBearer` 替代 `@login_required`
  - **OpenAPI 文档（§11）**：Pydantic BaseModel + Field + response_model 替代 Flasgger docstring；FastAPI 已原生暴露 `/openapi.json` 与 `/docs`（Swagger UI）；新增 `tools/export_openapi.py` 最小实现 + `custom_openapi()` 注入 BearerAuth 全局声明
  - **异常处理（§7）**：`@app.exception_handler(Exception)` 替代 `app.errorhandler`
  - **DB / Redis**：SQLAlchemy async + `aiomysql`；`contextvars.ContextVar` 替代 `flask.g`
  - **部署（§18）**：Gunicorn + `uvicorn.workers.UvicornWorker` 替代 `GeventWebSocketWorker`
  - **CORS（§17）**：CORSMiddleware + `allow_methods=['GET', 'POST']` 收紧（§1.H 铁律落地）
  - **辅助函数（§15）**：`hash_password` / `generate_token` / `generate_captcha` 等价实现，注明「复用优先于二次抽象」
- **`mcpowers-spec-index` §1 查表新增 `FastAPI / 后端 .py` 行** + **§2 接口类型速查新增 FastAPI 列**（与 Flask docstring 模板列对齐）+ **§3 文件树新增 `FastAPI后端规范.md`** + **示例 4 改写为 FastAPI**。模型现在按"接口契约规范 + 栈规范"双层加载：写 FastAPI 接口时同时 Read `接口契约规范.md`（栈无关）+ `FastAPI后端规范.md`（栈特定）。
- **`docs/CLAUDE.md`**「## 5. 规范体系」段新增 FastAPI 规范说明 + 「## 触发条件」段新增 FastAPI 触发映射（★ 加功能 / 新增接口 / 做页面 → 命中 `mcpowers-feat` 并加载 FastAPI 规范）。
- **`docs/README.md`**「规范体系」章节新增 FastAPI 规范行（共 33 个）+ 简要描述。
- **`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` 版本号 4.5.2 → 4.6.0**：新增 FastAPI 后端规范对应的市场元数据描述更新（规范库 32 → 33）。

### 调整

- **`FastAPI后端规范.md §11` v4.5.x OpenAPI 文档铁律完整落地**：§1.G 路径禁动态参数（`@router.get('/xxx/list')` 不写 `{xxx}`；详情走 `Query(..., alias='id')`）+ §1.H HTTP 方法白名单（仅 GET / POST）+ §1.I description 禁鉴权字眼 15 类 + §1.J description 禁错误码清单 + §1.K POST 强制 JSON（Pydantic BaseModel 默认 application/json；UploadFile 走 multipart 例外）。§22「v4.5.x 接口契约铁律落地」段对四铁律 + §1.K + v4.4.0 description 8 类禁用 + v4.4.0 SSOT 收敛逐条给出 FastAPI 落地点。
- **`FastAPI后端规范.md §20.4`「接口文档字眼规范（v4.3.0+）」**：列出 v4.3.0+ 代码/配置零引用铁律的 FastAPI 栈级落地——共享字眼清单 `mcpowers-shared/docs/_assets/_forbidden_ref_words.txt` + 智能二分判定（外部权威 / 内部规范名 / 项目内路径 / `.md` 文档）+ 一键扫描 `python mcpowers-shared/scripts/check_no_ref_words.py app/schemas/`。

### 风险

- **存量 FastAPI 项目升级 v4.6.0 后第一次写 schema 可能扫到历史违规**：v4.6.0 之前 FastAPI 项目没有强制 §1.G/§1.H/§1.I/§1.J/§1.K + description 8 类禁用 + 22 字眼 + `$ref` 复用——现在 hook 与 `mcpowers-code-review` R13-R23 会扫到。建议升级前批量预扫：`rg "@router\.(put|delete|patch|head|options)|\{[^}]+\}|described in|conform to" your_project/app/ --type py -l` 看哪些文件含历史违规。
- **`tools/export_openapi.py` 写入 `docs/API文档/openapi.md` 是占位实现**：v1.0 用 `json.dumps` 占位，生产环境建议替换为 fastapi-docs 或第三方 Markdown 渲染器（保持 SSOT——同一份 schema 渲染两次，机器 / 人类两份分别落盘）。
- **`FastAPI后端规范.md §21` Docker 部分仅给差异点速查**：完整 docker-compose 文件直接引用 `Flask后端规范.md §21.1-21.6`——避免与 Flask 版双向漂移；FastAPI 项目的三套 docker-compose 文件结构与 Flask 项目完全一致，仅 `command:` 字段固定 `python -u gunicorn_loader.py --{env}`，其他配置（image / volumes / environment / healthcheck）沿用 Flask 版。

## v4.5.2 - 2026-08-18

> 🎯 **核心定位**：Edit/MultiEdit 模式下硬门禁全量修复——用户在 `ynas-amadeus-service` 项目实测反馈「硬门禁对文档字眼 + 代码注释字眼相关都不生效，新增和编辑都没有拦截」「api 规范没生效」。v4.5.2 同时修 4 个 Edit/MultiEdit 漏配 / 盲区：
>   1. no-ref-words 硬门禁（v4.3.0 引入但 v4.5.1 漏配 Edit|MultiEdit matcher，detector 只读 content 字段）→ 全部修复
>   2. duplicate 函数检测（v2.28.x 起支持 Edit 但漏配 MultiEdit `edits` 数组）→ 全部修复
>   3. spec-frontmatter 删除字段检测（v2.27.4 起支持 Edit + MultiEdit，无 bug，仅加回归测试锁定）→ 加测试防退化
>   4. Swagger 接口契约（PreToolUse 钩子从磁盘读旧文件，Edit/MultiEdit 新增 @bp.route 时漏检）→ 新增 PostToolUse 兜底

### Breaking Changes

无（纯 bug 修复；行为差异：Edit/MultiEdit 写入代码/配置含禁用字眼、重复函数、Swagger 字段缺失现在会被 confirm UI / 自动反馈拦截；之前是静默放行——修复前的静默放行就是 bug）。

### 新增

- **`hooks/hooks.json` 在 `Edit|MultiEdit` matcher 下注册 `pre-write-check-no-ref-words.sh`**：v4.5.1 之前该 hook 仅在 Write matcher 下注册，Edit|MultiEdit 漏配导致编辑场景下硬门禁零拦截。v4.5.2 补齐——`Edit|MultiEdit` matcher 现在与 Write matcher 在硬门禁零字眼检测 wrapper 这一项上对齐（同样其他 5 个 hook：pre-write-confirm-api-hint / pre-write-check-duplicate / pre-write-check-import / pre-write-check-spec-frontmatter / pre-write-check-doc-sync 已在 v2.x 早期就注册）。
- **`skills/mcpowers-shared/scripts/check_no_ref_words.py` `main()` 增加 Edit / MultiEdit 输入格式归一化逻辑**：v4.3.0 引入的检测器只读 stdin JSON 的 `content` 字段，Claude Code Edit 工具传入 `old_string`/`new_string`、MultiEdit 传入 `edits[*].new_string`，导致即使 hook 注册了也因检测器拿到 `content=""` 直接 return 0 放行。v4.5.2 优先走 Write 的 `content` 字段（原行为不变），其次 Edit 的 `new_string`，再次 MultiEdit 拼接所有 `edits[*].new_string`；三种都拿不到才走兜底 `payload.get("content", "")`。
- **`hooks/check_duplicate_function.py` 输入解析扩展到 MultiEdit `edits[*].new_string`**：v2.28.x 起的检测器只读 `content` / `new_string` 字段，MultiEdit 模式拿到 `new_str=""` 后 `extract_function_names` 返回空集直接 return 0 → 静默放行。v4.5.2 复用 no-ref-words 同模式 3 档归一化（content / new_string / edits[*].new_string 拼接），MultiEdit 也走「同文件重名 + 跨文件单行透传」3 档判定。
- **`hooks/post-write-check-swagger.sh` 新增 PostToolUse 兜底钩子**：v2.31.0+ Swagger 契约门禁的 PreToolUse 钩子从磁盘读 `file_path`——Write 模式时新文件未落盘，Edit/MultiEdit 模式时读到旧文件。用户在 Edit 模式新增 `@bp.route` 但没写 docstring → PreToolUse 看到旧文件无新函数 → 静默放行（用户报告「api 规范没生效」的根因）。v4.5.2 新增 PostToolUse 钩子在文件已写入后跑同一 helper（`swagger-contract-check.sh` → `swagger-lint-helper.py`），命中违规 → exit 2 → Claude Code 把 stderr 喂回 Claude 自动修正（强反馈而非 confirm UI）。
- **`hooks/hooks.json` PostToolUse matcher 下注册 `post-write-check-swagger.sh`**：与 `post-write-check-no-ref-words.sh` 对齐——PostToolUse 段从 2 个 hook 增到 3 个。
- **`skills/mcpowers-shared/scripts/swagger-contract-check.sh` 增加 `--content-file=<tmp>` 可选参数**：PreToolUse wrapper 后续可改造为 stdin 注入 content 走临时文件路径，helper 优先用 content-file 缺失则回退磁盘读——为 v4.5.3+ PreToolUse Write 模式补齐做准备（v4.5.2 仅 PostToolUse 启用，本参数当前未被调用，留作接口预留）。
- **`tests/plugin-verify.sh §7.7` 新增 T11-T15 共 5 个 no-ref-words 回归测试**：T11 Edit 模式 .py 含内部规范名 → exit 2；T12 MultiEdit 模式 .py 含禁用字眼 → exit 2；T13 Edit 模式外部权威前缀（RFC 7519）→ exit 0 守护智能二分在 Edit 模式下仍放行；T14 Edit 模式项目内代码路径 → exit 2 守护项目内代码拦截在 Edit 模式下仍生效；T15 检查 `hooks.json` 中 `Edit|MultiEdit` matcher 块必须包含 `pre-write-check-no-ref-words.sh` 条目（根因 1 配置不漏配的硬守护）。
- **`tests/plugin-verify.sh §7.8` 新增 T16-T21 共 6 个 v4.5.2 扩展回归测试**：T16 Edit 模式单行透传 → exit 2（duplicate Edit 回归锁）；T17 MultiEdit 模式单行透传 → exit 2（duplicate MultiEdit v4.5.2 新支持）；T18 MultiEdit 删除 stability/last_breaking_change → exit 2（spec-frontmatter MultiEdit 行为锁定防退化）；T19 PostToolUse swagger 钩子文件存在 + 可执行；T20 hooks.json PostToolUse matcher 注册 swagger 兜底钩子；T21 PostToolUse swagger 钩子快速过滤（空 stdin / 非接口文件 / .txt 路径 → exit 0）。

### 调整

- **stderr 违规提示加 `[Edit]` / `[MultiEdit]` 前缀**（v4.5.2+）：让用户在 Edit 模式下能区分违规来源（行号仍为 new_string 相对行号；绝对化涉及外部 `old_string` → 文件位置查找，留待未来单独 issue）。
- **`CLAUDE.md` 第 100 行 v4.5.2+ 段扩写为 4 项并行修复条目**：明示 v4.5.1 之前 no-ref-words hook 仅在 Write matcher 下注册，v4.5.2 同时扩展 hooks.json Edit|MultiEdit matcher 注册 + detector 兼容 `new_string` / `edits[*].new_string` 输入格式；并新增 3 个并行修复说明（duplicate MultiEdit / spec-frontmatter MultiEdit 锁定 / Swagger PostToolUse 兜底）。
- **`README.md` 同步 11 → 12 个 Hook 脚本计数 + 核心功能表 6 行扩写 v4.5.2+ Swagger Edit/MultiEdit PostToolUse 兜底说明**：含 Claude Code 工具段 + 设计理念骨架增强段 + 1 句话总结 + 升级场景 5 维护说明 + 路由器 SKILL.md「## 5. 硬约束完整覆盖」标题。

### 风险

- **存量项目升级 v4.5.1 → v4.5.2 后第一次 Edit/MultiEdit 操作可能扫到历史违规**：v4.5.1 静默放行的禁用字眼 / 重复函数 / Swagger 字段缺失存量代码现在会被 confirm UI / 自动反馈拦截——这是修复（不是破坏），但用户体验上突然"严了"。建议升级前批量预扫：`rg "参考《|详见 utils/|按规范要求" 你的项目 --type py --type sh -l` 看哪些文件含历史违规；如有大量存量，可在 hook stderr 提示后临时在 confirm UI 选"是"放行，逐步清理。
- **`new_string` 相对行号对用户可读性下降**：用户看到 stderr 报 `L1` 不一定是文件第 1 行——而是 new_string 内相对第 1 行。已在 stderr 加 `[Edit]` / `[MultiEdit]` 前缀提示，但用户仍需打开 diff 才能精确定位；绝对化留待未来单独 issue。
- **PostToolUse swagger 钩子强反馈可能干扰 Claude 自动决策**：exit 2 把 stderr 喂回 Claude 触发自动重写流程；如果 Claude 选择 undo 该 Edit 而非补齐字段，会导致用户原本的改动被回退。属于「严谨反馈」的副作用，无法完全消除；用户可在 hook stderr 后追加一句话指引 Claude 该怎么改。

## v4.5.1 - 2026-08-16

> 🎯 **核心定位**：§1.K POST 强制 JSON 铁律（v4.5.0 接口契约四铁律之后用户决策 D 续的「第 5 条」——业务接口 POST 一律 `application/json`，禁 form-urlencoded/multipart，避免后端 `request.form` / `request.files` 兜底导致接口语义混乱）

### Breaking Changes

- **`swagger-lint-helper.py` 第 5 个新检查函数 `check_post_must_be_json()` 默认 ERROR 级**：业务接口 POST + `in: formData` 或 `consumes:` 含 `application/x-www-form-urlencoded` / `multipart/form-data`（路径段不在豁免白名单内）→ 写时 PreToolUse Write exit 2 + Claude Code confirm UI。**豁免白名单**（路径段内含关键字）：① 文件上传 `/upload` / `/attachment`（必须 multipart）；② 数据导入 `/import`（Excel/CSV 必须 multipart）；③ 第三方回调 `/webhook/<source>` / `/callback/<provider>` / `/notify` / `/oauth/<provider>/callback`（Content-Type 受第三方协议约束）。**升级影响**：存量项目第一次升级会扫到 POST + formData / form-urlencoded 违规触发 confirm UI，需改写为 `in: body` + JSON `schema`。

### 新增

- **`接口契约规范.md §1.K POST 强制 JSON 铁律`**（v4.5.1+ 用户决策 D 续第 5 条）：业务接口 HTTP POST 一律 `Content-Type: application/json`，禁止 `application/x-www-form-urlencoded` / `multipart/form-data`——避免后端 `request.form` / `request.files` 兜底导致接口语义混乱（后端统一 `request.get_json()`，schema 校验交 Webargs / pydantic）。**§1.K.4 与 §2 速查表关系**已明确：create/update/delete/batchDelete/bind/unbind 一律 JSON；upload/import/webhook 三类路径段豁免（multipart 或第三方协议决定 Content-Type）。`swagger-lint-helper.py check_post_must_be_json()` 实现 + `_POST_JSON_EXCEPTIONS = ('upload', 'import', 'attachment', 'webhook', 'callback', 'notify', 'oauth')` 白名单 + `_NON_JSON_CONTENT_TYPES` 3 类 form 模式扫描（formData / form-urlencoded / multipart-form-data）。
- **`swagger-lint-helper.py` 第 5 个新检查函数 `check_post_must_be_json()`**（~80 行）：methods= 含 POST → 检查路径段是否在 `_POST_JSON_EXCEPTIONS` 白名单 → 不在则扫描 docstring 内 `parameters[].in: formData` / `consumes:` 含 `_NON_JSON_CONTENT_TYPES` 之一 → 命中即 ERROR。`/`/`-`/`_`/`.` 分段判例外的实现与 `check_business_api_responses` 一致。

### 调整

- **`mcpowers-code-review` 反模式表新增 R23 + Quick-Check 段 1 条扫描命令**：R23 v4.5.1+ POST 非豁免路径段含 in: formData / consumes form-urlencoded/multipart；Quick-Check 段「v4.5.1+ POST 强制 JSON Quick-Check」含 1 条扫描命令（`in: formData` 正则 + consumes 字段扫描 + 路径段白名单判定豁免）+ 6 层 AI 视野覆盖说明（L1 CLAUDE.md / L2 description 触发词 / L3 ## 编排 Read 步骤 / L4 自检清单 / L5 硬门禁 / L6 审查门禁）。
- **`CLAUDE.md` 第 70 段后追加 §1.K POST 强制 JSON 铁律段**：`swagger-lint-helper.py check_post_must_be_json()` + `_POST_JSON_EXCEPTIONS` 7 关键字白名单 + R23 审查门禁——保证每次新会话自动加载的全局铁律段与实现 + 审查门禁三方一致。
- **`README.md` 第 15 行（特性 3.5 Swagger 接口契约硬门禁）+ 第 18 行（hook 清单）+ 第 23 行（mcpowers 一句话总结）+ 第 532 行（export_docs 说明）**：4 处同步加入 v4.5.1 §1.K POST 强制 JSON 铁律 + 第 5 个新检查函数描述。
- **3 个场景技能 description 触发词同步加 v4.5.1 段**：`mcpowers-feat` + `mcpowers-api-contract` + `mcpowers-requirement-change`——保证 L1 语义匹配能把「加新接口 / 改接口契约 / 改需求涉及接口」场景路由到正确技能时同步加载 v4.5.1 触发词。

### 风险

- **存量项目第一次升级会扫到大量 POST + formData 违规**：第 5 个新检查默认 ERROR 级，反模式范围广（POST + formData / form-urlencoded）。建议升级前批量预扫：`rg "in:\s*formData" 你的项目/views/*.py` 看命中数量；若项目 POST 接口较多（>10 个），可分批修复或临时在 hook 处加旁路。**这是设计意图**——CI 上线前必须清理，否则 AI 反复 confirm UI 拖累开发节奏。
- **`/notify` 路径段豁免可能误命中非回调接口**：当前白名单包含 `notify` 关键字（业务通知端点常含 `notify` 段，如 `user/notify/preferences`）——若业务路径有 `user_notify_settings` 这种段内含 `notify` 但实际是「用户通知设置」JSON 接口会被白名单跳过。**建议**：若发现误判，CR 时人工复核 + 改路径名为非 `notify` 关键字段（如 `user_notification_settings`）。
- **`consumes:` 字段扫描是字符串包含匹配**：当前覆盖 `application/x-www-form-urlencoded` / `multipart/form-data` / `application/x-www-form-urlencoded; charset=utf-8` 三种字面模式——若团队用 `application/x-www-form-urlencoded;charset=UTF-8`（无空格分隔）可能漏匹配。当前实现走字符串包含，足够日常但极端写法需人工 CR 兜底。

## v4.5.0 - 2026-08-16

> 🎯 **核心定位**：接口契约四铁律 ERROR 硬门禁（用户决策 D 续·v4.5.0 完成 v4.4.0 SSOT 终态收敛之后的「反模式全部 ERROR 化」阶段——路径禁动态参数 + HTTP 方法白名单 + description 禁鉴权 + description 禁错误码清单，4 条规则都是「明确反模式不是风格建议」，不设 WARNING 过渡期）

### Breaking Changes

- **`swagger-lint-helper.py` 4 个新检查函数默认 ERROR 级**（写时 PreToolUse Write → exit 2 + Claude Code confirm UI）：v4.4.0 的 3 个新检查（`check_description_redundant_content` / `check_no_path_in_description` / `check_no_repeated_schema`）在 v4.5.0 起升级为 ERROR 硬阻断（之前 v4.4.0 WARNING 阶段已结束）；v4.5.0 新增 4 个检查（`check_no_dynamic_path` / `check_allowed_methods` / `check_no_auth_in_description` / `check_no_error_codes_in_description`）**直接 ERROR 级**，不设 WARNING 过渡期——因为这些是「明确反模式」而不是「风格建议」（路径传 id 前端拼接差异 / PUT-PATCH 语义混淆前端调试困难）。**升级影响**：存量项目第一次升级会扫到更多违规触发 confirm UI，需批量改写后通过。

### 新增

- **`接口契约规范.md` §1.G-§1.J 4 段新铁律**（v4.5.0+ 用户决策 D 续）：
  - **§1.G 路径禁动态参数**（业务接口 `@bp.route` 装饰器路径模板**禁止**含 Flask 风格 `<xxx>` / `<int:xxx>` / `<string:xxx>` / `<uuid:xxx>` 动态参数；所有资源标识 `id` / `user_id` / `order_id` 走 query 或 body；例外白名单：`/webhook/<source>` / `/auth/oauth/<provider>/callback`）——`swagger-lint-helper.py check_no_dynamic_path()` 实现 + `_DYNAMIC_PATH_EXCEPTIONS = ('webhook', 'callback', 'oauth')` 白名单 + AST 解析 `@bp.route` 装饰器路径字符串
  - **§1.H HTTP 方法白名单**（业务接口 HTTP 方法**只允许 GET 或 POST**；按 §0 / §2 速查表：列表/详情/字典/导出/下载/流式/进度 → GET；创建/更新/删除（单+批量）/导入/上传/bind/webhook → POST；禁 PUT/PATCH/DELETE/HEAD/OPTIONS）——`swagger-lint-helper.py check_allowed_methods()` 实现 + `_ALLOWED_HTTP_METHODS = frozenset({'GET', 'POST'})` 白名单
  - **§1.I description 禁鉴权字眼**（`description` / `parameters[].description` / `responses[].description` 禁含 15 类鉴权字眼：`JWT` / `Bearer` / `需登录` / `需要登录` / `需 JWT` / `需要 JWT` / `需认证` / `需要认证` / `需鉴权` / `需要鉴权` / `需 token` / `需要 token` / `Authorization header` / `Authorization 头` / `鉴权失败`——鉴权方式由全局 `securityDefinitions` + `security` 声明，UI 自动展示锁图标）——`swagger-lint-helper.py check_no_auth_in_description()` 实现 + `_AUTH_WORDS_IN_DESCRIPTION` 字眼清单 + YAML 字段名行跳过
  - **§1.J description 禁错误码清单**（`description` 字段值禁含 6 类错误码清单模式：`错误码[：:]\s*\d+` / `错误码列表` / `返回码[：:]?\s*\d+` / `\d{5}\s+[一-鿿]` 标准行式 / `code[:\s]+\d{4,}` / `\d{5}\s*[、，,/]` 并列式；错误码统一在 `responses.examples` 或 `$ref BizError` 全局组件维护）——`swagger-lint-helper.py check_no_error_codes_in_description()` 实现 + `_ERROR_CODE_LIST_PATTERNS` 6 类正则

- **`swagger-lint-helper.py` 新增 AST 解析器 `_parse_route_decorators()`**（~80 行）：用 Python stdlib `ast` 模块扫描目标 .py 文件，提取 `@bp.route('/path', methods=['GET'])` / `@bp.get('/path')` / `@router.post('/path')` 等装饰器第一位置参数路径字符串 + methods 列表，返回 `dict[装饰器行号 → {path, methods}]`。`SyntaxError` 兜底返回 `{}` 不阻断；只在 `parse_python_docstring()` 已识别路由函数的前提下参与检查。`main()` 中按 `def` 行号向前找最近装饰器（`line-1` / `line-2` / `line-3` 三档回退，兼容多装饰器场景）关联 4 个新检查。

### 调整

- **`mcpowers-code-review` 反模式表新增 R19-R22 4 条 + Quick-Check 段 4 条扫描命令**：R19 v4.5.0+ 路径含 `<xxx>` 动态参数 / R20 v4.5.0+ methods= 含 PUT/PATCH/DELETE/HEAD/OPTIONS / R21 v4.5.0+ description 含鉴权字眼 / R22 v4.5.0+ description 含错误码清单；Quick-Check 段「v4.5.0+ 接口契约四铁律 ERROR 硬门禁 Quick-Check」含 4 条扫描命令（装饰器路径含 `<` 模式扫描 / methods= 含禁用方法扫描 / description 含鉴权字眼扫描 / description 含错误码模式扫描）+ 6 层 AI 视野覆盖说明（L1 CLAUDE.md / L2 description 触发词 / L3 ## 编排 Read 步骤 / L4 自检清单 / L5 硬门禁 / L6 审查门禁）。R18 同步升级为 v4.5.0 ERROR 硬阻塞（之前 v4.4.0 WARNING 阶段结束）。
- **`CLAUDE.md` 第 68 段「接口文档 SSOT 终态收敛」追加 v4.5.0 四铁律段**：`§1.G-§1.J` 4 段铁律 + 4 个新检查函数（`check_no_dynamic_path` / `check_allowed_methods` / `check_no_auth_in_description` / `check_no_error_codes_in_description`）+ R19-R22 审查门禁同步条目——保证每次新会话自动加载的全局铁律段与实现 + 审查门禁三方一致。
- **`README.md` 第 15 行（特性 3.5 Swagger 接口契约硬门禁）+ 第 18 行（hook 清单）+ 第 23 行（mcpowers 一句话总结）+ 第 461 行（PR 同步要求）+ 第 532 行（export_docs 说明）**：5 处同步加入 v4.5.0 四铁律 + 4 个新检查函数描述。
- **3 个场景技能 description 触发词同步加 v4.5.0 段**：`mcpowers-feat` + `mcpowers-api-contract` + `mcpowers-requirement-change`——保证 L1 语义匹配能把「加新接口 / 改接口契约 / 改需求涉及接口」场景路由到正确技能时同步加载 v4.5.0 触发词。

### 风险

- **存量项目第一次升级会触发大量 confirm UI**：4 个新检查全部 ERROR 级 + 1 个旧检查升级 ERROR，覆盖反模式范围广（动态路径 + 错误 HTTP 方法 + 鉴权字眼 + 错误码清单 + 旧 8 类冗余）。建议升级前批量预扫：`grep -E "(@bp\.|@app\.|@router\.|methods=\[)" 你的项目/views/*.py` 看命中数量；若项目接口较多（>50 个），可分批修复或临时在 hook 处加 `--allow-warnings` 旁路。**这是设计意图**——CI 上线前必须清理，否则 AI 反复 confirm UI 拖累开发节奏。
- **`check_no_auth_in_description` 的 15 字眼清单可能漏命中变体**：当前覆盖 `JWT` / `Bearer` / `需登录` / `需 JWT` / `需认证` / `需鉴权` / `需 token` / `Authorization header` / `Authorization 头` / `鉴权失败` 等 15 字眼——若团队用「需 token」/「鉴权失败」变体（中英混合 / 加空格）已覆盖，但「需要 token 才能访问」/「登录鉴权」/「需认证后调用」长句可能需要正则升级。当前实现走字符串包含匹配，足够日常但极端长句需人工 CR 兜底。
- **`check_no_dynamic_path` 的 webhook/oauth/callback 白名单段内匹配可能误命中**：当前走 `/`、`-`、`_`、`.`、`<`、`>`、`:` 分段后判段内含 `webhook` / `oauth` / `callback` 关键字——若业务路径有 `/user_oauth_callback_info/` 这种段内含 `oauth_callback` 的会被白名单跳过，但实际路径是「用户 OAuth 信息」而不是 OAuth 回调。**建议**：若发现误判，CR 时人工复核 + 改路径名为非 OAuth 关键字段（如 `/user_third_info/`）。

## v4.4.1 - 2026-08-16

> 🎯 **核心定位**：PreToolUse swagger 接口契约 wrapper hook 快速过滤覆盖范围扩展（覆盖 FastAPI/Express/Gin/Django/Rails/Laravel/Flask 蓝图等主流框架的常见接口文件命名约定）

### Breaking Changes

- 无。本次为纯增量扩展：wrapper hook regex 既有 4 类（views.py / /views/ / router.{py,js,ts} / /controllers/）完全保留，仅追加 7 类新模式；既有 v4.4.0 行为（5 字段契约 + 业务接口 200 + 零引用字眼 + description 零冗余）零影响。

### 新增

- **`hooks/pre-write-confirm-api-hint.sh` 接口文件快速过滤 regex 扩展（4 → 11 类模式）**：第 59 行 `grep -qE` regex 从 `(views\.py|/views/|router\.(py|js,ts)|controllers?/)` 追加 7 类常见命名约定——`/api/` `/routes/` `/handlers/` `/endpoints/` `/urls.py` `/resources/` `/blueprints/`——覆盖 FastAPI（`/api/` `/endpoints/`）/ Express（`/routes/` `/handlers/`）/ Gin（`/handlers/`）/ Django（`/urls.py`）/ Rails / Laravel（`/resources/`）/ Flask 蓝图（`/blueprints/`）等主流框架。**升级影响**：既有项目接口描述文件（views.py / router.py 等）行为完全保留；新增覆盖的命名约定现在也被 PreToolUse 物理门禁兜底——若文件已存在但 docstring 不满足 5 字段契约，写入时会触发 confirm UI。

### 调整

- **`hooks/post-write-commit-reminder.sh` regex 同步扩展**：commit reminder 第 100 行的 grep 模式同步追加 7 类——保证 lint 通过与 commit reminder 触发一致（避免「lint 通过但 commit reminder 漏触发」的不对称行为）。
- **`router/` 目录形式补全**：两个 hook regex 的 `router\.(py|js,ts)` 扩展为 `(router/|router\.(py|js,ts))`，覆盖 Express 路由目录入口（`src/router/index.ts` / `src/router/users.ts` 等）。**升级影响**：与文件名前缀形式合并到同一 group，仍属 patch bump 范围（纯增量扩展，无破坏性变更）。
- **`CLAUDE.md` 第 66 行 + `skills/mcpowers-code-review/SKILL.md` R13 段同步更新**：两处「写接口文件（views.py / /views/ / router.{py,js,ts} / /controllers/）」描述同步扩展为新 regex 列表（含 `/router/` 目录形式），保证文档与实现一致。

### 风险

- **新增覆盖范围的项目第一次升级会扫到更多接口文件触发 confirm UI**：用户项目里若已有 `/api/` `/routes/` `/handlers/` 等目录下的接口文件，PreToolUse hook 会扫这些文件，触发 v4.4.0 既有检查（5 字段契约 + 业务接口 200 + 零引用字眼 + description 零冗余）。**这是设计意图**——但用户升级前需确认已有 docstring 已达标或接受触发 confirm UI。
- **新增路径模式可能误命中非接口文件**：`/api/` `/routes/` `/handlers/` `/endpoints/` `/urls.py` `/resources/` `/blueprints/` 是**目录名/文件名约定**，不区分业务接口与工具类（如同名的 `utils/api_helpers.py`）。但 lint-helper.py 内部 `parse_python_docstring` 会自动识别 `@bp.route` / `@router.get` 等装饰器，没装饰器则短路 `sys.exit(0)`，所以误命中只增加 1 次 hook 启动开销（~50ms），不会产生误报。

## v4.4.0 - 2026-08-14

> 🎯 **核心定位**:接口文档 SSOT 终态收敛(用户决策 D 续:本次完成 v4.0.0 业务接口 HTTP 200 + v4.0.1 接口零引用 + v4.3.0 代码/配置零引用 + v4.4.0 接口 docstring 通用响应/分页/认证字段复用 + description 字段零冗余;三条用户决策合龙,接口文档闭环)

### Breaking Changes

- **接口 docstring 通用响应/分页结构必须用 `$ref` 复用(Warning 阶段)**:v4.4.0 起新增 `swagger-lint-helper.py check_no_repeated_schema()` 检测,业务接口 `responses.200.schema` 手工展开 `{code, msg, data}` / `{records, page_no, ...}` 视为 WARNING(渐进迁移)。**升级影响**:v4.4.0 不阻断,仅 stderr 提示;v4.5.0 起升级为 ERROR。**新接口按 v4.4.0 风格写;存量接口逐步迁移**。
- **description 字段禁用 8 类冗余内容(Warning 阶段)**:v4.4.0 起新增 `check_description_redundant_content()` 检测,description 字段值含 HTTP 状态码 / 认证方式 / 错误码清单 / 响应结构 / 完整路径 / 通用约束 / 路径内模块名 / summary 同义重复等 8 类内容视为 WARNING。**升级影响**:新接口必须 ≤ 30 字简短,只写接口功能;存量接口 review 阶段逐步清理。
- **接口路径不重复 basePath / 蓝图前缀**:`description` 字段禁止写完整路径(Warning 阶段);基础路径在 `Swagger(app, template=...)` 的 `basePath` 字段声明,蓝图前缀在 `Blueprint(url_prefix=...)` 声明,接口路径在 `@bp.route` 装饰器声明。

### 新增

- **`skills/mcpowers-shared/docs/API文档/swagger_components.md`(v4.4.0+ 新文件)**:5 个全局组件 SSOT 权威定义 — `StandardResponse` / `BizResponse` / `PageResponse` / `BizError` / `FileResponse`;`BearerAuth` security definition + 全局默认 `security`。SSOT 反漂移:任意接口 docstring 改动,只改本组件一次即可全局生效。
- **`skills/mcpowers-shared/docs/API文档/flask_swagger_config.py`(v4.4.0+ 新文件)**:Flask Flasgger 注入模板常量 `SWAGGER_TEMPLATE`,含 5 个全局组件 + BearerAuth + 全局 `security`。项目 `apps/__init__.py` 调 `Swagger(app, template={..., **SWAGGER_TEMPLATE})` 一行启用。
- **`skills/mcpowers-shared/docs/技术规范/接口契约规范.md §1.A.1 描述字段禁用内容清单(v4.4.0+ 强制)`**:8 类禁用内容列表(HTTP 状态码 / 认证方式 / 错误码清单 / 响应结构 / 完整路径 / 通用约束 / 路径内模块名 / summary 同义重复)+ 判别口诀「删掉这段文字后,对接方是否还能直接调通这个接口?能就说明是冗余,删」。
- **`skills/mcpowers-shared/docs/技术规范/接口契约规范.md §1.F 通用响应/分页必须用 $ref 复用(v4.4.0+ 强制)`**:5 类全局组件 + 必须用 `$ref` 的 5 类内容对照表 + 4 类反模式 + 强检测项 4 项。
- **`Flask后端规范.md §11.5 全局组件挂载(v4.4.0+ 推荐)`**:应用工厂注入步骤 + 复用示范 + 渐进迁移路径(v4.4.0 WARNING → v4.5.0 ERROR)。
- **`swagger-lint-helper.py 3 个新检查函数(v4.4.0+)`**:
  - `check_description_redundant_content()`:扫 8 类 description 禁用内容(HTTP 状态码 / 认证 / 错误码 / 响应结构等);
  - `check_no_path_in_description()`:扫 description 字段含完整路径前缀;
  - `check_no_repeated_schema()`:扫 responses schema 手工展开 `{code, msg, data}` / `{records, page_no, ...}`。
- **`swagger_template.md 19 类模板 v4.4.0+ 重写`**:所有 13 类基础 CRUD + 6 类扩展模板(bind / unbind / submit-task / progress / cancel-task / webhook / stream) + 3 类认证模板(login / logout / refresh)统一改用 `$ref` 引用全局组件;`description` 全 ≤ 30 字简短;`security` 由全局默认继承,公开接口显式 `security: []` 覆盖。
- **`mcpowers-code-review` R18(v4.4.0+ 新增)**:接口 docstring 冗余内容反模式条目 + description 字段禁用清单 + $ref 复用铁律 + v4.4.0+ Quick-Check 段含 4 条扫描命令（8 类描述禁用字眼扫描 / 通用响应/分页 `$ref` 复用扫描 / 完整路径前缀扫描 / 全局组件 `flask_swagger_config.py` 存在性扫描）。
- **`scripts/check-readme-sync.sh` §24(v4.4.0+ 新增)**:v4.4.0+ 接口文档 SSOT 5 件套完整性校验 — `swagger_components.md` + `flask_swagger_config.py` + 3 个新检查函数 + 接口契约规范 §1.A.1/§1.F + Flask §11.5 + CLAUDE.md v4.4.0 铁律段 + README v4.4.0 提及 + mcpowers-code-review R18 段 + 场景技能 description v4.4.0 触发词。

### 调整

- **`swagger_template.md` 文件版本 2.0 → 3.0**:`last_breaking_change` v2.3.0 → v4.4.0;`stability` 升级为 `evolving`(说明 v4.4.0 起大幅重构,后续还会演化)。
- **`接口契约规范.md` last_breaking_change v4.0.1 → v4.4.0**:本次新增 1 个强制铁律 §1.A.1 + 1 个强制铁律 §1.F,属小版本破坏性变更。
- **`Flask后端规范.md` §11.4 后新增 §11.5**:全局组件挂载 4 小节(11.5.1 复制模板常量 / 11.5.2 应用工厂注入 / 11.5.3 接口 docstring 复用 / 11.5.4 渐进迁移路径)。
- **`mcpowers-feat` v4.4.0 触发词增强**:description 末尾追加"v4.4.0+ 接口 docstring $ref 复用 + description 字段零冗余(全局组件 BizResponse/PageResponse 替代 `{code,msg,data}` 手工展开,描述 ≤ 30 字)"。
- **`mcpowers-api-contract` v4.4.0 触发词增强**:description 末尾追加 v4.4.0+ description 零冗余 + 通用响应/分页/认证 `$ref` 复用铁律（5 个全局组件 StandardResponse/BizResponse/PageResponse/BizError/FileResponse + BearerAuth 在 Swagger template 一次性注入）。

### 风险

- **存量接口 docstring 迁移工作量大**:用户项目每个接口 docstring 都要按 3 步迁移(全局组件注入 → 改用 `$ref` → description 简化)。`swagger-lint-helper.py` v4.4.0 默认 WARNING 不阻断,只让 AI 看见;v4.5.0 升级为 ERROR,**给存量项目 1 个 minor 周期迁移**。
- **Flasgger `$ref` 解析细节**:Flasgger 会把 `$ref: '#/definitions/BizResponse'` 字符串原样写到生成的 JSON spec,Swagger UI 5.17.14 自动解析(这是 OpenAPI 2.0 标准),无中间环节。Project 端的 `register_swagger` 注入 `SWAGGER_TEMPLATE` 必须在 `app.config['TESTING']` 设置之前完成,否则测试模式下可能拉不到全局组件。
- **更激进的接口契约收敛会带来学习成本**:本特性合龙 v4.0.0 + v4.0.1 + v4.3.0 + v4.4.0 4 个铁律,新成员上手门槛抬高。建议:新项目从第一天就用 v4.4.0 风格;存量项目可开启 WARNING 期逐步迁移,不开 v4.5.0 ERROR 仓促升级。
- **不影响 v4.3.0 既有检查**:`check_no_reference_words` + `check_business_api_responses` 行为完全保留;`swagger-lint-helper.py` 新增 3 个函数,既有 ERROR 级检查不被降级。

### 迁移指南

分 3 步:

1. **升级到 v4.4.0**:`plugin.json` 自动 4.3.0 → 4.4.0;`/plugin` → Update now 即可。
2. **应用工厂注入全局组件**:复制 `skills/mcpowers-shared/docs/API文档/flask_swagger_config.py` 到 `apps/`,在 `apps/__init__.py` 调 `Swagger(app, template={..., **SWAGGER_TEMPLATE})`(完整示例见 `Flask后端规范.md §11.5`)。
3. **接口 docstring 改造**:逐个接口按 `swagger_template.md §6.1` 3 处替换(schema → $ref / examples → $ref / security 删除)+ description 简化 ≤ 30 字。新写接口按 v4.4.0 风格;存量接口 v4.4.0 期内保持 WARNING 不阻断,review 阶段逐步清理。

## v4.3.0 - 2026-08-14


> 🎯 **核心定位**:代码/配置零引用铁律·智能二分判定(用户决策 D:之前 v4.0.1 接口零引用 + v4.0.2 .md 零引用已就绪,但代码注释/配置文件仍被「参考《代码规范》§11.3」「详见 utils/security.py」「按规范要求校验」字眼污染,要求最强有力点方案)

### Breaking Changes

- **`hooks/post-write-check-doc-content.sh` 移除**:v4.0.2+ 引入的 .md 软门禁脚本被新 `hooks/post-write-check-no-ref-words.sh` 完全替代。新脚本统一调用共享 `scripts/check_no_ref_words.py` 智能二分检测器,覆盖 .md + 代码 + 配置所有写入场景。**升级影响**:`hooks/hooks.json` 的 `PostToolUse` 段注册名同步替换;运行 `tests/plugin-verify.sh` 自检全过。
- **`hooks.json` PreToolUse Write 段新增 `pre-write-check-no-ref-words.sh`**:v4.3.0 新增硬门禁 hook,写代码/配置文件时智能二分判定 → ERROR 级 → exit 2 (confirm UI)。**升级影响**:AI 写 `.py` / `.yaml` / `.json` 等含禁用字眼会弹 confirm UI,要求改写为直接说明;运行 `plugin-verify.sh` 第 7.7 段自检覆盖。
- **代码注释硬门禁**:PreToolUse Write `.py` / `.sh` / `.yaml` 等代码/配置文件,若内容含 22 字眼 + 4 口语化补充,命中以下任一即 exit 2 阻断:内部规范名 / 项目内代码文件路径 / 项目内 .md 文档名(含 CLAUDE.md/README.md 无例外)/ 无外部前缀的「按规范」/ 兜底。**升级影响**:AI 写代码注释必须自洽,不指向其他文档;删掉字眼后意思不变视为画蛇添足。

### 新增

- **`scripts/check_no_ref_words.py` 共享检测器**(v4.3.0+):智能二分判定核心,被 3 个 hook 共用(`pre-write-check-no-ref-words.sh` + `post-write-check-no-ref-words.sh` + 未来扩展的 spec/check 脚本)。API: `scan_content(content, file_path)` / `scan_line(line, line_no)` / `is_path_whitelisted(file_path)` / `Violation` dataclass。CLI 入口支持 `--level=ERROR|WARNING|INFO` + `--json` 双格式输出。
- **3 份共享常量**(v4.3.0+ 与 R15/R16 共用一份字眼清单,避免漂移):
  - `_forbidden_ref_words.txt`:22 字眼 + 4 口语化补充(权威源)
  - `_internal_spec_docs.txt`:33 份规范 + 别名(代码规范/接口契约/日志规范/Flask规范/Vue规范/字段契约等)
  - `_external_authority.txt`:3 类外部权威 pattern(RFC/PEP/W3C/OWASP/ISO/IEEE + 公认作者 + 官方 URL)
- **`hooks/pre-write-check-no-ref-words.sh` 硬门禁 wrapper**(v4.3.0+):复用 `pre-write-check-import.sh` 的 wrapper 模式(探测 python 解释器 → 转发 stdin JSON → exit 2 触发 confirm UI),仅对代码/配置触发。
- **`hooks/post-write-check-no-ref-words.sh` 软兜底 wrapper**(v4.3.0+):PostToolUse 全量兜底,调用检测器 `--level=WARNING`,exit 0 不阻断仅 stderr 提示;覆盖 Edit/MultiEdit 无 content 场景。
- **6 类路径白名单**(v4.3.0+):`tests/` / `fixtures/` / `examples/` / `templates/` / `docs/历史教训/` / `CHANGELOG.md` —— 命中放行整个文件。
- **代码规范.md §11.3.1**(v4.3.0+):智能二分权威定义 + 22 字眼 + 4 口语化 + 7 优先级 + 14 反例 + 6 正例。
- **`mcpowers-code-review` R17**(v4.3.0+):代码/配置零引用智能二分反模式条目,与 R15(接口零引用)+ R16(.md 零引用)共用 22 字眼清单。
- **`mcpowers-code-review` v4.3.0+ Quick-Check**(v4.3.0+):8 条扫描命令(22 字眼扫描 + docstring 降级 + 外部权威放行 + 内部规范拦截 + 代码文件拦截 + CLAUDE.md/README.md 拦截 + 无前缀拦截 + 共享常量存在性)。
- **6 技能 description 加 v4.3.0 触发词**:`mcpowers-feat` / `mcpowers-bugfix` / `mcpowers-refactor` / `mcpowers-requirement-change` / `mcpowers-min-module` / `mcpowers-sdk-design` —— L1 索引增强触发灵敏度。

### 调整

- **`hooks/hooks.json` 事件组数 4 → 5**:PreToolUse Write 段新增硬门禁 hook,事件组按 matcher 分组计算 (SessionStart + PreToolUse Bash + PreToolUse Write + PreToolUse Edit|MultiEdit + PostToolUse)。
- **代码规范.md version 1.6 → 1.7**:`last_breaking_change` v2.28.2 → v4.3.0。
- **`tests/plugin-verify.sh` §6 + §7.7 重写**:替换 v4.0.2 post-write-check-doc-content 自检为 v4.3.0 pre/post-write-check-no-ref-words 自检 10 个 case(T1~T10:内部规范拦截 / 项目内代码拦截 / 兜底拦截 / 外部权威放行 / tests/白名单 / CHANGELOG 白名单 / post-write 软门禁 / CLAUDE.md 无例外 / .yaml refer to)。

### 风险

- **AI 写代码注释会频繁触发 confirm UI**:尤其是从其他项目复制代码注释或基于既有 spec 写新代码时,可能大量出现「参考《xxx 规范》」类写法。**这是设计意图**——强制自洽,但需给 AI 留出"按 RFC/PEP/OWASP 等外部权威"放行通道,避免误拦。
- **docstring 内违规降级为 WARNING**:避免整段 docstring 全 ERROR 阻塞(物理门禁放行,仅 stderr 提示),但 review 阶段仍需关注。
- **不影响 v4.0.1 接口零引用 + v4.0.2 .md 零引用既有行为**:22 字眼清单与 R15/R16 共用,只是扩展到代码/配置;swagger 5 字段契约 + 业务接口响应规范 + 表格防护 + XSS 阻断均不受影响。

### 迁移指南

无。本次纯增量扩展,既有 v4.0.0 ~ v4.2.0 行为完全保留:`hooks.json` 注册名替换 + `post-write-check-doc-content.sh` 文件删除是唯一破坏性变更;安装新版 mcpowers 后所有 hook 自动生效,无需用户项目侧任何操作。

## v4.2.0 - 2026-08-13

> 🎯 **核心定位**:`export_docs.py` 表格排版错乱防护(用户实测发现的真实痛点:7 个表格生成点全部裸拼文本,description / example 含换行 / `|` / 不可见字符即崩表)

### Breaking Changes

- 无。本次为纯渲染逻辑增强,不影响任何 .py docstring 写法、不破坏 v4.0.0 ~ v4.1.0 既有接口/规范/铁律。5 字段契约 + 零引用字眼检查 + 业务接口响应规范 3 类既有硬门禁的命中规则不变。
- **导出的 `.md` 表格风格会有差异**:单元格值里的 `|` 会被转义为 `\|`,换行会被转为 `<br>`,HTML 标签会被剥离(白名单 `<br>`),零宽字符 / NBSP 被清理——这是**故意**的视觉修复,用户重新生成即可。

### 新增

- **`_md_cell_safe()` 4 步走**(v4.2.0+ 表格单元格安全规整):7 个表格生成点(body / query-path / header / formData / 响应顶层 / data object / records / data 数组项) + 顶层 description 全部走该函数。4 步走:① 规范化(None / dict / list → str)→ ② 不可见字符清理(NBSP / EM SPACE → 空格;ZWSP / BOM → 删)→ ③ Markdown 转义(`\` → `\\`、`|` → `\|`、换行 → `<br>`)→ ④ 危险结构防御(HTML 标签剥离白名单 `<br>`、`|---` 等分隔行冒充 → `—`、代码块围栏 → 单 `` ` ``、列表 / 标题前缀 → 空格)。
- **`_scan_xss_risk()` 严重风险阻断**(v4.2.0+ spec 级别检查):扫描 `summary` / `description` / `parameters[].description` / `responses[].description` 全部可见字段,命中 10 类 XSS 模式(`<script>` / `<iframe>` / `<object>` / `<embed>` / `<style>` / `<form>` / `<svg>` / `on*= 事件处理器` / `javascript:` / `data:text/html`)即 exit 2 阻断。与 `check_5_field_contract` + `check_no_reference_words_spec` 平级——3 类硬门禁 + 1 类严重风险阻断。
- **`data: array` 响应字段渲染死代码修复**(v4.2.0+ 顺手):原 `if 'data' in resp_props and data_props:` 条件会因 `extract_response_data_fields` 在 `data: array` 时返回空 dict 而跳过整块,导致 `data: array` 类型接口**完全不显示**字段说明。本次把 `data.items.properties` 渲染从 901 行条件外移出来,标题改为 `**data 数组项字段**:` 区分于 `**data 响应参数**:`。

### 调整

- **`tools/export_docs.py` 表格生成集中改写**:7 个 `lines.append(f'| ... | {prop_desc} |')` 模式全部改为 `lines.append(f'| {_md_cell_safe(prop_name)} | {_md_cell_safe(prop_type)} | {_md_cell_safe(prop_desc)} |')`——这是同类改动,集中在 1 个 commit 内。
- **`tools/export_docs.py` 顶层 description 处理**:原 `description.replace('<br/>', '').strip()` 升级为 `_md_cell_safe(description)`——与表格走同一函数,手感一致。
- **`tests/test_export_docs.py` 新增文件**:31 个单元测试覆盖 _md_cell_safe 4 步走 + _scan_xss_risk 5 类 XSS 命中 + 端到端真实场景(Word 拷贝文本 / 多行 description / Markdown 注入)。仅用 stdlib `unittest`,无 pytest 依赖。

### 风险

- **导出的 `.md` diff 变化**:用旧 `export_docs.py` 生成的 `.md` 含有未转义 `|` / 换行 / 不可见字符的表格行,新版重新生成会:
  - 单元格值的 `|` → `\|`(视觉上不变,语义对齐 GFM)
  - 单元格值的换行 → `<br>`(GFM 表格内换行,主流渲染器支持)
  - 单元格值的 HTML 标签(非 `<br>`) → 整段剥离开来的剥离去除
  - 不可见字符(NBSP / ZWSP / BOM) → 清理
- **触发 XSS 阻断**:如果用户既往 spec 的 description 含 `<script>` 等注入测试片段,新版会阻断导出;**这是设计意图**——强制清理 spec 源头,不在渲染层做完脱敏。
- **不影响 JSON 导出**:`openapi.json` 不动,只动 `.md` 输出。

### 迁移指南

无。本次改动向后兼容,重新跑 `python tools/export_docs.py` 即可得到新格式 `.md`。

## v4.1.0 - 2026-08-13

> 🎯 **核心定位**:完全移除 `.env.example` 生命周期(用户决策 D:配置文件三件套易混淆 → 强制收敛到 `config_{env}.ini`)

### Breaking Changes

- **`doc-sync-check.sh` `env_in_doc` 检查类删除**(v4.1.0+):v2.29.0+ 引入的第三类检查 `.env.example KEY 必须在配置文档说明` 完全删除。原因是 mcpowers 禁读环境变量铁律(v2.25.0+)与 `.env.example` 文件本身的存在意义冲突——既然代码不读环境变量,`.env.example` 就没存在价值;且 `.env.example` / `config_{env}.ini` / 代码内写死 三件套并存极易让新人混淆哪个对。**升级影响**:项目根之前建过 `.env.example` 的——`doc-sync` 物理门禁不再检查它(也不报错);如果项目还在用 `.env.example`,按 §迁移指南 直接迁移到 `config_{env}.ini`。
- **`hooks/pre-write-check-doc-sync.sh` 过滤白名单删除 `.env.example`**:写 `.env.example` 不再触发 doc-sync 检查,hook 直接放行。
- **`mcpowers-init` 第 5 步「创建环境配置示例」改为「创建配置文档」**:不再创建 `.env.example`,直接生成 `config_dev.ini` / `config_prod.ini` 模板;项目目录树示例同步替换为 ini 文件。

### 新增

- **`config_{env}.ini` 一处收敛的强提示**:v2.29.3 「敏感字段各环境一律直接写在项目自己的 `config_{env}.ini` 里」升级为 v4.1.0「禁止 `.env.example`」——避免三件套并存。
- **`Swagger字段契约.md` 命名约定类比替换**:原 `.swagger-required-fields.yml` 与 `.env.example` / `.gitignore` 类比 → 改为 `.gitignore` / 各类 dotfile 通用类比。

### 调整

- **`doc-sync-check.sh` 头部注释**:`三类检查` → `两类检查`,顶部加 v4.1.0 删除说明段(不动 `path_in_doc` / `route_in_doc`)。
- **`mcpowers-init/SKILL.md` 表格第 5 步**:`创建环境配置示例 如 .env.example` → `创建配置文档 敏感字段直接写在 config_{env}.ini,不创建 .env.example(v4.1.0+ 与禁读环境变量铁律对齐)`。
- **`mcpowers-init/SKILL.md` 项目目录树**:`.env.example` 行删除;补 `config_dev.ini` / `config_prod.ini` 两行示范。
- **`开发环境规范.md` 表格第 5 步**:与 mcpowers-init 同步。

### 迁移指南

| 现状 | 操作 |
|:----|:-----|
| 项目根有 `.env.example`,且配置文档说明齐全 | 保留 `.env.example` 不动——v4.1.0 不强制删除,但建议逐步把 KEY 迁移到 `config_{env}.ini` 后删除 |
| 项目根有 `.env.example`,但 `Config.get()` 已直接读 `config_{env}.ini` | 直接删除 `.env.example`(纯死文件) |
| 项目根无 `.env.example` | 无需任何操作——v4.1.0 默认状态就是干净的 |

### 风险

- **删除而非重命名**:`.env.example` 这个文件名彻底从 mcpowers 自身规范/工具/技能/钩子中消失(只留在历史归档 CHANGELOG.md / docs/历史教训.md)。存量项目之前按 mcpowers 模板生成的 `.env.example`——升级后变孤儿文件,建议删除。
- **不强制迁移**:`.env.example` 是否删除由项目自己决定——mcpowers 不主动扫描项目根,也不报错。但项目内 `Config` 类的 ini 读取必须已正常工作,否则删了 `.env.example` 应用起不来。

## v4.0.3 - 2026-08-13

> 🎯 **核心定位**:`export_docs.py` parameters[].example 取值兜底,兼容 Flasgger body 参数重写行为(用户实测发现的真实 bug)

### Breaking Changes

- 无。本次为纯渲染逻辑兜底,不影响任何 .py docstring 写法、不破坏 v4.0.0/v4.0.1/v4.0.2 既有接口/规范/铁律。`swagger-lint-helper.py check_no_reference_words()` + `export_docs.py check_no_reference_words_spec()` 双层检测零引用字眼行为不变。

### 修复

- **`tools/export_docs.py` parameters[].example 取值兜底**(v4.0.3+ 必读):Flasgger 解析视图函数 docstring 时,如果用户把 `example:` 写在 body 参数的 schema **外面**(即 `parameters[].example` 顶层位置),Flasgger 会把 example **重写到 `parameters[].schema.example` 内**,导致参数顶层 `example` 字段为空——直接 `param.get('example')` 取不到值,渲染出的 API 文档就缺请求示例。本次修复新增 `_get_param_example(param)` 辅助函数(52 行含完整 docstring):
  - 路径 1(优先):参数顶层 `example` 字段(OpenAPI 标准 / Flasgger 正常解析路径)
  - 路径 2(body 类型兜底):`schema.example`(Flasgger 重写路径)
  - 其他类型(query/path/header/formData)无 schema 字段,只走路径 1
- **3 处参数取值替换**:`_render_endpoint` 内 query/path/header/formData 参数的 `param.get('example', '')` 全部改为 `_get_param_example(param)`,虽 body 重写行为不影响这 3 类,但统一走同一函数保持一致。
- **body 整体请求示例强化**:`json_to_markdown` 内 body 整体示例从单 `schema.get('example', {})` 改为 `schema.get('example', {}) or _get_param_example(body_params[0])`——兼容某些 Flasgger 版本可能不重写到 schema.example 的情况,双重兜底。

### 调整

- 无(纯函数级修复,不动接口、不动规范、不动铁律)。

### 风险

- **覆盖范围有限**:仅修复 `tools/export_docs.py` 的渲染逻辑;不修复 Flasgger 解析行为本身(项目内仍可继续按 docstring 顶层写 `example:`,本修复让 export_docs 兼容两种写法)。
- **零回归**:`tests/plugin-verify.sh` 74 项断言全过 + 7 个新增 `_get_param_example` 单元测试场景(query 顶层 / body 重写 / body 顶层优先 / 无 example / 都无 / formData / 非 dict / 字符串)+ 集成测试 body 类型参数请求示例渲染正确(输出 `{"username": "admin", "password": "123456"}`)。

## v4.0.2 - 2026-08-13

> 🎯 **核心定位**:文档编写铁律·画蛇添足字眼场景化规则(用户决策 C:v4.0.1 接口零引用的通则化推广)

### 新增

- **`文档编写规范.md §9.5` 「画蛇添足字眼场景化决策模型」新增**:3 类场景化(输出型 / 参考型 / 历史型)+ 22 字眼清单(中文 11 + 英文 11)+ 3 问决策流程图(Q1 给谁看 → Q2 删字眼意思变吗 → Q3 类型 + Q2 联合判定)+ 反向合规改写示范 4 条 + 跨场景落地表 + 与 v4.0.1 接口零引用关系(v4.0.1 接口零引用 = §9.5 输出型在 API 接口描述这一子集的最严格实施)。
- **`_assets/_forbidden_ref_words.txt` 共享常量新建**:v4.0.1 `swagger-lint-helper.py` line ~169 + `export_docs.py` line ~460 + v4.0.2 `post-write-check-doc-content.sh` 三处共用 22 字眼清单,避免漂移。`grep -v '^#'` 过滤注释 + `grep -v '^$'` 过滤空行即可加载。
- **`hooks/post-write-check-doc-content.sh` 软门禁新建**:PostToolUse(Write|Edit|MultiEdit) 触发,只对 `.md` 文件触发,扫 22 字眼并按 6 类路径白名单区分(参考型 / 历史型 自动跳过);命中且不在白名单 → stderr 提示(详见 22 字眼 + 3 决策问句 + 路径白名单清单);`exit 0` 不阻断(软门禁);从 stdin JSON 提取 `file_path` + `content`,`${CLAUDE_PLUGIN_ROOT}` 解析共享常量(hooks 唯一允许环境变量场景)。
- **CLAUDE.md「文档编写铁律·画蛇添足字眼场景化规则」段新增**:每次会话自动加载,AI 视野核心覆盖(包含 22 字眼清单 + 3 决策问句 + 链 §9.5 + 栈级落地:共享常量/软门禁 hook/R16 审查门禁)。
- **6 个文档场景技能 description L1 触发词 + Step 1 强 Read §9.5**:`mcpowers-prd` / `mcpowers-feat` / `mcpowers-plan` / `mcpowers-brainstorm` / `mcpowers-min-module` / `mcpowers-sdk-design` 全部加 v4.0.2+ 文档零引用触发词 + 必读 `文档编写规范.md §9.5` 步骤。
- **3 技能 ## 自检清单加 3 决策问句**:`mcpowers-feat` / `mcpowers-min-module` / `mcpowers-sdk-design` 完成后自检 / §0 审计 / 反模式清单全部加入 §9.5 决策 3 问 + 22 字眼扫描规则。
- **`mcpowers-code-review` R16 + v4.0.2+ 通用文档画蛇添足字眼 Quick-Check 段新增**:R16 文档正文含画蛇添足字眼反模式条目(3 类场景 + 路径白名单 + 6 层 AI 视野覆盖);Quick-Check 段 3 条扫描命令(输出型 .md 扫描 + 参考型白名单检查 + 路径白名单边界检查) + 6 层覆盖说明 + 与 v4.0.1 R15 接口零引用关系(R16 = 通则化推广)。

### 调整

- **`文档编写规范.md §9.3` 黑名单扩 22 字眼**:与 v4.0.1 接口零引用 + v4.0.2 文档零引用共享常量对齐(新增独立行「画蛇添足字眼(v4.0.2+ 通则化)」)。
- **`文档编写规范.md §10` 检查清单加 3 决策问句**:配合 §9.5 场景化决策模型。
- **`文档编写规范.md` frontmatter**:`version: 1.1 → 1.2` + `last_breaking_change: v2.24.0 → v4.0.2` + `stability: evolving` 声明。
- **`mcpowers-min-module` / `mcpowers-sdk-design` §0.1 外部参考字眼行扩展**:与 v4.0.2 22 字眼清单对齐(新增 11 中文 + 11 英文,扩展原 13 字眼清单)。
- **`mcpowers-min-module` / `mcpowers-sdk-design` §0.3 第 5 类扫描命令扩展**:正则覆盖 22 字眼 + 借鉴 / 致谢 / 致敬 / 改进自 / 类似 等历史保留字眼。
- **`mcpowers-min-module` / `mcpowers-sdk-design` 完成后自检清单 §0 审计第 5 项扩展**:与 22 字眼对齐 + 标注 `与 _forbidden_ref_words.txt 共享常量对齐`。
- **`mcpowers-feat` Step 3 加载规范段加条件分支**:若本次任务涉及新增 / 修改 README / 规范 / 设计文档 / 用户手册 → 必读 `文档编写规范.md §9.5`。
- **`mcpowers-prd` 必读加载规范段加注**:`文档编写规范.md` 必读 + 含 §9.5 画蛇添足字眼场景化决策标识。
- **`README.md` 第 15 行(3.5)表格同步声明**:v4.0.2+ 文档编写铁律·画蛇添足字眼场景化规则(无引用字眼 + 3 问决策 + 6 层 AI 视野覆盖)。

### 风险

- **软门禁误伤参考型 / 历史型文档**:6 类路径白名单(`.CHANGELOG.md` / `历史教训` / `mcpowers-spec-index` / `API契约` / `迁移` / `deprecation` / `README.md`)覆盖 95% 场景;剩余 5% 误伤 AI 看到 stderr 提示可主动确认「保留理由」并把路径加进白名单。
- **v4.0.2 不与 v4.0.1 冲突**:v4.0.2 是 v4.0.1 通则化扩展(22 字眼清单完全一致 + 共享常量三处共用),不破坏 v4.0.0 / v4.0.1 既有接口。`post-write-check-doc-content.sh` 是 PostToolUse 软门禁 + `swagger-lint-helper.py` PreToolUse 硬门禁互补,前者兜底 .md 文档,后者兜底 .py docstring。
- **`post-write-check-doc-content.sh` shell 兼容性**:用 `grep -v` / `while IFS= read` / `<<<` herestring(Bash 3.2+,跨 macOS / Linux / WSL / Git Bash);`set -euo pipefail` 严格模式 + `exit 0` 兜底不会阻断 Claude Code 流程。

## v4.0.1 - 2026-08-13

> 🎯 **核心定位**:API 文档零引用铁律(用户决策 B:接口文档应聚焦"怎么对接调用")。

### 新增

- **`swagger-lint-helper.py check_no_reference_words()` 新增**:`summary` / `description` / `parameters[].description` / `responses[].description` 字段值扫描禁用字眼(中文:参考 / 参见 / 详见 / 引用 / 参照 / 引自 / 根据规范 / 按照规范 / 按规范要求 / 遵守规范 / 按规范;英文:according to / refer to / referring to / as described in / as specified in / see also);YAML 字段名行(形如 `key:` 末尾冒号且无 value)跳过不扫。PreToolUse(Write) 阶段 exit 2 触发 Claude Code confirm UI。
- **`export_docs.py check_no_reference_words_spec()` 新增**:拉 spec 后立即扫描 `summary` / `description` / `parameters[].description` / `responses[].description` 各字段值含禁用字眼;返回 `(path, method, location, snippet)` 四元组;exit 2 + stderr 列违规位置 + 字眼前后各 20 字符片段。`--no-strict-fields` 不跳过本检查(铁律不允许兜底)。
- **`接口契约规范.md §1.E`「API 文档零引用铁律」新增**:禁用字眼清单 + 判定规则(子串包含即违规;代码块 JSON 示例仍按保守策略扫描)+ 强检测(写时 + 导出时双层)+ 反向合规改写示范(4 个 ❌ → ✅ 对照)+ 例外(URL 形式仍视为违规;「规范」作普通名词不违规)。
- **`mcpowers-code-review` R15 新增**:API 文档含禁用引用字眼反模式条目;Quick-Check 段增 v4.0.1+ 零引用字眼扫描命令(中文 + 英文禁用字眼 rg 扫描接口文件 diff)。

### 调整

- **`CLAUDE.md` Swagger 5 字段契约铁律段扩充**:追加 v4.0.1+ 接口文档零引用子句,链接 `接口契约规范.md §1.E` + `check_no_reference_words()` + `check_no_reference_words_spec()` 双层检测。
- **`README.md` 第 15 行功能同步表扩充:v4.0.1+ 接口文档零引用铁律表述,`check_no_reference_words` + `check_no_reference_words_spec` 双层拦截明示。

### 风险

- **存量接口 description 含历史引用字眼**:本次升级会让含「参考 / 参见 / 详见 / 引用」等字眼的存量接口 docstring 全部被写时 / 导出时双层门禁 block。迁移策略:①按 §1.E 反向合规改写示范逐条改写为在该接口 docstring 里直接说明(不引用其他文档);②删除指向外部文档的字面引用,改为接口内的字段值完整描述。
- **`description` 多行 YAML(`>` / `|`)扫描**:所有 description 字段值无论是否多行,均按子串匹配扫描;可能误伤示例值里含「参考」字眼的 JSON 字面量(如 `{"ref": "参考值"}`),保守策略下视为违规——建议作者改写示例值为不含禁用字眼的中性词。

## v4.0.0 - 2026-08-13

> 🎯 **核心定位**:工具脚本体系升级 + 业务接口响应规范铁律翻转

### Breaking Changes

- **`tools/export_docs.py` 默认输出文件名变更**:`swagger_spec.json` → `openapi.json`。下游 CI 脚本(`check_api_docs_sync.sh` / `run-api-tests.sh` / `generate-frontend-ts.sh`)已同步升级;旧版 mcpowers 项目升级后 CI 找不到 `openapi.json` 会红——按本仓发布的同步升级即可(本次 mcpowers 仓内 25 处已全部替换)。
- **`--openapi3` 参数被移除**:v2.4.0 引入的装样分支删除。mcpowers 锁定 Flasgger/Swagger 2.0 生态;OpenAPI 3.0 用户(FastAPI/Node 等)不在本规范内,迁移到 FastAPI/Node 时应使用其原生 OpenAPI 3.0 工具链。
- **`代码规范.md §7.4`「工具脚本 docstring 5 段骨架」新增(跨语言 + 当前实现 Python)**:函数级 docstring 强制 5 段骨架(Args / Returns / Raises / Side Effects / Example)。本次仓内同步:`hooks/check_duplicate_function.py`(8 函数)+ `hooks/check_python_import_placement.py`(2 公开函数)+ `tools/export_docs.py`(全部 14 个新/重写函数)已升级。
- **「业务接口响应规范」铁律翻转(用户决策 A)**:
  - **旧铁律**:业务接口 `responses` 块必须含至少 1 个错误码(401/403/500 等)
  - **新铁律(v4.0.0+)**:业务接口 `responses` 块**只列 `200`**;HTTP 一律 200,业务成功/失败由响应体 `code` 字段判断(`code: 0` = 成功;`code: 10001` = 业务失败);4xx/5xx 仅由框架层(Flask abort / Webargs / Flask-JWT-Extended 中间件)抛出,不由业务接口声明
  - **强检测**:`swagger-lint-helper.py check_business_api_responses(docstring, route)` 命中 → exit 2(触发 Claude Code confirm UI)
  - **迁移要求**:旧项目必须把业务接口 `responses` 块里的 401/403/404/500 删除,只留 200;认证接口(`/auth/login` `/auth/logout` `/auth/refresh` `/auth/verify` `/auth/register` `/auth/password`)与流式接口(`/download` `/export` `/stream` `/upload` `/file` `/attachment` 路径关键字)例外,保留 401/416

### 新增

- **`export_docs.py` 内嵌 5 字段契约硬门禁**:拉 spec 后立即校验 5 字段齐全(`tags` / `summary` / `description` / `parameters` / `responses`) + 必须含 `200`;任一不满足 exit 2 并列出缺失接口。详见 `接口契约规范 §1` + `swagger-lint-helper.py check_required_field_names`。
- **`export_docs.py` 对齐 API文档模板.md**:动态加载 `docs/API文档/API文档模板.md` 的「## 通用规范」段(基础路径 / 认证方式 / 统一响应说明 / 接口字段规范 / 导入导出字段规范),不再硬编码副本。模板改版 markdown 自动同步。
- **`export_docs.py` 新增 `--serve` flag**:导出文件后自动启动临时 web 服务(`http.server` + swagger-ui CDN),浏览器立即访问 `http://localhost:8080/` 看交互式文档。配套 `--port` / `--open-browser` flag。
- **`export_docs.py` 新增 `--no-strict-fields` flag**:跳过 5 字段契约检查(仅一次性紧急用,未来要删;不在 CI 兜底使用)。
- **`swagger-lint-helper.py check_business_api_responses()` 新增**:检测业务接口是否误列 4xx/5xx;认证 / 流式接口路径关键字白名单(login/logout/refresh/verify/register/password/download/export/stream/upload/file/attachment)。
- **`代码规范.md §7.4` 跨语言 docstring 5 段骨架对照表**:Python(Google) / Go(Godoc) / JS-TS(JSDoc) / Rust(rustdoc) / Java(Javadoc) 5 语言 5 段位对照——本仓当前实现仅 Python 栈完整落地,其他 4 语言仅参考。

### 修复

- **`export_docs.py` 装样 OpenAPI 3.0 分支清理**:仅认 `spec.swagger == '2.0'`,不满足 exit 2(原 line 532 隐式判断 `args.openapi3 or args.spec.endswith('openapi.json')` 删除)。
- **`export_docs.py` 5 失守位修复**:①模块 docstring 补完整使用方式 + 退出码约定;②核心函数 5 段 docstring 补全(`find_auth_paths` / `json_to_markdown` / `find_project_root` / `main`);③新增辅助函数 5 段 docstring(`get_error_codes` / `build_example_from_props` / `extract_response_data_fields` / `is_pagination_response` / `load_template_section` / `resolve_template_path` / `load_user_app` / `serve_docs`);④`from apps import create_app` 局部 import 改用 `importlib.util` 动态加载(合规 v2.27.0+ Python import 顶层铁律)。
- **`hooks/check_duplicate_function.py` 8 函数 docstring 失守修复**:`extract_function_names` / `count_in_source` / `is_one_line_wrapper` / `find_repo_root` / `is_protected_path` / `code_file_exts` / `git_grep_duplicate` / `format_block_message` 全部补 5 段 docstring(Args/Returns/Raises/Side Effects/Example)。
- **`hooks/check_python_import_placement.py` 公开函数 docstring 失守修复**:`collect_local_imports` + `main()` 补 5 段 docstring(私有 `_helper` 按 §7.4.5 YAGNI 不补)。
- **`接口契约规范 §1.C` 业务接口响应规范铁律修订**:`§1.C` 末段 + 新增 `§1.C.1` 业务接口响应规范(v4.0.0+ 铁律);`§4.3` 错误码规范加 v4.0.0+ 业务接口响应规范铁律联动段;`§7.1` 通用清单第 8 项从「`responses` 含 200 + 至少 1 个错误码」改为「业务接口只列 200;认证/下载接口例外(详见 §1.C.1)」。
- **`swagger-lint-helper.py` 旧铁律函数删除**:`check_responses_error_codes` 函数移除(旧铁律:业务接口必须含错误码,与新铁律「业务接口只列 200」直接冲突);由新 `check_business_api_responses` 替代。

### 调整

- **CI 校验不变**:本次不扩展 `check_api_docs_sync.sh` 加 5 字段内容检查(YAGNI + CI 耗时考虑)。5 字段硬门禁的"运行时"层在 `export_docs.py` 主流程,"写时"层在 `pre-write-confirm-api-hint.sh`,CI 只需保证 spec mtime 同步即可。
- **`mcpowers-code-review` R 系列新增 R14**:业务接口 responses 误列 4xx/5xx 反模式条目(依据用户决策 A §1.C.1 配套)。
- **跨语言扩展路径明确(YAGNI 本次不补)**:`swagger-lint-helper.py` 当前仅解析 Python docstring 文本;JS/TS router / Go / Rust / Java 的 5 段骨架对照表已在 `代码规范 §7.4.4` 提供,实际解析能力扩展留待后续版本。
- **`stability` 声明**:`接口契约规范.md` `last_breaking_change: v1.2`(linter 锁定,保留);本仓 v4.0.0 主要升级集中在工具脚本 + 业务接口响应规范铁律,核心接口契约规范本身元规则不变。

### 风险

- **业务接口响应规范破坏性**:旧项目大量业务接口 `responses` 块含 401/403/404/500,升级后会被 `swagger-lint-helper.py check_business_api_responses` 全部 block。迁移策略:①按路径关键字白名单豁免认证/流式接口;②其余业务接口 `responses` 块删除所有 4xx/5xx,只留 200。
- **默认输出文件名变更**:旧项目 CI 脚本(`check_api_docs_sync.sh` 等)依赖 `swagger_spec.json` 路径——升级后旧脚本找不到 `openapi.json`,CI 全红。必须按本仓发布的同步升级(本次 mcpowers 仓内 25 处已全部替换为 `openapi.json`)。
- **`--openapi3` 移除**:旧项目如使用 `python tools/export_docs.py --openapi3 ...`,升级后会 argparse 报错。mcpowers 锁定 Flasgger/Swagger 2.0 生态,本就是装样分支,影响面极小。
- **`代码规范 §7.4` 新章节影响**:函数级 docstring 强制 5 段骨架,旧项目如未升级会被 `mcpowers-code-review` 标 R1-R10 反模式;不阻断编译,但 CI 校验会警告。

## v3.0.0 - 2026-08-13

### Breaking Changes

- **`§10.3 Token 管理默认行为翻转**(Flask 后端):从「单端登录(同一账号只能在一处登录)」改为「允许多登录(同账号多设备同时在线)」,默认行为直接翻转,既有项目按旧版生成的代码会被新规范覆盖。详见 `skills/mcpowers-shared/docs/技术规范/Flask后端规范.md §10.3`。如必须保留单端行为,请自定义反向键实现并显式注释,不引用本节默认行为。
- **Key 命名变更**:`ADMIN_USER_TOKEN_BY_ID`(string,反向键,单端登录)→ `ADMIN_USER_TOKENS_BY_ID`(Set,反向集合,多端登录)。`skills/mcpowers-shared/docs/技术规范/缓存规范.md §3.3 Key 类` + `§3.4 Key 模式表` 同步更新。升级前请检查项目 `common/constants.py` 是否使用 `ADMIN_USER_TOKEN_BY_ID` —— 如有,必须按 Set 用法迁移(SADD/SREM);Redis 排查命令 `keys app:user:token_by_id:*` 须改为 `keys app:user:tokens_by_id:*`。

### 新增

- **Set 反向键支持多端登录**:`ADMIN_USER_TOKENS_BY_ID:{user_id}` 存同账号所有有效 token,登录时 SADD,登出时 SREM + DEL 正向键;正向键 `ADMIN_USER_TOKEN:{token}` 不变。
- **`kick_all` 强制下线辅助函数**(Flask 后端 §10.3 范例):从 Set 读取所有 token 一次性 DEL 正向键 + DEL 反向 Set,用于「改密码」「管理员强制下线」场景。
- **新增 `sadd` / `srem` / `smembers` 客户端方法**:`缓存规范.md §2.2` 客户端方法表补充 Redis Set 操作,§10.3 多登录 Set 用法落地。

### 修复

- 无

### 调整

- **frontmatter `last_breaking_change` 同步声明**:`Flask后端规范.md` `v2.29.1` → `v3.0.0`;`缓存规范.md` `v1.0` → `v3.0.0`(v2.27.4+ 铁律要求)。`mcpowers-code-review` 增 `R14` 反模式条目待跟进(下个 minor 版本)。
- **`mcpowers-code-review` 触发词与 Quick-Check 命令统一为 master 分支(本仓库适配)**:`SKILL.md` 11 处 `main` → `master`(L1 description 触发词 1 处 + 「何时触发」1 处 + 6 段 Quick-Check 命令 9 处),与本仓库实际主分支对齐;`git diff master...HEAD` 替换 `git diff main...HEAD`。

### 风险

- **旧项目默认行为翻转风险**:既有项目若按 v2.x.x 单端实现,新规范默认行为直接翻转会导致用户体验变化(用户现在能在多设备同时登录);必须显式告知产品/运营,或自定义反向键维持单端。
- **Redis 内存占用略增**:多端登录会保留多个 token(每个 TTL 24h),Set 内 token 数量 = 同时在线设备数;极端情况(同账号 100+ 设备)需监控 Set 体积。
- **运维工具不兼容**:Redis Key 名 `token_by_id` → `tokens_by_id`,老的 `keys app:user:token_by_id:*` 排查命令 + 监控告警规则须同步更新。

## v2.31.0 - 2026-08-12

### Breaking Changes

- 无(新增铁律,不破坏既有接口/规范)

### 新增

- **Swagger 接口契约硬门禁(v2.31.0+ 全栈适用铁律)**：写接口文件时 PreToolUse 阶段物理拦截 5 字段契约不合规的写法,避免 commit 时一次性报 20+ 错误导致返工。`hooks/pre-write-confirm-api-hint.sh` 由 v2.4.0 的「软提醒(exit 0)」升级为「真硬门禁(exit 2 + Claude Code confirm UI)」。详见 `CLAUDE.md` 「写 Swagger 接口必须按 5 字段契约」铁律段 + `mcpowers-shared/docs/技术规范/Swagger字段契约.md` + `mcpowers-shared/docs/技术规范/接口契约规范.md §1`。
- **项目自定义必填字段清单机制**：项目根放 `.swagger-required-fields.yml` 可声明项目特有的必填 swagger 字段(如 `deprecated` / `x-permission`);未声明时自动落 mcpowers 默认 5 字段契约清单。YAML 解析失败 → 软警告 + fallback 默认,不阻断开发。详见 `Swagger字段契约.md §2`。
- **新增 Swagger 资产**(集中 helper 模式,不向用户项目注入文件):
  - `skills/mcpowers-shared/scripts/swagger-stack-detect.sh` —— 探测项目是否真用了 swagger(flasgger/apispec/fastapi/springdoc 等),未装 → 直接放行,零摩擦
  - `skills/mcpowers-shared/scripts/swagger-required-fields.sh` —— 加载字段清单(项目优先 + mcpowers 默认 fallback)
  - `skills/mcpowers-shared/scripts/swagger-lint-helper.py` —— 单文件 lint,import 复用 `lint_api_docstrings.py` 的 `parse_python_docstring` + `lint_docstring` 函数
  - `skills/mcpowers-shared/scripts/swagger-contract-check.sh` —— 集中 helper,被 wrapper hook 调用
  - `skills/mcpowers-shared/docs/技术规范/Swagger字段契约.md` + `docs/API契约/默认Swagger必填字段.yml` —— 字段清单机制权威源 + mcpowers 默认清单
- **零新增 hook 槽位**：wrapper hook 复用既有 `pre-write-confirm-api-hint.sh` 路径(仅内部行为从软提醒改硬门禁),`hooks/hooks.json` 零改动。
- **新增审查门禁**：`mcpowers-code-review` 增 R13 反模式条目(swagger 接口 5 字段不完整)+ Quick-Check 段含 3 条扫描命令。

### 修复

- **修复 `check_api_docs_sync.sh` 硬编码路径纪律漏网**：line 100 提示文本的 `python tools/export_docs.py` 改为 `${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/tools/export_docs.py`,符合 v2.29.0 「不向用户项目注入任何文件」纪律(原硬编码假设项目里有 tools/export_docs.py,与 v2.29.0 wrapper→helper 集中模式冲突)。

### 调整

- **规范体系从 31 → 32 份**:`Swagger字段契约.md` 是新增第 32 份规范(stability: evolving),`mcpowers-spec-index/SKILL.md` 「做什么 → 读哪个规范」表同步更新。
- **`mcpowers-feat` 自检清单强化**：v2.31.0+ 写 Swagger 接口必须按 5 字段契约,`skills/mcpowers-feat/SKILL.md` 自检清单项加版本标注。

### 风险

- **lint 性能成本**：每次 Write hook 跑 6 → 7 个脚本(本版本新增 swagger-stack-detect + swagger-required-fields + swagger-lint-helper),Python 解释器启动开销 ~500ms,Write 总成本 ~1.7s。在可接受范围,未做 daemon 模式优化(YAGNI);若用户投诉再优化。
- **confirm UI 是软门禁**：用户一键放行时仍能写不合规的接口文件——这是 Claude Code hooks 固有限制,不是 mcpowers 能解决的。真正硬门禁在用户项目的 CI;铁律价值是「让 AI 在写完那一刻意识到漏写」,不是「强制阻止提交」。
- **非 Python 栈(JS/TS router)暂不校验**:`swagger-lint-helper.py` 只支持 Python(Flasgger docstring 解析),JS/TS 路由文件命中快速过滤后直接放行(YAGNI,不补全栈模板)。FastAPI / Spring Boot 等其他栈留给项目自定义 `.swagger-required-fields.yml` 走「必填字段名」层校验。

## v2.30.0 - 2026-08-12

### Breaking Changes

- **`create_app(protect_swagger=...)` 形参删除**：`Flask后端规范.md §3.1` 应用工厂不再接受 `protect_swagger` 形参。Swagger 是否启用完全由 `ENV_TYPE` 自动判断（生产环境硬禁用，非生产环境默认启用+Basic Auth）。升级前请检查项目 `apps/__init__.py` 是否传 `protect_swagger=...` 调用——如有，**必须删除**该关键字参数，否则启动抛 `TypeError`。
- **`register_swagger(app, protect=...)` 形参删除**：`Flask后端规范.md §11.1` 函数签名瘦身为 `register_swagger(app)`。`protect` 形参原本用于「dev/test 环境下是否加 Basic Auth」，新版改为 `app.config['TESTING']` 动态判断（钩子内部 `if app.config.get('TESTING'): return`），对调用方零时序要求。
- **配置文件示例字段名变更**：`config_{env}.ini` Swagger 凭据字段从旧代码读法（顶层扁平 `swagger_user / swagger_password`，**与配置示例错位导致保护静默失效——本版本修复**）改为 `[swagger] user / password` 段。**升级时如按旧示例配置（`[swagger] user=admin password=admin123`），新版代码能正确读取——但旧示例配置的弱凭据须替换为强密码**；如按旧代码读法配置（顶层 `swagger_user=...`），**启动会抛 `RuntimeError`**（fail-fast，不允许静默放行 Swagger）。
- **Swagger 凭据默认占位符**：配置文件示例 `[swagger]` 段从 `user = admin / password = admin123` 改为 `<部署时填入的强密码，禁止 admin/test/123456 等弱密码>`。**升级时必须替换占位符为强密码**，否则启动崩溃（fail-fast）。推荐生成命令：`openssl rand -base64 16`。

### 修复

- **修复 Swagger Basic Auth 保护完全失效的安全漏洞**：旧代码 `register_swagger` 内部读 `app_conf.get('swagger_user')`（默认 `[app]` 段），但配置文件示例写在 `[swagger].user`——字段名错位导致 `swagger_user = swagger_pass = None`，Basic Auth 比对条件 `not (None==None and None==None) = False` 永远不触发，**所有请求的 401 拦截形同虚设，任何人访问 Swagger 都通过**。新版改为读 `app_conf.get('swagger', 'user')` 与配置对齐 + 加 `RuntimeError` fail-fast（凭据缺失或为空字符串则启动崩溃），杜绝静默放行。
- **修复 Swagger 启用决策「默认反模式」**：旧 `create_app(protect_swagger=True)` 默认「启用+加 Basic Auth」，调用方必须在生产环境**主动传 `False`** 才能符合规范「仅非生产环境可用」铁律（违反 Secure by Default）。新版删除该形参，由 `ENV_TYPE` 自动判断——**调用方无需也无法在生产环境手动启用 Swagger**，安全决策下沉到环境配置。
- **修复 `protect_swagger` 钩子时序耦合**：旧钩子在 `register_swagger` 内部注册，依赖调用方在 `create_app()` **之前**设 `app.config['TESTING']=True`；测试场景 fixture 普遍是「先 `create_app()` 再设 TESTING」→ 钩子已注册，TESTING 已晚。新版改为钩子内部动态判断 TESTING，**对调用方零时序要求**。
- **修复 Swagger 默认弱凭据反模式**：配置文件示例引导用户写 `admin/admin123`，等于把生态安全基线拉到「教程级」；新版改占位符 + 推荐生成命令，禁止照抄弱密码。

### 调整

- `Flask后端规范.md §3.1`：`create_app()` 不再接受形参；删除「生产环境应传 False」误导性注释。
- `Flask后端规范.md §11.1`：`register_swagger(app)` 函数签名瘦身为无参；新增 docstring 说明 ENV_TYPE 决策逻辑 + TESTING 动态判断语义。
- `Flask后端规范.md §4.2`：配置文件示例 `[swagger]` 段从默认弱凭据改为占位符 + 推荐 `openssl rand -base64 16` 生成命令 + ⚠️ 禁止弱密码警告。
- `Flask后端规范.md §11.1`：Basic Auth 钩子改为从 `[swagger].user/password` 读取凭据，加 fail-fast `RuntimeError` 校验；钩子内部加 `if app.config.get('TESTING'): return` 动态判断。
- `数据库规范.md §3.2`、`测试规范.md §3.1`、`健康检查规范.md §2.2`：调用方代码从 `create_app(protect_swagger=False)` / `(protect_swagger=True)` 改为 `create_app()`（测试 fixture 的 `TESTING=True` 保留，钩子动态判断生效）。
- `export_docs.py`：`create_app(protect_swagger=False)` 改为 `create_app()` + 显式 `app.config['TESTING']=True`，让 `register_swagger` 钩子动态跳过 Basic Auth（test_client 拉 `/apispec_1.json` 不被 401 拦掉）。
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`：version bump `2.29.3 → 2.30.0`（3 处同步，接口签名变更走 minor 而非 patch）。

### 风险

- **老项目升级可能直接启动崩溃**：本次改动涉及 3 处用户级破坏——`create_app` 形参删除、`register_swagger` 形参删除、配置文件示例字段名变更 + 默认占位符强制强密码。**升级 mcpowers 到 v2.30.0 前请检查**：①项目 `apps/__init__.py` 是否传 `protect_swagger=...`；②`config_{env}.ini` 是否用旧 `swagger_user/swagger_password` 顶层键（旧代码读法，已无效）；③`[swagger]` 段是否仍写 `admin/admin123` 默认凭据（新版 fail-fast，缺失或弱密码直接崩溃）。任一项命中需先迁移再升级。
- **无新增机制**：本次为纯接口签名删除 + 字段名统一 + fail-fast 收紧，不引入新配置项、新依赖、新概念；mcpowers 自身运行时无变化（仅规范文档 + 工具脚本示例代码改动）。

## v2.29.3 - 2026-08-11

### Breaking Changes

无（向后兼容：仅删除从未在 compose 模板中落地的注入策略描述，`Config.get()` 读 ini 的既有机制完全不变；已按旧描述搭了 envsubst 的项目继续可用，但新代码不应再这么写）

### 修复

- **修复「禁止使用环境变量」最高铁律与 Flask 栈级落地自相矛盾（4 处）**：铁律禁 Shell 从外部环境读 `${XXX}`，但 `Flask后端规范.md §4.2` 却要求 test/prod 用 `docker-compose environment:` 注入 `${SECRET_KEY}` 占位符 + 容器启动时 `envsubst` 替换进 ini——该链路终点是 `Config.get()`，**已进入代码运行时**，不满足白名单例外「不进入 mcpowers 代码运行时」的成立前提，AI 读栈级规范时会照着生成 envsubst 方案从而架空铁律（hook 只扫 `.py`，扫不到 entrypoint 里的 envsubst）。
- `Flask后端规范.md`：删除 §4.2「敏感信息注入策略（强制）」整段（该策略在 §21.2 / §21.3 / §21.4 / §21.7 的 compose 模板中从未落地，模板 `environment:` 只有 `TZ`，属悬空死文字）；§4.2 `[swagger]` 注释去掉「test/prod 通过 docker-compose environment 注入」；§21.7.3 生产环境推荐去掉「（环境变量配置连接信息）」。
- `代码规范.md`：铁律 ✅ 正确示例第 66 行去掉尾注「dev 直写、prod 由 docker-compose environment: 注入 ini」——该注释位于铁律正文自身的正例区，等于铁律在教人用 environment 注入。

### 调整

- `CLAUDE.md`：环境变量铁律段补充 v2.29.3 边界澄清——`environment:` 例外仅限值不回流到代码的场景（`TZ`、MySQL 官方镜像 `MYSQL_ROOT_PASSWORD`）；禁止 `envsubst` 把环境变量替换进 ini / yaml 占位符；敏感字段各环境一律直接写在项目自己的 `config_{env}.ini` 里。
- `Flask后端规范.md` frontmatter：`version 1.1 → 1.2`；`代码规范.md` frontmatter：`version 1.5 → 1.6`、`last_updated 2026-08-05 → 2026-08-11`（两者 `last_breaking_change` 均不变，本次非破坏性变更）。
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`：version bump `2.29.2 → 2.29.3`（3 处同步）。

### 风险

- 无新增机制：本次为纯删除 + 措辞修正，不引入配置文件挂载、`.gitignore` 约定等任何新方案；`config_{env}.ini` 仍是项目内文件，由 `Config` 单例直接读取。

## v2.29.2 - 2026-08-11

### Breaking Changes

无（向后兼容：新增铁律仅约束新增代码默认行为，已有配置 `LOG_CONSOLE_COLOR=True` 不受影响；min-module / sdk-design 内置日志默认值升级为 plain formatter 仅影响 v2.29.2+ 之后产出的库）

### 新增

- **日志规范 §7.6 升级为跨语言总章铁律（v2.29.2+）**：把「控制台默认无颜色」从 v2.29.1 的「项目级 + 配置开关」升级为 v2.29.2 的「项目级 + 模块内置 + 任何环境」三合一总章铁律：(1) **任何环境（dev / test / staging / prod）一律默认关**——颜色开关不区分部署阶段，开发环境不会因为「dev 就该有颜色」而默认开；(2) **min-module / sdk-design 内置日志工厂硬编码默认即合规**——不假设调用方会传配置，开箱即无颜色；(3) **配置默认值全环境 `False`**——只有外部项目配置文件（如 Flask `config.ini [log]`）里 `console_color` 才允许暴露给运维；默认值仍是 `False`。
- **新增 `日志规范.md §7.6.4`「min-module / sdk-design 内置日志默认值」段**：给出 Python 参考实现（硬编码 `logging.Formatter` + `sys.stdout` + INFO 级别）+ 跨语言反例（JS / Go / Rust / Java），明确「模块内置硬编码走 colorlog」= 违规。
- **新增 `日志规范.md §7.6.5`「全栈反例清单」段**：9 条 Critical 反模式（Python 模块内置 colorlog / 默认 DEBUG / 默认 stderr / 宽度填充级别 / Go ForceColors / JS colorize / Rust with_ansi(true) / Java ConsoleHandler ANSI / 模块读环境变量判断颜色）。

### 修复

- 修复 min-module §4 日志默认行为描述：从 v2.29.1「INFO+stdout+紧凑+无颜色」升级为 v2.29.2「硬编码默认即合规 + 零配置即符合 §7.6」，并新增 Python 内置日志工厂参考实现段。
- 修复 min-module §11 自检清单：同步 v2.29.2 描述。
- 修复 sdk-design §11 自检清单 + 反模式章节：与 min-module §4 保持一致。

### 调整

- `日志规范.md` frontmatter：`version 2.7.1 → 2.7.2`；`last_breaking_change: v2.26.0 → v2.29.2`；`description` 强化 v2.29.2「任何环境一律默认关 + 模块内置即合规」语义。
- `Flask后端规范.md §6.1`：LOG_CONSOLE_COLOR 注释强化「v2.29.2+ 颜色开关任何环境一律默认关」；控制台 formatter 三态注释同步；§6 顶部引用句升级。
- `爬虫规范.md §12`：控制台输出引用句升级，明确「禁止读环境变量判断颜色开关」。
- `mcpowers-code-review/SKILL.md`：R12 反模式条目强化 v2.29.2「零配置即合规」表述；Quick-Check 段标题从 `v2.29.1+` 改为 `v2.29.2+` 并新增第 4 条命令（**模块内置日志硬编码默认值扫描**——即便在硬编码常量里出现 ColoredFormatter 也视为违规）。
- `CLAUDE.md`：v2.29.1 段升级为 v2.29.2，描述「任何环境一律默认关 + min-module/sdk 内置即合规 + 4 条 Quick-Check 命令」。
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`：version bump `2.29.1 → 2.29.2`（3 处同步）。

## v2.29.1 - 2026-08-11

### Breaking Changes

- 无。`mcpowers-min-module/SKILL.md §4` 默认行为描述修复 + 新增 `日志规范.md §7.6`「默认无颜色」铁律 + `Flask后端规范.md §6.1` `utils/loggings.py` 模板默认走 plain formatter（新增 `LOG_CONSOLE_COLOR = False` 配置项）。**向后兼容**：旧项目升级时仅需在 `config.ini` `[log]` 段加 `console_color = True` 即可恢复旧行为（彩色文本 + colorlog 默认 padding 后 `reset=True` 抑制 + `[INFO]` 紧凑级别 + `stream=sys.stdout`）。

### 新增

- **跨语言铁律**：[`日志规范.md`](skills/mcpowers-shared/docs/技术规范/日志规范.md) §7.6「默认无颜色（v2.29.1+ 强制）」⭐——除非用户主动配置，控制台 formatter **默认**走 plain formatter（无 ANSI 转义序列）。含 5 语言对照表（Python `logging.Formatter` / JS `winston.format.simple()` / Go `slog.NewTextHandler` / Rust `tracing-subscriber::fmt` 默认 / Java `java.util.logging.Formatter`）+ 4 类默认开颜色污染场景（复制粘贴 / 管道 / 文件重定向 / 日志聚合平台染红）+ Python 参考实现（含 `LOG_CONSOLE_COLOR` 配置项 + 三态分支 `LOG_CONSOLE_JSON=True` → JSON / `LOG_CONSOLE_COLOR=True` → 彩色文本 / 全 False → 纯文本）+ 反例清单（默认 `colorlog.ColoredFormatter` / `logrus ForceColors: true` / `winston.format.colorize()`）。
- **反模式条目**：[`日志规范.md`](skills/mcpowers-shared/docs/技术规范/日志规范.md) §10 黑名单增 #14（默认走 colorlog / `winston.format.colorize()` / `logrus ForceColors: true` 等开颜色）。

### 修复

- **[`skills/mcpowers-min-module/SKILL.md`](skills/mcpowers-min-module/SKILL.md) §4 自包含日志系统设计**：原描述「日志默认行为：DEBUG 级别 + stderr 输出 + 毫秒时间戳 + 8 字符等宽级别名」同时违反 v2.28.4 两条铁律（`stderr` 默认走 + `%(levelname)-8s` 宽度填充）——改为「INFO 级别 + stdout 输出 + 毫秒时间戳 + **紧凑级别**（无宽度填充）+ **默认无颜色**（仅 `LOG_CONSOLE_COLOR=True` 才开）」，并加 `日志规范.md §7.5 §7.6` 引用。§4 完成后自检清单行同步：原「默认 DEBUG+stderr」改为「默认 INFO+stdout+紧凑级别+无颜色」。

### 调整

- **[`Flask后端规范.md`](skills/mcpowers-shared/docs/技术规范/Flask后端规范.md) §6.1 `utils/loggings.py` 模板**：①加 `LOG_CONSOLE_COLOR = config.getboolean('log', 'console_color', fallback=False)` 配置项（v2.29.1+ 默认 `False`）；②控制台 formatter 改为三态分支：`LOG_CONSOLE_JSON=True` → `json_formatter` / `LOG_CONSOLE_COLOR=True` → `colorlog.ColoredFormatter(reset=True)` / 全 False → `logging.Formatter(CONSOLE_FORMAT)` plain 模式（原 `else` 分支无条件走 `colorlog.ColoredFormatter` 已不返）；③§6 顶部描述加 v2.29.1 + §7.6 引用；④frontmatter `last_updated: 2026-08-10` → `2026-08-11`、`last_breaking_change: v2.28.4` → `v2.29.1`。
- **[`爬虫规范.md`](skills/mcpowers-shared/docs/技术规范/爬虫规范.md) §12**：控制台输出行加 v2.29.1+ §7.6 引用——爬虫项目复用 Flask `get_logger` 三态控制台 formatter，默认无颜色（仅 `LOG_CONSOLE_COLOR=True` 才走 `colorlog.ColoredFormatter`）。
- **[`日志规范.md`](skills/mcpowers-shared/docs/技术规范/日志规范.md) §7.4 控制台 vs 文件的格式差异表**：开发环境颜色列从「开启（DEBUG=cyan / INFO=green / WARNING=yellow / ERROR=red）」改为「**默认关闭**（v2.29.1+）——仅当用户在配置 `LOG_CONSOLE_COLOR=True` 时才开」；§7.4 末尾「格式切换由配置文件控制」单 `LOG_CONSOLE_JSON` 改 `LOG_CONSOLE_JSON + LOG_CONSOLE_COLOR`。
- **[`mcpowers-code-review/SKILL.md`](skills/mcpowers-code-review/SKILL.md)** R1-R12 反模式表增 **R12**「控制台 formatter 默认走 colorlog / winston.format.colorize() / logrus ForceColors: true 等开颜色」（v2.29.1+）；新 Quick-Check 段「v2.29.1+ 默认无颜色 Quick-Check」含 3 条扫描命令（Python `setFormatter(...ColoredFormatter)` 缺配置开关 / JS-Go-Rust 默认颜色参数 / `console_color` 默认值 `True`）。
- **[`CLAUDE.md`](CLAUDE.md)**：v2.28.4+ 铁律段后加 v2.29.1+「控制台默认无颜色」段（含 4 类污染场景 + 跨语言对照 + `LOG_CONSOLE_COLOR` 配置项 + 审查门禁 R12 + Quick-Check 3 命令）。
- **版本号 bump**：`plugin.json` / `marketplace.json` 顶层 + `plugins[0]` `version` 2.29.0 → 2.29.1（patch bump：纯加新铁律 + 修历史违规 + 模板默认行为变更 + 新增 R12 审查维度，**无破坏性变更**，向后兼容）。

## v2.29.0 - 2026-08-11

### Breaking Changes

- **废弃**：`mcpowers-doc-sync-install` 技能（`skills/mcpowers-doc-sync-install/SKILL.md` + 整个目录）+ 5 个 `scripts/templates/project-doc-sync-*` 模板 + 整个 `scripts/templates/` 目录已删除。可路由技能 33 → 32（24 场景 + 8 方法）；路由器 SKILL.md L1 description、强制分流表、§3.2 方法层清单、§2.4 多意图裁决段 4 处已同步移除 `doc-sync-install`。**用户手动清理**：已装项目（v2.9.0 ~ v2.28.4 期间使用过 `mcpowers-doc-sync-install` 的）需手动删除 `scripts/check-doc-sync.sh` + `.doc-sync-rules.yml` + `.git/hooks/pre-commit` 里 doc-sync 段，mcpowers v2.29.0+ 不再生成这些文件。

### 新增

- **物理门禁**：[`hooks/pre-write-check-doc-sync.sh`](hooks/pre-write-check-doc-sync.sh)（v2.29.0+ 强制）：PreToolUse(Write|Edit|MultiEdit) hook；快速过滤可能影响 doc 同步的文件路径（README / `app/*.py` / `src/router/*.ts` / `scripts/*.sh` / `.env.example` / `requirements.txt` / `package.json`）→ 调 [`skills/mcpowers-shared/scripts/doc-sync-check.sh`](skills/mcpowers-shared/scripts/doc-sync-check.sh)（v2.29.0+ 新增）→ 失败 exit 2 触发 Claude Code confirm UI。和现有 `pre-write-check-duplicate.sh` / `pre-write-check-import.sh` / `pre-write-check-spec-frontmatter.sh` 同档次物理门禁。**不向用户项目注入任何文件**，装 mcpowers 即自动支持。
- **集中 helper**：[`skills/mcpowers-shared/scripts/doc-sync-check.sh`](skills/mcpowers-shared/scripts/doc-sync-check.sh)（v2.29.0+ 新增）：三类检查 `path_in_doc`（README 中 `scripts/*.sh` / `bin/*.py` 路径必须真实存在）+ `route_in_doc`（`@app.route` / `createRouter` 路径必须出现在 `docs/api.md` / `docs/API文档/API文档.md` / 视图 docstring）+ `env_in_doc`（`.env.example` 中所有 KEY 必须出现在配置文档）。可被 hook 自动调用，也可在对话里手动跑 `bash ${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/scripts/doc-sync-check.sh`。
- **hooks.json 注册**：[`hooks/hooks.json`](hooks/hooks.json) 在 PreToolUse(Write) 与 PreToolUse(Edit|MultiEdit) 两个 matcher 下各加一行调 `pre-write-check-doc-sync.sh`。事件组计数仍为 4（SessionStart / PreToolUse-Bash / PreToolUse-Write+Edit+MultiEdit / PostToolUse）；脚本数 8 → 9。

### 调整

- **[`skills/mcpowers/SKILL.md`](skills/mcpowers/SKILL.md)**：L1 description `doc-sync-install` 移除；强制分流表第 59 行删；§2.4 多意图裁决段第 114 行（`install-basics-skills` vs `doc-sync-install`）删；§3.2 方法层清单删；§4 末尾可路由技能数 33 → 32。
- **[`skills/mcpowers-init/SKILL.md`](skills/mcpowers-init/SKILL.md)**：移除 5 处 `mcpowers-doc-sync-install` 引用（编排表 / 阶段 C 选项 / "目标"段 / cp 命令 / 收尾清单）。init 阶段不再自动装 doc-sync——纪律由 mcpowers hook 全局接管。
- **4 个场景技能自检清单**：[`mcpowers-feat`](skills/mcpowers-feat/SKILL.md) / [`mcpowers-bugfix`](skills/mcpowers-bugfix/SKILL.md) / [`mcpowers-refactor`](skills/mcpowers-refactor/SKILL.md) / [`mcpowers-requirement-change`](skills/mcpowers-requirement-change/SKILL.md) 自检清单里「如项目已装 .doc-sync-rules 纪律，已跑 `bash scripts/check-doc-sync.sh` 验证」行删除——hook 已自动物理检查，AI 不再需要手动跑脚本。
- **[`skills/mcpowers-shared/docs/技术规范/代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)** 第 185 行 `项目级纪律 v{major}.{minor}.{patch}（由 mcpowers-doc-sync-install 注入）` 注释删除；保留"禁硬编码版本号"通用规则。
- **[`CLAUDE.md`](CLAUDE.md)**：§核心结构表 + §触发条件 + §设计维度 总数 33 → 32；hooks/ 行由「4 事件组 / 8 脚本」扩到「4 事件组 / 9 脚本」+ 加 v2.29.0+ doc-sync 物理门禁说明；注入物版本号写死禁令段里的 `.doc-sync-rules.yml` / `.doc-sync-check.sh` 模板示例移除。
- **[`README.md`](README.md)**：计数 + 目录树 + 触发映射表 + 平台支持矩阵 6 处同步；hooks 行扩到 9 脚本 + v2.29.0+ doc-sync 物理门禁说明。
- **版本号 bump**：`plugin.json` / `marketplace.json` 顶层 + `plugins[0]` `version` 2.28.4 → 2.29.0（minor bump：删除技能 + 新增物理门禁 = 能力增减而非接口破坏）；顶层 description「25 场景 + 8 方法」→「24 场景 + 8 方法」；`plugins[0].description`「33 个技能」→「32 个技能」。

## v2.28.4 - 2026-08-10

### Breaking Changes

- 无。`日志规范.md` 新增 §7.5「级别紧凑打印 + 控制台输出流」2 条铁律（仅约束以前默认行为不正确的实现，**不改变任何已符合预期实现的用户项目**）；`Flask后端规范.md §6.1` `utils/loggings.py` 实现层同步对齐新铁律（compact 级别 + stdout）。对早已实现 `stream=sys.stdout` 的项目 0 行为变更；对依赖 colorlog 默认 padding（输出 `[INFO   ]`）的项目从下次部署起输出 `[INFO]`，CR 看新 diff 时按 R11 兜底。

- **新增**：[`日志规范.md`](skills/mcpowers-shared/docs/技术规范/日志规范.md) §7.5「级别紧凑打印 + 控制台输出流（v2.28.4+ 强制）」——含 2 条铁律：①**级别字段必须紧凑**（formatter 用 `%(levelname)s` 或 `%(levelname).1s`，禁止 `%(levelname)-8s` / `%(levelname)-5s` 等宽度填充；colorlog 默认会把 `%(levelname)s` 改写为 `%(levelname)-8s`，需 `reset=True` 抑制）；②**控制台 handler 必须显式 `stream=sys.stdout`**（禁止 `logging.StreamHandler()` 默认 stderr —— PyCharm / IntelliJ 会把 stderr 整体染红，即使日志级别是 INFO / DEBUG）；§7.4 控制台 vs 文件的格式差异 表加 1 行说明；§10 反模式黑名单 加 #12（控制台 formatter 宽度填充）和 #13（StreamHandler 默认 stderr）两条 Critical；§12 自检清单加 2 条（级别紧凑 + stdout）。
- **调整**：[`Flask后端规范.md §6.1`](skills/mcpowers-shared/docs/技术规范/Flask后端规范.md) `utils/loggings.py` 实现层对齐 §7.5——①`import sys` 加到 import 区；②`CONSOLE_FORMAT = '%(asctime)s [%(levelname)s] [%(log_type)s] %(name)s - %(message)s'` 注释加 §7.5.1 引用（本身已无宽度填充，配合 `reset=True` 才能不被 colorlog 改写）；③`console = logging.StreamHandler()` → `console = logging.StreamHandler(stream=sys.stdout)`；④`colorlog.ColoredFormatter(...)` 加 `reset=True` 抑制默认 padding；§6 顶部描述同步加 v2.28.4 + §7.5 引用；frontmatter `last_updated: 2026-08-05` → `2026-08-10`、`last_breaking_change: v2.22.0` → `v2.28.4`。
- **调整**：[`爬虫规范.md §12`](skills/mcpowers-shared/docs/技术规范/爬虫规范.md) 加 1 行 v2.28.4+ 引用「控制台输出 → 见 `日志规范.md §7.5`」——爬虫脚本常在 PyCharm / VSCode 跑任务，依赖 Flask §6.1 的 `get_logger` 控制台 handler 已显式 `stream=sys.stdout` + `reset=True` 级别紧凑；爬虫项目禁止自行实现控制台 handler。
- **调整**：[`mcpowers-spec-index/SKILL.md`](skills/mcpowers-shared/mcpowers-spec-index/SKILL.md) 查表行「任何写日志 / 排查日志 / 设计日志体系」补 v2.28.4+ §7.5 描述；规范树注释 + 加载指引同步。
- **新增**：[`mcpowers-code-review/SKILL.md`](skills/mcpowers-code-review/SKILL.md) R11 反模式条目（v2.28.4+ 控制台日志级别未紧凑打印 / StreamHandler 未显式指定 stdout——`日志规范.md §7.5`）+ 新 Quick-Check 段「v2.28.4+ 控制台日志级别紧凑 + stdout Quick-Check」含 2 条扫描命令（`%(levelname)-Ns` 宽度填充 + `StreamHandler()` 未传 stream）。
- **调整**：[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) `version` `2.28.3` → `2.28.4`（patch bump，纯日志实现层约束加固）；[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) 顶层 `version` + `plugins[0].version` 同步 bump。
- **风险**：仅日志控制台输出的**格式细节**变更（输出长度变化 + 流方向变化）——级别从 `[INFO   ]`（8 字符）→ `[INFO]`（6 字符），stdout 流从应用控制可见改为显式；**stderr 现在不再被应用控制**，若有项目需要把 ERROR+ 同时输出到 stderr，由 §6.1 的「ERROR+ 聚合流 `error.log`」+ 配置文件 `LOG_CONSOLE_JSON=False`（走 stdout 文件输出）兜底，不要用 stderr 双跑。CI 门禁 `bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh` 全绿。

## v2.28.3 - 2026-08-10

### Breaking Changes

- 无。纯 SKILL.md 内部文档优化 + 元数据同步，不改变任何技能行为、Hook 检测、CI 门禁、规范。

- **调整**：[`skills/mcpowers-sdk-design/SKILL.md`](skills/mcpowers-sdk-design/SKILL.md) 在「§0 绝对零业务审计」之后、「核心定义」之前插入「与 min-module 的边界精确对比」段——含 3 个子段：①一句话定位表（min-module vs sdk-design 各一句）②12 维度差异矩阵（基础铁律 4 项继承 + SDK 升级点 8 项 + 典型产物对照）③复用机制对照表（5 行允许/禁止清单：允许 `from x import` 公开 API + SDK 自重写四件套；禁止 拷贝 `_internal_helper` / `_private_func` / `cp -r` 整个目录）。位置选择理由：新读者读 SKILL.md 时先建差异化认知，再读硬性约束清单，避免"读着读着把 SDK 当成 min-module"。
- **调整**：[`skills/mcpowers-min-module/SKILL.md`](skills/mcpowers-min-module/SKILL.md) 在「关联技能」之前插入「与 sdk-design 的边界精确对比」反向对偶段——含一句话「何时升级到 SDK」判定指引 + 9 维度反向对比表 + 一行相对路径指向 sdk-design SKILL.md 的详细段（不复制内容，遵循 CLAUDE.md 单一权威源门禁）。
- **调整**：[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) `version` 2.28.2 → 2.28.3（patch bump，纯 SKILL.md 文档优化）；[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) 顶层 `version` + `plugins[0].version` 同步 bump。
- **风险**：0 行为变更对外；纯 SKILL.md 文档强化 + 元数据同步；不动 description / frontmatter / 技能清单 / 路由 / 规范 / Hook；`mcpowers-spec-index` 不变；CI 门禁 `bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh` 全绿。

## v2.28.2 - 2026-08-09

### Breaking Changes

- **有**。重复函数检测 hook 行为从「v2.27.6~v2.28.1 的 4 类启发式分级（单行透传 block / 命名空间跨段 / 签名差异 / 绑定方法混搭 → warn 放行 + 默认 block）」改为 **v2.28.2+ 极简判定：跨文件同名默认放行，只保留「同文件重名（真 bug）」+「单行透传 wrapper（gold standard 二次包装）」两类 block**。原本依赖 hook 拦截「跨文件同名业务模块各自实现的 parse(data)」等场景的用户将不再被拦截；其余二次包装反模式由 `mcpowers-code-review` R1-R6 黑名单 + 同文件重名 / 单行透传两类 block 兜底。

- **调整**：[`hooks/check_duplicate_function.py`](hooks/check_duplicate_function.py) 重复函数检测 hook 行为简化（v2.28.2+）——删除 3 类启发式降级（命名空间 / 签名 / 绑定方法）+ 删除 `classify_namespace` / `is_cross_namespace` / `normalize_params` / `is_bound_method` / `decide_severity` / `format_warn_message` 等约 80 行代码 + 新增 `count_in_source(source, name)` 实现同文件内重名检测 + 重写 `hook_main` 主流程为 3 档判定：①同文件重名 count ≥ 2 → block ②跨文件同名 + `is_one_line_wrapper` 命中 → block ③其他跨文件同名 → 放行（不计入 duplicates）。理由：跨文件同名是合法常态（业务模块各自的 `parse(data)`），原 4 类启发式是给「过度拦截」打补丁，源头砍掉后不需要补丁；`is_one_line_wrapper` 是唯一值得保留的精准信号（gold standard，命中即真二次包装）。
- **修复**：[`hooks/check_duplicate_function.py`](hooks/check_duplicate_function.py) 修复「同文件内重名漏报」反向 bug——`git_grep_duplicate` 原本显式跳过新文件自身（`if rel == rel_path: continue`），意味着同一文件里写两个 `def foo()` 的真 bug（Python 后者覆盖前者，导致静默丢失前一个实现）反而被 hook 漏过；v2.28.2+ 通过 `count_in_source` 主动扫描新内容内的同名定义数，count ≥ 2 即 block；同时原 hook 也漏报「新增内容自身重名」场景（如 `Write` 内容里既有 `def foo` 又新增 `def foo`），新逻辑一并覆盖。
- **调整**：[`代码规范.md §6.1.1`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 表格从 5 行（单行透传 / 命名空间 / 签名 / 绑定 / 默认）简化为 3 档（同文件重名 / 跨文件同名 + 单行透传 / 跨文件同名其他情况），删掉「降级候选语义」「入口命名豁免（与具体启发式无关）」等过时描述；豁免段重写为「入口命名 + Python dunder 协议方法 + 单下划线私有名」3 类明确豁免；frontmatter `last_breaking_change` 字段 `v2.27.6` → `v2.28.2`；新增「为什么跨文件同名默认放行」段说明 v2.27.6 启发式是设计缺陷、v2.28.2 回归极简原则。
- **调整**：[`mcpowers-code-review/SKILL.md`](skills/mcpowers-code-review/SKILL.md) R10 反模式条目从「v2.27.6 启发式分级（命名空间 / 签名 / 绑定 / 单行透传）」改为「v2.28.2+ hook 已简化（跨文件默认放行 + 同文件重名 + 单行透传 block）」+ 旧 R10 描述（4 类典型合法重名被误报）作为 v2.27.6 历史问题归档；Quick-Check 段从「v2.27.6+ 启发式分级」改为「v2.28.2+ 单行透传」（hook 已自动处理单行透传 + 同文件重名，review 主要兜底扫描）；审查动作清单第 4 条「同名函数跨文件出现 ≥ 2 次」加「看是否真有共性」判断条件——hook 默认放行后由 review 判断是否属真重复（命中则提 `mcpowers-extract`）。
- **调整**：[`hooks/README.md`](hooks/README.md) 重复函数检测行描述从「v2.26.0+ 防过度抽象——与仓库已有同名定义冲突时弹 confirm UI」改为 v2.28.2+ 新行为描述。
- **调整**：[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) `version` `2.28.1` → `2.28.2`（patch bump；行为简化为修复过度拦截）+ [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) 顶层 `version` + `plugins[0].version` 同步 bump。
- **风险**：跨文件同名从 block 改为放行——原本依赖 hook 拦截的业务模块同名（业务模块各自的 `parse(data)` 等）的用户**不再**被 hook 拦截；同文件重名 + 单行透传 wrapper 仍被 block（这 2 类是真 bug 的兜底）；其余二次包装反模式（命名空间统一 / 跨项目搬运 / 抽象类单实现 / 公共函数零调用方）由 `mcpowers-code-review` R1-R6 黑名单 + PR 审查兜底；前端写代码时若依赖旧 hook 行为（看到重名就拦）会有反直觉感，需要让团队升级到 v2.28.2+ 行为。CI 门禁 `bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh` 全绿。

## v2.28.1 - 2026-08-06

### Breaking Changes

- 无。「绝对零业务」是 v2.28.0 已建立的零业务审计强度的**精确化命名**——把原来 13/14 条规则中的"零业务字眼"提升为定义性铁律 + 增加 4 类新禁止项（外部参考字眼 / 其他项目路径 / 模块名业务前缀 / docstring 错误消息业务字段），不改变既有行为。

- **强化**：[`skills/mcpowers-min-module/SKILL.md`](skills/mcpowers-min-module/SKILL.md) 「绝对零业务」升级为定义性铁律——v2.28.0 的"零业务字眼"只是 7 条规则中的一条，v2.28.1 提升为 **§0 绝对零业务审计**：① 加 §0 段（7 类禁止字眼 + 7 类例外允许 + 7 条审计命令）；② 通用规则从 7 条平铺重排为 6 条铁律 + 1 条实现细节分层；③ 自检清单独立 §0 段（10 项硬门槛 + 一键脚本兜底）；④ description 关键词加「绝对零业务 / 无任何外部参考 / business-free / no external reference」；⑤ 触发即执行 Step 2 从「零业务字眼审计」改为「§0 绝对零业务审计（强制首步）」；⑥ 编排段铁律从 5 条扩到 6 条；⑦ 反模式段拆为「§0 绝对零业务相关」+「实现细节相关」两层。
- **强化**：[`skills/mcpowers-sdk-design/SKILL.md`](skills/mcpowers-sdk-design/SKILL.md) 同步 §0 强化——加 §0 段；通用规则从 13 条重排为 6 条铁律 + 7 条实现细节；触发即执行 Step 2 从「混合复用判断」改为「§0 绝对零业务审计（强制首步）」，原 Step 2 顺延为 Step 3；编排段铁律从 7 条扩到 8 条；反模式段拆层；自检清单独立 §0 段（10 项硬门槛 + 一键脚本兜底）；description 关键词加「绝对零业务 / 无任何外部参考」；通讯层中立措辞统一（去掉"段设计参考"等中性参考字眼改为"段结构"，去掉"Node / TS 类似"改为"Node / TS 同理"）。
- **新增**：[`scripts/check-min-module.sh`](scripts/check-min-module.sh) §0 绝对零业务审计一键脚本——固化 7 类扫描命令（业务字眼 / 路径字面值 / 环境变量读取 / 真实凭据 / 外部参考字眼 / 其他项目路径 / 模块名业务前缀），支持 `--exclude PATTERN` 排除规则定义文件；任何一项命中退出码 1 + 打印命中位置；CI 物理兜底的轻量替代方案。
- **调整**：[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) `version` 2.28.0 → 2.28.1（patch bump，措辞 / 信息架构调整）；[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) 顶层 `version` + `plugins[0].version` 同步 bump。
- **风险**：0 行为变更对外；纯措辞 / 信息架构 / 元数据层强化；§0 的硬门槛**早就隐含在 v2.28.0 的"零业务字眼"中**——v2.28.1 显式提到禁止位 + 加 4 类新禁止项（外部参考字眼 / 其他项目路径 / 模块名业务前缀 / docstring 错误消息业务字段）；新增 `scripts/check-min-module.sh` 是零依赖半自动扫描（仅依赖 `rg`），不影响既有 33 个技能工作流；CI 门禁 `bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh` 全绿。

## v2.28.0 - 2026-08-06

### Breaking Changes

- 无。仅新增 2 个场景层技能（`mcpowers-min-module` / `mcpowers-sdk-design`），既有 31 个技能、工作流、规范铁律全部保持不变。

- **新增**：[`skills/mcpowers-min-module/SKILL.md`](skills/mcpowers-min-module/SKILL.md) 最小通用模块化场景层技能——把通用技术能力沉淀为「任何项目复制即用、零业务字眼、自包含日志/异常/配置/验证脚本」的最小工具模块。核心判定：①零业务字眼（模块代码 / 注释 / docstring / 配置 / README 不出现具体业务名 / 字段名 / 项目名 / 厂商名）②外部依赖边界（仅该语言标准库 + 直接相关第三方库）③禁止 import 业务模块 ④禁止读环境变量 ⑤自包含四件套（日志 / 异常 / 配置 / 验证脚本）⑥复制即用（任意项目 `cp -r {module_name}/` 即可使用）。SKILL.md 是机制层标准（不绑 Python 模板），用户项目按语言自行实现。
- **新增**：[`skills/mcpowers-sdk-design/SKILL.md`](skills/mcpowers-sdk-design/SKILL.md) SDK 设计场景层技能——把某个特定领域能力（HTTP API / gRPC / WebSocket / 数据库 / 第三方库 / CLI 工具）封装成可独立分发、可 `import`、可调用的 SDK。核心判定：①SDK = 升级版最小模块 + 领域能力封装 + 混合复用判断（用户声明优先 → 轻量扫描 → 集中询问一次 → 自包含兜底）②通讯层中立（HTTP / gRPC / WebSocket / 文件 IO / CLI 包装都支持；不绑具体技术栈）③健康检查硬拒绝（构造时调 `validate()`，发现 `CHANGE_ME` 必填字段未覆盖 → 立即抛 `ConfigError`）④上游错误 vs 客户端错误严格分离（上游错误指数退避重试，客户端错误立即抛业务异常，绝不重试）⑤资源泄漏防护（`with` 块 / `try/finally` / `close()`）+ 路径锚定（`pathlib.Path.home() / ".cache" / "{SDK 名称}"`）。
- **调整**：[`skills/mcpowers/SKILL.md`](skills/mcpowers/SKILL.md) 路由器加 2 行：①强制分流表（line 56 后）新增 `mcpowers-min-module` / `mcpowers-sdk-design` 两条路由 ②场景层清单（line 141 后）新增 `mcpowers-min-module/SKILL.md` + `mcpowers-sdk-design/SKILL.md` 2 条引用 ③路由器 description 段（line 3）补全 `min-module/sdk-design` 关键词 + 「31 行骨架」→「33 行骨架」+「31 个可路由技能」→「33 个可路由技能」。
- **调整**：[`CLAUDE.md`](CLAUDE.md) 顶栏 `skills/mcpowers-*` 行「**31 个可路由技能**（场景层 23 + 方法层 8）」→「**33 个可路由技能**（场景层 25 + 方法层 8）」；触发条件表（line 28-29 后）新增 2 条（`mcpowers-min-module` / `mcpowers-sdk-design`）；设计维度段「31 个可路由技能」→「33 个可路由技能」。
- **调整**：[`README.md`](README.md) 核心功能表「31 个技能（23 场景 + 8 方法）」→「33 个技能（25 场景 + 8 方法）」；技能树（line 87-90 区间）新增 2 行（`mcpowers-min-module/` + `mcpowers-sdk-design/`）；触发条件表（line 200-201 区间）新增 2 行；检查清单「31 个场景/方法技能（23 场景 + 8 方法）」→「33 个场景/方法技能（25 场景 + 8 方法）」；安装说明「31 个可路由技能」→「33 个可路由技能」。
- **调整**：[`scripts/check-readme-sync.sh`](scripts/check-readme-sync.sh) `SCENE_SKILLS` 变量（line 135）末尾追加 `mcpowers-min-module mcpowers-sdk-design`——CI 门禁自动校验 2 个新技能的路由表 / 场景清单 / 描述字符数。
- **调整**：[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) `version` 2.27.6 → 2.28.0（minor 升级，因新增 2 个技能）；[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) 顶层 `version` + `plugins[0].version` 同步 bump + 主入口描述「31 个技能 + 31 个技术规范」→「33 个技能 + 31 个技术规范」+ 数量声明「场景层 23 个 + 方法层 8 个」→「场景层 25 个 + 方法层 8 个」。
- **风险**：无破坏性变更。2 个新技能均为单纯增量（新增文件 + 文档同步），不影响已有 31 个技能的工作流、规范铁律、Hook 行为。CI 门禁 `bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh` 全绿。插件版本号 2.27.6 → 2.28.0。

## v2.27.6 - 2026-08-06

### Breaking Changes

- **block 行为不变**（单行透传 / 启发式全不命中仍 exit 2 + Claude Code confirm UI）。
- **warn 候选改走 exit 0**：命名空间跨段 / 签名差异 / 绑定方法混搭但**不是**单行透传的"合法重名"不再弹 confirm UI——自动放行，仅 stderr 写出 `⚠ [降级 · 合法重名·<理由>]` 提示；如确需强制复用/重命名请手动调整。
- 单行透传（`return <已有函数>(...)` 一行包转发）作为 gold standard，无论是否触发上述任一降级都强化阻断。

- **新增**：[`hooks/check_duplicate_function.py`](hooks/check_duplicate_function.py) 重复函数检测引入 4 类启发式精细化——①命名空间启发式：新文件与命中点都在同一通用命名空间（`utils/ helpers/ common/ lib/ ...`）但不同目录 → 视为模块自治，降级 warn；②签名启发式：参数列表归一化后不同（参数数量 / 第一个参数类型注解）→ 视为同名异义，降级 warn；③绑定方法启发式：新是 `def foo(self, ...)` 命中是模块函数（或反之）→ 视为绑定对象不同，降级 warn；④单行透传启发式（gold standard）：函数体仅一行 `return <已有函数>(...)` → 最经典二次包装，强化阻断（即使触发上述任一降级也仍阻断）。
- **调整**：[`代码规范.md §6.1.1`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 在三段式 Q1/Q2/Q3 + 自检清单之后插入「**v2.27.6 补充：hook 自动启发式分级**」段——把 hook 自动化分级策略与手动 Q1/Q2/Q3 分层标注（Q1/Q2/Q3 是手动判断，本段是 hook 自动兜底），同时说明单行透传强化阻断规则 + warn 候选不弹 confirm UI 的语义。
- **调整**：[`mcpowers-feat/SKILL.md §2.5`](skills/mcpowers-feat/SKILL.md) 「已有资产扫描」段末补 4 行——hook 会按方案 A 自动分级，真复用不必手工判；同命名空间/同名异义/绑定对象不同会被自动放行，仅 stderr 写提示；真二次包装仍被 confirm UI 拦下。
- **调整**：[`mcpowers-code-review/SKILL.md`](skills/mcpowers-code-review/SKILL.md) 「## 反模式（禁止）」段增 R10「**二次包装 vs 合法重名未区分**」条目（v2.27.5 及之前 hook 仅按函数名判定，4 类典型合法重名被误报为重复；R8/R9 已分别被 Python import 局部 / 规范 stability 占用，v2.27.6 反模式序号顺延）；新 Quick-Check 段「v2.27.6+ 启发式分级」增 1 条 `rg` 命令验证「单行透传」。
- **调整**：[`CLAUDE.md`](CLAUDE.md) 与 [`README.md`](README.md) 「复用优先于二次抽象（v2.26.0+ 全栈适用铁律）」段末各加 1 行 v2.27.6 补注。
- **修复**：[`hooks/check_duplicate_function.py`](hooks/check_duplicate_function.py) 入口函数从 `main()` 重命名为 `hook_main()`，避开与 [`hooks/check_spec_frontmatter.py:88`](hooks/check_spec_frontmatter.py) 的 `hook_main` 约定重复；同步 `CONVENTION_NAMES = frozenset({'main', 'hook_main'})` 提供豁免。
- **风险**：warn 候选不再弹 confirm UI 对**真二次包装**无影响（真二次包装走单行透传 gold standard 仍 exit 2 + UI）；受影响的是**合法重名**（同命名空间不同目录、同名异义、绑定对象不同）——自动放行但 stderr 写提示，需要用户主动翻 terminal 日志才能感知。CI 门禁 `bash tests/plugin-verify.sh` 增 4 类用例（命名空间跨段 / 签名差异 / 绑定方法混搭 / 单行透传）共 8 项断言验证；插件版本号 2.27.5 → 2.27.6。

## v2.27.5 - 2026-08-06

### Breaking Changes

- 无。仅减少重复函数 Hook 对 `main()` 入口惯例的误报，不改变其他同名函数检测行为。

- **修复**：`hooks/check_duplicate_function.py` 豁免 Python 模块入口惯例 `main()`，避免独立脚本因共享入口命名而被误判为重复实现。
- **调整**：重复函数 Hook 提示改为准确指向 Claude Code confirm UI，不再暗示检测器自身提供 Y/N 交互。
- **风险**：仅减少入口函数误报；其他公共函数仍按原规则检测。插件版本号 2.27.4 → 2.27.5。

## v2.27.4 - 2026-08-05

### Breaking Changes

- 无。3 条新铁律均为新增约束层（运行时版本访问白名单 / 规范稳定性分级 / CHANGELOG 强制破坏声明），不改动已有行为。
- v2.27.3 注入物版本号写死禁令同样不破坏：v2.27.4 在其基础上增补运行时例外条款，明确"运行时访问历史版本"合法，与原禁令互补。

- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §最高铁律·mcpowers 注入路径稳定性 增「运行时版本访问白名单（v2.27.4+ 全栈适用）」——明确区分"注入物禁硬编码版本号"（v2.27.3+）与"AI 运行时访问历史版本"（v2.27.4+）是两条铁律不冲突；3 种合法访问方式：①AI 主动 `ls ~/.claude/plugins/cache/mcpowers/mcpowers/` 发现用户已装旧版本后 `Read` 读该版本规范 ②项目根存在 `.mcpowers-version: v{major}.{minor}.{patch}` 标记时默认读该版本 ③用户显式"按 v{major}.{minor}.{patch} 规范写"。
- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §最高铁律·mcpowers 注入路径稳定性 增「CHANGELOG 强制破坏声明段（v2.27.4+ 全栈适用）」——每次发布 `CHANGELOG.md` **必须**含 `### Breaking Changes` 段（哪怕标"无"），作为用户升级兼容性的唯一权威索引；mcpowers 仓库自身禁止"minor bump + 破坏性变更"——破坏性变更必须 bump major。
- **新增**：31 份规范 frontmatter 全部增 `stability: stable|evolving|deprecated` + `last_breaking_change: v{major}.{minor}.{patch}` 字段——按 §代码规范.md 稳定性分级铁律 AI 读规范后必读这 2 个字段决定行为（stable 假设跨 minor 兼容 / evolving 升级时主动查 CHANGELOG Breaking Changes / deprecated 不写新代码）；**stability 元数据禁止写回用户项目 CLAUDE.md / 注入物**。
- **新增**：[`AI操作规范.md`](skills/mcpowers-shared/docs/AI操作规范.md) Step 1-4.5「检查规范稳定性分级」——AI 读取每个规范后必读 frontmatter 的 stability + last_breaking_change，按 3 档分别采取不同行为；用户的 `.mcpowers-version` 冻结标记**优先于**最新版 stability。
- **新增**：[`mcpowers-code-review/SKILL.md`](skills/mcpowers-code-review/SKILL.md) 增 R9 反模式条目——未声明 stability / last_breaking_change 就改规范 frontmatter 视为 Critical；审查动作清单增第 6 项"v2.27.4+ 规范 stability 自检"。
- **调整**：[`CLAUDE.md`](CLAUDE.md) 顶层铁律指针段增 3 条 v2.27.4 新铁律（运行时版本访问白名单 / 规范稳定性分级 / CHANGELOG 强制破坏声明）+ 补回 v2.27.3 注入物版本号写死禁令指针（v2.27.3 release 时漏写指针）；[`README.md`](README.md) 核心功能表 §2 / §5 同步标注 v2.27.4。
- **风险**：0 行为变更对外；本次纯规范 / 元数据 / 指针层新增；CI 门禁 `bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh` 验证；插件版本号 2.27.3 → 2.27.4。

## v2.27.3 - 2026-08-05

- **修复**：5 份 doc-sync 注入物模板（[`scripts/templates/project-doc-sync-rules.{generic,flask,vue,crawler}.yml`](scripts/templates/) + [`scripts/templates/project-doc-sync-check.sh`](scripts/templates/project-doc-sync-check.sh)）头部 `v2.9.0 L2 项目级纪律（由 mcpowers-doc-sync-install 注入）` 硬编码版本号违反 v2.26.2+ 「mcpowers 注入路径稳定性」铁律——升级时模板内残留旧版本号。统一改为「本文件对应 mcpowers 最新版本的纪律 / 后续访问必须始终读取 mcpowers 最新版本（不写具体版本号，跨升级永久适用）」正向框架。
- **修复**：[`mcpowers-doc-sync-install/SKILL.md`](skills/mcpowers-doc-sync-install/SKILL.md) §阶段 2 注释里的 `~/.claude/plugins/cache/mcpowers/mcpowers/2.26.2/` 硬编码示例路径违反 v2.26.2+ 注入路径稳定性铁律——改为 `${CLAUDE_PLUGIN_ROOT}/scripts/templates/...` 抽象 + 「框架层字符串替换自动展开为 mcpowers 最新版本对应的物理路径」说明。
- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §最高铁律·mcpowers 注入路径稳定性 增「注入物版本号写死禁令（v2.27.3+ · 全栈适用）」5 条强制条款：①禁止硬编码 mcpowers 版本号 ②必须描述为"对应 mcpowers 最新版本" ③禁止以"注入时刻的版本"为说明基准 ④版本演进历史只允许出现在 `.claude-plugin/*.json` / `CHANGELOG.md` / `docs/历史教训.md` ⑤物理兜底：注入脚本以本规范为唯一来源。
- **调整**：[`CLAUDE.md`](CLAUDE.md) 顶层铁律指针段同步标注 v2.27.3 新增的「注入物版本号写死禁令」；`README.md` §维护指南 增 1 行 v2.27.3 修复条目。
- **风险**：0 行为变更对外；本次纯文档级路径字面值修正 + 1 段铁律新增；CI 门禁 20+41 项验证（`bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh`）；插件版本号 2.27.2 → 2.27.3。

## v2.26.2 - 2026-08-04

- **修复**：[`mcpowers-init/SKILL.md`](skills/mcpowers-init/SKILL.md) §5 安装指引——"提示用户安装到 `~/.claude/skills/`" 改为 v2.0+ 唯一安装机制 `Claude Code 插件市场`（`/plugin marketplace add ... && /plugin install ...`）；§5 软链提议改为"**不软链不复制**，AI 按 mcpowers-spec-index 按需 Read"，避免软链指向带版本号 cache 路径、mcpowers 升级后失效；§5 注入的 CLAUDE.md「加载规范」段同步改为"按需 Read，**不**复制不软链"以消除内部矛盾。
- **修复**：[`mcpowers-doc-sync-install/SKILL.md`](skills/mcpowers-doc-sync-install/SKILL.md) §阶段 2 的 `<mcpowers>` 自定义占位符改用 `${CLAUDE_PLUGIN_ROOT}`，AI 在 Claude Code 会话里跑 cp 时框架自动展开；同时改"从环境变量读"措辞为"**Claude Code 框架在工具调用时自动展开的占位符（**非环境变量**）**"，避免与 v2.25.0 最高铁律"禁止使用环境变量"产生语感冲突。
- **修复**：[`开发环境规范.md`](skills/mcpowers-shared/docs/技术规范/开发环境规范.md) §2 给 `${CLAUDE_PLUGIN_ROOT}` 加脚注：说明是框架层字符串替换非环境变量、mcpowers-shared/docs/ 部分是稳定路径仅插件根目录带版本号。
- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 新增「最高铁律 · mcpowers 注入路径稳定性（强制 · 全栈适用 · v2.26.2+）」段——3 类禁行字面值（`cache/mcpowers/mcpowers/{version}/...` / `~/.claude/skills/mcpowers-shared/...` / 自定义占位符如 `<mcpowers>`）+ 3 条配套铁律（不软链、不装旧路径、AI 引用规范只用抽象路径）。
- **风险**：0 行为变更对外；本次纯文档级路径字面值修正 + 1 段铁律新增；CI 门禁 20+41 项验证（`bash scripts/check-readme-sync.sh` + `bash tests/plugin-verify.sh`）；插件版本号 2.26.1 → 2.26.2。

## v2.26.1 - 2026-08-04

- **修复**：[`开发环境规范.md`](skills/mcpowers-shared/docs/技术规范/开发环境规范.md) §2 + [`AI操作规范.md`](skills/mcpowers-shared/docs/AI操作规范.md) 10 处 + [`hooks/session-start.sh`](hooks/session-start.sh) 启动横幅——所有指向 `~/.claude/skills/mcpowers-shared/` 的旧路径改用 `${CLAUDE_PLUGIN_ROOT}` 占位符，与 `hooks/hooks.json` 既有惯例对齐；插件版本号同步 `2.26.0 → 2.26.1`。
- **调整**：[`AI操作规范.md` Step 1-1](skills/mcpowers-shared/docs/AI操作规范.md) 由 `ls ${CLAUDE_PLUGIN_ROOT}/skills/mcpowers-shared/docs/技术规范/*.md` 扫描改为 `Read mcpowers-spec-index.md` 索引（按 CLAUDE.md 既有"按需 Read"协议，bash 中 `${CLAUDE_PLUGIN_ROOT}` 不会被展开、`ls` 实际不可执行，原协议与现实不符）；[`mcpowers-spec-index/SKILL.md`](skills/mcpowers-shared/mcpowers-spec-index/SKILL.md) 删除"安装到 `~/.claude/skills/` 后调整相对路径"的过时提示行（plugin 整体安装机制下该用法不存在）。
- **风险**：0 行为变更对外；本次仅修正路径字面值与一处协议命令演示，不改动技能触发条件、路由表、技能/规范数量。

## v2.26.0 - 2026-08-03

- **新增**：[`日志规范.md §7.3`](skills/mcpowers-shared/docs/技术规范/日志规范.md) 新增「轮转 → 清理 → 压缩时序」——4 阶段强顺序：①轮转产生 `app.log.YYYY-MM-DD` ②保留 N 天原文件（默认 7 天，`keep_recent_uncompressed_days = 7`） ③超过窗口的轮转文件 `.gz` 压缩 ④超过保留期的 `.gz` 文件清理；§7.2 同时新增「免压缩窗口」配置项。
- **新增**：[`Flask后端规范.md §6.3`](skills/mcpowers-shared/docs/技术规范/Flask后端规范.md) `compress_old_logs()` + `purge_old_logs()` 两个工具函数落地免压缩窗口与 `.gz` 清理；`_file_handler()` `use_gzip=False` 由清理函数接管压缩时机；新增 `LOG_KEEP_UNCOMPRESSED` 配置项（默认 7）。
- **新增**：[`爬虫规范.md §12.3`](skills/mcpowers-shared/docs/技术规范/爬虫规范.md) 爬虫项目日志维护强制复用 Flask 的 `compress_old_logs` / `purge_old_logs`，新增 `daily_log_maintenance` 调度示例。
- **新增**：[`代码规范.md §6.1.1`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 新增「复用优先于二次抽象（强制 · 防过度设计）」段——6 条反模式黑名单（R1-R6）+ 3 条 bash 自检命令 + 3 类 wrapper 合理论证场景（参数映射 / 批量调用 / 异常归一）。
- **新增**：`hooks/check_duplicate_function.py` + `hooks/pre-write-check-duplicate.sh`——`PreToolUse(Write|Edit|MultiEdit)` 钩子，检测新增 `def` / `function` / `func` / `fn` 与仓库已有同名函数冲突；命中走 Claude Code confirm UI（exit 2）。同时保护 `skills/mcpowers-shared/` / `skills/mcpowers*/SKILL.md` 等白名单不被自身打扰。
- **新增**：[`mcpowers-feat/SKILL.md`](skills/mcpowers-feat/SKILL.md) 触发即执行 10 步中插入「## 2.5 已有资产扫描」强制步骤——PR 描述必填「已有资产扫描结果」清单（含 SDK / common / utils / shared 同名扫描），3 条 `rg` 自检命令；不填不允许进入第 3 步。
- **新增**：[`mcpowers-code-review/SKILL.md`](skills/mcpowers-code-review/SKILL.md) 「## 反模式（禁止）」段新增「过度抽象 / 重复代码 R1-R7」Critical 阻塞表 + 30 秒复用扫描 Quick-Check 3 条 `rg` 命令。
- **调整**：[`hooks/hooks.json`](hooks/hooks.json) `PreToolUse` 新增 `Edit|MultiEdit` 匹配器，注册 `pre-write-check-duplicate.sh`（之前仅在 `Write` 上）。
- **风险**：0 行为变更对外；日志免压缩窗口仅对启用新配置的项目生效，老项目沿用立即 gzip；钩子失败兜底放行（`try/except` 捕获所有异常 → exit 0），不会阻断正常 Write/Edit。

## v2.25.0 - 2026-08-03

- **新增**：[`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 新增「最高铁律 · 本技能禁止使用环境变量（强制 · 全栈适用）」段——仓库所有 .py / .sh / .js / .ts 源文件以及应用本规范的所有项目代码**一律禁止**读环境变量；Python 禁 `os.environ.*` / `os.getenv`，Shell 禁 `$XXX` 从外部环境读，JS/TS 运行时禁 `process.env.*` / `dotenv.config()`；唯一允许例外 `hooks.json` 的 `${CLAUDE_PLUGIN_ROOT}` 与 docker-compose `environment:` 字段。
- **新增**：[`Flask后端规范.md §4.1`](skills/mcpowers-shared/docs/技术规范/Flask后端规范.md) 改为「指向代码规范」短引用段，明确栈级落地走 `Config.get()` / `Config.items()`。
- **新增**：[`CLAUDE.md`](CLAUDE.md) 「## 规范体系」段插入「本技能禁止使用环境变量」基线段（强约束措辞）。
- **新增**：[`README.md`](README.md) 第 14 行表格 + 第 228 行段落同步 v2.25.0 摘要。
- **修复**：[`reverse-analysis-session.py:578`](skills/mcpowers-crawler-reverse/scripts/reverse-analysis-session.py) `browser_candidates()` 函数删除 `dict(os.environ)` 探测 Windows 浏览器路径的违规源——改为 `environment` 参数作为可选测试注入点（外部测试 `tests/reverse-analysis-session-verify.py` 仍可传 `windows_env` 模拟），函数内部硬编码 `C:/Program Files` / `C:/Program Files (x86)` + `pathlib.Path.home() / "AppData" / "Local"` 作默认 root，业务调用方无需传任何环境探测参数。
- **风险**：0 行为变更对外；OS 浏览器路径仅覆盖 Windows 默认安装位置，非标安装用户仍走 `_find_windows_browser_from_registry()` 注册表探测；本仓库 `import os` 在 `os.replace()` 文件重命名场景保留（不算违规）。

## v2.21.3 - 2026-07-31

- **调整**：铁律 #6 加资源所有权分类（v2.21.3）——`external/user-owned`（不可关闭）vs `task-owned`（finally 可关闭）；明确 `web_monitor_template.py` 属于 task-owned，finally 段 `browser.quit()` 不再与铁律 #6 冲突。
- **调整**：《爬虫工具与抓包规范》§8 章节标题从「用户操作录制与重放脚本」改为「Web 浏览器协作会话工具链」——章节实际承载范围（录制 + JS 监控 + 指纹审计 + 派生产物）已超出原标题语义。
- **新增**：《爬虫工具与抓包规范》§8.8.8「完整 body 获取路径」——临时方案走 §3.0.1 模式 C + §3.0.7 cURL 12 项清单（不受 1024 字符预览限制）；长期方案 `reverse-analysis-session.py --save-full-body`（v2.22+ 待办）。
- **调整**：`mcpowers-reverse-android/ios/flutter/hybrid` 4 个 App 专项 SKILL.md 加 v2.21.3 权威源声明——8 项证据交接合同以 `mcpowers-crawler-reverse/SKILL.md` §4 为唯一权威源，本节不再重复定义。
- **风险**：0 行为变更，纯文档同步；CI 门禁 20+41 项全过。

## v2.21.2 - 2026-07-31

- **新增**：`skills/mcpowers-crawler-reverse/scripts/web_monitor_template.py`——标准化 Web 浏览器监控模板（开箱即用，内置 7 类"配置正确性"防御 + run_js JS 异常保护）。供 Web 逆向 / 抓包分析 / 浏览器行为取证场景直接 `from web_monitor_template import monitor` 调用，避免 AI 从零写 DrissionPage 配置时踩坑。
- **修复**：`tab.cookies()` / `tab.run_js(...)` 缺 try/except 保护——目标页 JS 执行失败时整个 monitor 会抛致命异常（自验证暴露的真实 bug）。修复后 `monitor()` 在异常路径下也能正常返回 `result.json`。
- **调整**：《爬虫工具与抓包规范》§7.2 工具对照表新增 `web_monitor_template.py` 行（明确边界：不替代 `reverse-analysis-session.py web-start` 的工作区 + 协作会话 + 派生产物状态机）。
- **风险**：本工具关闭自身创建的浏览器（finally 段），不接管用户已有 Chrome；如需接管外部 Chrome 请使用专门的协作会话编排工具。

## v2.21.1 - 2026-07-29

- **调整**：治理 `CLAUDE.md` / `README.md` 顶层文档膨胀——`CLAUDE.md` 由 622 行收敛至 ~200 行（删除 13 个历史教训段），`README.md` 由 908 行收敛至 ~600 行（删除 7 个版本发布段）。
- **新增**：[`docs/历史教训.md`](docs/历史教训.md) 只读归档，承载 v2.0.3 → 当前版本完整复盘。
- **新增**：[`CHANGELOG.md`](CHANGELOG.md) 用户视角版本变更历史（顶层文档 4 段式）。
- **调整**：CI 门禁新增 3 段——`scripts/check-readme-sync.sh` §18 根文档结构门禁（禁止 `### 历史教训（v` / 禁止 `### vX.Y.Z`）、§19 根文档尺寸门禁（CLAUDE.md ≤ 350 行 / 35,000 字符，README.md ≤ 650 行 / 50,000 字符）、§20 单一权威源门禁（关键短语在根文档出现即告警）。
- **调整**：`.github/workflows/doc-sync.yml` DOCS_CHANGED 判定扩展为 4 文件（CLAUDE.md / README.md / CHANGELOG.md / docs/历史教训.md）至少一改。

## v2.21.0 - 2026-07-28

- **新增**：`session-artifacts-generator.py`——Web `web-stop` 自动派生产物（`02-接口分析/目标接口候选.md` + 响应样本 envelope + v2.17.0 类式 `client.py` / `quick_test.py` 种子）。
- **新增**：《爬虫分析规范》§3.11 App 录制选型调研（三方案对照矩阵 + v2.22+ 选型门槛）。
- **调整**：CI 门禁 `check-readme-sync.sh` §17 + `plugin-verify.sh` §7.6 同步新增。
- **风险**：真实并行场景 + 真实接管链路仍未跑；HAR body_preview 1024 字符上限；自动 lifecycle 分类是线索；真实 top10 排名仍需人工确认。

## v2.20.0 - 2026-07-27

- **新增**：`reverse-analysis-session.py` 端口独立分配（`pick_free_port` + 端口池 9222..9300 fallback + 100 次上限 SessionError）。
- **调整**：多项目可并行 web-start 互不冲突；端口与工作区一一对应，《会话状态.json》`chrome_port` 字段是唯一可信源。
- **调整**：《爬虫工具与抓包规范》§3.7.1 新增端口独立分配 SOP；`set_local_port(9222)` 全部占位符化为 `<port>`。
- **风险**：DrissionPage `set_local_port(0)` 兼容性未确认（绕开方式：外部 socket 探测后传入）。

## v2.19.0 - 2026-07-26

- **新增**：`reverse-analysis-session.py`——`init / web-start / web-stop / status` 单状态机强制起手式（WORKSPACE_READY → ENV_READY → BROWSER_READY → FINGERPRINT_READY → MONITORING → STOPPED）。
- **新增**：浏览器指纹一致性审计（`audit_browser_fingerprint`，分阻断 / 警告 / 不可本地证明 三档）。
- **新增**：JS 运行时持续监控（4 类高价值通道：script URL / fetch / XHR / WebSocket / console.error / unhandledrejection / 性能补采）。
- **调整**：`user-action-recorder.py` 强化脱敏（DOM / HAR / Body 三层）。
- **调整**：Python 注释 / docstring / 提示语强制中文。
- **风险**：真实接管链路 v2.19.0 仍未跑；JS 监控对 SRI + CSP 严格页面可能注入失败。

## v2.18.2 - 2026-07-25

- **修复**：`user-action-recorder.py:506` duck-type 致命 bug（`callable(page.listen)` 误判 → 接管模式完全不可用）。
- **修复**：`user-action-recorder.py:421` `page.actions.wheel` API 误用（DrissionPage 无此方法，应为 `page.actions.scroll`）。
- **修复**：`popup-handler.py` POPUP_SELECTORS 漏配 notification（补 2 行 selector）。
- **调整**：`replay_actions` 防御性读取 + `stop_recording` flush HAR buffer。
- **铁律**：新工具 / 新接管语法必须 1 次接管链路口令实测通过才能上线。

## v2.18.1 - 2026-07-25

- **调整**：《爬虫工具与抓包规范》§2.1/§7.2 DrissionPage 描述精准化（删除"内置反检测"，改为"接管便利性 + 国内站点适配"）。
- **新增**：4 个实测参考链接（[DrissionPage 官网](https://www.drissionpage.cn/browser_control/connect_browser/) + Chrome 136 修复方案 + Chrome 启动参数 + 真实接管链路留痕）。
- **调整**：Playwright fallback 路径从 3 类扩展到 5 类（新增重度反指纹检测 + 复杂行为分析风控）。
- **铁律**：未上网确认的事实禁止写进主表 description。

## v2.18.0 - 2026-07-24

- **调整**：浏览器自动化默认从 Playwright 切换为 **DrissionPage**（接管便利性 + 代码量少 30~50% + 国内站点适配）。
- **新增**：《爬虫工具与抓包规范》§2.1 接管语法对照表（`connect_over_cdp` → `ChromiumPage(addr_or_opts=ChromiumOptions().set_local_port(9222))` 等）。
- **新增**：《爬虫工具与抓包规范》§3.5/§3.6/§3.9 漏抓 7 层 DrissionPage 重新映射。
- **调整**：`popup-handler.py` / `user-action-recorder.py` 全文件 DrissionPage 适配（duck-type `hasattr(page, "listen")` 自动分支）。
- **风险**：Chrome 150+ `--remote-allow-origins=*` 必传；Chrome 136+ 独立 user data dir 必传。

## v2.17.0 - 2026-07-22

- **调整**：模块产物封装形式标准化——`functions.py` → `client.py` 类式封装 + `do_request` / `parse_response` 分离 + 零前置参数业务方法 + `quick_test.py` 必备。
- **调整**：分析文件命名强制中文（`01-目标画像/` / `02-接口分析/` / `03-逆向攻坚/` / `04-模块封装/` / `接口清单.md` / `验收报告.md` 等）。
- **新增**：《爬虫分析规范》§9.4.6 全段 6 小节（类式 / SRP / 零前置参数 / quick_test / 中文命名 / extract 同步）。
- **风险**：自动生成种子**不**作为阶段 5.5 PASS 替代，必须人工验证。

## v2.16.0 - 2026-07-20

- **新增**：《爬虫工具与抓包规范》§3.9 漏抓诊断 7 层决策树 + §3.9.2 切换模式前 6 问自检。
- **新增**：《爬虫分析规范》§3.0.7 cURL 12 项快速帮助清单 + §3.0.8 cURL → 代码转换 SOP 提示。
- **调整**：Chrome 150+ `--remote-allow-origins=*` 必传警告。
- **铁律**：`mcpowers-crawler-reverse/SKILL.md` 铁律 11——"抓不到 ≠ 不存在"。

## v2.15.0 - 2026-07-18

- **新增**：`user-action-recorder.py` 协作模式 B 工具（录制 + 重放，~5h 最小可用版）。
- **调整**：与 `popup-handler.py` 严格分工——popup-handler 主动清理；recorder 被动监听。
- **铁律**：全程遵守 §1.3 浏览器所有权——禁止 `browser.close()` / `context.close()` / `page.close()`。

## v2.14.0 - 2026-07-15

- **新增**：《爬虫分析规范》拆分 7 册 + 1 配套（`爬虫工具与抓包规范.md` + 6 个平台专项）。
- **调整**：`§1.3 外部接管资源不可关闭` 主册为唯一权威源；各册按需引用，不重复定义。
- **风险**：跨册改动面大（25 文件同步），CI 物理门禁强制要求 CLAUDE.md/README.md 同 PR 变化。

## v2.13.0 - 2026-07-12

- **调整**：逆向 7 专项拆分（统一入口 + Web + App 二级入口 + Android / iOS / Flutter / Hybrid / 小程序）。
- **新增**：`浏览器所有权铁律`——通过 CDP/WebView/daemon 接管的 browser/context/page/tab 一律视为外部所有，永不可关闭。
- **调整**：`check-readme-sync.sh` 增至 12 类检查（新增 reverse 拓扑 / 公共合同 / 外部资源所有权断言）。

## v2.12.0 - 2026-07-10

- **新增**：SKILL.md 阶段 5.5 真实可用性验收（业务语义 + ≥ 2 组输入 / 合计 ≥ 5 次 + 跨 session + 原报文重放 + 动态参数重生成 + 有界并发 2 → 5）。
- **新增**：生命周期 7 分类（`reusable` / `per-request` / `single-use-token` / `session-bound` / `time-bound` / `challenge-bound` / `unknown`）。
- **调整**：统一产出 `verification-report.md`，只有 `PASS` 才能进入阶段 6/7。
- **风险**：并发仅做小规模可用性验证，不做压力测试；遇 429 / 验证码 / 账号提示立即停止。

## v2.11.1 - 2026-07-08

- **新增**：bb-browser 完整实操链路（§2.5.5.0 安装与 MCP 配置 + §2.5.5.1 daemon + Playwright 共享 Chrome CDP + §2.0.5.1 adapter 失败判定与结果合并）。
- **铁律**：第三方 CLI 集成必须包含完整实操链路（安装 → 启动 → 验证 → 失败处理 → 结果合并）。

## v2.10.0 - 2026-07-05

- **新增**：`bb-browser`（[epiral/bb-browser](https://github.com/epiral/bb-browser)）第三方 CLI / MCP server 集成。
- **铁律**：第三方 CLI 必须是可选依赖；缺 bb-browser 时 v2.9.5 Chrome CDP + Playwright + popup-handler.py 原链路必须完全可用。

## v2.9.5 - 2026-07-02

- **新增**：`mcpowers-crawler-reverse` §2.7 弹窗检测（8 类弹窗字典）+ §3.0 协作模式 + §3.4.5 置信度。
- **新增**：`popup-handler.py`（与字典库对应）。
- **铁律**：单技能能力强化 ≠ 单文件改动；6 类文件同步是底线。

## v2.6.0 - 2026-06-25

- **新增**：`日志规范.md`（7 类日志 + JSON 字段 + 大内容默认截断 + 脱敏黑名单）。
- **调整**：`mcpowers-init` 注入日志基础设施（`utils/loggings.py` + `utils/request_log.py` + `log/` 目录）。

## v2.0.3 → v2.0.4

- **修复**：description 多行 `|` 字面量块导致 3 个文件超 1024c 被截断（code-review / brainstorm / bugfix）。
- **调整**：全部改为 4 段式单行紧凑版，L1 description 总预算从 ~9000c 降到 5986c（-34%），0 个文件超 800c。
