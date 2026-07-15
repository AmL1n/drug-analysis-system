/**
 * 将后端返回的 UTC ISO 字符串格式化为中国标准时间字符串。
 *
 * 后端存储的是 datetime.utcnow() 生成的 naive UTC 时间，ISO 字符串不带时区标记。
 * 这里统一按 UTC 解析，再转换为 Asia/Shanghai（UTC+8）展示。
 */
export function formatChinaTime(isoTime: string | number | Date | undefined | null): string {
  if (!isoTime || isoTime === '-') {
    return '-'
  }

  let isoStr: string
  if (isoTime instanceof Date) {
    isoStr = isoTime.toISOString()
  } else {
    isoStr = String(isoTime).trim()
  }

  if (!isoStr) {
    return '-'
  }

  // 后端返回的 naive UTC 时间没有 Z 或 +00:00，手动补 Z 按 UTC 解析
  if (!isoStr.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(isoStr)) {
    isoStr += 'Z'
  }

  const date = new Date(isoStr)
  if (Number.isNaN(date.getTime())) {
    return String(isoTime)
  }

  return date.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}
