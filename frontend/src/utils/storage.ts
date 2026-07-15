/**
 * 本地存储工具函数。
 * 对 localStorage 进行简单封装，支持 JSON 序列化。
 */

export function setItem(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.error('localStorage setItem failed:', error)
  }
}

export function getItem<T>(key: string): T | null {
  try {
    const item = localStorage.getItem(key)
    return item ? (JSON.parse(item) as T) : null
  } catch (error) {
    console.error('localStorage getItem failed:', error)
    return null
  }
}

export function removeItem(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch (error) {
    console.error('localStorage removeItem failed:', error)
  }
}
