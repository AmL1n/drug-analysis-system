import request, { type ApiResponse } from './request'

/**
 * 获取系统配置值。
 */
export function getSystemConfig<T = any>(key: string): Promise<ApiResponse<{ key: string; value: T }>> {
  return request.get(`/system/configs/${key}`)
}

/**
 * 设置系统配置值。
 */
export function setSystemConfig<T = any>(key: string, value: T, description?: string): Promise<ApiResponse<any>> {
  return request.put(`/system/configs/${key}`, { value, description })
}
