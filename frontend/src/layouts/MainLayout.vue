<template>
  <el-container class="main-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28"><FirstAidKit /></el-icon>
        <span class="title">药物检测系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="transparent"
        text-color="rgba(255,255,255,0.72)"
        active-text-color="#66b1ff"
      >
        <el-menu-item
          v-for="route in menuRoutes"
          :key="route.path"
          :index="route.path"
          :route="{ path: route.path }"
        >
          <el-icon>
            <component :is="route.meta?.icon" />
          </el-icon>
          <span>{{ route.meta?.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">HPLC-DAD 药物非法添加筛查系统</div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              {{ userStore.userInfo?.realName || userStore.userInfo?.username || '未知用户' }}
              <el-tag v-if="userStore.userInfo?.operatorNo" size="small" type="info" class="operator-tag">
                {{ userStore.userInfo.operatorNo }}
              </el-tag>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  工号：{{ userStore.userInfo?.operatorNo || '-' }}
                </el-dropdown-item>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, FirstAidKit } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import routerConfig from '@/router'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

// 从路由配置中提取需要显示的菜单
const menuRoutes = computed(() => {
  const mainRoute = routerConfig.getRoutes().find((r) => r.path === '/')
  return (mainRoute?.children || []).filter((r) => r.meta?.title)
})

function handleCommand(command: string) {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(() => {
      userStore.logout()
      router.push('/login')
    })
  } else if (command === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
  background: transparent;
}

.sidebar {
  position: relative;
  background: rgba(10, 12, 17, 0.55);
  backdrop-filter: blur(20px) saturate(130%);
  -webkit-backdrop-filter: blur(20px) saturate(130%);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 6px 0 22px rgba(0, 0, 0, 0.24);
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);

  .title {
    margin-left: 10px;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.04em;
  }
}

.sidebar-menu {
  border-right: none;
  background: transparent !important;

  :deep(.el-menu-item) {
    border-radius: 10px;
    margin: 6px 12px;
    transition: all 0.2s ease;

    &:hover {
      background: rgba(255, 255, 255, 0.08) !important;
    }

    &.is-active {
      background: linear-gradient(90deg, rgba(64, 158, 255, 0.2), rgba(64, 158, 255, 0.05)) !important;
      box-shadow: inset 3px 0 0 #409eff;
    }
  }
}

.header {
  position: relative;
  background: rgba(10, 12, 17, 0.48);
  backdrop-filter: blur(18px) saturate(120%);
  -webkit-backdrop-filter: blur(18px) saturate(120%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 3px 16px rgba(0, 0, 0, 0.20);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  font-size: 16px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.92);
  letter-spacing: 0.02em;
}

.header-right {
  cursor: pointer;

  .user-info {
    display: flex;
    align-items: center;
    color: rgba(255, 255, 255, 0.9);
    padding: 6px 10px;
    border-radius: 10px;
    transition: background 0.2s ease;

    &:hover {
      background: rgba(255, 255, 255, 0.08);
    }
  }

  .operator-tag {
    margin-left: 8px;
    margin-right: 4px;
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.85);
  }
}

.main-content {
  background: transparent;
  padding: 20px;
  overflow-y: auto;
}
</style>
