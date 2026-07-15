import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: '仪表盘', icon: 'Odometer' },
        },
        {
          path: 'detection',
          name: 'Detection',
          component: () => import('@/views/DetectionView.vue'),
          meta: { title: '检测分析', icon: 'Search' },
        },
        {
          path: 'library',
          name: 'Library',
          component: () => import('@/views/LibraryView.vue'),
          meta: { title: '数据库管理', icon: 'Collection' },
        },
        {
          path: 'report',
          name: 'Report',
          component: () => import('@/views/ReportView.vue'),
          meta: { title: '检测报告', icon: 'Document' },
        },
        {
          path: 'log',
          name: 'Log',
          component: () => import('@/views/LogView.vue'),
          meta: { title: '操作日志', icon: 'Tickets' },
        },
        {
          path: 'config',
          name: 'Config',
          component: () => import('@/views/ConfigView.vue'),
          meta: { title: '系统配置', icon: 'Setting' },
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('@/views/ProfileView.vue'),
          meta: { title: '个人中心', icon: 'User' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { public: true },
    },
  ],
})

// 路由守卫：未登录用户重定向到登录页
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  if (!to.meta.public && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
