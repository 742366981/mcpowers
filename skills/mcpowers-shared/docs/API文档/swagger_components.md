---
title: Swagger 全局组件契约
type: tech-spec
applies_to: [Flask/Flasgger, FastAPI, springdoc, swagger-jsdoc]
priority: required
version: 1.0
last_updated: 2026-08-14
stability: stable
last_breaking_change: v4.4.0
---

# Swagger 全局组件契约（v4.4.0+ 强制）

> **核心定位**：把"**通用响应/分页/认证/文件**"等**每个接口都重复声明**的 schema 集中到全局 `components` / `definitions` 一次，**所有接口用 `$ref` 复用**。
>
> **目标**：消除接口 docstring 的 6 大类重复内容（HTTP 200、错误码含义、响应结构 `{code,msg,data}`、分页结构、鉴权方式、文件流），让接口文档只剩"这一接口独有的业务字段"。

---

## 0. 单一权威源（SSOT）铁律

| 重复内容 | 重复在每个接口 | 集中写在 |
|:---------|:--------------|:--------|
| 响应外层 `{code, msg, data}` | 每个接口 `responses.200.schema` / `examples` | `StandardResponse` / `BizResponse` 全局组件 |
| 分页结构 `{records, page_no, ...}` | 每个 list 接口 | `PageResponse` 全局组件 |
| 业务错误 `{code: 10001, msg: ...}` | 每个接口 `responses.200.examples.data` | `BizError` 全局组件（examples 复用） |
| 文件流响应 | 每个 download/stream 接口 | `FileResponse` 全局组件 |
| JWT 鉴权声明 | 每个非公开接口 `security` | `BearerAuth` security definition + 全局默认 `security` |

**接口 docstring 只写业务独有字段**——通用响应/分页/认证只写 `$ref`，不复写一遍。

---

## 1. 五个全局组件（强制）

### 1.1 StandardResponse（业务接口通用响应）

```yaml
definitions:
  StandardResponse:
    type: object
    required: [code, msg]
    properties:
      code:
        type: integer
        description: 业务状态码（0=成功，非 0=业务失败）
        example: 0
      msg:
        type: string
        description: 提示信息
        example: success
      data:
        type: object
        description: 业务数据；为 null 时不返回此字段
```

### 1.2 BizResponse（带 data 字段的业务响应）

```yaml
definitions:
  BizResponse:
    allOf:
      - $ref: '#/definitions/StandardResponse'
      - type: object
        required: [data]
        properties:
          data:
            type: object
            description: 业务数据对象
```

### 1.3 PageResponse（分页响应）

```yaml
definitions:
  PageResponse:
    allOf:
      - $ref: '#/definitions/StandardResponse'
      - type: object
        required: [data]
        properties:
          data:
            type: object
            required: [records, page_no, page_size, total_page, total_count]
            properties:
              records:
                type: array
                description: 当前页数据列表
                items:
                  type: object
              page_no:
                type: integer
                description: 当前页码（从 1 开始）
                example: 1
              page_size:
                type: integer
                description: 每页条数
                example: 20
              total_page:
                type: integer
                description: 总页数
                example: 5
              total_count:
                type: integer
                description: 总记录数
                example: 100
```

### 1.4 BizError（业务错误）

```yaml
definitions:
  BizError:
    type: object
    required: [code, msg]
    properties:
      code:
        type: integer
        description: 业务错误码（非 0）
        example: 10001
      msg:
        type: string
        description: 业务错误信息
        example: 用户不存在
```

### 1.5 FileResponse（文件流响应）

```yaml
definitions:
  FileResponse:
    type: file
    description: 二进制文件流（Content-Type 由具体接口决定）
```

---

## 2. 安全定义（强制）

```yaml
securityDefinitions:
  BearerAuth:
    type: apiKey
    name: Authorization
    in: header
    description: JWT Token（格式：Bearer {token}）

# 全局默认认证：所有接口默认需 BearerAuth
# 公开接口用 `security: []` 覆盖
security:
  - BearerAuth: []
```

---

## 3. 使用方式

### 3.1 接口 docstring 复用标准响应

```yaml
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/BizResponse'
    examples:
      application/json:
        $ref: '#/definitions/BizResponse'
```

**禁止**在每个接口 `responses.200` 里**手动展开** `{code, msg, data}` schema——必须用 `$ref`。

### 3.2 接口 docstring 复用分页响应

```yaml
responses:
  200:
    description: 成功
    schema:
      $ref: '#/definitions/PageResponse'
    examples:
      application/json:
        $ref: '#/definitions/PageResponse'
```

### 3.3 接口 docstring 复用业务错误

```yaml
responses:
  200:
    description: 业务失败时返回 code 非 0
    schema:
      $ref: '#/definitions/BizError'
    examples:
      application/json:
        $ref: '#/definitions/BizError'
```

### 3.4 公开接口覆盖全局鉴权

```yaml
security: []  # 公开接口（登录、注册、密码重置等）覆盖全局 BearerAuth
```

---

## 4. 禁止行为（反模式）

| ❌ 禁止 | ✅ 正确 |
|:-------|:-------|
| 每个接口 `responses.200` 展开 `{code, msg, data}` | 用 `$ref: '#/definitions/BizResponse'` |
| 每个 list 接口的 `data` 字段展开 `{records, page_no, ...}` | 用 `$ref: '#/definitions/PageResponse'` |
| 每个接口声明 `securityDefinitions: Bearer: ...` | 全局声明一次 + 全局 `security` |
| `description` 写"业务接口 HTTP 永远 200" | 不写（业务接口响应规范已在 §1.C.1，每个接口不重述） |
| `description` 写"返回格式：{code, msg, data}" | 不写（schema 已是 BizResponse，自带） |

---

## 5. Flasgger 落地

Flasgger 通过 `Swagger(app, template={...})` 的 `template.definitions` 注册全局组件。

下方同目录提供 `flask_swagger_config.py`；Flask 应用工厂 mount 步骤在 Flask 实现层规范第 §11.5 节展开。
