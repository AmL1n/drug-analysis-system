<template>
  <div class="page-container">
    <h2 class="page-title">个人中心</h2>

    <el-row :gutter="20">
      <el-col :xs="24" :md="8">
        <GlassCard class="profile-card" :tilt="false" :halo="false" :glare="false">
          <div class="avatar-section">
            <div class="avatar">
              <el-icon size="48" color="rgba(255,255,255,0.9)"><UserFilled /></el-icon>
            </div>
            <h3 class="profile-name">{{ userStore.userInfo?.realName || userStore.userInfo?.username }}</h3>
            <p class="profile-role">{{ roleText }}</p>
          </div>
        </GlassCard>
      </el-col>

      <el-col :xs="24" :md="16">
        <GlassCard :tilt="false" :halo="false" :glare="false">
          <template #header>
            <span class="card-header-title">账号详情</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">{{ userStore.userInfo?.username || '-' }}</el-descriptions-item>
            <el-descriptions-item label="真实姓名">{{ userStore.userInfo?.realName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="工号">
              <el-tag v-if="userStore.userInfo?.operatorNo" size="small" type="info">{{ userStore.userInfo.operatorNo }}</el-tag>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ userStore.userInfo?.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ roleText }}</el-descriptions-item>
            <el-descriptions-item label="最后登录时间">{{ lastLoginText }}</el-descriptions-item>
          </el-descriptions>

          <div class="profile-actions">
            <GlassButton primary disabled>修改资料</GlassButton>
            <GlassButton disabled>修改密码</GlassButton>
          </div>
        </GlassCard>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getCurrentUser } from '@/api/auth'
import { formatChinaTime } from '@/utils/formatTime'
import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'

const userStore = useUserStore()
const lastLoginAt = ref<string | null>(null)

const roleText = computed(() => {
  const roles = userStore.userInfo?.roles
  if (!roles || roles.length === 0) return '未知角色'
  return roles.join(' / ')
})

const lastLoginText = computed(() => {
  const raw = lastLoginAt.value || (userStore.userInfo as any)?.lastLoginAt
  return formatChinaTime(raw)
})

async function loadProfile() {
  try {
    const res = await getCurrentUser()
    userStore.setUserInfo(res.data)
    lastLoginAt.value = (res.data as any).lastLoginAt || null
  } catch {
    ElMessage.error('获取个人信息失败')
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped lang="scss">
.profile-card {
  margin-bottom: 20px;

  :deep(.glass-card__content) {
    padding: 28px 24px;
  }
}

.card-header-title {
  font-weight: 600;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.92);
}

.avatar-section {
  text-align: center;

  .avatar {
    width: 96px;
    height: 96px;
    margin: 0 auto 16px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(64, 158, 255, 0.8), rgba(120, 80, 255, 0.8));
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 24px rgba(64, 158, 255, 0.25);
  }

  .profile-name {
    font-size: 20px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.95);
    margin-bottom: 6px;
  }

  .profile-role {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.55);
    margin: 0;
  }
}

:deep(.el-descriptions__label) {
  width: 120px;
}

.profile-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}
</style>
