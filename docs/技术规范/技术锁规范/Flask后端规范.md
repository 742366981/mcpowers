# Flask后端规范

本文档定义 Flask 后端项目的特定规范。

> **通用规范引用**：数据库、缓存、定时任务、部署等通用内容详见各自独立规范文档

---

## 1. 目录结构（强制）

### 1.1 整体目录结构

```
project/
├── apps/                              # 应用模块（蓝图）
│   ├── __init__.py                   # 应用工厂、蓝图注册
│   │
│   ├── system/                        # 系统管理模块
│   │   ├── auth/                      # 认证子模块
│   │   ├── user/                      # 用户子模块
│   │   ├── role/                      # 角色子模块
│   │   ├── permission/                # 权限子模块
│   │   ├── menu/                      # 菜单子模块
│   │   └── dict/                      # 字典子模块
│   │
│   ├── operation/                      # 运营管理模块
│   │   └── log/                       # 日志子模块
│   │
│   ├── file/                          # 文件管理模块
│   │   └── upload/                    # 上传子模块
│   │
│   └── business/                       # 业务模块（按需创建）
│
├── common/                             # 公共模块
│   ├── constants.py                   # 常量定义
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
│   │   ├── helpers.py                # SQLAlchemy实例、BaseModel
│   │   └── models/                   # 数据模型
│   └── redis/
│       └── helpers.py                 # Redis客户端
│
├── utils/                              # 工具函数
│   ├── responses.py                   # 统一响应
│   ├── decorators.py                  # 装饰器
│   ├── exceptions.py                  # 自定义异常
│   ├── validators.py                  # 参数验证
│   ├── loggings.py                    # 日志封装
│   └── scheduler.py                   # 定时任务调度器
│
├── db_init/                            # 数据库初始化
│   └── init_all.py                    # 初始化所有表和数据
│
├── jobs/                             # 定时任务
│   └── example.py                     # 示例任务
│
├── app.py                              # 应用入口
├── requirements.txt                    # 依赖
├── gunicorn_loader.py                  # Gunicorn启动器
└── Dockerfile                          # Docker镜像
```

### 1.2 模块划分规范

| 模块层级 | 模块名 | 说明 | 是否必须 |
|:---------|:-------|:-----|:--------|
| 一级 | `system/` | 系统管理：用户、角色、权限、菜单、字典、认证 | 必须 |
| 一级 | `operation/` | 运营管理：日志、监控 | 必须 |
| 一级 | `file/` | 文件管理：上传、附件 | 必须 |
| 一级 | `business/` | 业务模块：订单、商品等 | 按需扩展 |

---

## 2. 路径管理规范（强制）

### 2.1 禁止使用 sys.path（强制）

**严格禁止**在代码中使用 `sys.path.insert`、`sys.path.append` 等方式动态修改路径。

### 2.2 禁止硬编码绝对路径（强制）

**严格禁止**在代码中写死绝对路径。

### 2.3 统一使用 BASE_DIR（强制）

所有路径必须基于 `common.constants.BASE_DIR` 使用 `os.path.join` 拼接。

---

## 3. Flask应用工厂（强制）

```python
def create_app(protect_swagger=True):
    app = Flask(__name__)

    # 基础配置
    app.config['SECRET_KEY'] = config.get('secret_key')
    app.config['DEBUG'] = config.get('debug').lower() == 'true'
    app.json.ensure_ascii = False

    # 数据库配置
    # ...

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    compress.init_app(app)
    CORS(app, resources={r'/*': {'origins': cors_origins_list}})

    # 中间件
    register_blueprints(app)
    register_error_handlers(app)
    register_swagger(app, protect=protect_swagger)

    return app
```

---

## 4. 配置管理（强制）

### 4.1 配置加载器（强制）

> **强制要求：配置禁止使用默认值**
>
> 所有配置项**必须**从配置文件读取，**禁止**使用默认值 fallback。

### 4.2 配置文件格式（强制）

```ini
# config_dev.ini / config_test.ini / config_prod.ini
# 由 ENV_TYPE 控制加载哪个文件

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
port = 8000

[cors]
origins = *
supports_credentials = true
```

---

## 5. 中间件（强制）

### 5.1 请求ID中间件（强制）

```python
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

记录请求和响应日志，包含 request_id、user_id、method、path、cost_time、status_code。

---

## 6. 日志规范（强制）

### 6.1 日志封装类（强制）

```python
class Logger:
    def __init__(self, name, folder, type_=1, backup_count=9, vol=1, is_switch=True, is_save_file=False, is_print_console=True):
        # ...

    def save_critical(self, msg): ...
    def save_error(self, msg): ...
    def save_warning(self, msg): ...
    def save_info(self, msg): ...
    def save_debug(self, msg): ...
```

### 6.2 预定义日志实例

```python
admin_request_log = Logger('admin_request', 'logs', is_switch=True, is_save_file=True, is_print_console=True)
admin_response_log = Logger('admin_response', 'logs', is_switch=True, is_save_file=True, is_print_console=True)
general_log = Logger('general', 'logs', is_switch=True, is_save_file=True, is_print_console=True)
```

---

## 7. 响应规范（强制）

### 7.1 Flask 响应实现（强制）

```python
def api_success(data=None, msg='success', code=0):
    response = {'code': code, 'msg': msg}
    if data is not None:
        response['data'] = data
    return jsonify(response)


def api_error(code, msg=None):
    if msg is None:
        msg = get_error_message(code)
    response = {'code': code, 'msg': msg}
    return jsonify(response)


def api_page(records, page_no, page_size, total_count):
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

## 8. 认证授权（强制）

### 8.1 登录装饰器（强制）

```python
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

### 8.2 权限装饰器（强制）

检查用户角色权限，支持 `*` 通配符表示全部权限。

---

## 9. Swagger文档（强制）

### 9.1 docstring格式要求（强制）

> **重要：标题与`---`之间不能有空行**

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
          example: e10adc3949ba59abbe56e057f20f883e
responses:
  200:
    description: 登录成功
    examples:
      application/json:
        code: 0
        data:
          token: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
        msg: "success"
"""
    # 视图函数实现
```

---

## 10. 环境变量（强制）

### 10.1 环境类型（强制）

```python
ENV_TYPE = 'dev'
sys_args = sys.argv[1:]
if sys_args:
    if '--test' in sys_args:
        ENV_TYPE = 'test'
    elif '--prod' in sys_args:
        ENV_TYPE = 'prod'

IS_PRODUCT = ENV_TYPE == 'prod'
```

### 10.2 启动命令（强制）

```bash
python app.py          # 开发环境
python app.py --test   # 测试环境
python app.py --prod   # 生产环境
```

---

## 附录

### A. 相关文档

| 文档 | 位置 |
|:-----|:-----|
| API通用规范 | `通用规范/API规范.md` |
| 数据库规范 | `通用规范/数据库规范.md` |
| 缓存规范 | `通用规范/缓存规范.md` |
| 定时任务规范 | `通用规范/定时任务规范.md` |
| 部署规范 | `通用规范/部署规范.md` |
