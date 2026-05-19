---
name: mcpowers-vue-dev
description: |
  Vue 3 前端开发专项技能。当用户说"Vue项目"、"Vue前端"、"用Vue开发"、"前端项目"时自动触发。

  本技能提供 Vue 3 前端项目的完整开发规范，包括：
  - 技术栈（Vue 3 + Composition API + Vite + Vue Router + Pinia + Axios）
  - 项目结构（api/components/router/stores/views）
  - API调用（axios封装、拦截器、响应处理）
  - 组件规范（页面结构、变量命名、样式规范）
  - 状态管理（Pinia Store）
  - Token管理（localStorage + Bearer Header）
  - 错误处理（try-catch + Toast）

  **核心价值**：标准化Vue项目结构、统一API调用方式、规范组件命名。

  **使用场景**：
  - 用户要创建 Vue 前端项目
  - 用户要开发 Vue 页面组件
  - 用户要求按 Vue 规范开发前端

  **配合使用**：`mcpowers-workflow` 提供通用工作流程（12章完整内容）
---

# mcpowers-vue-dev

Vue 3 前端项目开发规范技能。

## Step 1: 识别核心规范

> ⚠️ **强制执行**，每次任务开始都必须执行。
>
> ⚠️ **重要**：本技能与 `mcpowers-workflow` 配合使用，`mcpowers-workflow` 提供完整的工作流程（12章内容），本技能提供 Vue 专项开发内容。

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

根据 `docs/设计文档/` 下的设计文档，确认项目类型为**前端 + Vue**。

### 1.3 识别技术锁规范

| 项目特征 | 技术锁规范 |
|:---------|:----------|
| 前端 + Vue | `Vue前端规范.md` |

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
| 必须 | `~/.claude/skills/mcpowers-shared/docs/技术规范/Vue前端规范.md` |

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
| 2 | Vue前端规范.md | 组件结构、API调用、状态管理 |
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
| 技术锁规范是否匹配？ | ✅ 前端 + Vue → Vue前端规范.md |
| 环境检查 | ⏳ 待执行 |

**承诺**：本次任务将严格遵守上述所有规范，如有违背，愿视为不合格。
```

### 1.6 汇报项目情况

向用户汇报：
- 项目类型：前端（Vue 3）
- 技术栈：Vue 3 + Vite + Vue Router + Pinia + Axios
- 本次需要遵守的规范清单

### 1.7 环境检查

执行 `~/.claude/skills/mcpowers-shared/docs/技术规范/开发环境规范.md` 中的检查命令，确认 Node.js 环境正常。

---

## Step 2: Vue 专项开发

### 技术栈

| 技术 | 说明 |
|:-----|:-----|
| Vue | 3.x (Composition API + `<script setup>`) |
| Vite | 5.x 构建工具 |
| Vue Router | 4.x |
| Pinia | 2.x 状态管理 |
| Axios | HTTP 客户端 |

### 项目结构

```
project/
├── src/
│   ├── api/              # API 封装
│   │   └── index.js     # axios 实例、拦截器
│   ├── components/        # 公共组件
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia 状态管理
│   ├── styles/           # 全局样式
│   ├── utils/            # 工具函数
│   ├── views/            # 页面组件
│   ├── App.vue
│   └── main.js
├── docs/                 # 文档
└── package.json
```

### 环境变量

| 文件 | 用途 |
|:-----|:-----|
| `.env.development` | 开发环境 |
| `.env.test` | 测试环境 |
| `.env.production` | 生产环境 |

| 变量 | 说明 |
|:-----|:-----|
| `VITE_API_BASE_URL` | API 基础路径 |
| `VITE_API_TARGET` | 开发代理目标地址 |

### axios 实例配置

```javascript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000
})
```

### 请求拦截器

```javascript
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### 响应拦截器

```javascript
axiosInstance.interceptors.response.use(
  (response) => {
    const res = response.data

    if (res.code === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.href = '/login'
      return Promise.reject(new Error(res.msg || '登录已过期'))
    }

    if (res.code !== 0) {
      return Promise.reject(new Error(res.msg || '请求失败'))
    }
    return res
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### API 模块结构

```javascript
export const api = {
  get(url, params) { return axiosInstance.get(url, { params }) },
  post(url, data) { return axiosInstance.post(url, data) },
  put(url, data) { return axiosInstance.put(url, data) },
  delete(url, params) { return axiosInstance.delete(url, params) }
}

export const baseApi = {
  moduleName: {
    list: (params) => api.get('/module-name/list', params),
    detail: (id) => api.get('/module-name/detail', { id }),
    create: (data) => api.post('/module-name/create', data),
    update: (data) => api.post('/module-name/update', data),
    delete: (id) => api.post('/module-name/delete', { id }),
    batchDelete: (ids) => api.post('/module-name/batch-delete', { ids }),
    import: (formData) => axiosInstance.post('/module-name/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    export: () => downloadBlob('/module-name/export'),
    template: () => downloadBlob('/module-name/template/download', {}, 'GET')
  }
}
```

### API 路径规范

| 操作 | URL 格式 |
|:-----|:---------|
| 列表 | /xxx/list |
| 详情 | /xxx/detail |
| 新增 | /xxx/create |
| 更新 | /xxx/update |
| 删除 | /xxx/delete |
| 批量删除 | /xxx/batch-delete |

### 页面组件结构

```vue
<template>
  <div class="page">
    <!-- 搜索栏 -->
    <div class="card mb-4">
      <div class="card-body">
        <div class="toolbar">
          <div class="toolbar-left">...</div>
          <div class="toolbar-right">
            <button class="btn btn-primary" @click="handleSearch">搜索</button>
            <button class="btn btn-ghost" @click="handleReset">重置</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">标题</span>
        <div class="toolbar-right">操作按钮</div>
      </div>
      <div class="table-container">
        <table class="table">...</table>
      </div>
      <div class="pagination">...</div>
    </div>

    <!-- 编辑弹窗 -->
    <div :class="['modal-overlay', { active: showModal }]" @click.self="closeModal">
      <div class="modal">...</div>
    </div>
  </div>
</template>

<script setup>
const loading = ref(false)
const showModal = ref(false)
const tableData = ref([])
const pageNo = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)
const searchForm = ref({})
const form = ref({})

onMounted(() => loadData())
</script>
```

### 变量命名

```javascript
// 数据
const tableData = ref([])
const loading = ref(false)
const submitting = ref(false)

// 分页
const pageNo = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)

// 弹窗
const showModal = ref(false)
const isEdit = ref(false)
const editId = ref(null)

// 表单
const form = ref({})
const searchForm = ref({})

// 选择
const selectedIds = ref([])
```

### 错误处理

```javascript
async function loadData() {
  loading.value = true
  try {
    const res = await baseApi.moduleName.list(params)
    tableData.value = res.data.records || []
    totalCount.value = res.data.total_count || 0
  } catch (e) {
    showToast(e.message || '加载数据失败', 'error')
    tableData.value = []
  } finally {
    loading.value = false
  }
}
```

### Pinia Store

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(
    localStorage.getItem('userInfo')
      ? JSON.parse(localStorage.getItem('userInfo'))
      : null
  )

  const isLoggedIn = computed(() => !!token.value)

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  return { token, userInfo, isLoggedIn, logout }
})
```

### 检查清单

#### API 调用必查

- [ ] 使用 try-catch 包裹
- [ ] 加载失败时清空数据
- [ ] finally 中关闭 loading

#### 组件开发必查

- [ ] 变量命名符合规范
- [ ] 弹窗使用 `showModal`
- [ ] 编辑状态使用 `isEdit`
- [ ] 符合 SOLID/KISS/DRY/YAGNI 原则
- [ ] 临时文件已清理