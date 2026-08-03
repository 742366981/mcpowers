---
title: Flask后端规范
type: tech-spec
applies_to: [Flask后端]
priority: required
version: 1.1
last_updated: 2026-07-31
---

# Flask后端项目规范

本文档定义 Flask 后端项目的特定规范，Flask 特有的内容（如应用工厂、蓝图、装饰器等）详见本章。

> ⚠️ **通用规范引用**：数据库、缓存、定时任务、部署等通用内容详见各自独立规范文档：
> - `数据库规范.md`
> - `缓存规范.md`
> - `定时任务规范.md`
> - `部署规范.md`

---

## 0. 接口类型速查表（最高频使用）

> **目的**：AI 写接口时**先看本表**确定类型，再跳转到对应章节。

### 0.1 标准 CRUD（7 类）

| 接口类型 | HTTP 方法 | 路径 | 请求位置 | 关键参数 | 响应 | 详细章节 |
|:---------|:----------|:-----|:---------|:---------|:-----|:---------|
| **list（列表）** | GET | `/{前缀}/{模块}/list` | query | `page_no`, `page_size`, 筛选条件 | 分页结构 | 详见 `API规范.md` 3.2 / 8.1 |
| **detail（详情）** | GET | `/{前缀}/{模块}/detail` | query | `id` | 本表字段+关联 | 详见 `API规范.md` 8.2 |
| **create（创建）** | POST | `/{前缀}/{模块}/create` | body | 本表字段 | `{code:0, data:{id:x}}` | 详见 `API规范.md` 8.3 |
| **update（更新）** | POST | `/{前缀}/{模块}/update` | body | `id` + 待更新字段 | `{code:0, msg:"更新成功"}` | 详见 `API规范.md` 8.3 |
| **delete（删除）** | POST | `/{前缀}/{模块}/delete` | body | `id` | `{code:0, msg:"删除成功"}` | 详见 `API规范.md` 8.4 |
| **batch-delete（批量删除）** | POST | `/{前缀}/{模块}/batch-delete` | body | `ids: []` | `{code:0, msg:"删除成功"}` | 详见 `API规范.md` 8.4 |
| **update-status（状态修改）** | POST | `/{前缀}/{模块}/update-status` | body | `id`, `status` | `{code:0, msg:"修改成功"}` | 详见 `API规范.md` 8.5 |

### 0.2 文件相关（4 类）

| 接口类型 | HTTP 方法 | 路径 | 请求位置 | 关键参数 | 响应 | 详细章节 |
|:---------|:----------|:-----|:---------|:---------|:-----|:---------|
| **upload（文件上传）** | POST | `/{前缀}/upload` | formData | `file` | `{code:0, data:{url}}` | 详见 `API规范.md` 8.6 |
| **import（批量导入）** | POST | `/{前缀}/{模块}/import` | formData | `file` (.xlsx/.csv) | `{total, success, fail, errors[]}` | 详见 `导入导出规范.md` 8 |
| **export（数据导出）** | GET | `/{前缀}/{模块}/export` | query | 筛选条件 | Excel 文件流 | 详见 `导入导出规范.md` 10 |
| **template/download（模板下载）** | GET | `/{前缀}/{模块}/template/download` | - | 无 | Excel 模板文件 | 详见 `导入导出规范.md` 11 |

### 0.3 字典相关（2 类）

| 接口类型 | HTTP 方法 | 路径 | 请求位置 | 关键参数 | 响应 | 详细章节 |
|:---------|:----------|:-----|:---------|:---------|:-----|:---------|
| **dict（下拉）** | GET | `/{前缀}/{模块}/dict?type={type}` | query | `type`（字典类型） | `[{dictCode, dictLabel, dictValue, ...}]` | 详见 `API规范.md` 3.3 |
| **dict/cascader（级联下拉）** | GET | `/{前缀}/{模块}/dict/cascader?type={type}` | query | `type` | 树形 `[{label, value, children[]}]` | 详见 `API规范.md` 3.4 |

### 0.4 认证相关（2 类，由 system/auth 子模块负责）

| 接口类型 | HTTP 方法 | 路径 | 请求位置 | 关键参数 | 响应 | 详细章节 |
|:---------|:----------|:-----|:---------|:---------|:-----|:---------|
| **login（登录）** | POST | `/{前缀}/auth/login` | body | `username`, `password` | `{token, user_id, username}` | 详见 10.1 |
| **logout（退出）** | POST | `/{前缀}/auth/logout` | header | `Authorization: Bearer {token}` | `{code:0}` | 详见 10.1 |

### 0.5 健康检查（1 类，新增）

| 接口类型 | HTTP 方法 | 路径 | 响应 | 详细章节 |
|:---------|:----------|:-----|:-----|:---------|
| **health（健康检查）** | GET | `/health` | `{status:"ok", db:"ok", redis:"ok"}` | 详见 `健康检查规范.md` |

### 0.6 接口命名反查（看到路径能识别类型）

```
GET  /xxx/list                    → list 接口
GET  /xxx/detail?id=1             → detail 接口
POST /xxx/create                  → create 接口
POST /xxx/update                  → update 接口
POST /xxx/delete                  → delete 接口
POST /xxx/batch-delete            → batch-delete 接口
POST /xxx/update-status           → update-status 接口
POST /xxx/import                  → import 接口（formData 上传文件）
GET  /xxx/export?status=1         → export 接口（下载文件）
GET  /xxx/template/download       → template/download 接口
GET  /xxx/dict?type=status        → dict 接口
GET  /xxx/dict/cascader?type=...  → dict/cascader 接口
POST /upload                      → upload 接口（无业务模块）
```

---

## 1. 目录结构（强制）

### 1.1 整体目录结构

```
project/
├── apps/                              # 应用模块（蓝图）
│   ├── __init__.py                   # 应用工厂、蓝图注册
│   │
│   ├── system/                        # 系统管理模块
│   │   ├── __init__.py               # 蓝图注册
│   │   ├── auth/                      # 认证子模块（登录、退出、Token刷新）
│   │   │   ├── __init__.py
│   │   │   └── views.py
│   │   ├── user/                      # 用户子模块（用户CRUD、状态管理）
│   │   │   ├── __init__.py
│   │   │   └── views.py
│   │   ├── role/                      # 角色子模块（角色CRUD、角色分配）
│   │   │   ├── __init__.py
│   │   │   └── views.py
│   │   ├── permission/                # 权限子模块（权限项CRUD、权限分配）
│   │   │   ├── __init__.py
│   │   │   └── views.py
│   │   ├── menu/                      # 菜单子模块（菜单CRUD、菜单树）
│   │   │   ├── __init__.py
│   │   │   └── views.py
│   │   └── dict/                      # 字典子模块（字典类型、字典项）
│   │       ├── __init__.py
│   │       └── views.py
│   │
│   ├── operation/                      # 运营管理模块
│   │   ├── __init__.py               # 蓝图注册
│   │   └── log/                       # 日志子模块（操作日志、登录日志）
│   │       ├── __init__.py
│   │       └── views.py
│   │
│   ├── file/                          # 文件管理模块
│   │   ├── __init__.py               # 蓝图注册
│   │   └── upload/                    # 上传子模块（通用文件上传）
│   │       ├── __init__.py
│   │       └── views.py
│   │
│   └── business/                       # 业务模块（按需创建）
│       ├── __init__.py               # 蓝图注册
│       ├── order/                     # 订单模块
│       │   ├── __init__.py
│       │   └── views.py
│       └── product/                   # 商品模块
│           ├── __init__.py
│           └── views.py
│
├── common/                             # 公共模块
│   ├── __init__.py
│   ├── constants.py                   # 常量定义（BASE_DIR/RedisKey/ENV_TYPE）
│   ├── codes.py                       # 错误码定义
│   └── settings.py                    # 配置加载器
│
├── config/                             # 配置文件
│   ├── config_dev.ini                 # 开发环境
│   ├── config_test.ini                # 测试环境
│   └── config_prod.ini                # 生产环境
│
├── db/                                # 数据库相关
│   ├── mysql/
│   │   ├── __init__.py
│   │   ├── helpers.py                # SQLAlchemy实例、BaseModel
│   │   └── models/                   # 数据模型
│   └── redis/
│       ├── __init__.py
│       └── helpers.py                 # Redis客户端
│
├── utils/                              # 工具函数
│   ├── __init__.py
│   ├── responses.py                   # 统一响应
│   ├── decorators.py                  # 装饰器（login_required, permission_required）
│   ├── exceptions.py                  # 自定义异常
│   ├── validators.py                  # 参数验证
│   ├── helpers.py                     # 辅助函数
│   ├── middleware.py                  # 请求ID中间件
│   ├── request_log.py                 # 请求日志中间件
│   ├── loggings.py                    # 日志封装
│   └── scheduler.py                   # 定时任务调度器
│
├── docs/                               # 文档
│   └── swagger_template.md            # Swagger文档模板
│
├── tools/                             # 工具脚本
│   └── export_docs.py                 # 导出API文档脚本
│
├── db_init/                            # 数据库初始化
│   ├── init_all.py                    # 初始化所有表和数据
│   └── init_*.py                      # 其他初始化脚本
│
├── jobs/                             # 定时任务
│   ├── __init__.py
│   └── example.py                     # 示例任务
│
├── app.py                              # 应用入口
├── requirements.txt                    # 依赖
├── gunicorn_loader.py                  # Gunicorn启动器
├── Dockerfile                          # Docker镜像
├── docker-compose.dev.yml              # 开发环境
├── docker-compose.test.yml             # 测试环境
└── docker-compose.prod.yml             # 生产环境
```

### 1.2 模块划分规范

| 模块层级 | 模块名 | 说明 | 是否必须 |
|:---------|:-------|:-----|:--------|
| 一级 | `system/` | 系统管理：用户、角色、权限、菜单、字典、认证 | 必须 |
| 一级 | `operation/` | 运营管理：日志、监控 | 必须 |
| 一级 | `file/` | 文件管理：上传、附件 | 必须 |
| 一级 | `business/` | 业务模块：订单、商品等 | 按需扩展 |

### 1.3 子模块划分规范

**system/ 系统管理模块的子模块**：

| 子模块 | 职责 | 接口示例 |
|:-------|:-----|:---------|
| `auth/` | 认证管理 | 登录、退出、Token刷新、验证码 |
| `user/` | 用户管理 | 用户CRUD、状态管理、个人信息 |
| `role/` | 角色管理 | 角色CRUD、角色分配 |
| `permission/` | 权限管理 | 权限项CRUD、权限分配 |
| `menu/` | 菜单管理 | 菜单CRUD、菜单树 |
| `dict/` | 字典管理 | 字典类型CRUD、字典项CRUD |

**operation/ 运营管理模块的子模块**：

| 子模块 | 职责 | 接口示例 |
|:-------|:-----|:---------|
| `log/` | 日志管理 | 操作日志、登录日志、异常日志 |
| `monitor/` | 监控管理 | 在线用户、访问统计 |

**file/ 文件管理模块的子模块**：

| 子模块 | 职责 | 接口示例 |
|:-------|:-----|:---------|
| `upload/` | 文件上传 | 通用文件上传、图片上传 |
| `attachment/` | 附件管理 | 附件列表、附件删除 |

### 1.4 蓝图注册规范

```python
# apps/__init__.py

def register_blueprints(app):
    url_prefix = '/api'

    # system 模块
    from apps.system.auth.views import auth_bp
    from apps.system.user.views import user_bp
    from apps.system.role.views import role_bp
    from apps.system.permission.views import permission_bp
    from apps.system.menu.views import menu_bp
    from apps.system.dict.views import dict_bp

    app.register_blueprint(auth_bp, url_prefix=f'{url_prefix}/auth')
    app.register_blueprint(user_bp, url_prefix=f'{url_prefix}/user')
    app.register_blueprint(role_bp, url_prefix=f'{url_prefix}/role')
    app.register_blueprint(permission_bp, url_prefix=f'{url_prefix}/permission')
    app.register_blueprint(menu_bp, url_prefix=f'{url_prefix}/menu')
    app.register_blueprint(dict_bp, url_prefix=f'{url_prefix}/dict')

    # operation 模块
    from apps.operation.log.views import log_bp
    app.register_blueprint(log_bp, url_prefix=f'{url_prefix}/log')

    # file 模块
    from apps.file.upload.views import upload_bp
    app.register_blueprint(upload_bp, url_prefix=f'{url_prefix}/upload')

    # business 模块（按需注册）
    # from apps.business.order.views import order_bp
    # app.register_blueprint(order_bp, url_prefix=f'{url_prefix}/order')
```

### 1.5 视图文件拆分规范（强制）

#### 1.5.1 拆分条件

满足以下任一条件时，必须拆分文件：

| 条件 | 阈值 | 说明 |
|:-----|:-----|:-----|
| 单文件接口数 | > 10 个 | 必须拆分 |
| 单文件行数 | > 500 行 | 含注释和空行 |

#### 1.5.2 拆分原则

**按业务子模块拆分，不按接口类型拆分**：

```
# ❌ 错误：按接口类型拆分
apps/user/list_view.py      # 所有 list 接口
apps/user/create_view.py   # 所有 create 接口

# ✅ 正确：按业务子模块拆分
apps/user/user_view.py     # 用户基础 CRUD
apps/user/address_view.py  # 用户地址相关
apps/user/profile_view.py # 用户资料相关
```

#### 1.5.3 拆分后命名规范

| 场景 | 命名规则 | 示例 |
|:-----|:---------|:-----|
| 子模块接口少 | `{module}_view.py` | `user_view.py` |
| 子模块接口多 | `{module}_{sub}_view.py` | `user_address_view.py` |
| 继续拆分 | `{module}_{sub}_{func}_view.py` | `user_address_list_view.py` |

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

# ❌ 禁止这样做
file_path = 'D:\\project\\uploads\\file.xlsx'
```

### 2.3 统一使用 BASE_DIR（强制）

所有路径必须基于 `common.constants.BASE_DIR` 使用 `os.path.join` 拼接。

```python
# common/constants.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOGGING_BASE_DIR = os.path.join(BASE_DIR, 'logs')   # 日志根目录（§6.1 落盘于此）

# ✅ 正确做法
from common.constants import BASE_DIR
config_path = os.path.join(BASE_DIR, 'config', 'config_dev.ini')
```

---

## 3. Flask应用工厂（强制）

### 3.1 完整应用工厂（强制）

```python
# apps/__init__.py
# 应用工厂 + 蓝图/异常/Swagger 注册入口

from flask import Flask
from flask_compress import Compress
from flask_migrate import Migrate
from flask_cors import CORS

from common.settings import config
from db.mysql.helpers import db  # SQLAlchemy 实例（详见 数据库规范.md 第 2.2 节）

compress = Compress()
migrate = Migrate()


def create_app(protect_swagger=True):
    """Flask 应用工厂

    Args:
        protect_swagger: 是否启用 Swagger Basic Auth 保护（生产环境应传 False）

    Returns:
        Flask: 配置完毕的应用实例
    """
    app = Flask(__name__)

    # === 基础配置 ===
    app.config['SECRET_KEY'] = config.get('secret_key')
    app.config['DEBUG'] = config.get('debug').lower() == 'true'
    app.json.ensure_ascii = False  # 响应中文不转义

    # === 数据库配置 ===
    from common.settings import admin_mysql_conf
    db_user = admin_mysql_conf.get('username')
    db_pass = admin_mysql_conf.get('password')
    db_host = admin_mysql_conf.get('host')
    db_port = admin_mysql_conf.get('port')
    db_name = admin_mysql_conf.get('db_name')
    db_charset = admin_mysql_conf.get('charset')

    # 密码可空（本地无密码开发环境）
    if db_pass:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset={db_charset}'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}@{db_host}:{db_port}/{db_name}?charset={db_charset}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = app.config['DEBUG']  # 仅 debug 模式打印 SQL

    # === 初始化扩展 ===
    db.init_app(app)
    migrate.init_app(app, db)
    compress.init_app(app)

    # === CORS 跨域配置 ===
    cors_origins = config.get('cors', 'origins')
    cors_origins_list = '*' if cors_origins == '*' else [o.strip() for o in cors_origins.split(',')]
    supports_credentials = config.getboolean('cors', 'supports_credentials')
    CORS(app, resources={r'/*': {'origins': cors_origins_list, 'supports_credentials': supports_credentials}})

    # === 中间件（顺序敏感：request_id 必须在 request_log 之前） ===
    from utils.middleware import init_request_id
    init_request_id(app)

    from utils.request_log import init_request_log
    init_request_log(app)

    # === 注册蓝图 ===
    register_blueprints(app)  # 本文件内定义，详见第 1.4 节

    # === 注册异常处理 ===
    register_error_handlers(app)  # 本文件内定义，详见第 7.1 节

    # === 注册 Swagger 文档 ===
    register_swagger(app, protect=protect_swagger)  # 本文件内定义，详见第 11.1 节

    return app
```

### 3.2 蓝图注册（强制）

```python
def register_blueprints(app):
    url_prefix = '/api'

    app.register_blueprint(auth_bp, url_prefix=f'{url_prefix}/auth')
    app.register_blueprint(user_bp, url_prefix=f'{url_prefix}/user')
    app.register_blueprint(role_bp, url_prefix=f'{url_prefix}/role')
    app.register_blueprint(permission_bp, url_prefix=f'{url_prefix}/permission')
    # ... 其他蓝图
```

---

## 4. 配置管理（强制）

### 4.1 配置加载器（强制）

> ⚠️ **强制要求：配置禁止使用默认值**
>
> 所有配置项**必须**从配置文件读取，**禁止**使用默认值 fallback。
>
> ❌ 错误示例：`app_conf.getint('port', 8000)`、`config.get('debug', fallback=False)`
>
> ✅ 正确示例：`app_conf.getint('port')`、`config.getboolean('debug')`
>
> 若配置文件缺失，程序应该**启动失败**而不是使用默认值。

```python
# common/settings.py

import configparser
import os
from common.constants import BASE_DIR, ENV_TYPE


def get_config_path():
    config_dir = f'{BASE_DIR}/config'
    return f'{config_dir}/config_{ENV_TYPE}.ini'


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
        """读取配置（禁止业务层使用 fallback 默认值！）

        注意：本方法的 `fallback` 参数**仅用于框架内部**，业务代码调用时
        **禁止传 fallback**，必须让缺失抛异常以保证配置完整性。
        """
        if key is None:
            key = section
            section = 'app'
        # fallback=None → configparser 自身在缺失时抛 NoSectionError/NoOptionError
        return self._config.get(section, key, fallback=fallback)

    def getint(self, section, key=None, fallback=None):
        """读取整型配置（禁止使用 fallback 默认值）"""
        if key is None:
            key = section
            section = 'app'
        return self._config.getint(section, key, fallback=fallback)

    def getboolean(self, section, key=None, fallback=None):
        """读取布尔配置（禁止使用 fallback 默认值）"""
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
> 通用规则见 [`代码规范.md`](代码规范.md) 「本技能禁止使用环境变量」段。**Flask 栈的栈级落地**：所有配置统一通过 `Config.get()` / `Config.items()` 读取（详见 §4.1 + §4.2），`*/business/*`、`*/services/*`、`*/api/*`、`*/models/*` 目录下禁止 `import os` 后调用 `os.environ.*` 或 `os.getenv(...)`。

### 4.2 配置文件格式（强制）

> ⚠️ **配置文件选择机制（强制）**
>
> 配置文件的加载由 `ENV_TYPE` 变量控制（取值顺序详见 §19.1；命令行参数 `--dev` / `--test` / `--prod` 首选）：
> - `ENV_TYPE='dev'` → 加载 `config_dev.ini`
> - `ENV_TYPE='test'` → 加载 `config_test.ini`
> - `ENV_TYPE='prod'` → 加载 `config_prod.ini`
>
> **禁止在代码中硬编码配置文件路径**，必须通过 `ENV_TYPE` 动态拼接。
>
> 注意：`ENV_TYPE` 是唯一允许通过命令行（或容器编排层注入）的元配置口子；按通用规则（[`代码规范.md`](代码规范.md) 「最高铁律」）业务代码**不直接读**任何环境变量。

> ⚠️ **环境配置差异原则**
>
> 所有环境的配置文件内容**基本一致**，主差异是 `[app]` 下的 `debug` 配置：
>
> | 环境 | debug值 | 说明 |
> |:-----|:--------|:-----|
> | dev | `true` | 开发环境开启调试 |
> | test | `false` | 测试环境关闭调试 |
> | prod | `false` | 生产环境关闭调试 |
>
> **允许的例外**：性能相关参数（如 Gunicorn workers 数、超时时间）允许按环境差异化。
> 这些参数**不放在 ini 配置文件**，而是在代码中按 `ENV_TYPE` 判断（如 18.2 Gunicorn 启动器）。

```ini
# config_dev.ini / config_test.ini / config_prod.ini
# 由 ENV_TYPE 控制加载哪个文件
# 除debug外，所有环境配置内容一致

[admin_mysql]
host = 127.0.0.1
port = 3309
username = root
password = password
db_name = myapp_db
charset = utf8mb4

[admin_redis]
host = 127.0.0.1
port = 6379
password =
db = 2

[app]
host = 0.0.0.0
secret_key = your-secret-key
# debug = true   # dev环境
# debug = false  # test/prod环境
port = 8000

[log]
# 级别：dev=DEBUG，test/prod=INFO（禁止 if DEBUG 硬编码在业务代码里）
level = INFO
# 控制台格式：false=彩色文本（开发），true=JSON（线上容器 stdout 采集）
console_json = false
# 大内容豁免开关（日志规范 §4.3）：true 才把完整响应体落 large-{date}.log
# 线上默认 false —— 让"大内容要存"必须显式声明
large_enabled = false

[cors]
# 允许跨域的域名（逗号分隔，* 表示允许所有）
origins = *
supports_credentials = true

[swagger]
# Swagger 文档保护账号（dev 环境可在配置文件中硬编码，test/prod 通过 docker-compose environment 注入）
user = admin
password = admin123
```

> ⚠️ **敏感信息注入策略（强制）**
>
> `secret_key`、数据库密码、第三方 API key 等敏感字段的部署策略：
>
> - **dev**：直接写 `config_dev.ini`（便于本地开发）
> - **test / prod**：**禁止**进 git，必须通过 `docker-compose.{env}.yml` 的 `environment:` 段注入到 `config_test.ini` / `config_prod.ini` 的占位符（如 `${SECRET_KEY}`），容器启动时 `envsubst` 替换
> - 业务代码读取方式不变：**仍走 `config.get('app', 'secret_key')`**；按通用规则 ([`代码规范.md`](代码规范.md)) 业务代码**禁止**读环境变量——这里的 `docker-compose environment:` 注入发生在容器编排层，不进入 mcpowers 代码运行时

> ⚠️ **配置加载器实现要求**
>
> 必须使用 **4.1 配置加载器** 中的 `Config` 类，**禁止**直接使用 `configparser` 或硬编码路径。

---

## 5. 中间件（强制）

### 5.1 请求ID中间件（强制）

```python
# utils/middleware.py

import uuid
from flask import g, request


def init_request_id(app):
    @app.before_request
    def set_request_id():
        g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    @app.after_request
    def add_request_id_header(response):
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '-')
        return response
```

### 5.2 全局请求日志中间件（强制）

```python
# utils/request_log.py

import time
from flask import request, g

from utils.loggings import request_log   # 脱敏/截断由封装层 JsonFormatter 统一兜底

SKIP_PREFIXES = ('/static',)


def init_request_log(app):
    @app.before_request
    def before_request():
        g.start_time = time.time()

        if request.path.startswith(SKIP_PREFIXES) or request.endpoint is None:
            return

        extra = {
            'log_type': 'request',
            'phase': 'before',
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
        }

        if request.args:
            extra['query'] = dict(request.args)

        if request.is_json:
            body = request.get_json(silent=True)
            if body:
                extra['body'] = body      # mask_sensitive + 截断在 Formatter 层完成

        # request_id / trace_id / user_id 由 ContextFilter 自动注入，无需手传
        request_log.info('请求开始', extra=extra)

    @app.after_request
    def after_request(response):
        if request.path.startswith(SKIP_PREFIXES) or request.endpoint is None:
            return response

        cost_ms = round((time.time() - getattr(g, 'start_time', time.time())) * 1000, 2)
        status = response.status_code

        extra = {
            'log_type': 'request',
            'phase': 'after',
            'method': request.method,
            'path': request.path,
            'status_code': status,
            'cost_ms': cost_ms,
        }

        resp_json = response.get_json(silent=True) if response.is_json else None
        if resp_json:
            extra['code'] = resp_json.get('code', 0)
            extra['biz_msg'] = resp_json.get('msg', '')   # 不能叫 msg，见 §6.2 保留字段

        # 日志规范 §2.2：状态码自动映射级别（2xx/3xx=INFO，4xx=WARNING，5xx=ERROR）
        level = 'error' if status >= 500 else ('warning' if status >= 400 else 'info')
        getattr(request_log, level)('请求结束', extra=extra)
        return response
```

> **`mask_sensitive` 已上移到 `utils/loggings.py`**（日志规范 §5.2 要求封装层自动脱敏一次）。中间件不再自己实现一份，业务层如需提前剔除敏感字段可 `from utils.loggings import mask_sensitive`。

---

## 6. 日志规范（强制）

> **本节为 Flask 实现层**。完整的日志类型分类、字段 schema、大内容处理、脱敏规则、轮转与免压缩窗口 → 见 `日志规范.md`（v2.6.0 起顶层规范，栈无关；v2.26.0 新增 §7.3 免压缩窗口）。
>
> **本节只保留 3 件事**：
> 1. `utils/loggings.py` 封装类的实现（含免压缩窗口实现）
> 2. 全局请求日志中间件 `utils/request_log.py` 的实现（§5.2）
> 3. 免压缩窗口与清理函数的配置/调用方式
>
> **所有 `logger.*` 调用必须符合 `日志规范.md §3` 字段约定**，禁止发明字段名。

### 6.0 分文件维度：按 type 切，不按级别切（强制）

> 这是本节最容易踩错的一点，先讲清楚再看代码。

| 切分维度 | 结论 | 理由 |
|:---------|:-----|:-----|
| 按业务 **type** 切（`biz.log` / `audit.log` / `request.log` / …） | ✅ **采用** | 不同 type 的**保留期和采样率天然不同**（`audit` ≥180 天、`perf` 采样 1%），这才是落盘分离的真实驱动力 |
| 按 **级别**切成多份（`xxx_info.log` / `xxx_error.log` / …） | ❌ **禁止** | 级别只是过滤条件，JSON 里一个 `level` 字段 + 一次查询就够；切文件反而把同一条 `request_id` 的 INFO→ERROR 链路**拆散到多个文件**，直接破坏 `日志规范.md` 目标 2「可排查」 |
| **ERROR+ 单独抽一条聚合流**（`error.log`） | ✅ **采用** | 唯一例外，且它是**聚合**不是**切分**——同一条 ERROR 同时写进 `{type}.log` 和 `error.log`，原始流不断裂 |

**切分 vs 聚合的区别**（决定了为什么禁止按级别切）：

- **切分**（❌）：一条 ERROR 只存在于 `general_error.log`，`general_info.log` 里看不到它 → 排查时在 info 流读到"订单校验通过"、下一条"订单创建成功"，中间那条 ERROR 你根本不知道存在
- **聚合**（✅）：ERROR 在原 type 文件里保持原位，另外复制一份进 `error.log` 供告警脚本 `tail` → 两边都完整

> **反模式**：❌ 用 `f'{name}_{level}.log'` 命名日志文件。文件数 = 实例数 × 级别数，handler 与文件句柄开销翻 5 倍，收益为零。

### 6.1 日志封装类（强制）

```python
# utils/loggings.py
# -*- coding: utf-8 -*-
"""
JSON 结构化日志封装

对齐 `日志规范.md`：§2（7 类 type）/ §3（字段 schema）/ §4（大内容截断）
/ §5（脱敏）/ §7（输出与轮转）。

设计要点：
1. 按业务 type 分文件，级别是 JSON 字段而非文件名后缀（见 §6.0）
2. ERROR+ 额外聚合到 error.log（多路复制，不切断原 type 流）
3. 上下文（request_id/trace_id/user_id）由 Filter 自动注入，业务层无需手传
4. 脱敏与大内容截断在 Formatter 层统一兜底（封装层保险，业务层仍需自查）
"""

import hashlib
import json
import logging
import os
import threading
from datetime import datetime

import colorlog
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler

from common.constants import LOGGING_BASE_DIR
from common.settings import config

# 日志开关统一来自 config.ini 的 [log] 段（§4.2），禁止 if DEBUG 硬编码在业务代码里
# 注：本文件属框架层，按 §4.1 约定可使用 fallback；业务代码禁止传 fallback
LOG_LEVEL = config.get('log', 'level', fallback='INFO').upper()
LOG_CONSOLE_JSON = config.getboolean('log', 'console_json', fallback=False)
LOG_LARGE_ENABLED = config.getboolean('log', 'large_enabled', fallback=False)
# 日志规范 §7.3（v2.26.0+）：免压缩窗口，生产默认 7 天；显式改 0 = 关闭免压缩（轮转即压缩）
LOG_KEEP_UNCOMPRESSED = config.getint('log', 'keep_recent_uncompressed_days', fallback=7)

# ---- 日志规范 §2：7 类固定 type，禁止发明新类型（铁律 5） ----
LOG_TYPES = ('biz', 'operation', 'audit', 'request', 'perf', 'schedule', 'exception')

# ---- 日志规范 §5.1：敏感字段黑名单（不区分大小写） ----
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

MAX_FIELD_SIZE = 2048           # 日志规范 §4.1：单字段 > 2KB 截断
MAX_FILE_BYTES = 200 * 1024 * 1024   # 日志规范 §7.2：单文件 ≤ 200MB
CONSOLE_FORMAT = '%(asctime)s [%(levelname)s] [%(log_type)s] %(name)s - %(message)s'
LOG_COLORS_CONFIG = {'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow',
                     'ERROR': 'red', 'CRITICAL': 'bold_red'}

# 日志规范 §7.2：差异化保留天数
BACKUP_DAYS = {'audit': 180, 'exception': 90, 'error': 90}
DEFAULT_BACKUP_DAYS = 30

# LogRecord 内建属性 + 自动注入字段，不重复进 extra
_RESERVED = frozenset(logging.LogRecord('', 0, '', 0, '', (), None).__dict__) | {
    'message', 'asctime', 'log_type', 'request_id', 'trace_id', 'span_id', 'user_id',
}

_LOGGER_CACHE = {}
_CACHE_LOCK = threading.Lock()


def _truncate(text, limit=MAX_FIELD_SIZE):
    """大内容截断 + 指纹（日志规范 §4.1：必须记录 original_size + sha256）"""
    raw = text.encode('utf-8')
    if len(raw) <= limit:
        return text
    head = raw[:int(limit * 0.75)].decode('utf-8', 'ignore')
    tail = raw[-int(limit * 0.25):].decode('utf-8', 'ignore')
    return (f'{head}...[TRUNCATED, original_size={len(raw)}, '
            f'sha256={hashlib.sha256(raw).hexdigest()}]...{tail}')


def mask_sensitive(data, limit=MAX_FIELD_SIZE):
    """递归脱敏 + 截断（日志规范 §4 + §5，dict/list 嵌套均覆盖）"""
    if isinstance(data, dict):
        return {k: ('******' if k.lower() in SENSITIVE_FIELDS else mask_sensitive(v, limit))
                for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [mask_sensitive(item, limit) for item in data]
    if isinstance(data, str):
        return _truncate(data, limit)
    return data


class ContextFilter(logging.Filter):
    """自动注入链路上下文（日志规范 铁律 2：禁止无上下文日志）"""

    FIELDS = ('request_id', 'trace_id', 'span_id', 'user_id')

    def filter(self, record):
        in_request = False
        try:
            from flask import g, has_request_context
            in_request = has_request_context()
        except ImportError:
            g = None
        for field in self.FIELDS:
            if not hasattr(record, field):
                setattr(record, field, getattr(g, field, '-') if in_request else '-')
        if not hasattr(record, 'log_type'):
            record.log_type = 'biz'
        return True


class JsonFormatter(logging.Formatter):
    """一行一 JSON 对象（日志规范 铁律 1 + §3.1）"""

    def format(self, record):
        # 用 getattr 兜底：即使 record 未经 ContextFilter（如第三方库 logger 复用本 Formatter）也不崩
        payload = {
            # ISO8601 带时区（强制）
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
            # 日志规范 §3.4：traceback 完整保留，禁止截断
            payload['traceback'] = self.formatException(record.exc_info)
        extra = {k: v for k, v in record.__dict__.items() if k not in _RESERVED}
        if extra:
            payload['extra'] = mask_sensitive(extra)
        return json.dumps(payload, ensure_ascii=False, default=str)


def _file_handler(filename, level, formatter):
    """按天 + 200MB 双触发轮转，多进程安全（日志规范 §7.2）

    注：7 个 type logger 各挂一个指向 error.log 的 handler，靠 concurrent-log-handler
    的文件锁保证轮转不打架；需 concurrent-log-handler >= 0.9.20（支持 maxBytes 组合）。

    v2.26.0 变更（对齐日志规范 §7.3 免压缩窗口）：
        use_gzip 由 True 改为 False（旧版：轮转即 gzip）。
        新版：轮转后保持 .log 状态，由 §6.3 的 compress_old_logs() 在免压缩窗口
        满（默认 7 天）后再主动 gzip。
    """
    handler = ConcurrentTimedRotatingFileHandler(
        os.path.join(LOGGING_BASE_DIR, filename),
        when='D', interval=1, encoding='utf-8',
        maxBytes=MAX_FILE_BYTES,     # 日志规范 §7.2：单文件 ≤ 200MB 强制轮转
        use_gzip=False,              # 日志规范 §7.3：免压缩窗口期间不压缩；超龄由 compress_old_logs 处理
        backupCount=BACKUP_DAYS.get(filename.split('.')[0], DEFAULT_BACKUP_DAYS),
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def get_logger(log_type):
    """按业务 type 取 logger（日志规范 §2 的 7 类之一）

    Args:
        log_type: biz / operation / audit / request / perf / schedule / exception

    Returns:
        logging.Logger —— 直接用 logger.info(msg, extra={...})，级别是字段不是文件
    """
    if log_type not in LOG_TYPES:
        raise ValueError(f'非法日志类型 {log_type!r}，必须为 {LOG_TYPES} 之一（日志规范 铁律 5）')

    cached = _LOGGER_CACHE.get(log_type)
    if cached is not None:
        return cached

    with _CACHE_LOCK:
        if log_type in _LOGGER_CACHE:          # 双检，避免并发重复初始化
            return _LOGGER_CACHE[log_type]

        logger = logging.getLogger(f'app.{log_type}')
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False               # 不上抛到 root，避免重复输出

        if not logger.handlers:                # 防 Flask reloader 二次 addHandler
            os.makedirs(LOGGING_BASE_DIR, exist_ok=True)
            logger.addFilter(ContextFilter())
            json_formatter = JsonFormatter()

            # 1) 按 type 分文件
            logger.addHandler(_file_handler(f'{log_type}.log', LOG_LEVEL, json_formatter))
            # 2) ERROR+ 聚合流（多路复制，原 type 流不断裂）
            logger.addHandler(_file_handler('error.log', logging.ERROR, json_formatter))
            # 3) 控制台：开发彩色文本 / 线上 JSON，由环境变量切换
            console = logging.StreamHandler()
            console.setLevel(LOG_LEVEL)
            console.setFormatter(json_formatter if LOG_CONSOLE_JSON else colorlog.ColoredFormatter(
                f'%(log_color)s{CONSOLE_FORMAT}', log_colors=LOG_COLORS_CONFIG))
            logger.addHandler(console)

        _LOGGER_CACHE[log_type] = logger
        return logger


def save_large(content, tag, extra=None):
    """大内容显式豁免落盘（日志规范 §4.3），线上默认关闭

    独立走 large-{date}.log，不污染 type 流；关闭时只记元信息 + 指纹。
    """
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

### 6.2 调用方式（强制）

> **级别通过方法名表达（`logger.info` / `logger.error`），业务字段通过 `extra` 传**。禁止把 JSON 字符串拼进 `msg`。

```python
from utils.loggings import biz_log, exception_log

# ✅ 正确：type 由 logger 决定，级别由方法决定，字段走 extra
biz_log.info('订单创建成功', extra={
    'log_type': 'biz',            # Formatter 写入 JSON 的 "type"
    'biz_event': 'order.created',
    'biz_id': order.id,
})

# ✅ 正确：异常必带 traceback（日志规范 §3.4）
try:
    create_order(data)
except Exception:
    exception_log.exception('订单创建失败', extra={
        'log_type': 'exception',
        'biz_event': 'order.created',
        'biz_id': data.get('order_id'),
    })
    raise

# ❌ 错误：把 JSON 字符串塞进 msg（外层仍是文本包裹，采集侧无法解析整行 JSON）
biz_log.info(json.dumps({'biz_event': 'order.created'}))

# ❌ 错误：按级别取 logger（级别不是分文件维度，见 §6.0）
error_log = get_logger('error')      # ValueError：非 7 类之一
```

| 输出文件 | 内容 |
|:---------|:-----|
| `logs/biz.log` | 上例第一条（`level=INFO`） |
| `logs/exception.log` | 上例第二条（`level=ERROR` + 完整 traceback） |
| `logs/error.log` | 上例第二条的**副本**（ERROR+ 聚合，供告警脚本 tail） |

> ⚠️ **`extra` 禁用 LogRecord 保留字段名**：`msg` / `message` / `args` / `name` / `module` / `levelname` / `exc_info` / `asctime` 等。传了会直接 `KeyError: "Attempt to overwrite 'xxx' in LogRecord"`。业务字段用 `biz_msg` / `biz_module` 这类带前缀的名字（日志规范 §3.5）。`module` 由 Formatter 自动取 `record.name` 填充。

### 6.3 免压缩窗口与清理函数（v2.26.0+ 强制）

> **本节配套 `日志规范.md §7.3`**。轮转 → 清理 → 压缩的 4 个时序阶段（轮转/窗口/压缩/清理）的实现细节都在本节。
>
> **两个新函数是接口契约**：业务代码禁止自己写清理脚本，只能调用本节的函数。

```python
# utils/loggings.py（接 §6.1 末尾）
import gzip
from datetime import date, datetime, timedelta
from pathlib import Path

from common.constants import LOGGING_BASE_DIR
# 同 §6.1 顶部 LOG_KEEP_UNCOMPRESSED / LOG_TYPES / BACKUP_DAYS / DEFAULT_BACKUP_DAYS


def _parse_rotated_date(filename: str) -> date | None:
    """从 `xx.log.2026-07-20` 解析日期；解析不到返回 None（兼容早期未按时命名的轮转文件）"""
    parts = filename.rsplit('.', 2)        # ['xx', 'log', '2026-07-20'] 或 ['xx', 'log-2026-07-20']
    try:
        return datetime.strptime(parts[-1], '%Y-%m-%d').date()
    except (ValueError, IndexError):
        return None


def compress_old_logs(keep_recent_days: int | None = None) -> list[str]:
    """压缩超过「免压缩窗口」的轮转文件（日志规范 §7.3 阶段 ③）

    Args:
        keep_recent_days: 免压缩窗口天数；None = 用配置 LOG_KEEP_UNCOMPRESSED（默认 7）

    Returns:
        被压缩的文件路径列表（用于运维回显/告警检测）

    触发时机：
        - 定时任务（推荐每天凌晨 00:30 跑一次，配合 §13 schedule）
        - 手动排查时也可单独调用
    """
    keep = LOG_KEEP_UNCOMPRESSED if keep_recent_days is None else keep_recent_days
    cutoff = date.today() - timedelta(days=keep)
    compressed = []
    for path in Path(LOGGING_BASE_DIR).glob('*.log.*'):    # 轮转文件 = <name>.log.<date>
        if path.suffix == '.gz':
            continue
        d = _parse_rotated_date(path.name)
        if d is None or d >= cutoff:
            continue
        gz_path = path.with_suffix(path.suffix + '.gz')
        with open(path, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
            f_out.writelines(f_in)
        path.unlink()
        compressed.append(str(path))
    return compressed


def purge_old_logs() -> dict[str, int]:
    """清理超过保留期的 .gz 文件（日志规范 §7.3 阶段 ④）

    Returns:
        {type 名称: 删除数量}，用于运维回显

    差异化保留（来自 BACKUP_DAYS，§6.1 顶部常量）：
        - audit.log.*.gz ≥ 180 天
        - exception.log.*.gz ≥ 90 天
        - error.log.*.gz ≥ 90 天
        - 其他 ≥ 30 天（DEFAULT_BACKUP_DAYS）

    ⚠️ 大文件清理：按 BACKUP_DAYS 直接 unlink，不进回收站（生产环境慎用前手动 dry-run）。
    """
    today = date.today()
    deleted: dict[str, int] = {}
    for gz_path in Path(LOGGING_BASE_DIR).glob('*.log.*.gz'):
        stem = gz_path.name.split('.')[0]    # 'biz' / 'audit' / 'error' / ...
        keep_days = BACKUP_DAYS.get(stem, DEFAULT_BACKUP_DAYS)
        d = _parse_rotated_date(gz_path.name.removesuffix('.gz'))
        if d is None:
            continue
        if (today - d).days <= keep_days:
            continue
        gz_path.unlink()
        deleted[stem] = deleted.get(stem, 0) + 1
    return deleted
```

**配置项登记**（`config.ini [log]` 段，对齐 §4.2）：

```ini
[log]
level = INFO
console_json = false
large_enabled = false
keep_recent_uncompressed_days = 7        # 日志规范 §7.3：生产默认 7；调试开发场景可改 0
```

**定时触发**（推荐挂到系统 cron / APScheduler / Celery beat 调度的定时任务上）：

```python
# apps/schedule_jobs/log_cleanup.py（已对齐 §13 schedule 写法）
from utils.loggings import compress_old_logs, purge_old_logs

def daily_log_maintenance():
    """每天凌晨 00:30 跑：先压缩超龄 .log，再清理超期 .gz"""
    compressed = compress_old_logs()
    deleted = purge_old_logs()
    if compressed or deleted:
        # 清理动作走 schedule 日志，方便追溯
        schedule_log = get_logger('schedule')
        schedule_log.info('日志维护完成', extra={
            'log_type': 'schedule',
            'job_name': 'log_maintenance',
            'compressed_count': len(compressed),
            'deleted_by_type': deleted,
        })
```

**反模式**（code-review 必须 Critical）：

| # | 反模式 | 后果 |
|:-:|:-------|:-----|
| 1 | ❌ 业务代码自己写 `for f in glob('*.log.*'): os.system(f'gzip {f}')` | 与框架压缩函数双跑/打架；窗口语义模糊 |
| 2 | ❌ 在 `cron` 或 `apscheduler` 里写定时清理，但**未声明**到 `config.ini` | 配置漂移，运维排查困难 |
| 3 | ❌ 把 `keep_recent_uncompressed_days` 改 `30`，磁盘占用没算过 | OOM 风险 |
| 4 | ❌ `purge_old_logs` 直接 `unlink` 但**没有 schedule 日志记录** | 删了就删了，事后无法追溯 |

---

## 7. 异常处理（强制）

### 7.1 全局异常处理（强制）

```python
# apps/__init__.py

def register_error_handlers(app):
    """注册全局异常处理器

    覆盖：
    - HTTP 标准错误（404/405/500）
    - Flask 内置 HTTPException
    - 数据库完整性错误（IntegrityError → 409）
    - 参数验证错误（ValidationError → 400）
    - 所有其他 Exception
    """
    from werkzeug.exceptions import HTTPException
    from sqlalchemy.exc import IntegrityError
    from marshmallow import ValidationError
    from utils.responses import api_error
    from utils.loggings import exception_log
    from flask import request, g

    @app.errorhandler(404)
    def not_found(e):
        return api_error(404, '请求的资源不存在')

    @app.errorhandler(405)
    def method_not_allowed(e):
        return api_error(405, '请求方法不允许')

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        """参数验证失败（marshmallow）"""
        return api_error(400, f'参数错误: {e.messages}')

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        """数据库完整性约束失败（唯一索引冲突等）"""
        from db.mysql.helpers import db
        db.session.rollback()
        return api_error(409, '数据已存在或违反约束')

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Flask 内置 HTTP 异常（401/403/400 等）"""
        return api_error(e.code, e.description)

    @app.errorhandler(Exception)
    def handle_exception(e):
        request_id = getattr(g, 'request_id', '-')
        # logger.exception 自动带完整 traceback（日志规范 §3.4），禁止手拼 traceback.format_exc()
        exception_log.exception('未捕获异常', extra={
            'log_type': 'exception',
            'path': request.path,
            'method': request.method,
        })
        # 响应中携带 request_id 便于用户反馈排查
        from flask import jsonify
        response = jsonify({'code': 500, 'msg': '服务器内部错误', 'request_id': request_id})
        return response, 500
```

> 该条同时落 `logs/exception.log`（原 type 流）与 `logs/error.log`（ERROR+ 聚合流），见 §6.0。

### 7.2 自定义异常（强制）

```python
# utils/exceptions.py

class GeneralError(Exception):
    def __init__(self, *args, **kwargs):
        pass

    def __str__(self):
        return self.args[0]
```

---

## 8. 错误码（强制）

> ⚠️ **通用规范引用**：详见 `API规范.md` 第1章

---

## 9. 响应规范（强制）

> ⚠️ **通用规范引用**：详见 `API规范.md` 第2章

### 9.1 Flask 响应实现（强制）

```python
# utils/responses.py

from flask import jsonify
from common.codes import get_error_message


def api_success(data=None, msg='success', code=0):
    """成功响应"""
    response = {'code': code, 'msg': msg}
    if data is not None:
        response['data'] = data
    return jsonify(response)


def api_error(code, msg=None):
    """错误响应"""
    if msg is None:
        msg = get_error_message(code)
    response = {'code': code, 'msg': msg}
    return jsonify(response)


def api_page(records, page_no, page_size, total_count):
    """分页响应"""
    total_page = (total_count + page_size - 1) // page_size if page_size > 0 else 0
    return jsonify({
        'code': 0,
        'msg': 'success',
        'data': {
            'records': records,
            'page_no': page_no,
            'page_size': page_size,
            'total_page': total_page,
            'total_count': total_count
        }
    })
```

---

## 10. 认证授权（强制）

### 10.1 登录装饰器（强制）

```python
# utils/decorators.py

from functools import wraps
from flask import request, g
from utils.responses import api_error
from db.redis.helpers import admin_redis
from common.constants import AdminRedisKeys


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return api_error(401, '请先登录')

        user_id = admin_redis.get(AdminRedisKeys.ADMIN_USER_TOKEN.format(token))
        if not user_id:
            return api_error(401, '登录已过期')

        g.user_id = user_id
        g.token = token

        return f(*args, **kwargs)

    return decorated_function
```

### 10.2 权限装饰器（强制）

```python
def permission_required(*permission_codes):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from db.mysql.models import User, Role

            user_id = getattr(g, 'user_id', None)
            if not user_id:
                return api_error(401, '请先登录')

            user = db.session.get(User, int(user_id))
            if not user:
                return api_error(401, '用户不存在')

            role = db.session.get(Role, user.role_id)
            if not role:
                return api_error(403, '用户角色不存在')

            user_permissions = role.permissions or []

            if '*' in user_permissions:
                return f(*args, **kwargs)

            for code in permission_codes:
                if code not in user_permissions:
                    return api_error(403, f'无权限: {code}')

            return f(*args, **kwargs)

        return decorated_function

    return decorator
```

### 10.3 Token管理（Redis）（强制）

> ⚠️ **通用规范引用**：详见 `缓存规范.md`

```python
# 同一账号只能在一处登录，新登录会使之前的token失效

# 生成新token（含用户信息确保唯一）
token = generate_login_token(user.id, user.username)

# 存储双向映射
admin_redis.set(AdminRedisKeys.ADMIN_USER_TOKEN.format(token), user_id, ex=86400)
admin_redis.set(AdminRedisKeys.ADMIN_USER_TOKEN_BY_ID.format(user_id), token, ex=86400)

# 删除该用户之前的token
old_token = admin_redis.get(AdminRedisKeys.ADMIN_USER_TOKEN_BY_ID.format(user_id))
if old_token:
    admin_redis.delete(AdminRedisKeys.ADMIN_USER_TOKEN.format(old_token))
```

---

## 11. Swagger文档 (Flasgger)（强制）

### 11.1 Flasgger配置（强制）

> ⚠️ **通用规范引用**：详见 `API规范.md` 第6章

> ⚠️ **强制要求：先写文档，后写代码**
>
> **每个接口必须先在视图函数docstring中编写文档，再编写视图函数实现。**
>
> **必须包含完整字段**：summary、description、parameters（含各参数example）、responses（含examples示例）。
>
> **检查模板文件**：
> - 检查 `docs/API文档/swagger_template.md` 是否存在
> - 若不存在 → **必须先询问用户**是否需要创建模板文件
> - 若存在 → 参考模板格式编写

**仅非生产环境可用**：仅在开发/测试环境启用，生产环境自动禁用，不暴露接口信息。

```python
# apps/__init__.py

def get_internal_ip():
    import socket
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


def register_swagger(app, protect=True):
    from common.constants import ENV_TYPE

    if ENV_TYPE == 'prod':
        return  # 生产环境不启用Swagger

    from flasgger import Swagger, NO_SANITIZER

    swagger_config = {
        "headers": [],
        "specs": [{"endpoint": "apispec_1", "route": "/apispec_1.json", "rule_filter": lambda rule: True}],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
        # v2.4.0 升级：Swagger UI 3.52.5 → 5.17.14（修复 XSS 漏洞 CVE-2023-24998 + 更好的移动适配）
        "swagger_ui_bundle_js": "//unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js",
        "swagger_ui_standalone_preset_js": "//unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-standalone-preset.js",
        "swagger_ui_css": "//unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css",
    }

    Swagger(app, config=swagger_config, sanitizer=NO_SANITIZER, template={
        "swagger": "2.0",
        "info": {"title": "API文档", "version": "1.0.0"},
        "host": f"{get_internal_ip()}:{app_conf.get('port')}",
        "basePath": "/api",
        "tags": [
            {"name": "系统管理/认证管理", "description": "用户登录、退出等认证相关接口"},
            {"name": "系统管理/用户管理", "description": "用户信息管理接口"},
        ],
        "securityDefinitions": {
            "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header", "description": "JWT Token"}
        },
        "security": [{"Bearer": []}]
    })

    # HTTP Basic Auth保护文档
    if protect:
        # 账号密码从配置文件读取，禁止硬编码（详见 安全规范.md）
        from common.settings import app_conf
        swagger_user = app_conf.get('swagger_user')
        swagger_pass = app_conf.get('swagger_password')

        @app.before_request
        def protect_swagger():
            swagger_paths = ['/apidocs', '/apispec_1.json', '/static/flasgger/']
            if any(request.path.startswith(p) for p in swagger_paths):
                auth = request.authorization
                if not auth or not (auth.username == swagger_user and auth.password == swagger_pass):
                    return Response('Login Required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
```

### 11.1.4 Header 参数声明示例（v2.4.0 新增，适配 webhook / 签名校验场景）

**Webhook 场景**（如 `/webhook/payment` 接收回调，强制要求签名头）：

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
    example: sha256=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
  - in: header
    name: X-Event-Id
    type: string
    required: true
    description: 事件唯一 ID（用于幂等去重）
    example: evt_20240715_xxx
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        event_id:
          type: string
          description: 事件 ID（与 X-Event-Id 一致）
          example: evt_20240715_xxx
        event_type:
          type: string
          description: 事件类型
          example: payment.success
        data:
          type: object
          description: 业务数据
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

### 11.1.5 formData 文件上传参数声明示例（v2.4.0 新增，适配 upload/import 场景）

**文件上传场景**：

```python
@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传文件
---
tags:
  - 文件管理/通用上传
summary: 上传文件
description: 上传文件到服务器。
parameters:
  - in: formData
    name: file
    type: file
    required: true
    description: 文件（支持图片、文档，单文件 ≤ 10MB）
responses:
  200:
    description: 上传成功
    examples:
      application/json:
        code: 0
        data:
          url: /uploads/20240715_xxx.png
        msg: 上传成功
"""
```

### 11.2 docstring格式要求（强制）

> ⚠️ **重要：标题与`---`之间不能有空行**，否则Flasgger解析会出错

**正确格式：**
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
        data:
          token: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
          user_id: 1
          username: "admin"
        msg: "success"
"""
    # 视图函数实现
```

**错误格式（会导致description显示<br/>）：**
```python
# ❌ 标题和---之间有空行
def login():
    """用户登录

    ---
    tags:
    ...
"""
```

### 11.3 必需字段（强制 — v2.4.0 对齐接口契约规范）

> **本节是 Flasgger docstring 写法的强制基线**。完整通用规则（含 19 类接口、description ≤ 100 字强约束、parameters/responses 完整结构化）见 `接口契约规范.md`。
>
> 本节只约束**Flask/Flasgger 栈特有**的字段落地方式，**通用规则完全沿用接口契约规范 §1**。

| 字段 | 必须 | Flasgger 落地 | 通用规则出处 |
|:-----|:-----|:--------------|:-------------|
| `tags` | ✅ | tags: `- 大模块/子模块` | 接口契约规范 §1 |
| `summary` | ✅ | `summary: 用户登录`（≤ 30 字） | 接口契约规范 §1.D |
| `description` | ✅ | `description: ...`（≤ 100 字，**简短功能说明**） | 接口契约规范 §1.A |
| `parameters` | ✅ | `parameters:` 列表，**每个含 `description` + `example`** | 接口契约规范 §1.B |
| `responses` | ✅ | `responses:` 字典，**每个状态码含 `schema` + `examples`** | 接口契约规范 §1.C |

#### 11.3.1 parameters 子字段强制项（沿用接口契约规范 §1.B）

| 子字段 | 必须 | Flasgger 写法示例 |
|:-------|:-----|:-----------------|
| `name` | ✅ | `name: page_no` |
| `in` | ✅ | `in: query` / `body` / `path` / `formData` / `header` |
| `required` | ✅ | `required: true` |
| `type` | ✅ | `type: integer` |
| `description` | ✅ 强制 | `description: 页码，从 1 开始`（**业务含义，不要复制字段名**） |
| `example` | ✅ 强制 | `example: 1`（**必填**，前端可直接复制） |
| `schema` | 条件 | `in: body` 且为复杂对象时必填，嵌套结构用 `schema/properties` |

#### 11.3.2 responses 子字段强制项（沿用接口契约规范 §1.C）

| 子字段 | 必须 | Flasgger 写法示例 |
|:-------|:-----|:-----------------|
| **状态码** | ✅ | `200:` / `400:` / `401:` / `500:`（**必含 200 + 至少 1 错误码**） |
| `description` | ✅ | `description: 登录成功` |
| `schema` | ✅ 强制 | `schema: {type: object, properties: {...}}`（**Swagger UI 靠它渲染可点击结构**） |
| `examples` | ✅ 强制 | `examples: {application/json: {code: 0, msg: success, data: {...}}}` |

> **铁律**：
> - ❌ `responses` 只列 `200:`（禁止）
> - ❌ `parameters[].description` 或 `example` 漏写（禁止）
> - ❌ `description` 写成"5 段式背景/前置/字段/错误/副作用"长篇（v1.1 已禁止，应 ≤ 100 字简短）
> - ✅ 反模式全部见 `接口契约规范.md` §8

#### 11.3.3 description 字段硬约束（v2.4.0 起强制）

| 约束 | 说明 |
|:-----|:-----|
| **字数** | ≤ 100 字 |
| **内容** | 只写接口**功能**（一句话） |
| **禁止** | 业务背景 / 前置条件 / 字段含义 / 错误码 / 副作用（这些放 `parameters[].description` 和 `responses[error_code].description`） |
| **禁止** | 写"待补充" / "TBD" / "TODO" |

> ✅ 正确：`description: 使用用户名或手机号和密码登录，返回访问 token。`
> ❌ 错误：300+ 字的"5 段式背景/前置/字段/错误/副作用"

### 11.4 文档导出（强制 — v2.4.0 加强）

**强制闭环**：改 docstring → 重跑 export_docs.py → 校验输出 → commit spec 文件。

#### 11.4.1 强制出口（v2.4.0 新增）

每次改视图函数 docstring 后**必须**重跑导出：

```bash
# 在 Flask 项目根目录
python tools/export_docs.py

# 输出：
#   docs/API文档/swagger_spec.json   ← 机器消费
#   docs/API文档/API文档.md          ← 人类阅读
```

**禁止**只改 docstring 不重跑导出（这是 mcpowers 的接口契约 SSOT 铁律）。

#### 11.4.2 一致性校验（v2.4.0 推荐）

可选运行一致性校验脚本（**v2.4.0 新增** `scripts/check_api_docs_sync.sh`）：

```bash
bash scripts/check_api_docs_sync.sh
# 检查项：
#   - 视图函数 docstring 是否齐全
#   - 导出的 swagger_spec.json 是否比 .py 文件旧（导出滞后）
#   - API文档.md 是否已 commit
```

#### 11.4.3 导出后必须 commit 的文件

- `docs/API文档/swagger_spec.json`
- `docs/API文档/API文档.md`

#### 11.4.4 现有导出能力（沿用 v2.2.0）

```bash
# 1. 完成接口开发后，运行 export_docs.py 导出文档
python tools/export_docs.py

# 2. 自动生成 swagger_spec.json 和 API文档.md（v2.4.0 起支持 formData/header/错误码）
```

#### 11.4.5 下游派生（v2.4.0 新增一键脚本）

```bash
# 前端 TypeScript 客户端自动生成（v2.4.0 新增 scripts/generate-frontend-ts.sh）
bash scripts/generate-frontend-ts.sh

# API 测试自动跑（v2.4.0 新增 scripts/run-api-tests.sh）
bash scripts/run-api-tests.sh
```

---

## 12. API路径规范（强制）

> ⚠️ **通用规范引用**：详见 `API规范.md` 第3章

---

## 13. API参数命名规范（强制）

> ⚠️ **通用规范引用**：详见 `API规范.md` 第4章

---

## 14. 参数验证（强制）

> ⚠️ **通用规范引用**：详见 `API规范.md` 第5章

### 14.1 Flask 参数获取示例（强制）

```python
from flask import request

# 获取查询参数
id = request.args.get('id')
status = request.args.get('status')

# 获取body参数
data = request.get_json()
user_id = data.get('id')

# 分页参数
page_no = request.args.get('page_no', 1, type=int)
page_size = request.args.get('page_size', 10, type=int)
```

---

## 15. 辅助函数

### 15.1 密码处理（强制）

```python
# utils/helpers.py

import hashlib


def hash_password(password):
    """MD5加密"""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password, hashed):
    """验证密码"""
    return hash_password(password) == hashed
```

### 15.2 Token生成（强制）

```python
# utils/helpers.py

import uuid
import time
import hashlib


def generate_token(length=32):
    """生成随机token"""
    return str(uuid.uuid4()).replace('-', '')[:length]


def generate_login_token(user_id, username):
    """生成登录token"""
    timestamp = str(int(time.time()))
    random_str = generate_token(8)
    raw = f'{user_id}:{username}:{timestamp}:{random_str}'
    return hashlib.sha256(raw.encode()).hexdigest()
```

### 15.3 验证码生成（强制）

```python
# utils/helpers.py

import random
from PIL import Image, ImageDraw, ImageFont


def generate_captcha(length=4):
    """生成验证码"""
    chars = 'abcdefghjkmnpqrstuvwxy3456789'
    return ''.join(random.choice(chars) for _ in range(length))


def generate_captcha_image(code):
    """生成验证码图片"""
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), code, fill=(0, 0, 0), font=font)
    # 添加干扰线...
    return image
```

---

## 16. Excel导入导出（强制）

> ⚠️ **通用规范引用**：详见 `API规范.md` 第7章

### 16.1 Flask 特定实现（强制）

```python
# 获取上传文件
from flask import request
from openpyxl import load_workbook

file = request.files.get('file')
if not file or not file.filename.endswith('.xlsx'):
    return api_error(400, '请上传.xlsx格式文件')

wb = load_workbook(file)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))

# 返回文件下载
from io import BytesIO
from flask import make_response

output = BytesIO()
wb.save(output)
output.seek(0)
response = make_response(output.getvalue())
response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
response.headers['Content-Disposition'] = 'attachment; filename=export.xlsx'
return response
```

---

## 17. CORS跨域（强制）

```python
# 在create_app中
cors_origins = config.get('cors', 'origins')
cors_origins_list = '*' if cors_origins == '*' else [o.strip() for o in cors_origins.split(',')]
supports_credentials = config.getboolean('cors', 'supports_credentials')
CORS(app, resources={r'/*': {'origins': cors_origins_list, 'supports_credentials': supports_credentials}})
```

---

## 18. Gunicorn配置

> ⚠️ **技术锁定**：Gunicorn 是 Python WSGI 特有的应用服务器，不属于通用部署规范。

### 18.1 Worker Class选择（强制）

Gunicorn 支持多种 worker_class，推荐使用 `GeventWebSocketWorker`。

#### 常见 Worker Class 对比

| Worker Class | 特点 | 并发能力 | 适用场景 | WebSocket支持 |
|:-------------|:-----|:---------|:---------|:--------------|
| **sync**（默认） | 同步阻塞，每个请求一个进程 | 低（workers × 1） | 简单 Flask 应用 | ❌ 不支持 |
| **gevent** | 异步非阻塞，协程 | 高（workers × 2000） | 需要高并发的 HTTP 服务 | ⚠️ 需配合 pywebsocket |
| **geventwebsocket** | 异步非阻塞，协程 | 高（workers × 2000） | 需要 WebSocket 的应用 | ✅ 原生支持 |
| **eventlet** | 异步非阻塞，协程 | 高（workers × 2000） | 需要高并发和 WebSocket | ✅ 支持 |
| **gthread** | 线程池模型 | 中（workers × 50） | 需要多线程的场景 | ⚠️ 有限支持 |

#### 为什么推荐 GeventWebSocketWorker

1. **一步到位**：同时支持普通 HTTP 和 WebSocket，无需中途切换
2. **性能优异**：基于 gevent 协程，异步非阻塞，高并发场景表现优秀
3. **兼容性广**：绝大多数第三方库都能与 gevent 兼容
4. **维护简单**：统一使用一种 worker，避免后续因需求变更而重构

> ⚠️ **强制要求**：所有 Flask 项目必须使用 `GeventWebSocketWorker`，不得使用其他 worker_class

### 18.2 Gunicorn启动器（强制）

```python
# gunicorn_loader.py
# Gunicorn 启动器（生产环境推荐使用 geventwebsocket worker）

import multiprocessing
from gunicorn.app.base import BaseApplication
from geventwebsocket.gunicorn.workers import GeventWebSocketWorker

from common.settings import app_conf
from common.constants import ENV_TYPE  # 环境类型（dev/test/prod）


def create_application():
    """创建 WSGI 应用实例"""
    from app import app
    return app


class StandaloneApplication(BaseApplication):
    """Gunicorn 独立应用封装"""

    def __init__(self, options=None):
        self.options = options or {}
        super().__init__()

    def load_config(self):
        """加载 Gunicorn 配置"""
        # 开发环境只启动 2 个 worker（避免本地内存占用过高）
        # 其他环境按 CPU 核数 × 2 + 1 启动（生产推荐）
        if ENV_TYPE == 'dev':
            workers = 2
        else:
            workers = (multiprocessing.cpu_count() * 2) + 1

        config = {
            'bind': f'{app_conf.get("host")}:{app_conf.getint("port")}',
            'worker_class': GeventWebSocketWorker,  # 强制使用 GeventWebSocketWorker
            'workers': workers,
            'worker_connections': 1000,  # 单 worker 并发连接数（WebSocket 需要较高）
            'timeout': 60,              # 请求超时（秒）
            'keepalive': 5,             # keep-alive 超时
            'max_requests': 1000,       # 处理 N 个请求后重启 worker（防内存泄漏）
            'max_requests_jitter': 100, # 随机抖动，避免所有 worker 同时重启
            'graceful_timeout': 30,     # 优雅退出超时
            'accesslog': '-',           # 访问日志输出到 stdout
            'errorlog': '-',            # 错误日志输出到 stdout
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        """返回 WSGI 应用"""
        return create_application()


# 模块级 app 实例（供 gunicorn 导入使用：gunicorn gunicorn_loader:app）
app = create_application()


if __name__ == '__main__':
    # 启动命令：python -u gunicorn_loader.py
    # 环境切换：python -u gunicorn_loader.py --test / --prod（详见 19.1）
    StandaloneApplication().run()
```

**启动命令：** `python -u gunicorn_loader.py`

---

## 19. 环境变量（强制）

### 19.1 环境类型（强制）

```python
# common/constants.py

import sys

# 默认开发环境；命令行可覆盖（详见 19.2 启动命令）
ENV_TYPE = 'dev'
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

### 19.2 启动命令（强制）

```bash
# 开发环境
python app.py

# 测试环境
python app.py --test

# 生产环境
python app.py --prod
```

---

## 20. 规范执行检查清单（强制）

### 20.1 接口开发时必查（强制）

| 检查项 | 要求 |
|:-------|:-----|
| 参数名 | 单资源接口使用 `id`，关联表接口使用 `xxx_id` |
| docstring | 先写文档后写代码，标题与`---`之间不能有空行 |
| 字段注释 | 所有 `comment` 使用小写 `id`（如`角色id`） |
| responses | 必须包含 examples 示例 |
| 查询条件类型 | 单选用单值、多选用IN、范围用BETWEEN、模糊用LIKE |
| 导入接口 | docstring需包含total/success/fail/errors返回结构 |
| 导出接口 | docstring需声明content-type为Excel格式 |
| 模板下载 | 模板列名必须与需求文档字段含义一致 |

### 20.2 提交前必查（强制）

| 检查项 | 要求 |
|:-------|:-----|
| 接口参数 | 符合 **API参数命名规范** |
| docstring格式 | 符合 **11.2 docstring格式要求** |
| 查询条件 | 符合 **参数验证** 规范 |
| 导入导出 | 符合 **API规范** 导入导出流程 |
| 代码无冗余 | 无重复定义、无调试代码残留 |

### 20.3 配置管理必查（强制）

| 检查项 | 要求 |
|:-------|:-----|
| 配置文件路径 | 必须通过 `ENV_TYPE` 动态拼接（`config_{ENV_TYPE}.ini`），禁止硬编码 |
| 配置加载 | 必须使用 `Config` 类，禁止直接使用 `configparser` |
| 配置读取 | 禁止使用 `fallback` 默认值，缺失必须启动失败 |
| debug配置 | dev=true, test/prod=false，与环境匹配 |
| 敏感信息 | `secret_key`、`password` 等必须从配置文件读取，禁止硬编码 |

---

## 附录

### A. 相关文档（强制）

| 文档 | 位置 |
|:-----|:-----|
| **API通用规范** | `API规范.md` |
| **数据库规范** | `数据库规范.md` |
| **缓存规范** | `缓存规范.md` |
| **定时任务规范** | `定时任务规范.md` |
| **部署规范** | `部署规范.md` |
| Swagger文档模板 | `docs/API文档/swagger_template.md` |
| API文档导出脚本 | `tools/export_docs.py` |
| 导出后API文档 | `docs/API文档/swagger_spec.json` |
| 导出后Markdown | `docs/API文档/API文档.md` |

### B. 标签对照表（强制）

> ⚠️ **通用规范引用**：详见 `API规范.md` 第9章

---

## 21. Docker容器化（强制）

### 21.1 Dockerfile

```dockerfile
FROM python:3.13.3

WORKDIR /{项目名}

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 复制依赖文件并安装
COPY requirements.txt .
RUN python3 -m pip install -U pip -i https://mirrors.aliyun.com/pypi/simple && \
    pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
```

### 21.2 docker-compose.dev.yml

```yaml
version: '2.1'
services:
  {项目名}:
    build:
      context: .
      dockerfile: Dockerfile
    image: {项目名}:dev
    container_name: {项目名}-dev
    restart: always
    ports:
      - '{端口}:{端口}'
    volumes:
      - .:/{项目名}
    environment:
      - TZ=Asia/Shanghai
    command: python -u gunicorn_loader.py --dev
    logging:
      driver: 'json-file'
      options:
        max-size: '100m'
        max-file: '2'
```

### 21.3 docker-compose.test.yml

```yaml
version: '2.1'
services:
  {项目名}:
    build:
      context: .
      dockerfile: Dockerfile
    image: {项目名}:test
    container_name: {项目名}-test
    restart: always
    ports:
      - '{端口}:{端口}'
    volumes:
      - .:/{项目名}
    environment:
      - TZ=Asia/Shanghai
    command: python -u gunicorn_loader.py --test
    logging:
      driver: 'json-file'
      options:
        max-size: '100m'
        max-file: '2'
```

### 21.4 docker-compose.prod.yml

```yaml
version: '2.1'
services:
  {项目名}:
    build:
      context: .
      dockerfile: Dockerfile
    image: {项目名}:prod
    container_name: {项目名}-prod
    restart: always
    ports:
      - '{端口}:{端口}'
    volumes:
      - .:/{项目名}
    environment:
      - TZ=Asia/Shanghai
    command: python -u gunicorn_loader.py --prod
    logging:
      driver: 'json-file'
      options:
        max-size: '100m'
        max-file: '2'
```

### 21.5 启动命令

> **统一原则**：所有环境的"启动/重启/重部署"都走 `up -d --force-recreate`。
> `--force-recreate` 强制重建容器，确保新代码（已构建好的镜像）一定生效。
> **只有在依赖变了（Dockerfile / requirements.txt / package.json）才需要加 `--build`**——`--build` 会重新构建镜像，docker compose 会自动检测到镜像变化并重建容器，无需额外加 `--force-recreate`。

```bash
# ========== 启动/重启/重部署（默认命令，覆盖 99% 场景） ==========
# dev
docker-compose -f docker-compose.dev.yml up -d --force-recreate
# test
docker-compose -f docker-compose.test.yml up -d --force-recreate
# prod
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# ========== 依赖变了（Dockerfile / requirements.txt 等）才用这个 ==========
# dev
docker-compose -f docker-compose.dev.yml up -d --build
# test
docker-compose -f docker-compose.test.yml up -d --build
# prod
docker-compose -f docker-compose.prod.yml up -d --build

# ========== 通用命令 ==========
# 查看日志
docker-compose -f docker-compose.{环境}.yml logs -f

# 停止（容器仍在，可 start 重启）
docker-compose -f docker-compose.{环境}.yml stop

# 删除（停止并清理容器、网络、默认网络——配置变更后常用）
docker-compose -f docker-compose.{环境}.yml down
```

> ❌ **禁止**：`docker-compose restart`（不重建容器，新代码不生效）/ `docker-compose up -d`（容器没变，新镜像不被加载）。
> 详见 `开发环境规范.md §4.4`。

### 21.6 三环境差异对照表

| 配置项 | dev | test | prod |
|:-------|:----|:-----|:-----|
| image tag | `:dev` | `:test` | `:prod` |
| container_name | `{项目名}-dev` | `{项目名}-test` | `{项目名}-prod` |
| config文件 | `config_dev.ini` | `config_test.ini` | `config_prod.ini` |
| command | `--dev` | `--test` | `--prod` |

---

### 21.7 完整 docker-compose（含 MySQL + Redis 依赖，推荐）

> ⚠️ **本地开发强制**：21.2/21.3/21.4 的极简版只包含 app 服务，适用于"依赖服务外置"的场景。
> **本地开发默认必须使用本节的完整版**，确保 `bash start_dev.sh` 即可拉起全部依赖。
>
> **设计要点**：
> - MySQL/Redis 数据持久化到 `./docker-data/{mysql,redis}/`
> - 端口固定：MySQL 3306、Redis 6379
> - 健康检查：`mysql:3306` 和 `redis:6379` 起来后才启动 app
> - 跨环境差异仅在 image tag / container_name / command / config

#### 21.7.1 docker-compose.dev.yml（完整版）

```yaml
version: '2.1'
services:
  {项目名}-mysql:
    image: mysql:8.0
    container_name: {项目名}-mysql-dev
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: root_dev
      MYSQL_DATABASE: {项目名}_dev
      TZ: Asia/Shanghai
    ports:
      - '3306:3306'
    volumes:
      - ./docker-data/mysql-dev:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "127.0.0.1", "-uroot", "-proot_dev"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging:
      driver: 'json-file'
      options:
        max-size: '100m'
        max-file: '2'

  {项目名}-redis:
    image: redis:7.2-alpine
    container_name: {项目名}-redis-dev
    restart: always
    ports:
      - '6379:6379'
    volumes:
      - ./docker-data/redis-dev:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging:
      driver: 'json-file'
      options:
        max-size: '100m'
        max-file: '2'

  {项目名}-app:
    build:
      context: .
      dockerfile: Dockerfile
    image: {项目名}:dev
    container_name: {项目名}-app-dev
    restart: always
    ports:
      - '{端口}:{端口}'
    volumes:
      - .:/{项目名}
    environment:
      - TZ=Asia/Shanghai
    command: python -u gunicorn_loader.py --dev
    depends_on:
      {项目名}-mysql:
        condition: service_healthy
      {项目名}-redis:
        condition: service_healthy
    logging:
      driver: 'json-file'
      options:
        max-size: '100m'
        max-file: '2'
```

#### 21.7.2 docker-compose.test.yml（完整版）

> 复制 21.7.1，将 `mysql-dev` → `mysql-test`、`redis-dev` → `redis-test`、image tag `:dev` → `:test`、command `--dev` → `--test`、数据库名 `{项目名}_dev` → `{项目名}_test`、MySQL 密码 `root_dev` → `root_test`、容器名加 `-test` 后缀。

#### 21.7.3 docker-compose.prod.yml（完整版）

> ⚠️ **生产环境慎用容器化 DB**：本节仅给出模板。
> **生产环境推荐**：MySQL 用云数据库 RDS，Redis 用云 Redis；compose 中删除 mysql/redis services，app 改为 `depends_on` 云服务（环境变量配置连接信息）。

#### 21.7.4 一键启动（推荐方式）

```bash
# macOS / Linux / Git Bash on Windows
bash mcpowers-shared/scripts/start_dev.sh              # 默认 dev
bash mcpowers-shared/scripts/start_dev.sh test --build # test 环境强制重建

# Windows PowerShell
.\mcpowers-shared\scripts\start_dev.ps1
.\mcpowers-shared\scripts\start_dev.ps1 -Build
```

启动脚本会自动：
1. 检查 docker / docker compose
2. 检查 `config/config_{env}.ini` 是否存在
3. 首次启动自动 `--build`，后续快速启动
4. 等待 5s 后验证 `/health` 端点

#### 21.7.5 数据持久化

```
project-root/
└── docker-data/
    ├── mysql-dev/      # MySQL 数据卷（git ignore）
    ├── mysql-test/
    ├── redis-dev/      # Redis 数据卷
    └── redis-test/
```

`.gitignore` 必须加：
```
docker-data/
```

#### 21.7.6 配置示例（config/config_dev.ini）

```ini
[admin_mysql]
host = 127.0.0.1
port = 3306
username = root
password = root_dev
db_name = {项目名}_dev
charset = utf8mb4

[admin_redis]
host = 127.0.0.1
port = 6379
password =
db = 0
```

> 💡 **关键设计**：app 容器内访问 mysql/redis 用**服务名**（如 `{项目名}-mysql`）作为 host，端口 3306/6379。
> 本地 `python app.py` 调试时用 `127.0.0.1`，因为宿主机已端口映射。
