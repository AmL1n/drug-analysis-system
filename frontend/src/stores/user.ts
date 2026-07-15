import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getItem, removeItem, setItem } from '@/utils/storage'

const TOKEN_KEY = 'drug_check_token'
const USER_KEY = 'drug_check_user'

export interface UserInfo {
  id: number
  username: string
  realName: string
  email?: string
  operatorNo?: string
  roles: string[]
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(getItem(TOKEN_KEY))
  const userInfo = ref<UserInfo | null>(getItem(USER_KEY))

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken: string) {
    token.value = newToken
    setItem(TOKEN_KEY, newToken)
  }

  function setUserInfo(info: UserInfo) {
    userInfo.value = info
    setItem(USER_KEY, info)
  }

  function logout() {
    token.value = null
    userInfo.value = null
    removeItem(TOKEN_KEY)
    removeItem(USER_KEY)
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    setToken,
    setUserInfo,
    logout,
  }
})
