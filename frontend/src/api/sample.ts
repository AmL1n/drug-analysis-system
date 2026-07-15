import request from './request'
import type { ApiResponse } from './request'

export interface SampleItem {
  id: number
  sampleNo: string
  sampleName: string
  status: string
  instrumentBrand?: string
  detectTime?: string
  createdAt: string
}

export interface SamplePeak {
  id: number
  peakIndex: number
  retentionTime: number
  area?: number
  height?: number
  areaRatio?: number
  relativeRetentionTime?: number
}

export interface SampleDetail extends SampleItem {
  peaks: SamplePeak[]
}

export interface CreateSampleForm {
  sampleName?: string
  fileId: number
  instrumentBrand?: string
  detectTime?: string
}

/**
 * 创建样本。
 */
export function createSample(data: CreateSampleForm): Promise<ApiResponse<SampleItem>> {
  return request.post('/samples', data)
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

/**
 * 获取样本列表。
 */
export function listSamples(params?: { status?: string; page?: number; pageSize?: number }): Promise<ApiResponse<PageResult<SampleItem>>> {
  return request.get('/samples', { params })
}

/**
 * 获取样本详情。
 */
export function getSampleDetail(sampleId: number): Promise<ApiResponse<SampleDetail>> {
  return request.get(`/samples/${sampleId}`)
}

export interface ChromatogramData {
  time: number[]
  intensity: number[]
  wavelength?: number
  peaks: SamplePeak[]
}

/**
 * 获取样本原始色谱图数据。
 */
export function getSampleChromatogram(sampleId: number): Promise<ApiResponse<ChromatogramData>> {
  return request.get(`/samples/${sampleId}/chromatogram`)
}
