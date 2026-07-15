import request from './request'
import type { ApiResponse } from './request'

export interface LoginForm {
  username: string
  password: string
}

export interface UserInfo {
  id: number
  username: string
  realName: string
  email?: string
  operatorNo?: string
  roles: string[]
}

export interface LoginResult {
  token: string
  user: UserInfo
}

/**
 * 用户登录。
 */
export function login(data: LoginForm): Promise<ApiResponse<LoginResult>> {
  return request.post('/auth/login', data)
}

/**
 * 获取当前登录用户信息。
 */
export function getCurrentUser(): Promise<ApiResponse<UserInfo>> {
  return request.get('/auth/me')
}
