<template>
  <div class="page-container">
    <h2 class="page-title">系统配置</h2>
    <GlassCard class="config-card" :tilt="false">
      <el-form label-width="180px" style="max-width: 600px">
        <el-form-item label="RRT 容差">
          <el-input-number :min="0" :max="1" :step="0.01" :model-value="0.02" />
        </el-form-item>
        <el-form-item label="UV 距离阈值">
          <el-input-number :min="0" :max="1" :step="0.01" :model-value="0.15" />
        </el-form-item>
        <el-form-item label="峰面积比概率阈值">
          <el-input-number :min="0" :max="1" :step="0.01" :model-value="0.05" />
        </el-form-item>
        <el-form-item label="默认 Top-N">
          <el-input-number :min="1" :max="50" :model-value="10" />
        </el-form-item>
        <el-form-item>
          <GlassButton primary disabled>保存配置</GlassButton>
        </el-form-item>
      </el-form>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'
</script>

<style scoped lang="scss">
.config-card {
  :deep(.glass-card__content) {
    padding: 28px 24px;
  }
}
</style>
