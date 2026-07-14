---
title: API版本管理规范
type: tech-spec
applies_to: [Flask后端]
priority: required
version: 1.1
last_updated: 2026-07-14
---

# API 版本管理规范

本文档定义 API 版本管理策略，确保接口演进时不破坏老客户端。

> **核心原则**：**渐进式演进** —— 永远保持向后兼容；破坏性变更必须走新版本

---

## 1. 版本策略选择（强制）

### 1.1 两种主流方案对比

| 方案 | 路径示例 | 优点 | 缺点 | 适用场景 |
|:-----|:---------|:-----|:-----|:---------|
| **URL 路径版本**（推荐） | `/api/v1/user/list` | 直观、易调试、缓存友好 | URL 较长 | **本规范默认采用** |
| Header 版本 | `/api/user/list` + `Accept: application/vnd.api.v2+json` | URL 干净 | 难调试、难缓存 | 公开 API |

### 1.2 本规范强制要求

> ⚠️ **所有新项目必须使用 URL 路径版本**

```python
# ✅ 推荐
@user_bp.route('/api/v1/user/list', methods=['GET'])

# ❌ 禁止（无版本号）
@user_bp.route('/api/user/list', methods=['GET'])
```

---

## 2. Breaking Change 定义（强制）

### 2.1 什么算 Breaking Change

| 类型 | 示例 | 是否 Breaking |
|:-----|:-----|:--------------|
| **删除接口** | `/user/detail` 下线 | ✅ 是 |
| **修改路径** | `/user/list` → `/users/list` | ✅ 是 |
| **修改 HTTP 方法** | POST → PUT | ✅ 是 |
| **删除响应字段** | `data.role_name` 字段移除 | ✅ 是 |
| **修改字段类型** | `id: int` → `id: string` | ✅ 是 |
| **修改必填参数** | 选填 → 必填 | ✅ 是 |
| **重命名字段** | `username` → `user_name` | ✅ 是 |

### 2.2 什么**不算** Breaking Change

| 类型 | 是否兼容 |
|:-----|:---------|
| **新增接口** | ✅ 兼容 |
| **新增可选请求参数** | ✅ 兼容 |
| **新增响应字段** | ✅ 兼容 |
| **新增错误码** | ✅ 兼容 |

---

## 3. 版本演进流程（强制）

### 3.1 触发新版本的条件

**满足任一即需新建版本**：
- [ ] 计划删除某个接口
- [ ] 计划重命名/移动路径
- [ ] 计划修改必填参数
- [ ] 计划修改响应字段类型
- [ ] 计划重命名字段

### 3.2 标准流程

```
1. 提案：issue/PRD 中说明 breaking change 内容
   ↓
2. 评审：架构师 + 前后端负责人签字
   ↓
3. 开发：v1 旁新建 v2（不直接修改 v1）
   ↓
4. 文档：swagger_template.md 加 v2 模板
   ↓
5. 通知：邮件/企微通知所有 API 消费者（6个月废弃期）
   ↓
6. 下线：6个月后 v1 返回 410 Gone
```

### 3.3 完整时间线示例

| 时间点 | 动作 | v1 状态 | v2 状态 |
|:-------|:-----|:--------|:--------|
| T0 | v2 开发 | ✅ 正常 | 🚧 开发中 |
| T+0 | v2 上线 | ✅ 正常（响应头加 `Deprecation: true`） | ✅ 正常 |
| T+1M | 通知消费者 | ✅ 正常 | ✅ 正常 |
| T+6M | v1 标记 Sunset | ⚠️ `Sunset: Wed, 01 Jan 2025 00:00:00 GMT` | ✅ 推荐 |
| T+12M | v1 返回 410 | ❌ 410 Gone | ✅ 唯一推荐 |
| T+15M | v1 下线 | ❌ 404 | ✅ 唯一推荐 |

---

## 4. 多版本并行实现（强制）

### 4.1 目录结构

```
apps/
├── v1/                          # v1 版本
│   ├── __init__.py
│   ├── user/views.py
│   └── order/views.py
└── v2/                          # v2 版本（按需）
    ├── __init__.py
    └── user/views.py
```

### 4.2 蓝图注册

```python
# apps/__init__.py

def register_blueprints(app):
    from apps.v1.user.views import user_bp as user_bp_v1
    app.register_blueprint(user_bp_v1, url_prefix='/api/v1/user')

    # v2 按需启用
    # from apps.v2.user.views import user_bp as user_bp_v2
    # app.register_blueprint(user_bp_v2, url_prefix='/api/v2/user')
```

### 4.3 跨版本复用业务逻辑

```python
# apps/services/user_service.py
class UserService:
    def get_user_detail(self, user_id):
        return User.query.get(user_id)

# apps/v1/user/views.py
@user_bp.route('/detail', methods=['GET'])
def detail():
    user = UserService().get_user_detail(request.args.get('id'))
    return api_success({'id': user.id, 'name': user.username})  # v1 字段叫 name

# apps/v2/user/views.py
@user_bp.route('/detail', methods=['GET'])
def detail():
    user = UserService().get_user_detail(request.args.get('id'))
    return api_success({
        'id': user.id,
        'username': user.username,  # v2 升级
        'avatar_url': user.avatar_url,  # v2 新增
    })
```

---

## 5. 废弃响应头（推荐）

### 5.1 关键响应头

| Header | 示例值 | 含义 |
|:-------|:-------|:-----|
| `Deprecation` | `true` | 标记接口已废弃 |
| `Sunset` | `Wed, 01 Jan 2025 00:00:00 GMT` | 下线时间 |
| `Link` | `</api/v2/user/detail>; rel="successor-version"` | 推荐替代版本 |

### 5.2 Flask 实现

```python
@app.after_request
def add_deprecation_headers(response):
    if request.path.startswith('/api/v1/'):
        response.headers['Deprecation'] = 'true'
        response.headers['Sunset'] = 'Wed, 01 Jan 2025 00:00:00 GMT'
        response.headers['Link'] = '</api/v2' + request.path[7:] + '>; rel="successor-version"'
    return response
```

---

## 6. ❌ 禁止（反模式）

| 禁止行为 | 后果 | 正确做法 |
|:---------|:-----|:---------|
| ❌ 直接修改 v1 接口响应 | 破坏老客户端 | 新建 v2，v1 保持不变 |
| ❌ URL 中用日期做版本 | 不可读 | 使用 v1/v2 |
| ❌ 跳过 6 个月废弃期直接删除 | 客户端崩溃 | 走标准流程（§3.2） |
| ❌ 超过 3 个版本同时并行 | 维护成本爆炸 | 强制下线老版本 |

---

## 附录

### A. 相关文档

| 文档 | 位置 |
|:-----|:-----|
| API规范 | `API规范.md` |
| Flask后端规范 | `Flask后端规范.md`（蓝图注册） |
