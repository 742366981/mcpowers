"""mcpowers Flask Flasgger 全局组件注入模板（v4.4.0+ 推荐）

把 swagger_components.md 定义的 5 个全局组件 + BearerAuth 安全声明写到
SWAGGER_TEMPLATE 常量，项目 `apps/__init__.py` 调 `Swagger(app, template=SWAGGER_TEMPLATE)`
即可启用全局组件复用——接口 docstring 用 `$ref: '#/definitions/BizResponse'` 即可
复用通用响应结构，不再每个接口手工展开 `{code, msg, data}`。

使用方式（apps/__init__.py）：

    from mcpowers_swagger_config import SWAGGER_TEMPLATE
    Swagger(app, template=SWAGGER_TEMPLATE)

设计原则（YAGNI）：
- 只暴露 SWAGGER_TEMPLATE 一个常量，不封装 helper / class（项目按需扩展）
- host / basePath / swagger UI bundle JS URL 等由项目自己配置（不在 SSOT 范围）
- 5 个组件定义与 swagger_components.md §1 完全一致（避免双源漂移）
"""

from __future__ import annotations

# v4.4.0+ 全局组件定义（与 swagger_components.md §1 同步）
_DEFINITIONS: dict = {
    "StandardResponse": {
        "type": "object",
        "required": ["code", "msg"],
        "properties": {
            "code": {
                "type": "integer",
                "description": "业务状态码（0=成功，非 0=业务失败）",
                "example": 0,
            },
            "msg": {
                "type": "string",
                "description": "提示信息",
                "example": "success",
            },
            "data": {
                "type": "object",
                "description": "业务数据；为 null 时不返回此字段",
            },
        },
    },
    "BizResponse": {
        "allOf": [
            {"$ref": "#/definitions/StandardResponse"},
            {
                "type": "object",
                "required": ["data"],
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "业务数据对象",
                    },
                },
            },
        ],
    },
    "PageResponse": {
        "allOf": [
            {"$ref": "#/definitions/StandardResponse"},
            {
                "type": "object",
                "required": ["data"],
                "properties": {
                    "data": {
                        "type": "object",
                        "required": [
                            "records",
                            "page_no",
                            "page_size",
                            "total_page",
                            "total_count",
                        ],
                        "properties": {
                            "records": {
                                "type": "array",
                                "description": "当前页数据列表",
                                "items": {"type": "object"},
                            },
                            "page_no": {
                                "type": "integer",
                                "description": "当前页码（从 1 开始）",
                                "example": 1,
                            },
                            "page_size": {
                                "type": "integer",
                                "description": "每页条数",
                                "example": 20,
                            },
                            "total_page": {
                                "type": "integer",
                                "description": "总页数",
                                "example": 5,
                            },
                            "total_count": {
                                "type": "integer",
                                "description": "总记录数",
                                "example": 100,
                            },
                        },
                    },
                },
            },
        ],
    },
    "BizError": {
        "type": "object",
        "required": ["code", "msg"],
        "properties": {
            "code": {
                "type": "integer",
                "description": "业务错误码（非 0）",
                "example": 10001,
            },
            "msg": {
                "type": "string",
                "description": "业务错误信息",
                "example": "用户不存在",
            },
        },
    },
    "FileResponse": {
        "type": "file",
        "description": "二进制文件流（Content-Type 由具体接口决定）",
    },
}

# v4.4.0+ 安全定义 + 全局默认认证
_SECURITY_DEFINITIONS: dict = {
    "BearerAuth": {
        "type": "apiKey",
        "name": "Authorization",
        "in": "header",
        "description": "JWT Token（格式：Bearer {token}）",
    },
}

# 全局默认 security：所有接口默认需 BearerAuth
# 公开接口用 `security: []` 覆盖
_SECURITY: list = [{"BearerAuth": []}]


# ---- 顶层 SSOT 常量 ----

# v4.4.0+ 5 件套 + 全局鉴权（项目 import 后塞到 Swagger(app, template=SWAGGER_TEMPLATE)）
SWAGGER_TEMPLATE: dict = {
    "definitions": _DEFINITIONS,
    "securityDefinitions": _SECURITY_DEFINITIONS,
    "security": _SECURITY,
}


__all__ = ["SWAGGER_TEMPLATE"]
