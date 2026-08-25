---
name: mcpowers-spec-index
description: 规范导航技能。把"当前任务/文件类型 → 该读哪个规范"做成查表。场景/方法层技能按需 Read 本表，再定向加载规范文件，避免一次加载所有规范造成上下文爆掉。
---

# 规范导航索引

> **用法**：上层技能命中后，先 Read 本表确定要加载的规范文件路径，再按需 Read 命中的规范。**不要跳过本表去猜**。
>
> **当前索引 36 个规范文件**（24 原有 + 4 API契约新增 v2.2.0 + 1 接口契约规范新增 v2.3.0 + 1 日志规范新增 v2.6.0 + 1 公共配套 + 6 平台专项 = 爬虫分析规范 v2.14.0 拆分 7 册，按需加载避免爆上下文；v2.19.0 新增 `reverse-analysis-session.py` 与 §8.5/§8.6 章节，归属工具与抓包册；v2.21.0 新增 §8.8 派生产物自动生成 + 工具 `session-artifacts-generator.py` + 规范《爬虫分析规范》§3.11 App 录制选型调研；**v4.6.0 新增 `FastAPI后端规范.md` v1.0**——Pydantic BaseModel + Field + response_model 替代 Flasgger docstring；§11 OpenAPI 文档体系完整落地 v4.5.x 四铁律 + §1.K POST 强制 JSON）

---

## 1. 快速查表（做什么 → 读哪个）

| 任务 / 文件类型 | 必读规范 |
|:----------------|:---------|
| **任何写代码** | `代码规范.md`（SOLID/KISS/DRY/YAGNI，常驻基线，**含 §Python import 位置规范**——`import` 必须位于模块顶部） |
| **任何接口契约设计 / API 设计**（v2.3.0）⭐ | **`接口契约规范.md`**（栈无关通用层：19 类接口 + 简短 description + parameters/responses 完整结构化规则 + 多栈 docstring 模板） |
| **Flask / 后端 `.py`** | `Flask后端规范.md` + `API规范.md` |
| **FastAPI / 后端 `.py`**（v4.6.0 新增） | `FastAPI后端规范.md` + `API规范.md`（Pydantic BaseModel + 原生 OpenAPI；栈级落地 §1.G/§1.H/§1.I/§1.J/§1.K 五铁律） |
| **Vue / 前端 `.vue`** | `Vue前端规范.md` + `设计规范.md` |
| **Vue / 前端 `.vue`** | `Vue前端规范.md` + `设计规范.md` |
| **爬虫（项目骨架）** | `爬虫规范.md` |
| **逆向统一入口 / 交付与验收** | `爬虫分析规范.md` §1.1-§1.3 + §9.4（目标分层、三种交付形态、外部资源所有权铁律、生命周期、真实可用性、有界并发） |
| **逆向工作区与 Web 协作会话编排（v2.19.0 新增）** | `reverse-analysis-session.py`（统一 init/web-start/web-stop/status）+ `爬虫工具与抓包规范.md` §8.5/§8.6（JS 监控 + 步骤证据索引） |
| **Web 会话派生产物自动生成（v2.21.0 新增）** | `session-artifacts-generator.py`（`run_artifacts_generation`，产物：目标接口候选 top10 + 响应样本 envelope + v2.17.0 类式模块种子）+ `爬虫工具与抓包规范.md` §8.8（产物契约 / 六维评分 / 失败隔离 / 反模式） |
| **App 录制选型调研（v2.21.0 新增，**仅调研不落代码**）** | `爬虫分析规范.md` §3.11（Appium / Frida + 自研 / Accessibility Service 三方案对照 + v2.22+ 选型门槛） |
| **网站 / Web JS / CDP / bb-browser** | `爬虫Web逆向规范.md` + `爬虫工具与抓包规范.md` §3/§6/§8.8（§8.8 为 Web 任务 web-stop 后的派生产物生成） |
| **App 类型未知 / 运行时识别** | `爬虫分析规范.md` §1.2 + §10.9（Android/iOS/Flutter/Hybrid 主专项判断） |
| **Android / Kotlin / Java / JNI** | `爬虫Android逆向规范.md` + `爬虫工具与抓包规范.md` §1.2/§2.3 |
| **iOS / Swift / Objective-C** | `爬虫IOS逆向规范.md` + `爬虫工具与抓包规范.md` §1.2 |
| **Flutter / Dart AOT** | `爬虫Flutter逆向规范.md` |
| **uni-app / React Native / WebView / JSBridge** | `爬虫Hybrid逆向规范.md` + `爬虫工具与抓包规范.md` §3 |
| **小程序 / 小游戏** | `爬虫小程序逆向规范.md` + `爬虫工具与抓包规范.md` §3 调试资源所有权 |
| **涉及 DB / 模型 / SQL** | `数据库规范.md` |
| **涉及缓存 / Redis** | `缓存规范.md` |
| **定时任务 / Celery** | `定时任务规范.md` |
| **导入 / 导出 / Excel** | `导入导出规范.md`（含大文件/前端集成/判重策略） |
| **写测试 / 单测** | `测试规范.md` |
| **端到端验证 / 数据清理**（v2.0.5） | `测试规范.md`（§7.1.1 测试数据生命周期 + §9.6 Step 6 清理测试数据） |
| **自动化测试 / E2E**（v2.1.0） | `自动化测试规范.md` + `测试规范.md`（新增自动化默认 Python；按项目证据选择 pytest/Playwright-Python/DrissionPage 等） |
| **前后端联调 / API 契约 / Swagger 集成**（v2.2.0） | `API契约/集成方案对比.md` + `加密方案对比.md` + `前端对接流程.md` + `API测试自动生成.md` + 复用 `接口契约规范.md`（v2.3.0）+ `API文档/API文档模板.md` + `tools/export_docs.py` |
| **前端自动生成 TS 类型**（v2.2.0） | `API契约/前端对接流程.md` |
| **基于 spec 自动生成 API 测试**（v2.2.0） | `API契约/API测试自动生成.md` |
| **导出 Markdown 接口文档**（已有工具，Flask §11.4） | `tools/export_docs.py`（一键导出 `openapi.json` + `API文档.md`） |
| **部署 / 上线** | `部署规范.md` + `开发环境规范.md` + **`健康检查规范.md`** |
| **安全 / SQL注入 / XSS / 限流 / 幂等** | `安全规范.md` |
| **任何写日志 / 排查日志 / 设计日志体系**（v2.6.0）⭐ | **`日志规范.md`**（栈无关通用层：7 类日志 + JSON 字段 schema + 大内容默认截断 + 脱敏黑名单 + 级别采样 + 输出轮转 + §7.5 级别紧凑打印 + 控制台 stdout 避免 PyCharm 染红 v2.28.4+；任何后端/爬虫项目必读） |
| **API 版本管理** | `API版本管理规范.md` |
| **提交 / 分支** | `Git规范.md` |
| **改动波及多处** | `代码同步修改规范.md` |
| **记录细节 / 重要决策** | `细节记录规范.md` |
| **写文档 / README** | `文档编写规范.md`（含 §9 终态交付原则：只写当前状态、不留历史演进与参考来源痕迹） |
| **读参考资料 / 参考项目后产出文档** | `文档编写规范.md` §9.2/§9.3（学习后自己组织表达，正文禁止出现"参考 xxx"来源指代） |
| **产品设计 / 需求** | `产品设计/产品设计规范.md` |
| **架构 / 概要设计** | `设计规范.md` |
| **AI 全局行为约束** | `AI操作规范.md`（路由器已注入摘要，按需 Read 全文） |

---

## 2. 接口类型速查（19 类，写接口前必看 — v2.3.0 起）

> **栈无关通用契约（任何语言）**：`接口契约规范.md` §0（19 类接口速查表）+ §2.1-§2.13（每类详细契约）
>
> **Flask/Flasgger docstring 实现细节**：见 `docs/API文档/swagger_template.md`（仅 13 类基础 CRUD + 登录登出）
>
> **FastAPI / Pydantic 实现细节**（v4.6.0 新增）：见 `FastAPI后端规范.md §11`——`APIRouter` 装饰器 + `Pydantic BaseModel + Field` + `response_model` 完整替代 docstring；§11.5 自带 `tools/export_openapi.py` 拉 `/openapi.json` 落盘脚本
>
> **业务路径/响应/错误码**：见 `API规范.md`

### 2.1 标准 CRUD + 文件 + 字典（13 类）

| 类型 | HTTP | 路径模板 | 通用契约（任何栈） | Flask docstring 模板 |
|:-----|:-----|:---------|:-------------------|:---------------------|
| list | GET | `/{前缀}/{模块}/list` | 接口契约规范 §2.1 | swagger_template §"GET 列表" |
| detail | GET | `/{前缀}/{模块}/detail` | 接口契约规范 §2.2 | swagger_template §"GET 详情" |
| create | POST | `/{前缀}/{模块}/create` | 接口契约规范 §2.3 | swagger_template §"POST 创建" |
| update | POST | `/{前缀}/{模块}/update` | 接口契约规范 §2.4 | swagger_template §"POST 更新" |
| delete | POST | `/{前缀}/{模块}/delete` | 接口契约规范 §2.5 | swagger_template §"POST 删除" |
| batch-delete | POST | `/{前缀}/{模块}/batch-delete` | 接口契约规范 §2.5 | swagger_template §"POST 批量删除" |
| update-status | POST | `/{前缀}/{模块}/update-status` | 接口契约规范 §2.6 | swagger_template §"POST 状态修改" |
| **dict** | GET | `/{前缀}/{模块}/dict?type=` | 接口契约规范 §2.7 | swagger_template §"GET 数据字典" |
| **dict/cascader** | GET | `/{前缀}/{模块}/dict/cascader?type=` | 接口契约规范 §2.7 | swagger_template §"GET 级联下拉" |
| **import** | POST | `/{前缀}/{模块}/import` | 接口契约规范 §2.8 | swagger_template §"POST 导入" |
| export | GET | `/{前缀}/{模块}/export` | 接口契约规范 §2.8 | swagger_template §"GET 导出" |
| template/download | GET | `/{前缀}/{模块}/template/download` | 接口契约规范 §2.8 | swagger_template §"GET 模板下载" |
| upload | POST | `/{前缀}/upload` | 接口契约规范 §2.9 | swagger_template §"POST 文件上传" |

### 2.2 扩展接口类型（6 类，v2.3.0 新增 — 仅通用契约，无 Flask 模板）

| 类型 | HTTP | 路径模板 | 通用契约 |
|:-----|:-----|:---------|:---------|
| **bind / unbind** | POST | `/{前缀}/{关联表}/{bind\|unbind}` | 接口契约规范 §2.10 |
| **submit-task** | POST | `/{前缀}/{模块}/submit-task` | 接口契约规范 §2.11 |
| **progress** | GET | `/{前缀}/{模块}/progress?task_id=` | 接口契约规范 §2.11 |
| **cancel-task** | POST | `/{前缀}/{模块}/cancel-task` | 接口契约规范 §2.11 |
| **webhook** | POST | `/{前缀}/webhook/{source}` | 接口契约规范 §2.12 |
| **stream/sse** | GET | `/{前缀}/{模块}/stream` | 接口契约规范 §2.13 |

> 💡 **写接口时（v2.3.0 标准流程）**：
> 1. **先看本表**确定接口类型
> 2. **任何栈都读** `接口契约规范.md` 对应章节（含 description 简短规则 + parameters/responses 完整结构化强制规则 + 自检清单）
> 3. **Flask 项目**复制 `swagger_template.md` 的 docstring 模板，按接口契约规范填简短 description + 完整结构化参数/响应
> 4. **其他栈**用 `接口契约规范 §3.2-§3.6` 对应语言的写法（FastAPI / Spring Boot / Express / Gin）

---

## 3. 规范文件路径

所有规范在 `mcpowers-shared/docs/` 下，路径稳定不变：

```
mcpowers-shared/docs/
├── AI操作规范.md
├── 产品设计/
│   └── 产品设计规范.md
└── 技术规范/
    ├── 接口契约规范.md       # 🆕 v2.3.0 通用层（栈无关，19 类接口 + 简短 description + 结构化 parameters/responses）
    ├── API规范.md
    ├── Flask后端规范.md
    ├── FastAPI后端规范.md  # 🆕 v4.6.0（22 章节镜像 Flask；Pydantic + 原生 OpenAPI；§11 OpenAPI 文档落地 v4.5.x 五铁律）
    ├── Vue前端规范.md
    ├── 爬虫规范.md
    ├── 爬虫分析规范.md        # v2.14.0 主册（公共方法论：§1 流程/§3-§6 接口分析/§9.4 真实可用性验收/§10.9 指纹交接/§11 风控）
    ├── 爬虫工具与抓包规范.md  # 🆕 v2.14.0 公共配套（§1 抓包/§2 自动化基础/§3 浏览器运行时复用/§4 弹窗字典/§5 协议层/§6 bb-browser/§7 工具对照表）
    ├── 爬虫Web逆向规范.md     # 🆕 v2.14.0 ↔ mcpowers-reverse-web（§1 加密定位/§2 Web JS 逆向/§3 算法复现/§4 跨端指纹）
    ├── 爬虫Android逆向规范.md # 🆕 v2.14.0 ↔ mcpowers-reverse-android（§1 脱壳/§2 SSL Pinning/§3 静态/§4 动态/§5 so 层）
    ├── 爬虫IOS逆向规范.md     # 🆕 v2.14.0 ↔ mcpowers-reverse-ios（§1 IPA/§2 SSL Pinning/§3 静态/§4 动态）
    ├── 爬虫Flutter逆向规范.md # 🆕 v2.14.0 ↔ mcpowers-reverse-flutter（§1 Dart AOT/§2 blutter darlk/§3 Platform Channel）
    ├── 爬虫Hybrid逆向规范.md  # 🆕 v2.14.0 ↔ mcpowers-reverse-hybrid（§1 容器识别/§2 Bridge 三层定位/§3 接管 WebView）
    ├── 爬虫小程序逆向规范.md   # 🆕 v2.14.0 ↔ mcpowers-reverse-miniprogram（§1 包运行时/§2 平台差异/§3 接口算法/§4 调试资源所有权）
    ├── 代码规范.md
    ├── 数据库规范.md
    ├── 缓存规范.md
    ├── Git规范.md
    ├── 开发环境规范.md
    ├── 设计规范.md
    ├── 测试规范.md
    ├── 部署规范.md
    ├── 定时任务规范.md
    ├── 导入导出规范.md
    ├── 文档编写规范.md
    ├── 代码同步修改规范.md
    ├── 细节记录规范.md
    ├── 安全规范.md          # 🆕 SQL注入/XSS/CSRF/限流/幂等
    ├── API版本管理规范.md   # 🆕 版本策略/breaking change/废弃
    ├── 健康检查规范.md      # 🆕 /health/liveness/readiness
    ├── 自动化测试规范.md    # 🆕 Python 默认/项目证据选型/工具角色/bug 二维分类/报告 JSON schema/修复路由/循环机制
    └── 日志规范.md          # 🆕 v2.6.0 通用层（栈无关，7 类日志 + JSON 字段 + 大内容默认截断 + 脱敏黑名单；v2.28.4+ §7.5 级别紧凑 + stdout）
├── API文档/
│   ├── API文档模板.md
│   └── swagger_template.md  # v2.3.0 标记为「Flask 实现参考」（extends 接口契约规范）
├── API契约/   # 🆕 v2.2.0（前后端联调：4 份资产）
│   ├── 集成方案对比.md        # Flasgger / apispec / flask-openapi3 对比
│   ├── 加密方案对比.md        # Basic Auth / JWT / IP 白名单 / 限流对比
│   ├── 前端对接流程.md        # openapi-typescript-codegen + CI 校验
│   └── API测试自动生成.md     # schemathesis / dredd
└── 工具参考/
    └── 交互数据存档.md
```

---

## 3. 加载原则

1. **基线常驻**：写代码必读 `代码规范.md`（SOLID/KISS/DRY/YAGNI）
2. **栈相关**：识别技术栈后加载对应栈规范（Flask/Vue/爬虫）
3. **场景相关**：识别当前场景后加载场景规范（DB/缓存/定时/导入导出）
4. **不重复加载**：相同规范一次会话只 Read 一次
5. **变化即刷新**：规范被修改后下次 Read 拿到最新版

---

## 4. 使用示例

**示例 1：用户说"加一个 Flask 接口"**
1. 命中 `mcpowers-feat`
2. Read 本表 → 查"任何接口契约设计"（⭐ v2.3.0）+ "Flask/后端 .py" 行
3. 加载：`代码规范.md` + **`接口契约规范.md`** + `Flask后端规范.md` + `API规范.md`
4. 不加载：Vue/爬虫/设计等无关规范

**示例 2：用户说"列表页查询太慢"**
1. 命中 `mcpowers-optimize`
2. Read 本表 → 查"涉及 DB" 行
3. 加载：`代码规范.md` + `数据库规范.md` + `缓存规范.md`
4. 不加载：前端/部署等无关规范

**示例 3：用户说"需求文档里登录方式要改"**
1. 命中 `mcpowers-requirement-change`
2. Read 本表 → 查"改动波及多处" + "记录细节" + "任何接口契约设计"（如涉及接口改动 ⭐ v2.3.0）
3. 加载：`代码同步修改规范.md` + `细节记录规范.md` + 对应栈规范 + **`接口契约规范.md`**（接口改动时）
4. 不加载：无关规范

**示例 4：用户说"加一个 FastAPI 接口"（v4.6.0 起改写）**
1. 命中 `mcpowers-feat`
2. Read 本表 → 查"任何接口契约设计"（⭐ v2.3.0）+ "FastAPI / 后端 .py" 行（⭐ v4.6.0）
3. 加载：`代码规范.md` + **`接口契约规范.md`**（栈无关契约）+ **`FastAPI后端规范.md`**（栈特定：Pydantic + APIRouter + response_model + 5 铁律落地）
4. 不加载：Flask 后端规范（栈无关）/ Vue/爬虫/设计等

**示例 5：用户说"加一个 WebHook 回调接口"（v2.3.0 新增）**
1. 命中 `mcpowers-feat`
2. Read 本表 → 查"任何接口契约设计"
3. 加载：`代码规范.md` + `接口契约规范.md §2.12`（webhook 通用契约）+ 栈对应规范
4. 不加载：WebHook 不属于 §2 的 13 类基础 CRUD，无需 swagger_template.md

**示例 6：用户说"生产日志找不到问题在哪"（v2.6.0 新增）**
1. 命中 `mcpowers-bugfix`
2. Read 本表 → 查"任何写日志 / 排查日志"（⭐ v2.6.0）
3. 加载：`代码规范.md` + **`日志规范.md`**（含 §3 字段 schema + §4 大内容截断 + §5 脱敏 + §7.5 级别紧凑 + stdout；按 `request_id` / `trace_id` 串联日志）
4. 不加载：与日志无关的接口契约/缓存/部署规范

**示例 7：用户说"新项目要统一日志格式"（v2.6.0 新增）**
1. 命中 `mcpowers-init`
2. Read 本表 → 查"任何写日志 / 排查日志 / 设计日志体系"（⭐ v2.6.0）
3. 加载：`代码规范.md` + `开发环境规范.md` + **`日志规范.md`**（§9 架构设计必须声明 3 件事）+ 对应栈规范
4. 不加载：与日志体系无关的产品设计/定时任务规范
