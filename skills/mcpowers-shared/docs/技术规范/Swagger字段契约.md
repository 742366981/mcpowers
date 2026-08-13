---
title: Swagger 字段契约(项目自定义必填字段清单机制)
type: tech-spec
applies_to: [所有使用 Swagger/OpenAPI 的栈]
priority: required
version: 1.0
last_updated: 2026-08-12
stability: evolving
last_breaking_change: v1.0
---

# Swagger 字段契约(项目自定义必填字段清单机制)

> **核心定位**:本文档定义**"哪些字段是 Swagger 接口的必填字段"**的可覆盖机制。任何项目可在项目根声明自己的必填字段清单;未声明时,mcpowers 自动落 5 字段契约默认清单。
>
> | 层 | 文件 | 谁读 |
> |:---|:-----|:---|
> | **通用层**(本文) | `Swagger字段契约.md` | 任何栈、任何 swagger 工具 |
> | **5 字段契约定义** | `接口契约规范.md §1` | 引用,不重写 |
> | **Flask 实现层** | `docs/API文档/swagger_template.md` | Flasgger docstring 注解细节 |
> | **默认清单** | `mcpowers-shared/docs/API契约/默认Swagger必填字段.yml` | mcpowers 内部加载 |

---

## 1. 字段清单加载顺序(优先级从高到低)

| # | 来源 | 触发条件 | 失败行为 |
|:-:|:-----|:---------|:---------|
| 1 | 项目根 `.swagger-required-fields.yml` | 文件存在 | 加载并优先使用 |
| 2 | mcpowers 默认清单 | 项目未自定义 | 直接使用 |
| 3 | 软警告 + fallback 默认 | YAML 解析失败 | 不阻断,避免 lint 自身 bug 阻塞开发 |

> **YAGNI 原则**:不引入 YAML 解析库(`pyyaml` 等),helper 用 grep/awk 极简解析。如未来需要复杂 YAML,再补库。

---

## 2. 项目自定义清单格式

### 2.1 文件位置

```
<项目根>/.swagger-required-fields.yml
```

> **命名约定**:点开头(`.swagger-required-fields.yml`)——与 `.gitignore` / 各类 dotfile 风格一致,标识"配置文件而非业务文件",**不应提交业务代码**。

### 2.2 文件格式(极简 YAML 子集)

```yaml
# .swagger-required-fields.yml 示例
# 字段清单:列出接口契约中必须出现的 swagger 字段名
# 注意:本文件只描述字段名,字段格式/子字段约束见 接口契约规范.md §1

required_fields:
  # --- mcpowers 默认清单(5 字段契约)自动包含,无需重复声明 ---
  # tags
  # summary
  # description
  # parameters(含 description + example)
  # responses(含 schema + examples)

  # --- 项目自定义追加字段(可选) ---
  - deprecated          # 标记废弃接口时必填
  - x-permission        # 项目自定义 RBAC 权限标签

# --- 字段子项约束(可选,默认走 mcpowers 标准) ---
parameter_subfields:
  required:
    - description       # 参数描述(默认已在 5 字段契约中)
    - example           # 参数示例
  # project_addition:
  #   - unit             # 项目自定义:单位字段

response_subfields:
  required:
    - schema
    - examples
```

### 2.3 解析规则(grep/awk 极简实现)

helper 不引入 pyyaml,只识别**单层字段** + **数组项**:
- `required_fields:` 后每行 `- <field_name>` 视为一个必填字段
- 注释行(`#` 开头)与空行忽略
- 嵌套结构(如 `parameter_subfields`)作为扩展点预留,**当前版本不解析**(避免过度设计)

---

## 3. mcpowers 默认清单

文件位置:`skills/mcpowers-shared/docs/API契约/默认Swagger必填字段.yml`

```yaml
# mcpowers 默认 Swagger 必填字段清单(v2.31.0+)
# 来源:接口契约规范.md §1 元数据强制字段
# 修改本文件 = 全局升级 mcpowers 默认契约,谨慎

required_fields:
  - tags
  - summary
  - description
  - parameters
  - responses

parameter_subfields:
  required:
    - description
    - example

response_subfields:
  required:
    - schema
    - examples

# 5 字段契约的完整格式约束详见 接口契约规范.md §1
```

---

## 4. 与接口契约规范 §1 的关系

| 字段 | 契约规范定义 | 字段清单声明 | 谁负责校验 |
|:-----|:-------------|:-------------|:-----------|
| `tags` / `summary` / `description` | §1 字段表 | `required_fields` 列名 | lint 检查存在性 |
| `parameters[].description` / `example` | §1.B 子字段 | `parameter_subfields.required` | lint 检查子字段存在 |
| `responses[].schema` / `examples` | §1.C 子字段 | `response_subfields.required` | lint 检查子字段存在 |
| 错误码必含至少 1 个 | §1.C 末尾 | 内置于 lint 逻辑(无需声明) | lint 强校验(不可配置) |

> **错误码检查不开放配置**:这是 mcpowers 的硬纪律,避免项目把它关掉。前端调试时只列 200 = 不可用接口。

---

## 5. 检查清单(本规范的"自检清单",违反则视为规范失效)

- [ ] 项目根有 `.swagger-required-fields.yml` 时,helper 优先使用并跳过默认
- [ ] 项目根未声明时,helper 落 mcpowers 默认(5 字段契约)
- [ ] YAML 解析失败时,helper stderr 软警告 + fallback 默认,**不阻断**
- [ ] 字段清单变更需要在 CHANGELOG 写明(版本兼容,stability: evolving)
- [ ] 不引入 YAML 解析库(grep/awk 足够,YAGNI)
- [ ] 项目自定义字段名(如 `x-permission`)不在 mcpowers 默认清单里时,helper 不应误报

---

## 6. 反模式(禁止)

- ❌ 在 `.swagger-required-fields.yml` 里写空数组(`required_fields: []`)绕过契约
- ❌ 把错误码必含规则放进可配置项(违反 §4 末段硬纪律)
- ❌ 把项目自定义字段命名为 mcpowers 内部字段名(如 `mcpowers_internal`)造成冲突
- ❌ 用 YAML 锚点(`&` / `*`)等高级特性——grep/awk 解析器不识别
- ❌ 把字段清单文件放在项目子目录(必须在项目根,沿用 dotfile 配置惯例)

---

## 7. 版本兼容

`stability: evolving` —— 字段清单格式可能扩展(如未来加 `parameter_subfields.project_addition` 解析)。**升级前会在 CHANGELOG.md 写破坏声明**。`last_breaking_change: v1.0` —— 当前格式自首次发布起未破坏。
