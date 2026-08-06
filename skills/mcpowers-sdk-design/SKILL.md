---
name: mcpowers-sdk-design
description: "SDK设计 / 封装领域API / 业务封装库 / 通用可import / defaults.ini+覆盖合并 / 健康检查硬拒绝 / 上游错误重试vs客户端错误分离 → 触发本技能。口语：做个SDK、写个接口封装、封装第三方接口、做客户端库、SDK怎么设计、客户端SDK、领域SDK、可分发包。中英：SDK design,API wrapper,client library,business封装,health check,retry on upstream error。边界：纯工具函数零业务→mcpowers-min-module；从零搭骨架→mcpowers-init；从已有项目抽离可复用资产→mcpowers-extract；已有项目加功能→mcpowers-feat。流程：确认领域→外部依赖分析→SDK形态→defaults.ini+覆盖→健康检查→异常分层→资源泄漏防护→verify验证。"
---

# mcpowers-sdk-design（SDK 设计）

> **核心**：把**某个特定领域能力**封装成可独立分发、可 `import`、可调用的 SDK。SDK 本身必须遵守最小模块基线（零业务字眼 / 自包含 / 可独立 import），同时多一层「领域能力封装 + 健壮性纪律」。
> 不是 `mcpowers-min-module`（纯技术能力，无特定领域），不是 `mcpowers-feat`（已存在项目加功能）——本技能专注**一个 SDK 从零到可交付**的工程标准。

> **通讯层中立**：SDK 不绑 HTTP / gRPC / WebSocket / 文件 IO / CLI 包装等任何具体通道。"调用" / "响应" / "上游错误" / "客户端错误" 是抽象口径；具体技术选型由用户场景决定。

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

1. **【最高优先级】SDK = 升级版最小模块 + 领域能力封装 + 混合复用判断**——
   - SDK 必须满足最小模块基线（零业务字眼 / 自包含 / 可独立 import / 跨项目可搬运）
   - **混合复用判断**：
     - (a) 用户**主动声明**「我用了 X」「项目下有 Y」→ 记录复用清单，不再询问
     - (b) 未声明 → AI 做一次轻量项目扫描（< 5 秒），扫到候选**集中询问一次**（一次性列出所有候选 + 对应能力，不重复问）
     - (c) 都没命中 → SDK 自包含所有能力 = 自当最小模块（**不询问**）
   - **禁止每个能力重复询问**用户
   - SDK 与 min-module 的**唯一差别**：是否封装了某个领域能力
2. **零业务字眼**（同 min-module 铁律）—— 不出现具体业务名、字段名、状态机名、项目名
3. **外部依赖边界**：仅标准库 + 直接相关第三方库（按通讯层选型：HTTP 用 `requests`/`httpx`；gRPC 用 `grpc`；CLI 用 `subprocess` 等）
4. **自包含日志**（同 min-module 铁律）—— `get_sdk_logger(name)` 工厂
5. **自包含异常体系**—— `SDKError` 基类 + `ConfigError` / `UpstreamError` / `ClientError` / `AuthError` / `RetryExhaustedError` / `HealthCheckError` / `ModeConflictError`
6. **defaults.ini + 覆盖合并**（同 min-module 铁律）—— 全部 `CHANGE_ME` 占位符
7. **健康检查硬拒绝**—— 构造时调 `config.validate()`，发现必填字段未覆盖 → 立即抛 `ConfigError`，不懒加载
8. **双模式 API 互斥**（强烈建议；简单 SDK 可不启用）—— `mode="sync"|"async"` 二选一，跨模式调用同一实例 → `ModeConflictError`
9. **上游错误自动重试**—— 上游错误（5xx / 网络断开 / 超时）→ 指数退避重试，超过 max_attempts 抛 `RetryExhaustedError`
10. **客户端错误立即抛异常**—— 客户端错误（4xx / 参数非法 / 凭据失效）→ 立即抛对应业务异常，**不重试**
11. **连接池路径锚定**—— `pathlib.Path.home() / ".cache" / "{SDK 名称}"`，跨平台可搬运
12. **常驻进程轮次不重叠**—— 同一 SDK 实例不并发跑两次长任务；提供 `is_running` 标记
13. **资源泄漏防护**—— session / connection / file handle / lock 用 `with` 块或 `try/finally` 管理

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
1. **必须遵守最小模块基线**——把 SDK 当作「升级版最小模块」来设计
2. **健康检查硬拒绝**——决不允许 SDK 拿默认值运行时才发现 `CHANGE_ME`，必须构造时立即抛错
3. **上游错误 vs 客户端错误严格分离**——客户端错误绝不能混入重试逻辑
4. **defaults.ini 凭据全占位**——任何 key/secret/token 字段在 `defaults.ini` 里都是 `CHANGE_ME`
5. **禁读环境变量**——同 min-module 铁律
6. **混合复用判断**——不要每个能力重复询问用户，按规则 1 走
7. **通讯层中立**——不预设具体通讯技术栈；规则 9/10 用"上游错误 / 客户端错误"抽象口径

---

## 触发即执行（8 步）

### 1. 确认领域能力边界
- 用户说"封装 XX" → 识别该能力的调用形态（HTTP REST / gRPC / WebSocket / 文件 IO / CLI 包装 / 第三方库 / 数据库）
- 典型能力：auth / 列表查询 / 详情查询 / 提交 / 异步通知 / webhook / 流式订阅
- 产出：**领域能力清单**（每个能力含：调用方式 / 输入参数 / 返回结构 / 错误模式）

### 2. 混合复用判断（混合方案）
- **优先级 1**：解析用户输入是否含「我用了 X」「项目下有 Y」等声明字样
  - 命中 → 记录「复用清单：X→IO, Y→日志, Z→连接池」，进入 Step 3 按清单 `import`
- **优先级 2**：未声明 → AI 做一次轻量扫描（< 5 秒）
  - 用 `Glob` 扫 `*_client*` / `*loggings*` / `*pool*` / `*retry*` / `*validators*` 等候选
  - 用 `Grep` 扫 `def get\|def post\|def request\|class.*Client\|class.*Pool` 等特征
- **优先级 3**：判定结果
  - 扫到 1+ 候选 → **集中询问一次**（用 `AskUserQuestion` 一次性列出所有候选 + 对应能力）
  - 没扫到任何候选 → **不询问**，直接进入 Step 3，SDK 自包含 = 自当最小模块

### 3. 外部依赖边界确认
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

### 4. defaults.ini + 覆盖合并设计
- 段设计参考（按通讯层裁剪）：
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

### 5. 健康检查硬拒绝设计
- 构造时调 `config.validate()`（无论是 `__init__` / `__new__` / `build()` 工厂 / `bind()` 注入，都必须"在用户拿到实例前"完成）
- 必填字段未覆盖 → 立即抛 `ConfigError`（或 SDK 自定义的 `HealthCheckError`）
- **不要懒加载**——避免运行时才发现凭据缺失

### 6. 上游错误 vs 客户端错误分层设计
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

### 7. 资源泄漏防护 + 路径锚定
- session / connection / file handle / lock / subprocess 全部用 `with` 块或 `try/finally` 管理
- 池路径用 `pathlib.Path.home() / ".cache" / "{SDK 名称}"`，跨平台可搬运
- 提供 `close()` 方法
- 可选 `__enter__` / `__exit__` 支持 `with SDK() as sdk:` 语法

### 8. 验证脚本 + 零业务字段最终审计
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
  # Node / TS 类似
  ```

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

- ❌ SDK 内部包含具体业务字段、具体业务状态机、具体业务路径
- ❌ SDK 内部注释 / docstring 出现项目特定字眼
- ❌ import 业务模块（`common.*` / `apps.*` / `flask.*` / 本项目 `config/*`）
- ❌ 依赖整个框架（ORM 之外的 Flask / Django / FastAPI 等）
- ❌ 读环境变量（`os.getenv` / `os.environ` / `process.env`）
- ❌ 配置文件含真实凭据（必须 `CHANGE_ME` 占位符）
- ❌ 健康检查懒加载（构造时必须立即拒绝）
- ❌ 客户端错误也走重试（违反"上游错误 vs 客户端错误"分离）
- ❌ 上游错误重试无退避（必须指数退避）
- ❌ 双模式 API 混用同一实例（违反双模式互斥）
- ❌ 资源泄漏（session / connection / file handle 未用 `with` 块）
- ❌ 预设 SDK 必须是 HTTP 形态（违反通讯层中立）
- ❌ 每个能力重复询问用户「复用 X 吗？」——必须按规则 1 走混合复用判断

---

## 完成后自检清单

- [ ] 领域能力清单已产出（能力 / 通讯层 / 输入 / 输出 / 错误模式）
- [ ] 通讯层选型已确认（HTTP / gRPC / WebSocket / CLI / DB / 第三方库）
- [ ] 混合复用判断已执行（声明优先 / 扫描命中 / 自包含兜底）
- [ ] 零业务字眼审计通过
- [ ] 零具体路径审计通过
- [ ] 零环境变量审计通过
- [ ] 零真实凭据审计通过
- [ ] 外部依赖边界确认（仅标准库 + 直接相关第三方库，按通讯层选型）
- [ ] 自包含日志系统已实现
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
