---
name: mcpowers-min-module
description: "最小通用模块化 / 绝对零业务 / 无任何外部参考 / 自包含四件套 / 复制即用跨项目零成本 → 触发本技能。口语：做成最小模块、通用化工具、抽成独立模块、可import的模块、零业务字眼、无项目名/无业务字段、无任何参考引用、通用utils/日志/校验/重试、自包含模块。中英：min-module,standalone module,reusable module,absolute zero business,no external reference,business-free,zero business audit,cross-project。边界：封装特定领域能力→mcpowers-sdk-design；原地改结构→mcpowers-refactor；从零搭骨架→mcpowers-init；从已有项目抽离可复用资产→mcpowers-extract。流程：识别技术能力→剥离业务→§0零业务审计→自包含四件套→配置自包含→自带日志异常→验证脚本→七类扫描兜底。"
---

# mcpowers-min-module（最小通用模块化）

> **核心**：把**通用技术能力**沉淀为「任何项目复制即用、绝对零业务、自包含日志/异常/配置/验证脚本」的最小工具模块。
> 不是 `mcpowers-refactor`（原地改结构），不是 `mcpowers-extract`（从已有项目抽离）——本技能专注**最小模块的最终形态标准**：产物可立即被任意项目 `cp -r` 复用，无需二次抽象。

> **语言中立**：本技能默认示例是 Python（mcpowers 现有规范倾向），但"自包含四件套 / 绝对零业务 / 禁读环境变量"等机制对任何语言都适用；用户项目用什么语言，按该语言的对应形式实现即可。

> **绝对零业务（v2.28.1+ 定义性铁律）**：本技能所有规则、示例、术语必须围绕**该模块自身的技术能力**展开。模块代码 / 注释 / docstring / 配置示例 / README / 验证脚本 / 错误消息字符串 / 日志字段名 / 模块名 / 文件名——任何产出物都**禁止**含具体业务名、字段名、项目名、厂商名、具体路径、外部参考字眼。模块只描述自己做什么、怎么做，不指代任何外部对象。

---

## §0 绝对零业务审计（v2.28.1+ 定义性铁律）

**任何产物在自称为 min-module 之前必须通过 §0 审计；任何一项命中即不通过——不叫 min-module，只是普通模块。**

### §0.1 禁止的字眼（不限于）

| 类别 | 禁止示例 | 允许替代 |
|:-----|:---------|:---------|
| **具体业务名** | 项目名 `bangkokair` / 业务字段 `order_status` / 状态机 `payment_pending` / 厂商名 `stripe` | 抽象占位符 `<your_module_name>` / `{module_name}` / `CHANGE_ME` |
| **具体路径字面值** | `C:\projects\xxx` / `D:\workspace\yyy` / `/Users/alice/foo` / `/home/bob/bar` | 跨平台抽象 `pathlib.Path.home() / ".cache" / "{模块名}"` |
| **环境变量读取** | `os.getenv("API_KEY")` / `os.environ["TOKEN"]` / `process.env.SECRET` / `${ENV_VAR}` | 配置文件 + 运行时覆盖 dict / 命令行参数 |
| **真实凭据** | `sk-xxx...` / `AKIA...` / `Bearer eyJhbGc...` | `CHANGE_ME` / `<your-credential>` 占位符 |
| **外部参考字眼** | "参考 XXX 文档" / "引用 XXX 规范" / "详见 XXX" / "参见 XXX" / "借鉴 XXX" / "基于 XXX 改进" / "类似 XXX 但更..." / "致敬 XXX" / "致谢 XXX" / `based on xxx` / `inspired by xxx` / `reference: xxx` / `see also xxx` | 只描述该模块自身的技术决策（"按 X 协议"、"遵循 RFC 7231"等通用标准是允许的） |
| **其他项目路径** | `<project_root>/xxx` / `<your_app>/yyy` / `<repo_root>/zzz` / `<app_root>/...`（即使抽象路径也禁止） | 跨平台抽象 `Path(__file__).parent / "defaults.ini"` / `Path.home() / ".cache" / "{name}"` |
| **模块名 / 文件名业务前缀** | `payment_utils.py` / `order_validators.py` / `bangkokair_client.py` | 通用名 `validators.py` / `retry.py` / `loggings.py` / `client.py` |

### §0.2 例外（允许的字眼）

| 类别 | 允许示例 | 理由 |
|:-----|:---------|:-----|
| 通用技术术语 | `HTTP` / `OAuth` / `SQL` / `JSON` / `trace_id` / `request_id` / `Order`（领域模型通用）/ `User`（通用概念） | 跨语言跨项目通用 |
| 协议 / RFC 引用 | "按 RFC 7231" / "遵循 OAuth 2.0" / "兼容 HTTP/2" | 公开标准，非具体项目 |
| 抽象占位符 | `<your_module_name>` / `{module_name}` / `CHANGE_ME` / `<sdk_root>` / `<your-credential>` | 模块本身通用 |
| 跨平台抽象路径 | `pathlib.Path.home() / ".cache" / "{模块名}"` / `Path(__file__).parent` | 不绑定具体机器 |

### §0.3 审计命令（任何模块自称为 min-module 之前必跑）

```bash
# 1. 业务字眼扫描（替换 ${项目名} / ${业务字段} / ${厂商} 为实际词）
rg -i "${项目名}|${业务字段}|${状态机}|${厂商}" {module_dir}/

# 2. 具体路径扫描
rg "C:\\\\|D:\\\\|/Users/|/home/[^/]+/" {module_dir}/

# 3. 环境变量读取扫描
rg "os\.getenv|os\.environ|process\.env|\${ENV}" {module_dir}/

# 4. 真实凭据扫描
rg "sk-[A-Za-z0-9]{20}|AKIA[A-Z0-9]{16}|Bearer [A-Za-z0-9]{20}" {module_dir}/

# 5. 外部参考字眼扫描
rg -in "参考|引用|参照|借鉴|致谢|致敬|改进自|参考:|reference:|see also|详见|参见|类似|based on|inspired by" {module_dir}/

# 6. 其他项目路径扫描（即使抽象路径也禁止）
rg "<project|<your.*project|<your_workspace|<repo_root|<app_root" {module_dir}/

# 7. 一键脚本：bash scripts/check-min-module.sh {module_dir}/
```

**任一项命中 → §0 审计不通过 → 不是 min-module**，必须替换或移除后重跑。

---

## 核心定义

| 要求 | 说明 |
|:-----|:-----|
| **零业务字眼** | 模块代码 / 注释 / docstring / 配置 / README 不出现任何具体业务名、字段名、项目名、厂商名 |
| **外部依赖边界** | 仅允许 (1) 该语言标准库 (2) 已在项目 `requirements.txt` / `package.json` / `go.mod` 中且与该模块能力直接相关的第三方库 |
| **禁止 import** | 绝对禁止 import 本项目 utils/common/config 任何业务模块；禁止 import 框架级业务路由 |
| **禁止读环境变量** | 禁 `os.getenv(...)` / `os.environ[...]` / `process.env.*` / `${ENV}` 任何形式；配置统一走 `defaults.ini` + 运行时覆盖 dict |
| **自包含四件套** | (a) 自带日志系统 (b) 自带异常体系 (c) 自带配置加载（`defaults.ini` 或硬编码常量）(d) 自带 manual 验证脚本 |
| **复制即用** | 任意项目 `cp -r {module_name}/` 即可使用，无需任何适配 |
| **典型承载** | HTTP 客户端、加解密算法、签名算法、数据校验器、通用重试器、连接池封装、日志框架等纯技术能力 |

---

## 通用规则

### ⛔ 铁律（不满足则不叫 min-module）

1. **§0 绝对零业务审计通过**——按 §0.3 七类扫描命令逐项跑通，任何命中即不通过
2. **可独立 import**——任意项目 `cp -r {module_name}/` 即可使用，无需任何适配；模块本身**不依赖**外部业务模块
3. **自包含四件套**——日志 / 异常 / 配置 / 验证脚本全部在模块内部
4. **外部依赖边界**——仅该语言标准库 + 直接相关第三方库；禁止拖家带口引入整个框架
5. **配置凭据全占位**——如需配置写 `defaults.ini`（或 `config.json` / `config.toml`），任何 key/secret/token 字段都是 `CHANGE_ME` / `<your-credential>` 占位符
6. **禁读环境变量**——所有 `os.getenv` / `os.environ` / `process.env` / `${ENV}` 全部禁止（v2.25.0+ 全栈最高铁律）

### ⚙️ 实现细节（满足铁律后的具体做法）

7. **通讯层中立**（仅当 min-module 含 IO 时）—— 不预设 HTTP / gRPC / WebSocket / 文件 IO，由用户场景决定

---

## 编排

本技能按需调用以下方法层技能 + 规范：

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-brainstorm` | 方法 | 边界不明确（候选是否技术能力/能否独立） | 中断并回问用户 |
| 2 | `mcpowers-plan` | 方法 | 任务 > 3 步 | 拆解成 2-5 分钟可验证小任务 |
| 3 | 规范组（按 mcpowers-spec-index 查表） | 规范 | 必读 | 中断，提示加载失败 |
| 4 | `mcpowers-tdd` | 方法 | 核心算法无验证保护 | 补最小验证脚本 |
| 5 | `mcpowers-code-review` | 方法 | 模块封装完成 | Critical 必须修复 |
| 6 | `mcpowers-git-commit` | Git | 收尾提交 | — |

**铁律**：
1. **§0 绝对零业务审计通过**——不通过则不叫 min-module（参见 §0）
2. **可独立 import**——任意项目 `cp -r {module_name}/` 即可使用
3. **自包含**——日志 / 异常 / 配置 / 验证脚本必须全部在模块内部
4. **外部依赖边界**——仅该语言标准库 + 直接相关第三方库
5. **配置凭据全占位**——写 `defaults.ini`（或对应格式）作为模块一部分，所有 key/secret/token 是 `CHANGE_ME`
6. **禁读环境变量**——所有 `os.getenv` / `os.environ` / `process.env` 全部禁止（v2.25.0+ 全栈最高铁律）

---

## 触发即执行（7 步）

### 1. 识别模块边界（技术能力 vs 业务逻辑）
- 扫描目标代码，识别「技术能力层」（可跨项目复用）vs「业务逻辑层」（与当前项目强绑定）
- 典型技术能力：HTTP 请求构造、加解密、签名算法、数据校验、重试逻辑、日志封装、配置加载
- 典型业务逻辑：具体业务 CRUD、页面渲染、具体业务字段处理
- 产出：**模块候选清单**（每项标注：技术能力类型 / 依赖分析 / 是否达零业务标准）

### 2. §0 绝对零业务审计（强制首步）
按 §0.3 七类扫描命令逐项跑通（业务字眼 / 路径字面值 / 环境变量读取 / 真实凭据 / 外部参考字眼 / 其他项目路径 / 模块名业务前缀）。任一项命中：
- 业务字眼 → 替换为抽象占位符（`<your_module_name>` / `{module_name}`）或参数化
- 路径字面值 → 改为相对路径（模块内部路径加载）或从配置读取
- 业务字段名 → 改为通用字段名或泛型参数
- 参考字眼 → 删除或改为该模块自身的技术决策描述

### 3. 外部依赖边界确认
- 列出模块内所有 `import` / `require` / `use` 语句
- 逐条判断：标准库 ✅ / 直接相关第三方库 ✅ / 业务模块 ❌
- 如发现禁止的 import → 替换为标准库等价实现或参数注入
- 确认**没有**任何形式的环境变量读取

### 4. 自包含日志系统设计（v2.29.2+ 强化·零配置即合规）

> **v2.29.2 核心新增**：min-module 自带的日志工厂**内部硬编码默认值**就必须是 plain formatter + stdout + 紧凑级别 + 无颜色 + INFO 级别——**调用方零配置即符合 §7.6**，无需传 ini / config / 任何开关。
>
> **不假设调用方会传配置**。min-module 是「复制即用」资产，调用方可能根本不知道有这个配置开关；如果硬编码默认走 colorlog，调用方拿到日志就带 ANSI——污染复制粘贴 / 管道 / 文件。

- 模块内部实现轻量日志类（**禁止依赖外部业务日志模块**）
- 日志默认行为（**v2.29.2+ 默认无颜色铁律——任何环境 dev/test/prod 一律默认关**，详见 `日志规范.md §7.6`）：
  - **级别**：INFO（`DEBUG` 可由调用方主动传参覆盖）
  - **输出流**：stdout（**禁止**默认 stderr——PyCharm / IntelliJ 会把 stderr 整体染红，详见 `日志规范.md §7.5.2`）
  - **时间戳**：毫秒精度 ISO8601 或本地时间（按语言生态选择，但**禁止**无时间戳）
  - **级别字段**：**紧凑**（Python `%(levelname)s` 禁用 `%(levelname)-Ns` 宽度填充；JS/Go/Rust 对应"无对齐字符填充"）
  - **颜色**：**默认关闭，任何环境统一**——除非调用方**显式**构造时传 `console_color=True`，**禁止**默认开启；硬编码默认值就是 `logging.Formatter(...)` 不是 `colorlog.ColoredFormatter(...)`（详见 `日志规范.md §7.6.4`）
- **首次调用日志工厂时自动安装默认 Handler，调用方零配置**（硬编码默认即合规）
- **可选**：构造参数 `console_color: bool = False`（默认 False）让主动要颜色的调用方按需开启；不传 = 默认无颜色
- **禁止**：读环境变量判断是否开颜色（`os.environ.get('LOG_COLOR')` 等违反 v2.25.0+ 全栈禁令 + §7.6）
- 幂等安装：多次调用不重复装 Handler
- 不污染 root logger：`propagate=False`
- 必含字段：`ts` / `level` / `logger_name` / `msg`；可选上下文：`trace_id` / `request_id`

**Python 内置日志工厂参考实现**（详见 `日志规范.md §7.6.4`）：

```python
def get_sdk_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)         # §7.5.2 显式 stdout
        handler.setFormatter(logging.Formatter(                    # §7.6.4 v2.29.2+ 默认 plain
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s')) # §7.5.1 紧凑级别
        handler.setLevel(logging.INFO)                             # §7.6 默认 INFO
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False                                   # 不污染 root
    return logger
```

> **JS/Go/Rust/Java**：默认走 `winston.format.simple()` / `slog.NewTextHandler(os.Stdout)` / `tracing-subscriber::fmt` 默认 / `java.util.logging.Formatter`——**不挂**任何 colorize / ANSI formatter，除非调用方显式传参。

### 5. 自包含异常体系设计
- 定义模块专属异常类（继承该语言标准异常基类）：
  - 基类 `ModuleError`（含 `error_code` 字符串字段）
  - 子类按能力分类：`ConfigError` / `ValidationError` / `ConnectionError` / `AuthError` / `RetryExhaustedError`
- 异常消息必须含 `error_code`（字符串枚举，如 `E001`）供调用方捕获判断
- 禁止抛出业务异常（与业务项目解耦）
- 异常类名纯技术，无业务绑定

### 6. 配置自包含（`defaults.ini` 或硬编码）
- **方式 A（推荐）**：模块根目录含 `defaults.ini`（或 `config.json` / `config.toml`）
- **方式 B**：配置硬编码为模块内部常量（适合极简模块）
- 运行时从模块内部路径加载（`Path(__file__).parent / "defaults.ini"` 等）
- **禁止**读环境变量
- 凭据 / 密钥字段全部 `CHANGE_ME` / `<your-credential>` 占位符，运行时由调用方覆盖

### 7. Manual 验证脚本 + 七类扫描兜底
- 写 `verify.{py,js,ts,go}` 手动验证脚本（按用户项目语言）：
  - 入口：**禁止** `sys.argv` / `process.argv` 传参（违反 KISS）；硬编码 mock 数据
  - 至少 3 组样本：import 自测 / 配置加载自测 / 核心方法自测
  - 用 `assert` / `chai.assert` / `testing.T` 等做自检
- 最终零业务字段审计（按用户语言）：
  - 业务字眼扫描：项目名 / 业务字段 / 项目特定路径 / 具体厂商 → 必须空
  - 环境变量扫描：`os.getenv` / `os.environ` / `process.env` / `${ENV}` → 必须空
  - 具体路径扫描：`C:\` / `D:\` / `/Users/` / `/home/xxx/` → 必须空
  - 真实凭据扫描：`sk-` / `AKIA` / `Bearer [A-Za-z0-9]{20}` → 必须空
  - **外部参考字眼扫描**：参考 / 引用 / 借鉴 / 致谢 / 类似 / based on → 必须空
  - **其他项目路径扫描**：`<project_root>` / `<your_app>` / `<repo_root>` → 必须空
  - 一键兜底：`bash scripts/check-min-module.sh {module_dir}/`

---

## 何时中断并询问用户

- 候选模块包含大量业务逻辑，无法剥离到零业务标准
- 用户要求引入框架级依赖（如 flask、django、fastapi）—— 违反外部依赖边界
- 模块边界模糊（"这个到底是技术能力还是业务逻辑？"）
- 候选模块已存在等价实现（复用优先检查）
- 配置项必须使用真实凭据（违反 `CHANGE_ME` 占位符纪律）

---

## 反模式（禁止）

### ⛔ §0 绝对零业务相关（v2.28.1+ 新增）

- ❌ 模块含具体业务名、业务字段名、具体业务路径、具体厂商域名
- ❌ 模块内部注释 / docstring 出现项目特定字眼
- ❌ 模块任何产物（README / verify / 错误消息 / 日志字段名）含外部参考字眼（"参考 xxx" / "引用 xxx" / "详见 xxx" / "类似 xxx" / `based on xxx` / `inspired by xxx`）
- ❌ 模块任何产物含其他项目路径字面值（即使抽象路径 `<project_root>/...` 也禁止）
- ❌ import 业务模块（`common.*` / `apps.*` / `flask.*` / 本项目 `config/*`）
- ❌ 依赖整个框架（ORM 之外的 Flask / Django / FastAPI 等）
- ❌ 读环境变量（任何形式）—— 违反 v2.25.0+ 全栈禁令
- ❌ 配置文件含真实凭据（必须 `CHANGE_ME` / `<your-credential>` 占位符）
- ❌ 配置项含具体业务字段（如 `order_status` / `payment_token`）
- ❌ 模块文件名含业务前缀（`payment_utils.py`）—— 必须通用名（`validators.py` / `retry.py` / `loggings.py`）

### ⚙️ 实现细节相关

- ❌ 无日志系统（调用方无法观测模块行为）
- ❌ 无异常体系（所有错误都抛裸异常）
- ❌ 产物散落工作区不按 `{module_name}/` 归档
- ❌ 无验证脚本
- ❌ 验证脚本用命令行参数传参（违反 KISS，必须硬编码 mock 数据）
- ❌ **模块内置日志默认走 `colorlog.ColoredFormatter(...)` / `winston.format.colorize()` / `logrus ForceColors: true` 等开颜色**——违反 `日志规范.md §7.6`（v2.29.2+）；必须硬编码默认走 plain formatter，调用方显式传 `console_color=True` 才开
- ❌ **模块内置日志默认 `DEBUG` 级别**——违反 `日志规范.md §7.6` 默认 INFO
- ❌ **`logging.StreamHandler()` 不传 `stream=sys.stdout`**（默认 stderr）——违反 `日志规范.md §7.5.2` PyCharm 染红
- ❌ **CONSOLE_FORMAT 含 `%(levelname)-Ns` 宽度填充**（输出 `[INFO   ]`）——违反 `日志规范.md §7.5.1`

---

## 完成后自检清单

### §0 绝对零业务审计（v2.28.1+ 新增 · 不通过则不叫 min-module）

- [ ] **业务字眼扫描**：项目名 / 业务字段 / 状态机 / 厂商 → 必须空
- [ ] **路径字面值扫描**：`C:\` / `D:\` / `/Users/` / `/home/xxx/` → 必须空
- [ ] **环境变量读取扫描**：`os.getenv` / `os.environ` / `process.env` / `${ENV}` → 必须空
- [ ] **真实凭据扫描**：`sk-` / `AKIA` / `Bearer [A-Za-z0-9]{20}` → 必须空
- [ ] **外部参考字眼扫描**：参考 / 引用 / 借鉴 / 致谢 / 类似 / 致敬 / `based on` / `inspired by` / `see also` → 必须空
- [ ] **其他项目路径扫描**：`<project_root>` / `<your_app>` / `<repo_root>` / `<your_workspace>` → 必须空
- [ ] **模块名 / 文件名无业务前缀**（`payment_xxx.py` ❌ / `validators.py` ✅）
- [ ] **docstring / 错误消息字符串无业务字段名**
- [ ] **README / verify 脚本无具体项目部署路径**
- [ ] **一键兜底**：`bash scripts/check-min-module.sh {module_dir}/` 退出码 0

### ⚙️ 通用规则自检

- [ ] 模块候选清单已产出（技术能力 vs 业务逻辑分类）
- [ ] 外部依赖边界确认（仅标准库 + 直接相关第三方库）
- [ ] 自包含日志系统已实现（日志工厂 + **v2.29.2+ 硬编码默认 = INFO+stdout+紧凑级别+plain Formatter（无颜色）+ 必含字段**；调用方零配置即合规；详见 `日志规范.md §7.5 §7.6 §7.6.4`）
- [ ] 自包含异常体系已实现（基类 + ≥3 子类 + `error_code` 字段）
- [ ] 配置自包含已实现（`defaults.ini` 或硬编码常量，运行时从模块内部路径加载）
- [ ] 验证脚本可独立运行（硬编码 mock 数据 + `assert` 自检）
- [ ] 模块可被 `from {module_name} import ...` / `require('{module_name}')` 正常调用
- [ ] 产物归档到 `{module_name}/` 目录
- [ ] README 含 ≥2 个 import 使用示例（不出现具体项目部署路径）

---

## 与 sdk-design 的边界精确对比（v2.28.3+ 新增）

> **何时升级到 SDK**：当一个 min-module 开始封装**特定领域能力**（业务 API / 第三方服务 / 协议 / 数据库驱动）时，不是再加 min-module，而是用 `mcpowers-sdk-design` 升级产出 SDK。

| 维度 | min-module（自身） | sdk-design（升级产物） |
|:-----|:-------------------|:-----------------------|
| **定位** | 纯技术能力（HTTP 客户端、加解密、重试器、日志框架、连接池等） | 特定领域能力封装（业务 API / 第三方服务 / 协议 / 数据库驱动） |
| **自包含四件套** | ✅ 自己实现 | ✅ 自己实现（**不继承** min-module） |
| **绝对零业务审计**（§0） | ✅ 必须 | ✅ 必须 |
| **禁读环境变量** | ✅ 必须 | ✅ 必须 |
| **defaults.ini + 覆盖合并** | ❌（可选硬编码常量） | ✅（必含，凭据全 `CHANGE_ME`） |
| **构造时健康检查硬拒绝** | ❌ | ✅ |
| **上游错误 vs 客户端错误分层重试** | ❌ | ✅（上游指数退避；客户端立即抛，**不重试**） |
| **资源泄漏防护**（`with` 块 / `close()`） | ❌（按需） | ✅（必含） |
| **可依赖已存在的 min-module** | ❌（自身就是） | ✅（`from x import ...` 公开 API 调用） |

**详细 12 维度差异矩阵 + 复用机制（允许 import 公开 API、禁止 源码拷贝 / `_private_func` / `cp -r` 整个目录）** 详见 [`mcpowers-sdk-design/SKILL.md`](mcpowers-sdk-design/SKILL.md) §「与 min-module 的边界精确对比」。本段不复制内容（CLAUDE.md 单一权威源门禁）。

---

## 关联技能

- **上游**：`mcpowers-brainstorm`（边界不清时澄清）
- **下游**：`mcpowers-plan`（任务 > 3 步拆解）/ `mcpowers-tdd`（补 verify 测试）/ `mcpowers-code-review`（封装自审）/ `mcpowers-git-commit`（提交）
- **同级（易混淆）**：
  - `mcpowers-refactor` —— 原地改结构，行为不变，产物留原项目；本技能产出**跨项目独立可搬运资产**
  - `mcpowers-extract` —— 从已有项目抽离可复用资产；本技能专注**最小模块的最终形态标准**（如何自包含、零业务字眼、配置如何自包含）
  - `mcpowers-sdk-design` —— 在最小模块基础上加一层**领域能力封装**；SDK 本身也必须遵守最小模块基线
  - `mcpowers-init` —— 从零搭项目骨架；本技能从已有技术能力沉淀
