# API 设计规范

本文档定义通用的 API 设计规范，适用于所有后端框架（Flask、Node.js、Go、Java 等）。

> **核心原则**：规范内容语言无关，代码示例仅作参考

---

## 1. 错误码规范（强制）

### 1.1 错误码定义（强制）

错误码采用**分层设计**：

| 层级 | 范围 | 说明 |
|:-----|:-----|:-----|
| 系统错误码 | 0, 400-599 | HTTP状态语义，通用 |
| 业务错误码 | 10001+ | 自定义业务错误 |

**系统错误码定义**：

| code | 说明 | 使用场景 |
|:----:|:-----|:---------|
| 0 | 成功 | 操作成功 |
| 400 | 参数错误 | 请求参数校验失败 |
| 401 | 未授权 | 未登录或token过期 |
| 403 | 禁止访问 | 无权限 |
| 404 | 资源不存在 | 资源不存在 |
| 500 | 服务器错误 | 服务器内部错误 |

---

## 2. 响应规范（强制）

### 2.1 统一响应结构

| 字段 | 类型 | 必须 | 说明 |
|:-----|:-----|:-----|:-----|
| code | int | 是 | 状态码，0=成功，非0=失败 |
| msg | string | 是 | 消息，成功为"success"或自定义 |
| data | object | 否 | 数据，null时不返回此字段 |

### 2.2 分页响应结构

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| records | array | 数据列表 |
| page_no | int | 当前页码 |
| page_size | int | 每页条数 |
| total_page | int | 总页数 |
| total_count | int | 总记录数 |

---

## 3. API路径规范（强制）

### 3.1 接口前缀规范

**所有接口必须使用项目英文标识作为前缀**：

| 前缀类型 | 格式 | 示例 |
|:---------|:-----|:-----|
| 业务接口 | `/{项目前缀}/{模块}/{操作}` | `/ec/order/list` |

### 3.2 路径规范

| 接口类型 | 路径规则 | 完整示例 |
|:---------|:---------|:---------|
| 列表接口 | `/list` | `GET /{前缀}/order/list` |
| 详情接口 | `/detail` | `GET /{前缀}/order/detail` |
| 创建接口 | `/create` | `POST /{前缀}/order/create` |
| 更新接口 | `/update` | `POST /{前缀}/order/update` |
| 删除接口 | `/delete` | `POST /{前缀}/order/delete` |
| 批量删除 | `/batch-delete` | `POST /{前缀}/order/batch-delete` |

---

## 4. API参数命名规范（强制）

### 4.1 单资源接口

**统一使用 `id` 作为参数名**：

| 接口类型 | 参数位置 | 参数名 |
|:---------|:--------|:-------|
| 详情 | query | `id` |
| 更新 | body | `id` |
| 删除 | body | `id` |

### 4.2 关联表接口

**关联表保留具体参数名**（ user_id、role_id 等）。

---

## 5. 参数验证规范（强制）

### 5.1 验证规则

| 验证类型 | 规则 | 错误信息示例 |
|:---------|:-----|:-------------|
| 必填检验 | 字段不能为空 | "xxx不能为空" |
| 长度检验 | 字符串长度范围 | "xxx长度不能超过N" |
| 格式检验 | 正则表达式匹配 | "xxx格式不正确" |
| 范围检验 | 数值/日期范围 | "xxx必须在N到M之间" |

### 5.2 查询条件类型

| 类型 | 格式 | 示例 |
|:-----|:-----|:-----|
| 单选查询 | 直接值 | `?status=1` |
| 多选查询 | 逗号分隔 | `?role_id=1,2,3` |
| 范围查询 | _min, _max | `?balance_min=100&balance_max=1000` |
| 模糊查询 | 直接字符串 | `?username=admin` |

---

## 6. 接口文档规范（强制）

### 6.1 必需字段

| 字段 | 必须 | 说明 |
|:-----|:-----|:-----|
| summary | 是 | 接口简短描述 |
| description | 是 | 接口详细描述 |
| parameters | 是 | 请求参数列表 |
| responses | 是 | 响应格式列表 |

### 6.2 docstring模板

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
          description: 用户名
          example: admin
        password:
          type: string
          description: 密码(MD5)
          example: e10adc3949ba59abbe56e057f20f883e
responses:
  200:
    description: 登录成功
    examples:
      application/json:
        code: 0
        data:
          token: "a1b2c3d4..."
        msg: "success"
"""
```

**重要：标题与`---`之间不能有空行**

---

## 7. 导入导出接口规范（强制）

详见 `导入导出规范.md`

---

## 附录

### A. 相关文档

| 文档 | 位置 |
|:-----|:-----|
| 导入导出规范 | `导入导出规范.md` |
| Flask后端规范 | `技术锁规范/Flask后端规范.md` |
