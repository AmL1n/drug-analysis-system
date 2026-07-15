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

export interface CascadeDetectPayload {
  categoryId: number
  referenceDrugId: number
  tx: number
  lambda1?: number | null
  lambda2?: number | null
  areas: {
    '245': number
    '250': number
    '255': number
    '260': number
  }
  thresholds: {
    rrtTolerance: number
    lambdaTolerance: number
    r1Tolerance: number
    r2Tolerance: number
    r3Tolerance: number
  }
  topN?: number
}

export interface CascadeReferenceDrug {
  id: number
  name: string
  retentionTime: number
}

export interface CascadeStep1Candidate {
  drugId: number
  drugName: string
  rrtDb: number
  delta: number
}

export interface CascadeStep2Candidate {
  drugId: number
  drugName: string
  rrtDb: number
  delta: number
}

export interface CascadeStep3Result {
  drugId: number
  drugName: string
  r1Db: number
  r2Db: number
  r3Db: number
  deltaR1: number
  deltaR2: number
  deltaR3: number
  score: number
}

export interface CascadeDetectResult {
  referenceDrug: CascadeReferenceDrug
  step1: {
    rrtSample: number
    tolerance: number
    candidateCount: number
    candidates: CascadeStep1Candidate[]
  }
  step2: {
    lambda1?: number | null
    lambda2?: number | null
    tolerance: number
    candidateCount: number
    candidates: CascadeStep2Candidate[]
  }
  step3: {
    r1: number
    r2: number
    r3: number
    results: CascadeStep3Result[]
  }
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

/**
 * 三步级联检测（RRT → UV λmax → 峰面积比）。
 */
export function detectCascade(data: CascadeDetectPayload): Promise<ApiResponse<CascadeDetectResult>> {
  return request.post('/detect/cascade', data)
}
