# mcpowers

AI 辅助开发的标准化技能体系。**按场景拆分的轻量级技能组合**，借鉴 superpowers 设计。**完全独立运行**（含 Git 操作），不依赖任何外部技能。

## 核心结构

| 目录 | 用途 |
|:-----|:-----|
| `.claude-plugin/` | **插件市场元数据**（`marketplace.json` + `plugin.json`，由 Claude Code 插件系统读取） |
| `skills/mcpowers/` | **主入口路由器**（每次对话注入） |
| `skills/mcpowers-*` | **32 个可路由技能**（场景层 24 + 方法层 8，扁平化） |
| `skills/mcpowers-shared/` | 规范资产库（32 个技术规范 + `mcpowers-spec-index` 导航，v2.6.0 新增 `日志规范.md`；v2.14.0 爬虫拆分 7 册；v2.15.0 协作模式 B 工具化 `user-action-recorder.py`；v2.22.0 Flask/爬虫日志实现层对齐 `日志规范.md`——按 type 分文件、禁止按级别切文件；v2.23.1 docker-compose 启动命令统一：`up -d --force-recreate`、`--build` 不带 `--force-recreate`、stop/down 区分停止与删除；v2.31.0 新增 `Swagger字段契约.md` 字段清单机制） |
| `hooks/` | Claude Code hooks 资产（4 个事件组 / 10 个脚本 + `hooks.json`；v2.28.2+ 含 `pre-write-check-duplicate.sh` 重复函数检测（极简：跨文件同名默认放行 + 同文件重名 + 单行透传 wrapper 两类 block；豁免 `main` / `hook_main` 入口惯例 + Python dunder 协议方法 + 单下划线私有名）；v2.27.0+ 含 `pre-write-check-import.sh` Python 局部 import 拦截；v2.27.4+ 含 `pre-write-check-spec-frontmatter.sh` 规范 frontmatter 字段强制声明；**v2.29.0+ 含 `pre-write-check-doc-sync.sh` doc-sync 物理门禁（path/route/env 三类检查）——替代 v2.9.0 引入的 `doc-sync-install` 技能 [已废弃]，不向用户项目注入任何文件，装 mcpowers 即自动支持**；v4.0.2+ 含 `post-write-check-doc-content.sh` 文档画蛇添足字眼软门禁，6 类路径白名单区分参考型/历史型文档） |
| `tests/` | 插件结构验证（`plugin-verify.sh`） |
| `scripts/` | 工具脚本（`check-readme-sync.sh`） |

## 触发条件

`mcpowers` 主入口路由器在每次对话自动加载，识别用户意图后路由到对应技能：

- **加功能/新增接口/做页面** → `mcpowers-feat`
- **修 bug/报错/不生效** → `mcpowers-bugfix`
- **重构/抽离/拆分** → `mcpowers-refactor`
- **性能优化/查询慢** → `mcpowers-optimize`
- **部署/上线/发布** → `mcpowers-deploy`
- **需求变更/调整逻辑/加字段** → `mcpowers-requirement-change`
- **新项目/初始化/脚手架** → `mcpowers-init`
- **最小模块化/通用模块/零业务自包含工具/复制即用/跨项目可搬运** → `mcpowers-min-module`
- **SDK 设计/封装领域 API/业务封装库/客户端 SDK/接口封装库** → `mcpowers-sdk-design`
- **写需求/PRD/文档** → `mcpowers-prd`
- **任务拆解/列计划** → `mcpowers-plan`
- **按计划执行/实施计划/开始执行** → `mcpowers-execute`
- **代码审查/自审** → `mcpowers-code-review`
- **写测试/TDD** → `mcpowers-tdd`
- **需求不清/澄清** → `mcpowers-brainstorm`
- **复杂任务/并行** → `mcpowers-subagent`
- **自动化测试/E2E/测试报告/跑 pytest/跑 Playwright/跑 DrissionPage/跑 Selenium/跑 Cypress** → `mcpowers-autoTest`（新增自动化默认 Python；先查项目证据，已有套件沿用）
- **前后端联调/API契约/接口文档** → `mcpowers-api-contract`
- **安装基础技能/一键装基础** → `mcpowers-install-basics-skills`
- **爬虫逆向/接口分析/抓包分析/加密参数还原/RPC逆向/纯协议/半自动化/纯自动化/一次性报文/token复用/并发稳定性/模块真实可用/目标类型不明** → `mcpowers-crawler-reverse`（统一入口）
- **网站逆向/Web JS反混淆/浏览器抓包/CDP接管/WASM/bb-browser** → `mcpowers-reverse-web`
- **App逆向但平台或运行时未知/识别App技术栈** → `mcpowers-reverse-app`（二级入口）
- **Android逆向/安卓/APK/AAB/Kotlin/Java/JNI/jadx/frida hook/LSPosed** → `mcpowers-reverse-android`
- **iOS逆向/苹果App/IPA/Mach-O/Swift/Objective-C/LLDB** → `mcpowers-reverse-ios`
- **Flutter逆向/Dart AOT/libapp.so/App.framework/Platform Channel** → `mcpowers-reverse-flutter`
- **混合App逆向/uni-app/React Native/Cordova/Capacitor/WebView/JSBridge/Hermes** → `mcpowers-reverse-hybrid`
- **小程序逆向/小游戏/微信小程序/支付宝小程序/抖音小程序/百度小程序/wxapkg** → `mcpowers-reverse-miniprogram`
- **抽离公共模块/抽离通用能力/提取可复用组件/拆出独立库/爬虫逆向层剥离/抽成公共库/做成可调用脚本/模块化调用** → `mcpowers-extract`
- **commit/提交** → `mcpowers-git-commit`
- **worktree/分支隔离** → `mcpowers-git-worktree`
- **回滚/撤销** → `mcpowers-git-rollback`
- **清理分支** → `mcpowers-git-cleanBranches`

## 规范体系

位于 `mcpowers-shared/docs/技术规范/`：
- **通用规范**：API、数据库、缓存、Git、代码(SOLID/KISS/DRY/YAGNI)、测试、部署等
- **技术锁规范**：Flask后端、Vue前端、爬虫

**按需加载**：场景/方法层技能不预加载规范，而是通过 `mcpowers-spec-index` 查表（"做什么 → 读哪个规范"）按需 Read。

**自动化选型基线**：新增自动化默认使用 Python + pytest；先检查项目已有测试文件、依赖、配置和 CI/脚本证据；已有非 Python 套件沿用原框架，未知框架不得凭 AI 熟悉度引入。

**日志分文件基线**：按业务 type 分文件（`biz.log` / `audit.log` / `request.log` / …），**级别是 JSON 的 `level` 字段，不是文件名后缀**；禁止 `xxx_info.log` / `xxx_error.log` 这类按级别切文件（会拆散同一 `request_id` 的链路）；ERROR+ 仅以**聚合流**形式额外落一份 `error.log`。详见 `日志规范.md §7.2` + `Flask后端规范.md §6.0`。

**写 Swagger 接口必须按 5 字段契约（v2.31.0+ 全栈适用铁律；v4.0.0+ 业务接口只列 200；v4.0.1+ 接口文档零引用；v4.2.0+ 表格排版防护 + XSS 阻断）**：任何使用 Swagger / OpenAPI 工具栈的项目（flasgger / apispec / fastapi / springdoc / openapi-typescript 等）写接口文件（views.py / /views/ / router.{py,js,ts} / /controllers/）时，**PreToolUse 阶段物理门禁**——`tags` + `summary`（≤ 30 字，句末无标点）+ `description`（≤ 100 字简短功能说明）+ `parameters`（每个含 `description` + `example`）+ `responses`（含 200，每个状态码含 `schema` + `examples`）任一缺失视为不完整接口，触发 Claude Code confirm UI（exit 2）。**v4.0.0+ 业务接口 `responses` 只列 `200`**——业务成功/失败由响应体 `code` 字段判断（`code: 0` = 成功；非 0 = 业务失败），4xx/5xx 仅由框架层（Flask abort / Webargs / Flask-JWT-Extended 中间件）抛出，不由业务接口在 docstring 声明；认证接口（路径含 `login`/`logout`/`refresh`/`verify`/`register`/`password`）+ 流式接口（路径含 `download`/`export`/`stream`/`upload`/`file`/`attachment`）为例外，可保留 401/416。**v4.0.1+ API 文档零引用铁律**——接口文档（docstring → spec → md 全链路）应聚焦"怎么对接调用"，`summary` / `description` / `parameters[].description` / `responses[].description` 等用户可见字段值**禁用字眼**：「参考 / 参见 / 详见 / 引用 / 参照 / 引自」+「根据规范 / 按照规范 / 按规范要求 / 遵守规范 / 按规范」+「according to / refer to / referring to / as described in / as specified in / see also」——这些字眼会让对接方以为还要再去查其他文档才能用。**v4.2.0+ 表格排版防护 + XSS 阻断**——`export_docs.py` 导出 markdown 时,所有 7 个表格生成点（含顶层 description）走 `_md_cell_safe()` 4 步走：① 规范化（None / dict / list → str）→ ② 不可见字符清理（NBSP / EM SPACE → 空格；ZWSP / BOM → 删）→ ③ Markdown 转义（`\` → `\\`、`|` → `\|`、换行 → `<br>`）→ ④ 危险结构防御（HTML 标签剥离白名单 `<br>`、`|---` 等分隔行冒充 → `—`、代码块围栏 → 单 `` ` ``、列表 / 标题前缀 → 空格）；`_scan_xss_risk()` 在 main() 阶段扫描 10 类 XSS 模式（`script` / `iframe` / `object` / `embed` / `style` / `form` / `svg` / `on*= 事件处理器` / `javascript:` / `data:text/html`）命中即 exit 2 阻断。详见 [`接口契约规范.md`](skills/mcpowers-shared/docs/技术规范/接口契约规范.md) §1（5 字段契约权威定义）+ §1.C.1（v4.0.0+ 业务接口响应规范铁律）+ §1.E（v4.0.1+ API 文档零引用铁律）+ §1.F（v4.2.0+ 表格排版防护 + XSS 阻断铁律）+ [`Swagger字段契约.md`](skills/mcpowers-shared/docs/技术规范/Swagger字段契约.md)（项目自定义必填字段清单机制，`.swagger-required-fields.yml`）。栈级落地：`hooks/pre-write-confirm-api-hint.sh` 由 v2.4.0 软提醒升级为 v2.31.0 真硬门禁（wrapper→helper 集中模式：`scripts/swagger-contract-check.sh` → `scripts/swagger-stack-detect.sh` → `scripts/swagger-required-fields.sh` → `scripts/swagger-lint-helper.py`，不向用户项目注入任何文件）；Flask/Flasgger 实现层参考 [`swagger_template.md`](skills/mcpowers-shared/docs/API文档/swagger_template.md) 24 类接口模板；**`swagger-lint-helper.py check_business_api_responses()` 在 PreToolUse 阶段检测业务接口误列 4xx/5xx**——按 `/`-`_-.` 段内切分避免 `profile` 含 `file` 等子串误判；**`swagger-lint-helper.py check_no_reference_words()` + `export_docs.py check_no_reference_words_spec()` 双层检测零引用字眼**——YAML 字段名行（`key:` 末尾冒号且无 value）跳过不扫；**`export_docs.py _md_cell_safe()` 在导出时统一规整表格单元格**——7 个表格生成点 + 顶层 description 全部集中走该函数,防止 description / example 含换行 / `|` / 不可见字符破坏 Markdown 表格语法；**`export_docs.py _scan_xss_risk()` 在 main() 阶段扫描 XSS / HTML 注入**——10 类危险模式命中即 exit 2。审查门禁：`mcpowers-code-review` 增 R13 反模式条目（swagger 接口 5 字段不完整）+ R14（v4.0.0+ 业务接口 responses 误列 4xx/5xx）+ R15（v4.0.1+ API 文档含禁用引用字眼）+ R16（v4.2.0+ 导出文档含未规整单元格 / XSS 注入风险）+ Quick-Check 段含 3 条扫描命令（grep `tags:` 顶层字段名 / `description:` + `example:` 子字段配对 / `responses:` 块含 ≥ 2 个状态码）+ 1 条 v4.0.0+ 业务接口响应规范扫描命令 + 1 条 v4.0.1+ 零引用字眼扫描命令 + 1 条 v4.2.0+ 表格 `_md_cell_safe()` 覆盖扫描命令（grep `lines.append(f'| {prop_name}` 模式 = 漏走 _md_cell_safe）+ 1 条 v4.2.0+ XSS 阻断扫描命令（grep `<script>` / `javascript:` 模式）。

**控制台日志级别紧凑 + stdout（v2.28.4+ 全栈适用铁律）**：控制台 formatter 的级别字段必须紧凑（`%(levelname)s` 或 `%(levelname).1s`，禁止 `%(levelname)-8s` / `%(levelname)-5s` 等宽度填充——宽度由 format 字符串决定，不是 colorlog 参数）；控制台 handler 必须显式 `logging.StreamHandler(stream=sys.stdout)`（禁止 `logging.StreamHandler()` 默认 `sys.stderr`——PyCharm / IntelliJ 会把 stderr 整体染红，即使日志级别是 INFO / DEBUG）。详见 `日志规范.md §7.5`；栈级落地见 `Flask后端规范.md §6.1` `utils/loggings.py` 实现层。审查门禁：`mcpowers-code-review` 增 R11 反模式条目（控制台日志级别未紧凑打印 / StreamHandler 未显式指定 stdout）+ 新 Quick-Check 段「v2.28.4+ 控制台日志级别紧凑 + stdout Quick-Check」含 2 条扫描命令。

**控制台默认无颜色（v2.29.2+ 跨语言全栈总章铁律·任何环境一律默认关·模块内置即合规）**：除非用户在配置 / 调用方**主动**开启，控制台 formatter **默认**走 plain formatter（无 ANSI 转义序列）。**禁止**任何模块——**包括 min-module / sdk-design 的内置日志模块**——默认开启颜色。**任何环境（dev / test / staging / prod）一律默认关**——颜色开关不区分部署阶段，开发环境不会因为「dev 就该有颜色」而默认开；**min-module / sdk-design 内置日志工厂硬编码默认即合规**——不假设调用方会传配置，开箱即无颜色。颜色是「按需着色」哲学，不是「按需去色」哲学。默认开颜色会污染：①复制粘贴（`\x1b[32m...` 混入 Markdown / issue 评论）；②管道（`grep` / `tee` 关键字匹配穿插转义字符）；③文件重定向（Loki / ELK 把 ANSI 当异常染色）；④日志聚合平台（Sentry / DataDog 把含 ANSI 的字符串归类为 error）。详见 `日志规范.md §7.6`（v2.29.2 升级为总章铁律：含 Python / JS / Go / Rust / Java 5 语言对照表 + `§7.6.4` min-module/sdk 内置日志硬编码默认示例 + `§7.6.5` 全栈反例清单）；栈级落地见 `Flask后端规范.md §6.1`（`LOG_CONSOLE_COLOR = False` 配置项 + 控制台 formatter 三态：JSON / colorlog（仅 console_color=True）/ plain（v2.29.2+ 默认））+ `爬虫规范.md §12` 同步引用 + `mcpowers-min-module/SKILL.md §4` + `mcpowers-sdk-design/SKILL.md §11` 自检清单对齐：内置日志工厂硬编码默认 = `INFO + stdout + 紧凑级别 + plain Formatter`，**调用方零配置即合规**。审查门禁：`mcpowers-code-review` 增 R12 反模式条目（默认走 `colorlog.ColoredFormatter` / `winston.format.colorize()` / `logrus ForceColors: true` 等开颜色）+ 新 Quick-Check 段「v2.29.2+ 默认无颜色 Quick-Check」含 **4 条**扫描命令（Python `setFormatter(...ColoredFormatter)` 缺配置开关 / JS-Go-Rust 默认颜色参数 / `console_color` 默认值 `True` / **v2.29.2+ 新增**：模块内置日志硬编码默认值扫描——即便在硬编码常量里出现 ColoredFormatter 也视为违规）。

**本技能禁止使用环境变量（v2.25.0+ 全栈适用最高铁律）**：仓库所有 .py / .sh / .js / .ts 源文件以及应用本规范的所有项目代码**一律禁止**读环境变量——Python 禁 `os.environ.*` / `os.getenv` / `from os import environ`；Shell 禁 `echo "$XXX"` / `${XXX}` 从外部环境读；JS/TS 运行时禁 `process.env.*` / `dotenv.config()`。配置统一走**文件 + 加载器**或**命令行参数**；OS 探测（浏览器路径、用户目录）走 `pathlib.Path.home()` + 已知路径硬编码 + `shutil.which()` 组合。唯一允许的例外：`hooks.json` 的 `${CLAUDE_PLUGIN_ROOT}` 与 Docker Compose YAML 的 `environment:` 字段（这两处不进入 mcpowers 代码运行时）。**v2.29.3+ 边界澄清**：`environment:` 例外仅限值不回流到代码的场景（如 `TZ=Asia/Shanghai`、MySQL 官方镜像的 `MYSQL_ROOT_PASSWORD`）；**禁止**用 `envsubst` 等方式把环境变量替换进 `ini` / `yaml` 配置文件的占位符（如 `${SECRET_KEY}`）——那条链路终点是 `Config.get()`，已进入代码运行时，不在例外内。敏感字段各环境一律直接写在项目自己的 `config_{env}.ini` 里。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) 「最高铁律 · 本技能禁止使用环境变量」段；栈级落地见 `Flask后端规范.md §4.1` / `Vue前端规范.md` / `爬虫工具与抓包规范.md`。

**复用优先于二次抽象（v2.26.0+ 全栈适用铁律）**：写新函数 / 新类 / 新模块前必须先扫仓库 + SDK + 通用模块是否已有等价实现——禁止「明明 SDK 已有，又包一层」的二次抽象。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §6.1.1。物理兜底：`hooks/pre-write-check-duplicate.sh` 在 `PreToolUse(Write|Edit|MultiEdit)` 时检测新增 `def` / `function` / `func` / `fn` 走 3 档判定：①同文件内重名（count ≥ 2）→ block（exit 2 + confirm UI）；②跨文件同名 + 函数体单行透传 `return <已有函数>(...)` → block（gold standard 二次包装信号，exit 2 + confirm UI）；③其他跨文件同名 → 默认放行（exit 0；Python import 是模块级作用域，跨文件同名不冲突）。豁免：`main` / `hook_main` 入口惯例 + Python dunder 协议方法 + 单下划线私有名。审查门禁：`mcpowers-code-review` 增 R1-R10 Critical 反模式表（R1-R6 未扫仓库就写 wrapper / 二次抽象仅一行调用 / 命名冲突 / 跨项目搬运不复用 / 抽象类单实现 / 公共函数零调用方；R7 绕过 `utils/loggings.py` 自写清理；R8 Python 局部 import；R9 规范 stability 未声明；R10 旧 hook 4 类启发式分级行为）。方法层落地：`mcpowers-feat` 触发即执行 10 步中新增「## 2.5 已有资产扫描」强制步骤（PR 描述必填扫描清单）。

**v2.28.2 补充：重复检测行为简化**——上述 3 档判定的设计动机：v2.27.6 之前 hook 默认按函数名一刀切 block，v2.27.6~v2.28.1 走 4 类启发式分级（命名空间跨段 / 签名差异 / 绑定方法 / 单行透传），但**两者都用启发式打补丁，源头是「跨文件同名默认视为重复」**——跨文件同名是合法常态（业务模块各自的 `parse(data)` 等），v2.28.2 砍掉 3 类启发式降级，回归「只有真 bug 才拦」的极简原则；新增「同文件内重名」检测（`count_in_source` 扫新内容内同名 def ≥ 2 即 block）修复原 hook 显式跳过新文件自身的反向 bug。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md) §6.1.1 v2.28.2 补充段。审查门禁：`mcpowers-code-review` R10 描述从「v2.27.6 启发式分级」改为「v2.28.2+ hook 已简化」+ Quick-Check 段从「v2.27.6+ 启发式分级」改为「v2.28.2+ 单行透传」。

**日志免压缩窗口（v2.26.0+ 强制基线）**：日志文件轮转后**不立即** gzip——保留最近 N 天的轮转文件为明文（默认 7 天，`keep_recent_uncompressed_days = 7`，可配 `0` 表示立即压缩）；超过窗口的轮转文件才压缩为 `.gz`；超过保留期的 `.gz` 文件清理。详见 [`日志规范.md`](skills/mcpowers-shared/docs/技术规范/日志规范.md) §7.2 + §7.3「轮转 → 清理 → 压缩时序」4 阶段；栈级落地见 `Flask后端规范.md §6.3` 的 `compress_old_logs` / `purge_old_logs` 双函数（爬虫项目复用同一对函数，详见 `爬虫规范.md §12.3`）。

**Python import 顶层（v2.27.0+ 全栈适用铁律）**：Python 文件的 `import` / `from ... import ...` 必须位于模块级导入区，按标准库、第三方、本项目模块分组；函数、方法、类体、条件块、装饰器内部禁止局部 import。局部 import 仅在循环依赖或真正可选依赖时可例外，且必须写明原因并由用户确认；禁止以"延迟加载 / 按需使用 / 性能优化"作为默认理由。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)「Python import 位置规范」段。物理兜底：`hooks/pre-write-check-import.sh`（含 `check_python_import_placement.py`）在 `PreToolUse(Write|Edit|MultiEdit)` 时 AST 检测新增的局部 import，命中则弹 Claude Code confirm UI（exit 2）；Write 视为覆盖、Edit/MultiEdit 仅 diff 新增违规。规范层落地：`mcpowers-feat` / `mcpowers-tdd` / `mcpowers-code-review` 已在自检清单与审查维度加 import 位置检查，`mcpowers-code-review` 增 R8 反模式条目与「v2.27.0+ Python import 位置扫描 Quick-Check」grep 两条。

**注入物版本号写死禁令（v2.27.3+ 全栈适用铁律）**：mcpowers 注入到用户项目的内容（CLAUDE.md 段、`utils/loggings.py`、`.doc-sync-rules.yml`、`.git/hooks/pre-commit`、`.doc-sync-check.sh` 模板、`user-action-recorder.py` 等）**禁止**硬编码 mcpowers 版本号字面值（`v{major}.{minor}.{patch}` / `{version}/` / `cache/mcpowers/mcpowers/{version}/`）；注入物必须描述为"对应 mcpowers 最新版本的纪律"，后续访问永远指向最新版本。版本演进历史只允许出现在 `.claude-plugin/*.json` / `CHANGELOG.md` / `docs/历史教训.md`。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)「最高铁律 · mcpowers 注入路径稳定性 §注入物版本号写死禁令」。

**运行时版本访问白名单（v2.27.4+ 全栈适用铁律）**：上条禁的是"注入物硬编码版本号"。本条允许的是"AI 运行时访问历史版本"——AI 在 Claude Code 工具调用层 `ls ~/.claude/plugins/cache/mcpowers/mcpowers/` 发现用户已装的旧版本 → `Read` 读该版本规范（version 是运行时发现，**不**是预先硬编码）；项目根存在 `.mcpowers-version: v{major}.{minor}.{patch}` 时 AI 默认读该版本；用户显式指定"按 v{major}.{minor}.{patch} 规范写"时 AI 按指令读历史版本。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)「最高铁律 · mcpowers 注入路径稳定性 §运行时版本访问白名单」。

**规范稳定性分级 + CHANGELOG 强制破坏声明（v2.27.4+ 全栈适用铁律）**：所有 32 份规范 frontmatter 必须声明 `stability: stable|evolving|deprecated` + `last_breaking_change: v{major}.{minor}.{patch}`；AI 读取规范后必读这两个字段决定行为（stable 假设跨 minor 兼容 / evolving 升级时主动查 CHANGELOG / deprecated 不写新代码）。每次 mcpowers 发布的 `CHANGELOG.md` 必须含 `### Breaking Changes` 段（哪怕标"无"），作为用户升级兼容性的**唯一权威索引**。详见 [`代码规范.md`](skills/mcpowers-shared/docs/技术规范/代码规范.md)「最高铁律 · mcpowers 注入路径稳定性 §CHANGELOG 强制破坏声明段」；方法层落地：`mcpowers-code-review` 增 R9 stability 审查维度 + 审查动作清单第 6 项。

**终态交付基线**：文档与代码注释只描述当前状态，不保留历史演进痕迹（"原为 xxx" / "已废弃" / 变更历史章节）与参考来源指代（"参考 xxx 文档"）；变更历史只允许出现在 `CHANGELOG.md` 与 README「最近变更」。详见 `文档编写规范.md §9` + `代码规范.md §11.3`。

**文档编写铁律·画蛇添足字眼场景化规则（v4.0.2+ 用户决策 C·全栈适用）**：AI 写任何文档（不只是接口描述）都需遵守——**22 个禁用字眼**（中文 11 + 英文 11：参考 / 参见 / 详见 / 引用 / 参照 / 引自 / 根据规范 / 按照规范 / 按规范要求 / 遵守规范 / 按规范 + according to / refer to / referring to / as described in / as specified in / see also / conform to / conforms to / based on / defined in / outlined in）出现必须跑 3 问决策：**① 这段文字是给谁看的？** 对接方/终端用户=输出型 / 自己查的索引=参考型 / 追溯历史=历史型。**② 删掉字眼后意思会变吗？** 不变=画蛇添足=删，变=必要引用=保留。**③ 类型 + Q2 联合判定**——输出型禁止（删/改写）/ 参考型允许且必要 / 历史型允许（§9.4 白名单）。详见 [`文档编写规范.md`](skills/mcpowers-shared/docs/技术规范/文档编写规范.md) §9.5（场景化决策模型）+ §1.E 接口零引用铁律（v4.0.1+ 接口描述特化子集）。栈级落地：共享常量 `skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt`（v4.0.1 + v4.0.2 三处脚本共用）；软门禁 hook `post-write-check-doc-content.sh`（写 .md 时扫禁用字眼 + 6 类路径白名单区分场景 + exit 0 stderr 提示）；审查门禁：`mcpowers-code-review` 增 R16 反模式条目（文档正文含画蛇添足字眼）+ Quick-Check 段含 3 条扫描命令（输出型 .md 扫描 + 参考型白名单扫描 + 路径白名单检查）。

## 仓库地址

git@github.com:742366981/mcpowers.git

## 技能修改流程（重要）

修改本技能时，请遵循以下流程：

1. **先改本项目**：在当前工作目录下修改
2. **插件市场模式无需重装**：直接重启 Claude Code 即可生效（除非是首次安装）
3. **最后推送**：commit 并 push 到 git 仓库

**禁止**直接修改 `${CLAUDE_PLUGIN_ROOT}` 下的安装副本（插件市场模式下改了会被覆盖）。所有修改在源码仓库根目录进行。

### 文档同步约束（强制）

凡是新增、删除、重命名或调整技能体系的能力、路由、编排、规范、Hook、目录结构、安装方式或版本号，必须在同一变更中同步检查并更新：

- `CLAUDE.md`：维护规则、技能分类、触发映射、数量和验证流程
- `README.md`：用户功能说明、技能树、触发条件、安装和维护指南
- `skills/mcpowers/SKILL.md`：主路由器和技能清单
- `scripts/check-readme-sync.sh`：技能/规范清单和场景技能检查
- `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`：插件版本和市场元数据

新增场景技能时，还必须把技能加入 `SCENE_SKILLS`，并确认其包含 `## 编排` 段。禁止只修改 `skills/` 目录而不更新上述文档和校验项。纯规范正文修订至少运行同步检查；凡影响用户可见能力或体系结构的修订必须同步更新两份文档。

新增工具脚本时（如 `skills/<技能>/scripts/<新工具>.py`），还必须把脚本路径加到对应规范文档的 §工具对照表 / §字典库对应关系（参考《爬虫工具与抓包规范》§7.2 / 末尾附录）+ 顶层维护文档引用（参考 v2.15.0 `user-action-recorder.py` 的 8 类同步）。

#### CI 物理门禁（v2.5.2+）

`.github/workflows/doc-sync.yml` 在 PR 涉及 `skills/`、`hooks/`、`.claude-plugin/`、`scripts/`、`tests/`、规范变化时自动跑：
- `bash scripts/check-readme-sync.sh`（12 类一致性：技能/规范清单、frontmatter、场景编排、版本号、description ≤800c、文档数字、引用、逆向分层拓扑、公共合同、浏览器所有权门禁）
- `bash tests/plugin-verify.sh`（插件结构 + Hook 行为 + 事件组数 = 4 + 引用脚本存在）
- 检查 CLAUDE.md 或 README.md 是否在同一 PR 中变化（**未变化则 PR 红 X**，从"AI 自觉"升级为"合并前硬阻止"）

本地开发可选装 pre-commit hook（参考 README 末尾的 `.git/hooks/pre-commit` 示例）。

## Skill Description 编写规范（强制）

Claude Code 通过 L1 索引（每个 skill 的 `description` 字段）做语义匹配。**这是触发灵敏度的唯一可调旋钮**。

### 硬约束

| 项 | 要求 | 后果 |
|:---|:-----|:-----|
| **字符硬上限** | 1024 字符 | 超过会被 Claude Code 截断，**尾部触发词全部失效** |
| **字符安全预算** | ≤ 800 字符 | 保留 ~20% 余量，防误判 |
| **格式** | 单行紧凑（YAML 字符串在一行内） | 多行 `\|` 字面量块浪费 30%+ 字符预算 |

### 4 段式内容（用 `；` `，` 分隔）

```yaml
# ✅ 推荐
description: "骨架1 / 骨架2 / 骨架3 → 触发本技能。口语：xxx,xxx。中英：xxx,xxx。边界：邻技能1→A；邻技能2→B。流程一句话。"

# ❌ 禁止
description: |
  骨架触发
  
  口语：xxx      # ← 多行浪费 30%+ 字符预算
```

每段作用：
1. **骨架触发**（3-5 个最高频词） → 一眼命中
2. **口语变体**（30-50 个口语/倒装/省略） → 长尾覆盖
3. **中英混输**（3-8 个英文术语） → 兼容开发场景
4. **边界防误触发**（指向最相似邻技能） → 防止串技能

### 修改 description 后必跑检查

```bash
python -c "import os, re
for f in sorted(os.listdir('skills')):
  p = os.path.join('skills', f, 'SKILL.md')
  if not os.path.isfile(p): continue
  c = open(p, encoding='utf-8').read()
  m = re.search(r'^---\n(.*?)\n---', c, re.DOTALL)
  if not m: continue
  d = re.search(r'description:\s+(.+?)\s*$', m.group(1), re.MULTILINE)
  if not d: continue
  print(f'{f}: {len(d.group(1))}c {\"⚠\" if len(d.group(1))>800 else \"✓\"}')"
```

任一文件 > 800c → **立刻压缩**，**不要等截断问题出现再修**。

### 反模式（禁止）

- ❌ 多行 `|` 字面量块（截断风险首要元凶）
- ❌ 单段长句无结构（LLM 难以切片做语义匹配）
- ❌ 触发词与边界说明混在一起（混淆 L1 匹配方向）
- ❌ 单个 description < 100 字符（覆盖太窄，命中率低）
- ❌ 不区分近义技能（refactor / bugfix / requirement-change 极易串技能）
- ❌ 在本文件复制 `docs/历史教训.md` 或 `CHANGELOG.md` 内容（v2.21.1+ 强制；仅允许 1 行相对链接）

> **历史归档**：完整版本复盘（v2.0.3 → 当前）见 [`docs/历史教训.md`](docs/历史教训.md)。
> **用户视角变更**：见 [`CHANGELOG.md`](CHANGELOG.md)。

## 版本管理（强制）

**Claude Code 插件市场以 `plugin.json` 的 `version` 字段为唯一更新触发器**。version 不变，用户（包括你自己）的 Update now / `/plugin install` 都不会拉取新版。

### 修改技能体系后必须做

1. **bump version**：修改 `.claude-plugin/plugin.json` 的 `version` 字段
   - 修复 bug / 小改 → patch：`2.0.0` → `2.0.1`
   - 新增技能 / 功能 → minor：`2.0.0` → `2.1.0`
   - 破坏性改动 → major：`2.0.0` → `3.0.0`
2. **同步市场元数据**：`.claude-plugin/marketplace.json` 的 `plugins[0].version` 必须与 `plugin.json.version` 一致；当前单插件市场的顶层 `version` 也保持同一发布版本，避免元数据漂移。
3. **验证后再提交**：先运行 `bash scripts/check-readme-sync.sh`，再运行 `bash tests/plugin-verify.sh`。
4. **commit + push**：版本号和代码改动放在同一个 commit（或分两个 commit 都行，但必须一起 push）
5. **不要**用任何 hack 方式绕过 version 机制（删缓存、自建更新脚本等都禁止）

用户收到新版只需：
- `/plugin` → 选 mcpowers → `Update now`
- 或 `/plugin uninstall mcpowers@mcpowers` → `/plugin install mcpowers@mcpowers`

两种方式都需要先 bump version 才能生效。

## 技能安装（首次/重装）

通过 Claude Code 插件市场：

```bash
/plugin marketplace add https://github.com/742366981/mcpowers
/plugin install mcpowers@mcpowers
```

本地开发模式（指向本地路径）：

```bash
/plugin marketplace add /d/document/my/workspace/mcpowers
/plugin install mcpowers@mcpowers
```

## 设计维度

- **精准路由**：单入口路由器（`skills/mcpowers/`）+ 扁平化技能目录（32 个可路由技能），按意图关键词精准分流
- **方法复用**：TDD / Review / Plan / Brainstorm 等方法层技能被场景层按需编排
- **按需加载**：通过 `mcpowers-spec-index` 查表按需 Read 规范文件，避免爆上下文
- **铁律双约束**：软约束靠技能描述（`铁律` 段落 + `## 反模式（禁止）` ❌ 清单），硬约束靠 Claude Code hooks 物理阻断
- **资产零损耗**：32 个技术规范原地保留，路径不重组、不重命名
- **完全独立**：不依赖任何外部技能，Git 操作由 4 个 `mcpowers-git-*` 技能自包含
- **零安装脚本**：依赖 Claude Code 插件系统管理安装/卸载/升级，仓库零维护成本
