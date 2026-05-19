---
name: mcpowers-flask-dev
description: |
  Flask 后端开发专项技能。当用户说"Flask项目"、"Flask后端"、"用Flask开发"、"Python后端"时自动触发。
  
  本技能提供 Flask 后端项目的完整开发规范，包括：
  - 目录结构（应用工厂、蓝图、模块划分）
  - 配置管理（环境变量、配置加载器）
  - 中间件（请求ID、日志）
  - 异常处理、错误码、响应规范
  - 认证授权（装饰器、Token管理）
  - Swagger文档（docstring格式、导出）
  - Gunicorn部署
  
  **核心价值**：标准化Flask项目结构、强制docstring先行、完整接口文档。
  
  **使用场景**：
  - 用户要创建 Flask 后端项目
  - 用户要开发 Flask 接口
  - 用户要求按 Flask 规范开发后端
---

# mcpowers-flask-dev

Flask 后端项目开发规范技能。

## 触发词

| 触发词 | 场景 |
|:-------|:-----|
| Flask项目 | 创建新的 Flask 项目 |
| Flask后端 / Python后端 | 开发后端接口 |
| 用Flask开发 | 指定使用 Flask 框架 |

## 目录结构

```
project/
├── apps/                    # 应用模块（蓝图）
│   ├── __init__.py         # 应用工厂、蓝图注册
│   ├── system/             # 系统管理模块
│   │   ├── auth/          # 认证子模块
│   │   ├── user/          # 用户子模块
│   │   ├── role/          # 角色子模块
│   │   ├── permission/    # 权限子模块
│   │   ├── menu/          # 菜单子模块
│   │   └── dict/          # 字典子模块
│   ├── operation/          # 运营管理模块
│   │   └── log/           # 日志子模块
│   ├── file/              # 文件管理模块
│   │   └── upload/        # 上传子模块
│   └── business/           # 业务模块（按需）
├── common/                  # 公共模块
│   ├── constants.py       # 常量定义
│   ├── codes.py           # 错误码定义
│   └── settings.py         # 配置加载器
├── config/                  # 配置文件
│   ├── config_dev.ini     # 开发环境
│   ├── config_test.ini    # 测试环境
│   └── config_prod.ini    # 生产环境
├── db/                     # 数据库相关
│   ├── mysql/             # MySQL (SQLAlchemy)
│   │   ├── helpers.py     # 实例、BaseModel
│   │   └── models/        # 数据模型
│   └── redis/
│       └── helpers.py     # Redis客户端
├── utils/                  # 工具函数
│   ├── responses.py       # 统一响应
│   ├── decorators.py      # 装饰器
│   ├── exceptions.py      # 自定义异常
│   ├── middleware.py      # 请求ID中间件
│   ├── request_log.py     # 请求日志
│   └── loggings.py        # 日志封装
├── docs/                   # 文档
├── tools/                  # 工具脚本
│   └── export_docs.py     # API文档导出
├── app.py                  # 应用入口
├── requirements.txt
└── gunicorn_loader.py     # Gunicorn启动器
```

## 应用工厂模式

```python
# apps/__init__.py

def create_app(protect_swagger=True):
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = config.get('secret_key')
    
    # 数据库
    from db.mysql.helpers import db
    db.init_app(app)
    
    # CORS
    CORS(app, resources={r'/*': {'origins': '*'}})
    
    # 中间件
    from utils.middleware import init_request_id
    init_request_id(app)
    
    # 蓝图注册
    register_blueprints(app)
    
    # Swagger
    register_swagger(app, protect=protect_swagger)
    
    return app
```

## 核心原则

| 原则 | 说明 |
|:-----|:-----|
| **禁止 sys.path** | 不使用 sys.path.insert/append |
| **禁止硬编码路径** | 使用 BASE_DIR + os.path.join |
| **禁止默认值** | 配置缺失必须启动失败 |
| **先写docstring** | 接口必须先写文档再写实现 |

## Swagger docstring 格式

> ⚠️ **标题与 `---` 之间不能有空行**

```python
@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录
---
tags:
  - 系统管理/认证管理
summary: 用户登录
description: 使用用户名和密码登录，返回Token。
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
    # 视图函数实现
```

## 必需字段

| 字段 | 必须 | 说明 |
|:-----|:-----|:-----|
| summary | ✅ | 接口简短描述 |
| description | ✅ | 接口详细描述 |
| parameters | ✅ | 请求参数 |
| responses | ✅ | 响应格式+examples |

## 装饰器

```python
# 登录装饰器
@login_required

# 权限装饰器
@permission_required('user:create', 'user:update')
```

## 响应格式

```python
# 成功响应
return api_success(data={'id': 1}, msg='操作成功')

# 错误响应
return api_error(400, '参数错误')

# 分页响应
return api_page(records, page_no, page_size, total_count)
```

## 检查清单

### 接口开发必查

- [ ] docstring 先于代码编写
- [ ] 标题与 `---` 之间无空行
- [ ] parameters 包含完整字段
- [ ] responses 包含 examples
- [ ] 参数名符合规范（id / xxx_id）

### 提交前必查

- [ ] 接口参数命名正确
- [ ] docstring 格式正确
- [ ] 配置通过 ENV_TYPE 动态加载
- [ ] 无调试代码残留
