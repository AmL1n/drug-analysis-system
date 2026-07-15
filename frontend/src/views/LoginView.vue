<template>
  <div class="login-page">
    <div class="login-background">
      <div class="shape shape-1" />
      <div class="shape shape-2" />
      <div class="shape shape-3" />
    </div>

    <GlassCard class="login-card" :tilt="true" halo-color="rgba(64, 158, 255, 0.35)">
      <div class="login-header">
        <div class="logo">
          <el-icon size="40" color="#fff"><FirstAidKit /></el-icon>
        </div>
        <h1 class="login-title">药物检测系统</h1>
        <p class="login-subtitle">HPLC-DAD 非法添加药物筛查平台</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        size="large"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            :prefix-icon="User"
            clearable
            aria-label="用户名"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            show-password
            :prefix-icon="Lock"
            aria-label="密码"
          />
        </el-form-item>
        <el-form-item>
          <GlassButton
            primary
            large
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登 录
          </GlassButton>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>演示账号：admin / admin123 或 operator / admin123</p>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { FirstAidKit, Lock, User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { login } from '@/api/auth'
import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: 'admin',
  password: 'admin123',
})

const rules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
})

async function handleLogin() {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login({
      username: loginForm.username,
      password: loginForm.password,
    })
    const { token, user } = res.data
    userStore.setToken(token)
    userStore.setUserInfo(user)
    ElMessage.success('登录成功')
    await router.push('/')
  } catch (error) {
    console.error('登录异常:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  overflow: hidden;
  background: radial-gradient(at 0% 0%, hsla(253, 40%, 24%, 0.85) 0, transparent 50%),
    radial-gradient(at 100% 0%, hsla(190, 45%, 26%, 0.8) 0, transparent 50%),
    radial-gradient(at 100% 100%, hsla(280, 42%, 28%, 0.8) 0, transparent 50%),
    radial-gradient(at 0% 100%, hsla(340, 42%, 28%, 0.8) 0, transparent 50%),
    #0b0d12;
  background-size: 200% 200%;
  animation: login-mesh 24s ease infinite;
}

@keyframes login-mesh {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.login-background {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;

  .shape {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.35;
    animation: float 12s ease-in-out infinite;
  }

  .shape-1 {
    width: 360px;
    height: 360px;
    background: rgba(64, 158, 255, 0.4);
    top: -100px;
    left: -100px;
    animation-delay: 0s;
  }

  .shape-2 {
    width: 460px;
    height: 460px;
    background: rgba(160, 120, 255, 0.32);
    bottom: -140px;
    right: -140px;
    animation-delay: -4s;
  }

  .shape-3 {
    width: 300px;
    height: 300px;
    background: rgba(80, 220, 200, 0.28);
    top: 45%;
    left: 60%;
    animation-delay: -7s;
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-28px) scale(1.06);
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 440px;
  padding: 18px;

  :deep(.glass-card__content) {
    padding: 28px 32px 36px;
  }
}

.login-header {
  text-align: center;
  margin-bottom: 28px;

  .logo {
    width: 72px;
    height: 72px;
    margin: 0 auto 16px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(64, 158, 255, 0.9) 0%, rgba(120, 80, 255, 0.9) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 28px rgba(64, 158, 255, 0.45);
  }

  .login-title {
    font-size: 28px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.96);
    margin: 0 0 8px;
  }

  .login-subtitle {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    margin: 0;
  }
}

.login-form {
  .el-input {
    --el-input-border-radius: 10px;
  }

  .login-button {
    width: 100%;
    margin-top: 8px;
  }
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;

  p {
    margin: 0;
  }
}
</style>
