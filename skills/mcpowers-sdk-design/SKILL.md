---
name: mcpowers-sdk-design
description: "SDK设计 / 封装领域能力 / 绝对零业务 / 无任何外部参考 / 通讯层中立 / 默认健康检查硬拒绝 / 上游错误重试vs客户端错误分离 → 触发本技能。口语：做个SDK、写个接口封装、封装第三方接口、做客户端库、SDK怎么设计、客户端SDK、领域SDK、可分发包。中英：SDK design,API wrapper,client library,absolute zero business,no external reference,domain SDK,health check,retry on upstream error。边界：纯工具函数零业务→mcpowers-min-module；从零搭骨架→mcpowers-init；从已有项目抽离可复用资产→mcpowers-extract；已有项目加功能→mcpowers-feat。流程：确认领域→§0零业务审计→外部依赖分析→SDK形态→defaults.ini+覆盖→健康检查→异常分层→资源泄漏防护→七类扫描兜底。"
---

# mcpowers-sdk-design（SDK 设计）

> **核心**：把**某个特定领域能力**封装成可独立分发、可 `import`、可调用的 SDK。SDK 本身必须遵守最小模块基线（绝对零业务 / 自包含 / 可独立 import），同时多一层「领域能力封装 + 健壮性纪律」。
> 不是 `mcpowers-min-module`（纯技术能力，无特定领域），不是 `mcpowers-feat`（已存在项目加功能）——本技能专注**一个 SDK 从零到可交付**的工程标准。

> **通讯层中立**：SDK 不绑 HTTP / gRPC / WebSocket / 文件 IO / CLI 包装等任何具体通道。"调用" / "响应" / "上游错误" / "客户端错误" 是抽象口径；具体技术选型由用户场景决定。

> **绝对零业务（v2.28.1+ 定义性铁律）**：本技能所有规则、示例、术语必须围绕**该 SDK 自身的能力**展开。SDK 代码 / 注释 / docstring / 配置示例 / README / 验证脚本 / 错误消息字符串 / 日志字段名 / SDK 名 / 文件名——任何产出物都**禁止**含具体业务名、字段名、项目名、厂商名、具体路径、外部参考字眼。SDK 只描述自己封装什么领域能力、怎么做，不指代任何外部对象。

---

## §0 绝对零业务审计（v2.28.1+ 定义性铁律）

**任何产物在自称为 SDK 之前必须通过 §0 审计；任何一项命中即不通过——不叫 SDK，只是普通库。**

### §0.1 禁止的字眼（不限于）

| 类别 | 禁止示例 | 允许替代 |
|:-----|:---------|:---------|
| **具体业务名** | 项目名 `bangkokair` / 业务字段 `order_status` / 状态机 `payment_pending` / 厂商名 `stripe` | 抽象占位符 `<your_sdk_name>` / `{sdk_name}` / `CHANGE_ME` |
| **具体路径字面值** | `C:\projects\xxx` / `D:\workspace\yyy` / `/Users/alice/foo` / `/home/bob/bar` | 跨平台抽象 `pathlib.Path.home() / ".cache" / "{SDK 名称}"` |
| **环境变量读取** | `os.getenv("API_KEY")` / `os.environ["TOKEN"]` / `process.env.SECRET` / `${ENV_VAR}` | 配置文件 + 运行时覆盖 dict / 命令行参数 |
| **真实凭据** | `sk-xxx...` / `AKIA...` / `Bearer eyJhbGc...` | `CHANGE_ME` / `<your-credential>` 占位符 |
| **外部参考字眼** | "参考 XXX 文档" / "引用 XXX 规范" / "详见 XXX" / "参见 XXX" / "借鉴 XXX" / "基于 XXX 改进" / "类似 XXX 但更..." / "致敬 XXX" / "致谢 XXX" / `based on xxx` / `inspired by xxx` / `reference: xxx` / `see also xxx` | 只描述该 SDK 自身的技术决策（"按 X 协议"、"遵循 RFC 7231"等通用标准是允许的） |
| **其他项目路径** | `<project_root>/xxx` / `<your_app>/yyy` / `<repo_root>/zzz` / `<app_root>/...`（即使抽象路径也禁止） | 跨平台抽象 `Path(__file__).parent / "defaults.ini"` / `Path.home() / ".cache" / "{SDK 名称}"` |
| **SDK 名 / 文件名业务前缀** | `payment_sdk.py` / `bangkokair_client.py` / `order_api.py` | 通用名 `client.py` / `config.py` / `exceptions.py` / `<抽象领域>_sdk.py` |

### §0.2 例外（允许的字眼）

| 类别 | 允许示例 | 理由 |
|:-----|:---------|:-----|
| 通用技术术语 | `HTTP` / `OAuth` / `SQL` / `JSON` / `trace_id` / `request_id` / `Order`（领域模型通用）/ `User`（通用概念） | 跨语言跨项目通用 |
| 协议 / RFC 引用 | "按 RFC 7231" / "遵循 OAuth 2.0" / "兼容 HTTP/2" | 公开标准，非具体项目 |
| 抽象占位符 | `<your_sdk_name>` / `{sdk_name}` / `CHANGE_ME` / `<sdk_root>` / `<your-credential>` | SDK 本身通用 |
| 跨平台抽象路径 | `pathlib.Path.home() / ".cache" / "{SDK 名称}"` / `Path(__file__).parent` | 不绑定具体机器 |
| 抽象领域词（无业务绑定） | `<抽象能力>_sdk.py`（如 `payment_sdk.py` 仍是业务前缀；`billing_abstract_sdk.py` 是抽象） | 只在描述通用能力时允许 |

### §0.3 审计命令（任何产物自称为 SDK 之前必跑）

```bash
# 1. 业务字眼扫描
rg -i "${项目名}|${业务字段}|${状态机}|${厂商}" {sdk_dir}/

# 2. 具体路径扫描
rg "C:\\\\|D:\\\\|/Users/|/home/[^/]+/" {sdk_dir}/

# 3. 环境变量读取扫描
rg "os\.getenv|os\.environ|process\.env|\${ENV}" {sdk_dir}/

# 4. 真实凭据扫描
rg "sk-[A-Za-z0-9]{20}|AKIA[A-Z0-9]{16}|Bearer [A-Za-z0-9]{20}" {sdk_dir}/

# 5. 外部参考字眼扫描
rg -in "参考|引用|参照|借鉴|致谢|致敬|改进自|参考:|reference:|see also|详见|参见|类似|based on|inspired by" {sdk_dir}/

# 6. 其他项目路径扫描（即使抽象路径也禁止）
rg "<project|<your.*project|<your_workspace|<repo_root|<app_root" {sdk_dir}/

# 7. 一键脚本：bash scripts/check-min-module.sh {sdk_dir}/
```

**任一项命中 → §0 审计不通过 → 不是 SDK**，必须替换或移除后重跑。

---

## 与 min-module 的边界精确对比（v2.28.3+ 新增）

> **新读者必读**：先把 SDK 和 min-module 的差异锚定，再读后续规则。
> SKILL.md 内自带闭环，不依赖 CLAUDE.md / README.md 入口说明。

### 一句话定位

| 技能 | 一句话 |
|:-----|:-------|
| `mcpowers-min-module` | 把**纯技术能力**沉淀为「跨项目可搬运、自包含、绝对零业务」的最小工具模块（`Retry` / `Loggings` / `Validators` 等） |
| `mcpowers-sdk-design` | 在最小模块基础上**叠加领域能力封装 + 健壮性纪律**，产出可独立分发的 SDK |

### 详细差异矩阵

| 维度 | min-module | sdk-design（升级点） |
|:-----|:-----------|:---------------------|
| **定位** | 纯技术能力（HTTP 客户端、加解密、重试器、日志框架、连接池等） | 特定领域能力封装（业务 API / 第三方服务 / 协议封装 / 数据库驱动） |
| **自包含四件套**（日志 / 异常 / 配置 / 验证） | ✅ 必须（自己实现） | ✅ 必须（**自己实现，不继承自 min-module**） |
| **绝对零业务审计**（§0） | ✅ 必须 | ✅ 必须 |
| **可独立 import / 复制即用** | ✅ 必须 | ✅ 必须 |
| **禁读环境变量** | ✅ 必须 | ✅ 必须 |
| **可依赖已存在的 min-module** | ❌（自身就是 min-module） | ✅（`from min_module import ...` 公开 API 调用，详见下表） |
| **defaults.ini + 覆盖合并** | ❌（可选硬编码常量） | ✅（必含，凭据字段全 `CHANGE_ME`） |
| **构造时健康检查硬拒绝** | ❌ | ✅（不懒加载，`ConfigError` 立即抛） |
| **上游错误 vs 客户端错误分层重试** | ❌ | ✅（上游指数退避；客户端立即抛，**不重试**） |
| **资源泄漏防护**（`with` 块 / `close()`） | ❌（按需） | ✅（session / connection / handle 全覆盖） |
| **双模式互斥**（sync/async） | ❌ | ✅（强烈建议；简单 SDK 可不启用） |
| **通讯层中立** | ⚠️ 仅含 IO 时要求 | ✅（每个 SDK 必选 HTTP / gRPC / WS / CLI / DB / 第三方库） |
| **领域能力清单产出** | ❌（纯技术能力） | ✅（必产出：能力 / 通讯层 / 输入 / 输出 / 错误模式） |
| **典型产物举例** | `loggings.py` / `validators.py` / `retry.py` / `connection_pool.py` | `<抽象领域>_sdk/` / `client.py` + `config.py` + `exceptions.py` + `verify.py` |

### 复用机制（SDK 如何使用 min-module）

SDK 与 min-module 的关系 = **「第三方库调用」**，不是"源码集成"。

| 行为 | 是否允许 | 说明 |
|:-----|:---------|:-----|
| `from min_module import Retry, Loggings; Retry().execute(...)` | ✅ | Python 标准 import + 公开 API 调用 |
| SDK 自己重写四件套（不抄 min-module） | ✅ | 因为 SDK 是独立分发包，不能假设调用方已装 min-module |
| 把 min-module 的 `def _internal_helper` 拷贝进 SDK | ❌ | 违反 DRY + 失去独立性 + 同步维护成本 |
| `from min_module import _private_func` | ❌ | 违反单下划线私有名约定 |
| 把 min-module 整个目录 `cp -r` 进 SDK | ❌ | 违反"自包含"原则 + 跨项目搬运时 SDK 会带一大堆无关文件 |

**为什么 SDK 必须自己重写四件套？**
- SDK 是独立可分发包，不能假设调用方已装 min-module
- 调用方只装 SDK 不装 min-module 时，SDK 必须能跑
- 这与"SDK 可以 import min-module"**不矛盾**——两者并存的两种情况：
  - (a) SDK 自己实现四件套 + `import min_module` 的特定公开 API（如 `Retry`）
  - (b) SDK 完全自包含（不 import 任何 min-module）——`from min_module import ...` 一句都不写

**复用判断决策**（SDK 端 Step 3「混合复用判断」已定义，此处不重复）：
- 用户声明「我用了 X」 → 直接 `import`
- AI 扫描命中候选 → 一次 `AskUserQuestion` 集中询问
- 都没命中 → SDK 自包含（不询问）

---

## 核心定义

| 要求 | 说明 |
|:-----|:-----|
| **领域能力封装** | SDK 绑定一个明确的外部能力（HTTP API / gRPC / 数据库 / 第三方库 / 文件协议 / CLI 工具），所有公开方法都是该能力的薄封装 |
| **必须遵守最小模块基线** | 零业务字眼 / 自包含 / 可独立 import / 跨项目可搬运 |
| **可依赖已存在的最小模块** | 用户已声明「我项目下有 X」或扫描命中 → 直接 `from X import ...` 复用；否则 SDK 自包含 |
| **禁依赖业务项目层** | 绝对禁止 import 本项目 `utils/common/config/路由/服务层` 任何业务模块 |
| **defaults.ini + 覆盖合并** | SDK 自带 `defaults.ini`，所有凭据字段为 `CHANGE_ME`；调用方通过 `overrides` dict 运行时覆盖 |
| **健康检查硬拒绝** | 构造时调 `config.validate()`，发现 `CHANGE_ME` 必填字段未覆盖 → 直接抛 `ConfigError`，禁用懒加载 |
| **上游错误 vs 客户端错误分离** | 上游错误（5xx / 网络断开 / 超时）→ 指数退避重试；客户端错误（4xx / 参数非法 / 凭据失效）→ 立即抛业务异常，**不重试** |
| **资源泄漏防护** | session / connection / file handle / lock 全部用 `with` 块或 `try/finally` 管理；提供 `close()` 入口 |
| **通讯层中立** | 不预设 HTTP / gRPC / WebSocket / 文件 IO；`requests` / `httpx` / `grpc` / `websocket` / `subprocess` / 自实现协议 都可 |

---

## 通用规则（不绑通讯层）

### ⛔ 铁律（不满足则不叫 SDK）

1. **§0 绝对零业务审计通过**——按 §0.3 七类扫描命令逐项跑通，任何命中即不通过
2. **必须遵守最小模块基线**——SDK = 升级版最小模块 + 领域能力封装
   - **混合复用判断**：
     - (a) 用户**主动声明**「我用了 X」「项目下有 Y」→ 记录复用清单，不再询问
     - (b) 未声明 → AI 做一次轻量项目扫描（< 5 秒），扫到候选**集中询问一次**（一次性列出所有候选 + 对应能力，不重复问）
     - (c) 都没命中 → SDK 自包含所有能力 = 自当最小模块（**不询问**）
   - **禁止每个能力重复询问**用户
3. **可独立 import + 跨项目可搬运**——任意项目 `cp -r {sdk_name}/` 即可使用
4. **外部依赖边界**：仅标准库 + 直接相关第三方库（按通讯层选型：HTTP 用 `requests`/`httpx`；gRPC 用 `grpc`；CLI 用 `subprocess` 等）
5. **defaults.ini 凭据全占位 + 禁读环境变量**—— 全部 `CHANGE_ME` 占位符；禁 `os.getenv` / `os.environ` / `process.env` / `${ENV}`（v2.25.0+ 全栈最高铁律）
6. **健康检查硬拒绝**—— 构造时调 `config.validate()`，发现必填字段未覆盖 → 立即抛 `ConfigError`，不懒加载

### ⚙️ 实现细节（满足铁律后的具体做法）

7. **自包含日志**（同 min-module 铁律）—— `get_sdk_logger(name)` 工厂
8. **自包含异常体系**—— `SDKError` 基类 + `ConfigError` / `UpstreamError` / `ClientError` / `AuthError` / `RetryExhaustedError` / `HealthCheckError` / `ModeConflictError`
9. **双模式 API 互斥**（强烈建议；简单 SDK 可不启用）—— `mode="sync"|"async"` 二选一，跨模式调用同一实例 → `ModeConflictError`
10. **上游错误自动重试**—— 上游错误（5xx / 网络断开 / 超时）→ 指数退避重试，超过 max_attempts 抛 `RetryExhaustedError`
11. **客户端错误立即抛异常**—— 客户端错误（4xx / 参数非法 / 凭据失效）→ 立即抛对应业务异常，**不重试**
12. **连接池路径锚定**—— `pathlib.Path.home() / ".cache" / "{SDK 名称}"`，跨平台可搬运
13. **常驻进程轮次不重叠**—— 同一 SDK 实例不并发跑两次长任务；提供 `is_running` 标记
14. **资源泄漏防护**—— session / connection / file handle / lock 用 `with` 块或 `try/finally` 管理

---

## 编排

本技能按需调用以下方法层技能 + 规范：

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-brainstorm` | 方法 | 领域边界不清晰 | 中断并回问用户 |
| 2 | **混合复用判断**（用 `Glob` 扫 + `Grep` 特征） | 子步骤 | (a) 命中用户声明 → 记录清单；(b) 扫描到候选 → 一次 `AskUserQuestion` 集中列出；(c) 两者皆无 → 自包含 | 询问后用户选「不复用」→ SDK 自包含 |
| 3 | `mcpowers-plan` | 方法 | 任务 > 3 步 | 拆解成 2-5 分钟可验证小任务 |
| 4 | `mcpowers-tdd` | 方法 | 核心 API 逻辑无验证保护 | 补最小 verify 测试 |
| 5 | `mcpowers-code-review` | 方法 | 封装完成 | Critical 必须修复 |
| 6 | `mcpowers-git-commit` | Git | 收尾提交 | — |

**铁律**：
1. **§0 绝对零业务审计通过**——不通过则不叫 SDK（参见 §0）
2. **必须遵守最小模块基线**——把 SDK 当作「升级版最小模块」来设计
3. **健康检查硬拒绝**——决不允许 SDK 拿默认值运行时才发现 `CHANGE_ME`，必须构造时立即抛错
4. **上游错误 vs 客户端错误严格分离**——客户端错误绝不能混入重试逻辑
5. **defaults.ini 凭据全占位**——任何 key/secret/token 字段在 `defaults.ini` 里都是 `CHANGE_ME`
6. **禁读环境变量**——同 min-module 铁律
7. **混合复用判断**——不要每个能力重复询问用户，按铁律 2 走
8. **通讯层中立**——不预设具体通讯技术栈；用"上游错误 / 客户端错误"抽象口径

---

## 触发即执行（8 步）

### 1. 确认领域能力边界
- 用户说"封装 XX" → 识别该能力的调用形态（HTTP REST / gRPC / WebSocket / 文件 IO / CLI 包装 / 第三方库 / 数据库）
- 典型能力：auth / 列表查询 / 详情查询 / 提交 / 异步通知 / webhook / 流式订阅
- 产出：**领域能力清单**（每个能力含：调用方式 / 输入参数 / 返回结构 / 错误模式）

### 2. §0 绝对零业务审计（强制首步）
按 §0.3 七类扫描命令逐项跑通（业务字眼 / 路径字面值 / 环境变量读取 / 真实凭据 / 外部参考字眼 / 其他项目路径 / SDK 名业务前缀）。任一项命中：
- 业务字眼 → 替换为抽象占位符（`<your_sdk_name>` / `{sdk_name}`）或参数化
- 路径字面值 → 改为相对路径（SDK 内部路径加载）或从配置读取
- 业务字段名 → 改为通用字段名或泛型参数
- 参考字眼 → 删除或改为该 SDK 自身的技术决策描述

### 3. 混合复用判断（混合方案）
- **优先级 1**：解析用户输入是否含「我用了 X」「项目下有 Y」等声明字样
  - 命中 → 记录「复用清单：X→IO, Y→日志, Z→连接池」，进入 Step 4 按清单 `import`
- **优先级 2**：未声明 → AI 做一次轻量扫描（< 5 秒）
  - 用 `Glob` 扫 `*_client*` / `*loggings*` / `*pool*` / `*retry*` / `*validators*` 等候选
  - 用 `Grep` 扫 `def get\|def post\|def request\|class.*Client\|class.*Pool` 等特征
- **优先级 3**：判定结果
  - 扫到 1+ 候选 → **集中询问一次**（用 `AskUserQuestion` 一次性列出所有候选 + 对应能力）
  - 没扫到任何候选 → **不询问**，直接进入 Step 4，SDK 自包含 = 自当最小模块

### 4. 外部依赖边界确认
- 列出 SDK 内所有 `import` 语句
- 逐条判断：标准库 ✅ / 直接相关第三方库 ✅ / 业务模块 ❌
- 第三方库选择服从通讯层选型：
  - HTTP REST → `requests` / `httpx` / `urllib3`
  - gRPC → `grpc` / `grpcio`
  - WebSocket → `websockets` / `websocket-client`
  - CLI 包装 → `subprocess` (标准库)
  - 第三方库 → 该库本身
  - 数据库 → `sqlalchemy` / `pymongo` / 对应驱动
- 如发现禁止的 import → 替换为标准库等价实现或参数注入
- 确认**没有** `os.getenv` / `os.environ` / `process.env` 任何形式的环境变量读取

### 5. defaults.ini + 覆盖合并设计
- 段结构（按通讯层裁剪）：
  - **通用段**：`[log]` / `[retry]` / `[pool]`
  - **HTTP 段**：`[api]` (base_url, timeout_seconds) / `[auth]` (credentials)
  - **gRPC 段**：`[endpoint]` (host, port) / `[auth]` (tokens)
  - **WebSocket 段**：`[endpoint]` (url) / `[heartbeat]` (interval_seconds)
  - **数据库段**：`[connection]` (host, port, db, user)
  - **CLI 段**：`[binary]` (path, args)
- 全部凭据字段 `CHANGE_ME` 占位符
- 运行时从 `Path(__file__).parent / "defaults.ini"` 加载
- 提供合并入口（无论叫 `update` / `merge` / `load_config` 都行）
- 提供 `validate()` 检查必填字段（用 `CHANGE_ME` 判定）

### 6. 健康检查硬拒绝设计
- 构造时调 `config.validate()`（无论是 `__init__` / `__new__` / `build()` 工厂 / `bind()` 注入，都必须"在用户拿到实例前"完成）
- 必填字段未覆盖 → 立即抛 `ConfigError`（或 SDK 自定义的 `HealthCheckError`）
- **不要懒加载**——避免运行时才发现凭据缺失

### 7. 上游错误 vs 客户端错误分层设计
- **上游错误自动重试**（指数退避）：
  - HTTP 5xx / 网络断开 / 超时
  - gRPC UNAVAILABLE / DEADLINE_EXCEEDED
  - WebSocket 断线 / 心跳超时
  - 数据库连接断开
  - CLI 进程崩溃 / 退出码 ≥ 128
- **客户端错误立即抛**（**不重试**）：
  - HTTP 4xx
  - gRPC INVALID_ARGUMENT / UNAUTHENTICATED / PERMISSION_DENIED / NOT_FOUND
  - 参数非法 / 凭据失效 / 资源不存在
- 装饰器模式（@retry_on_upstream_error）或装饰器包装（`with_retry(fn)`）都可

### 8. 资源泄漏防护 + 路径锚定
- session / connection / file handle / lock / subprocess 全部用 `with` 块或 `try/finally` 管理
- 池路径用 `pathlib.Path.home() / ".cache" / "{SDK 名称}"`，跨平台可搬运
- 提供 `close()` 方法
- 可选 `__enter__` / `__exit__` 支持 `with SDK() as sdk:` 语法

### 9. 验证脚本 + 七类扫描兜底
- 写 `verify.py` ≥3 组样本：
  - 健康检查硬拒绝（覆盖 `CHANGE_ME` 字段）→ 实例化成功
  - 上游错误重试（mock 上游错误）→ 触发 N 次重试后抛 `RetryExhaustedError`
  - 客户端错误（mock 客户端错误）→ 立即抛对应业务异常，**不重试**
- 验证脚本不绑 Python 模板——按用户项目语言写（Python 用 `pytest` / 纯 assert；Node 用 `node:test`；Go 用 `go test`）
- 最终零业务字段审计（按用户语言）：
  ```bash
  # Python
  rg -i "from (common|utils|config|apps|flask)" {sdk_dir}/ --type py
  rg -i "os\.getenv|os\.environ|process\.env" {sdk_dir}/ --type py
  rg "C:\\\\|D:\\\\|/Users/|/home/[^/]+/" {sdk_dir}/
  rg -in "参考|引用|类似|based on|inspired by" {sdk_dir}/
  # Node / TS 同理
  ```
- **一键兜底**：`bash scripts/check-min-module.sh {sdk_dir}/` 退出码 0

---

## 何时中断并询问用户

- 领域能力边界模糊（"这个 SDK 到底要封装哪些能力？"）
- 通讯层选型不明（HTTP / gRPC / WebSocket / CLI / 数据库 / 第三方库）—— 必须先问
- 用户要求引入框架级依赖（如 Flask、Django）—— 违反外部依赖边界
- SDK 形态模糊（同步 vs 异步；是否需要双模式互斥）
- 候选最小模块已存在且不可放弃复用（用户明确要求复用）
- 凭据字段必须使用真实值（违反 `CHANGE_ME` 占位符纪律）

---

## 反模式（禁止）

### ⛔ §0 绝对零业务相关（v2.28.1+ 新增）

- ❌ SDK 含具体业务字段、具体业务状态机、具体业务路径、具体厂商域名
- ❌ SDK 内部注释 / docstring / README / verify 脚本出现项目特定字眼
- ❌ SDK 任何产物含外部参考字眼（"参考 xxx" / "引用 xxx" / "详见 xxx" / "类似 xxx" / `based on xxx` / `inspired by xxx`）
- ❌ SDK 任何产物含其他项目路径字面值（即使抽象路径 `<project_root>/...` 也禁止）
- ❌ import 业务模块（`common.*` / `apps.*` / `flask.*` / 本项目 `config/*`）
- ❌ 依赖整个框架（ORM 之外的 Flask / Django / FastAPI 等）
- ❌ 读环境变量（`os.getenv` / `os.environ` / `process.env`）—— 违反 v2.25.0+ 全栈禁令
- ❌ 配置文件含真实凭据（必须 `CHANGE_ME` 占位符）
- ❌ SDK 名 / 文件名含业务前缀（`payment_sdk.py` ❌ / `client.py` ✅）

### ⚙️ 实现细节相关

- ❌ 健康检查懒加载（构造时必须立即拒绝）
- ❌ 客户端错误也走重试（违反"上游错误 vs 客户端错误"分离）
- ❌ 上游错误重试无退避（必须指数退避）
- ❌ 双模式 API 混用同一实例（违反双模式互斥）
- ❌ 资源泄漏（session / connection / file handle 未用 `with` 块）
- ❌ 预设 SDK 必须是 HTTP 形态（违反通讯层中立）
- ❌ 每个能力重复询问用户「复用 X 吗？」——必须按铁律 2 走混合复用判断
- ❌ **SDK 内置日志默认走 `colorlog.ColoredFormatter(...)` / `winston.format.colorize()` / `logrus ForceColors: true` 等开颜色**——违反 `日志规范.md §7.6`（v2.29.2+）；必须硬编码默认走 plain formatter，调用方显式传 `console_color=True` 才开

---

## 完成后自检清单

### §0 绝对零业务审计（v2.28.1+ 新增 · 不通过则不叫 SDK）

- [ ] **业务字眼扫描**：项目名 / 业务字段 / 状态机 / 厂商 → 必须空
- [ ] **路径字面值扫描**：`C:\` / `D:\` / `/Users/` / `/home/xxx/` → 必须空
- [ ] **环境变量读取扫描**：`os.getenv` / `os.environ` / `process.env` / `${ENV}` → 必须空
- [ ] **真实凭据扫描**：`sk-` / `AKIA` / `Bearer [A-Za-z0-9]{20}` → 必须空
- [ ] **外部参考字眼扫描**：参考 / 引用 / 借鉴 / 致谢 / 类似 / 致敬 / `based on` / `inspired by` / `see also` → 必须空
- [ ] **其他项目路径扫描**：`<project_root>` / `<your_app>` / `<repo_root>` / `<your_workspace>` → 必须空
- [ ] **SDK 名 / 文件名无业务前缀**（`payment_sdk.py` ❌ / `client.py` ✅）
- [ ] **docstring / 错误消息字符串无业务字段名**
- [ ] **README / verify 脚本无具体项目部署路径**
- [ ] **一键兜底**：`bash scripts/check-min-module.sh {sdk_dir}/` 退出码 0

### ⚙️ 通用规则自检

- [ ] 领域能力清单已产出（能力 / 通讯层 / 输入 / 输出 / 错误模式）
- [ ] 通讯层选型已确认（HTTP / gRPC / WebSocket / CLI / DB / 第三方库）
- [ ] 混合复用判断已执行（声明优先 / 扫描命中 / 自包含兜底）
- [ ] 外部依赖边界确认（仅标准库 + 直接相关第三方库，按通讯层选型）
- [ ] 自包含日志系统已实现（**v2.29.2+ 硬编码默认 = INFO+stdout+紧凑级别+plain Formatter（无颜色）**；调用方零配置即合规；详见 `日志规范.md §7.6 §7.6.4`；**禁止**模块内置硬编码走 `colorlog.ColoredFormatter` / `winston.format.colorize()` / `logrus ForceColors: true`）
- [ ] 自包含异常体系已实现（≥6 子类 + `error_code`）
- [ ] `defaults.ini` 全部 `CHANGE_ME` 占位符
- [ ] 构造时健康检查硬拒绝（`validate()` 失败立即抛 `ConfigError`）
- [ ] 上游错误指数退避重试已实现
- [ ] 客户端错误立即抛异常已实现（**不重试**）
- [ ] 双模式互斥已实现（如启用 `mode` 参数）
- [ ] 资源泄漏防护已实现（`with` 块 / `close()`）
- [ ] 验证脚本至少 3 组样本（健康检查 / 上游错误重试 / 客户端错误）
- [ ] SDK 可被外部 `import` / `require` 正常调用
- [ ] 产物可被 `cp -r` 复制到任意项目使用
- [ ] README 含 ≥2 个使用示例 + 配置覆盖示例

---

## 关联技能

- **上游**：`mcpowers-brainstorm`（领域边界不清时澄清）
- **下游**：`mcpowers-plan`（任务 > 3 步拆解）/ `mcpowers-tdd`（补 verify 测试）/ `mcpowers-code-review`（封装自审）/ `mcpowers-git-commit`（提交）
- **同级（易混淆）**：
  - `mcpowers-min-module` —— 纯技术能力，无特定领域；本技能封装**特定领域能力**
  - `mcpowers-feat` —— 已存在项目加功能；本技能**从零生成 SDK**
  - `mcpowers-extract` —— 从已有项目抽离可复用资产；本技能专注**新 SDK 工程标准**
  - `mcpowers-init` —— 从零搭项目骨架；本技能专注**可分发的 SDK 形态**
