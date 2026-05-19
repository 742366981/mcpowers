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
---

# mcpowers-vue-dev

Vue 3 前端项目开发规范技能。

## 触发词

| 触发词 | 场景 |
|:-------|:-----|
| Vue项目 | 创建新的 Vue 项目 |
| Vue前端 / 前端项目 | 开发前端页面 |
| 用Vue开发 | 指定使用 Vue 框架 |

## 技术栈

| 技术 | 说明 |
|:-----|:-----|
| Vue | 3.x (Composition API + `<script setup>`) |
| Vite | 5.x 构建工具 |
| Vue Router | 4.x |
| Pinia | 2.x 状态管理 |
| Axios | HTTP 客户端 |

## 项目结构

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

## 环境变量

| 文件 | 用途 |
|:-----|:-----|
| `.env.development` | 开发环境 |
| `.env.test` | 测试环境 |
| `.env.production` | 生产环境 |

| 变量 | 说明 |
|:-----|:-----|
| `VITE_API_BASE_URL` | API 基础路径 |
| `VITE_API_TARGET` | 开发代理目标地址 |

## axios 实例配置

```javascript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000
})
```

## 请求拦截器

```javascript
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

## 响应拦截器

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

## API 模块结构

```javascript
export const api = {
  get(url, params) { return axiosInstance.get(url, { params }) },
  post(url, data) { return axiosInstance.post(url, data) },
  put(url, data) { return axiosInstance.put(url, data) },
  delete(url, params) { return axiosInstance.delete(url, { params }) }
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

## API 路径规范

| 操作 | URL 格式 |
|:-----|:---------|
| 列表 | /xxx/list |
| 详情 | /xxx/detail |
| 新增 | /xxx/create |
| 更新 | /xxx/update |
| 删除 | /xxx/delete |
| 批量删除 | /xxx/batch-delete |

## 页面组件结构

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

## 变量命名

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

## 错误处理

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

## Pinia Store

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

## 检查清单

### API 调用必查

- [ ] 使用 try-catch 包裹
- [ ] 加载失败时清空数据
- [ ] finally 中关闭 loading

### 组件开发必查

- [ ] 变量命名符合规范
- [ ] 弹窗使用 `showModal`
- [ ] 编辑状态使用 `isEdit`
