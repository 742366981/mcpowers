# API 测试自动生成（基于 OpenAPI Spec）

> **核心理念**：spec = 测试用例的元数据，**自动派生 fuzz / 契约测试**，零测试编写成本。

---

## 0. 与现有工具的关系（重要！避免重复造轮子）

| 工具 | 用途 | 何时用 |
|:-----|:-----|:-------|
| **`tools/export_docs.py`** | 一键导出 `openapi.json` | **Step 6 必跑**（生成 schemathesis/dredd 直接消费的 spec 文件） |
| **`schemathesis`** | Fuzz 测试（property-based） | **Step 7 必跑**（发现 422/500/性能 bug） |
| **`dredd`** | 契约测试（响应结构/类型校验） | **Step 7 必跑**（验证响应符合 spec） |
| **`mcpowers-autoTest`** | 自动化测试编排 + 报告 | **Step 7 可选**（汇总报告 + bug 分类） |

> ⚠️ **禁止**：本文件不得重新定义 spec 导出逻辑（已有 `export_docs.py`）。
> ⚠️ **禁止**：本文件不得重新定义 docstring 模板（已有 `API文档/` 两份模板）。

**典型调用链**：
```
1. 后端开发完接口（docstring 完整）
2. python tools/export_docs.py          # 已有工具：导出 openapi.json
3. schemathesis run openapi.json   # 本文件：fuzz 测试
4. dredd                                # 本文件：契约测试
5. mcpowers-autoTest                    # 可选：汇总报告
```

---

## 1. 整体流程

```
后端 Flask（docstring 完整）
        ↓ Flasgger 自动生成
/apispec_1.json（OpenAPI 2.0 规范）
        ↓ schemathesis / dredd
自动化测试用例（fuzz / 契约）
        ↓ 失败 → 报错 / 报告
bug 定位 + 修复
```

---

## 2. 工具选型

| 工具 | 测试类型 | 特点 |
|:-----|:---------|:-----|
| **schemathesis** | Fuzz 测试（基于 property-based testing） | 自动生成边界值、异常值，发现 422/500 错误 |
| **dredd** | 契约测试（基于 spec 期望） | 验证响应结构/类型是否符合 spec |
| tavern | 集成测试 | YAML 编写测试用例，适合复杂场景 |
| postman / newman | 手工转自动 | 学习成本低，但需手工编写 |

> 推荐组合：**schemathesis（fuzz）+ dredd（契约）**，与 `mcpowers-autoTest` 衔接。

---

## 3. schemathesis（Fuzz 测试，强烈推荐）

### 3.1 安装

```bash
pip install schemathesis
```

### 3.2 基本用法

```bash
# 启动 Flask 服务后执行
schemathesis run http://localhost:5000/apispec_1.json
```

**自动生成测试场景**：
- ✅ 合法值（每个字段的有效类型）
- ✅ 边界值（最小/最大长度、边界数字）
- ✅ 异常值（空字符串、超长字符串、负数、null）
- ✅ 缺失字段、额外字段
- ✅ 类型错误（字符串传入数字字段）

**检测的 bug 类型**：
- 500 错误（未处理的异常）
- 422 错误（参数校验缺失）
- 性能问题（响应时间过长）
- 数据泄漏（响应中包含意外字段）

### 3.3 与鉴权配合

```bash
# JWT token（如果接口需要鉴权）
schemathesis run http://localhost:5000/apispec_1.json \
  --headers "Authorization: Bearer $JWT_TOKEN"

# Basic Auth（如果 Swagger 用 Basic Auth 加密）
schemathesis run http://localhost:5000/apispec_1.json \
  --auth user:pass
```

### 3.4 CI 集成

```yaml
# .github/workflows/api-fuzz.yml
name: API Fuzz Test

on: [push, pull_request]

jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install schemathesis pytest
      - name: 启动后端
        run: |
          pip install -r requirements.txt
          python app.py &
          sleep 10
      - name: 运行 fuzz 测试
        run: schemathesis run http://localhost:5000/apispec_1.json --checks all
```

---

## 4. dredd（契约测试）

### 4.1 安装

```bash
npm install -g dredd
```

### 4.2 配置文件（`dredd.yml`）

```yaml
reporter: [markdown, junit]
output: [./reports/api-contract.md, ./reports/api-contract.xml]
custom: {}

# 后端地址
endpoint: http://localhost:5000

# Spec 文件
api-description: ./apispec_1.json

# 仅在 dev 模式运行（生产环境另外配）
dry-run: false

# 跳过登录等需要特殊流程的接口
hooks: ./dredd-hooks.js

# 鉴权
headers:
  Authorization: Bearer dev-token-123
```

### 4.3 Hook 处理特殊场景（`dredd-hooks.js`）

```javascript
// 登录前获取 token
before('登录 > 登录', (transaction) => {
  transaction.request.headers['Authorization'] = '';
});

after('登录 > 登录', (transaction) => {
  // 保存 token 供后续接口使用
  global.authToken = transaction.real.body.data.token;
});

beforeEach((transaction) => {
  // 自动为所有接口注入 token
  if (transaction.name !== '登录 > 登录') {
    transaction.request.headers['Authorization'] = `Bearer ${global.authToken}`;
  }
});
```

### 4.4 执行

```bash
dredd
```

**检测的 bug 类型**：
- 响应结构与 spec 不一致（字段缺失/多余）
- 响应类型与 spec 不一致（字符串变数字）
- 必填字段缺失

---

## 5. 与 mcpowers-autoTest 的衔接

| 维度 | mcpowers-autoTest | schemathesis / dredd |
|:-----|:------------------|:---------------------|
| 触发方式 | 用户说"跑自动化测试" | 本技能 Step 7 自动触发 |
| 测试用例来源 | 手工编写 / TDD | spec 自动生成 |
| 报告格式 | `mcpowers-autoTest` 定义的 JSON schema | dredd 自带 markdown/junit |
| Bug 分类 | 二维分类（前端/后端 + P0/P1/P2） | 需额外处理 |
| 数据清理 | 自动清理 `test_` / `tmp_` 前缀数据 | schemathesis 默认无清理 |

**推荐工作流**：

```
1. 后端改完接口
2. 本技能 Step 7 触发 schemathesis + dredd
3. 测试报告输出到 reports/
4. 如有失败 → 自动调 mcpowers-bugfix 分析
5. mcpowers-autoTest 跑完整回归测试
6. mcpowers-code-review 自审
```

---

## 6. 测试报告位置与命名

```
backend/
└── reports/
    ├── api-fuzz-20260714.md         # schemathesis 报告
    ├── api-contract-20260714.md     # dredd 报告
    └── api-test-summary.json        # 汇总报告（mcpowers-autoTest 可消费）
```

---

## 7. 常见问题

### 7.1 schemathesis 报"Schema not found"

**原因**：spec 中 schema 引用格式问题（如 `$ref: "#/definitions/User"`）。

**解决**：
```bash
# 升级 schemathesis 到最新版本（>= 3.0）
pip install -U schemathesis
```

### 7.2 dredd 报"Expected status code 200 but got 401"

**原因**：鉴权未传递或错误。

**解决**：检查 `dredd-hooks.js` 中的 token 注入逻辑。

### 7.3 接口需要特定数据（如数据库中存在的 ID）

**解决**：在 hook 中通过 API 创建测试数据，保存 ID 供后续接口使用。

---

## 8. 反模式（禁止）

- ❌ 手工编写测试用例而不利用 spec（重复劳动）
- ❌ 只跑 happy path 不跑 fuzz（漏掉大量边界 bug）
- ❌ CI 中不执行 fuzz（生产环境才发现 500）
- ❌ 测试报告不存档（无法追溯历史）
- ❌ 测试数据不清理（污染数据库）

---

## 9. v2.4.0 增量：一键运行脚本

> **v2.4.0 新增** — 封装了 `scripts/run-api-tests.sh`，避免每个项目重复写启动 + 鉴权 + fuzz 配置。

### 9.1 一键运行（替代手动 schemathesis 命令）

```bash
# 基础运行（默认 http://localhost:5000，无 token）
bash scripts/run-api-tests.sh

# 自定义目标 + 鉴权
bash scripts/run-api-tests.sh \
    --base-url http://staging.example.com \
    --token "eyJhbGciOi..."

# 自定义 spec 路径
bash scripts/run-api-tests.sh --spec path/to/spec.json
```

> 完整源码见 `mcpowers-shared/scripts/run-api-tests.sh`，**直接复制到项目根目录的 `scripts/` 即可使用**。

### 9.2 在 `mcpowers-autoTest` 中调用

```python
# 调用 mcpowers-autoTest 时，可选运行：
subprocess.run(["bash", "scripts/run-api-tests.sh"])
```

### 9.3 跨项目复用

```bash
# 项目初始化时，从 mcpowers 复制
cp path/to/mcpowers/skills/mcpowers-shared/scripts/run-api-tests.sh \
   my-project/scripts/

# CI 中调用
- name: API fuzz tests
  run: bash scripts/run-api-tests.sh --base-url ${{ env.STAGING_URL }}
```