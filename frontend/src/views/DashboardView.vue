<template>
  <div class="page-container">
    <h2 class="page-title">仪表盘</h2>

    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="12" :md="6">
        <GlassCard class="stat-card" :tilt="false">
          <div class="stat-item">
            <div class="stat-icon pending">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.pending }}</div>
              <div class="stat-label">待检测样本</div>
            </div>
          </div>
        </GlassCard>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <GlassCard class="stat-card" :tilt="false">
          <div class="stat-item">
            <div class="stat-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.completed }}</div>
              <div class="stat-label">已完成检测</div>
            </div>
          </div>
        </GlassCard>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <GlassCard class="stat-card" :tilt="false">
          <div class="stat-item">
            <div class="stat-icon primary">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.drugs }}</div>
              <div class="stat-label">对照品药物</div>
            </div>
          </div>
        </GlassCard>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <GlassCard class="stat-card" :tilt="false">
          <div class="stat-item">
            <div class="stat-icon warning">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.reports }}</div>
              <div class="stat-label">今日报告</div>
            </div>
          </div>
        </GlassCard>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24" :md="12">
        <GlassCard class="status-card" :tilt="false">
          <template #header>
            <div class="card-header">
              <span class="card-title">后端服务状态</span>
              <GlassButton
                class="refresh-btn"
                :loading="loading"
                @click="checkHealth"
                aria-label="刷新状态"
              >
                <el-icon><Refresh /></el-icon>
              </GlassButton>
            </div>
          </template>
          <div v-if="loading" class="status-loading">
            <el-skeleton :rows="2" animated />
          </div>
          <div v-else class="status-content">
            <div class="status-badge">
              <el-tag :type="healthStatus.type" size="large" effect="dark">
                {{ healthStatus.text }}
              </el-tag>
            </div>
            <div v-if="healthInfo" class="status-meta">
              <p><strong>服务：</strong>{{ healthInfo.service }}</p>
              <p><strong>时间：</strong>{{ formatTime(healthInfo.timestamp) }}</p>
            </div>
          </div>
        </GlassCard>
      </el-col>
      <el-col :xs="24" :md="12">
        <GlassCard class="quick-actions-card" :tilt="false">
          <template #header>
            <span class="card-title">快捷操作</span>
          </template>
          <div class="quick-actions">
            <GlassButton primary large @click="goToDetection">
              <el-icon><Plus /></el-icon>
              新建检测
            </GlassButton>
            <GlassButton large @click="goToLibrary">
              <el-icon><Collection /></el-icon>
              管理数据库
            </GlassButton>
          </div>
        </GlassCard>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  CircleCheck,
  Collection,
  Document,
  Plus,
  Refresh,
  Timer,
} from '@element-plus/icons-vue'
import { getHealth, getStats, type HealthInfo } from '@/api/common'
import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'

const router = useRouter()
const loading = ref(false)
const healthInfo = ref<HealthInfo | null>(null)
const healthStatus = reactive({
  type: 'info' as 'success' | 'danger' | 'info' | 'warning',
  text: '未检测',
})

const stats = reactive({
  pending: 0,
  completed: 0,
  drugs: 0,
  reports: 0,
})

async function checkHealth() {
  loading.value = true
  try {
    const res = await getHealth()
    healthInfo.value = res.data
    healthStatus.type = 'success'
    healthStatus.text = '后端服务正常'
  } catch (error) {
    healthStatus.type = 'danger'
    healthStatus.text = '后端服务异常'
    ElMessage.error('无法连接到后端服务')
  } finally {
    loading.value = false
  }
}

function formatTime(isoTime: string): string {
  try {
    return new Date(isoTime).toLocaleString('zh-CN')
  } catch {
    return isoTime
  }
}

async function loadStats() {
  try {
    const res = await getStats()
    stats.pending = res.data.pending
    stats.completed = res.data.completed
    stats.drugs = res.data.drugs
    stats.reports = res.data.reports
  } catch {
    ElMessage.error('加载仪表盘统计失败')
  }
}

let refreshInterval: number | null = null

function startAutoRefresh() {
  refreshInterval = window.setInterval(loadStats, 10000)
}

function stopAutoRefresh() {
  if (refreshInterval !== null) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

function goToDetection() {
  router.push('/detection')
}

function goToLibrary() {
  router.push('/library')
}

onMounted(() => {
  loadStats()
  checkHealth()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped lang="scss">
.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  margin-bottom: 16px;
  transition: transform 0.2s ease;

  :deep(.glass-card__content) {
    padding: 18px 20px;
  }

  &:hover {
    transform: translateY(-2px);
  }
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);

  &.pending {
    background: linear-gradient(135deg, rgba(144, 147, 153, 0.9), rgba(110, 115, 125, 0.9));
  }

  &.success {
    background: linear-gradient(135deg, rgba(103, 194, 58, 0.9), rgba(72, 160, 40, 0.9));
  }

  &.primary {
    background: linear-gradient(135deg, rgba(64, 158, 255, 0.9), rgba(40, 120, 230, 0.9));
  }

  &.warning {
    background: linear-gradient(135deg, rgba(230, 162, 60, 0.9), rgba(200, 130, 30, 0.9));
  }
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.96);
  line-height: 1.2;
}

.stat-label {
  color: rgba(255, 255, 255, 0.55);
  font-size: 14px;
  margin-top: 4px;
}

.content-row {
  align-items: stretch;
}

.status-card,
.quick-actions-card {
  height: 100%;

  :deep(.glass-card__content) {
    padding: 20px;
  }
}

.card-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
}

.refresh-btn {
  padding: 7px 10px;
}

.status-loading {
  padding: 20px 0;
}

.status-content {
  text-align: center;
  padding: 20px 0;
}

.status-badge {
  margin-bottom: 16px;
}

.status-meta {
  color: rgba(255, 255, 255, 0.72);
  line-height: 2;

  p {
    margin: 4px 0;
  }

  strong {
    color: rgba(255, 255, 255, 0.92);
  }
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px 0;
  justify-content: center;
}
</style>
