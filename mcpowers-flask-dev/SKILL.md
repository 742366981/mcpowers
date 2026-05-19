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

  **配合使用**：`mcpowers-workflow` 提供通用工作流程（12章完整内容）
---

# mcpowers-flask-dev

Flask 后端项目开发规范技能。

## Step 1: 识别核心规范

> ⚠️ **强制执行**，每次任务开始都必须执行。
>
> ⚠️ **重要**：本技能与 `mcpowers-workflow` 配合使用，`mcpowers-workflow` 提供完整的工作流程（12章内容），本技能提供 Flask 专项开发内容。

### 核心红线（违反视为不合格）

| 红线行为 | 违规后果 |
|:---------|:---------|
| **未经确认直接修改代码/文档** | 用户有权要求回滚 |
| **先写代码后补文档** | 视为不合格 |
| **多个操作后才 commit** | 视为不规范 |
| **只 commit 代码不 commit 文档** | 视为不规范 |
| **发现重复定义未处理** | 视为不合格 |
| **代码注释不完整** | 视为不合格 |
| **临时文件不清理** | 视为不规范 |
| **违反 SOLID/KISS/DRY/YAGNI** | 视为不合格 |

### 1.1 扫描规范目录

> ⚠️ **规范文件位于共享技能 `mcpowers-shared` 目录**
>
> ```bash
> ls ~/.claude/skills/mcpowers-shared/docs/技术规范/*.md
> ```

### 1.2 确定项目类型

根据 `docs/设计文档/` 下的设计文档，确认项目类型为**后端 + Flask**。

### 1.3 识别技术锁规范

| 项目特征 | 技术锁规范 |
|:---------|:----------|
| 后端 + Flask | `Flask后端规范.md` |

### 1.4 读取适用规范

必须读取以下规范文件：

| 优先级 | 规范文件 |
|:-------|:---------|
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/Git规范.md` |
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/代码同步修改规范.md` |
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/开发环境规范.md` |
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/设计规范.md` |
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/代码规范.md` |
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/细节记录规范.md` |
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/Flask后端规范.md` |

每读取一个文件，输出：`✓ 已读取：{文件路径}`

### 1.5 规范遵守承诺（强制）

**读取完所有规范后，必须向用户做出明确承诺**，输出：

```
## 规范遵守承诺

### ✅ 已完整阅读
本次任务涉及的 {N} 个规范文件，我已完整阅读：

| 序号 | 规范 | 核心条款 |
|:----:|:-----|:---------|
| 1 | Git规范.md | commit规范、提交信息格式 |
| 2 | Flask后端规范.md | 应用工厂、蓝图注册、docstring规范 |
| ... | ... | ... |

### 🚫 核心红线（本次必须遵守）
| 红线 | 违反后果 |
|:-----|:---------|
| 未经确认直接修改代码/文档 | 用户有权要求回滚 |
| 先写代码后补文档 | 视为不合格 |
| 多个操作后才 commit | 视为不规范 |
| 只 commit 代码不 commit 文档 | 视为不规范 |
| 发现重复定义未处理 | 视为不合格 |
| 代码注释不完整 | 视为不合格 |
| 临时文件不清理 | 视为不规范 |
| 违反 SOLID/KISS/DRY/YAGNI | 视为不合格 |

### 🔍 本次检查结果
| 检查项 | 结果 |
|:-------|:-----|
| 规范文件是否完整？ | ✅ 全部存在 |
| 核心红线是否清晰？ | ✅ 全部已知 |
| 技术锁规范是否匹配？ | ✅ 后端 + Flask → Flask后端规范.md |
| 环境检查 | ⏳ 待执行 |

**承诺**：本次任务将严格遵守上述所有规范，如有违背，愿视为不合格。
```

### 1.6 汇报项目情况

向用户汇报：
- 项目类型：后端（Flask）
- 技术栈：Flask + MySQL + Redis
- 本次需要遵守的规范清单

### 1.7 环境检查

执行 `~/.claude/skills/mcpowers-shared/docs/技术规范/开发环境规范.md` 中的检查命令，确认 Python 环境正常。

---

## Step 2: Flask 专项开发

### 目录结构

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

### 应用工厂模式

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

### 核心原则

| 原则 | 说明 |
|:-----|:-----|
| **禁止 sys.path** | 不使用 sys.path.insert/append |
| **禁止硬编码路径** | 使用 BASE_DIR + os.path.join |
| **禁止默认值** | 配置缺失必须启动失败 |
| **先写docstring** | 接口必须先写文档再写实现 |

### Swagger docstring 格式

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

### 必需字段

| 字段 | 必须 | 说明 |
|:-----|:-----|:-----|
| summary | ✅ | 接口简短描述 |
| description | ✅ | 接口详细描述 |
| parameters | ✅ | 请求参数 |
| responses | ✅ | 响应格式+examples |

### 装饰器

```python
# 登录装饰器
@login_required

# 权限装饰器
@permission_required('user:create', 'user:update')
```

### 响应格式

```python
# 成功响应
return api_success(data={'id': 1}, msg='操作成功')

# 错误响应
return api_error(400, '参数错误')

# 分页响应
return api_page(records, page_no, page_size, total_count)
```

### 检查清单

#### 接口开发必查

- [ ] docstring 先于代码编写
- [ ] 标题与 `---` 之间无空行
- [ ] parameters 包含完整字段
- [ ] responses 包含 examples
- [ ] 参数名符合规范（id / xxx_id）

#### 提交前必查

- [ ] 接口参数命名正确
- [ ] docstring 格式正确
- [ ] 配置通过 ENV_TYPE 动态加载
- [ ] 无调试代码残留
- [ ] 符合 SOLID/KISS/DRY/YAGNI 原则
- [ ] 临时文件已清理