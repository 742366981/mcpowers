---
name: mcpowers-min-module
description: "最小通用模块化 / 零业务自包含工具 / 复制即用跨项目零成本 / 自带日志异常配置 → 触发本技能。口语：做成最小模块、通用化工具、抽成独立模块、可import的模块、零业务字眼、无项目名/无业务字段、通用utils/日志/校验/重试、自包含模块。中英：min-module,standalone module,reusable module,self-contained,zero business logic,cross-project。边界：封装特定领域能力→mcpowers-sdk-design；原地改结构→mcpowers-refactor；从零搭骨架→mcpowers-init；从已有项目抽离可复用资产→mcpowers-extract。流程：识别技术能力→剥离业务→自包含四件套设计→配置自包含→自带日志异常→验证脚本→零业务字段审计。"
---

# mcpowers-min-module（最小通用模块化）

> **核心**：把**通用技术能力**沉淀为「任何项目复制即用、零业务字眼、自包含日志/异常/配置/验证脚本」的最小工具模块。
> 不是 `mcpowers-refactor`（原地改结构），不是 `mcpowers-extract`（从已有项目抽离）——本技能专注**最小模块的最终形态标准**：产物可立即被任意项目 `cp -r` 复用，无需二次抽象。

> **语言中立**：本技能默认示例是 Python（mcpowers 现有规范倾向），但"自包含四件套 / 零业务字眼 / 禁读环境变量"等机制对任何语言都适用；用户项目用什么语言，按该语言的对应形式实现即可。

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

1. **零业务字眼**——代码 / 注释 / docstring / 配置示例 / README 禁止出现具体业务名、字段名、项目名、厂商名
2. **自包含**——日志 / 异常 / 配置 / 验证脚本必须全部在模块内部，不引用外部业务模块
3. **外部依赖边界**——仅该语言标准库 + 直接相关第三方库；禁止拖家带口引入整个框架
4. **配置自包含**——如需配置，写 `defaults.ini`（或 `config.json` / `config.toml`）作为模块一部分，运行时从模块内部路径加载（`Path(__file__).parent / "defaults.ini"` 等）
5. **禁读环境变量**——所有 `os.getenv` / `os.environ` / `process.env` / `${ENV}` 全部禁止
6. **凭据全占位**——任何 key/secret/token 字段在 `defaults.ini` 里都是 `CHANGE_ME` / `<your-credential>` 占位符
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
1. **零业务字眼**——最严的一条，违反则 CI 红 X
2. **自包含**——日志 / 异常 / 配置 / 验证脚本必须全部在模块内部
3. **外部依赖边界**——仅该语言标准库 + 直接相关第三方库
4. **配置自包含**——写 `defaults.ini`（或对应格式）作为模块一部分
5. **禁读环境变量**——所有 `os.getenv` / `os.environ` / `process.env` 全部禁止

---

## 触发即执行（7 步）

### 1. 识别模块边界（技术能力 vs 业务逻辑）
- 扫描目标代码，识别「技术能力层」（可跨项目复用）vs「业务逻辑层」（与当前项目强绑定）
- 典型技术能力：HTTP 请求构造、加解密、签名算法、数据校验、重试逻辑、日志封装、配置加载
- 典型业务逻辑：具体业务 CRUD、页面渲染、具体业务字段处理
- 产出：**模块候选清单**（每项标注：技术能力类型 / 依赖分析 / 是否达零业务标准）

### 2. 零业务字眼审计
对每个候选模块，逐文件 grep 检查：
- 用 `rg / grep` 扫描业务字眼（项目名 / 业务字段 / 项目特定路径 / 具体厂商）
- 发现任何业务字眼 → 替换为抽象占位符（`<your_module_name>` / `{module_name}`）或参数化
- 项目特有路径 → 改为相对路径（模块内部路径加载）或从配置读取
- 业务字段名 → 改为通用字段名或泛型参数

### 3. 外部依赖边界确认
- 列出模块内所有 `import` / `require` / `use` 语句
- 逐条判断：标准库 ✅ / 直接相关第三方库 ✅ / 业务模块 ❌
- 如发现禁止的 import → 替换为标准库等价实现或参数注入
- 确认**没有**任何形式的环境变量读取

### 4. 自包含日志系统设计
- 模块内部实现轻量日志类（**禁止引用外部业务日志模块**）
- 日志默认行为：DEBUG 级别 + stderr 输出 + 毫秒时间戳 + 8 字符等宽级别名
- 首次调用日志工厂时自动安装默认 Handler，调用方零配置
- 幂等安装：多次调用不重复装 Handler
- 不污染 root logger：`propagate=False`
- 必含字段：`ts` / `level` / `logger_name` / `msg`；可选上下文：`trace_id` / `request_id`

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

### 7. Manual 验证脚本 + 零业务字段最终审计
- 写 `verify.{py,js,ts,go}` 手动验证脚本（按用户项目语言）：
  - 入口：**禁止** `sys.argv` / `process.argv` 传参（违反 KISS）；硬编码 mock 数据
  - 至少 3 组样本：import 自测 / 配置加载自测 / 核心方法自测
  - 用 `assert` / `chai.assert` / `testing.T` 等做自检
- 最终零业务字段审计（按用户语言）：
  - 业务字眼扫描：项目名 / 业务字段 / 项目特定路径 / 具体厂商 → 必须空
  - 环境变量扫描：`os.getenv` / `os.environ` / `process.env` / `${ENV}` → 必须空
  - 具体路径扫描：`C:\` / `D:\` / `/Users/` / `/home/xxx/` → 必须空
  - 真实凭据扫描：`sk-` / `AKIA` / `Bearer [A-Za-z0-9]{20}` → 必须空

---

## 何时中断并询问用户

- 候选模块包含大量业务逻辑，无法剥离到零业务标准
- 用户要求引入框架级依赖（如 flask、django、fastapi）—— 违反外部依赖边界
- 模块边界模糊（"这个到底是技术能力还是业务逻辑？"）
- 候选模块已存在等价实现（复用优先检查）
- 配置项必须使用真实凭据（违反 `CHANGE_ME` 占位符纪律）

---

## 反模式（禁止）

- ❌ 模块包含具体项目名、业务字段名、具体业务路径、具体厂商域名
- ❌ 模块内部注释 / docstring 出现项目特定字眼（违反零业务字眼）
- ❌ import 业务模块（`common.*` / `apps.*` / `flask.*` / 本项目 `config/*`）
- ❌ 依赖整个框架（ORM 之外的 Flask / Django / FastAPI 等）
- ❌ 读环境变量（任何形式）—— 违反 v2.25.0+ 全栈禁令
- ❌ 配置文件含真实凭据（必须 `CHANGE_ME` / `<your-credential>` 占位符）
- ❌ 无日志系统（调用方无法观测模块行为）
- ❌ 无异常体系（所有错误都抛裸异常）
- ❌ 配置项含具体业务字段（如 `order_status` / `payment_token`）
- ❌ 模块文件名含业务前缀（`payment_utils.py`）—— 必须通用名（`validators.py` / `retry.py` / `loggings.py`）
- ❌ 产物散落工作区不按 `{module_name}/` 归档
- ❌ 无验证脚本
- ❌ 验证脚本用命令行参数传参（违反 KISS，必须硬编码 mock 数据）

---

## 完成后自检清单

- [ ] 模块候选清单已产出（技术能力 vs 业务逻辑分类）
- [ ] 零业务字眼审计通过（grep 无业务字眼命中）
- [ ] 零具体路径审计通过（grep 无 `C:\` / `D:\` / `/Users/` / `/home/xxx/` 命中）
- [ ] 零环境变量审计通过（grep 无环境变量读取命中）
- [ ] 零真实凭据审计通过（grep 无 `sk-` / `AKIA` / `Bearer [A-Za-z0-9]{20}` 命中）
- [ ] 外部依赖边界确认（仅标准库 + 直接相关第三方库）
- [ ] 自包含日志系统已实现（日志工厂 + 默认 DEBUG+stderr + 必含字段）
- [ ] 自包含异常体系已实现（基类 + ≥3 子类 + `error_code` 字段）
- [ ] 配置自包含已实现（`defaults.ini` 或硬编码常量，运行时从模块内部路径加载）
- [ ] 验证脚本可独立运行（硬编码 mock 数据 + `assert` 自检）
- [ ] 模块可被 `from {module_name} import ...` / `require('{module_name}')` 正常调用
- [ ] 产物归档到 `{module_name}/` 目录
- [ ] README 含 ≥2 个 import 使用示例（不出现具体项目部署路径）

---

## 关联技能

- **上游**：`mcpowers-brainstorm`（边界不清时澄清）
- **下游**：`mcpowers-plan`（任务 > 3 步拆解）/ `mcpowers-tdd`（补 verify 测试）/ `mcpowers-code-review`（封装自审）/ `mcpowers-git-commit`（提交）
- **同级（易混淆）**：
  - `mcpowers-refactor` —— 原地改结构，行为不变，产物留原项目；本技能产出**跨项目独立可搬运资产**
  - `mcpowers-extract` —— 从已有项目抽离可复用资产；本技能专注**最小模块的最终形态标准**（如何自包含、零业务字眼、配置如何自包含）
  - `mcpowers-sdk-design` —— 在最小模块基础上加一层**领域能力封装**；SDK 本身也必须遵守最小模块基线
  - `mcpowers-init` —— 从零搭项目骨架；本技能从已有技术能力沉淀
