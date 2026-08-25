---
title: FastAPI后端规范
type: tech-spec
applies_to: [FastAPI后端]
priority: required
version: 1.0
last_updated: 2026-08-25
description: FastAPI 后端项目的技术锁规范。1:1 镜像 Flask 后端规范的 22 章节结构，框架绑定部分替换为 FastAPI 原生实现（lifespan / Depends / APIRouter / Pydantic + 原生 OpenAPI）。v4.5.x 接口契约四铁律、§1.K POST 必 JSON、控制台日志紧凑 + stdout + 默认无颜色、本技能禁止使用环境变量、Python import 顶层、复用优先于二次抽象等铁律全部在 §11/§22 落地。
stability: evolving
last_breaking_change: v4.6.0
---

## 0. 接口类型速查表（最高频使用）

> **目的**：AI 写接口时**先看本表**确定类型，再跳转到对应章节。

### 0.1 标准 CRUD（7 类）

| 接口类型 | HTTP 方法 | 路径 | 请求位置 | 关键参数 | 响应 |
|:---------|:----------|:-----|:---------|:---------|:-----|
| **list（列表）** | GET | `/{前缀}/{模块}/list` | query | `page_no`, `page_size`, 筛选条件 | 分页结构 |
| **detail（详情）** | GET | `/{前缀}/{模块}/detail` | query | `id` | 本表字段+关联 |
| **create（创建）** | POST | `/{前缀}/{模块}/create` | body | 本表字段 | `{code:0, data:{id:x}}` |
| **update（更新）** | POST | `/{前缀}/{模块}/update` | body | `id` + 待更新字段 | `{code:0, msg:"更新成功"}` |
| **delete（删除）** | POST | `/{前缀}/{模块}/delete` | body | `id` | `{code:0, msg:"删除成功"}` |
| **batch-delete（批量删除）** | POST | `/{前缀}/{模块}/batch-delete` | body | `ids: []` | `{code:0, msg:"删除成功"}` |
| **update-status（状态修改）** | POST | `/{前缀}/{模块}/update-status` | body | `id`, `status` | `{code:0, msg:"修改成功"}` |

> **§1.H HTTP 方法白名单落地**：业务接口**仅允许 GET / POST**。列表/详情/字典/导出/下载/流式/进度 → GET；创建/更新/删除（单+批量）/导入/上传/bind/webhook → POST。**禁止** PUT / PATCH / DELETE / HEAD / OPTIONS。FastAPI 落地：`@router.get(...)` / `@router.post(...)`，禁 `@router.put/delete/patch/...`。

### 0.2 文件相关（4 类）

| 接口类型 | HTTP 方法 | 路径 | 请求位置 | 关键参数 | 响应 |
|:---------|:----------|:-----|:---------|:---------|:-----|
| **upload（文件上传）** | POST | `/{前缀}/upload` | formData | `file` | `{code:0, data:{url}}` |
| **import（批量导入）** | POST | `/{前缀}/{模块}/import` | formData | `file` (.xlsx/.csv) | `{total, success, fail, errors[]}` |
| **export（数据导出）** | GET | `/{前缀}/{模块}/export` | query | 筛选条件 | Excel 文件流 |
| **template/download（模板下载）** | GET | `/{前缀}/{模块}/template/download` | - | 无 | Excel 模板文件 |

> **§1.K POST 强制 JSON 例外**：路径段含 `upload` / `import` / `attachment` 时允许 `multipart/form-data`（文件必须 multipart）；其余业务 POST 一律 `Content-Type: application/json`，禁 form-urlencoded / multipart。

### 0.3 字典相关（2 类）

| 接口类型 | HTTP 方法 | 路径 | 请求位置 | 关键参数 | 响应 |
|:---------|:----------|:-----|:---------|:---------|:-----|
| **dict（下拉）** | GET | `/{前缀}/{模块}/dict?type={type}` | query | `type`（字典类型） | `[{dictCode, dictLabel, dictValue, ...}]` |
| **dict/cascader（级联下拉）** | GET | `/{前缀}/{模块}/dict/cascader?type={type}` | query | `type` | 树形 `[{label, value, children[]}]` |

### 0.4 认证相关（2 类，由 system/auth 子模块负责）

| 接口类型 | HTTP 方法 | 路径 | 请求位置 | 关键参数 | 响应 |
|:---------|:----------|:-----|:---------|:---------|:-----|
| **login（登录）** | POST | `/{前缀}/auth/login` | body | `username`, `password` | `{token, user_id, username}` |
| **logout（退出）** | POST | `/{前缀}/auth/logout` | header | `Authorization: Bearer {token}` | `{code:0}` |

> **§1.B 认证接口例外**：路径含 `login` / `logout` / `refresh` / `verify` / `register` / `password` 的认证接口，`responses` 允许保留 `401`（非业务响应码，由框架层统一抛出）。其余业务接口禁列 4xx/5xx（响应规范见 §11.5）。

### 0.5 健康检查（1 类）

| 接口类型 | HTTP 方法 | 路径 | 响应 |
|:---------|:----------|:-----|:-----|
| **health（健康检查）** | GET | `/health` | `{status:"ok", db:"ok", redis:"ok"}` |

### 0.6 接口命名反查（看到路径能识别类型）

```
GET  /xxx/list                    → list 接口
GET  /xxx/detail?id=1             → detail 接口
POST /xxx/create                  → create 接口
POST /xxx/update                  → update 接口
POST /xxx/delete                  → delete 接口
POST /xxx/batch-delete            → batch-delete 接口
POST /xxx/update-status           → update-status 接口
POST /xxx/import                  → import 接口（multipart/form-data 上传文件）
GET  /xxx/export?status=1         → export 接口（下载文件）
GET  /xxx/template/download       → template/download 接口
GET  /xxx/dict?type=status        → dict 接口
GET  /xxx/dict/cascader?type=...  → dict/cascader 接口
POST /upload                      → upload 接口（无业务模块）
```

> **§1.G 路径禁动态参数落地**：业务接口路径模板**禁止**含 `{xxx}` / `{int:xxx}` 等动态段（资源标识走 query/body）。例外白名单：`webhook` / `oauth` / `callback` 路径段内的动态参数可保留（第三方协议约束）。FastAPI 落地：`@router.get("/xxx/list")` 不写 `{item_id}`；详情接口 `GET /xxx/detail?id={id}` 用 `Query(...)`。

---

## 1. 目录结构（强制）

### 1.1 整体目录结构

```
project/
├── app/                                # 应用包（FastAPI 实例）
│   ├── __init__.py                     # 应用工厂 create_app() + lifespan 入口
│   ├── main.py                         # uvicorn 启动入口（python -m app.main）
│   │
│   ├── core/                           # 框架层（与业务无关）
│   │   ├── __init__.py
│   │   ├── config.py                   # 配置加载器
│   │   ├── constants.py                # 常量定义（BASE_DIR / ENV_TYPE / RedisKey）
│   │   ├── exceptions.py               # 自定义业务异常 + AppException
│   │   ├── response.py                 # 统一响应（api_success / api_error / api_page）
│   │   ├── deps.py                     # 通用 Depends（get_db / get_current_user / get_redis）
│   │   └── security.py                 # 密码 hash / JWT encode-decode
│   │
│   ├── middleware/                     # 中间件（BaseHTTPMiddleware 子类）
│   │   ├── __init__.py
│   │   ├── request_id.py               # 请求 ID 中间件
│   │   └── request_log.py              # 全局请求日志中间件
│   │
│   ├── loggings/                       # 日志封装
│   │   ├── __init__.py
│   │   └── loggings.py                 # JSON 结构化日志 + 7 类 type
│   │
│   ├── db/                             # 数据库
│   │   ├── mysql/
│   │   │   ├── __init__.py
│   │   │   ├── session.py              # SQLAlchemy async session factory
│   │   │   └── models/                 # ORM 模型
│   │   └── redis/
│   │       ├── __init__.py
│   │       └── client.py               # redis.asyncio 客户端
│   │
│   ├── routers/                        # APIRouter 集合（FastAPI 等价 Flask Blueprint）
│   │   ├── __init__.py                 # register_routers(app)
│   │   ├── system/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # /auth/login /auth/logout
│   │   │   ├── user.py                 # /user/* CRUD
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   ├── menu.py
│   │   │   └── dict.py
│   │   ├── operation/
│   │   │   └── log.py
│   │   ├── file/
│   │   │   └── upload.py
│   │   └── business/                   # 业务模块（按需扩展）
│   │       ├── __init__.py
│   │       ├── order.py
│   │       └── product.py
│   │
│   ├── schemas/                        # Pydantic 模型（请求/响应 schema）
│   │   ├── __init__.py
│   │   ├── common.py                   # PageResponse / BizResponse / StandardResponse 通用 schema
│   │   └── system/
│   │       ├── auth.py                 # LoginRequest / LoginResponse
│   │       ├── user.py
│   │       └── ...
│   │
│   ├── services/                       # 业务逻辑层（与 router 解耦）
│   │   ├── __init__.py
│   │   └── system/
│   │       ├── auth_service.py
│   │       └── user_service.py
│   │
│   └── utils/                          # 辅助工具
│       ├── __init__.py
│       ├── captcha.py
│       └── token_helper.py
│
├── config/                             # 配置文件
│   ├── config_dev.ini
│   ├── config_test.ini
│   └── config_prod.ini
│
├── docs/                               # 文档
│   └── api_docs/
│       ├── openapi.json                # 导出物
│       └── api_docs.md                 # 人类阅读
│
├── tools/
│   └── export_openapi.py               # 导出脚本
│
├── db_init/                            # 数据库初始化
│   └── init_all.py
│
├── jobs/                               # 定时任务（APScheduler / arq）
│   └── example.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.dev.yml
├── docker-compose.test.yml
└── docker-compose.prod.yml
```

### 1.2 模块划分规范

| 模块层级 | 包路径 | 说明 | 是否必须 |
|:---------|:-------|:-----|:--------|
| 一级 | `app/routers/system/` | 系统管理：用户、角色、权限、菜单、字典、认证 | 必须 |
| 一级 | `app/routers/operation/` | 运营管理：日志、监控 | 必须 |
| 一级 | `app/routers/file/` | 文件管理：上传、附件 | 必须 |
| 一级 | `app/routers/business/` | 业务模块：订单、商品等 | 按需扩展 |

### 1.3 子模块划分规范

**`system/` 系统管理模块**：

| 子模块 | 职责 | 接口示例 |
|:-------|:-----|:---------|
| `auth.py` | 认证管理 | 登录、退出、Token 刷新、验证码 |
| `user.py` | 用户管理 | 用户 CRUD、状态管理、个人信息 |
| `role.py` | 角色管理 | 角色 CRUD、角色分配 |
| `permission.py` | 权限管理 | 权限项 CRUD、权限分配 |
| `menu.py` | 菜单管理 | 菜单 CRUD、菜单树 |
| `dict.py` | 字典管理 | 字典类型、字典项 |

**`operation/` 运营管理模块**：

| 子模块 | 职责 | 接口示例 |
|:-------|:-----|:---------|
| `log.py` | 日志管理 | 操作日志、登录日志、异常日志 |

**`file/` 文件管理模块**：

| 子模块 | 职责 | 接口示例 |
|:-------|:-----|:---------|
| `upload.py` | 文件上传 | 通用文件上传、图片上传 |

### 1.4 路由注册规范

```python
# app/routers/__init__.py
# APIRouter 统一在模块顶部导入，避免 register_routers 内部出现局部 import

from fastapi import FastAPI
from app.routers.system import auth, user, role, permission, menu, dict as dict_router
from app.routers.operation import log
from app.routers.file import upload


def register_routers(app: FastAPI):
    """注册所有 APIRouter（FastAPI 等价 Flask Blueprint）"""
    api_prefix = '/api'

    # === system ===
    app.include_router(auth.router, prefix=f'{api_prefix}/auth', tags=['系统管理/认证管理'])
    app.include_router(user.router, prefix=f'{api_prefix}/user', tags=['系统管理/用户管理'])
    app.include_router(role.router, prefix=f'{api_prefix}/role', tags=['系统管理/角色管理'])
    app.include_router(permission.router, prefix=f'{api_prefix}/permission', tags=['系统管理/权限管理'])
    app.include_router(menu.router, prefix=f'{api_prefix}/menu', tags=['系统管理/菜单管理'])
    app.include_router(dict_router.router, prefix=f'{api_prefix}/dict', tags=['系统管理/字典管理'])

    # === operation ===
    app.include_router(log.router, prefix=f'{api_prefix}/log', tags=['运营管理/日志管理'])

    # === file ===
    app.include_router(upload.router, prefix=f'{api_prefix}/upload', tags=['文件管理/通用上传'])

    # === business 按需注册 ===
    # from app.routers.business import order, product
    # app.include_router(order.router, prefix=f'{api_prefix}/order', tags=['业务模块/订单管理'])
```

### 1.5 视图文件拆分规范（强制）

#### 1.5.1 拆分条件

| 条件 | 阈值 | 说明 |
|:-----|:-----|:-----|
| 单文件接口数 | > 10 个 | 必须拆分 |
| 单文件行数 | > 500 行 | 含注释和空行 |

#### 1.5.2 拆分原则

**按业务子模块拆分，不按接口类型拆分**：

```python
# ❌ 错误：按接口类型拆分
app/routers/user/list_view.py       # 所有 list 接口
app/routers/user/create_view.py     # 所有 create 接口

# ✅ 正确：按业务子模块拆分
app/routers/user/user_view.py       # 用户基础 CRUD
app/routers/user/address_view.py    # 用户地址相关
app/routers/user/profile_view.py    # 用户资料相关
```

#### 1.5.3 拆分后命名规范

| 场景 | 命名规则 | 示例 |
|:-----|:---------|:-----|
| 子模块接口少 | `{module}.py` | `user.py` |
| 子模块接口多 | `{module}_{sub}.py` | `user_address.py` |
| 继续拆分 | `{module}_{sub}_{func}.py` | `user_address_list.py` |

#### 1.5.4 拆分检查清单

| 检查项 | 要求 |
|:-------|:-----|
| 单文件接口数 | ≤ 10 |
| 单文件行数 | ≤ 500 |
| 拆分方式 | 按业务拆分，不按接口类型 |
| 命名规范 | 符合 1.5.3 命名规则 |

---

## 2. 路径管理规范（强制）

### 2.1 禁止使用 sys.path（强制）

**严格禁止**在代码中使用 `sys.path.insert`、`sys.path.append` 等方式动态修改路径。

```python
# ❌ 禁止这样做
import sys
sys.path.insert(0, '/path/to/module')
```

### 2.2 禁止硬编码绝对路径（强制）

**严格禁止**在代码中写死绝对路径。

```python
# ❌ 禁止这样做
config_path = '/app/config/config_dev.ini'
upload_dir = '/data/uploads'
```

### 2.3 统一使用 BASE_DIR（强制）

所有路径必须基于 `app.core.constants.BASE_DIR` 使用 `os.path.join` 拼接。

```python
# app/core/constants.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOGGING_BASE_DIR = os.path.join(BASE_DIR, 'logs')

# ✅ 正确做法
from app.core_constants import BASE_DIR
config_path = os.path.join(BASE_DIR, 'config', 'config_dev.ini')
```

---

## 3. FastAPI 应用工厂（强制）

### 3.1 完整应用工厂（强制）

> FastAPI 用 `lifespan` 上下文管理器替代 Flask 的 `before_first_request`。启动逻辑放 `yield` 之前，关闭逻辑放 `yield` 之后。

```python
# app/__init__.py
# FastAPI 应用工厂 + 路由/中间件/异常/OpenAPI 配置入口

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import config, admin_mysql_conf
from app.db.mysql.session import async_engine
from app.db.redis.client import redis_client
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_log import RequestLogMiddleware
from app.routers import register_routers
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期（FastAPI 等价 Flask before_first_request / teardown_appcontext）

    启动阶段：初始化数据库连接池 / Redis 连接池
    关闭阶段：释放连接
    """
    # === 启动 ===
    # 校验 SQLAlchemy async engine 已就绪（实际连接 lazy）
    # redis 客户端单例
    yield
    # === 关闭 ===
    await async_engine.dispose()
    await redis_client.aclose()


def create_app() -> FastAPI:
    """FastAPI 应用工厂"""
    app = FastAPI(
        title='API 文档',
        version='1.0.0',
        # v4.4.0+ 强制：description 字段禁用 8 类内容（HTTP 状态码 / 认证方式 / 错误码清单 / 响应结构 / 完整路径前缀 / 通用约束 / 路径内模块名 / summary 同义重复）
        description='FastAPI 后端服务的接口文档。',
        lifespan=lifespan,
        # §11.4 原生 OpenAPI 元数据
        openapi_tags=[
            {'name': '系统管理/认证管理', 'description': '用户登录、退出等认证相关接口'},
            {'name': '系统管理/用户管理', 'description': '用户信息管理接口'},
        ],
    )

    # === 数据库配置 ===
    db_user = admin_mysql_conf.get('username')
    db_pass = admin_mysql_conf.get('password')
    db_host = admin_mysql_conf.get('host')
    db_port = admin_mysql_conf.get('port')
    db_name = admin_mysql_conf.get('db_name')
    db_charset = admin_mysql_conf.get('charset')

    if db_pass:
        database_url = f'mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset={db_charset}'
    else:
        database_url = f'mysql+aiomysql://{db_user}@{db_host}:{db_port}/{db_name}?charset={db_charset}'

    app.state.database_url = database_url
    app.state.debug = config.get('app', 'debug').lower() == 'true'

    # === CORS 跨域配置 ===
    cors_origins = config.get('cors', 'origins')
    cors_origins_list = '*' if cors_origins == '*' else [o.strip() for o in cors_origins.split(',')]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_list,
        allow_credentials=config.getboolean('cors', 'supports_credentials'),
        allow_methods=['GET', 'POST'],   # §1.H HTTP 方法白名单
        allow_headers=['*'],
    )

    # === GZip 压缩 ===
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # === 中间件（顺序敏感：request_id 必须在 request_log 之前） ===
    # FastAPI 中间件注册是栈式 LIFO（最后注册的最近请求），所以「先注册的后执行」
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # === 注册全局异常处理 ===
    register_exception_handlers(app)

    # === 注册路由 ===
    register_routers(app)

    return app
```

### 3.2 路由注册（强制）

`register_routers(app)` 内聚于 `app/routers/__init__.py`，所有 APIRouter 在该文件顶部导入，`app.include_router(router, prefix=..., tags=[...])` 等价 Flask `app.register_blueprint(bp, url_prefix=...)`。

---

## 4. 配置管理（强制）

### 4.1 配置加载器（强制）

> ⚠️ **强制要求：配置禁止使用默认值**
>
> 所有配置项**必须**从配置文件读取，**禁止**使用默认值 fallback。
>
> ❌ 错误示例：`config.getint('port', 8000)`、`config.get('debug', fallback=False)`
>
> ✅ 正确示例：`config.getint('port')`、`config.getboolean('debug')`
>
> 若配置文件缺失，程序应该**启动失败**而不是使用默认值。

```python
# app/core/config.py
import configparser
import os
from app.core.constants import BASE_DIR, ENV_TYPE


def get_config_path() -> str:
    config_dir = os.path.join(BASE_DIR, 'config')
    return os.path.join(config_dir, f'config_{ENV_TYPE}.ini')


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = get_config_path()
        if not os.path.exists(config_path):
            raise Exception(f'配置文件<{config_path}>不存在')
        self._config = configparser.ConfigParser()
        self._config.read(config_path, encoding='utf-8')

    def get(self, section, key=None, fallback=None):
        if key is None:
            key = section
            section = 'app'
        return self._config.get(section, key, fallback=fallback)

    def getint(self, section, key=None, fallback=None):
        if key is None:
            key = section
            section = 'app'
        return self._config.getint(section, key, fallback=fallback)

    def getboolean(self, section, key=None, fallback=None):
        if key is None:
            key = section
            section = 'app'
        return self._config.getboolean(section, key, fallback=fallback)


config = Config()
admin_mysql_conf = config.items('admin_mysql')
admin_redis_conf = config.items('admin_redis')
app_conf = config
```

> ⚠️ **本技能禁止使用环境变量（强制）**
>
> 所有配置统一通过 `Config.get()` / `Config.items()` 读取（业务代码禁止传 fallback），`app/routers/` / `app/services/` / `app/db/` / `app/schemas/` 目录下禁止 `import os` 后调用 `os.environ.*` 或 `os.getenv(...)`。

### 4.2 配置文件格式（强制）

> ⚠️ **配置文件选择机制（强制）**
>
> 配置文件的加载由 `ENV_TYPE` 变量控制（取值顺序由命令行参数 `--dev` / `--test` / `--prod` 决定）：
> - `ENV_TYPE='dev'` → 加载 `config_dev.ini`
> - `ENV_TYPE='test'` → 加载 `config_test.ini`
> - `ENV_TYPE='prod'` → 加载 `config_prod.ini`

配置文件结构与通用后端项目一致。FastAPI 栈额外需要：

```ini
[app]
host = 0.0.0.0
# debug = true   # dev
# debug = false  # test/prod
port = 8000

[uvicorn]
# uvicorn workers 数（生产用 Gunicorn + uvicorn worker 时此段不生效）
workers = 1

[swagger]
# 仅非生产环境的 Basic Auth 凭据；缺失即崩溃
user = <部署时填入的强密码>
password = <部署时填入的强密码>
```

---

## 5. 中间件（强制）

### 5.1 请求 ID 中间件（强制）

> FastAPI 用 `BaseHTTPMiddleware` 子类，等价 Flask `@app.before_request` + `@app.after_request` 组合。

```python
# app/middleware/request_id.py

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求 ID 中间件（强制基线）"""

    HEADER_NAME = 'X-Request-ID'
    CONTEXT_ATTR = 'request_id'

    async def dispatch(self, request: Request, call_next):
        # 优先复用上游 X-Request-ID（便于跨服务追踪），否则生成新 UUID
        request_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[self.HEADER_NAME] = request_id
        return response
```

### 5.2 全局请求日志中间件（强制）

```python
# app/middleware/request_log.py

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.loggings.loggings import request_log   # 脱敏/截断由封装层 JsonFormatter 统一兜底

SKIP_PREFIXES = ('/static', '/openapi.json', '/docs', '/redoc')


class RequestLogMiddleware(BaseHTTPMiddleware):
    """全局请求日志中间件（强制基线）"""

    async def dispatch(self, request: Request, call_next):
        start = time.time()

        if request.url.path.startswith(SKIP_PREFIXES):
            return await call_next(request)

        request.state.request_id = getattr(request.state, 'request_id', '-')

        extra = {
            'log_type': 'request',
            'phase': 'before',
            'method': request.method,
            'path': request.url.path,
            'ip': request.client.host if request.client else '-',
        }

        if request.query_params:
            extra['query'] = dict(request.query_params)

        if request.method in ('POST', 'PUT', 'PATCH'):
            body_bytes = await request.body()
            if body_bytes:
                try:
                    import json
                    extra['body'] = json.loads(body_bytes)
                except Exception:
                    extra['body'] = '<unparsable>'

        request_log.info('请求开始', extra=extra)

        response = await call_next(request)

        cost_ms = round((time.time() - start) * 1000, 2)
        status = response.status_code

        extra_after = {
            'log_type': 'request',
            'phase': 'after',
            'method': request.method,
            'path': request.url.path,
            'status_code': status,
            'cost_ms': cost_ms,
        }

        # 状态码自动映射级别（2xx/3xx=INFO，4xx=WARNING，5xx=ERROR）
        level = 'error' if status >= 500 else ('warning' if status >= 400 else 'info')
        getattr(request_log, level)('请求结束', extra=extra_after)
        return response
```

> **复用优先**：FastAPI 栈**禁止**重写一份日志封装。日志封装层对外暴露 `mask_sensitive` / `get_logger` / `JsonFormatter`，直接复用 Flask 栈的实现，仅需把 `ContextFilter` 的 `flask.g` 依赖替换为 `contextvars.ContextVar`（见 §6.1）。

---

## 6. 日志规范（强制）

> **本节为 FastAPI 实现层**。完整的日志类型分类、字段 schema、大内容处理、脱敏规则、轮转与免压缩窗口、级别紧凑打印、控制台走 stdout、默认无颜色等铁律集中于顶层日志规范文档。
>
> **本节只保留 3 件事**：
> 1. `app/loggings/loggings.py` 封装类（替换 Flask `gl` 为 `ContextVar`，其余完全沿用）
> 2. 全局请求日志中间件 `app/middleware/request_log.py` 的实现
> 3. 免压缩窗口与清理函数的配置/调用方式

### 6.0 分文件维度：按 type 切，不按级别切（强制）

按业务 `type` 切分（`biz.log` / `audit.log` / `request.log` / …），级别是 JSON `level` 字段；ERROR+ 额外聚合到 `error.log`。**禁止**按级别切文件（`xxx_info.log` / `xxx_error.log`）。

| 切分维度 | 结论 | 理由 |
|:---------|:-----|:-----|
| 按业务 **type** 切 | ✅ 采用 | 不同 type 的**保留期和采样率天然不同**（`audit` ≥180 天、`perf` 采样 1%） |
| 按 **级别**切成多份 | ❌ 禁止 | 级别是 JSON `level` 字段 + 一次查询；切文件会拆散同 `request_id` 链路 |
| **ERROR+ 聚合流** | ✅ 采用 | 唯一例外，同一条 ERROR 同时写 `{type}.log` 和 `error.log` |

### 6.1 日志封装类（强制）

```python
# app/loggings/loggings.py
# -*- coding: utf-8 -*-
"""
JSON 结构化日志封装（FastAPI 栈）

7 类固定 type / 字段 schema / 大内容截断 / 脱敏 / 输出与轮转。

FastAPI 栈与 Flask 栈差异点：ContextFilter 用 contextvars 替代 flask.g，
其他实现完全一致（按 DRY 原则禁止复制 Flask 实现后二次抽象）。
"""

import hashlib
import json
import logging
import os
import sys
import threading
from contextvars import ContextVar
from datetime import datetime

import colorlog
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler

from app.core.constants import LOGGING_BASE_DIR
from app.core.config import config

# === FastAPI 栈特有：contextvars 替代 flask.g ===
_request_id_var: ContextVar[str] = ContextVar('request_id', default='-')
_trace_id_var: ContextVar[str] = ContextVar('trace_id', default='-')
_span_id_var: ContextVar[str] = ContextVar('span_id', default='-')
_user_id_var: ContextVar[str] = ContextVar('user_id', default='-')


def set_request_id(value: str) -> None:
    """中间件入口调用"""
    _request_id_var.set(value)


def set_user_id(value: str) -> None:
    """鉴权 Depends 调用"""
    _user_id_var.set(value)


# === 配置（禁止 if DEBUG 硬编码在业务代码里）===
LOG_LEVEL = config.get('log', 'level', fallback='INFO').upper()
LOG_CONSOLE_JSON = config.getboolean('log', 'console_json', fallback=False)
LOG_CONSOLE_COLOR = config.getboolean('log', 'console_color', fallback=False)  # 默认关
LOG_LARGE_ENABLED = config.getboolean('log', 'large_enabled', fallback=False)
LOG_KEEP_UNCOMPRESSED = config.getint('log', 'keep_recent_uncompressed_days', fallback=7)

LOG_TYPES = ('biz', 'operation', 'audit', 'request', 'perf', 'schedule', 'exception')

SENSITIVE_FIELDS = {
    'password', 'pwd', 'passwd',
    'token', 'access_token', 'refresh_token',
    'secret', 'api_secret', 'client_secret',
    'api_key', 'apikey', 'app_key',
    'authorization', 'cookie', 'set-cookie',
    'id_card', '身份证', '身份证号',
    'phone', 'mobile', '手机号',
    'bank_card', '银行卡', '银行卡号',
    '统一社会信用代码',
}

MAX_FIELD_SIZE = 2048
MAX_FILE_BYTES = 200 * 1024 * 1024
CONSOLE_FORMAT = '%(asctime)s [%(levelname)s] [%(log_type)s] %(name)s - %(message)s'
LOG_COLORS_CONFIG = {'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow',
                     'ERROR': 'red', 'CRITICAL': 'bold_red'}

BACKUP_DAYS = {'audit': 180, 'exception': 90, 'error': 90}
DEFAULT_BACKUP_DAYS = 30

_RESERVED = frozenset(logging.LogRecord('', 0, '', 0, '', (), None).__dict__) | {
    'message', 'asctime', 'log_type', 'request_id', 'trace_id', 'span_id', 'user_id',
}

_LOGGER_CACHE = {}
_CACHE_LOCK = threading.Lock()


def _truncate(text, limit=MAX_FIELD_SIZE):
    raw = text.encode('utf-8')
    if len(raw) <= limit:
        return text
    head = raw[:int(limit * 0.75)].decode('utf-8', 'ignore')
    tail = raw[-int(limit * 0.25):].decode('utf-8', 'ignore')
    return (f'{head}...[TRUNCATED, original_size={len(raw)}, '
            f'sha256={hashlib.sha256(raw).hexdigest()}]...{tail}')


def mask_sensitive(data, limit=MAX_FIELD_SIZE):
    if isinstance(data, dict):
        return {k: ('******' if k.lower() in SENSITIVE_FIELDS else mask_sensitive(v, limit))
                for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [mask_sensitive(item, limit) for item in data]
    if isinstance(data, str):
        return _truncate(data, limit)
    return data


class ContextFilter(logging.Filter):
    """FastAPI 栈：从 ContextVar 自动注入链路上下文"""

    FIELDS = ('request_id', 'trace_id', 'span_id', 'user_id')

    def filter(self, record):
        for field in self.FIELDS:
            if not hasattr(record, field):
                if field == 'request_id':
                    setattr(record, field, _request_id_var.get())
                elif field == 'trace_id':
                    setattr(record, field, _trace_id_var.get())
                elif field == 'span_id':
                    setattr(record, field, _span_id_var.get())
                elif field == 'user_id':
                    setattr(record, field, _user_id_var.get())
        if not hasattr(record, 'log_type'):
            record.log_type = 'biz'
        return True


class JsonFormatter(logging.Formatter):
    """一行一 JSON 对象"""

    def format(self, record):
        payload = {
            'time': datetime.fromtimestamp(record.created).astimezone().isoformat(timespec='milliseconds'),
            'level': record.levelname,
            'type': getattr(record, 'log_type', 'biz'),
            'trace_id': getattr(record, 'trace_id', '-'),
            'msg': _truncate(record.getMessage()),
            'request_id': getattr(record, 'request_id', '-'),
            'span_id': getattr(record, 'span_id', '-'),
            'user_id': getattr(record, 'user_id', '-'),
            'module': record.name,
        }
        if record.exc_info:
            exc_cls, exc_obj = record.exc_info[0], record.exc_info[1]
            payload['exc_type'] = getattr(exc_cls, '__name__', '-')
            payload['exc_msg'] = str(exc_obj)
            payload['traceback'] = self.formatException(record.exc_info)
        extra = {k: v for k, v in record.__dict__.items() if k not in _RESERVED}
        if extra:
            payload['extra'] = mask_sensitive(extra)
        return json.dumps(payload, ensure_ascii=False, default=str)


def _file_handler(filename, level, formatter):
    handler = ConcurrentTimedRotatingFileHandler(
        os.path.join(LOGGING_BASE_DIR, filename),
        when='D', interval=1, encoding='utf-8',
        maxBytes=MAX_FILE_BYTES,
        use_gzip=False,        # 免压缩窗口
        backupCount=BACKUP_DAYS.get(filename.split('.')[0], DEFAULT_BACKUP_DAYS),
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def get_logger(log_type):
    if log_type not in LOG_TYPES:
        raise ValueError(f'非法日志类型 {log_type!r}，必须为 {LOG_TYPES} 之一')

    cached = _LOGGER_CACHE.get(log_type)
    if cached is not None:
        return cached

    with _CACHE_LOCK:
        if log_type in _LOGGER_CACHE:
            return _LOGGER_CACHE[log_type]

        logger = logging.getLogger(f'app.{log_type}')
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False

        if not logger.handlers:
            os.makedirs(LOGGING_BASE_DIR, exist_ok=True)
            logger.addFilter(ContextFilter())
            json_formatter = JsonFormatter()

            logger.addHandler(_file_handler(f'{log_type}.log', LOG_LEVEL, json_formatter))
            logger.addHandler(_file_handler('error.log', logging.ERROR, json_formatter))

            console = logging.StreamHandler(stream=sys.stdout)
            console.setLevel(LOG_LEVEL)
            if LOG_CONSOLE_JSON:
                console.setFormatter(json_formatter)
            elif LOG_CONSOLE_COLOR:
                console.setFormatter(colorlog.ColoredFormatter(
                    f'%(log_color)s{CONSOLE_FORMAT}', log_colors=LOG_COLORS_CONFIG, reset=True))
            else:
                console.setFormatter(logging.Formatter(CONSOLE_FORMAT))
            logger.addHandler(console)

        _LOGGER_CACHE[log_type] = logger
        return logger


def save_large(content, tag, extra=None):
    """大内容显式豁免落盘（线上默认关闭）"""
    raw = content if isinstance(content, bytes) else str(content).encode('utf-8')
    meta = {'tag': tag, 'original_size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    meta.update(extra or {})
    if not LOG_LARGE_ENABLED:
        get_logger('biz').info('大内容未落盘（LOG_LARGE_ENABLED=False）', extra=meta)
        return
    os.makedirs(LOGGING_BASE_DIR, exist_ok=True)
    date = datetime.now().astimezone().strftime('%Y-%m-%d')
    with open(os.path.join(LOGGING_BASE_DIR, f'large-{date}.log'), 'a', encoding='utf-8') as f:
        f.write(json.dumps({**meta, 'content': raw.decode('utf-8', 'ignore')}, ensure_ascii=False) + '\n')


# 预定义 logger（按 type，不按级别）
biz_log = get_logger('biz')
operation_log = get_logger('operation')
audit_log = get_logger('audit')
request_log = get_logger('request')
perf_log = get_logger('perf')
schedule_log = get_logger('schedule')
exception_log = get_logger('exception')
```

> **§6.1 与 Flask 栈实现层差异**：仅 `ContextFilter`（`flask.g` → `ContextVar`）+ 配置读取路径（`common.settings` → `app.core.config`）。其他完全一致——这是 mcpowers 复用优先于二次抽象铁律（v2.26.0+）的体现：**禁止**复制 Flask 实现后「看起来像」地换变量名。

### 6.2 调用方式（强制）

> **级别通过方法名表达（`logger.info` / `logger.error`），业务字段通过 `extra` 传**。禁止把 JSON 字符串拼进 `msg`。

```python
from app.loggings.loggings import biz_log, exception_log

# ✅ 正确：type 由 logger 决定，级别由方法决定，字段走 extra
biz_log.info('订单创建成功', extra={
    'log_type': 'biz',
    'biz_event': 'order.created',
    'biz_id': order.id,
})

# ✅ 正确：异常必带 traceback
try:
    create_order(data)
except Exception:
    exception_log.exception('订单创建失败', extra={
        'log_type': 'exception',
        'biz_event': 'order.created',
        'biz_id': data.get('order_id'),
    })
    raise

# ❌ 错误：把 JSON 字符串塞进 msg
biz_log.info(json.dumps({'biz_event': 'order.created'}))

# ❌ 错误：按级别取 logger
error_log = get_logger('error')      # ValueError：非 7 类之一
```

### 6.3 免压缩窗口与清理函数（强制）

与 Flask 栈一致——`compress_old_logs()` / `purge_old_logs()` 直接复用，仅需把 `app` 根目录识别改为 `BASE_DIR`。

---

## 7. 异常处理（强制）

### 7.1 全局异常处理（强制）

> FastAPI 用 `@app.exception_handler(ExceptionCls)` 注册，等价 Flask `@app.errorhandler(ExceptionCls)`。

```python
# app/core/exceptions.py

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.codes import get_error_message
from app.loggings.loggings import exception_log


class AppException(Exception):
    """业务异常基类"""
    def __init__(self, code: int, msg: str | None = None, status_code: int = 200):
        self.code = code
        self.msg = msg or get_error_message(code)
        self.status_code = status_code
        super().__init__(self.msg)


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={'code': exc.code, 'msg': exc.msg},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={'code': exc.status_code, 'msg': exc.detail or '请求错误'},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first = errors[0] if errors else {}
        msg = f"参数错误: {first.get('loc', ['?'])[-1] if first.get('loc') else '?'} {first.get('msg', '')}"
        return JSONResponse(
            status_code=200,
            content={'code': 400, 'msg': msg, 'data': {'errors': errors}},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        exception_log.exception('未捕获异常', extra={'path': request.url.path})
        return JSONResponse(
            status_code=500,
            content={'code': 500, 'msg': '服务器内部错误'},
        )
```

### 7.2 自定义异常（强制）

```python
from app.core.exceptions import AppException


class AuthExpiredException(AppException):
    def __init__(self):
        super().__init__(code=401, msg='登录已过期', status_code=401)


class PermissionDeniedException(AppException):
    def __init__(self):
        super().__init__(code=403, msg='无权限', status_code=403)


class NotFoundException(AppException):
    def __init__(self, resource: str = '资源'):
        super().__init__(code=404, msg=f'{resource}不存在', status_code=404)
```

---

## 8. 错误码（强制）

错误码常量集中于 `app/core/codes.py`，配套 `get_error_message(code)` 函数返回错误码对应的提示信息。

---

## 9. 响应规范（强制）

> FastAPI 业务接口直接返回 `dict`，由框架序列化为 JSON。**禁止**返回 `JSONResponse` 对象（破坏 FastAPI 的 response_model 校验）。

```python
# app/core/response.py

from app.core.codes import get_error_message


def api_success(data=None, msg: str = 'success', code: int = 0):
    """成功响应（返回 dict，由 FastAPI 序列化）"""
    response = {'code': code, 'msg': msg}
    if data is not None:
        response['data'] = data
    return response


def api_error(code: int, msg: str | None = None):
    """错误响应"""
    if msg is None:
        msg = get_error_message(code)
    return {'code': code, 'msg': msg}


def api_page(records, page_no: int, page_size: int, total_count: int):
    """分页响应"""
    total_page = (total_count + page_size - 1) // page_size if page_size > 0 else 0
    return {
        'code': 0,
        'msg': 'success',
        'data': {
            'records': records,
            'page_no': page_no,
            'page_size': page_size,
            'total_page': total_page,
            'total_count': total_count,
        },
    }
```

---

## 10. 认证授权（强制）

### 10.1 鉴权依赖（强制）

> FastAPI 用 `Depends(get_current_user)` 替代 Flask `@login_required` 装饰器。Token 校验逻辑与 Flask 栈一致（Redis 存正向键 + 反向 Set）。

```python
# app/core/deps.py

from typing import Annotated
from fastapi import Depends, Header

from app.core.exceptions import AuthExpiredException
from app.core.security import decode_token
from app.db.redis.client import redis_client
from app.core.constants import AdminRedisKeys
from app.loggings.loggings import set_user_id


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """鉴权 Depends：从 Authorization: Bearer {token} 解析用户身份

    Returns:
        dict: {'user_id': int, 'username': str}

    Raises:
        AuthExpiredException: token 缺失或已失效
    """
    if not authorization:
        raise AuthExpiredException()

    token = authorization.replace('Bearer ', '').strip()
    if not token:
        raise AuthExpiredException()

    # 校验 token（Redis 正向键）
    user_id = await redis_client.get(AdminRedisKeys.ADMIN_USER_TOKEN.format(token))
    if not user_id:
        raise AuthExpiredException()

    # 写入 ContextVar，供日志中间件自动注入 user_id
    set_user_id(str(user_id))

    return {'user_id': int(user_id), 'token': token}
```

### 10.2 权限依赖（强制）

```python
# app/core/deps.py（接续）

from app.core.codes import PERMISSION_DENIED
from app.core.exceptions import AppException


def require_permissions(*permission_codes: str):
    """权限校验 Depends 工厂"""
    async def _checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_id = current_user['user_id']

        # 查询用户角色与权限（同步 ORM 调用走 Depends(get_db) 拿 session）
        if not has_permission(user_id, permission_codes):
            raise AppException(code=PERMISSION_DENIED, msg='无权限')

        return current_user

    return _checker
```

### 10.3 Token 管理（Redis）（强制）

多端共存默认行为，正向键 `token → user_id` + 反向 Set `user_id → {token1, token2, ...}`：

```python
from app.db.redis.client import redis_client
from app.core.constants import AdminRedisKeys

# 生成新 token
token = generate_login_token(user.id, user.username)

# 正向键：token → user_id
await redis_client.set(AdminRedisKeys.ADMIN_USER_TOKEN.format(token), user.id, ex=86400)

# 反向 Set：user_id → {token1, token2, ...}
await redis_client.sadd(AdminRedisKeys.ADMIN_USER_TOKENS_BY_ID.format(user.id), token)
await redis_client.expire(AdminRedisKeys.ADMIN_USER_TOKENS_BY_ID.format(user.id), 86400)
```

---

## 11. OpenAPI 文档（FastAPI 原生）（强制）

> **要点**：FastAPI 用 Pydantic 模型 + `Field(description=...)` + `response_model` 自动生成 OpenAPI 3.0 spec，**不依赖任何第三方库**（如 Flasgger / apispec）。本节是 FastAPI 栈的核心差异章节。

### 11.1 原生 OpenAPI 配置（强制）

> ⚠️ **强制要求：先写 schema，再写路由**
>
> 每个接口必须**先在 Pydantic schema 中编写字段 `description` + `example`，再编写 router 函数**。
>
> **必含完整字段**：
> - Pydantic schema：每个字段 `Field(description=..., example=...)`
> - 路由函数：`summary` + `description`（≤ 100 字）+ `response_model` + `responses={...}` + 每个参数 `Query/Body(description=...)`

**仅非生产环境可用**：仅在开发/测试环境暴露 `/docs` 与 `/redoc`，生产环境自动禁用。

```python
# app/__init__.py
from fastapi import FastAPI
from app.core.constants import ENV_TYPE

def create_app() -> FastAPI:
    app = FastAPI(
        title='API 文档',
        version='1.0.0',
        docs_url='/docs' if ENV_TYPE != 'prod' else None,
        redoc_url='/redoc' if ENV_TYPE != 'prod' else None,
        openapi_url='/openapi.json' if ENV_TYPE != 'prod' else None,
    )
    return app
```

### 11.2 Pydantic Schema 强制基线

| 字段 | 必须 | FastAPI/Pydantic 落地 |
|:-----|:-----|:---------------------|
| `summary` | ✅ | 路由函数装饰器 `summary="用户登录"`（≤ 30 字） |
| `description` | ✅ | 路由函数装饰器 `description="..."`（≤ 100 字简短） |
| `parameters` | ✅ | 路由函数签名声明 `Query/Path/Body/Header/Form/File`，**每个含 `description` + `example`** |
| `responses` | ✅ | 路由函数装饰器 `responses={...}`，每个状态码含 `model`（Pydantic Schema） + `description` + `content`（example） |
| `tags` | ✅ | `app.include_router(router, tags=[...])` |

#### 11.2.1 参数（Query/Body）子字段强制项

| 子字段 | 必须 | 写法示例 |
|:-------|:-----|:---------|
| `description` | ✅ 强制 | `Query(..., description='页码，从 1 开始')`（**业务含义，不要复制字段名**） |
| `example` | ✅ 强制 | `Query(..., example=1)`（**必填**，前端可直接复制） |
| `ge` / `le` | 推荐 | `Query(1, ge=1, le=10000, description='页码', example=1)` |

#### 11.2.2 Pydantic Field 子字段强制项

```python
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求 schema"""
    username: str = Field(..., description='用户名（手机号也可以）', example='admin')
    password: str = Field(..., description='密码（MD5）', example='0192023a7bbd73250516f069df18b500')
```

| 子字段 | 必须 | 写法示例 |
|:-------|:-----|:---------|
| `description` | ✅ 强制 | `Field(..., description='业务含义')` |
| `example` | ✅ 强制 | `Field(..., example='具体值')` |
| `default` | 条件 | `Field(None, description='...')`（可选字段才有 default） |

#### 11.2.3 description 字段硬约束

| 约束 | 说明 |
|:-----|:-----|
| **字数** | ≤ 100 字 |
| **内容** | 只写接口**功能**（一句话） |
| **禁止** | 业务背景 / 前置条件 / 字段含义 / 错误码 / 副作用 |
| **禁止** | 写"待补充" / "TBD" / "TODO" |

> ✅ 正确：`description='使用用户名或手机号和密码登录，返回访问 token。'`
> ❌ 错误：300+ 字的"5 段式背景/前置/字段/错误/副作用"

### 11.3 路由函数签名强制格式

> ⚠️ **重要**：所有路由函数必须显式声明 `response_model`、`summary`、`description`、`responses`。**FastAPI 自动生成的 spec 不会含响应示例**，必须手工注入。

```python
# app/routers/system/auth.py

from fastapi import APIRouter
from app.schemas.system.auth import LoginRequest, LoginResponse
from app.schemas.common import BizResponse
from app.services.system.auth_service import login

router = APIRouter()


@router.post(
    '/login',
    summary='用户登录',
    description='使用用户名或手机号和密码登录，返回访问 token。',
    response_model=BizResponse[LoginResponse],
    responses={
        200: {
            'description': '登录成功',
            'content': {
                'application/json': {
                    'example': {
                        'code': 0,
                        'msg': 'success',
                        'data': {
                            'token': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6',
                            'user_id': 1,
                            'username': 'admin',
                        },
                    }
                }
            },
        }
    },
)
async def login_endpoint(body: LoginRequest):
    """路由函数实现"""
    return await login(body)
```

> **§1.H HTTP 方法白名单落地**：业务接口**仅允许** `POST`（创建类）/ `GET`（查询类）。**禁止** `@router.put(...)` / `@router.delete(...)` / `@router.patch(...)`——即使 FastAPI 原生支持。

### 11.4 OpenAPI 元数据与 Swagger UI

FastAPI 的 `FastAPI()` 构造参数支持完整的 OpenAPI 元数据：

```python
app = FastAPI(
    title='API 文档',
    version='1.0.0',
    description='FastAPI 后端服务的接口文档。',
    openapi_tags=[
        {'name': '系统管理/认证管理', 'description': '用户登录、退出等认证相关接口'},
        {'name': '系统管理/用户管理', 'description': '用户信息管理接口'},
    ],
)
```

**BearerAuth 全局声明**（v4.4.0+ 推荐）：

```python
# app/__init__.py 中追加 openapi_schema 自定义
from fastapi.openapi.utils import get_openapi


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # 注入 BearerAuth 安全方案
    openapi_schema['components']['securitySchemes'] = {
        'Bearer': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'JWT Token',
        }
    }
    # 全局默认应用（除显式 security=[] 外）
    openapi_schema['security'] = [{'Bearer': []}]
    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi
```

### 11.5 文档导出（强制）

**强制闭环**：改 schema → 重跑 `export_openapi.py` → 校验输出 → commit spec 文件。

#### 11.5.1 强制出口

每次改 Pydantic schema 后**必须**重跑导出：

```bash
# 在 FastAPI 项目根目录
python tools/export_openapi.py

# 输出：
#   openapi.json   ← 机器消费
#   api_docs.md    ← 人类阅读
```

**禁止**只改 schema 不重跑导出（这是 mcpowers 的 OpenAPI 文档 SSOT 铁律）。

#### 11.5.2 导出脚本最小实现

```python
# tools/export_openapi.py
# -*- coding: utf-8 -*-
"""
导出 OpenAPI spec：启动 FastAPI 应用 → 拉 /openapi.json → 写文件

FastAPI 已原生暴露 `/openapi.json` 与 `/docs`（Swagger UI）端点。导出脚本只需拉 schema 落盘：

```python
# tools/export_openapi.py
# -*- coding: utf-8 -*-
"""
导出 OpenAPI schema：拉 FastAPI 应用的 /openapi.json 写入 docs/API文档/ 目录。

依赖：项目根目录可被 import（即 app 包在 sys.path 中）。
输出：
  - openapi.json   （机器消费；前端 / SDK 生成）
  - openapi.md     （人类阅读；通过 json.dumps 简单占位；生产环境可替换为 fastapi-docs / 第三方 Markdown 渲染器）
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402  （必须在 sys.path 修改之后）


def main():
    app = create_app()
    schema = app.openapi()

    out_dir = PROJECT_ROOT / 'docs' / 'API文档'
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / 'openapi.json'
    json_path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    md_path = out_dir / 'openapi.md'
    md_path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),  # 占位；可换 Markdown 渲染器
        encoding='utf-8',
    )

    print(f'✔ openapi.json → {json_path}')
    print(f'✔ openapi.md   → {md_path}')


if __name__ == '__main__':
    main()
```

#### 11.5.3 强制闭环

```bash
# 提交前必跑
python tools/export_openapi.py
git diff docs/API文档/openapi.json   # 确认本次 schema 变更与代码意图一致
```

任何对 `app/schemas/**` 或路由 Pydantic 类型的修改，**必须**重跑导出，未跑即视为变更不完整。

---

## 12. API路径规范（强制）

> 📘 **通用规范**：`API规范.md` 第3章（基础语义适用于所有 Python 后端框架）。

**FastAPI 特定落地**：

```python
# @router.get('/xxx/list') 装饰器路径即 OpenAPI 路径模板
# §1.G 落地：路径模板禁止含 {xxx} 动态段；详情走 Query(..., alias='id')
router = APIRouter(prefix='/user', tags=['用户管理'])

@router.get('/list', summary='用户列表')          # ✅ 合规
@router.get('/detail')                            # ✅ 无动态段
@router.post('/webhook/callback/{source}')        # ✅ §1.G 例外白名单（callback）
async def webhook(source: str, request: Request): # source 通过函数参数注入
    ...
```

详情接口若需要 `id` 走 query：

```python
from fastapi import Query


@router.get('/detail', summary='用户详情')
async def user_detail(user_id: int = Query(..., alias='id', description='用户id', example=1)):
    ...
```

---

## 13. API参数命名规范（强制）

> 📘 **通用规范**：`API规范.md` 第4章。

**FastAPI 特定落地**：参数名通过 `Field(alias=...)` 或 `Query(alias=...)` 与外部字段名对齐；函数内部统一用 snake_case。

```python
from pydantic import BaseModel, Field


class ListQuery(BaseModel):
    """列表查询参数（OpenAPI 字段驼峰，函数内部蛇形）"""
    page_no: int = Field(default=1, alias='pageNo', description='页码', example=1)
    page_size: int = Field(default=10, alias='pageSize', description='每页条数', example=10)

    model_config = {'populate_by_name': True}  # 既能 by alias 也能 by field name 构造


@router.get('/list', summary='用户列表')
async def user_list(q: ListQuery = Query(...)):  # OpenAPI 自动渲染 pageNo / pageSize
    records = await svc.list_users(page=q.page_no, size=q.page_size)
    ...
```

---

## 14. 参数验证（强制）

> 📘 **通用规范**：`API规范.md` 第5章。

### 14.1 Pydantic 参数验证（强制）

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CreateUserBody(BaseModel):
    """创建用户 body（POST 必 application/json；§1.K 落地）"""
    username: str = Field(..., min_length=3, max_length=20, description='用户名', example='zhangsan')
    email: str = Field(..., pattern=r'^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$', description='邮箱', example='zhangsan@company.com')
    age: int = Field(..., ge=0, le=150, description='年龄', example=25)
    department_id: Optional[int] = Field(default=None, description='部门 id', example=100)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v[0].isalpha():
            raise ValueError('用户名必须以字母开头')
        return v


@router.post('/create', summary='创建用户', response_model=BizResponse[dict])
async def create_user(body: CreateUserBody):
    """创建用户（§1.K 强制 JSON）"""
    user_id = await svc.create_user(**body.model_dump())
    return BizResponse(data={'id': user_id})
```

**§1.K POST 强制 JSON 落地**：所有业务 POST 接口接收 Pydantic BaseModel（FastAPI 默认渲染 `application/json`），严禁 `Form(...)` / `File(...)` 滥用（仅 upload / attachment / import / webhook / callback / notify / oauth 路径段可用 multipart）。

---

## 15. 辅助函数（强制）

### 15.1 密码处理（强制）

```python
# app/utils/security.py

import hashlib


def hash_password(password: str) -> str:
    """MD5 加密（与 Flask utils/helpers.py 行为等价）"""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return hash_password(password) == hashed
```

> 💡 **复用优先于二次抽象（v2.26.0+）**：若项目已有 `utils/security.py` 等价实现，禁止在 FastAPI 项目里重新包一层；如需异步版本（`async def`），可放到 `app/services/auth.py` 复用 `hash_password` 而非复制。

### 15.2 Token生成（强制）

```python
# app/utils/security.py

import uuid
import time
import hashlib


def generate_token(length: int = 32) -> str:
    """生成随机 token"""
    return str(uuid.uuid4()).replace('-', '')[:length]


def generate_login_token(user_id: int, username: str) -> str:
    """生成登录 token"""
    timestamp = str(int(time.time()))
    random_str = generate_token(8)
    raw = f'{user_id}:{username}:{timestamp}:{random_str}'
    return hashlib.sha256(raw.encode()).hexdigest()
```

### 15.3 验证码生成（强制）

```python
# app/utils/security.py

import random
from PIL import Image, ImageDraw, ImageFont


def generate_captcha(length: int = 4) -> str:
    """生成验证码字符串"""
    chars = 'abcdefghjkmnpqrstuvwxy3456789'
    return ''.join(random.choice(chars) for _ in range(length))


def generate_captcha_image(code: str) -> Image.Image:
    """生成验证码图片"""
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), code, fill=(0, 0, 0), font=font)
    # 添加干扰线、噪点（业务可选）
    return image
```

---

## 16. Excel导入导出（强制）

> 📘 **通用规范**：`API规范.md` 第7章。

### 16.1 FastAPI 特定实现（强制）

```python
# app/modules/user/views.py
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from openpyxl import load_workbook, Workbook

router = APIRouter(prefix='/user', tags=['用户管理'])


@router.post(
    '/import',
    summary='批量导入用户',
    response_model=BizResponse[dict],
)
async def import_users(
    file: UploadFile = File(..., description='xlsx 文件'),
) -> BizResponse:
    """
    批量导入用户

    多部分表单数据：路径段含 import，走 §1.K multipart 例外。
    响应结构：total / success / fail / errors[]。
    """
    if not file.filename or not file.filename.endswith('.xlsx'):
        return BizResponse(code=400, msg='请上传 .xlsx 格式文件')

    wb = load_workbook(filename=BytesIO(await file.read()), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    total, success, fail, errors = await svc.import_users(rows)
    return BizResponse(data={'total': total, 'success': success, 'fail': fail, 'errors': errors})


@router.get(
    '/export',
    summary='导出用户列表',
    response_class=StreamingResponse,
)
async def export_users(
    status: int | None = Query(default=None, description='状态筛选', example=1),
):
    """
    导出用户列表为 Excel 文件流。
    """
    wb = Workbook()
    ws = wb.active
    ws.append(['id', 'username', 'email'])
    async for row in svc.iter_users(status=status):
        ws.append([row.id, row.username, row.email])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=users.xlsx'},
    )
```

---

## 17. CORS跨域（强制）

> **§1.H HTTP 方法白名单落地**：CORS `allow_methods` 必须收紧到 `['GET', 'POST']`——业务接口禁 PUT / PATCH / DELETE / HEAD / OPTIONS。

```python
# app/__init__.py 中 create_app() 末尾追加

from fastapi.middleware.cors import CORSMiddleware
from app.core.config import app_conf


def _setup_cors(app: FastAPI) -> None:
    """CORS 配置（§1.H 收紧 allow_methods）"""
    cors_origins = app_conf.get('cors', 'origins')
    origins_list = (
        ['*'] if cors_origins == '*'
        else [o.strip() for o in cors_origins.split(',')]
    )
    supports_credentials = app_conf.getboolean('cors', 'supports_credentials')

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins_list,
        allow_credentials=supports_credentials,
        allow_methods=['GET', 'POST'],   # §1.H 铁律
        allow_headers=['*'],
    )
```

---

## 18. Uvicorn + Gunicorn 部署（强制）

> ⚠️ **技术锁定**：FastAPI 是 ASGI 应用，必须用 ASGI 服务器部署——生产推荐 **Gunicorn + uvicorn.workers.UvicornWorker** 组合；开发环境用 `uvicorn --reload` 即可。

### 18.1 Worker Class 选择（强制）

| Worker Class | 特点 | 适用场景 |
|:-------------|:-----|:---------|
| **uvicorn**（开发） | 单进程，自动 reload | 开发环境 |
| **UvicornWorker**（生产） | Gunicorn 多进程管理 + Uvicorn ASGI worker | 生产环境 |

> ⚠️ **强制要求**：所有 FastAPI 项目生产环境必须使用 `uvicorn.workers.UvicornWorker`，不允许用 sync 阻塞 worker。

### 18.2 启动器（强制）

```python
# gunicorn_loader.py
# -*- coding: utf-8 -*-
"""Gunicorn 启动器（生产环境使用 UvicornWorker）。"""

import multiprocessing
from gunicorn.app.base import BaseApplication
from uvicorn.workers import UvicornWorker

from app.core.config import app_conf  # 应用配置
from app.core.constants import ENV_TYPE  # 环境类型
from app import create_app


def create_application():
    """创建 ASGI 应用实例"""
    return create_app()


class StandaloneApplication(BaseApplication):
    """Gunicorn 独立应用封装。"""

    def __init__(self, options=None):
        self.options = options or {}
        super().__init__()

    def load_config(self):
        """加载 Gunicorn 配置"""
        if ENV_TYPE == 'dev':
            workers = 2
        else:
            workers = (multiprocessing.cpu_count() * 2) + 1

        config = {
            'bind': f'{app_conf.get("host")}:{app_conf.getint("port")}',
            'worker_class': UvicornWorker,  # 强制使用 UvicornWorker
            'workers': workers,
            'timeout': 60,
            'keepalive': 5,
            'max_requests': 1000,
            'max_requests_jitter': 100,
            'graceful_timeout': 30,
            'accesslog': '-',
            'errorlog': '-',
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        """返回 ASGI 应用"""
        return create_application()


# 模块级 app 实例（供 gunicorn 导入：gunicorn gunicorn_loader:app）
app = create_application()


if __name__ == '__main__':
    StandaloneApplication().run()
```

**启动命令**：

```bash
# 生产 / 测试
python -u gunicorn_loader.py --prod
python -u gunicorn_loader.py --test

# 开发（自动 reload）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 19. 环境类型（强制）

> 🚧 **本技能禁止使用环境变量（v2.25.0+ 全栈适用最高铁律）**——配置走文件 + 加载器；环境类型通过命令行参数切换（与 Flask 一致）。

```python
# app/core/constants.py

import sys

ENV_TYPE = 'dev'  # 默认开发环境
sys_args = sys.argv[1:]
if sys_args:
    # 三个环境参数都显式识别，顺序：--dev > --test > --prod
    if '--dev' in sys_args:
        ENV_TYPE = 'dev'
    elif '--test' in sys_args:
        ENV_TYPE = 'test'
    elif '--prod' in sys_args:
        ENV_TYPE = 'prod'

IS_PRODUCT = ENV_TYPE == 'prod'
```

```bash
# 生产
python -u gunicorn_loader.py --prod

# 测试
python -u gunicorn_loader.py --test

# 开发（推荐 uvicorn --reload）
uvicorn app.main:app --reload
```

---

## 20. 规范执行检查清单（强制）

### 20.1 接口开发时必查（强制）

| 检查项 | 要求 |
|:-------|:-----|
| **Pydantic Schema 5 字段** | tags / summary (≤30) / description (≤100) / parameters（每个含 description + example）/ responses.200（schema + examples）任一缺失视为不完整（铁律） |
| **§1.G 路径禁动态参数** | `@router.get` 装饰器路径模板禁含 `{xxx}`；详情走 `Query(..., alias='id')`；例外 webhook / oauth / callback |
| **§1.H HTTP 方法白名单** | 仅用 `@router.get` / `@router.post`；禁 `@router.put` / `@router.delete` / `@router.patch` / `@router.head` / `@router.options` |
| **§1.I description 禁鉴权字眼** | description / parameters[].description / responses[].description 不重述 JWT / Bearer / 需登录 / 需鉴权等 15 类字眼；鉴权由 OpenAPI `securitySchemes` + 全局 `security` 自动应用 |
| **§1.J description 禁错误码清单** | 不罗列「10001 用户不存在」清单；错误码由 `BizResponse` 字段 `code` 表达 |
| **§1.K POST 必 JSON** | 业务 POST 强制 `application/json`；仅路径段 upload / attachment / import / webhook / callback / notify / oauth 可走 multipart |
| **§4.A description 8 类禁用** | 不写 HTTP 状态码 / 认证方式 / 错误码清单 / 响应结构 / 完整路径 / 通用约束 / 路径模块名 / summary 同义重复——删掉看能否调通 |
| **字段命名** | 单资源接口用 `id`，关联表用 `xxx_id`（小写，OpenAPI 字段通过 `alias` 渲染驼峰） |
| **Pydantic 校验** | 所有 Body / Query 用 `BaseModel + Field`；必填用 `...`，可选 `Optional[T] = None`；边界用 `ge` / `le` / `min_length` / `max_length` / `pattern` |
| **导入接口** | 返回结构含 `total` / `success` / `fail` / `errors` |
| **导出接口** | 用 `StreamingResponse` + `media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'` |
| **模板下载** | 模板列名与需求文档字段含义一致 |

### 20.2 提交前必查（强制）

| 检查项 | 要求 |
|:-------|:-----|
| **OpenAPI schema 已导出** | 已跑 `python tools/export_openapi.py`，`git diff docs/API文档/openapi.json` 无意外变更 |
| **接口字段命名** | 符合 **§13 API参数命名规范** |
| **Pydantic 描述** | 符合 **§11 Pydantic Schema 强制基线** |
| **校验规则** | 符合 **§14 Pydantic 参数验证** |
| **导入导出** | 符合 **§16 Excel导入导出** |
| **代码无冗余** | 无重复定义、无调试 `print` 残留、无未用 import |

### 20.3 配置管理必查（强制）

| 检查项 | 要求 |
|:-------|:-----|
| **环境变量** | 禁用 `os.environ` / `os.getenv` / `from os import environ`；配置走文件 + 加载器（v2.25.0+ 铁律） |
| **Pydantic 零陷阱** | `BaseModel` 类内不调用业务 DB；DB 操作放 `services/` 层（v2.27.0+ 解耦边界） |
| **复用优先** | 写新工具函数前已扫描仓库 + SDK + 通用模块等价实现（v2.26.0+ 铁律） |
| **import 顶层** | Python import 必须在模块顶部；函数内 / 类内 / 装饰器内 / 条件块内禁局部 import（v2.27.0+ 铁律） |
| **控制台日志紧凑 + stdout** | `%(levelname).1s` 或 `%(levelname)s`；`StreamHandler(stream=sys.stdout)`（v2.28.4+ 铁律） |
| **控制台默认无颜色** | 默认走 plain Formatter；颜色开关不区分 dev/test/prod；模块内置日志工厂硬编码默认即合规（v2.29.2+ 铁律） |

### 20.4 接口文档字眼规范（v4.3.0+ 强制）

- 接口 Pydantic `Field.description` / 路由 `description` **禁用** 22 类画蛇添足字眼
- 共享字眼清单：`mcpowers-shared/docs/_assets/_forbidden_ref_words.txt`
- 含禁用字眼即走智能二分判定：外部权威（RFC / PEP / W3C 等）→ 放行；内部规范名 / 项目内路径 / `.md` 文档 → 拦截
- docstring 降级为 WARNING（避免整段 ERROR 阻塞）
- 一键扫描：`python mcpowers-shared/scripts/check_no_ref_words.py app/schemas/`

### 20.5 接口路由函数格式（强制）

```python
# ✅ 推荐格式（FastAPI 路由装饰器内就近声明 schema 与 response_model）
@router.post(
    '/create',
    tags=['用户管理'],
    summary='创建用户',
    description='创建新用户并返回 id',
    response_model=BizResponse[dict],
)
async def create_user(body: CreateUserBody) -> BizResponse:
    """路由函数体。"""
    user_id = await svc.create_user(body)
    return BizResponse(data={'id': user_id})


# ❌ 反例：业务接口用 @router.delete（违反 §1.H）
@router.delete('/delete/{user_id}')
async def delete_user(user_id: int):
    ...
```

---

## 附录

### A. 相关文档（强制）

| 文档 | 位置 |
|:-----|:-----|
| **API 通用规范** | `API规范.md` |
| **数据库规范** | `数据库规范.md` |
| **缓存规范** | `缓存规范.md` |
| **定时任务规范** | `定时任务规范.md` |
| **部署规范** | `部署规范.md` |
| OpenAPI 元数据 / Swagger UI 注入 | `app/__init__.py` 中 `custom_openapi()` |
| OpenAPI 导出脚本 | `tools/export_openapi.py` |
| 导出后 OpenAPI schema | `docs/API文档/openapi.json` |
| 导出后 Markdown | `docs/API文档/openapi.md` |

### B. 标签对照表（强制）

> 📘 **通用规范**：`API规范.md` 第9章。

---

## 21. Docker容器化（强制）

> 💡 **本地开发**：FastAPI 项目的三套 docker-compose 文件结构与 Flask 项目**完全一致**——直接复用 `Flask后端规范.md §21.1-21.6` 即可（极简版 + 三环境差异对照表）。仅 `command:` 字段改 `gunicorn_loader.py --{env}`，其他不变。

下面给出 FastAPI 栈的差异点速查：

| 差异点 | Flask | FastAPI |
|:-------|:------|:--------|
| 进程模型 | sync（WSGI） | async（ASGI） |
| Server | Gunicorn + GeventWebSocketWorker | Gunicorn + uvicorn.workers.UvicornWorker |
| Server class | `GeventWebSocketWorker` | `UvicornWorker` |
| command | `python -u gunicorn_loader.py --{env}` | `python -u gunicorn_loader.py --{env}`（相同） |

启动命令、`.gitignore`、`docker-data/` 目录、`config/config_{env}.ini` 等三套环境的写法**完全沿用** `Flask后端规范.md` §21 节，不再重复。

---

## 22. v4.5.x 接口契约铁律落地（强制）

> ✅ **本规范是 v4.5.x OpenAPI 文档铁律的 FastAPI 栈级落地**。

**v4.5.x OpenAPI 文档四铁律**：

| 铁律 | 条款 | FastAPI 落地 |
|:-----|:-----|:-------------|
| **§1.G** | 路径禁动态参数 | 装饰器路径不含 `{xxx}`；详情走 Query alias；例外 webhook / oauth / callback |
| **§1.H** | HTTP 方法白名单 | 仅 GET / POST；禁 PUT / DELETE / PATCH / HEAD / OPTIONS |
| **§1.I** | description 禁鉴权字眼 | 不重述 JWT / Bearer / 需登录等 15 类字眼；鉴权由 OpenAPI 全局 securitySchemes 自动应用 |
| **§1.J** | description 禁错误码清单 | 不罗列「10001 用户不存在」清单；错误码由 BizResponse.code 字段表达 |

**v4.5.1 §1.K POST 强制 JSON**：业务 POST 走 Pydantic BaseModel；仅 UploadFile 例外。

**v4.4.0 description 8 类禁用**：状态码 / 认证方式 / 错误码清单 / 响应结构 / 完整路径前缀 / 通用约束 / 路径模块名 / summary 同义重复——判别口诀：删掉看能否调通。

**v4.4.0 SSOT 收敛**：通用响应 BizResponse / 分页 PageResponse / 文件 FileResponse 等在 app/schemas/common.py 定义一次；response_model 字段复用。

**栈级落地**：
- 创建 Pydantic Schema 时直接用 BaseModel + Field + response_model
- 写 description 字段时跳过 22 类画蛇添足字眼
- 写完 schema 后必跑 export_openapi.py
- 提交前用 check_no_ref_words.py 扫 schemas/ 一遍

**审查门禁**：mcpowers-code-review R13-R23 已包含 Pydantic 5 字段不完整 / 业务误列 4xx / 画蛇添足字眼 / description 8 类 / components/schemas 未复用 / HTTP 方法越界 / POST 非 JSON 等反模式条目。

---

**版本演进**：v1.0（2026-08-25）首发。本规范镜像 Flask后端规范.md v1.2 的 22 章节结构，框架绑定部分替换为 FastAPI 原生实现（lifespan / Depends / APIRouter / Pydantic + 原生 OpenAPI）。
```