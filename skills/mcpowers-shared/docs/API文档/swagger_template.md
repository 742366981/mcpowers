---
title: Flasgger 文档模板（v4.4.0+ 精简版）
type: tech-template
applies_to: [Flask后端, Flasgger]
extends_from: 接口契约规范.md
priority: required
version: 3.0
last_updated: 2026-08-14
stability: evolving
last_breaking_change: v4.4.0
---

# Flasgger 文档模板（Flask/Flasgger 实现指南）

> **v4.4.0 重写**：所有 19 类模板统一改用 `$ref` 复用全局组件（`BizResponse` / `PageResponse` / `BizError` / `FileResponse`），不再每个接口展开 `{code, msg, data}`；`description` 全部 ≤ 30 字简短；`security` 由全局默认继承，公开接口显式 `security: []` 覆盖。
>
> **核心原则**：接口 docstring 只写**这个接口独有的业务字段**——通用响应 / 分页 / 认证全部由全局组件承担。

---

## 0. 前置准备（应用工厂注入全局组件）

`apps/__init__.py` 调 `Swagger(app, template=SWAGGER_TEMPLATE)` 挂载 5 个全局组件 + BearerAuth：

```python
from apps.flask_swagger_config import SWAGGER_TEMPLATE
Swagger(app, template={"swagger": "2.0", "info": {...}, "basePath": "/api", "tags": [...], **SWAGGER_TEMPLATE})
```

完整 SSOT 定义在同目录 `swagger_components.md` + `flask_swagger_config.py`；Flask mount 步骤在 Flask 实现层规范第 §11.5 节展开。

---

## 1. 通用约定

### 1.1 字段缩写约定

| 写法 | 含义 |
|:-----|:-----|
| `schema: {$ref: '#/definitions/BizResponse'}` | 通用业务响应（带 data） |
| `schema: {$ref: '#/definitions/StandardResponse'}` | 通用业务响应（无 data） |
| `schema: {$ref: '#/definitions/PageResponse'}` | 分页列表响应 |
| `schema: {$ref: '#/definitions/BizError'}` | 业务错误 |
| `schema: {$ref: '#/definitions/FileResponse'}` | 文件流 |
| `examples: {application/json: {$ref: '#/definitions/BizResponse'}}` | examples 复用本体 |

### 1.2 模板字段选择清单

| 接口类型 | responses schema | examples |
|:---------|:-----------------|:---------|
| list（分页） | `PageResponse` | `PageResponse` |
| detail / create / update / delete / dict / bind / unbind / submit-task / cancel-task | `BizResponse` | `BizResponse` |
| update / delete / cancel-task（无 data） | `StandardResponse` | `StandardResponse` |
| export / template/download / stream | `FileResponse` | `BizResponse` |
| progress / import（带状态） | `BizResponse` | `BizResponse` |
| webhook（公开回调） | `BizResponse` | `BizResponse` |
| 公开接口（login / register / refresh） | `BizResponse` | `BizResponse`（含 `security: []`） |

### 1.3 路径前缀约定

完整路径 = `basePath` + 蓝图 `url_prefix` + `@bp.route` 路径。**接口 docstring 不写完整路径**——基础路径在 `Swagger(app, template=...)` 的 `basePath` 字段声明；蓝图前缀在 `Blueprint(name, url_prefix='/xxx')` 声明；接口路径在 `@bp.route` 装饰器声明。

### 1.4 description 字段硬约束（v4.4.0+ 加强）

- **≤ 30 字**（仅接口功能一句话）
- **禁写**：HTTP 状态码 / 认证方式 / 错误码清单 / 响应结构 / 完整路径 / 通用约束
- **禁写**：summary 同义重复 / "待补充" / "TBD" / "TODO"

完整禁用清单在接口契约规范 §1.A.1 段。

---

## 2. 13 类基础 CRUD 模板（v4.4.0+ 精简版）

### 2.1 GET list（分页列表）

```python
@auth_bp.route('/list', methods=['GET'])
def list():
    """分页查询列表
---
tags:
  - 大模块/子模块
summary: 分页查询列表
description: 支持多条件筛选与分页排序。
parameters:
  - in: query
    name: page_no
    type: integer
    required: false
    description: 页码，从 1 开始
    example: 1
  - in: query
    name: page_size
    type: integer
    required: false
    description: 每页条数
    example: 20
  - in: query
    name: keyword
    type: string
    required: false
    description: 关键词（模糊匹配）
    example: ""
  - in: query
    name: status
    type: integer
    required: false
    description: 状态（0=禁用，1=启用）
    example: 1
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/PageResponse'
    examples:
      application/json:
        $ref: '#/definitions/PageResponse'
"""
```

### 2.2 GET detail（详情）

```python
@auth_bp.route('/detail', methods=['GET'])
def detail():
    """查询详情
---
tags:
  - 大模块/子模块
summary: 查询详情
description: 根据 ID 查询完整记录。
parameters:
  - in: query
    name: id
    type: integer
    required: true
    description: 记录 ID
    example: 1
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 2.3 POST create

```python
@auth_bp.route('/create', methods=['POST'])
def create():
    """创建
---
tags:
  - 大模块/子模块
summary: 创建
description: 创建新记录。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        name:
          type: string
          description: 名称
          example: 示例名称
        code:
          type: string
          description: 编码
          example: CODE001
        status:
          type: integer
          description: 状态（0=禁用，1=启用）
          example: 1
      required:
        - name
        - code
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 2.4 POST update

```python
@auth_bp.route('/update', methods=['POST'])
def update():
    """更新
---
tags:
  - 大模块/子模块
summary: 更新
description: 按 ID 更新记录字段。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        id:
          type: integer
          description: 记录 ID
          example: 1
        name:
          type: string
          description: 名称
          example: 新名称
        status:
          type: integer
          description: 状态
          example: 1
      required:
        - id
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/StandardResponse'
    examples:
      application/json:
        $ref: '#/definitions/StandardResponse'
"""
```

### 2.5 POST delete

```python
@auth_bp.route('/delete', methods=['POST'])
def delete():
    """删除
---
tags:
  - 大模块/子模块
summary: 删除
description: 软删除指定记录。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        id:
          type: integer
          description: 记录 ID
          example: 1
      required:
        - id
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/StandardResponse'
    examples:
      application/json:
        $ref: '#/definitions/StandardResponse'
"""
```

### 2.6 POST batch-delete

```python
@auth_bp.route('/batch-delete', methods=['POST'])
def batch_delete():
    """批量删除
---
tags:
  - 大模块/子模块
summary: 批量删除
description: 批量删除多条记录（上限 100 条）。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        ids:
          type: array
          items:
            type: integer
          description: 记录 ID 列表
          example: [1, 2, 3]
      required:
        - ids
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/StandardResponse'
    examples:
      application/json:
        $ref: '#/definitions/StandardResponse'
"""
```

### 2.7 POST update-status

```python
@auth_bp.route('/update-status', methods=['POST'])
def update_status():
    """修改状态
---
tags:
  - 大模块/子模块
summary: 修改状态
description: 单独修改记录状态字段。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        id:
          type: integer
          description: 记录 ID
          example: 1
        status:
          type: integer
          description: 状态（0=禁用，1=启用）
          example: 0
      required:
        - id
        - status
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/StandardResponse'
    examples:
      application/json:
        $ref: '#/definitions/StandardResponse'
"""
```

### 2.8 GET dict（数据字典）

```python
@auth_bp.route('/dict', methods=['GET'])
def dict():
    """获取数据字典
---
tags:
  - 大模块/子模块
summary: 获取数据字典
description: 按字典类型查询选项列表。
parameters:
  - in: query
    name: type
    type: string
    required: true
    description: 字典类型
    example: account_type
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 2.9 GET dict/cascader（级联下拉）

```python
@order_bp.route('/dict/cascader', methods=['GET'])
def cascader_dict():
    """级联下拉数据
---
tags:
  - 大模块/子模块
summary: 级联下拉数据
description: 返回树形结构，value 用路径格式（如 0-0-0）保证唯一。
parameters:
  - in: query
    name: type
    type: string
    required: true
    description: 字典类型代码
    example: region
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 2.10 GET export（导出文件流）

```python
@auth_bp.route('/export', methods=['GET'])
def export():
    """导出列表
---
tags:
  - 大模块/子模块
summary: 导出列表
description: 按筛选条件导出 Excel 文件流。
parameters:
  - in: query
    name: keyword
    type: string
    required: false
    description: 关键词
    example: ""
  - in: query
    name: status
    type: integer
    required: false
    description: 状态
    example: 1
responses:
  200:
    description: Excel 文件流
    schema:
      $ref: '#/definitions/FileResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 2.11 GET template/download

```python
@auth_bp.route('/template/download', methods=['GET'])
def template_download():
    """下载导入模板
---
tags:
  - 大模块/子模块
summary: 下载导入模板
description: 下载 Excel 导入模板。
responses:
  200:
    description: Excel 文件流
    schema:
      $ref: '#/definitions/FileResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 2.12 POST import（导入）

```python
@auth_bp.route('/import', methods=['POST'])
def import_():
    """导入数据
---
tags:
  - 大模块/子模块
summary: 导入数据
description: 通过 Excel 导入数据，失败行最多返回 10 条。
parameters:
  - in: formData
    name: file
    type: file
    required: true
    description: Excel 文件（.xlsx/.csv）
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 2.13 POST upload（通用文件上传）

```python
@auth_bp.route('/upload', methods=['POST'])
def upload():
    """上传文件
---
tags:
  - 大模块/子模块
summary: 上传文件
description: 上传文件到服务器（单文件 ≤ 10MB）。
parameters:
  - in: formData
    name: file
    type: file
    required: true
    description: 文件
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

---

## 3. 6 类扩展模板

### 3.1 POST bind（绑定）

```python
@user_role_bp.route('/bind', methods=['POST'])
def bind_user_role():
    """绑定用户角色
---
tags:
  - 系统管理/角色分配
summary: 绑定用户角色
description: 为用户绑定一个或多个角色（已绑定则跳过）。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        user_id:
          type: integer
          description: 用户 ID
          example: 1
        role_ids:
          type: array
          items:
            type: integer
          description: 角色 ID 列表
          example: [1, 2, 3]
      required:
        - user_id
        - role_ids
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/StandardResponse'
    examples:
      application/json:
        $ref: '#/definitions/StandardResponse'
"""
```

### 3.2 POST unbind（解绑）

```python
@user_role_bp.route('/unbind', methods=['POST'])
def unbind_user_role():
    """解绑用户角色
---
tags:
  - 系统管理/角色分配
summary: 解绑用户角色
description: 解绑用户的一个或多个角色。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        user_id:
          type: integer
          description: 用户 ID
          example: 1
        role_ids:
          type: array
          items:
            type: integer
          description: 角色 ID 列表
          example: [1, 2]
      required:
        - user_id
        - role_ids
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/StandardResponse'
    examples:
      application/json:
        $ref: '#/definitions/StandardResponse'
"""
```

### 3.3 POST submit-task（异步提交）

```python
@report_bp.route('/generate/submit-task', methods=['POST'])
def submit_generate_task():
    """提交报表生成任务
---
tags:
  - 业务模块/报表管理
summary: 提交报表生成任务
description: 异步提交任务，返回 task_id 用于查询进度。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        report_type:
          type: string
          description: 报表类型
          example: monthly_sales
        date_range_start:
          type: string
          format: date
          description: 起始日期
          example: "2024-01-01"
        date_range_end:
          type: string
          format: date
          description: 结束日期
          example: "2024-01-31"
      required:
        - report_type
        - date_range_start
        - date_range_end
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 3.4 GET progress（任务进度）

```python
@report_bp.route('/generate/progress', methods=['GET'])
def query_generate_progress():
    """查询任务进度
---
tags:
  - 业务模块/报表管理
summary: 查询任务进度
description: 根据 task_id 查询任务状态与进度。
parameters:
  - in: query
    name: task_id
    type: string
    required: true
    description: 任务 ID（来自 submit-task 接口）
    example: t_20240715_abc123
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 3.5 POST cancel-task（取消任务）

```python
@report_bp.route('/generate/cancel-task', methods=['POST'])
def cancel_generate_task():
    """取消任务
---
tags:
  - 业务模块/报表管理
summary: 取消任务
description: 取消正在执行的任务（终态任务不可取消）。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        task_id:
          type: string
          description: 任务 ID
          example: t_20240715_abc123
      required:
        - task_id
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/StandardResponse'
    examples:
      application/json:
        $ref: '#/definitions/StandardResponse'
"""
```

### 3.6 POST webhook（第三方回调）

```python
@payment_bp.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    """支付回调
---
tags:
  - 业务模块/支付管理
summary: 支付回调
description: 接收支付回调，验签后处理订单状态。
security: []
parameters:
  - in: header
    name: X-Signature
    type: string
    required: true
    description: HMAC-SHA256 签名（格式 sha256={hex}）
    example: sha256=a1b2c3d4e5f6g7h8i9j0
  - in: header
    name: X-Event-Id
    type: string
    required: true
    description: 事件唯一 ID（用于幂等去重）
    example: evt_20240715_abc
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        event_id:
          type: string
          description: 事件 ID（与 X-Event-Id 一致）
          example: evt_20240715_abc
        event_type:
          type: string
          description: 事件类型
          example: payment.success
        occurred_at:
          type: string
          format: date-time
          description: 事件发生时间（ISO 8601）
          example: "2024-07-15T10:30:00Z"
        data:
          type: object
          description: 业务数据
      required:
        - event_id
        - event_type
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 3.7 GET stream/sse（服务器推送）

```python
@log_bp.route('/stream', methods=['GET'])
def stream_logs():
    """实时日志流
---
tags:
  - 运营管理/日志管理
summary: 实时日志流
description: 通过 SSE 实时推送系统日志。
security: []
parameters:
  - in: query
    name: level
    type: string
    required: false
    description: 日志级别（error/warn/info/debug）
    example: error
  - in: query
    name: task_id
    type: string
    required: false
    description: 任务 ID（仅推送该任务的日志）
    example: t_20240715_abc
produces:
  - text/event-stream
responses:
  200:
    description: SSE 事件流
    schema:
      type: string
"""
```

---

## 4. 认证 3 类模板（公开接口）

### 4.1 POST login（登录·公开）

```python
@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录
---
tags:
  - 系统管理/认证管理
summary: 用户登录
description: 使用用户名或手机号和密码登录。
security: []
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        username:
          type: string
          description: 用户名或手机号
          example: admin
        password:
          type: string
          description: 密码（MD5）
          example: 0192023a7bbd73250516f069df18b500
      required:
        - username
        - password
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

### 4.2 POST logout（登出）

```python
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """退出登录
---
tags:
  - 系统管理/认证管理
summary: 退出登录
description: 使当前 Token 失效。
security: []
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/StandardResponse'
    examples:
      application/json:
        $ref: '#/definitions/StandardResponse'
"""
```

### 4.3 POST refresh（token 刷新）

```python
@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """刷新 Token
---
tags:
  - 系统管理/认证管理
summary: 刷新 Token
description: 使用旧 Token 换新 Token。
security: []
parameters:
  - in: header
    name: Authorization
    type: string
    required: true
    description: 旧 Token（格式：Bearer {token}）
    example: Bearer a1b2c3d4e5f6g7h8i9j0
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
"""
```

---

## 5. 标签对照表

标签格式：`大模块/子模块`，按实际业务增删。

| 大模块 | 子模块 |
|:-------|:-------|
| 系统管理 | 认证、用户、角色、权限、菜单、操作日志、登录日志 |
| 基础数据 | 国家、地区、平台、部门、机构 |
| 业务模块 | （按实际业务填写，如：订单、商品、会员等） |

---

## 6. v4.4.0+ 迁移指引

### 6.1 从 v4.3.0 风格迁移到 v4.4.0 风格

**Step 1**：在 `apps/__init__.py` 注入 `SWAGGER_TEMPLATE`（Flask 实现层规范第 §11.5 节）。

**Step 2**：每个接口 docstring 执行 3 处替换：

| 旧（v4.3.0 风格） | 新（v4.4.0 风格） |
|:------------------|:------------------|
| `responses.200.schema` 展开 `{code, msg, data}` | `schema: {$ref: '#/definitions/BizResponse'}` |
| `responses.200.examples` 写 `{code: 0, msg: success, data: {...}}` | `examples: {application/json: {$ref: '#/definitions/BizResponse'}}` |
| `security: - Bearer: []` 每个接口重复 | 删除（全局 `security` 已默认） |

**Step 3**：description 改写为 ≤ 30 字简短，去掉通用约束 / 状态码 / 认证 / 错误码内容。

### 6.2 自动迁移脚本（推荐）

项目根目录自主实现迁移脚本（基于 `swagger-lint-helper.py` 的 `parse_python_docstring` 即可写一个简单的文本替换器）；本仓库不强制托管迁移工具。
