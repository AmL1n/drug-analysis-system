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

    <el-row :gutter="20" class="main-row">
      <el-col :xs="24" :md="8">
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

      <el-col :xs="24" :md="16">
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

            <h3 class="section-title">Top 候选药物</h3>
            <el-table
              v-if="detectionResults.length > 0"
              :data="detectionResults"
              border
              stripe
              highlight-current-row
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
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.isDetected ? 'danger' : 'info'" size="small">
                    {{ row.isDetected ? '检出' : '未检出' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>

            <el-result
              v-if="detectionResults.length === 0"
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
        </GlassCard>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { ArrowDown, DataAnalysis, Document, UploadFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { uploadFile } from '@/api/file'
import { createSample } from '@/api/sample'
import {
  detectSample,
  downloadReport,
  getDetectionResults,
  type DetectionResultItem,
} from '@/api/detection'
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
const detectionResults = ref<DetectionResultItem[]>([])
const selectedDrug = ref<DetectionResultItem | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

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

    if (sampleId.value) {
      const [chromRes, resultsRes] = await Promise.all([
        getSampleChromatogram(sampleId.value),
        getDetectionResults(sampleId.value),
      ])
      chromatogram.value = chromRes.data
      detectionResults.value = resultsRes.data
      if (detectionResults.value.length > 0) {
        selectedDrug.value = detectionResults.value[0]
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

function renderChart() {
  if (!chartRef.value || !chromatogram.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, 'dark')
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
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
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
</style>
