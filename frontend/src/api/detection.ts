import request from './request'
import type { ApiResponse } from './request'
import type { AxiosResponse } from 'axios'

export interface DetectForm {
  sampleId: number
  modelType?: string
  topN?: number
  confidenceThreshold?: number
  rrtTolerance?: number
  uvDistanceThreshold?: number
  areaRatioMethod?: 'relative_error' | 'cosine' | 'correlation'
}

export interface DetectBatchForm {
  sampleIds: number[]
  name?: string
}

export interface TaskProgress {
  id: number
  taskNo: string
  name: string
  status: string
  totalSamples: number
  completedSamples: number
  failedSamples: number
  progress: number
}

/**
 * 单样本检测。
 */
export function detectSample(data: DetectForm): Promise<ApiResponse<Record<string, unknown>>> {
  return request.post('/detect', data)
}

/**
 * 创建批量检测任务。
 */
export function detectBatch(data: DetectBatchForm): Promise<ApiResponse<TaskProgress>> {
  return request.post('/detect/batch', data)
}

/**
 * 获取任务进度。
 */
export function getTaskProgress(taskId: number): Promise<ApiResponse<TaskProgress>> {
  return request.get(`/detect/tasks/${taskId}`)
}

export interface DetectionResultItem {
  drugId: number
  drugName: string
  totalScore: number
  confidence: number
  isDetected: boolean
  matchedPeakCount: number
  totalPeakCount: number
  algorithmDetails: Record<string, unknown>
  referencePeaks: Array<{
    peakIndex: number
    retentionTime: number
    relativeRetentionTime?: number
    areaRatio?: number
    wavelength?: number
    height?: number
    width?: number
    isMainPeak?: boolean
  }>
  createdAt: string
}

/**
 * 获取样本检测结果明细。
 */
export function getDetectionResults(sampleId: number): Promise<ApiResponse<DetectionResultItem[]>> {
  return request.get(`/detect/results/${sampleId}`)
}

/**
 * 下载检测报告。
 */
export function downloadReport(sampleId: number, format: 'pdf' | 'excel' = 'pdf'): Promise<AxiosResponse<Blob>> {
  return request.get(`/reports/${sampleId}/download?format=${format}`, {
    responseType: 'blob',
  })
}
