<template>
  <div class="page-container">
    <h2 class="page-title">操作日志</h2>
    <GlassCard :tilt="false">
      <el-table v-loading="loading" :data="logs" border style="width: 100%">
        <el-table-column prop="createdAt" label="时间" min-width="160">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作人" min-width="140">
          <template #default="{ row }">
            {{ row.operator }}
            <el-tag v-if="row.operatorNo" size="small" type="info">{{ row.operatorNo }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作" min-width="120" />
        <el-table-column prop="module" label="模块" min-width="100" />
        <el-table-column prop="targetType" label="目标类型" min-width="100" />
        <el-table-column prop="targetId" label="目标ID" min-width="100" />
        <el-table-column prop="ipAddress" label="IP 地址" min-width="120" />
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.detail ? JSON.stringify(row.detail) : '-' }}
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
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getLogs, type OperationLogItem } from '@/api/common'
import { formatChinaTime as formatTime } from '@/utils/formatTime'
import GlassCard from '@/components/GlassCard.vue'

const loading = ref(false)
const logs = ref<OperationLogItem[]>([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

async function loadLogs() {
  loading.value = true
  try {
    const res = await getLogs({
      page: pagination.page,
      pageSize: pagination.pageSize,
    })
    logs.value = res.data.items
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('加载操作日志失败')
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  pagination.page = page
  loadLogs()
}

function handleSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  loadLogs()
}

onMounted(() => {
  loadLogs()
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
