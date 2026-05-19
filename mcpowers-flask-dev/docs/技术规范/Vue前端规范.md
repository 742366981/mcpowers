# Vue前端规范

本文档定义 Vue 3 前端项目的通用规范。

---

## 1. 技术栈（强制）

| 技术 | 说明 |
|:-----|:-----|
| Vue | 3.x (Composition API + `<script setup>`) |
| Vite | 5.x 构建工具 |
| Vue Router | 4.x |
| Pinia | 2.x 状态管理 |
| Axios | HTTP 客户端 |

---

## 2. 项目结构（强制）

```
project/
├── src/
│   ├── api/           # API 封装
│   │   └── index.js   # axios 实例、拦截器、API 方法
│   ├── components/     # 公共组件
│   ├── router/        # 路由配置
│   ├── stores/        # Pinia 状态管理
│   ├── styles/        # 全局样式
│   ├── utils/         # 工具函数
│   ├── views/         # 页面组件
│   ├── App.vue
│   └── main.js
├── docs/              # 文档
└── package.json
```

---

## 3. 环境配置（强制）

### 3.1 环境文件（强制）

| 文件 | 用途 |
|:-----|:-----|
| `.env.development` | 开发环境 |
| `.env.test` | 测试环境 |
| `.env.production` | 生产环境 |

### 3.2 环境变量（强制）

| 变量 | 说明 |
|:-----|:-----|
| `VITE_API_BASE_URL` | API 基础路径 |
| `VITE_API_TARGET` | 开发代理目标地址 |

### 3.3 启动命令（强制）

```bash
npm run dev        # 开发环境
npm run dev:test  # 测试环境
npm run dev:prod  # 生产环境
npm run build     # 构建
```

---

## 4. API 调用规范（强制）

### 4.1 axios 实例配置（强制）

```javascript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000
})
```

### 4.2 请求拦截器（强制）

```javascript
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### 4.3 响应拦截器（强制）

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

### 4.4 API 模块结构（强制）

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

### 4.5 API 路径规范（强制）

| 操作 | URL 格式 | 示例 |
|:-----|:---------|:-----|
| 列表 | /xxx/list | /country/list |
| 详情 | /xxx/detail | /country/detail |
| 新增 | /xxx/create | /country/create |
| 更新 | /xxx/update | /country/update |
| 删除 | /xxx/delete | /country/delete |
| 批量删除 | /xxx/batch-delete | /country/batch-delete |
| 导入 | /xxx/import | /country/import |
| 导出 | /xxx/export | /country/export |
| 模板下载 | /xxx/template/download | /country/template/download |

---

## 5. 错误处理规范（强制）

### 5.1 统一错误处理原则（强制）

**API 调用必须使用 try-catch**：

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

### 5.2 错误提示规范（强制）

| 场景 | 方式 |
|:-----|:-----|
| 数据加载失败 | Toast + 清空数据 |
| 操作失败 | Toast |
| 导出/下载失败 | Toast |
| 删除确认 | confirm 对话框 |

---

## 6. 登录机制（强制）

### 6.1 Token 存储（强制）

| 项目 | 实现 |
|:-----|:-----|
| 存储位置 | localStorage |
| 存储 key | `token`、`userInfo` |
| 传输方式 | Authorization Bearer Header |

---

## 7. 组件规范（强制）

### 7.1 页面组件结构（强制）

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

### 7.2 变量命名（强制）

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

---

## 8. 状态管理（强制）

### 8.1 Pinia Store（强制）

```javascript
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

---

## 9. 命名规范

### 9.1 文件命名（强制）

| 类型 | 规范 | 示例 |
|:-----|:-----|:-----|
| Vue 组件 | PascalCase | `UserManage.vue` |
| JS 文件 | camelCase | `toast.js` |

### 9.2 变量命名（强制）

| 类型 | 规范 | 示例 |
|:-----|:-----|:-----|
| 普通变量 | camelCase | `tableData`, `pageNo` |
| 组件 refs | camelCase | `showModal`, `isEdit` |
| 事件处理 | handle+Action | `handleSubmit`, `handleDelete` |

### 9.3 CSS 类命名（强制）

使用 kebab-case：`.card-header`, `.modal-overlay`

---

## 附录

### A. 相关文档

| 文档 | 位置 |
|:-----|:-----|
| API规范 | `通用规范/API规范.md` |
| 代码同步修改规范 | `通用规范/代码同步修改规范.md` |
