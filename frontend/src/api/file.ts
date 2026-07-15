import request from './request'
import type { ApiResponse } from './request'

export interface UploadResult {
  id: number
  originalName: string
  fileSize: number
  fileType?: string
  createdAt: string
}

/**
 * 上传仪器数据文件。
 */
export function uploadFile(file: File): Promise<ApiResponse<UploadResult>> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
