---
name: mcpowers-code-review
description: "code review / 代码审查 / 帮我审一下 / CR / review / 帮我看看这段代码 → 触发本技能。口语：帮我 review 一下这段/帮我审一下/审一下这段/审一下代码、帮我 CR 一下、检视一下、看看有没有问题/有没有 bug/代码质量怎么样/有没有问题/OK 吗/有什么问题、代码健康度怎么样、帮我把把关/过一遍、过一下代码、PR 要提交了/我要提 PR/提 MR 前帮我审、合并到 master 前帮我审、自审一下/自查/再审一遍、再帮我审一遍。中英：review, CR, PR review, MR review, code review, peer review, self-review。边界：完整测试→`mcpowers-tdd`；排查特定 bug→`mcpowers-bugfix`；性能审查→`mcpowers-optimize`。多维并行审查，Critical 阻塞提交。"
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
- 合并到 master 前（**强制**）
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
| **R12** | ❌ **控制台 formatter 默认走 colorlog / winston.format.colorize() / logrus ForceColors: true 等开颜色**（v2.29.2+ 跨语言总章铁律·零配置即合规）：模块 / 框架默认行为让 95% 用户不感知就拿到 ANSI 转义序列，污染复制粘贴（`\x1b[32m...` 混入 Markdown / issue 评论）+ 管道（`grep` / `tee` 关键字匹配穿插转义字符）+ 文件重定向（Loki / ELK 把 ANSI 当异常染色）+ 日志聚合平台（Sentry / DataDog 把 ANSI 字符串归类为 error）。**任何环境（dev / test / prod）一律默认关**；**min-module / sdk-design 内置日志工厂也必须硬编码走 plain**——不允许「等调用方传配置再关」。违反 `日志规范.md §7.6` | 默认 formatter 必须用 plain 实现（Python `logging.Formatter` / JS `winston.format.simple()` / Go `slog.NewTextHandler` / Java `java.util.logging.Formatter`）；用户主动配置才开启颜色（Python `LOG_CONSOLE_COLOR=True` / JS `colorize: true` 显式传参）；CR 看到默认分支直接挂 `colorlog.ColoredFormatter` / `ForceColors: true` / `winston.format.colorize()` 即阻塞；min-module / sdk 内置日志硬编码走 colorlog 也阻塞（v2.29.2+ 新增） |
| **R13** | ❌ **Swagger 接口 5 字段契约不完整**（v2.31.0+ 全栈适用铁律）：写接口文件（views.py / /views/ / router.{py,js,ts} 或 /router/ / /controllers/ / /api/ / /routes/ / /handlers/ / /endpoints/ / /urls.py / /resources/ / /blueprints/）时漏 `tags` / `summary` / `description` / `parameters` / `responses` 任一顶层字段，或 `parameters[]` 缺 `description`+`example`、或 `responses[]` 缺 `200`、或 `responses[]` 状态码缺 `schema`+`examples`。违反 `接口契约规范.md §1` + `Swagger字段契约.md §1` | 5 字段必须齐全（按规范 §1.A/B/C）；parameters 子字段必须含 description+example；responses 必须含 200 + 每个状态码含 schema+examples（业务接口只列 200；4xx/5xx 误列见 R14）；项目根 `.swagger-required-fields.yml` 自定义字段也必须满足；CR 看到缺任一字段即阻塞，要求补全后重跑 lint |
| **R14** | ❌ **业务接口 responses 误列 4xx/5xx**（v4.0.0+ 用户决策 A 铁律·业务接口响应规范）：业务接口 docstring 的 `responses:` 块误列 `401` / `403` / `404` / `500` 等 4xx/5xx 状态码——按新铁律，业务接口 HTTP 一律 `200`，业务成功 / 失败由响应体 `code` 字段判断（`code: 0` = 成功；`code: 10001` = 业务失败）；4xx/5xx 仅由框架层（Flask abort / Webargs / Flask-JWT-Extended 中间件）抛出，不由业务接口声明。违反 `接口契约规范.md §1.C.1` + `swagger-lint-helper.py check_business_api_responses` | 业务接口 responses 块只允许列 `200`；路径含 `login` / `logout` / `refresh` / `verify` / `register` / `password` / `download` / `export` / `stream` / `upload` / `file` / `attachment` 关键字的认证 / 流式 / 下载接口例外（可保留 401/416）；CR 看到业务接口 docstring 误列 `401` / `403` / `404` / `500` 即阻塞，要求删除并只保留 `200`；写时硬门禁已被 `swagger-lint-helper.py check_business_api_responses` 兜底，CR 复核时同步检查 |
| **R15** | ❌ **API 文档含禁用引用字眼**（v4.0.1+ 用户决策 B 铁律·接口文档零引用）：接口 docstring 的 `summary:` / `description:` / `parameters[].description` / `responses[].description` 等用户可见字段值含「参考 / 参见 / 详见 / 引用 / 参照 / 引自」+「根据规范 / 按照规范 / 按规范要求 / 遵守规范 / 按规范」+「according to / refer to / referring to / as described in / as specified in / see also」等指向其他文档的字眼——按 v4.0.1+ 铁律，接口文档（docstring → spec → md 全链路）应聚焦"怎么对接调用"，**不应含指向其他文档的字眼**——这些字眼会让对接方以为还要再去查其他文档才能用。违反 `接口契约规范.md §1.E` + `swagger-lint-helper.py check_no_reference_words` + `export_docs.py check_no_reference_words_spec` | 接口文档 description / summary 等字段值不应含指向其他文档的字眼；YAML 字段名行（`summary:` / `description:` 等结构标记行）跳过不扫；CR 看到 description 含「参考」「参见」「详见」「引用」「refer to」「according to」等字眼即阻塞，要求改写为在该接口 docstring 里直接说明（不引用其他文档）；写时硬门禁已被 `swagger-lint-helper.py check_no_reference_words` 兜底，导出时硬门禁已被 `export_docs.py check_no_reference_words_spec` 兜底，CR 复核时同步检查 |
| **R16** | ❌ **文档正文含画蛇添足字眼**（v4.0.2+ 用户决策 C 铁律·文档零引用）：通用文档（README / 用户手册 / 技术规范正文 / 设计文档 / 任何内容型 .md 文档）正文含「参考 / 参见 / 详见 / 引用 / 参照 / 引自」+「根据规范 / 按照规范 / 按规范要求 / 遵守规范 / 按规范」+「according to / refer to / referring to / as described in / as specified in / see also / conform to / conforms to / based on / defined in / outlined in」等 22 个禁止字眼（独立出现也算画蛇添足，不限于"在某文档后"），路径不在白名单内——按 v4.0.2+ 铁律（`文档编写规范.md §9.5`），输出型文档应聚焦"当前怎么做"，**不应含指向其他文档的字眼**；删掉字眼后读者对"当前该怎么做"的理解不受损即视为画蛇添足；3 问决策：① 这段文字是给谁看的？② 删掉字眼后意思会变吗？③ 输出型禁止 / 参考型允许且必要 / 历史型允许。违反 `文档编写规范.md §9.5` + `post-write-check-doc-content.sh` 软门禁 + CLAUDE.md 必读铁律段 | CR 看到输出型 .md 正文含 22 字眼任一即阻塞，要求改写为在该文档内直接说明（不引用其他文档）；参考型（mcpowers-spec-index / API 契约 / 迁移指南 / 技能索引）+ 历史型（CHANGELOG / 历史教训 / Deprecation / README「最近变更」）走路径白名单跳过；CLAUDE.md 段 + 6 文档场景技能（L1 + L3 + L4）+ 软门禁 hook（L5）共 6 层 AI 视野覆盖；v4.0.1 接口零引用 = R16 在接口描述这一子集的最严格实施 |
| **R17** | ❌ **代码注释 / 配置文件含禁用引用字眼**（v4.3.0+ 用户决策 D 铁律·代码/配置零引用智能二分）：代码注释（`#` 单行 / `"""` docstring / `//` JS / `--` SQL）/ YAML 配置文件 / JSON 配置文件 / .ini / .toml / .sh 头部注释含 22 字眼（中文 11 + 英文 11，共享常量 `_forbidden_ref_words.txt`）+ v4.3.0 新增 4 个口语化补充（遵循本项目规范 / 遵循团队规范 / 遵循本仓库规范 / 按团队规范）——按 v4.3.0 智能二分判定：①外部权威（RFC/PEP/W3C/OWASP/ISO/IEEE/公认作者/官方 URL/行业+规范前缀）→ 放行；②内部规范名（33 份规范 + 别名，共享常量 `_internal_spec_docs.txt`）→ 拦截；③项目内代码文件路径（`utils/xxx.py` / `apps/yyy.go` 等）→ 拦截；④项目内 .md 文档名（含 CLAUDE.md/README.md/AGENTS.md，**用户决策：无例外**）→ 拦截；⑤「按规范/根据规范/遵守规范」无外部前缀 → 拦截；⑥兜底 → 拦截。违反 `代码规范.md §11.3.1` + `pre-write-check-no-ref-words.sh` 硬门禁 + `post-write-check-no-ref-words.sh` 软门禁兜底 + 共享检测器 `scripts/check_no_ref_words.py` | CR 看到代码注释/配置含 22 字眼 + 4 口语化补充任一即阻塞；智能二分判定走 6 优先级（外部权威放行 / 内部规范拦截 / 项目内代码拦截 / .md 拦截 / 无前缀画蛇添足拦截 / 兜底拦截）；路径白名单 6 类（tests/ / fixtures/ / examples/ / templates/ / docs/历史教训/ / CHANGELOG.md）允许保留；PreToolUse Write 硬门禁 exit 2 已物理阻断，CR 复核 PR diff 即可；与 R15（接口零引用）+ R16（.md 零引用）共享 22 字眼清单，3 条铁律共用同一权威源 `_forbidden_ref_words.txt` 避免漂移 |
| **R18** | ❌ **接口 docstring 含冗余内容 / 通用响应分页未用 `$ref` 复用**（v4.4.0+ 用户决策 D 续·接口文档 SSOT 终态收敛）：接口 docstring `description` 字段含 8 类冗余内容（HTTP 状态码 / 认证方式 / 错误码清单 / 响应结构 / 完整路径 / 通用约束 / 路径内模块名 / summary 同义重复）+ 接口 `responses.200.schema` / `responses.200.examples` 内联展开 `{code, msg, data}` / `{records, page_no, ...}` 等通用响应 / 分页结构（未用 `$ref: '#/definitions/BizResponse'` 等复用全局组件）+ 接口 `security` 内联 `Bearer: []`（未用 `$ref: ['#/securityDefinitions/BearerAuth']` 复用全局安全声明）+ `description` 字段含完整接口路径（应只在 `Swagger(basePath=)` + `Blueprint(url_prefix=)` + `@bp.route` 三处声明）。**判别口诀**：删掉这段文字后对接方是否还能直接调通这个接口？能就说明是冗余，删。违反 `接口契约规范.md §1.A.1`（description 禁用内容清单）+ §1.F（`$ref` 复用铁律）+ `swagger_components.md`（5 全局组件 SSOT）+ `flask_swagger_config.py`（Flasgger 注入模板）+ `Flask后端规范.md §11.5`（应用工厂 4 步）+ `swagger-lint-helper.py check_description_redundant_content` / `check_no_path_in_description` / `check_no_repeated_schema` 3 个新检查函数 | CR 看到接口 docstring 含 8 类 description 冗余任一即阻塞（v4.5.0 起升级为 ERROR 阻塞——之前 v4.4.0 WARNING 过渡期已结束）；CR 看到通用响应/分页/认证结构内联展开即阻塞，要求改写为 `$ref: '#/definitions/BizResponse'` / `$ref: '#/definitions/PageResponse'` / `$ref: ['#/securityDefinitions/BearerAuth']` 复用全局组件；接口路径只允许在 `basePath` / 蓝图 `url_prefix` / `@bp.route` 三处声明，`description` 字段不再重复完整路径；`swagger_components.md` + `flask_swagger_config.py` 必须存在作为 SSOT 资产 |
| **R19** | ❌ **接口路径含动态参数 `<xxx>`**（v4.5.0+ 用户决策 D 续·接口契约 §1.G 铁律）：装饰器 `@bp.route('/detail/<int:id>')` / `@bp.route('/users/<user_id>/orders')` / `@bp.route('/update/<int:id>')` 等模板含 Flask 风格的动态参数 `<xxx>` / `<int:xxx>` / `<string:xxx>` / `<uuid:xxx>`——按 v4.5.0+ 铁律，所有资源标识（`id` / `user_id` / `order_id` 等）必须走 query 或 body 传递，路径模板禁止包含动态参数（避免前端路径拼接差异 + 后端路由表被无限扩张）。**例外白名单**（必须含 path param 的场景）：① webhook 回调 `/webhook/<source>`（§2.12）/ ② OAuth 第三方回调 `/auth/oauth/<provider>/callback`（§X.1）。违反 `接口契约规范.md §1.G` + `swagger-lint-helper.py check_no_dynamic_path` | CR 看到接口 `@bp.route` 装饰器路径模板含 `<...>` 模式即阻塞，要求改为 `@bp.route('/detail', methods=['GET'])` + query `id` 或 body `{"id": ...}`；例外白名单路径段含 `webhook` / `oauth` / `callback` 关键字自动跳过；写时硬门禁已被 `swagger-lint-helper.py check_no_dynamic_path` 兜底（AST 解析 `@bp.route` 装饰器路径字符串 + `/`、`-`、`_`、`.`、`<`、`>`、`:` 分段判例外），CR 复核 PR diff 即可 |
| **R20** | ❌ **HTTP 方法含 PUT/PATCH/DELETE/HEAD/OPTIONS**（v4.5.0+ 用户决策 D 续·接口契约 §1.H 铁律）：装饰器 `methods=` 列表含 `PUT` / `PATCH` / `DELETE` / `HEAD` / `OPTIONS` 之一——按 v4.5.0+ 铁律，业务接口 HTTP 方法**只允许 GET 或 POST**（列表/详情/字典/导出/下载/流式/进度 → GET；创建/更新/删除（单+批量）/导入/上传/bind/webhook → POST）；避免前端区分 PUT/PATCH 语义差异（`§2.4 update` 显式说明「为什么用 POST 不用 PUT」）。违反 `接口契约规范.md §1.H` + `swagger-lint-helper.py check_allowed_methods` | CR 看到业务接口 `methods=` 含 PUT/PATCH/DELETE/HEAD/OPTIONS 即阻塞；按 §0 / §2 速查表改为 GET 或 POST；速记表：列表/详情/字典/导出/下载/流式/进度 → GET；创建/更新/删除（单+批量）/导入/上传/bind/webhook → POST；写时硬门禁已被 `swagger-lint-helper.py check_allowed_methods` 兜底（methods= 列表 vs `_ALLOWED_HTTP_METHODS = frozenset({'GET', 'POST'})` 白名单比对），CR 复核 PR diff 即可 |
| **R21** | ❌ **`description` / `parameters[].description` / `responses[].description` 含鉴权字眼**（v4.5.0+ 用户决策 D 续·接口契约 §1.I 铁律）：接口 docstring 的 `description` 字段值 / `parameters[].description` / `responses[].description` 含 15 类鉴权字眼之一（`JWT` / `Bearer` / `需登录` / `需要登录` / `需 JWT` / `需要 JWT` / `需认证` / `需要认证` / `需鉴权` / `需要鉴权` / `需 token` / `需要 token` / `Authorization header` / `Authorization 头` / `鉴权失败`）——按 v4.5.0+ 铁律，鉴权方式由 Swagger 全局 `securityDefinitions` + `security` 声明，UI 自动展示锁图标，不必在每个接口 description 重述。违反 `接口契约规范.md §1.I` + `swagger-lint-helper.py check_no_auth_in_description` | CR 看到接口 description / parameters[].description / responses[].description 含鉴权字眼即阻塞，要求改写为简短接口功能描述；鉴权走全局 `securityDefinitions` + `security` 即可；YAML 字段名行（`key:` 末尾冒号且无 value）跳过不扫；写时硬门禁已被 `swagger-lint-helper.py check_no_auth_in_description` 兜底，CR 复核 PR diff 即可 |
| **R22** | ❌ **`description` 含错误码清单**（v4.5.0+ 用户决策 D 续·接口契约 §1.J 铁律）：接口 docstring 的 `description` 字段值罗列「10001 用户不存在 / 10002 用户已禁用」错误码清单（命中 6 类模式：① `错误码[：:]\s*\d+` / ② `错误码列表` / ③ `返回码[：:]?\s*\d+` / ④ `\d{5}\s+[一-鿿]` 标准行式 / ⑤ `code[:\s]+\d{4,}` / ⑥ `\d{5}\s*[、，,/]` 并列式）——按 v4.5.0+ 铁律，错误码统一在 `responses.examples` 或 `$ref BizError` 全局组件维护，description 短句仅说明接口功能。违反 `接口契约规范.md §1.J` + `swagger-lint-helper.py check_no_error_codes_in_description` | CR 看到接口 description 含 6 类错误码清单模式之一即阻塞，要求把错误码移到 `responses.examples` 或 `$ref BizError` 组件维护，description 改写为简短接口功能描述；写时硬门禁已被 `swagger-lint-helper.py check_no_error_codes_in_description` 兜底（6 类 `_ERROR_CODE_LIST_PATTERNS` 正则匹配），CR 复核 PR diff 即可 |
| **R23** | ❌ **POST 接口 Content-Type 非 JSON**（v4.5.1+ 铁律·接口契约 §1.K）：接口 `methods=` 含 `POST` 且 docstring `parameters[].in: formData` 或 `consumes:` 含 `application/x-www-form-urlencoded` / `multipart/form-data`（路径段不在豁免白名单内）——按 v4.5.1+ 铁律，业务接口 POST 一律 `Content-Type: application/json`，避免后端 `request.form` / `request.files` 兜底导致接口语义混乱；后端统一 `request.get_json()`，schema 校验交 Webargs / pydantic。**豁免白名单**（路径段内含关键字）：① 文件上传 `/upload` / `/attachment`（必须 multipart）；② 数据导入 `/import`（Excel/CSV 必须 multipart）；③ 第三方回调 `/webhook/<source>` / `/callback/<provider>` / `/notify` / `/oauth/<provider>/callback`（Content-Type 受第三方协议约束）。违反 `接口契约规范.md §1.K` + `swagger-lint-helper.py check_post_must_be_json` | CR 看到 POST 接口 docstring 含 `in: formData` 或 `consumes:` 含 form-urlencoded/multipart（非豁免路径段）即阻塞，要求改写为 `in: body` + JSON `schema` 或 `consumes: application/json`；豁免白名单（路径段含 `upload` / `import` / `attachment` / `webhook` / `callback` / `notify` / `oauth` 任一）自动跳过；写时硬门禁已被 `swagger-lint-helper.py check_post_must_be_json` 兜底（`in: formData` 正则 + consumes 字段扫描），CR 复核 PR diff 即可 |

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
git diff master...HEAD -U0 | grep -E "^\+[[:space:]]*(async[[:space:]]+)?(def|function|func|fn)[[:space:]]+" | sort -u
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
git diff master...HEAD -U0 | grep -E "^\+[[:space:]]+(import[[:space:]]+[A-Za-z_]|from[[:space:]]+[A-Za-z_.]+[[:space:]]+import)" | sort -u
# 2. 仓库所有 .py 文件的缩进 import（确认全文件现状）
rg --type py -n '^( +|\t+)(import|from\s+[^ ]+\s+import)' .
```

> 命令 1 命中 → Critical 阻塞，必须改为模块级导入；命令 2 仅作为全文件盘点依据，不直接阻塞但应纳入修复计划。

## v2.28.2+ 单行透传 Quick-Check（review 必跑）

> 对齐 `代码规范.md §6.1.1` v2.28.2 补充段。v2.28.2+ hook 已简化：跨文件同名默认放行，只有「同文件重名」+「单行透传 wrapper」两类 block。**hook 自动处理这 2 类，review 主要是兜底扫描**——单行透传 wrapper 是 hook 唯一仍在拦截的跨文件二次包装信号（gold standard）。

```bash
# 单行透传扫描：函数体仅一行 `return <已有函数>(...)` 的二次包装
# （hook 已自动拦截，但 review 仍要扫一遍兜底——防止 hook 配置丢失 / 受保护路径漏过）
git diff master...HEAD -U0 | rg -U "(?:async\s+)?(?:def|function|func|fn)\s+\w+\s*\([^)]*\)\s*:\s*\n\s*return\s+\w[\w.]*\s*\("
# 或全文件视角（审查时优先用 diff 视角）
rg --type py -U "def\s+\w+\s*\([^)]*\)\s*:\s*\n\s*return\s+\w[\w.]*\s*\(" .
```

> 命令命中 → Critical 阻塞——这是最经典的二次包装，无论同/不同命名空间都必须复用底层。
> **跨文件同名（非单行透传）已不再由 hook / review 强制拦截**——属业务模块各自实现，是否抽离由作者按需提 `mcpowers-extract`（见上方审查动作清单第 4 条）。

## v2.28.4+ 控制台日志级别紧凑 + stdout Quick-Check（review 必跑）

> 对齐 `日志规范.md §7.5` + `Flask后端规范.md §6.1` 控制台实现层。审查者收到 PR 后必须执行的 2 条扫描命令：

```bash
# 1. diff 内控制台 formatter 是否含 %(levelname)-Ns 宽度填充（命中即违规，应为 %(levelname)s）
git diff master...HEAD -U0 | rg "%\(levelname\)-[0-9]+s"

# 2. diff 内 StreamHandler() 是否显式传 stream=sys.stdout（未传即违规）
git diff master...HEAD -U0 | rg "StreamHandler\(\s*\)" | rg -v "stream="
```

> 命令 1 命中 → Critical 阻塞——formatter 字符串里 `%(levelname)-Ns` 宽度填充会输出 `[INFO   ]` 带填充空格；要求改回 `%(levelname)s`（无宽度）或 `%(levelname).1s`（首字母极简）。（注：`colorlog.ColoredFormatter(reset=True)` 只控制 ANSI 颜色重置，**不**控制 levelname 宽度——宽度由 format 字符串决定。）
>
> 命令 2 命中 → Critical 阻塞——Python `logging.StreamHandler()` 默认 `sys.stderr`，PyCharm / IntelliJ 会把 stderr 整体染红，即使日志级别是 INFO / DEBUG；必须显式 `stream=sys.stdout`。

## v2.29.2+ 默认无颜色 Quick-Check（review 必跑·跨语言总章铁律）

> 对齐 `日志规范.md §7.6` v2.29.2 总章铁律。**任何环境（dev / test / prod）一律默认关**；**min-module / sdk-design 内置日志工厂硬编码默认即合规**。审查者收到 PR 后必须执行的 4 条扫描命令：

```bash
# 1. Python 项目级控制台 formatter 三态保护（缺 LOG_CONSOLE_COLOR 开关即违规）
git diff master...HEAD -U0 | rg "setFormatter\([^)]*ColoredFormatter" | rg -v "if .*LOG_CONSOLE_COLOR"

# 2. JS / TS / Go / Rust diff 内默认开启颜色参数（命中即违规）
git diff master...HEAD -U0 | rg "colorize\s*:\s*true|ForceColors\s*:\s*true|with_ansi\s*\(\s*true\s*\)"

# 3. 项目级配置文件默认值检测（命中即违规——任何环境默认 False）
git diff master...HEAD -U0 | rg "console_color.*=.*True|console_color.*=.*true"

# 4. 模块内置日志硬编码默认值扫描（v2.29.2+ 新增）
#    min-module / sdk-design 的日志工厂即便在硬编码里出现 ColoredFormatter 也视为违规
git diff master...HEAD -U0 | rg "ColoredFormatter" | rg -v "if .*LOG_CONSOLE_COLOR|if .*console_color"
```

> 命令 1 命中 → Critical 阻塞——`colorlog.ColoredFormatter` **必须**受 `LOG_CONSOLE_COLOR` 配置开关保护，且默认 `False`；CR 看到控制台 formatter 默认挂 `ColoredFormatter` 即阻塞，要求改为 `if LOG_CONSOLE_COLOR: colorlog.ColoredFormatter(...) else: logging.Formatter(CONSOLE_FORMAT)` 三态。
>
> 命令 2 命中 → Critical 阻塞——`winston.format.colorize()` / `logrus.TextFormatter{ForceColors: true}` / `tracing_subscriber::fmt().with_ansi(true)` 都是默认开颜色；CR 看到任一即阻塞，要求调用方**主动传参**才生效。
>
> 命令 3 命中 → Critical 阻塞——`console_color` 默认值**必须**是 `False` / `false`；任何环境（dev / test / prod）一律 False；CR 看到 `True` / `true` 即阻塞，要求改为 `False` 并在配置文件示例里加注释「仅调用方主动开启」。
>
> 命令 4 命中 → Critical 阻塞（**v2.29.2+ 新增**）——模块内置日志（min-module / sdk-design）的 `get_logger` / `get_sdk_logger` 工厂即便在硬编码默认值里出现 `ColoredFormatter`，**也视为违规**：必须硬编码走 `logging.Formatter(...)` plain 实现，**不允许**「等调用方传配置再关」（详见 `日志规范.md §7.6.4`）。
>
> **跨语言判定标准（v2.29.2+ 总章铁律）**：
> - **项目级**：模块对外暴露的「日志工厂 / 配置默认值」里，任何会让 95% 用户不感知就拿到 ANSI 转义的写法 = 违规。
> - **模块内置**：min-module / sdk-design 自带日志工厂，**硬编码默认值**就必须是 plain formatter。开发者要颜色 → 主动传参。**不允许**模块「我代码里硬编码默认走 colorlog，等调用方传参关」。
> - **颜色开关任何环境默认关**——dev / test / prod 一律 False，没有「dev 环境例外」。

## v2.31.0+ Swagger 5 字段契约 Quick-Check（review 必跑）

> 对齐 `接口契约规范.md §1` + `Swagger字段契约.md §1` v2.31.0+ 全栈适用铁律。审查者收到 PR 后必须执行的 3 条扫描命令：

```bash
# 1. 接口文件顶层 5 字段齐全性扫描(命中 YAML 顶层键)
#    期望:tags/summary/description/parameters/responses 五者全在
git diff master...HEAD -U0 -- '*.py' '*.ts' '*.js' '*.java' '*.go' \
  | rg -B1 "@(bp|app|router)\.(get|post|put|delete|route)" \
  | rg "^\s*(tags|summary|description|parameters|responses):" \
  | rg -v "tags:|summary:|description:|parameters:|responses:" \
  | sort -u

# 2. parameters 子字段 description+example 配对扫描
#    期望:每个参数块 description: 与 example: 必须同时存在
git diff master...HEAD -U0 \
  | rg -A6 '^\s+-\s+in:\s+(query|body|path|formData|header)' \
  | rg -v 'description:|example:|in:|- name:'

# 3. responses 状态码扫描(v4.0.0+ 业务接口只列 200 是合规;认证/下载接口例外)
#    期望:业务接口只含 200;认证/下载接口可保留 401/416
git diff master...HEAD -U0 \
  | rg -A20 '^\s*responses:' \
  | rg "^\s+\d{3}:" \
  | awk -F: '{print $1}' | sort -u
```

> 命令 1 命中(接口 docstring 不含五者之一) → Critical 阻塞——CR 看到缺 `tags:` / `summary:` / `description:` / `parameters:` / `responses:` 任一即阻塞,要求补全后重跑 `bash scripts/swagger-contract-check.sh --file-path=<view>` 确认 exit 0。
>
> 命令 2 命中(parameters 块缺 description 或 example) → Critical 阻塞——`interface契约规范 §1.B` 强制每个参数必须含 `description` + `example`,前端调试时只看 example 即可传参,缺任一即视为不完整接口。
>
> 命令 3 命中(业务接口响应块含 4xx/5xx 且路径不在认证/下载白名单) → Critical 阻塞——`interface契约规范 §1.C.1 v4.0.0+` 业务接口响应规范铁律,业务接口 HTTP 一律 200,业务错误走 code 字段;CR 看到业务接口误列 401/403/404/500 即阻塞,要求删除并只留 200;详见 R14 Quick-Check + `swagger-lint-helper.py check_business_api_responses`。
>
> **跨栈判定标准(v2.31.0+ 全栈铁律)**:
> - **5 字段缺任一 = 接口视为不完整**,禁止合并 commit
> - **项目根 `.swagger-required-fields.yml` 自定义字段**也必须满足(用户主动扩展的必填字段,如 `deprecated` / `x-permission`)
> - **未装 swagger 的项目零摩擦放行**——detector 探测 `flasgger/apispec/fastapi/springdoc/openapi-typescript` 任一关键字才校验,纯业务项目直接跳过

## v4.0.0+ 业务接口响应规范 Quick-Check（review 必跑·用户决策 A）

> 对齐 `接口契约规范.md §1.C.1` + `swagger-lint-helper.py check_business_api_responses` 写时硬门禁。审查者收到 PR 后必须执行的扫描命令：

```bash
# 业务接口误列 4xx/5xx 扫描（v4.0.0+ 业务接口响应规范铁律）
# 期望：业务接口（路径不含 login/logout/refresh/verify/register/password
#                /download/export/stream/upload/file/attachment 关键字）
#       的 responses 块不应出现 4xx/5xx（401/403/404/416/422/500）
git diff master...HEAD -U0 \
  | rg -B1 -A20 'responses:' \
  | rg "^\s+(4\d{2}|5\d{2}):" \
  | rg -v "login|logout|refresh|verify|register|password|download|export|stream|upload|file|attachment"
```

> 命令命中（业务接口 responses 含 4xx/5xx）→ Critical 阻塞——按 v4.0.0+ 业务接口响应规范铁律，业务接口 HTTP 一律 200，业务错误走响应体 `code` 字段；4xx/5xx 仅由框架层（Flask abort / Webargs / Flask-JWT-Extended 中间件）抛出，不由业务接口在 docstring 声明。CR 看到误列即阻塞，要求删除并只保留 `200`，重跑 `bash scripts/swagger-contract-check.sh --file-path=<view>` 确认 exit 0。
>
> **白名单路径关键字**（不参与本检查）：`login` / `logout` / `refresh` / `verify` / `register` / `password`（认证接口）+ `download` / `export` / `stream` / `upload` / `file` / `attachment`（流式/下载接口）—— 这些接口可保留 401/416 等错误码。
>
> **写时硬门禁**：`swagger-lint-helper.py check_business_api_responses(docstring, route)` 在 PreToolUse(Write) 阶段拦截（exit 2 → Claude Code confirm UI），CR 复核时同步确认；该函数已替代旧 `check_responses_error_codes`（旧铁律与新铁律冲突，v4.0.0 删除）。

## v4.0.1+ API 文档零引用字眼 Quick-Check（review 必跑·用户决策 B）

> 对齐 `接口契约规范.md §1.E` + `swagger-lint-helper.py check_no_reference_words()` + `export_docs.py check_no_reference_words_spec()` 双层拦截。审查者收到 PR 后必须执行的扫描命令：

```bash
# 接口文件 docstring 描述字段值禁含指向其他文档的字眼
# 期望:命中 0 条违规
git diff -r master...HEAD \
  -- '*.py' '*.ts' '*.js' '*.java' '*.go' \
  | rg -B0 -A1 "^\+.*\s+(summary|description|in|200|201|401|403|500):\s+" \
  | rg -i "参考|参见|详见|引用|参照|引自|根据规范|按照规范|按规范要求|遵守规范|according to|refer to|referring to|as described in|as specified in|see also" \
  | rg -v "^--$"
```

> 命令命中 → Critical 阻塞——按 v4.0.1+ API 文档零引用铁律，接口文档应聚焦"怎么对接调用"，不应含指向其他文档的字眼；CR 看到 `summary` / `description` / `parameters[].description` / `responses[].description` 字段值含「参考」「参见」「详见」「引用」「refer to」「according to」等字眼即阻塞，要求改写为在该接口 docstring 里直接说明（不引用其他文档）。
>
> **白名单**（不参与本检查）：YAML 字段名行（`summary:` / `description:` 等形如 `key:` 末尾冒号且无 value 的纯结构标记行）—— 是结构不是字眼；业务术语「规范」作为普通名词（"接口规范""行业规范"）不违规，但「按规范」「按规范要求」违规。
>
> **双层写时硬门禁**：`swagger-lint-helper.py check_no_reference_words(docstring, route)` 在 PreToolUse(Write) 阶段拦截（exit 2 → Claude Code confirm UI）+ `export_docs.py check_no_reference_words_spec(spec)` 在拉 spec 后立即校验（exit 2 + stderr 列出违规位置 + 字眼片段），CR 复核时同步确认。

## v4.0.2+ 通用文档画蛇添足字眼 Quick-Check（review 必跑·用户决策 C）

> 对齐 `文档编写规范.md §9.5` 画蛇添足字眼场景化决策模型 + `post-write-check-doc-content.sh` 软门禁。审查者收到 PR 后必须执行的 3 条扫描命令（**输出型 vs 参考型 vs 历史型** 3 类场景，路径白名单区分）：

```bash
# 1. 输出型 .md 文档：扫 22 字眼（中文 11 + 英文 11）+ 路径不在白名单
#    期望:命中 0 条违规（白名单:CHANGELOG.md / docs/历史教训/ / mcpowers-spec-index/ / API契约/ / 迁移指南/ / migration/ / deprecation/）
git diff master...HEAD -U0 -- '*.md' \
  | rg -i "参考|参见|详见|引用|参照|引自|根据规范|按照规范|按规范要求|遵守规范|按规范|according to|refer to|referring to|as described in|as specified in|see also|conform to|conforms to|based on|defined in|outlined in" \
  | rg -v "CHANGELOG\.md|历史教训|mcpowers-spec-index|API契约|迁移|migration|deprecation"

# 2. 参考型文档白名单检查：路径含 6 类白名单标识 → 跳过（不视为违规）
git diff master...HEAD -U0 -- '*.md' \
  | rg -i "参考|参见|详见|引用|参照|引自" \
  | rg -i "CHANGELOG\.md|历史教训|mcpowers-spec-index|API契约|迁移|migration|deprecation" \
  | rg -v "^--$"
# 3. 路径白名单边界检查：确认白名单已覆盖 + 类比场景（如「REFERENCE.md」「指南」类）可主动加进 hooks/post-write-check-doc-content.sh
rg "CHANGELOG|历史教训|mcpowers-spec-index|API契约|迁移|migration|deprecation" hooks/post-write-check-doc-content.sh
```

> 命令 1 命中（输出型 .md 含 22 字眼且不在白名单）→ Critical 阻塞——按 v4.0.2+ 文档零引用铁律（`文档编写规范.md §9.5`），输出型文档（README / 用户手册 / 技术规范正文 / 设计文档）应聚焦"当前怎么做"，**不应含指向其他文档的字眼**；CR 看到命中即阻塞，要求改写为在该文档内直接说明（不引用其他文档）；删掉字眼后读者对"当前该怎么做"的理解不受损即视为画蛇添足——按 §9.5 决策 3 问：① 这段文字是给谁看的？② 删掉字眼后意思会变吗？③ 输出型禁止 / 参考型允许且必要 / 历史型允许。
>
> 命令 2 命中（路径在白名单里）→ 跳过——按 §9.5.5 跨场景落地表，参考型（mcpowers-spec-index / API 契约 / 迁移指南 / 技能索引）+ 历史型（CHANGELOG / 历史教训 / Deprecation / README「最近变更」）走路径白名单跳过。
>
> 命令 3 提示——若新增了参考型 / 历史型文档类型，需同步更新 `hooks/post-write-check-doc-content.sh` 路径白名单与 §9.5.5 落地表。
>
> **6 层 AI 视野覆盖（v4.0.2+）**：
> - L1 全局铁律段：`CLAUDE.md` 必读段（每次会话自动加载）
> - L2 L1 索引触发词：6 个文档场景技能 description 加触发词
> - L3 编排 Read 步骤：6 技能 ## 编排 / ## 触发即执行 Step 1 强 Read §9.5
> - L4 自检清单决策问句：3 技能 ## 自检清单加 3 决策问句
> - L5 软门禁 hook：`post-write-check-doc-content.sh`（写 .md 时扫 + 路径白名单 + exit 0 stderr 提示）
> - L6 审查门禁：R16 + 上述 Quick-Check 段（review 兜底）
>
> **与 v4.0.1 接口零引用关系**：R16 = §9.5 输出型在 API 接口描述（docstring）这一子集的最严格实施（v4.0.1 接口零引用 = R15，无扩展不涉及 .md 文档）；R16 把规则推广到所有输出型 .md 文档。两者共用 22 字眼清单（共享常量 `_forbidden_ref_words.txt`），避免漂移。

## v4.3.0+ 代码/配置零引用智能二分 Quick-Check（review 必跑·用户决策 D）

> 对齐 `代码规范.md §11.3.1` 智能二分判定 + `pre-write-check-no-ref-words.sh` 硬门禁 + `post-write-check-no-ref-words.sh` 软门禁兜底。审查者收到 PR 后必须执行的 8 条扫描命令（**覆盖代码 + 配置 6 类文件 + 4 类违规 + 路径白名单 + docstring 降级 + 外部权威放行 + 共享常量**）：

```bash
# 1. 代码/配置文件含 22 字眼 + 4 口语化（命中 → Critical）
#    覆盖 .py / .sh / .js / .ts / .yaml / .yml / .json / .ini / .toml / .go / .java / .rs
git diff master...HEAD -U0 -- '*.py' '*.sh' '*.js' '*.ts' '*.jsx' '*.tsx' \
  '*.yaml' '*.yml' '*.json' '*.ini' '*.toml' '*.go' '*.java' '*.rs' \
  | rg -i "参考|参见|详见|引用|参照|引自|根据规范|按照规范|按规范要求|遵守规范|按规范|遵循本项目规范|遵循团队规范|遵循本仓库规范|按团队规范|according to|refer to|referring to|as described in|as specified in|see also|conform to|conforms to|based on|defined in|outlined in" \
  | rg -v "^\\+\\+\\+|^---" \
  | rg -v "tests/|fixtures/|examples/|templates/|docs/历史教训/|CHANGELOG\.md"

# 2. docstring 内违规降级为 WARNING（不应阻塞,但需提示）
#    期望:docstring 中 22 字眼命中,但已在 hook 自动降级为 WARNING
git diff master...HEAD -U0 -- '*.py' \
  | rg '"""|'\'''\''' \
  -A 5 \
  | rg -i "参考|参见|详见|refer to"

# 3. 外部权威应放行（不应误拦）
#    期望:含 RFC/PEP/W3C/OWASP/官方 URL 的行 不在违规列表里
git diff master...HEAD -U0 -- '*.py' '*.yaml' '*.yml' \
  | rg -i "RFC[ -]?[0-9]+|PEP[ -]?[0-9]+|W3C|WHATWG|WCAG|OWASP|ASVS|ISO[/ ]?[0-9]+|IEEE|docs\.python\.org|developer\.mozilla\.org|vuejs\.org|react\.dev"

# 4. 内部规范名引用应拦截（期望:命中 = 真违规）
git diff master...HEAD -U0 -- '*.py' '*.yaml' '*.yml' \
  | rg "《代码规范》|《API规范》|《Flask后端规范》|《Vue前端规范》|《接口契约规范》|《Swagger字段契约》|《文档编写规范》"

# 5. 项目内代码文件路径引用应拦截（期望:命中 = 真违规）
git diff master...HEAD -U0 -- '*.py' '*.yaml' '*.yml' \
  | rg "utils/[a-z_]+\.py|apps/[a-z_]+/[a-z_]+\.go|src/[a-z_]+\.ts|hooks/[a-z_-]+\.sh"

# 6. 引用 CLAUDE.md / README.md / AGENTS.md 应拦截（用户决策:无例外）
git diff master...HEAD -U0 -- '*.py' '*.yaml' '*.yml' '*.md' \
  | rg -i "CLAUDE\.md|README\.md|AGENTS\.md"

# 7. 「按规范/根据规范/遵守规范」无外部前缀应拦截（兜底）
git diff master...HEAD -U0 -- '*.py' '*.yaml' '*.yml' \
  | rg -i "按规范要求|按照规范|遵守规范|按本项目规范|按团队规范|按行业规范|按国家标准|按国际标准" \
  | rg -v "RFC|PEP|OWASP|ISO|IEEE|行业|国家|国际|全球"

# 8. 共享常量 3 份必须存在 + 5 段骨架不被改坏
test -f skills/mcpowers-shared/docs/_assets/_forbidden_ref_words.txt
test -f skills/mcpowers-shared/docs/_assets/_internal_spec_docs.txt
test -f skills/mcpowers-shared/docs/_assets/_external_authority.txt
test -f skills/mcpowers-shared/scripts/check_no_ref_words.py
```

> 命令 1 命中（含 22 字眼 + 4 口语化且不在 6 类白名单）→ Critical 阻塞——按 v4.3.0+ 代码/配置零引用铁律（`代码规范.md §11.3.1`），代码注释/配置文件应聚焦"当前怎么做"，**不应含指向其他文档的字眼**；CR 看到命中即阻塞，要求改写为在该文件内直接说明（不引用其他文档）；删掉字眼后读者对"当前该怎么做"的理解不受损即视为画蛇添足。
>
> 命令 2 命中（docstring 含 22 字眼）→ WARNING 软提示——hook 自动降级为 WARNING，不强制阻塞；但 review 仍应询问"这段 docstring 是否真的需要引用其他文档？能不能直接说明？"
>
> 命令 3 命中（外部权威）→ 跳过——按 v4.3.0 智能二分优先级 2，含 RFC/PEP/W3C/OWASP/官方 URL 的引用属合规技术引用，应放行。
>
> 命令 4 命中（内部规范名）→ Critical 阻塞——按 v4.3.0 智能二分优先级 3，内部规范引用必须改写为直接说明当前做法。
>
> 命令 5 命中（项目内代码文件路径）→ Critical 阻塞——按 v4.3.0 智能二分优先级 4，注释应说明该文件做什么，不指向具体文件让读者跳转。
>
> 命令 6 命中（CLAUDE.md / README.md / AGENTS.md 引用）→ Critical 阻塞——按 v4.3.0 智能二分优先级 5 + 用户决策，CLAUDE.md/README.md 无例外，注释应自洽。
>
> 命令 7 命中（无外部前缀的「按规范」类）→ Critical 阻塞——按 v4.3.0 智能二分优先级 6，删掉字眼后意思不变视为画蛇添足；如确需引用规范名（含 RFC/PEP/行业/国家/国际前缀）则放行。
>
> 命令 8 失败（共享常量/检测器缺失）→ Critical 阻塞——v4.3.0 智能二分依赖 3 份共享常量 + 1 个检测器，缺任一即视为门禁被破坏。
>
> **6 层 AI 视野覆盖（v4.3.0+）**：
> - L1 全局铁律段：`CLAUDE.md` 必读段（每次会话自动加载）
> - L2 L1 索引触发词：6 个代码/配置场景技能 description 加触发词
> - L3 编排 Read 步骤：6 技能 ## 编排 / ## 触发即执行 Step 1 强 Read §11.3.1
> - L4 自检清单决策问句：3 技能 ## 自检清单加"代码注释含字眼？"问句
> - L5 硬门禁 hook：`pre-write-check-no-ref-words.sh`（写代码/配置时智能二分 → exit 2 confirm UI）+ `post-write-check-no-ref-words.sh` 软兜底
> - L6 审查门禁：R17 + 上述 Quick-Check 段（review 兜底）
>
> **与 R15/R16 关系**：R15 = 接口零引用（docstring/spec/md 接口子集）；R16 = 文档零引用（输出型 .md）；R17 = 代码/配置零引用（代码注释 + YAML/JSON/INI/TOML）。三者共用 22 字眼清单（共享常量 `_forbidden_ref_words.txt`），避免漂移；3 条铁律层层递进——接口最严（含字段值）、文档次严（路径白名单区分场景）、代码/配置最广（智能二分覆盖所有写入场景）。

## v4.4.0+ 接口文档 description 零冗余 + `$ref` 复用 Quick-Check（review 必跑·用户决策 D 续）

> 对齐 `接口契约规范.md §1.A.1`（description 禁用 8 类内容）+ §1.F（`$ref` 复用铁律）+ `swagger_components.md`（5 全局组件 SSOT）+ `flask_swagger_config.py`（Flasgger 注入模板）+ `Flask后端规范.md §11.5`（应用工厂 4 步）。审查者收到 PR 后必须执行的 4 条扫描命令（**v4.4.0 WARNING 阶段不阻塞但应记录 + 要求改写；v4.5.0 起升级为 ERROR 硬阻塞**）：

```bash
# 1. 接口 docstring description 字段 8 类禁用内容扫描
#    期望:命中 0 条（命中即视为冗余,删掉后对接方仍能调通）
git diff master...HEAD -U0 -- '*.py' '*.ts' '*.js' '*.java' '*.go' \
  | rg -B1 -A2 '^\s*description:\s*' \
  | rg -i "HTTP\s*\d{3}|状态码|需.*鉴权|需.*认证|需.*登录|需.*JWT|Bearer.*Token|返回.*\{.*code.*msg.*data|10001|用户不存在|完整路径|/api/v\d+/\S+|业务接口统一响应|模块名|用户管理接口|角色管理接口|权限管理接口" \
  | rg -v "summary:|tags:|description:|- "

# 2. 通用响应/分页/认证未用 $ref 复用扫描（应改写为 $ref 引用全局组件）
#    期望:通用响应/分页 schema 走 $ref 复用（不应内联展开 {code, msg, data}/{records, page_no, ...}）
git diff master...HEAD -U0 -- '*.py' \
  | rg -A3 '^\s*(schema|examples):\s*$' \
  | rg '\s+(code|msg|data|records|page_no|page_size|total|items):\s'

# 3. 接口 description 含完整路径扫描（路径只允许在 basePath + 蓝图 url_prefix + @bp.route 三处声明）
#    期望:命中 0 条
git diff master...HEAD -U0 -- '*.py' \
  | rg -A1 '^\s*description:\s*' \
  | rg "完整路径|/api/v\d+|/v\d+/" \
  | rg -v "summary:|tags:"

# 4. 全局组件 SSOT 资产存在性扫描（v4.4.0+ 落地必备）
test -f skills/mcpowers-shared/docs/API文档/swagger_components.md
test -f skills/mcpowers-shared/docs/API文档/flask_swagger_config.py
rg "StandardResponse|BizResponse|PageResponse|BizError|FileResponse|BearerAuth" skills/mcpowers-shared/docs/API文档/swagger_components.md
rg "check_description_redundant_content|check_no_path_in_description|check_no_repeated_schema" skills/mcpowers-shared/scripts/swagger-lint-helper.py
```

> 命令 1 命中（接口 docstring description 含 8 类禁用内容任一）→ WARNING 软提示（v4.4.0）→ v4.5.0 ERROR 硬阻塞——按 v4.4.0+ 接口文档 SSOT 终态收敛铁律（`接口契约规范.md §1.A.1`），8 类 description 禁用内容（HTTP 状态码 / 认证方式 / 错误码清单 / 响应结构 / 完整路径 / 通用约束 / 路径内模块名 / summary 同义重复）会让对接方误以为还要再去查其他资料才能调用——按「删掉字眼后对接方是否还能调通」判别口诀，能就说明是冗余，删。
>
> 命令 2 命中（通用响应/分页/认证 schema 内联展开）→ WARNING 软提示（v4.4.0）→ v4.5.0 ERROR 硬阻塞——按 v4.4.0+ `$ref` 复用铁律（`接口契约规范.md §1.F`），5 个全局组件（`StandardResponse` / `BizResponse` / `PageResponse` / `BizError` / `FileResponse` + `BearerAuth`）必须在 `Swagger(app, template={..., **SWAGGER_TEMPLATE})` 一次性注入；接口 docstring 用 `$ref: '#/definitions/BizResponse'` / `$ref: '#/definitions/PageResponse'` 复用而非内联展开 `{code, msg, data}` / `{records, page_no, ...}`；认证用 `$ref: ['#/securityDefinitions/BearerAuth']` 复用而非内联 `Bearer: []`。
>
> 命令 3 命中（description 含完整路径）→ WARNING 软提示（v4.4.0）→ v4.5.0 ERROR 硬阻塞——接口路径只在 `Swagger(template=..., basePath='/api/v1')` + `Blueprint(url_prefix='/biz')` + `@bp.route('/list')` 三处声明；`description` 字段不应再重复完整路径，否则当 `url_prefix` 或 `basePath` 变化时所有接口 description 都要跟着改。
>
> 命令 4 失败（SSOT 资产缺失）→ Critical 阻塞——v4.4.0 终态收敛依赖 2 份新文件（`swagger_components.md` + `flask_swagger_config.py`）+ 3 个新检查函数 + `Flask后端规范.md §11.5` 4 步挂载流程，缺任一即视为门禁被破坏。
>
> **6 层 AI 视野覆盖（v4.4.0+）**：
> - L1 全局铁律段：`CLAUDE.md` 必读段（每次会话自动加载）
> - L2 L1 索引触发词：`mcpowers-feat` + `mcpowers-api-contract` description 加 v4.4.0 触发词
> - L3 编排 Read 步骤：相关技能 ## 编排 / ## 触发即执行 Step 1 强 Read `接口契约规范.md §1.A.1` + `§1.F`
> - L4 自检清单决策问句：「description 含 8 类冗余？」「通用响应/分页是否走 `$ref`？」问句
> - L5 软门禁：`swagger-lint-helper.py check_description_redundant_content` / `check_no_path_in_description` / `check_no_repeated_schema` 3 个新检查函数（WARNING 阶段不阻断；v4.5.0 起升级为 ERROR 硬阻断）
> - L6 审查门禁：R18 + 上述 Quick-Check 段（review 兜底）
>
> **渐进迁移路径**：
> - **v4.4.0**（当前版本）：3 个新检查函数 WARNING 阶段，不阻断；CR 仍应记录 + 要求改写
> - **v4.5.0**：3 个新检查函数升级为 ERROR 硬阻断（PreToolUse Write exit 2 → Claude Code confirm UI）
> - **v5.0.0**：考虑全面替换 `export_docs.py` 表格模板为 `$ref` 全展开视图（自动渲染全局组件）

## v4.5.0+ 接口契约四铁律 ERROR 硬门禁 Quick-Check（review 必跑·用户决策 D 续）

> 对齐 `接口契约规范.md §1.G`（路径禁动态参数）+ §1.H（HTTP 方法白名单）+ §1.I（description 禁鉴权）+ §1.J（description 禁错误码清单）。审查者收到 PR 后必须执行的 4 条扫描命令（**v4.5.0 起全部 ERROR 硬门禁，无 WARNING 过渡期**——4 条规则都是「明确反模式，不是风格建议」）：

```bash
# 1. 装饰器路径含动态参数 <xxx> 扫描（v4.5.0+ §1.G 铁律）
#    期望:业务接口命中 0 条；webhook/oauth/callback 段内例外白名单跳过
git diff master...HEAD -U0 -- '*.py' \
  | rg "@(?:bp|app|router|api)\.(?:route|get|post)\(['\"][^'\"]*<[^>]+>" \
  | rg -v "(webhook|oauth|callback)"

# 2. 装饰器 methods= 含禁用方法扫描（v4.5.0+ §1.H 铁律：只允许 GET 或 POST）
#    期望:命中 0 条
git diff master...HEAD -U0 -- '*.py' \
  | rg "methods\s*=\s*\[[^\]]*['\"](?:PUT|PATCH|DELETE|HEAD|OPTIONS)['\"]"

# 3. description / parameters[].description / responses[].description 含鉴权字眼扫描（v4.5.0+ §1.I 铁律）
#    期望:命中 0 条（15 类鉴权字眼：JWT / Bearer / 需登录 / 需 JWT / 需认证 / 需鉴权 / 需 token / Authorization 等）
git diff master...HEAD -U0 -- '*.py' \
  | rg -A3 '^\s*(description:|parameters:|responses:)' \
  | rg -i "JWT|Bearer\s*Token|需.*登录|需.*认证|需.*鉴权|需.*JWT|Authorization\s*header|鉴权失败"

# 4. description 含错误码清单扫描（v4.5.0+ §1.J 铁律：6 类模式）
#    期望:命中 0 条
git diff master...HEAD -U0 -- '*.py' \
  | rg -A5 '^\s*description:\s*$|^\s*description:\s*[^\s]' \
  | rg "错误码[:：]\s*\d+|错误码列表|返回码[:：]?\s*\d+|\d{5}\s+[一-鿿]|code[:\s]+\d{4,}|\d{5}\s*[、，,/]"
```

> 命令 1 命中（装饰器路径含 `<...>` 且不在 webhook/oauth/callback 白名单内）→ Critical 阻塞——按 v4.5.0+ §1.G 路径禁动态参数铁律，所有资源标识走 query 或 body；反例 `/detail/<int:id>` 改为 `/detail?id={id}`；例外白名单（段内含 `webhook` / `oauth` / `callback` 关键字）自动跳过；写时硬门禁已被 `swagger-lint-helper.py check_no_dynamic_path` 兜底（AST 解析 `@bp.route` 装饰器），CR 复核 PR diff 即可。
>
> 命令 2 命中（`methods=` 含 PUT/PATCH/DELETE/HEAD/OPTIONS）→ Critical 阻塞——按 v4.5.0+ §1.H HTTP 方法白名单铁律，业务接口只允许 GET 或 POST；按 §0 / §2 速查表对应改为 GET（列表/详情/字典/导出/下载/流式/进度）或 POST（创建/更新/删除/批量删除/导入/上传/bind/webhook）；写时硬门禁已被 `swagger-lint-helper.py check_allowed_methods` 兜底。
>
> 命令 3 命中（description / parameters[].description / responses[].description 含鉴权字眼）→ Critical 阻塞——按 v4.5.0+ §1.I 铁律，鉴权方式由全局 `securityDefinitions` + `security` 声明，UI 自动展示锁图标，不必在每个接口 description 重述「JWT / Bearer / 需登录」；写时硬门禁已被 `swagger-lint-helper.py check_no_auth_in_description` 兜底（15 类 `_AUTH_WORDS_IN_DESCRIPTION` 扫描）。
>
> 命令 4 命中（description 含 6 类错误码清单模式之一）→ Critical 阻塞——按 v4.5.0+ §1.J 铁律，错误码统一在 `responses.examples` 或 `$ref BizError` 全局组件维护，description 短句仅说明接口功能；写时硬门禁已被 `swagger-lint-helper.py check_no_error_codes_in_description` 兜底（6 类 `_ERROR_CODE_LIST_PATTERNS` 正则匹配）。
>
> **6 层 AI 视野覆盖（v4.5.0+ 四铁律）**：
> - L1 全局铁律段：`CLAUDE.md` 必读段（每次会话自动加载）——v4.5.0 接口契约四铁律
> - L2 L1 索引触发词：`mcpowers-feat` + `mcpowers-api-contract` + `mcpowers-requirement-change` description 加 v4.5.0 触发词
> - L3 编排 Read 步骤：相关技能 ## 编排 / ## 触发即执行 Step 1 强 Read `接口契约规范.md §1.G-§1.J` + `swagger-lint-helper.py` 4 个新检查函数
> - L4 自检清单决策问句：「路径含动态参数？」「methods= 在白名单？」「description 含鉴权？」「description 含错误码清单？」4 问句
> - L5 硬门禁：`swagger-lint-helper.py check_no_dynamic_path` / `check_allowed_methods` / `check_no_auth_in_description` / `check_no_error_codes_in_description` 4 个新检查函数（v4.5.0 起 ERROR 级，PreToolUse Write exit 2 → Claude Code confirm UI）
> - L6 审查门禁：R19 + R20 + R21 + R22 + 上述 Quick-Check 段（review 兜底）
>
> **与 R18 关系**：R18 = description 8 类禁用内容（HTTP 状态码 / 完整路径 / 响应结构 等）——v4.4.0 WARNING → v4.5.0 ERROR；R19-R22 = v4.5.0 直接 ERROR（无过渡期）——因为这 4 条是「明确反模式」而不是「风格建议」（路径传 id 前端拼接差异 / PUT/PATCH 语义混淆前端调试困难），不留 WARNING 试错期。

## v4.5.1+ POST 强制 JSON Quick-Check（review 必跑）

> 对齐 `接口契约规范.md §1.K`（POST 一律 application/json）。审查者收到 PR 后必须执行的 1 条扫描命令（**v4.5.1 起 ERROR 硬门禁，无 WARNING 过渡期**——这是「明确反模式」不是风格建议）：

```bash
# POST 接口非豁免路径段含 in: formData / consumes 含 form-urlencoded / multipart 扫描（v4.5.1+ §1.K 铁律）
#    期望:命中 0 条（POST + formData/form-urlencoded 视为违规；豁免白名单路径段 upload/import/attachment/webhook/callback/notify/oauth 跳过）
git diff master...HEAD -U0 -- '*.py' \
  | rg -B5 -A0 "methods\s*=\s*\[[^\]]*['\"]POST['\"]" \
  | rg "in:\s*formData|consumes:.*(application/x-www-form-urlencoded|multipart/form-data)" \
  | rg -v "upload|import|attachment|webhook|callback|notify|oauth"
```

> 命令命中（POST 接口 + in: formData / consumes 含 form-urlencoded/multipart，且路径段不在豁免白名单内）→ Critical 阻塞——按 v4.5.1+ §1.K POST 强制 JSON 铁律，业务接口 POST 一律 `Content-Type: application/json`；改写为 `in: body` + JSON `schema` 或 `consumes: application/json`；豁免白名单（路径段含 `upload` / `import` / `attachment` / `webhook` / `callback` / `notify` / `oauth` 任一关键字）自动跳过；写时硬门禁已被 `swagger-lint-helper.py check_post_must_be_json` 兜底（`in: formData` 正则 + consumes 字段扫描 + 路径段白名单判定），CR 复核 PR diff 即可。
>
> **6 层 AI 视野覆盖（v4.5.1+ §1.K）**：
> - L1 全局铁律段：`CLAUDE.md` 必读段（每次会话自动加载）——v4.5.1 POST 强制 JSON 铁律
> - L2 L1 索引触发词：`mcpowers-feat` + `mcpowers-api-contract` + `mcpowers-requirement-change` description 加 v4.5.1 触发词
> - L3 编排 Read 步骤：相关技能 ## 编排 / ## 触发即执行 Step 1 强 Read `接口契约规范.md §1.K` + `swagger-lint-helper.py` 5 个新检查函数
> - L4 自检清单决策问句：「POST 接口是否声明 formData / form-urlencoded？是否在豁免白名单？」2 问句
> - L5 硬门禁：`swagger-lint-helper.py check_post_must_be_json()`（v4.5.1 起 ERROR 级，PreToolUse Write exit 2 → Claude Code confirm UI）
> - L6 审查门禁：R23 + 上述 Quick-Check 段（review 兜底）
>
> **与 R19-R22 关系**：R19-R22 = v4.5.0 四铁律（路径 / 方法 / 鉴权 / 错误码清单）；R23 = v4.5.1 新增（POST 强制 JSON）——5 条规则都是「明确反模式不是风格建议」，全部 ERROR 级无 WARNING 过渡期。

## 审查后

- 修复完成 → 再审一次
- 整体通过 → 调 `mcpowers-git-commit` 提交
