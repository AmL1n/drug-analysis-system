<template>
  <div class="page-container">
    <h2 class="page-title">检测分析</h2>

    <GlassCard class="step-card" :tilt="false">
      <el-steps :active="currentStep" finish-status="success" simple>
        <el-step title="上传数据" />
        <el-step title="峰识别" />
        <el-step title="模型匹配" />
        <el-step title="查看结果" />
      </el-steps>
    </GlassCard>

    <GlassCard class="config-card" :tilt="false">
      <template #header>
        <div class="config-header" @click="configExpanded = !configExpanded">
          <span class="card-header-title">本次实验配置</span>
          <el-icon class="config-toggle-icon" :class="{ 'is-expanded': configExpanded }">
            <arrow-down />
          </el-icon>
        </div>
      </template>

      <el-collapse-transition>
        <div v-show="configExpanded">
          <el-form label-position="top" class="config-form">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12">
                <el-form-item label="模型类型">
                  <el-select v-model="experimentConfig.modelType" style="width: 100%">
                    <el-option label="融合模型" value="fusion" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="Top-N">
                  <el-input-number v-model="experimentConfig.topN" :min="1" :max="50" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="置信度阈值">
                  <el-input-number
                    v-model="experimentConfig.confidenceThreshold"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="RRT 容差">
                  <el-input-number
                    v-model="experimentConfig.rrtTolerance"
                    :min="0"
                    :max="1"
                    :step="0.001"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="UV 距离阈值">
                  <el-input-number
                    v-model="experimentConfig.uvDistanceThreshold"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="峰面积比方法">
                  <el-select v-model="experimentConfig.areaRatioMethod" style="width: 100%">
                    <el-option label="relative_error" value="relative_error" />
                    <el-option label="cosine" value="cosine" />
                    <el-option label="correlation" value="correlation" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-collapse-transition>
    </GlassCard>

    <el-tabs v-model="activeTab" type="border-card" class="detect-tabs">
      <el-tab-pane label="文件上传检测" name="file">
        <el-row :gutter="20" class="main-row">
          <el-col :xs="24" :md="7">
            <GlassCard class="upload-card" :tilt="false">
              <template #header>
                <span class="card-header-title">上传样品数据</span>
              </template>

              <el-upload
                ref="uploadRef"
                drag
                action="#"
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                accept=".txt,.csv,.xlsx,.xls"
                class="upload-area"
              >
                <el-icon class="el-icon--upload" size="48"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  将文件拖到此处，或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 TXT / CSV / Excel 格式，单个文件不超过 50MB
                  </div>
                </template>
              </el-upload>

              <el-form label-position="top" class="sample-form">
                <el-form-item label="样品名称">
                  <el-input v-model="sampleName" placeholder="请输入样品名称" />
                </el-form-item>
                <el-form-item label="仪器品牌">
                  <el-select v-model="instrumentBrand" placeholder="请选择仪器品牌" style="width: 100%">
                    <el-option label="Agilent" value="Agilent" />
                    <el-option label="Waters" value="Waters" />
                    <el-option label="Shimadzu" value="Shimadzu" />
                    <el-option label="其它" value="Other" />
                  </el-select>
                </el-form-item>
              </el-form>

              <GlassButton
                primary
                large
                :loading="detecting"
                :disabled="!selectedFile"
                style="width: 100%"
                @click="handleDetect"
              >
                {{ detecting ? '检测中...' : '开始检测' }}
              </GlassButton>
            </GlassCard>
          </el-col>

          <el-col :xs="24" :md="17">
            <GlassCard class="result-card" :tilt="false">
              <template #header>
                <span class="card-header-title">检测结果</span>
              </template>

              <el-empty v-if="!result" description="请先上传文件并点击开始检测">
                <template #image>
                  <el-icon size="64" color="rgba(255,255,255,0.25)"><DataAnalysis /></el-icon>
                </template>
              </el-empty>

              <div v-else>
                <div class="result-summary">
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="样品编号">{{ result.sample_no }}</el-descriptions-item>
                    <el-descriptions-item label="样品名称">{{ result.sample_name || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="候选药物数">{{ result.summary.total_candidates }}</el-descriptions-item>
                    <el-descriptions-item label="检出药物数">
                      <el-tag :type="result.summary.detected_count > 0 ? 'danger' : 'success'">
                        {{ result.summary.detected_count }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="检测时间">{{ formatChinaTime(result.detect_time) }}</el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="result-actions">
                  <GlassButton primary :icon="Document" @click="downloadReportFile('pdf')">
                    <el-icon><Document /></el-icon>
                    下载 PDF 报告
                  </GlassButton>
                  <GlassButton @click="downloadReportFile('excel')">
                    <el-icon><Document /></el-icon>
                    下载 Excel 报告
                  </GlassButton>
                </div>

                <div class="result-table-header">
                  <h3 class="section-title">Top 候选药物</h3>
                  <div class="filter-tip">
                    <el-icon size="14"><InfoFilled /></el-icon>
                    <span>综合评分低于 20% 的结果已隐藏</span>
                    <el-tooltip
                      content="综合评分过低的候选结果参考价值有限，已自动过滤。可在上方「实验配置」中调整置信度阈值后重新检测。"
                      placement="top"
                    >
                      <el-icon size="14" class="tip-icon"><InfoFilled /></el-icon>
                    </el-tooltip>
                  </div>
                </div>
                <el-table
                  v-if="filteredDetectionResults.length > 0"
                  :data="filteredDetectionResults"
                  border
                  stripe
                  highlight-current-row
                  class="detection-result-table"
                  style="width: 100%"
                  @current-change="handleDrugSelect"
                >
                  <el-table-column type="index" width="50" label="排名" />
                  <el-table-column prop="drugName" label="药物名称" min-width="140" />
                  <el-table-column prop="totalScore" label="综合评分" width="140">
                    <template #default="{ row }">
                      <el-progress
                        :percentage="Math.round(row.totalScore * 100)"
                        :color="scoreColor"
                        :show-text="true"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column prop="confidence" label="置信度" width="120">
                    <template #default="{ row }">
                      {{ (row.confidence * 100).toFixed(1) }}%
                    </template>
                  </el-table-column>
                  <el-table-column prop="matchedPeakCount" label="匹配峰数" width="120">
                    <template #default="{ row }">
                      {{ row.matchedPeakCount }} / {{ row.totalPeakCount }}
                    </template>
                  </el-table-column>
                  <el-table-column label="状态" width="95">
                    <template #default="{ row }">
                      <el-tag
                        :type="row.isDetected ? 'danger' : 'info'"
                        size="small"
                        class="status-tag"
                      >
                        {{ row.isDetected ? '检出' : '未检出' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="130">
                    <template #default="{ row }">
                      <el-button
                        link
                        type="primary"
                        size="small"
                        class="train-button"
                        @click.stop="handleTrainRrt(row)"
                      >
                        确认并训练
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>

                <el-result
                  v-if="filteredDetectionResults.length === 0"
                  icon="info"
                  title="未匹配到候选药物"
                  sub-title="请确认样品数据质量或补充对照品库"
                />
              </div>
            </GlassCard>

            <GlassCard
              v-if="result"
              class="chart-card"
              :tilt="false"
              :halo="false"
              :glare="false"
              :rim="false"
            >
              <template #header>
                <div class="chart-header">
                  <span class="card-header-title">峰值图对比</span>
                  <span v-if="selectedDrug" class="chart-subtitle">
                    当前对照：{{ selectedDrug.drugName }}
                  </span>
                </div>
              </template>
              <div ref="chartRef" class="chart-container" />
              <el-empty
                v-if="chromatogramError"
                :description="chromatogramError"
                class="chart-empty"
              />
            </GlassCard>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="级联检测 / 手动录入" name="cascade">
        <el-row :gutter="20" class="main-row">
          <el-col :xs="24" :md="8">
            <GlassCard class="upload-card" :tilt="false">
              <template #header>
                <span class="card-header-title">级联检测录入</span>
              </template>

              <el-form label-position="top" class="cascade-form">
                <el-form-item label="药物类别">
                  <el-select
                    v-model="cascadeForm.categoryId"
                    placeholder="请选择药物类别"
                    style="width: 100%"
                    @change="onCascadeCategoryChange"
                  >
                    <el-option
                      v-for="cat in categories"
                      :key="cat.id"
                      :label="cat.name"
                      :value="cat.id"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="参照药物">
                  <el-select
                    v-model="cascadeForm.referenceDrugId"
                    placeholder="请选择参照药物"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="drug in referenceDrugs"
                      :key="drug.id"
                      :label="`${drug.name} (ts=${drug.retentionTime}min)`"
                      :value="drug.id"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="保留时间 tx (min)">
                  <el-input-number
                    v-model="cascadeForm.tx"
                    :min="0.001"
                    :step="0.001"
                    :precision="3"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="λ1 (nm)">
                      <el-input-number
                        v-model="cascadeForm.lambda1"
                        :min="0"
                        :step="0.1"
                        :precision="1"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="λ2 (nm)">
                      <el-input-number
                        v-model="cascadeForm.lambda2"
                        :min="0"
                        :step="0.1"
                        :precision="1"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>

                <div class="area-section-title">不同波长下峰面积（A245 / A250 / A255 / A260）</div>
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="A245 峰面积">
                      <el-input-number
                        v-model="cascadeForm.areas['245']"
                        :min="1"
                        :step="1000"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="A250 峰面积">
                      <el-input-number
                        v-model="cascadeForm.areas['250']"
                        :min="1"
                        :step="1000"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="A255 峰面积">
                      <el-input-number
                        v-model="cascadeForm.areas['255']"
                        :min="1"
                        :step="1000"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="A260 峰面积">
                      <el-input-number
                        v-model="cascadeForm.areas['260']"
                        :min="1"
                        :step="1000"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-collapse v-model="cascadeThresholdExpanded">
                  <el-collapse-item title="阈值设定" name="thresholds">
                    <el-form-item label="RRT 容差">
                      <el-input-number
                        v-model="cascadeForm.thresholds.rrtTolerance"
                        :min="0.001"
                        :step="0.001"
                        :precision="3"
                        style="width: 100%"
                      />
                    </el-form-item>
                    <el-form-item label="Lambda 容差 (nm)">
                      <el-input-number
                        v-model="cascadeForm.thresholds.lambdaTolerance"
                        :min="0.1"
                        :step="0.1"
                        :precision="1"
                        style="width: 100%"
                      />
                    </el-form-item>
                    <el-form-item label="R1 容差">
                      <el-input-number
                        v-model="cascadeForm.thresholds.r1Tolerance"
                        :min="0.001"
                        :step="0.01"
                        :precision="3"
                        style="width: 100%"
                      />
                    </el-form-item>
                    <el-form-item label="R2 容差">
                      <el-input-number
                        v-model="cascadeForm.thresholds.r2Tolerance"
                        :min="0.001"
                        :step="0.01"
                        :precision="3"
                        style="width: 100%"
                      />
                    </el-form-item>
                    <el-form-item label="R3 容差">
                      <el-input-number
                        v-model="cascadeForm.thresholds.r3Tolerance"
                        :min="0.001"
                        :step="0.01"
                        :precision="3"
                        style="width: 100%"
                      />
                    </el-form-item>
                    <GlassButton
                      style="width: 100%; margin-top: 8px"
                      :loading="savingThresholds"
                      @click="saveCascadeThresholds"
                    >
                      保存阈值
                    </GlassButton>
                  </el-collapse-item>
                </el-collapse>
              </el-form>

              <GlassButton
                primary
                large
                :loading="cascadeDetecting"
                style="width: 100%; margin-top: 16px"
                @click="handleCascadeDetect"
              >
                {{ cascadeDetecting ? '检测中...' : '开始级联检测' }}
              </GlassButton>
            </GlassCard>
          </el-col>

          <el-col :xs="24" :md="16">
            <GlassCard class="result-card" :tilt="false">
              <template #header>
                <span class="card-header-title">级联检测结果</span>
              </template>

              <el-empty v-if="!cascadeResult" description="请录入参数并点击开始级联检测">
                <template #image>
                  <el-icon size="64" color="rgba(255,255,255,0.25)"><DataAnalysis /></el-icon>
                </template>
              </el-empty>

              <div v-else class="cascade-result">
                <div class="result-summary">
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="参照药物">
                      {{ cascadeResult.referenceDrug.name }} (ts={{ cascadeResult.referenceDrug.retentionTime }}min)
                    </el-descriptions-item>
                    <el-descriptions-item label="样本 RRT">
                      {{ cascadeResult.step1.rrtSample.toFixed(6) }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <!-- Step 1 -->
                <div class="step-section step-1">
                  <div class="step-header">
                    <el-tag type="primary" effect="dark" size="large">Step 1</el-tag>
                    <span class="step-title">相对保留时间初筛</span>
                    <span class="step-count">命中 {{ cascadeResult.step1.candidateCount }} 个</span>
                  </div>
                  <div class="step-meta">
                    <span>rrtSample = tx / ts = {{ cascadeResult.step1.rrtSample.toFixed(6) }}</span>
                    <span>容差：±{{ cascadeResult.step1.tolerance }}</span>
                  </div>
                  <el-table
                    :data="cascadeResult.step1.candidates"
                    border
                    stripe
                    size="small"
                    style="width: 100%"
                  >
                    <el-table-column type="index" width="45" label="#" />
                    <el-table-column prop="drugName" label="药物名称" min-width="140" />
                    <el-table-column prop="rrtDb" label="库 RRT" width="120" />
                    <el-table-column prop="delta" label="偏差" width="120" />
                  </el-table>
                </div>

                <!-- Step 2 -->
                <div class="step-section step-2">
                  <div class="step-header">
                    <el-tag type="success" effect="dark" size="large">Step 2</el-tag>
                    <span class="step-title">紫外最大吸收波长复筛</span>
                    <span class="step-count">命中 {{ cascadeResult.step2.candidateCount }} 个</span>
                  </div>
                  <div class="step-meta">
                    <span>λ1 = {{ cascadeResult.step2.lambda1 ?? '-' }} nm</span>
                    <span>λ2 = {{ cascadeResult.step2.lambda2 ?? '-' }} nm</span>
                    <span>容差：±{{ cascadeResult.step2.tolerance }} nm</span>
                  </div>
                  <el-table
                    :data="cascadeResult.step2.candidates"
                    border
                    stripe
                    size="small"
                    style="width: 100%"
                  >
                    <el-table-column type="index" width="45" label="#" />
                    <el-table-column prop="drugName" label="药物名称" min-width="140" />
                    <el-table-column prop="rrtDb" label="库 RRT" width="120" />
                    <el-table-column prop="delta" label="偏差" width="120" />
                  </el-table>
                </div>

                <!-- Step 3 -->
                <div class="step-section step-3">
                  <div class="step-header">
                    <el-tag type="danger" effect="dark" size="large">Step 3</el-tag>
                    <span class="step-title">峰面积常数最终定性</span>
                  </div>
                  <div class="step-meta">
                    <span>样本 R1 = {{ cascadeResult.step3.r1.toFixed(6) }}</span>
                    <span>样本 R2 = {{ cascadeResult.step3.r2.toFixed(6) }}</span>
                    <span>样本 R3 = {{ cascadeResult.step3.r3.toFixed(6) }}</span>
                  </div>
                  <el-table
                    :data="cascadeResult.step3.results"
                    border
                    stripe
                    highlight-current-row
                    size="small"
                    style="width: 100%"
                  >
                    <el-table-column type="index" width="45" label="#" />
                    <el-table-column prop="drugName" label="药物名称" min-width="140" />
                    <el-table-column label="库 R1/R2/R3" min-width="160">
                      <template #default="{ row }">
                        {{ row.r1Db.toFixed(4) }} / {{ row.r2Db.toFixed(4) }} / {{ row.r3Db.toFixed(4) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="偏差" min-width="140">
                      <template #default="{ row }">
                        {{ row.deltaR1.toFixed(4) }} / {{ row.deltaR2.toFixed(4) }} / {{ row.deltaR3.toFixed(4) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="综合得分" width="120">
                      <template #default="{ row }">
                        <el-progress
                          :percentage="Math.round(row.score * 100)"
                          :color="scoreColor"
                          :show-text="true"
                        />
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </GlassCard>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { ArrowDown, DataAnalysis, Document, InfoFilled, UploadFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { uploadFile } from '@/api/file'
import { createSample } from '@/api/sample'
import {
  detectCascade,
  detectSample,
  downloadReport,
  getDetectionResults,
  type CascadeDetectResult,
  type DetectionResultItem,
} from '@/api/detection'
import { getSystemConfig, setSystemConfig } from '@/api/config'
import {
  getCategories,
  getCategoryReferenceDrug,
  getCategoryReferenceDrugs,
  trainDrugRrt,
  type CategoryItem,
  type ReferenceDrugItem,
} from '@/api/library'
import { getSampleChromatogram, type ChromatogramData } from '@/api/sample'
import { formatChinaTime } from '@/utils/formatTime'
import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'

const currentStep = ref(0)
const selectedFile = ref<File | null>(null)
const sampleName = ref('')
const instrumentBrand = ref('')
const detecting = ref(false)
const result = ref<Record<string, any> | null>(null)
const sampleId = ref<number | null>(null)
const chromatogram = ref<ChromatogramData | null>(null)
const chromatogramError = ref('')
const detectionResults = ref<DetectionResultItem[]>([])
const filteredDetectionResults = computed(() =>
  detectionResults.value.filter((item) => item.totalScore >= 0.2),
)
const selectedDrug = ref<DetectionResultItem | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
const uploadRef = ref<any>(null)
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const configExpanded = ref(false)
const experimentConfig = reactive({
  modelType: 'fusion',
  topN: 10,
  confidenceThreshold: 0.7,
  rrtTolerance: 0.02,
  uvDistanceThreshold: 0.15,
  areaRatioMethod: 'relative_error' as 'relative_error' | 'cosine' | 'correlation',
})

const scoreColor = [
  { color: '#f56c6c', percentage: 80 },
  { color: '#e6a23c', percentage: 60 },
  { color: '#67c23a', percentage: 40 },
  { color: '#909399', percentage: 20 },
]

// 级联检测
const activeTab = ref('file')
const categories = ref<CategoryItem[]>([])
const referenceDrugs = ref<ReferenceDrugItem[]>([])
const cascadeDetecting = ref(false)
const savingThresholds = ref(false)
const cascadeResult = ref<CascadeDetectResult | null>(null)
const cascadeThresholdExpanded = ref<string[]>(['thresholds'])
const CASCADING_THRESHOLDS_KEY = 'cascade_thresholds'
const DEFAULT_THRESHOLDS = {
  rrtTolerance: 0.03,
  lambdaTolerance: 2.0,
  r1Tolerance: 0.1,
  r2Tolerance: 0.1,
  r3Tolerance: 0.1,
}

const cascadeForm = reactive({
  categoryId: null as number | null,
  referenceDrugId: null as number | null,
  tx: undefined as number | undefined,
  lambda1: undefined as number | undefined,
  lambda2: undefined as number | undefined,
  areas: {
    '245': undefined as number | undefined,
    '250': undefined as number | undefined,
    '255': undefined as number | undefined,
    '260': undefined as number | undefined,
  },
  thresholds: { ...DEFAULT_THRESHOLDS },
})

function applyCascadeThresholds(saved: Record<string, any> | null | undefined) {
  if (!saved || typeof saved !== 'object') return
  const keys = Object.keys(DEFAULT_THRESHOLDS) as Array<keyof typeof DEFAULT_THRESHOLDS>
  keys.forEach((key) => {
    const value = saved[key]
    if (typeof value === 'number' && value > 0) {
      cascadeForm.thresholds[key] = value
    }
  })
}

async function loadCascadeThresholds() {
  try {
    const res = await getSystemConfig(CASCADING_THRESHOLDS_KEY)
    applyCascadeThresholds(res.data.value)
  } catch (error) {
    console.warn('加载级联阈值配置失败，使用默认值:', error)
  }
}

async function saveCascadeThresholds() {
  savingThresholds.value = true
  try {
    await setSystemConfig(CASCADING_THRESHOLDS_KEY, { ...cascadeForm.thresholds }, '级联检测阈值设定')
    ElMessage.success('阈值已保存')
  } catch (error) {
    console.error('保存阈值失败:', error)
  } finally {
    savingThresholds.value = false
  }
}

async function loadCategories() {
  try {
    const res = await getCategories()
    categories.value = res.data
    if (categories.value.length > 0 && cascadeForm.categoryId === null) {
      cascadeForm.categoryId = categories.value[0].id
      await onCascadeCategoryChange(cascadeForm.categoryId)
    }
  } catch (error) {
    console.error('加载药物类别失败:', error)
    ElMessage.error('加载药物类别失败')
  }
}

async function loadReferenceDrugs(categoryId: number) {
  try {
    const res = await getCategoryReferenceDrugs(categoryId)
    referenceDrugs.value = res.data
  } catch (error) {
    console.error('加载参照药物失败:', error)
    referenceDrugs.value = []
  }
}

async function loadDefaultReferenceDrug(categoryId: number) {
  try {
    const res = await getCategoryReferenceDrug(categoryId)
    if (res.data && res.data.id) {
      cascadeForm.referenceDrugId = res.data.id
    } else if (referenceDrugs.value.length > 0) {
      cascadeForm.referenceDrugId = referenceDrugs.value[0].id
    } else {
      cascadeForm.referenceDrugId = null
    }
  } catch (error) {
    console.error('加载默认参照药物失败:', error)
    if (referenceDrugs.value.length > 0) {
      cascadeForm.referenceDrugId = referenceDrugs.value[0].id
    } else {
      cascadeForm.referenceDrugId = null
    }
  }
}

async function onCascadeCategoryChange(categoryId: number) {
  cascadeForm.referenceDrugId = null
  await loadReferenceDrugs(categoryId)
  await loadDefaultReferenceDrug(categoryId)
}

async function handleCascadeDetect() {
  if (!cascadeForm.categoryId) {
    ElMessage.warning('请选择药物类别')
    return
  }
  if (!cascadeForm.referenceDrugId) {
    ElMessage.warning('请选择参照药物')
    return
  }
  if (!cascadeForm.tx || cascadeForm.tx <= 0) {
    ElMessage.warning('保留时间 tx 必须大于 0')
    return
  }
  const areaKeys = ['245', '250', '255', '260'] as const
  for (const key of areaKeys) {
    const value = cascadeForm.areas[key]
    if (!value || value <= 0) {
      ElMessage.warning(`A${key} 必须大于 0`)
      return
    }
  }

  cascadeDetecting.value = true
  cascadeResult.value = null
  try {
    const res = await detectCascade({
      categoryId: cascadeForm.categoryId,
      referenceDrugId: cascadeForm.referenceDrugId,
      tx: cascadeForm.tx,
      lambda1: cascadeForm.lambda1 ?? null,
      lambda2: cascadeForm.lambda2 ?? null,
      areas: {
        '245': cascadeForm.areas['245']!,
        '250': cascadeForm.areas['250']!,
        '255': cascadeForm.areas['255']!,
        '260': cascadeForm.areas['260']!,
      },
      thresholds: { ...cascadeForm.thresholds },
      topN: 10,
    })
    cascadeResult.value = res.data
    ElMessage.success('级联检测完成')
  } catch (error) {
    console.error('级联检测失败:', error)
  } finally {
    cascadeDetecting.value = false
  }
}

onMounted(() => {
  loadCategories()
  loadCascadeThresholds()
})

function handleFileChange(uploadFile: UploadFile) {
  selectedFile.value = uploadFile.raw || null
  currentStep.value = 0
}

function handleFileRemove() {
  selectedFile.value = null
  currentStep.value = 0
}

async function handleDetect() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  detecting.value = true
  currentStep.value = 1
  result.value = null
  chromatogram.value = null
  chromatogramError.value = ''
  detectionResults.value = []
  selectedDrug.value = null

  try {
    const uploadRes = await uploadFile(selectedFile.value)
    const fileId = uploadRes.data.id
    currentStep.value = 2

    const sampleRes = await createSample({
      sampleName: sampleName.value || undefined,
      fileId,
      instrumentBrand: instrumentBrand.value || undefined,
    })
    sampleId.value = sampleRes.data.id
    currentStep.value = 3

    const detectRes = await detectSample({
      sampleId: sampleId.value,
      modelType: experimentConfig.modelType,
      topN: experimentConfig.topN,
      confidenceThreshold: experimentConfig.confidenceThreshold,
      rrtTolerance: experimentConfig.rrtTolerance,
      uvDistanceThreshold: experimentConfig.uvDistanceThreshold,
      areaRatioMethod: experimentConfig.areaRatioMethod,
    })
    result.value = detectRes.data
    currentStep.value = 4
    ElMessage.success('检测完成')

    // 清空上传组件，避免文件残留
    uploadRef.value?.clearFiles()
    selectedFile.value = null
    sampleName.value = ''
    instrumentBrand.value = ''

    if (sampleId.value) {
      // 先获取检测结果，确保即使色谱图接口失败也能看到检测结论
      try {
        const resultsRes = await getDetectionResults(sampleId.value)
        detectionResults.value = resultsRes.data
        if (filteredDetectionResults.value.length > 0) {
          selectedDrug.value = filteredDetectionResults.value[0]
        }
      } catch (error) {
        console.error('加载检测结果失败:', error)
        ElMessage.error('加载检测结果失败')
      }

      // 再获取色谱图，失败时给出明确提示
      try {
        chromatogramError.value = ''
        const chromRes = await getSampleChromatogram(sampleId.value)
        chromatogram.value = chromRes.data
      } catch (error: any) {
        chromatogram.value = null
        chromatogramError.value = error?.response?.data?.msg || '色谱图数据加载失败'
        console.error('加载色谱图失败:', error)
      }

      nextTick(() => renderChart())
    }
  } catch (error) {
    currentStep.value = 0
    console.error('检测失败:', error)
  } finally {
    detecting.value = false
  }
}

function handleDrugSelect(row: DetectionResultItem | undefined) {
  selectedDrug.value = row || null
  renderChart()
}

function findNearestSamplePeak(retentionTime: number) {
  const peaks = chromatogram.value?.peaks
  if (!peaks || peaks.length === 0) return undefined

  let nearest = peaks[0]
  let minDiff = Math.abs(peaks[0].retentionTime - retentionTime)
  for (const peak of peaks) {
    const diff = Math.abs(peak.retentionTime - retentionTime)
    if (diff < minDiff) {
      minDiff = diff
      nearest = peak
    }
  }
  return nearest
}

function suggestDrugRrt(row: DetectionResultItem): number | undefined {
  const refPeaks = row.referencePeaks || []
  for (const ref of refPeaks) {
    if (
      ref.relativeRetentionTime == null ||
      ref.relativeRetentionTime <= 0 ||
      ref.retentionTime <= 0
    ) {
      continue
    }
    const referenceDrugRt = ref.retentionTime / ref.relativeRetentionTime
    const samplePeak = findNearestSamplePeak(ref.retentionTime)
    if (samplePeak && samplePeak.retentionTime > 0) {
      return samplePeak.retentionTime / referenceDrugRt
    }
  }
  return undefined
}

async function handleTrainRrt(row: DetectionResultItem) {
  const suggested = suggestDrugRrt(row)

  try {
    const { value, action } = await ElMessageBox.prompt(
      suggested !== undefined
        ? `系统将使用匹配样本峰推算的 RRT ${suggested.toFixed(6)} 训练「${row.drugName}」的 RRT 模型，也可手动修改。`
        : `请为「${row.drugName}」输入本次样本的 RRT 值以训练模型：`,
      '确认并训练 RRT',
      {
        confirmButtonText: '确认训练',
        cancelButtonText: '取消',
        inputValue: suggested !== undefined ? String(suggested.toFixed(6)) : '',
        inputValidator: (value) => {
          const num = Number(value)
          if (value === '' || Number.isNaN(num) || num <= 0) {
            return '请输入有效的正数 RRT'
          }
          return true
        },
      }
    )

    if (action !== 'confirm') return

    const rrt = Number(value)
    await trainDrugRrt(row.drugId, rrt)
    ElMessage.success(`「${row.drugName}」RRT 模型训练成功`)
  } catch (error: any) {
    if (error?.action === 'cancel' || error === 'cancel') return
    console.error('RRT 训练失败:', error)
    ElMessage.error(error?.response?.data?.msg || 'RRT 训练失败')
  }
}

function renderChart() {
  if (!chartRef.value) return

  // 清理旧实例，确保容器尺寸变化后能正确初始化
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  if (!chromatogram.value) {
    // 没有数据时不绘制，保留容器用于展示错误提示
    return
  }

  try {
    const time = chromatogram.value.time
    const intensity = chromatogram.value.intensity
    const samplePeaks = chromatogram.value.peaks || []
    const refPeaks = selectedDrug.value?.referencePeaks || []

    if (!time || !intensity || time.length === 0 || intensity.length === 0) {
      console.warn('色谱图数据为空，无法绘图')
      return
    }

    chartInstance = echarts.init(chartRef.value, 'dark')

    if (!resizeObserver) {
      resizeObserver = new ResizeObserver(() => {
        chartInstance?.resize()
      })
      resizeObserver.observe(chartRef.value)
    }

    const sampleMax = Math.max(...intensity, 1)
    const sampleCurve = time.map((t, i) => [t, intensity[i]])
    const referenceCurve = buildReferenceCurve(time, refPeaks, sampleMax)

    const sampleScatter = samplePeaks.map((p) => ({
      value: [p.retentionTime, findIntensity(p.retentionTime)],
      ...p,
    }))
    const refScatter = refPeaks.map((p) => ({
      value: [p.retentionTime, findReferenceIntensity(referenceCurve, p.retentionTime)],
      ...p,
    }))

    const markLineData = refPeaks.map((p) => ({
      xAxis: p.retentionTime,
      label: {
        formatter: `P${p.peakIndex}`,
        color: 'rgba(255,255,255,0.8)',
        fontSize: 10,
      },
      lineStyle: {
        color: 'rgba(255, 200, 120, 0.5)',
        type: 'dashed' as const,
        width: 1,
      },
    }))

  const series: echarts.SeriesOption[] = [
    {
      name: '样本色谱',
      type: 'line',
      data: sampleCurve,
      smooth: 0.35,
      showSymbol: false,
      lineStyle: { width: 3, color: '#4aa3ff' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(74, 163, 255, 0.35)' },
          { offset: 1, color: 'rgba(74, 163, 255, 0.02)' },
        ]),
      },
      emphasis: { focus: 'series' },
    },
    {
      name: '样本峰',
      type: 'scatter',
      data: sampleScatter,
      symbolSize: 12,
      itemStyle: {
        color: '#67c23a',
        borderColor: 'rgba(255,255,255,0.8)',
        borderWidth: 2,
        shadowBlur: 8,
        shadowColor: 'rgba(103, 194, 58, 0.5)',
      },
    },
  ]

  if (refPeaks.length > 0) {
    series.push(
      {
        name: '标准品曲线',
        type: 'line',
        data: referenceCurve,
        smooth: 0.35,
        showSymbol: false,
        lineStyle: { width: 2.5, color: '#f5b041' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245, 176, 65, 0.25)' },
            { offset: 1, color: 'rgba(245, 176, 65, 0.02)' },
          ]),
        },
        markLine: {
          symbol: 'none',
          data: markLineData,
          animation: false,
        },
        emphasis: { focus: 'series' },
      },
      {
        name: '标准品峰',
        type: 'scatter',
        data: refScatter,
        symbolSize: (d: any) => Math.max(8, Math.min(18, (d?.areaRatio || 0.2) * 30)),
        itemStyle: {
          color: '#f5b041',
          borderColor: 'rgba(255,255,255,0.85)',
          borderWidth: 2,
          shadowBlur: 10,
          shadowColor: 'rgba(245, 176, 65, 0.5)',
        },
      }
    )
  }

  chartInstance.setOption(
    {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(12, 14, 22, 0.82)',
        borderColor: 'rgba(255,255,255,0.15)',
        textStyle: { color: 'rgba(255,255,255,0.92)' },
        axisPointer: { type: 'cross', label: { backgroundColor: 'rgba(64,158,255,0.7)' } },
        formatter: (params: any) => {
          const axis = params[0]?.axisValue
          let html = `<div style="font-weight:600;margin-bottom:6px;">RT ${axis} min</div>`
          params.forEach((p: any) => {
            const data = p.data
            let val: number | undefined
            if (Array.isArray(data)) {
              val = data[1]
            } else if (Array.isArray(data.value)) {
              val = data.value[1]
            } else {
              val = data.value
            }
            const displayVal = typeof val === 'number' && !Number.isNaN(val) ? val.toFixed(2) : '-'
            html += `<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">
              <span style="width:10px;height:10px;border-radius:50%;background:${p.color}"></span>
              <span>${p.seriesName}: ${displayVal}</span>`
            if (data && data.peakIndex !== undefined) {
              html += `<span style="color:rgba(255,255,255,0.6);margin-left:8px;">P${data.peakIndex}`
              if (data.area !== undefined) html += ` / 面积 ${Number(data.area).toExponential(2)}`
              if (data.wavelength !== undefined) html += ` / λ ${data.wavelength}nm`
              html += `</span>`
            }
            html += `</div>`
          })
          return html
        },
      },
      legend: {
        data: ['样本色谱', '样本峰', '标准品曲线', '标准品峰'],
        bottom: 0,
        textStyle: { color: 'rgba(255,255,255,0.8)' },
      },
      grid: { left: '3%', right: '4%', bottom: '12%', top: '10%', containLabel: true },
      xAxis: {
        type: 'value',
        name: '保留时间 (min)',
        nameTextStyle: { color: 'rgba(255,255,255,0.7)' },
        axisLabel: { color: 'rgba(255,255,255,0.65)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
        min: 0,
      },
      yAxis: {
        type: 'value',
        name: '响应值',
        nameTextStyle: { color: 'rgba(255,255,255,0.7)' },
        axisLabel: { color: 'rgba(255,255,255,0.65)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      },
      dataZoom: [
        { type: 'inside', xAxisIndex: 0 },
        { type: 'slider', xAxisIndex: 0, bottom: 36, height: 18, borderColor: 'transparent' },
      ],
      series,
    },
    true
    )
  } catch (error) {
    console.error('绘制色谱图失败:', error)
  }
}

function findIntensity(rt: number): number {
  if (!chromatogram.value) return 0
  const time = chromatogram.value.time
  const intensity = chromatogram.value.intensity
  let closest = 0
  let minDiff = Infinity
  for (let i = 0; i < time.length; i++) {
    const diff = Math.abs(time[i] - rt)
    if (diff < minDiff) {
      minDiff = diff
      closest = intensity[i]
    }
  }
  return closest
}

function buildReferenceCurve(
  time: number[],
  refPeaks: DetectionResultItem['referencePeaks'],
  scaleMax: number
): number[][] {
  if (!refPeaks.length) return []
  const totalRatio = refPeaks.reduce((sum, p) => sum + (p.areaRatio || 0.2), 0) || refPeaks.length
  return time.map((t) => {
    let y = 0
    refPeaks.forEach((p) => {
      const rt = p.retentionTime
      const sigma = (p.width || 0.08) / 2.355 || 0.05
      const ratio = p.areaRatio || 0.2
      const amp = (ratio / totalRatio) * scaleMax * 0.95
      y += amp * Math.exp(-0.5 * Math.pow((t - rt) / sigma, 2))
    })
    return [t, y]
  })
}

function findReferenceIntensity(curve: number[][], rt: number): number {
  let closest = 0
  let minDiff = Infinity
  for (const [t, y] of curve) {
    const diff = Math.abs(t - rt)
    if (diff < minDiff) {
      minDiff = diff
      closest = y
    }
  }
  return closest
}

async function downloadReportFile(format: 'pdf' | 'excel') {
  if (!sampleId.value) return
  try {
    const res = await downloadReport(sampleId.value, format)
    const blob = new Blob([res.data])
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${sampleId.value}.${format === 'pdf' ? 'pdf' : 'xlsx'}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('报告下载成功')
  } catch (error) {
    ElMessage.error('报告下载失败')
  }
}

watch(
  () => selectedDrug.value,
  () => renderChart(),
  { deep: true }
)

onBeforeUnmount(() => {
  if (resizeObserver && chartRef.value) {
    resizeObserver.unobserve(chartRef.value)
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped lang="scss">
.step-card,
.config-card {
  margin-bottom: 20px;

  :deep(.glass-card__content) {
    padding: 18px 20px;
  }
}

/* 步骤条：当前步骤带流动光效 */
.step-card {
  :deep(.el-step__head.is-process) {
    .el-step__icon {
      background: rgba(64, 158, 255, 0.12);
      border-color: #409eff;
      color: #66b1ff;
      box-shadow: 0 0 12px rgba(64, 158, 255, 0.25);
    }
  }

  :deep(.el-step__title.is-process) {
    color: #66b1ff;
    font-weight: 600;
  }

  :deep(.el-step__line) {
    background: rgba(255, 255, 255, 0.08);
  }

  :deep(.el-step__line-inner) {
    border-radius: 2px;
    background: linear-gradient(
      90deg,
      rgba(64, 158, 255, 0.25),
      rgba(102, 177, 255, 0.8),
      rgba(64, 158, 255, 0.25)
    );
    background-size: 200% 100%;
    animation: step-flow 1.8s linear infinite;
  }
}

@keyframes step-flow {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.config-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.config-toggle-icon {
  transition: transform 0.3s;
  color: rgba(255, 255, 255, 0.65);
}

.config-toggle-icon.is-expanded {
  transform: rotate(180deg);
}

.config-form {
  padding-top: 8px;
}

.main-row {
  align-items: stretch;
}

.upload-card,
.result-card,
.chart-card {
  margin-bottom: 20px;

  :deep(.glass-card__content) {
    padding: 20px;
  }
}

.result-card {
  overflow-x: auto;
}

.card-header-title {
  font-weight: 600;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.92);
}

.upload-area {
  margin-bottom: 20px;
}

:deep(.el-upload-dragger) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px dashed rgba(255, 255, 255, 0.25);
  border-radius: 12px;
}

:deep(.el-upload-dragger:hover) {
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(64, 158, 255, 0.55);
}

:deep(.el-upload__text) {
  color: rgba(255, 255, 255, 0.78);

  em {
    color: #409eff;
  }
}

:deep(.el-upload__tip) {
  color: rgba(255, 255, 255, 0.5);
}

.sample-form {
  margin-bottom: 20px;
}

.result-summary {
  margin-bottom: 20px;
}

.result-actions {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  margin-bottom: 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex: 1;
}

.result-table-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.filter-tip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  white-space: nowrap;

  .tip-icon {
    cursor: help;
    color: rgba(64, 158, 255, 0.8);
  }
}

/* 修复 stripe 背景覆盖 current-row 高亮 */
:deep(.el-table__body tr.current-row > td.el-table__cell) {
  background-color: rgba(64, 158, 255, 0.22) !important;
  color: rgba(255, 255, 255, 0.95) !important;
}

:deep(.el-table__body tr.current-row > td.el-table__cell .cell) {
  color: rgba(255, 255, 255, 0.95) !important;
}

/* 修复检测结果表格状态/操作列文字堆叠 */
.detection-result-table {
  min-width: 820px;

  :deep(.status-tag) {
    white-space: nowrap;
  }

  :deep(.train-button) {
    white-space: nowrap;
  }

  :deep(.el-table__cell .cell) {
    line-height: 1.4;
  }
}

.chart-card {
  margin-top: 20px;
}

.chart-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chart-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}

.chart-container {
  width: 100%;
  height: 460px;
}

.chart-empty {
  margin-top: -460px;
  height: 460px;
  position: relative;
  z-index: 1;
}

.detect-tabs {
  :deep(.el-tabs__header) {
    background: rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 0;
  }

  :deep(.el-tabs__item) {
    color: rgba(255, 255, 255, 0.65);
    font-weight: 500;
  }

  :deep(.el-tabs__item.is-active) {
    color: #66b1ff;
    background: rgba(64, 158, 255, 0.1);
  }

  :deep(.el-tabs__content) {
    padding: 20px 0 0;
  }
}

.cascade-form {
  .el-form-item {
    margin-bottom: 14px;
  }

  :deep(.el-input-number) {
    width: 100%;
  }

  :deep(.el-collapse) {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.03);
  }

  :deep(.el-collapse-item__header) {
    background: rgba(255, 255, 255, 0.04);
    color: rgba(255, 255, 255, 0.92);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0 16px;
    font-weight: 500;
  }

  :deep(.el-collapse-item__wrap) {
    background: transparent;
    border-bottom: none;
  }

  :deep(.el-collapse-item__content) {
    background: transparent;
    color: rgba(255, 255, 255, 0.86);
    padding: 16px;
  }

  :deep(.el-collapse-item__arrow) {
    color: rgba(255, 255, 255, 0.7);
  }
}

.area-section-title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  margin: 8px 0 12px;
}

.cascade-result {
  .step-section {
    margin-bottom: 24px;
    padding: 16px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .step-1 {
    border-left: 4px solid #409eff;
  }

  .step-2 {
    border-left: 4px solid #67c23a;
  }

  .step-3 {
    border-left: 4px solid #f56c6c;
  }

  .step-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }

  .step-title {
    font-size: 15px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.92);
  }

  .step-count {
    margin-left: auto;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
  }

  .step-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 12px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.7);
  }
}
</style>
