---
title: Flasgger 文档模板
type: tech-template
applies_to: [Flask后端, Flasgger]
extends_from: 接口契约规范.md
priority: required
version: 2.0
last_updated: 2026-07-16
---

# Flasgger 文档模板（Flask 实现参考）

> **⚠️ 重定位说明（v2.3.0 起）**：
>
> | 你要做什么 | 读哪份文档 |
> |:----------|:----------|
> | **设计任何接口的契约**（任何栈）| [`docs/技术规范/接口契约规范.md`](../技术规范/接口契约规范.md) ← **通用层** |
> | **用 Flask/Flasgger 写 docstring** | **本文档** ← 实现层 |
> | **业务规范**（路径/错误码/响应） | [`docs/技术规范/API规范.md`](../技术规范/API规范.md) |
>
> **本文档是 [`接口契约规范.md`](../技术规范/接口契约规范.md) 的 Flask/Flasgger 实现参考**，不是主规范。
>
> **何时读本文档**：
> - 项目使用 **Flask + Flasgger** 框架，需要在视图函数 docstring 中写 Swagger 注解时
> - 需要复制现成的 docstring 模板（13 类基础 CRUD）时
>
> **何时不读本文档**：
> - 用 FastAPI / Spring Boot / Express / Gin → 直接看通用层，然后跳到 §3.2-§3.5 语言模板
> - 只想知道接口设计原则 → 只看通用层即可

---

## 版本声明

本文档基于 **Swagger 2.0** (OpenAPI 2.0) 规范编写。当前项目工具链（Flasgger）对此版本有良好支持。

复制下面的模板到你的视图函数前，根据实际接口修改参数。

---

## 注意事项

### 格式要求
1. **docstring格式**：直接写在视图函数的 `"""..."""` 中，使用 `---` 分隔
2. **标题与`---`之间不能有空行**：否则Flasgger解析会出错
3. **使用 `NO_SANITIZER`**：在 `register_swagger` 时传入，防止换行转义为 `<br/>`

### 正确格式
```python
@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录
---
tags:
  - 系统管理/认证管理
summary: 用户登录
description: 使用用户名或手机号和密码登录，返回Token。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        username:
          type: string
          description: 用户名（手机号也可以）
          example: admin
        password:
          type: string
          description: 密码(MD5)
          example: 0192023a7bbd73250516f069df18b500
      required:
        - username
        - password
responses:
  200:
    description: 登录成功
    examples:
      application/json:
        code: 0
        msg: "success"
"""
```

### 错误格式（会导致description显示<br/>）
```python
# ❌ 标题和---之间有空行
def login():
    """用户登录

    ---
    tags:
    ...
```

---

## 统一响应说明

**所有接口统一返回 HTTP 200 状态码**，成功或失败通过响应体中的 `code` 字段判断：

| code | 说明 |
|:----:|:-----|
| 0 | 成功 |
| 400 | 参数错误 |
| 401 | 未登录或token过期 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

**响应格式**：
```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

---

## 认证说明

- 除登录接口外，其他接口均需认证
- 认证格式：在 Authorization header 中填入 `Bearer {token}`
- token 通过登录接口获取

---

## GET 列表接口模板

```python
@auth_bp.route('/list', methods=['GET'])
def list():
    """查询列表
---
tags:
  - 大模块/子模块
summary: 查询列表
description: 分页查询列表，支持筛选条件。
security:
  - Bearer: []
parameters:
  - in: query
    name: page_no
    type: integer
    required: false
    description: 页码，从1开始
    example: 1
  - in: query
    name: page_size
    type: integer
    required: false
    description: 每页显示数量
    example: 10
  - in: query
    name: keyword
    type: string
    required: false
    description: 关键词（模糊查询）
    example: ""
  - in: query
    name: status
    type: integer
    required: false
    description: 状态（0=禁用，1=启用）
    example: 1
responses:
  200:
    description: 查询成功
    examples:
      application/json:
        code: 0
        data:
          records:
            - id: 1
              name: "示例"
              status: 1
          page_no: 1
          page_size: 10
          total_page: 1
          total_count: 1
        msg: "success"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "success"
        data:
          type: object
          properties:
            records:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: 记录ID
                    example: 1
                  name:
                    type: string
                    description: 名称
                    example: "示例"
                  status:
                    type: integer
                    description: 状态
                    example: 1
            page_no:
              type: integer
              description: 当前页码
              example: 1
            page_size:
              type: integer
              description: 每页数量
              example: 10
            total_page:
              type: integer
              description: 总页数
              example: 1
            total_count:
              type: integer
              description: 总记录数
              example: 1
"""
```

---

## GET 详情接口模板

```python
@auth_bp.route('/detail', methods=['GET'])
def detail():
    """查询详情
---
tags:
  - 大模块/子模块
summary: 查询详情
description: 根据ID查询详细信息。
security:
  - Bearer: []
parameters:
  - in: query
    name: id
    type: integer
    required: true
    description: 记录ID
    example: 1
responses:
  200:
    description: 查询成功
    examples:
      application/json:
        code: 0
        data:
          id: 1
          name: "示例"
          status: 1
        msg: "success"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "success"
        data:
          type: object
          properties:
            id:
              type: integer
              description: 记录ID
              example: 1
            name:
              type: string
              description: 名称
              example: "示例"
            status:
              type: integer
              description: 状态
              example: 1
"""
```

---

## POST 创建接口模板

```python
@auth_bp.route('/create', methods=['POST'])
def create():
    """创建
---
tags:
  - 大模块/子模块
summary: 创建
description: 创建新记录。
security:
  - Bearer: []
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
          example: "示例名称"
        code:
          type: string
          description: 编码
          example: "CODE001"
        status:
          type: integer
          description: 状态（0=禁用，1=启用）
          example: 1
      required:
        - name
        - code
      example:
        name: "示例名称"
        code: "CODE001"
        status: 1
responses:
  200:
    description: 创建成功
    examples:
      application/json:
        code: 0
        data:
          id: 2
        msg: "创建成功"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "创建成功"
        data:
          type: object
          properties:
            id:
              type: integer
              description: 新创建的记录ID
              example: 2
"""
```

---

## POST 更新接口模板

```python
@auth_bp.route('/update', methods=['POST'])
def update():
    """更新
---
tags:
  - 大模块/子模块
summary: 更新
description: 更新记录信息。
security:
  - Bearer: []
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        id:
          type: integer
          description: 记录ID
          example: 1
        name:
          type: string
          description: 名称
          example: "新名称"
        status:
          type: integer
          description: 状态（0=禁用，1=启用）
          example: 1
      required:
        - id
      example:
        id: 1
        name: "新名称"
        status: 1
responses:
  200:
    description: 更新成功
    examples:
      application/json:
        code: 0
        msg: "更新成功"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "更新成功"
        data:
          type: object
          example: {}
"""
```

---

## POST 删除接口模板

```python
@auth_bp.route('/delete', methods=['POST'])
def delete():
    """删除
---
tags:
  - 大模块/子模块
summary: 删除
description: 删除记录。
security:
  - Bearer: []
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        id:
          type: integer
          description: 记录ID
          example: 1
      required:
        - id
      example:
        id: 1
responses:
  200:
    description: 删除成功
    examples:
      application/json:
        code: 0
        msg: "删除成功"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "删除成功"
        data:
          type: object
          example: {}
"""
```

---

## POST 批量删除接口模板

```python
@auth_bp.route('/batch-delete', methods=['POST'])
def batch_delete():
    """批量删除
---
tags:
  - 大模块/子模块
summary: 批量删除
description: 批量删除记录。
security:
  - Bearer: []
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
          description: 记录ID列表
          example: [1, 2, 3]
      required:
        - ids
      example:
        ids: [1, 2, 3]
responses:
  200:
    description: 删除成功
    examples:
      application/json:
        code: 0
        msg: "删除成功"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "删除成功"
        data:
          type: object
          example: {}
"""
```

---

## POST 状态修改接口模板

```python
@auth_bp.route('/update-status', methods=['POST'])
def update_status():
    """修改状态
---
tags:
  - 大模块/子模块
summary: 修改状态
description: 修改记录状态。
security:
  - Bearer: []
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        id:
          type: integer
          description: 记录ID
          example: 1
        status:
          type: integer
          description: 状态（0=禁用，1=启用）
          example: 1
      required:
        - id
        - status
      example:
        id: 1
        status: 0
responses:
  200:
    description: 修改成功
    examples:
      application/json:
        code: 0
        msg: "修改成功"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "修改成功"
        data:
          type: object
          example: {}
"""
```

---

## GET 数据字典接口模板

```python
@auth_bp.route('/dict', methods=['GET'])
def dict():
    """获取数据字典
---
tags:
  - 大模块/子模块
summary: 获取数据字典
description: 获取指定类型的数据字典列表，用于下拉选项。
security:
  - Bearer: []
parameters:
  - in: query
    name: type
    type: string
    required: true
    description: 字典类型
    example: account_type
responses:
  200:
    description: 查询成功
    examples:
      application/json:
        code: 0
        data:
          - dictCode: 1146
            dictSort: 20
            dictLabel: "PayPal"
            dictValue: "PAY_PAL"
            dictType: "account_type"
            cssClass: null
            listClass: null
            defaultFlag: "1"
            status: "0"
            remark: null
          - dictCode: 1147
            dictSort: 10
            dictLabel: "银行转账"
            dictValue: "BANK_TRANSFER"
            dictType: "account_type"
            cssClass: null
            listClass: null
            defaultFlag: "0"
            status: "0"
            remark: null
        msg: "success"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "success"
        data:
          type: array
          items:
            type: object
            properties:
              dictCode:
                type: integer
                description: 字典编码（对应数据库id）
                example: 1146
              dictSort:
                type: integer
                description: 排序号
                example: 20
              dictLabel:
                type: string
                description: 显示文本（对应数据库name，没有时用code）
                example: "PayPal"
              dictValue:
                type: string
                description: 存储值（对应数据库code，没有时用name）
                example: "PAY_PAL"
              dictType:
                type: string
                description: 字典类型
                example: "account_type"
              cssClass:
                type: string
                description: CSS样式类
                example: null
              listClass:
                type: string
                description: 列表样式类
                example: null
              defaultFlag:
                type: string
                description: 默认标志
                example: "1"
              status:
                type: string
                description: 状态
                example: "0"
              remark:
                type: string
                description: 备注
                example: null
"""
```

---

## GET 级联下拉接口模板（dict/cascader）

> **新增** - 适用于地区选择、组织架构、分类层级等树形数据
> **响应规范**：详见 `API规范.md` 第 3.4 节

```python
@order_bp.route('/dict/cascader', methods=['GET'])
def cascader_dict():
    """级联下拉
---
tags:
  - 大模块/子模块
summary: 级联下拉数据
description: |
  返回树形结构数据，适用于 Element UI 的 el-cascader 组件。
  value 字段建议使用路径格式（如 "0-0-0"）保证唯一性。
parameters:
  - in: query
    name: type
    type: string
    required: true
    description: 字典类型代码
    example: region
responses:
  200:
    description: 树形数据
    examples:
      application/json:
        code: 0
        data:
          - label: 四川省
            value: "510000"
            children:
              - label: 成都市
                value: "510100"
                children:
                  - label: 武侯区
                    value: "510107"
              - label: 绵阳市
                value: "510700"
                children:
                  - label: 涪城区
                    value: "510703"
                    disabled: true
        msg: success
"""
```

---

## GET 导出列表接口模板（文件下载）

```python
@auth_bp.route('/export', methods=['GET'])
def export():
    """导出列表
---
tags:
  - 大模块/子模块
summary: 导出列表
description: 导出数据为 Excel 文件。
security:
  - Bearer: []
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
    description: |
      Excel 文件流（二进制下载）
      - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
      - Content-Disposition: attachment; filename={module}_export_{YYYYMMDD}.xlsx
    examples:
      application/json:
        code: 0
        msg: "导出成功"
    schema:
      type: file
"""
```

> **后端实现要点**（Flask）：
> ```python
> from io import BytesIO
> from flask import make_response
>
> response = make_response(output.getvalue())
> response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
> response.headers['Content-Disposition'] = 'attachment; filename=role_export_20240101.xlsx'
> return response
> ```
> 完整实现见 `导入导出规范.md` §10
> 大于 1万行建议使用流式导出（§13.4）

---

## GET 模板下载接口模板

```python
@auth_bp.route('/template/download', methods=['GET'])
def template_download():
    """下载导入模板
---
tags:
  - 大模块/子模块
summary: 下载导入模板
description: 下载 Excel 导入模板。
security:
  - Bearer: []
responses:
  200:
    description: Excel 文件流
    examples:
      application/json:
        code: 0
        msg: "下载成功"
    schema:
      type: file
"""
```

---

## POST 导入接口模板

```python
@auth_bp.route('/import', methods=['POST'])
def import_():
    """导入数据
---
tags:
  - 大模块/子模块
summary: 导入数据
description: |
  通过 Excel 文件导入数据。
  - 唯一性字段：xxx_code（编码）/xxx_name（名称，模糊匹配不推荐）
  - 重复策略：失败（详见 导入导出规范.md §14）
  - 大于 1000 行请使用异步任务接口（/import-task）
parameters:
  - in: formData
    name: file
    type: file
    required: true
    description: Excel 文件（.xlsx/.csv）
responses:
  200:
    description: 导入结果
    examples:
      application/json:
        code: 0
        data:
          total: 100
          success: 95
          fail: 5
          errors:
            - row: 3
              message: "第3行角色编码 'ADMIN' 已存在"
            - row: 17
              message: "第17行部门编码 'DEPT99' 不存在"
        msg: "导入完成"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "导入完成"
        data:
          type: object
          properties:
            total:
              type: integer
              description: 总行数
              example: 100
            success:
              type: integer
              description: 成功行数
              example: 95
            fail:
              type: integer
              description: 失败行数
              example: 5
            errors:
              type: array
              description: 错误详情列表（最多 10 条）
              items:
                type: object
                properties:
                  row:
                    type: integer
                    description: 失败行号（从 2 开始，第 1 行是表头）
                    example: 3
                  message:
                    type: string
                    description: 错误原因（含字段名+值+已存在信息）
                    example: "第3行角色编码 'ADMIN' 已存在"
"""
```

---

## POST 文件上传接口模板

```python
@auth_bp.route('/upload', methods=['POST'])
def upload():
    """上传文件
---
tags:
  - 大模块/子模块
summary: 上传文件
description: 上传文件到服务器。
security:
  - Bearer: []
parameters:
  - in: formData
    name: file
    type: file
    required: true
    description: 文件
responses:
  200:
    description: 上传成功
    examples:
      application/json:
        code: 0
        data:
          url: "/uploads/xxx.png"
        msg: "上传成功"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "上传成功"
        data:
          type: object
          properties:
            url:
              type: string
              description: 文件访问URL
              example: "/uploads/xxx.png"
"""
```

---

## POST 登录接口模板（无需认证）

```python
@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录
---
tags:
  - 系统管理/认证管理
summary: 用户登录
description: 使用用户名或手机号和密码登录，返回Token。
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        username:
          type: string
          description: 用户名（手机号也可以）
          example: admin
        password:
          type: string
          description: 密码(MD5)
          example: 0192023a7bbd73250516f069df18b500
      required:
        - username
        - password
      example:
        username: admin
        password: 0192023a7bbd73250516f069df18b500
responses:
  200:
    description: 登录成功
    examples:
      application/json:
        code: 0
        data:
          token: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
          user_id: 1
          username: "admin"
        msg: "success"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "success"
        data:
          type: object
          properties:
            token:
              type: string
              description: 访问令牌
              example: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
            user_id:
              type: integer
              description: 用户ID
              example: 1
            username:
              type: string
              description: 用户名
              example: "admin"
"""
```

---

## POST 登出接口模板

```python
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """退出登录
---
tags:
  - 系统管理/认证管理
summary: 退出登录
description: 用户退出登录，使当前Token失效。
security:
  - Bearer: []
responses:
  200:
    description: 退出成功
    examples:
      application/json:
        code: 0
        msg: "退出成功"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "退出成功"
        data:
          type: object
          example: {}
"""
```

---

## POST 关联表绑定接口模板（bind）

> **新增**（v2.4.0）— 适用于关联表操作（用户角色绑定、用户权限分配等）

```python
@user_role_bp.route('/bind', methods=['POST'])
def bind_user_role():
    """绑定用户角色
---
tags:
  - 系统管理/角色分配
summary: 绑定用户角色
description: 为已存在的用户绑定一个或多个角色。
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
      example:
        user_id: 1
        role_ids: [1, 2, 3]
responses:
  200:
    description: 绑定成功（已绑定则跳过，返回提示）
    examples:
      application/json:
        code: 0
        msg: "绑定成功"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "绑定成功"
"""
```

---

## POST 关联表解绑接口模板（unbind）

> **新增**（v2.4.0）

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
      example:
        user_id: 1
        role_ids: [1]
responses:
  200:
    description: 解绑成功
    examples:
      application/json:
        code: 0
        msg: "解绑成功"
"""
```

---

## POST 异步任务提交接口模板（submit-task）

> **新增**（v2.4.0）— 长时间任务（如批量导入/导出/报表生成）异步化处理

```python
@report_bp.route('/generate/submit-task', methods=['POST'])
def submit_generate_task():
    """提交报表生成任务
---
tags:
  - 业务模块/报表管理
summary: 提交报表生成任务
description: 异步提交报表生成任务，返回 task_id 用于查询进度。
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
      example:
        report_type: monthly_sales
        date_range_start: "2024-01-01"
        date_range_end: "2024-01-31"
responses:
  200:
    description: 任务提交成功
    examples:
      application/json:
        code: 0
        data:
          task_id: "t_20240715_abc123"
        msg: "已提交"
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        msg:
          type: string
          example: "已提交"
        data:
          type: object
          properties:
            task_id:
              type: string
              description: 任务 ID（UUID，用于查询进度）
              example: t_20240715_abc123
"""
```

---

## GET 异步任务进度查询接口模板（progress）

> **新增**（v2.4.0）— 必须与 submit-task 配合使用

```python
@report_bp.route('/generate/progress', methods=['GET'])
def query_generate_progress():
    """查询报表生成进度
---
tags:
  - 业务模块/报表管理
summary: 查询报表生成进度
description: 根据 task_id 查询异步任务的当前状态和进度。
parameters:
  - in: query
    name: task_id
    type: string
    required: true
    description: 任务 ID（来自 submit-task 接口的 data.task_id）
    example: t_20240715_abc123
responses:
  200:
    description: 查询成功
    examples:
      application/json:
        code: 0
        data:
          status: running
          progress: 50
          result: null
          error: null
        msg: success
    schema:
      type: object
      properties:
        code:
          type: integer
          example: 0
        data:
          type: object
          properties:
            status:
              type: string
              enum: [pending, running, success, failed, cancelled]
              description: |
                任务状态：
                - pending：等待调度
                - running：执行中
                - success：成功（result 有值）
                - failed：失败（error 有值）
                - cancelled：已取消
              example: running
            progress:
              type: integer
              minimum: 0
              maximum: 100
              description: 进度百分比 0-100
              example: 50
            result:
              type: object
              description: 任务成功时的结果（status=success 才有值）
              example: null
            error:
              type: string
              description: 任务失败时的错误信息（status=failed 才有值）
              example: null
"""
```

---

## POST 异步任务取消接口模板（cancel-task）

> **新增**（v2.4.0）

```python
@report_bp.route('/generate/cancel-task', methods=['POST'])
def cancel_generate_task():
    """取消报表生成任务
---
tags:
  - 业务模块/报表管理
summary: 取消报表生成任务
description: 取消正在执行的异步任务（终态任务不可取消）。
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
      example:
        task_id: t_20240715_abc123
responses:
  200:
    description: 已取消
    examples:
      application/json:
        code: 0
        msg: "已取消"
  400:
    description: 任务已结束，不允许取消
    examples:
      application/json:
        code: 400
        msg: "任务已结束，不允许取消"
"""
```

---

## POST WebHook 回调接口模板（webhook）

> **新增**（v2.4.0）— 第三方回调接收方，必须验签 + 幂等
>
> 响应规范：详见 `API规范.md` 第 2.x 节 + `接口契约规范.md` §2.12

```python
@payment_bp.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    """支付回调
---
tags:
  - 业务模块/支付管理
summary: 支付回调
description: 接收第三方支付回调，验签后处理订单状态。
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
    description: 接收成功
    examples:
      application/json:
        code: 0
        msg: ok
  401:
    description: 签名校验失败
    examples:
      application/json:
        code: 401
        msg: signature invalid
"""
```

---

## GET SSE 流式接口模板（stream）

> **新增**（v2.4.0）— Server-Sent Events 长连接推送
>
> 响应规范：详见 `接口契约规范.md` §2.13

```python
@log_bp.route('/stream', methods=['GET'])
def stream_logs():
    """实时日志流
---
tags:
  - 运营管理/日志管理
summary: 实时日志流
description: 通过 SSE 实时推送系统日志，前端用 EventSource 监听。
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
      description: |
        text/event-stream 格式，每条事件格式：
        ```
        event: message
        id: {event_id}
        data: {"timestamp": "2024-07-15T10:30:00Z", "level": "error", "message": "..."}

        ```
"""
```

---

## 标签对照表

> 标签格式：`大模块/子模块`，按实际业务增删

| 大模块 | 子模块 |
|:-------|:-------|  
| 系统管理 | 认证、用户、角色、权限、菜单、操作日志、登录日志 |
| 基础数据 | 国家、地区、平台、部门、机构 |
| 业务模块 | （按实际业务填写，如：订单、商品、会员等） |

**使用说明**：
- 标签在视图函数 docstring 的 `tags` 字段中定义
- 标签格式：`大模块/子模块`，如 `系统管理/用户管理`
- 按实际业务增删子模块，格式保持一致
