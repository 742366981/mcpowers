---
title: Vue前端规范
type: tech-spec
applies_to: [Vue前端]
priority: required
version: 1.0
last_updated: 2026-07-08
stability: stable
last_breaking_change: v1.0
---

# Vue 3 前端项目规范

本文档定义 Vue 3 前端项目的通用规范，适用于所有 Vue 3 项目。

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
      const err = new Error(res.msg || '请求失败')
      err.response = response
      err.code = res.code
      return Promise.reject(err)
    }
    return res
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.href = '/login'
    }
    if (error.response?.data?.msg) {
      error.message = error.response.data.msg
    }
    return Promise.reject(error)
  }
)
```

### 4.4 Blob 下载（导出/模板）（强制）

```javascript
export function downloadBlob(url, data = {}, method = 'POST') {
  return axiosInstance.request({
    method,
    url,
    data,
    responseType: 'blob'
  }).then(response => {
    if (response.headers['content-type']?.includes('json')) {
      // 解析 JSON 错误信息
    }
    // 处理 Blob 下载
  })
}
```

### 4.5 API 模块结构（强制）

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

### 4.6 API 路径规范（强制）

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

### 5.3 401 重定向（强制）

触发条件：HTTP 401 或业务 code 401

---

## 6. 登录机制（强制）

### 6.1 Token 存储（强制）

| 项目 | 实现 |
|:-----|:-----|
| 存储位置 | localStorage |
| 存储 key | `token`、`userInfo` |
| 传输方式 | Authorization Bearer Header |

### 6.2 登录流程（强制）

```javascript
const res = await api.post('/auth/login', {
  username,
  password: md5(password)
})

if (res.code === 0) {
  localStorage.setItem('token', res.data.token)
  localStorage.setItem('userInfo', JSON.stringify(res.data.user))
}
```

### 6.3 退出登录（强制）

```javascript
function logout() {
  token.value = ''
  userInfo.value = null
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
}
```

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

### 7.2 表格结构（强制）

```vue
<table class="table">
  <thead><tr><th>...</th></tr></thead>
  <tbody>
    <tr v-if="loading">
      <td colspan="..." class="text-center">加载中...</td>
    </tr>
    <tr v-else-if="tableData.length === 0">
      <td colspan="..." class="text-center">暂无数据</td>
    </tr>
    <tr v-else v-for="item in tableData" :key="item.id">...</tr>
  </tbody>
</table>
```

### 7.3 变量命名（强制）

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

## 8. 样式规范（强制）

### 8.1 CSS 变量（强制）

```css
:root {
  --primary-color: #6366f1;
  --success-color: #10b981;
  --danger-color: #ef4444;
  --warning-color: #f59e0b;
  --text-primary: #0f172a;
  --text-muted: #64748b;
  --bg-gray: #f8fafc;
  --border-color: #e5e7eb;
}
```

### 8.2 通用样式类（强制）

| 类名 | 用途 |
|:-----|:-----|
| `.page` | 页面容器 |
| `.card` | 卡片容器 |
| `.card-header` | 卡片头部 |
| `.card-body` | 卡片内容 |
| `.table-container` | 表格容器 |
| `.table` | 表格 |
| `.toolbar` | 工具栏 |
| `.modal-overlay` | 弹窗遮罩 |
| `.modal` | 弹窗内容 |
| `.btn` | 按钮基础 |
| `.btn-primary` | 主按钮 |
| `.btn-secondary` | 次按钮 |
| `.btn-ghost` | 幽灵按钮 |
| `.btn-danger` | 危险按钮 |
| `.pagination` | 分页 |

### 8.3 布局类（强制）

```css
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
```

---

## 9. 状态管理（强制）

### 9.1 Pinia Store（强制）

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

---

## 10. 工具函数

### 10.1 Toast 消息提示

```javascript
import { showToast, confirm } from '../utils/toast'

showToast('操作成功', 'success')
showToast('操作失败', 'error')
showToast('警告信息', 'warning')

if (!await confirm('确认删除？')) return
```

### 10.2 Toast 类型

| 类型 | 颜色 |
|:-----|:-----|
| success | 绿色 |
| error | 红色 |
| warning | 黄色 |
| info | 蓝色 |

---

## 11. 命名规范

### 11.1 文件命名（强制）

| 类型 | 规范 | 示例 |
|:-----|:-----|:-----|
| Vue 组件 | PascalCase | `UserManage.vue` |
| JS 文件 | camelCase | `toast.js` |

### 11.2 变量命名（强制）

| 类型 | 规范 | 示例 |
|:-----|:-----|:-----|
| 普通变量 | camelCase | `tableData`, `pageNo` |
| 组件 refs | camelCase | `showModal`, `isEdit` |
| 事件处理 | handle+Action | `handleSubmit`, `handleDelete` |

### 11.3 CSS 类命名（强制）

使用 kebab-case：`.card-header`, `.modal-overlay`

---

## 12. 安全规范

### 12.1 Token 安全（强制）

| 项目 | 说明 |
|:-----|:-----|
| 存储 | localStorage（XSS 风险） |
| 传输 | Authorization Bearer Header（无需 CSRF） |

### 12.2 XSS 防护（强制）

- Toast message 使用 `textContent` 插入
- 禁止传入未转义的 HTML

---

## 13. Vite 配置（强制）

```javascript
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          headers: {
            'Access-Control-Expose-Headers': 'Content-Disposition'
          }
        }
      }
    }
  }
})
```

---

## 14. 变更同步（强制）

代码变更时需同步修改，详见 `代码同步修改规范.md`。

---

## 15. TypeScript 规范（强制）

### 15.1 类型定义文件

#### 15.1.1 全局类型声明

```typescript
// src/types/global.d.ts

// 通用响应结构
interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

// 分页响应结构
interface PaginatedResponse<T> {
  records: T[]
  total_count: number
  page_no: number
  page_size: number
}

// 通用 ID 类型
interface Identifiable {
  id: number
}

// 通用时间戳
interface Timestamps {
  created_at?: string
  updated_at?: string
}
```

#### 15.1.2 业务类型声明

```typescript
// src/types/index.ts

// 用户相关
interface User extends Identifiable, Timestamps {
  username: string
  nickname?: string
  email?: string
  phone?: string
  avatar?: string
  status: 0 | 1
}

// 登录请求
interface LoginRequest {
  username: string
  password: string
}

// 登录响应
interface LoginResponse {
  token: string
  user: User
}
```

### 15.2 基础类型规范

#### 15.2.1 接口 vs 类型别名

| 场景 | 规范 | 原因 |
|:-----|:-----|:-----|
| 对象结构 | 使用 `interface` | 可被 implements、支持声明合并 |
| 联合类型/工具类型 | 使用 `type` | 灵活性更强 |
| 复杂对象 | 使用 `interface` | 语义更清晰 |

```typescript
// ✅ 推荐：对象结构用 interface
interface User {
  id: number
  name: string
}

// ✅ 推荐：联合类型用 type
type Status = 'pending' | 'active' | 'deleted'

// ✅ 推荐：复杂类型用 type
type UserList = PaginatedResponse<User>
```

#### 15.2.2 泛型规范

```typescript
// ✅ 推荐：通用泛型函数
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key]
}

// ✅ 推荐：API 响应泛型
async function fetchData<T>(url: string): Promise<ApiResponse<T>> {
  const res = await api.get(url)
  return res as ApiResponse<T>
}
```

### 15.3 Vue 组件类型

#### 15.3.1 Props 定义（强制）

```typescript
// ✅ 推荐：使用 defineProps 泛型
interface Props {
  // 基础类型
  title: string
  count: number
  
  // 可选 + 默认值
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  
  // 对象类型
  config?: ComponentConfig
  
  // 数组类型
  items?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  disabled: false,
  items: () => []
})
```

#### 15.3.2 Emits 定义（强制）

```typescript
// ✅ 推荐：使用 defineEmits 泛型
interface Emits {
  (e: 'update', value: string): void
  (e: 'delete', id: number): void
  (e: 'click', event: MouseEvent): void
}

const emit = defineEmits<Emits>()

// 使用
emit('update', newValue)
emit('delete', itemId)
```

#### 15.3.3 Refs 类型

```typescript
// ✅ 推荐：ref 显式声明类型
const count = ref<number>(0)
const loading = ref<boolean>(false)
const userInfo = ref<User | null>(null)

// ✅ 推荐：reactive 显式声明类型
interface FormState {
  username: string
  password: string
}
const form = reactive<FormState>({
  username: '',
  password: ''
})

// ✅ 推荐：computed 显式声明类型
const fullName = computed<string>(() => `${firstName.value} ${lastName.value}`)
const isActive = computed<boolean>(() => status.value === 'active')
```

### 15.4 API 类型规范（强制）

#### 15.4.1 API 模块类型定义

```typescript
// src/api/types/user.d.ts

// 请求参数
interface UserListParams {
  page_no?: number
  page_size?: number
  keyword?: string
  status?: number
}

interface UserCreateParams {
  username: string
  nickname?: string
  password: string
  email?: string
}

interface UserUpdateParams extends Partial<UserCreateParams> {
  id: number
}

// 响应数据
type UserListResponse = PaginatedResponse<User>
type UserDetailResponse = ApiResponse<User>
type UserCreateResponse = ApiResponse<{ id: number }>
```

#### 15.4.2 API 方法类型化

```typescript
// src/api/user.ts

import { api } from './index'
import type {
  UserListParams,
  UserListResponse,
  UserDetailResponse,
  UserCreateParams,
  UserCreateResponse,
  UserUpdateParams
} from './types/user.d'

export const userApi = {
  list: (params: UserListParams) => 
    api.get<UserListResponse>('/user/list', { params }),
  
  detail: (id: number) => 
    api.get<UserDetailResponse>('/user/detail', { params: { id } }),
  
  create: (data: UserCreateParams) => 
    api.post<UserCreateResponse>('/user/create', data),
  
  update: (data: UserUpdateParams) => 
    api.post<UserCreateResponse>('/user/update', data),
  
  delete: (id: number) => 
    api.post<ApiResponse<null>>('/user/delete', { id })
}
```

### 15.5 工具函数类型规范

```typescript
// ✅ 推荐：工具函数泛型化
function pick<T extends object, K extends keyof T>(
  obj: T, 
  keys: K[]
): Pick<T, K> {
  const result = {} as Pick<T, K>
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key]
    }
  })
  return result
}

// 使用
const user = { id: 1, name: '张三', age: 18, email: 'zhangsan@example.com' }
const picked = pick(user, ['id', 'name']) // { id: 1, name: '张三' }
```

### 15.6 store 类型规范

```typescript
// src/stores/user.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<User | null>(
    JSON.parse(localStorage.getItem('userInfo') || 'null')
  )
  
  // Getters
  const isLoggedIn = computed<boolean>(() => !!token.value)
  const userId = computed<number>(() => userInfo.value?.id ?? 0)
  
  // Actions
  function setUser(user: User, newToken: string) {
    token.value = newToken
    userInfo.value = user
    localStorage.setItem('token', newToken)
    localStorage.setItem('userInfo', JSON.stringify(user))
  }
  
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }
  
  return {
    token,
    userInfo,
    isLoggedIn,
    userId,
    setUser,
    logout
  }
})
```

### 15.7 TypeScript 禁止模式

```typescript
// ❌ 禁止：any 类型
function processData(data: any) { ... }

// ❌ 禁止：unchecked index access
const name = users['name']  // 可能不存在

// ❌ 禁止：隐式 any
function fetchData(url) {  // 参数缺少类型
  return api.get(url)
}

// ❌ 禁止：类型断言过多
const user = response.data as any as User as any

// ✅ 推荐：unknown 代替 any
async function parseResponse(response: unknown) {
  if (isUserResponse(response)) {
    return response.data
  }
  throw new Error('Invalid response')
}
```

---

## 16. 组件设计规范（强制）

### 16.1 组件分类

| 类型 | 存放位置 | 说明 |
|:-----|:---------|:-----|
| 页面组件 | `src/views/` | 对应路由，组合公共组件 |
| 公共组件 | `src/components/` | 可复用的业务组件 |
| 基础组件 | `src/components/base/` | 原子级别组件（Button/Input等） |

```typescript
// 组件目录结构示例
src/
├── components/
│   ├── base/              # 基础组件（不依赖业务）
│   │   ├── BaseButton.vue
│   │   ├── BaseInput.vue
│   │   └── BaseModal.vue
│   │
│   ├── business/           # 业务公共组件
│   │   ├── UserSelect.vue
│   │   ├── StatusTag.vue
│   │   └── ConfirmDialog.vue
│   │
│   └── layout/            # 布局组件
│       ├── AppHeader.vue
│       └── AppSidebar.vue
```

### 16.2 Props 规范（强制）

#### 16.2.1 Props 类型定义

```typescript
// ✅ 推荐：基础类型直接标注
defineProps<{
  title: string
  count: number
  disabled: boolean
}>()

// ✅ 推荐：可选属性用 ? 标记
defineProps<{
  title?: string           // 可选
  size?: 'small' | 'large' // 可选 + 枚举
}>()

// ✅ 推荐：带默认值的可选
withDefaults(defineProps<{
  size?: 'small' | 'medium' | 'large'
  color?: string
}>(), {
  size: 'medium',
  color: '#000'
})
```

#### 16.2.2 Props 校验

```typescript
// ✅ 推荐：使用 validator 进行复杂校验
defineProps<{
  status: 'pending' | 'active' | 'deleted'
  percent: number
}>()

// ✅ 推荐：添加详细校验（在 JSDoc 中说明）
/**
 * 组件说明
 * @param title - 标题，必填
 * @param size - 大小，可选，默认 medium
 * @param items - 列表数据，可选，默认空数组
 */
defineProps<{
  title: string
  size?: 'small' | 'medium' | 'large'
  items?: Array<{ id: number; name: string }>
}>()
```

#### 16.2.3 Props 命名规范

| 规范 | 示例 |
|:-----|:-----|
| 使用 camelCase | `userName`, `isLoading` |
| 避免缩写 | `disabled` 而非 `dis` |
| 布尔值用 is/has/can 前缀 | `isOpen`, `hasError`, `canEdit` |

### 16.3 Emits 规范（强制）

#### 16.3.1 Emits 类型定义

```typescript
// ✅ 推荐：使用 defineEmits 泛型
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: number): void
  (e: 'delete', id: number): void
}>()

// ✅ 推荐：v-model 双向绑定
// 组件内
const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

// 使用
emit('update:modelValue', newValue)
```

#### 16.3.2 Emits 命名规范

| 规范 | 示例 | 说明 |
|:-----|:-----|:-----|
| 事件名用 kebab-case | `'update:modelValue'` | HTML 事件规范 |
| 动词开头 | `'delete'`, `'change'` | 表达动作 |
| 避免时态混用 | `'change'` 而非 `'changed'` | 保持一致 |

### 16.4 Slots 规范

#### 16.4.1 插槽类型

```vue
<!-- 默认插槽 -->
<template #default="{ item, index }">
  <div>{{ item.name }}</div>
</template>

<!-- 具名插槽 -->
<template #header>
  <h3>标题</h3>
</template>

<!-- 作用域插槽 -->
<template #item="{ row }">
  <span :class="row.status">{{ row.label }}</span>
</template>
```

#### 16.4.2 插槽命名规范

| 插槽名 | 用途 | 示例 |
|:-------|:-----|:-----|
| `default` | 默认内容 | 表单内容、列表项 |
| `header` | 头部区域 | 表格头、弹窗标题 |
| `footer` | 底部区域 | 按钮、操作区 |
| `toolbar` | 工具栏 | 搜索、操作按钮 |
| `empty` | 空状态 | 无数据提示 |
| `loading` | 加载状态 | loading 骨架屏 |

### 16.5 组件文档规范（强制）

#### 16.5.1 JSDoc 注释

```typescript
/**
 * 用户选择器组件
 * @description 用于在表单中选择用户，支持搜索和单选/多选
 * @version 1.0.0
 * @author 张三
 * @see [组件设计规范]{@link ../docs/组件规范.md}
 */
```

#### 16.5.2 Props 注释

```typescript
/**
 * @param modelValue - v-model 绑定值
 * @param options - 选项列表
 * @param multiple - 是否多选，默认 false
 * @param searchable - 是否可搜索，默认 true
 * @param placeholder - 占位文本，默认"请选择"
 */
defineProps<{
  modelValue: string | string[]
  options: Array<{ label: string; value: string }>
  multiple?: boolean
  searchable?: boolean
  placeholder?: string
}>()
```

### 16.6 组件拆分原则

| 场景 | 拆分建议 |
|:-----|:---------|
| 组件超过 300 行 | 考虑拆分 |
| 存在独立可复用单元 | 拆分为子组件 |
| Props 超过 10 个 | 考虑拆分或使用配置对象 |
| 存在多个 v-if 分支 | 使用插槽或拆分子组件 |

```vue
<!-- ❌ 不推荐：过大的组件 -->
<template>
  <div>
    <UserForm />      <!-- 表单区域 -->
    <UserList />      <!-- 列表区域 -->
    <UserDetail />    <!-- 详情弹窗 -->
    <UserImport />    <!-- 导入功能 -->
  </div>
</template>

<!-- ✅ 推荐：按功能拆分 -->
src/
├── views/UserManage/
│   ├── index.vue          # 页面入口，组合子组件
│   ├── components/
│   │   ├── UserSearch.vue    # 搜索栏
│   │   ├── UserTable.vue     # 表格
│   │   ├── UserForm.vue      # 表单弹窗
│   │   └── UserImport.vue    # 导入功能
```

### 16.7 组件通信规范

| 场景 | 规范 | 说明 |
|:-----|:-----|:-----|
| 父子通信 | Props + Emits | 推荐的父子通信方式 |
| 爷孙通信 | Provide/Inject | 中间组件无需透传 |
| 跨级通信 | Pinia Store | 全局状态 |
| 兄弟通信 | Pinia Store | 通过 store 中转 |

```typescript
// ✅ 推荐：Provide/Inject（爷孙通信）
// 父组件
const theme = inject<Ref<string>>('theme', ref('light'))

// 孙组件
const theme = inject<Ref<string>>('theme')
```

---

## 附录

### A. 相关文档

| 文档 | 位置 |
|:-----|:-----|
| API通用规范 | `docs/技术规范/API规范.md` |
| 代码同步修改规范 | `docs/技术规范/代码同步修改规范.md` |
| TypeScript 官方文档 | https://www.typescriptlang.org/docs/ |
| Vue 3 + TS 指南 | https://vuejs.org/guide/typescript/ |

### B. 标签对照表

> ⚠️ **通用规范引用**：详见 `API规范.md` 第9章
