---
name: mcpowers-crawler-dev
description: |
  Python 爬虫项目开发专项技能。当用户说"爬虫项目"、"爬虫开发"、"抓取数据"、"数据采集"时自动触发。

  本技能提供爬虫项目的完整开发规范，包括：
  - 目录结构（apps/general/ + 模块层）
  - 配置管理（INI配置文件 + sys.argv启动参数）
  - 任务源（Excel/API/Redis队列/数据库）
  - 结果存储（Redis缓存 + 后端API回调）
  - 请求封装（requests_try / requests_session_try）
  - 重试机制（retry装饰器 + 重试条件函数）
  - 异常处理（GeneralError / NeedDingtalkFailError）
  - 日志规范（分级日志 + 模块专用日志）
  - Docker部署

  **核心价值**：标准化爬虫项目结构、完善的任务包装器、规范的回调机制。

  **使用场景**：
  - 用户要创建爬虫项目
  - 用户要开发爬虫模块
  - 用户要求按爬虫规范开发

  **配合使用**：`mcpowers-workflow` 提供通用工作流程（12章完整内容）
---

# mcpowers-crawler-dev

Python 爬虫项目开发规范技能。

## Step 1: 识别核心规范

> ⚠️ **强制执行**，每次任务开始都必须执行。
>
> ⚠️ **重要**：本技能与 `mcpowers-workflow` 配合使用，`mcpowers-workflow` 提供完整的工作流程（12章内容），本技能提供爬虫专项开发内容。

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

根据 `docs/设计文档/` 下的设计文档，确认项目类型为**爬虫**。

### 1.3 识别技术锁规范

| 项目特征 | 技术锁规范 |
|:---------|:----------|
| 爬虫功能 | `爬虫规范.md` |

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
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/爬虫规范.md` |

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
| 2 | 爬虫规范.md | 任务包装器、重试机制、回调机制 |
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
| 技术锁规范是否匹配？ | ✅ 爬虫功能 → 爬虫规范.md |
| 环境检查 | ⏳ 待执行 |

**承诺**：本次任务将严格遵守上述所有规范，如有违背，愿视为不合格。
```

### 1.6 汇报项目情况

向用户汇报：
- 项目类型：爬虫
- 技术栈：Python + requests + Redis
- 本次需要遵守的规范清单

### 1.7 环境检查

执行 `~/.claude/skills/mcpowers-shared/docs/技术规范/开发环境规范.md` 中的检查命令，确认 Python 环境正常。

---

## Step 2: 爬虫专项开发

### 目录结构

```
project/
├── apps/
│   ├── general/            # 通用爬虫函数
│   │   ├── crawl_constants.py        # 通用常量
│   │   ├── crawl_functions.py       # 通用函数
│   │   ├── crawl_locks.py           # 文件锁
│   │   └── crawl_retry_conditions.py # 重试条件
│   └── {module}/           # 业务模块
│       ├── crawl_constants.py        # 模块常量
│       ├── crawl_functions.py       # 模块函数
│       ├── crawl_wrappers.py        # 任务包装器
│       ├── crawl_loggers.py         # 模块日志
│       ├── crawl_retry_conditions.py # 重试条件
│       ├── crawl_task_generators.py  # 任务生成器
│       └── crawl_scripts.py         # 脚本入口
├── common/
│   ├── constants.py         # 常量（BASE_DIR/REDIS_KEY_*/RUN_TYPE）
│   ├── functions.py        # 工具函数
│   └── confs.py           # 配置加载
├── config/
│   ├── config_dev.ini     # 开发环境
│   ├── config_test.ini    # 测试环境
│   └── config_prod.ini    # 生产环境
├── db/redis/
│   └── helpers.py         # Redis客户端（连接池）
├── utils/
│   ├── contexts.py        # 请求上下文管理器
│   ├── requests_sessions.py # Session管理
│   ├── concurrent_pools.py # 线程池
│   ├── loggings.py        # 日志封装
│   ├── exceptions.py       # 自定义异常
│   ├── pandas_op.py       # Excel/CSV操作
│   └── dingtalk.py        # 钉钉通知
├── main.py                 # 入口
├── requirements.txt
└── Dockerfile
```

### 配置管理

#### 配置文件（INI格式）

```ini
# config_dev.ini
[redis]
host = 127.0.0.1
port = 6379
password =
db = 2

[proxy]
pool_size = 10
timeout = 30

[callback_service]
host = http://api.example.com
```

#### 启动参数（sys.argv）

```python
# common/constants.py
import os
import sys

PLATFORM = os.name
IS_PRODUCT = True
IS_OUTER = False
IS_ONCE = False

sys_args = sys.argv[1:]
if sys_args:
    if '--test' in sys_args: IS_PRODUCT = False
    if '--outer' in sys_args: IS_OUTER = True
    if '--once' in sys_args: IS_ONCE = True

# 运行类型、线程数、数据源ID
RUN_TYPE = sys_args[0] if len(sys_args) > 0 else 'default'
RUN_THREAD_SIZE = int(sys_args[1]) if len(sys_args) > 1 else 1
DATASOURCE_ID = sys_args[2] if len(sys_args) > 2 else 'DEFAULT'
```

### 任务包装器

```python
def xxx_task_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        extra = args[-1]
        uid = f'{extra["id"]}'

        try:
            # 1. 任务分布式锁
            lock = redis_crawl.atomic_lock(f'{REDIS_KEY_STRING_LOCK_TASK_XXX}{uid}', ex=120)
            if not lock: return

            # 2. 执行任务
            result = func(*args, **kwargs)

            # 3. Redis缓存回调
            xxx_callback_success_redis(result, extra)

            # 4. 后端API回调
            xxx_callback_success(*result, extra)

            # 5. 删除任务锁
            redis_crawl.delete(f'{REDIS_KEY_STRING_LOCK_TASK_XXX}{uid}')
            return result

        except Exception as e:
            # 失败处理
            xxx_callback_fail_redis(hint, extra)
            xxx_callback_fail(hint, extra)
            redis_crawl.delete(f'{REDIS_KEY_STRING_LOCK_TASK_XXX}{uid}')
            return hint

    return wrapper
```

### 重试机制

```python
from retrying import retry

@xxx_task_wrapper
@retry(stop_max_attempt_number=3, wait_fixed=1500, retry_on_exception=xxx_retry_if_exception)
def xxx_crawl_run(product_id, extra):
    # 业务逻辑
    return result
```

#### 重试条件函数

```python
def xxx_retry_if_exception(e):
    hint = str(e)
    if check_hint_keywords(hint, ['代理ip失效', '接口超时', '接口连接错误', '状态码异常']):
        return True  # 可重试
    return False
```

### 请求封装

```python
from utils.contexts import requests_try, requests_session_try

# 独立请求
with requests_try('get', url, headers=headers, is_json_response=True) as resp:
    if type(resp) is str:
        raise GeneralError(resp)  # 请求失败
    data = resp.json()

# Session请求（保持cookie和代理）
session = get_valid_session()
with requests_session_try(session, 'post', url, json=data) as resp:
    if type(resp) is str:
        raise GeneralError(resp)
    data = resp.json()
```

### 异常类

| 异常 | 用途 | 钉钉通知 |
|:-----|:-----|:---------|
| `GeneralError` | 一般性异常 | 否 |
| `NeedDingtalkFailError` | 需要发送失败通知 | 失败通知 |
| `NeedDingtalkReminderError` | 需要发送提醒通知 | 温馨提示 |

### 任务源类型

| 类型 | 实现 |
|:-----|:-----|
| Excel | `xxx_query_task_args_excel()` |
| 后端API | `xxx_query_task_args_api()` |
| Redis队列 | `xxx_query_task_args_list()` |
| 数据库 | `xxx_query_task_args_db()` |

### 回调机制

```python
# 多级回调：Redis缓存 + API回调
def xxx_callback_success_redis(result, extra):
    """结果存入Redis供后续查询"""
    redis_crawl.hset(REDIS_KEY_HASH_XXX_SUCCESS_RESULT, extra['id'], json.dumps(result))

@retry(stop_max_attempt_number=3, wait_fixed=1500)
def xxx_callback_success(result, extra):
    host = service_api_conf['callback_service']
    url = f'{host}/api/{{project}}/saveResult'
    data = {'task_id': extra['id'], ...}
    with requests_try('post', url, json=data) as resp:
        if resp.json()['code'] != 200:
            raise GeneralError(f'回调失败')
```

### 日志分级

| 级别 | 方法 | 用途 |
|:-----|:-----|:-----|
| INFO | save_info | 正常流程日志 |
| ERROR | save_error | 可恢复错误 |
| CRITICAL | save_critical | 严重错误（traceback） |

### 模块日志实例

```python
# apps/review/crawl_loggers.py
review_request_log = Logger('review_request', 'logs', ...)  # 任务请求
review_result_log = Logger('review_result', 'logs', ...)    # 任务结果
review_retry_log = Logger('review_retry', 'logs', ...)     # 重试记录
review_error_log = Logger('review_error', 'logs', ...)      # 异常记录
```

### Docker 启动命令

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 命令格式
# python3 -u main.py <module> <thread_size> <datasource_id>
```

### 检查清单

#### 爬虫模块必查

- [ ] 使用任务包装器
- [ ] 使用重试装饰器
- [ ] 配置分布式锁
- [ ] 实现多级回调

#### 请求处理必查

- [ ] 使用上下文管理器
- [ ] 处理请求失败情况
- [ ] 实现重试条件

#### 异常处理必查

- [ ] 使用自定义异常类
- [ ] 失败时发送钉钉通知
- [ ] 异常信息脱敏过滤
- [ ] 符合 SOLID/KISS/DRY/YAGNI 原则
- [ ] 临时文件已清理