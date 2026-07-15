import request, { type ApiResponse } from './request'

export interface HealthInfo {
  service: string
  version: string
  status: string
  timestamp: string
}

export interface DashboardStats {
  pending: number
  completed: number
  drugs: number
  reports: number
}

export interface OperationLogItem {
  id: number
  operator: string
  operatorNo?: string
  action: string
  module: string
  targetType?: string
  targetId?: string
  detail?: Record<string, any>
  ipAddress?: string
  userAgent?: string
  createdAt: string
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export function getHealth(): Promise<ApiResponse<HealthInfo>> {
  return request.get('/common/health')
}

export function getStats(): Promise<ApiResponse<DashboardStats>> {
  return request.get('/common/stats')
}

export function getLogs(params: {
  page?: number
  pageSize?: number
}): Promise<ApiResponse<PageResult<OperationLogItem>>> {
  return request.get('/common/logs', { params })
}
