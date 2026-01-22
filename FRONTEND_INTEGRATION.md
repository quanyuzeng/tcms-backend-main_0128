# TCMS 前端对接指南

## 概述

本文档描述了如何将 TCMS 后端 API 与前端 Vue 3 应用进行对接。

## 技术栈

- **前端**: Vue 3 + Element Plus + Axios
- **后端**: Django REST Framework + JWT
- **通信**: RESTful API + JSON

## 环境配置

### 前端环境变量

在前端项目根目录创建 `.env` 文件：

```env
# 开发环境
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=TCMS

# 生产环境
# VITE_API_BASE_URL=https://api.your-domain.com/api
```

### 后端 CORS 配置

确保后端 `config/settings/development.py` 或 `config/settings/production.py` 中配置了正确的前端域名：

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # 开发环境
    "https://your-frontend-domain.com",  # 生产环境
]
```

## API 对接说明

### 1. 认证模块

#### 登录

**前端调用示例：**
```javascript
import { userAPI } from '@/api'

const login = async () => {
  try {
    const response = await userAPI.login({
      username: 'username',
      password: 'password',
      remember: false
    })
    
    // 保存 token
    const { access, refresh, user } = response.data
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('user_info', JSON.stringify(user))
    
    // 设置 Axios 默认请求头
    axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
    
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  }
}
```

**后端响应：**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "username": "testuser",
      "real_name": "测试用户",
      "email": "test@example.com",
      "department": "技术部",
      "position": "软件工程师",
      "role": "employee",
      "permissions": ["profile:*", "course:read", "exam:take"]
    }
  }
}
```

#### Token 刷新

**前端自动刷新：**
```javascript
// src/utils/request.js
import axios from 'axios'
import { userAPI } from '@/api'
import { ElMessage } from 'element-plus'

// 创建 Axios 实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code === 200) {
      return res
    } else {
      ElMessage.error(res.message || 'Error')
      return Promise.reject(new Error(res.message || 'Error'))
    }
  },
  async error => {
    const { response } = error
    
    if (response.status === 401) {
      // Token 过期，尝试刷新
      try {
        const refresh_token = localStorage.getItem('refresh_token')
        const res = await userAPI.refreshToken(refresh_token)
        
        const { access } = res.data
        localStorage.setItem('access_token', access)
        service.defaults.headers.common['Authorization'] = `Bearer ${access}`
        
        // 重试原请求
        return service(error.config)
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    ElMessage.error(response.data.message || '请求失败')
    return Promise.reject(error)
  }
)

export default service
```

#### 登出

**前端调用：**
```javascript
const logout = async () => {
  try {
    const refresh_token = localStorage.getItem('refresh_token')
    await userAPI.logout(refresh_token)
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    // 清除本地存储
    localStorage.clear()
    delete axios.defaults.headers.common['Authorization']
    router.push('/login')
  }
}
```

### 2. 用户管理模块

#### 获取用户列表

**前端调用：**
```javascript
const loadUsers = async (params) => {
  try {
    const response = await userAPI.getUsers({
      page: params.page || 1,
      size: params.size || 10,
      search: params.search || '',
      department: params.department || '',
      role: params.role || '',
      status: params.status || ''
    })
    
    return {
      list: response.data.results,
      total: response.data.count
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
    return { list: [], total: 0 }
  }
}
```

#### 创建用户

**前端调用：**
```javascript
const createUser = async (userData) => {
  try {
    const response = await userAPI.createUser(userData)
    ElMessage.success('用户创建成功')
    return response.data
  } catch (error) {
    ElMessage.error('用户创建失败')
    throw error
  }
}
```

### 3. 培训管理模块

#### 获取课程列表

**前端调用：**
```javascript
const loadCourses = async (params) => {
  try {
    const response = await courseAPI.getCourses({
      page: params.page || 1,
      size: params.size || 10,
      search: params.search || '',
      category: params.category || '',
      status: params.status || ''
    })
    
    return {
      list: response.data.results,
      total: response.data.count
    }
  } catch (error) {
    ElMessage.error('获取课程列表失败')
    return { list: [], total: 0 }
  }
}
```

#### 报名课程

**前端调用：**
```javascript
const enrollCourse = async (courseId) => {
  try {
    const response = await courseAPI.enrollCourse(courseId)
    ElMessage.success('报名成功')
    return response.data
  } catch (error) {
    ElMessage.error('报名失败')
    throw error
  }
}
```

### 4. 考试管理模块

#### 开始考试

**前端调用：**
```javascript
const startExam = async (examId) => {
  try {
    const response = await examAPI.startExam(examId)
    
    // 保存考试信息
    const examInfo = response.data
    sessionStorage.setItem('current_exam', JSON.stringify(examInfo))
    
    // 跳转到考试页面
    router.push(`/exam/${examId}`)
    
    return examInfo
  } catch (error) {
    ElMessage.error(error.message || '无法开始考试')
    throw error
  }
}
```

#### 提交考试

**前端调用：**
```javascript
const submitExam = async (examId, answers, duration) => {
  try {
    const response = await examAPI.submitExam(examId, {
      answers: answers,
      duration: duration
    })
    
    ElMessage.success('考试提交成功')
    sessionStorage.removeItem('current_exam')
    
    return response.data
  } catch (error) {
    ElMessage.error('提交失败')
    throw error
  }
}
```

### 5. 能力管理模块

#### 获取能力矩阵

**前端调用：**
```javascript
const loadCompetencyMatrix = async (params) => {
  try {
    const response = await competencyAPI.getCompetencyMatrix({
      department_id: params.departmentId || '',
      position_id: params.positionId || ''
    })
    
    return response.data
  } catch (error) {
    ElMessage.error('获取能力矩阵失败')
    return { users: [], competencies: [], matrix: [] }
  }
}
```

### 6. 报表管理模块

#### 导出报表

**前端调用：**
```javascript
const exportReport = async (params) => {
  try {
    const response = await reportAPI.exportReport(params)
    
    // 下载文件
    const downloadUrl = response.data.download_url
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${params.report_type}.${params.format}`
    link.click()
    
    ElMessage.success('导出任务已提交')
  } catch (error) {
    ElMessage.error('导出失败')
    throw error
  }
}
```

## 错误处理

### 统一错误处理

```javascript
// src/utils/error-handler.js
export const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response
    
    switch (status) {
      case 400:
        ElMessage.error(data.message || '请求参数错误')
        break
      case 401:
        ElMessage.error('未授权，请重新登录')
        router.push('/login')
        break
      case 403:
        ElMessage.error('权限不足')
        break
      case 404:
        ElMessage.error('资源不存在')
        break
      case 500:
        ElMessage.error('服务器错误，请稍后重试')
        break
      default:
        ElMessage.error(data.message || '请求失败')
    }
  } else if (error.request) {
    ElMessage.error('网络错误，请检查网络连接')
  } else {
    ElMessage.error('发生未知错误')
  }
}
```

## 权限控制

### 前端权限控制

```javascript
// src/utils/permission.js
import { useAuthStore } from '@/stores/auth'

export const hasPermission = (permission) => {
  const authStore = useAuthStore()
  const permissions = authStore.user?.permissions || []
  
  // 超级权限
  if (permissions.includes('*')) {
    return true
  }
  
  return permissions.includes(permission)
}

export const hasAnyPermission = (permissions) => {
  return permissions.some(permission => hasPermission(permission))
}

// 自定义指令
app.directive('permission', {
  mounted(el, binding) {
    const { value } = binding
    if (!hasPermission(value)) {
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
})
```

### 路由权限控制

```javascript
// src/permission.js
import router from './router'
import { useAuthStore } from '@/stores/auth'

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要登录
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // 检查权限
  if (to.meta.permissions) {
    const hasPermission = to.meta.permissions.some(permission => 
      authStore.hasPermission(permission)
    )
    
    if (!hasPermission) {
      next('/403')
      return
    }
  }
  
  next()
})
```

## 国际化支持

### 后端多语言

后端返回的错误信息支持多语言：

```javascript
// 在请求头中设置语言
axios.defaults.headers.common['Accept-Language'] = 'zh-CN'
// 或
axios.defaults.headers.common['Accept-Language'] = 'en-US'
```

### 前端多语言

```javascript
// src/i18n/index.js
import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'

const i18n = createI18n({
  locale: localStorage.getItem('language') || 'zh',
  messages: {
    zh,
    en
  }
})

export default i18n
```

## 开发调试

### 1. 使用浏览器开发者工具

- 查看 Network 标签中的 API 请求和响应
- 检查 Console 中的错误信息
- 使用 Application 标签查看 LocalStorage 和 SessionStorage

### 2. 使用 Vue DevTools

安装 Vue DevTools 浏览器扩展，可以：
- 查看组件树
- 检查组件状态
- 调试 Vuex/Pinia 状态管理

### 3. 使用 Postman 测试 API

导入 API 文档到 Postman，可以：
- 测试各个 API 接口
- 保存测试用例
- 自动化测试

## 性能优化

### 1. 请求缓存

```javascript
// 使用 Axios 缓存
import { setupCache } from 'axios-cache-adapter'

const cache = setupCache({
  maxAge: 15 * 60 * 1000 // 15分钟
})

const api = axios.create({
  adapter: cache.adapter
})
```

### 2. 数据分页

```javascript
// 使用虚拟滚动或分页加载大量数据
const loadMoreData = async () => {
  const response = await api.get('/users/', {
    params: {
      page: currentPage.value + 1,
      size: pageSize
    }
  })
  
  userList.value = [...userList.value, ...response.data.results]
  currentPage.value += 1
}
```

### 3. 图片懒加载

```javascript
// 使用 Element Plus 的懒加载
<el-image
  v-for="img in imageList"
  :key="img.id"
  :src="img.url"
  lazy
/>
```

## 常见问题

### 1. 跨域问题

**问题**：浏览器报 CORS 错误

**解决**：
1. 检查后端 CORS 配置
2. 确保前端域名在后端白名单中
3. 开发环境可以使用代理

### 2. Token 过期

**问题**：接口返回 401

**解决**：
1. 实现自动刷新 Token 机制
2. 检查 Token 有效期设置
3. 确保 Refresh Token 有效

### 3. 权限问题

**问题**：接口返回 403

**解决**：
1. 检查用户角色和权限
2. 确保请求头中包含正确的 Token
3. 检查后端权限配置

### 4. 数据格式问题

**问题**：数据无法正确显示

**解决**：
1. 检查前后端数据格式是否一致
2. 使用浏览器开发者工具查看响应数据
3. 检查序列化器配置

## 测试

### 1. 单元测试

```javascript
// 使用 Vitest 测试 API
import { describe, it, expect, vi } from 'vitest'
import { userAPI } from '@/api'

describe('User API', () => {
  it('should login successfully', async () => {
    const response = await userAPI.login({
      username: 'testuser',
      password: 'testpass'
    })
    
    expect(response.code).toBe(200)
    expect(response.data).toHaveProperty('access')
    expect(response.data).toHaveProperty('refresh')
  })
})
```

### 2. 集成测试

```javascript
// 使用 Cypress 进行端到端测试
describe('User Management', () => {
  it('should create a new user', () => {
    cy.login('admin', 'admin123')
    cy.visit('/users')
    
    cy.contains('新建用户').click()
    cy.get('#username').type('newuser')
    cy.get('#real_name').type('新用户')
    cy.get('#email').type('new@example.com')
    
    cy.contains('保存').click()
    
    cy.contains('用户创建成功').should('be.visible')
  })
})
```

## 部署

### 1. 开发环境

```bash
# 启动前端开发服务器
npm run dev

# 启动后端开发服务器
python manage.py runserver
```

### 2. 生产环境

```bash
# 构建前端
npm run build

# 部署后端
python manage.py collectstatic
```

## 联系支持

如有对接问题，请联系开发团队。

---

**对接完成！** 现在前端应用应该能够与后端 API 正常通信了。