---
name: mcpowers-feat
description: "加个功能 / 加功能 / 做个新功能 / 新增功能 / 新做一个 / 实现一下 → 触发本技能。口语：我想加/做个功能、帮我做/开发/实现/加一个 XX、做一个 XX、写一个 XX、搭一个新模块/接口/页面、新建 XX、创建 XX、加个 XX、做个新 XX、搞个 XX、弄一个 XX、整一个 XX、做一下 XX、加进来、新加一个。中英：add, add feature, implement, create, develop, feat, feature, new, build, ship。边界：改既有→`mcpowers-requirement-change`；修 bug→`mcpowers-bugfix`。澄清→拆解→规范→TDD→自审→提交；v4.0.2+ 文档零引用 + v4.3.0+ 代码/配置零引用智能二分（22+4 字眼）；**v4.4.0+ 接口 docstring description 零冗余 + `$ref` 复用**（禁 8 类冗余；通用响应走 5 全局组件）；**v4.5.0+ 接口契约四铁律 ERROR 硬门禁**（`@bp.route` 路径禁 `<xxx>`+ `methods=` 只允许 GET/POST + description 禁鉴权 + 禁错误码清单）；**v4.5.1+ §1.K POST 强制 JSON**（POST 一律 application/json；豁免 upload/import/attachment/webhook/callback/notify/oauth 路径段）。"
---

# mcpowers-feat（加功能）

> 借鉴自 superpowers `writing-plans`。
> **核心**：只编排流程，不复制规范内容；规范按需 Read。

---

## 编排

本技能按顺序调用以下方法层技能 + 规范：

| 步骤 | 调用对象 | 类型 | 触发条件 | 失败时 |
|:-----|:---------|:-----|:---------|:-------|
| 1 | `mcpowers-brainstorm` | 方法 | 需求不清 / 多义 | 中断并回问用户 |
| 2 | `mcpowers-plan` | 方法 | 任务 > 3 步 | 跳过（不强制） |
| 3 | 规范组（见 mcpowers-spec-index） | 规范 | 必读 | 中断，提示加载失败 |
| 4 | `mcpowers-tdd` | 方法 | 必走 | RED 缺失则不进入下一步 |
| 5 | `mcpowers-code-review` | 方法 | 实现完成 | Critical 必须修复 |
| 6 | `mcpowers-git-commit` | 场景 | 自审通过 | 阻断提交直到修复 |

**保护路径**（PreToolUse(Write) hook 强制确认）：`mcpowers-shared/`、`mcpowers/`、`hooks/` 三个目录的写操作触发前确认。

**复用优先门禁**（v2.26.0+）：写新函数前必须先扫仓库是否已有等价实现。步骤 `## 2.5` 强制要求输出「已有资产扫描清单」，否则不允许进入第 3 步加载规范之后直接动手实现。
详见 `代码规范.md §6.1.1 复用优先于二次抽象`；hooks 侧由 `pre-write-check-duplicate.sh` 物理兜底。

**不允许跳过**：标注"必走"或"必读"的步骤必须执行。

---

## 触发即执行（10 步）

### 1. 澄清需求
- 需求**清楚** → 跳过，直接进入第 2 步
- 需求**不清** → 调 `mcpowers-brainstorm` 澄清
- 用户明确说"按这个 PRD 做" → 跳过澄清，直接进入第 2 步

### 2. 任务拆解
- 任务 **≤ 3 步** → 跳过拆解，直接进入第 2.5 步
- 任务 **> 3 步** → 调 `mcpowers-plan` 拆成 2-5 分钟可验证小任务

### 2.5 已有资产扫描（v2.26.0+ 强制）

> **目的**：避免「明明 SDK 已有，又包一层」的过度抽象。
>
> 在写任何新函数 / 类 / 模块之前，必须先扫仓库里是否已有等价或近似实现。

**清单格式**（PR 描述 / 对话回复必填；缺则不进入下一步）：

```markdown
## 已有资产扫描结果
- [搜过] `from common.order import create_order` —— 完全满足，未引入
- [搜过] `from sdk.pagination import paginate` —— 完全满足，未二次抽象
- [搜过] `from common.validators import validate_phone` —— 与本需求不匹配（仅校验大陆手机号），改用 `re.match` 正则
- [新写] `parse_url_v2` —— SDK `parse_url` 不支持本场景的 query 参数排序，未引入
```

**自检命令**（在动手前先跑一遍）：

```bash
# 1. 同名函数扫描（仓库内）
rg --type py "def\s+${候选函数名}\b" .
# 2. SDK / 通用模块扫描
rg --type py "def\s+${候选关键词}\b" common/ sdk/ utils/ shared/ helpers/
# 3. 跨项目搬运场景：是否在 common/ 或 sdk/ 里已有
rg --type py "def\s+${候选关键词}\b" $(git rev-parse --show-toplevel)/common/
```

> 任一项命中已有 → **直接复用**，禁止包同名 wrapper。
> 三个命令都跑过、都「未命中」 → 才能进第 3 步动手实现。

**Hook 物理兜底**（免用户自觉）：`hooks/pre-write-check-duplicate.sh` 在 Write/Edit 时自动检测新增 `def` 与仓库内同名 def 冲突，命中则弹 confirm UI 让用户决策。

**v2.28.2 补充：hook 行为简化**——重复检测从 v2.27.6 的 4 类启发式分级砍掉，回归极简 3 档判定：

- **同文件内重名**（同一文件对同一函数名定义 ≥ 2 次）→ 真 bug（Python 后者覆盖前者），**强化阻断**（exit 2 + UI）
- **跨文件同名 + 单行透传**（gold standard）：`def run(x): return other.process(x)` → **强化阻断**（exit 2 + UI），是最经典的二次包装
- **跨文件同名（其他情况）** → Python import 是模块级作用域，跨文件同名不冲突，**默认放行**（exit 0）

豁免：`main` / `hook_main` 入口惯例 + Python dunder 协议方法 + 单下划线私有名。

> 手工 Q1/Q2/Q3 + 自检命令仍是写新函数前必走；hook 是兜底不是替代——同文件重名 + 单行透传它会拦下；跨文件同名（业务模块各自实现）它会放行（是否抽离由作者按需提 `mcpowers-extract`）。详见 `代码规范.md §6.1.1` 的「v2.28.2 补充：hook 行为简化」段。

### 3. 加载规范
- **必须** Read `mcpowers-shared/mcpowers-spec-index/SKILL.md`
- 按查表结果加载对应规范（基线 + 栈规范 + 场景规范）
- 常见组合：
  - Flask 后端接口 → `代码规范` + `接口契约规范`（v2.3.0+ 通用层）+ `Flask后端规范` + `API规范` + **`日志规范`（v2.6.0+ 必读）**
  - FastAPI / Spring Boot / Express / Gin → `代码规范` + `接口契约规范` + 对应栈规范 + **`日志规范`（v2.6.0+ 必读）**
  - Vue 页面 → `代码规范` + `Vue前端规范` + `设计规范`（前端日志不在 `日志规范` 范围，留 TODO）
  - 爬虫 → `代码规范` + `爬虫规范` + **`日志规范`（v2.6.0+ 必读）**
  - 涉及 DB → 加上 `数据库规范`
  - 涉及缓存 → 加上 `缓存规范`
  - **v4.0.2+ 文档编写**：若本次任务涉及新增 / 修改 README / 规范 / 设计文档 / 用户手册 → 必读 `文档编写规范.md §9.5 画蛇添足字眼场景化决策模型`（输出型禁止 / 参考型允许 / 历史型允许——3 问决策）

### 4. 接口先写文档（强制 — v2.3.0 对齐接口契约规范）

> **v2.6.0 强化：架构设计阶段先声明日志体系**
>
> 任何会产生日志的功能/接口/任务，必须在 Step 4 之前先回答 3 件事（详见 `日志规范.md §9`）：
>
> 1. **涉及哪些日志类型**（从 7 类中选，列出具体事件名，如 `biz.order.created`）
> 2. **字段 schema**（业务自定义字段的命名约定，避免与全局字段冲突）
> 3. **大内容策略**（哪些字段会触发截断、哪些豁免场景）
>
> 这 3 件事记入设计文档的"日志设计"子章节，无设计文档则在对话中明确告诉用户。

- 接口 / 公共函数 / 类：先写 docstring，再写实现
- **5 字段契约强制**（任何栈）：`tags` + `summary`（≤ 30 字）+ `description`（≤ 100 字简短功能说明）+ `parameters`（每个含 description+example）+ `responses`（每个含 schema+examples）
- **栈特定写法**：
  - Flask/Flasgger：详见 `mcpowers-shared/docs/技术规范/Flask后端规范.md` §11 + `swagger_template.md`
  - FastAPI/Spring/Express/Gin：详见 `mcpowers-shared/docs/技术规范/接口契约规范.md` §3
- **完整校验清单**：Read `接口契约规范.md` §7 自检清单，**任一项不通过则不提交**
- **反模式黑名单**：Read `接口契约规范.md` §8 反模式（description 写长篇背景 / 漏 description / 漏 example / responses 只列 200 等）

### 5. TDD 循环
- **调 `mcpowers-tdd`**，按 RED-GREEN-REFACTOR 循环
- **铁律**：没有失败的测试，不写生产代码
- 小步快走：每步可独立运行验证

### 6. 按规范实现
- 严格遵守已加载的规范
- SOLID / KISS / DRY / YAGNI 是基线
- 改动波及多处 → Read `代码同步修改规范.md` 找全引用点
- **Python import 顶层（v2.27.0+）**：所有 `import` / `from ... import ...` 必须位于模块顶部导入区；函数/方法/类体、条件块、装饰器内部禁止出现 import；物理门禁 `hooks/pre-write-check-import.sh` 会自动检测新增违规并弹 confirm UI

### 7. 自审
- 调 `mcpowers-code-review`，多维并行审查
- Critical 问题立即修复，Important 评估后处理

### 8. 端到端验证（强制）— 不可跳过

> **铁律**：单测全绿 ≠ 系统正常。新功能首次合入最容易在集成层（接口契约、配置加载、依赖服务、数据库迁移）出问题，必须重启服务跑一遍主链路。

**展开内容**：Read `mcpowers-shared/docs/技术规范/测试规范.md` 第 9 章「端到端自检 6 步」。

**快速版（6 步）**：

1. **重启服务**：dev/staging 环境实际启动一次（不是 `pytest` 跑过就完事）
2. **主链路 curl**：至少跑通 1 个 happy path 接口 / 核心功能点
3. **日志无 ERROR**：服务启动后 5 分钟内日志无 ERROR/WARN 异常
4. **回归点走过**：新功能依赖的上下游接口 / 数据流已验证
5. **环境就绪**：配置/数据库迁移/外部依赖（如有）都已生效
6. **清理测试数据**（v2.0.5 新增）：按 `test_` / `tmp_` 前缀清理数据库记录、缓存键值、上传文件（详见 测试规范 §9.6）

**失败处理**：任何一步失败 → 回 Step 6 修复，禁止带病进入收尾。

### 9. 收尾
- 记录重要细节 → 按需 Read `细节记录规范.md` 后追加
- 调 `mcpowers-git-commit` 提交（按 `Git规范.md`）
- 代码和文档必须同 commit

---

## 何时中断并询问用户

- 需求中存在歧义（"做一个登录"是密码登录？手机号？第三方？）
- 多个方案都不明显占优（"用 Redis 还是用数据库存 session"）
- 改动影响范围超出预期（"改一个字段牵连 5 个模块"）
- 涉及架构变更（新增服务 / 改数据流）

---

## 反模式（禁止）

- ❌ 一上来就写代码，不读规范
- ❌ 一开始就 Read 所有规范文件（爆上下文）
- ❌ 跳过 TDD 直接写实现
- ❌ 写完代码不测试就自审
- ❌ 改完不 commit / 只 commit 代码不 commit 文档
- ❌ **单测全绿就提交，跳过端到端验证**（集成层故障看不见）

---

## 完成后自检清单

- [ ] 规范已按需加载（不是全量）
- [ ] **接口/函数有完整 docstring（v2.4.0 严要求·v2.31.0+ Swagger 接口契约硬门禁）**
  - [ ] 5 字段齐全：tags + summary（≤ 30 字）+ description（≤ 100 字简短）+ parameters（含 description+example）+ responses（含 schema+examples）
  - [ ] responses 含 200 + 至少 1 个错误码
  - [ ] 项目根有 `.swagger-required-fields.yml` 时,必填字段含 mcpowers 默认 + 项目自定义
  - [ ] 已对照 `接口契约规范.md` §7 自检清单逐项过
  - [ ] 已对照 `接口契约规范.md` §8 反模式清单确认无误
  - [ ] **[v2.31.0+]** PreToolUse 硬门禁已自动触发:`hooks/pre-write-confirm-api-hint.sh` → `scripts/swagger-contract-check.sh` → 5 字段不合规 → exit 2 + confirm UI(避免返工)
- [ ] **接口改动已同步**（如改了 Flask 接口）
  - [ ] docstring 已更新（如改路径/参数/响应）
  - [ ] 已重跑 `python tools/export_docs.py`（导出 openapi.json + API文档.md）
  - [ ] 前端 TS 客户端已通知（如有协作前端）
- [ ] 测试覆盖核心逻辑
- [ ] 自审通过（无 Critical 问题）
- [ ] **Python import 全部位于模块顶部（v2.27.0+ 必检）**
  - [ ] 函数/方法/类/条件块/装饰器内部无 import
  - [ ] 仅有循环依赖或真正可选依赖可例外，并已写明原因
  - [ ] Hook 阻断时已向用户确认继续放行
- [ ] **端到端自检 5 步已通过**（见 Step 8）
  - [ ] 服务已重启
  - [ ] 主链路接口 curl 通过
  - [ ] 日志无 ERROR/WARN
  - [ ] 回归点已验证
  - [ ] 环境/配置/迁移已就绪
- [ ] **日志体系符合规范（v2.6.0+ 必检）**
  - [ ] 所有 `logger.*` 调用均带 §3.1 必填字段 + 任一上下文（`request_id` / `trace_id` / `user_id`）
  - [ ] 所有日志类型从 `日志规范.md §2` 的 7 类中选
  - [ ] 所有大内容字段按 §4.1 截断 + 记录 `original_size` + `sha256`
  - [ ] 所有敏感字段经 `mask_sensitive` 脱敏
  - [ ] 所有异常日志用 `logger.exception(...)` 或 `exc_info=True`
- [ ] 重要细节已记录
- [ ] 代码和文档已同 commit
- [ ] **文档与代码同步（v2.9.0+ 必检）**
  - [ ] 如本次改动涉及对外接口/路由/数据库表/环境变量/部署脚本，已同步更新对应文档（docs/api.md / README.md / CHANGELOG.md 等）
- [ ] **文档画蛇添足字眼（v4.0.2+ 新增·如本次写了文档）**
  - [ ] 已跑 §9.5 决策 3 问：① 这段文字是给谁看的？② 删掉「参考 / 参见 / 详见 / 引用 / 参照 / 引自」等 22 字眼后意思会变吗？③ 输出型禁止 / 参考型允许且必要 / 历史型允许
  - [ ] 输出型文档正文无 22 禁用字眼（独立出现也算画蛇添足，不限于"在某文档后"）
  - [ ] 参考型 / 历史型文档已确认走路径白名单（CHANGELOG / 历史教训 / mcpowers-spec-index / API 契约 / 迁移指南）
