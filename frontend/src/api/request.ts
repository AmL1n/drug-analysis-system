import axios, { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

// 后端返回的统一响应格式
export interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

// 创建 Axios 实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：注入 Token
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误，并直接返回后端数据体
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // 二进制流响应（如下载文件）直接返回原始响应
    if (response.config.responseType === 'blob') {
      return response
    }
    const { data } = response
    if (data.code !== 0) {
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(new Error(data.msg || '请求失败'))
    }
    return data as any
  },
  (error: AxiosError<ApiResponse>) => {
    const status = error.response?.status
    const msg = error.response?.data?.msg || error.message || '网络错误'

    if (status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
    } else {
      ElMessage.error(msg)
    }

    return Promise.reject(error)
  }
)

export default request
