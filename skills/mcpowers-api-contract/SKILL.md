---
name: mcpowers-api-contract
description: "前后端联调 / 接口对接 / API文档 / 自动生成接口规范 / 接口契约 → 触发本技能。口语：前后端怎么对接,接口文档怎么自动生成,前端怎么拿到接口类型,接口测试怎么做,接口改了文档没更新,Swagger怎么用,OpenAPI怎么生成。English: api contract,openapi generation,frontend api sync,api schema,flasgger,apispec,openapi spec。边界：纯文档编写→mcpowers-prd；纯测试→mcpowers-autoTest；纯部署→mcpowers-deploy。流程一句话：基于 Flask docstring 自动生成 OpenAPI 规范，支持加密访问，前端/测试基于 spec 自动对接，代码即单一真实来源。"
---

# mcpowers-api-contract（API 契约 / 前后端联调）

> **核心理念**：**代码即规范，规范即单一真实来源（SSOT）**。
> Flask 视图函数的 docstring 是接口定义的唯一权威，前端 TS 类型 / API 测试用例 / Markdown 文档**全部自动派生**，零维护成本。

---

## 0. 与 Flask 后端规范 §11 的关系（必读）

> ⚠️ **本技能不替代 Flask 后端规范 §11，而是它的"下游自动化扩展 + 已有工具的整合编排"**。

| 项 | Flask 后端规范 §11 | mcpowers-api-contract（本技能） |
|:---|:-------------------|:--------------------------------|
| 定位 | **强制基线**（每个 Flask 项目必须遵守） | **编排与扩展**（前后端联调场景触发） |
| docstring 格式 | 强制 4 段（summary / description / parameters / responses） | **直接复用 Flask §11.3**，不新建模板 |
| 集成方案 | **锁定 Flasgger** | **默认 Flasgger**（与 Flask §11 一致） |
| 加密方案 | **HTTP Basic Auth + 仅开发环境** | **默认 Basic Auth + 仅开发环境**（与 Flask §11.1 完全一致） |
| 文档导出 | `tools/export_docs.py` → `swagger_spec.json` + `API文档.md` | **复用**：Step 6 直接调此脚本 |
| 前端 TS / API 测试 | （Flask §11 未涉及） | **新增**：Step 7 自动生成 TS 客户端 + API 测试 |

**强约束**：
- 本技能**不得**修改 Flask §11 的任何约束
- 本技能**不得**新建 docstring 模板（直接引用 `API文档/swagger_template.md` Swagger YAML + `API文档/API文档模板.md` Markdown 参考）
- 本技能**复用** `tools/export_docs.py`，**不得**重写导出逻辑

---

## 1. 何时触发

满足以下任一条件：

| 场景 | 用户说法示例 |
|:-----|:-------------|
| 新建 Flask 后端项目需要接口文档 | "做一套接口文档"、"前后端怎么对接" |
| 接口改完文档没同步 | "接口改了文档没更新"、"文档和代码对不上" |
| 前端需要自动生成 TS 类型 | "前端怎么拿到接口类型"、"自动生成 TS 客户端" |
| API 测试需要自动生成 | "接口测试怎么自动做"、"用 spec 跑测试" |
| OpenAPI / Swagger 集成（新建项目） | "新项目集成 Swagger"、"想用 apispec" |
| 接口文档加密访问 | "/apispec_1.json 加密"、"接口文档要登录才能看" |
| **现有项目补 Swagger** | "项目里有 Flask 但没 Swagger，补一套" |

> 💡 **现有 Flask 项目补 Swagger** 场景：跳过 Step 2 的方案选择，**直接走 Flask §11 锁定的 Flasgger**。

---

## 2. 工作流（8 步，含 Step 0 基线对齐）

### Step 0：基线对齐（必读 Flask §11）

**强制 Read** `mcpowers-shared/docs/技术规范/Flask后端规范.md` 第 11 章，确认：

- [ ] Flasgger 已锁定为默认 Swagger 工具
- [ ] docstring 强制 4 段格式已明确
- [ ] HTTP Basic Auth + 仅开发环境的加密策略已确认
- [ ] `/apispec_1.json` 路由 + `/apidocs/` UI 已规划

> 本技能的所有产出**必须**与 Flask §11 对齐，不偏离。

### Step 1：评估现状

读取项目根目录 + `app.py`/`main.py`/`蓝图中关键文件`，识别：

- 是否已有 Flask 项目结构
- 是否已集成 Flasgger / apispec / 其他 Swagger 工具
- 现有 docstring 完整度（接口覆盖率）
- 现有响应格式（统一 `{code, msg, data}` 还是其他）

**输出**：现状清单 + 改造点预估

### Step 2：选择集成方案（**默认 Flasgger**，仅新建项目需选）

**默认行为**：现有 Flask 项目 → **直接走 Flasgger**（无需选择）。

**仅新建项目**才需要 AskUserQuestion，参考 `mcpowers-shared/docs/API契约/集成方案对比.md`：

| 候选方案 | 适用场景 | 与 Flask §11 关系 |
|:---------|:---------|:------------------|
| **Flasgger**（默认） | 现有 Flask 项目 / 喜欢 docstring 内联 YAML / 团队已熟悉 | ✅ **与 Flask §11 完全对齐** |
| apispec + marshmallow | 新项目 / 想要 OpenAPI 3.0 / 前后端分离 | ⚠️ 需用户主动选择（与 Flask §11 不一致） |
| flask-openapi3 | 新项目 / 想要 OpenAPI 3.0 + 自动 UI | ⚠️ 需用户主动选择（与 Flask §11 不一致） |

### Step 3：选择加密方案（**默认 HTTP Basic Auth + 仅开发环境**）

**默认行为**：**完全沿用 Flask §11.1**（HTTP Basic Auth + 仅开发/测试环境，生产环境自动禁用）。

**仅当用户明确要求变更时**，才通过 AskUserQuestion 选其他方案。参考 `mcpowers-shared/docs/API契约/加密方案对比.md`：

| 候选方案 | 适用场景 | 与 Flask §11 关系 |
|:---------|:---------|:------------------|
| **HTTP Basic Auth + 仅开发环境**（默认） | 现有 Flask 项目 / 内部工具 | ✅ **与 Flask §11.1 完全对齐** |
| JWT | 与业务鉴权统一 / 前端已用 JWT | ⚠️ 需主动变更 Flask §11 配置 |
| IP 白名单 | 纯内网 / VPN 环境 | ⚠️ 需主动变更 Flask §11 配置 |
| 限流 + Token | 生产环境 / 高安全要求 | ⚠️ 需主动变更 Flask §11 配置 |

### Step 4：改造 1-2 个示范接口（**直接复用 Flask §11.3 + 现有模板**）

**模板来源**（**不新建任何模板**，直接复用）：

| 用途 | 模板文件 |
|:-----|:---------|
| Swagger 2.0 YAML 模板（写进 docstring） | `mcpowers-shared/docs/API文档/swagger_template.md` |
| 人类阅读 Markdown 模板（导出后样式参考） | `mcpowers-shared/docs/API文档/API文档模板.md` |
| 强制字段基线 | `mcpowers-shared/docs/技术规范/Flask后端规范.md` §11.3 |

**执行步骤**：
1. Read `API文档/swagger_template.md`，按对应接口类型（list/detail/create/update/delete 等）复制 Swagger 2.0 YAML 模板
2. 按 Flask §11.3 强制 4 段格式填写：tags + summary + description + parameters（含 example）+ responses（含 examples）
3. （可选）如需增强，在 `description` 字段末尾补充 **错误码表** 和 **业务示例**（仅作为 Markdown 增强，不影响 Flasgger 解析）
4. `API文档/API文档模板.md` 是 export_docs.py 导出 Markdown 时的**样式参考**（验证导出的 Markdown 是否符合预期）

**只示范 1-2 个接口**，让用户认可风格后再批量推广。

### Step 5：注册 `/apispec_1.json` 路由 + 加密中间件

参考所选方案的集成代码：
- Flasgger：自动注册 `/apidocs/`
- apispec：手动注册 `/apispec_1.json`
- flask-openapi3：自动注册 `/openapi/openapi.json` + Swagger UI

加密中间件按 Step 3 选择的方案挂载。

### Step 6：验证 + 导出 Markdown（**复用 export_docs.py**）

**6.1 验证 spec 可访问**

```bash
# 开发环境（无加密）
curl -fsSL http://localhost:5000/apispec_1.json | jq '.paths | keys'

# 生产环境（带 Basic Auth）
curl -fsSL -u user:pass https://api.example.com/apispec_1.json | jq '.paths | keys'
```

**验证项**：
- [ ] spec 文件能下载
- [ ] 所有接口路径都在 `.paths` 中
- [ ] 关键 schema（请求体/响应体）都有 type 和 example

**6.2 一键导出 Markdown 文档**（**复用 `tools/export_docs.py`，不重写**）

```bash
# 项目根目录执行（自动向上查找 Flask app）
python tools/export_docs.py

# 或指定项目根目录
python tools/export_docs.py --project /path/to/flask-project

# 输出：
#   docs/API文档/swagger_spec.json   ← 机器可消费（前端/测试工具）
#   docs/API文档/API文档.md          ← 人类可读（产品/测试）
```

> 💡 **`API文档.md` 给产品经理/测试看，`swagger_spec.json` 给前端/测试工具消费**。
> 详见 `mcpowers-shared/tools/export_docs.py` 源码。

### Step 7：派生下游（前端 TS + API 测试）

参考：
- 前端：`mcpowers-shared/docs/API契约/前端对接流程.md`
- 测试：`mcpowers-shared/docs/API契约/API测试自动生成.md`

输出：
1. 前端自动生成命令（如 `npx openapi-typescript-codegen`）
2. CI 校验脚本（检测 spec 变更→重新生成）
3. API 测试命令（如 `schemathesis run`）

---

## 3. 必读规范（4 份资产 + 3 份复用）

| 资产 / 工具 | 何时 Read / 调 |
|:------------|:---------------|
| `集成方案对比.md`（新增） | **Step 2** 必读，选方案前 |
| `加密方案对比.md`（新增） | **Step 3** 必读，选加密前 |
| `前端对接流程.md`（新增） | **Step 7** 前端环节必读 |
| `API测试自动生成.md`（新增） | **Step 7** 测试环节必读 |
| **`API文档/swagger_template.md`**（复用） | **Step 4** 必读，复制 Swagger 2.0 YAML 到 docstring |
| **`API文档/API文档模板.md`**（复用） | **Step 4** 必读，验证 export_docs.py 导出的 Markdown 符合预期 |
| **`tools/export_docs.py`**（复用） | **Step 6** 必跑，一键导出 JSON + Markdown |

---

## 4. 与现有规范的关系

| 关系 | 说明 |
|:-----|:-----|
| **依赖** `API规范.md` | 统一响应格式 `{code, msg, data}` + 错误码规范 |
| **依赖** `Flask后端规范.md` §11 | 视图函数 docstring 4 段格式 + Flasgger 集成 + Basic Auth |
| **依赖** `安全规范.md` | 加密中间件要遵守整体安全规范 |
| **复用** `tools/export_docs.py` | 不重写导出逻辑，直接调 |
| **不修改** 上述规范/工具 | 本技能是**编排 + 扩展**而非**替代** |

---

## 5. 触发即执行（精简版）

用户输入触发后：

1. 立即 Read `集成方案对比.md` 准备 Step 2 提问
2. 评估现状（Step 1）→ AskUserQuestion × 2（Step 2 + 3）
3. 按用户选择 Read 对应资产 → 改造示范接口（Step 4-5）
4. 验证 + 派生下游（Step 6-7）

---

## 6. 反模式（禁止）

- ❌ **手动维护 Markdown 接口文档**（与代码不同步是必然的）
- ❌ **在 docstring 里写散文式说明而不写结构化 YAML**（机器无法解析）
- ❌ **跳过 Step 2/3 直接开干**（方案不对再返工成本极高）
- ❌ **一次性改造所有接口**（应示范 1-2 个 → 用户认可 → 批量推广）
- ❌ **spec 路由裸奔不加密**（生产环境泄漏接口信息 = 泄漏业务）
- ❌ **改了 spec 不通知前端**（必须配 CI 校验 + 通知机制）

---

## 7. 完成后自检清单

- [ ] 集成方案已选定并配置
- [ ] 加密方案已选定并挂载中间件
- [ ] 至少 1-2 个示范接口按 5 段格式改造
- [ ] `/apispec_1.json` 可访问（含/不含加密按环境）
- [ ] 前端 TS 客户端生成命令已输出
- [ ] CI 校验脚本（spec 变更→重新生成）已提供
- [ ] API 测试命令（基于 spec）已输出
- [ ] 文档已追加到 `mcpowers-shared/docs/技术规范/API规范.md` 第 X 章（如必要）

---

## 8. 与 mcpowers 其他技能的协作

| 协作技能 | 触发时机 |
|:---------|:---------|
| `mcpowers-feat` | 新建 Flask 接口时，本技能 Step 4 可被嵌入 |
| `mcpowers-autoTest` | Step 7 的 API 测试可调 mcpowers-autoTest 跑报告 |
| `mcpowers-deploy` | 生产环境部署时确保 spec 路由加密配置正确 |
| `mcpowers-git-commit` | Step 5/6 完成后 commit 时确保 spec 文件一并提交 |