import request, { type ApiResponse } from './request'

export interface CategoryItem {
  id: number
  name: string
  description?: string
  sortOrder?: number
}

export interface DrugItem {
  id: number
  categoryId?: number
  name: string
  cas?: string
  molecularFormula?: string
  description?: string
  status: number
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface PeakItem {
  id: number
  drugId: number
  drugName?: string
  peakIndex: number
  retentionTime?: number
  relativeRetentionTime?: number
  areaRatio?: number
  wavelength?: number
  isMainPeak?: boolean
}

export interface SpectrumItem {
  id: number
  drugId: number
  drugName?: string
  wavelength: number
  absorbance: number
  isMax?: boolean
}

export interface ImportLibraryResult {
  created: number
  updated: number
  failed: { name: string; reason: string }[]
}

export function getCategories(): Promise<ApiResponse<CategoryItem[]>> {
  return request.get('/library/categories')
}

export function getDrugs(params: {
  categoryId?: number
  keyword?: string
  page?: number
  pageSize?: number
}): Promise<ApiResponse<PageResult<DrugItem>>> {
  return request.get('/library/drugs', { params })
}

export function getDrugDetail(id: number): Promise<ApiResponse<DrugItem & { peaks: any[]; spectra: any[] }>> {
  return request.get(`/library/drugs/${id}`)
}

export function getPeaks(params: {
  categoryId?: number
  drugId?: number
  page?: number
  pageSize?: number
}): Promise<ApiResponse<PageResult<PeakItem>>> {
  return request.get('/library/peaks', { params })
}

export function getSpectra(params: {
  categoryId?: number
  drugId?: number
  page?: number
  pageSize?: number
}): Promise<ApiResponse<PageResult<SpectrumItem>>> {
  return request.get('/library/spectra', { params })
}

export function importLibraryDrugs(data: FormData): Promise<ApiResponse<ImportLibraryResult>> {
  return request.post('/library/import', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
