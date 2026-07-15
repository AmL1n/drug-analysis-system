<template>
  <div class="page-container">
    <h2 class="page-title">对照品库</h2>

    <GlassCard class="library-card" :tilt="false">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="药物列表" name="drugs">
          <div class="filter-bar">
            <el-select
              v-model="filter.categoryId"
              placeholder="全部类别"
              clearable
              style="width: 180px"
              @change="handleCategoryChange"
            >
              <el-option
                v-for="cat in categories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
            <el-input
              v-model="filter.keyword"
              placeholder="搜索药物名称 / CAS"
              clearable
              style="width: 260px"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button :icon="Search" @click="handleSearch" />
              </template>
            </el-input>
            <GlassButton danger :disabled="selectedDrugs.length === 0" @click="handleBatchDelete">
              批量删除
            </GlassButton>
          </div>

          <div class="import-section">
            <el-upload
              drag
              action="#"
              :auto-upload="false"
              :limit="1"
              :on-change="handleLibraryImportFileChange"
              :on-remove="handleLibraryImportFileRemove"
              accept=".json"
              class="import-uploader"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">拖拽 JSON 文件到此处，或点击上传</div>
              <div class="upload-tip">仅支持 .json，外部药物标准库格式</div>
            </el-upload>

            <div class="import-form">
              <el-select
                v-model="libraryImportCategoryId"
                placeholder="选择类别（可选，默认导入药物）"
                clearable
                style="width: 260px"
              >
                <el-option
                  v-for="cat in categories"
                  :key="cat.id"
                  :label="cat.name"
                  :value="cat.id"
                />
              </el-select>
              <GlassButton primary :loading="libraryImporting" @click="handleImportLibraryDrugs">
                导入药物列表
              </GlassButton>
            </div>

            <div v-if="libraryImportMessage" class="import-result">
              <el-alert
                :title="libraryImportMessage"
                :type="libraryImportSuccess ? 'success' : 'error'"
                :closable="false"
                show-icon
              />
              <el-table
                v-if="libraryImportFailed.length > 0"
                :data="libraryImportFailed"
                border
                stripe
                size="small"
                style="width: 100%; margin-top: 12px"
              >
                <el-table-column prop="name" label="药物名称" min-width="160" />
                <el-table-column prop="reason" label="失败原因" min-width="260" />
              </el-table>
            </div>
          </div>

          <el-table
            v-loading="loading"
            :data="drugs"
            border
            stripe
            style="width: 100%"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="药物名称" min-width="160" />
            <el-table-column label="类别" min-width="120">
              <template #default="{ row }">
                {{ row.categoryId ? categoryMap[row.categoryId] : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="cas" label="CAS号" min-width="140" />
            <el-table-column prop="molecularFormula" label="分子式" min-width="120" />
            <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <div class="row-actions">
                  <GlassButton primary @click="showDetail(row)">详情</GlassButton>
                  <GlassButton danger @click="handleDelete(row)">删除</GlassButton>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            class="pagination"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </el-tab-pane>

        <el-tab-pane label="峰库" name="peaks">
          <div class="filter-bar">
            <el-select
              v-model="peakFilter.categoryId"
              placeholder="全部类别"
              clearable
              style="width: 180px"
              @change="handlePeakFilterChange"
            >
              <el-option
                v-for="cat in categories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
            <el-select
              v-model="peakFilter.drugId"
              placeholder="全部药物"
              clearable
              filterable
              style="width: 220px"
              @change="handlePeakFilterChange"
            >
              <el-option
                v-for="drug in drugOptions"
                :key="drug.id"
                :label="drug.name"
                :value="drug.id"
              />
            </el-select>
            <GlassButton :icon="Search" @click="handlePeakSearch">
              <el-icon><Search /></el-icon>
              查询
            </GlassButton>
          </div>

          <el-table
            v-loading="peakLoading"
            :data="peaks"
            border
            stripe
            style="width: 100%"
          >
            <el-table-column prop="drugName" label="药物名称" min-width="160" />
            <el-table-column prop="peakIndex" label="峰序号" width="90" />
            <el-table-column prop="retentionTime" label="保留时间" min-width="120" />
            <el-table-column prop="relativeRetentionTime" label="相对保留时间" min-width="140" />
            <el-table-column prop="areaRatio" label="面积比" min-width="120" />
            <el-table-column prop="wavelength" label="波长" min-width="100" />
            <el-table-column label="是否主峰" width="100">
              <template #default="{ row }">
                <el-tag :type="row.isMainPeak ? 'success' : 'info'" size="small">
                  {{ row.isMainPeak ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="peakPagination.page"
            v-model:page-size="peakPagination.pageSize"
            :total="peakPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            class="pagination"
            @size-change="handlePeakSizeChange"
            @current-change="handlePeakPageChange"
          />
        </el-tab-pane>

        <el-tab-pane label="光谱库" name="spectra">
          <div class="filter-bar">
            <el-select
              v-model="spectrumFilter.categoryId"
              placeholder="全部类别"
              clearable
              style="width: 180px"
              @change="handleSpectrumFilterChange"
            >
              <el-option
                v-for="cat in categories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
            <el-select
              v-model="spectrumFilter.drugId"
              placeholder="全部药物"
              clearable
              filterable
              style="width: 220px"
              @change="handleSpectrumFilterChange"
            >
              <el-option
                v-for="drug in drugOptions"
                :key="drug.id"
                :label="drug.name"
                :value="drug.id"
              />
            </el-select>
            <GlassButton :icon="Search" @click="handleSpectrumSearch">
              <el-icon><Search /></el-icon>
              查询
            </GlassButton>
          </div>

          <el-table
            v-loading="spectrumLoading"
            :data="spectra"
            border
            stripe
            style="width: 100%"
          >
            <el-table-column prop="drugName" label="药物名称" min-width="160" />
            <el-table-column prop="wavelength" label="波长" min-width="120" />
            <el-table-column prop="absorbance" label="吸光度" min-width="120" />
            <el-table-column label="是否最大吸收" width="120">
              <template #default="{ row }">
                <el-tag :type="row.isMax ? 'success' : 'info'" size="small">
                  {{ row.isMax ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="spectrumPagination.page"
            v-model:page-size="spectrumPagination.pageSize"
            :total="spectrumPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            class="pagination"
            @size-change="handleSpectrumSizeChange"
            @current-change="handleSpectrumPageChange"
          />
        </el-tab-pane>

      </el-tabs>
    </GlassCard>

    <el-dialog v-model="detailVisible" title="药物详情" width="680px">
      <el-descriptions v-if="selectedDrug" :column="2" border>
        <el-descriptions-item label="名称">{{ selectedDrug.name }}</el-descriptions-item>
        <el-descriptions-item label="CAS">{{ selectedDrug.cas || '-' }}</el-descriptions-item>
        <el-descriptions-item label="分子式">{{ selectedDrug.molecularFormula || '-' }}</el-descriptions-item>
        <el-descriptions-item label="类别">{{ selectedDrug.categoryId ? categoryMap[selectedDrug.categoryId] : '-' }}</el-descriptions-item>
        <el-descriptions-item label="说明" :span="2">{{ selectedDrug.description || '-' }}</el-descriptions-item>
      </el-descriptions>
      <h4 class="detail-section">参考峰</h4>
      <el-empty v-if="!selectedDrug?.peaks?.length" description="暂无参考峰数据" />
      <el-table v-else :data="selectedDrug.peaks" border size="small" style="width: 100%">
        <el-table-column prop="peakIndex" label="峰序号" width="90" />
        <el-table-column prop="retentionTime" label="保留时间" />
        <el-table-column prop="relativeRetentionTime" label="相对保留时间" />
        <el-table-column prop="areaRatio" label="面积比" />
        <el-table-column prop="wavelength" label="波长" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, UploadFilled } from '@element-plus/icons-vue'
import {
  batchDeleteDrugs,
  deleteDrug,
  getCategories,
  getDrugDetail,
  getDrugs,
  getPeaks,
  getSpectra,
  importLibraryDrugs,
  type CategoryItem,
  type DrugItem,
  type PeakItem,
  type SpectrumItem,
} from '@/api/library'

import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'

const activeTab = ref('drugs')
const loading = ref(false)
const categories = ref<CategoryItem[]>([])
const categoryMap = ref<Record<number, string>>({})
const drugs = ref<DrugItem[]>([])
const filter = reactive({
  categoryId: undefined as number | undefined,
  keyword: '',
})
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})
const detailVisible = ref(false)
const selectedDrug = ref<DrugItem & { peaks?: any[]; spectra?: any[] } | null>(null)

const drugOptions = ref<DrugItem[]>([])

const peaks = ref<PeakItem[]>([])
const peakLoading = ref(false)
const peakFilter = reactive({
  categoryId: undefined as number | undefined,
  drugId: undefined as number | undefined,
})
const peakPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const spectra = ref<SpectrumItem[]>([])
const spectrumLoading = ref(false)
const spectrumFilter = reactive({
  categoryId: undefined as number | undefined,
  drugId: undefined as number | undefined,
})
const spectrumPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const libraryImportCategoryId = ref<number | undefined>(undefined)
const libraryImportFile = ref<File | null>(null)
const libraryImporting = ref(false)
const libraryImportSuccess = ref(false)
const libraryImportMessage = ref('')
const libraryImportFailed = ref<{ name: string; reason: string }[]>([])
const selectedDrugs = ref<DrugItem[]>([])

async function loadCategories() {
  try {
    const res = await getCategories()
    categories.value = res.data
    categoryMap.value = Object.fromEntries(res.data.map((c) => [c.id, c.name]))
  } catch (error) {
    console.error('加载类别失败:', error)
  }
}

async function loadDrugs() {
  loading.value = true
  try {
    const res = await getDrugs({
      categoryId: filter.categoryId,
      keyword: filter.keyword || undefined,
      page: pagination.page,
      pageSize: pagination.pageSize,
    })
    drugs.value = res.data.items
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载药物列表失败')
  } finally {
    loading.value = false
  }
}

function handleCategoryChange() {
  pagination.page = 1
  loadDrugs()
}

function handleSearch() {
  pagination.page = 1
  loadDrugs()
}

function handlePageChange(page: number) {
  pagination.page = page
  loadDrugs()
}

function handleSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  loadDrugs()
}

async function showDetail(row: DrugItem) {
  try {
    const res = await getDrugDetail(row.id)
    selectedDrug.value = res.data
    detailVisible.value = true
  } catch (error) {
    ElMessage.error('加载药物详情失败')
  }
}

async function handleDelete(row: DrugItem) {
  try {
    await ElMessageBox.confirm(`确定删除药物「${row.name}」吗？`, '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteDrug(row.id)
    ElMessage.success('删除成功')
    loadDrugs()
    loadDrugOptions()
  } catch (error: any) {
    if (error !== 'cancel' && error?.message !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleBatchDelete() {
  if (selectedDrugs.value.length === 0) {
    ElMessage.warning('请先选择要删除的药物')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedDrugs.value.length} 条药物吗？`,
      '提示',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    const ids = selectedDrugs.value.map((d) => d.id)
    await batchDeleteDrugs(ids)
    ElMessage.success('批量删除成功')
    selectedDrugs.value = []
    loadDrugs()
    loadDrugOptions()
  } catch (error: any) {
    if (error !== 'cancel' && error?.message !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

function handleSelectionChange(rows: DrugItem[]) {
  selectedDrugs.value = rows
}

async function loadDrugOptions() {
  try {
    const res = await getDrugs({ page: 1, pageSize: 1000 })
    drugOptions.value = res.data.items
  } catch (error) {
    console.error('加载药物选项失败:', error)
  }
}

async function loadPeaks() {
  peakLoading.value = true
  try {
    const res = await getPeaks({
      categoryId: peakFilter.categoryId,
      drugId: peakFilter.drugId,
      page: peakPagination.page,
      pageSize: peakPagination.pageSize,
    })
    peaks.value = res.data.items
    peakPagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载峰库数据失败')
  } finally {
    peakLoading.value = false
  }
}

async function loadSpectra() {
  spectrumLoading.value = true
  try {
    const res = await getSpectra({
      categoryId: spectrumFilter.categoryId,
      drugId: spectrumFilter.drugId,
      page: spectrumPagination.page,
      pageSize: spectrumPagination.pageSize,
    })
    spectra.value = res.data.items
    spectrumPagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载光谱库数据失败')
  } finally {
    spectrumLoading.value = false
  }
}

function handlePeakFilterChange() {
  peakPagination.page = 1
  loadPeaks()
}

function handlePeakSearch() {
  peakPagination.page = 1
  loadPeaks()
}

function handlePeakPageChange(page: number) {
  peakPagination.page = page
  loadPeaks()
}

function handlePeakSizeChange(size: number) {
  peakPagination.pageSize = size
  peakPagination.page = 1
  loadPeaks()
}

function handleSpectrumFilterChange() {
  spectrumPagination.page = 1
  loadSpectra()
}

function handleSpectrumSearch() {
  spectrumPagination.page = 1
  loadSpectra()
}

function handleSpectrumPageChange(page: number) {
  spectrumPagination.page = page
  loadSpectra()
}

function handleSpectrumSizeChange(size: number) {
  spectrumPagination.pageSize = size
  spectrumPagination.page = 1
  loadSpectra()
}

function handleLibraryImportFileChange(file: any) {
  libraryImportFile.value = file.raw as File
}

function handleLibraryImportFileRemove() {
  libraryImportFile.value = null
}

async function handleImportLibraryDrugs() {
  if (!libraryImportFile.value) {
    ElMessage.warning('请选择要导入的药物列表 JSON 文件')
    return
  }

  const formData = new FormData()
  formData.append('file', libraryImportFile.value)
  if (libraryImportCategoryId.value !== undefined) {
    formData.append('categoryId', String(libraryImportCategoryId.value))
  }

  libraryImporting.value = true
  libraryImportSuccess.value = false
  libraryImportMessage.value = ''
  libraryImportFailed.value = []

  try {
    const res = await importLibraryDrugs(formData)
    const { created, updated, failed } = res.data
    libraryImportSuccess.value = true
    libraryImportFailed.value = failed || []
    libraryImportMessage.value =
      `导入完成：新建 ${created} 条，更新 ${updated} 条` +
      (libraryImportFailed.value.length > 0 ? `，失败 ${libraryImportFailed.value.length} 条` : '')
    ElMessage.success('药物列表导入成功')
    loadDrugs()
  } catch (error) {
    libraryImportSuccess.value = false
    libraryImportMessage.value = '导入失败，请稍后重试'
  } finally {
    libraryImporting.value = false
  }
}

function handleTabChange(tabName: string) {
  if (tabName === 'peaks') {
    loadPeaks()
  } else if (tabName === 'spectra') {
    loadSpectra()
  }
}

onMounted(() => {
  loadCategories()
  loadDrugs()
  loadDrugOptions()
})
</script>

<style scoped lang="scss">
.library-card {
  min-height: 600px;

  :deep(.glass-card__content) {
    padding: 16px 20px 24px;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.placeholder {
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  padding: 60px 0;
}

.detail-section {
  font-size: 15px;
  font-weight: 600;
  margin: 20px 0 12px;
  color: rgba(255, 255, 255, 0.92);
}

.import-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.import-uploader {
  width: 100%;

  :deep(.el-upload-dragger) {
    background: rgba(255, 255, 255, 0.04);
    border: 1px dashed rgba(255, 255, 255, 0.22);
    border-radius: 12px;

    &:hover {
      border-color: rgba(64, 158, 255, 0.55);
      background: rgba(64, 158, 255, 0.06);
    }
  }

  :deep(.el-upload__text) {
    color: rgba(255, 255, 255, 0.72);
  }
}

.upload-icon {
  font-size: 40px;
  color: rgba(64, 158, 255, 0.72);
  margin-bottom: 8px;
}

.upload-text {
  color: rgba(255, 255, 255, 0.88);
  font-size: 15px;
  margin-bottom: 4px;
}

.upload-tip {
  color: rgba(255, 255, 255, 0.52);
  font-size: 12px;
}

.import-form {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.row-actions {
  display: flex;
  gap: 8px;
}

.import-result {
  margin-top: 4px;
}

:deep(.el-table) {
  --el-table-header-bg-color: rgba(255, 255, 255, 0.06);
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-border-color: rgba(255, 255, 255, 0.1);
  --el-table-text-color: rgba(255, 255, 255, 0.86);
  --el-table-header-text-color: rgba(255, 255, 255, 0.92);
}

:deep(.el-pagination) {
  --el-pagination-text-color: rgba(255, 255, 255, 0.72);
  --el-pagination-button-color: rgba(255, 255, 255, 0.72);
}

:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset !important;
}

:deep(.el-input__inner) {
  color: rgba(255, 255, 255, 0.92);
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.42);
}
</style>
