<template>
  <div class="page-container">
    <h2 class="page-title">检测报告</h2>
    <GlassCard :tilt="false">
      <el-table v-loading="loading" :data="samples" border stripe style="width: 100%">
        <el-table-column prop="sampleNo" label="样品编号" min-width="160" />
        <el-table-column prop="sampleName" label="样品名称" min-width="160" />
        <el-table-column prop="createdAt" label="检测时间" min-width="180" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType[row.status] || 'info'" size="small">
              {{ statusText[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <GlassButton primary @click="downloadReportFile(row.id, 'pdf')">
              下载 PDF
            </GlassButton>
            <GlassButton @click="downloadReportFile(row.id, 'excel')">
              下载 Excel
            </GlassButton>
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
        @size-change="loadSamples"
        @current-change="loadSamples"
      />
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listSamples, type SampleItem } from '@/api/sample'
import { downloadReport as apiDownloadReport } from '@/api/detection'
import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'

const loading = ref(false)
const samples = ref<SampleItem[]>([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const statusType: Record<string, any> = {
  pending: 'info',
  running: 'warning',
  success: 'success',
  failed: 'danger',
}

const statusText: Record<string, string> = {
  pending: '待检测',
  running: '检测中',
  success: '已完成',
  failed: '失败',
}

async function loadSamples() {
  loading.value = true
  try {
    const res = await listSamples({
      page: pagination.page,
      pageSize: pagination.pageSize,
    })
    samples.value = res.data.items
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载样本列表失败')
  } finally {
    loading.value = false
  }
}

async function downloadReportFile(sampleId: number, format: 'pdf' | 'excel') {
  try {
    const res = await apiDownloadReport(sampleId, format)
    const blob = new Blob([res.data])
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${sampleId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('报告下载成功')
  } catch (error) {
    ElMessage.error('报告下载失败')
  }
}

onMounted(() => {
  loadSamples()
})
</script>

<style scoped lang="scss">
:deep(.glass-card__content) {
  padding: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
