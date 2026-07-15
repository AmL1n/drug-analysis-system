/// <reference types="vite/client" />

/**
 * Vite 环境变量类型声明。
 */
interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
  readonly url: string
}

/**
 * 声明静态资源模块，避免 TypeScript 报错。
 */
declare module '*.svg' {
  const src: string
  export default src
}

declare module '*.png' {
  const src: string
  export default src
}

declare module '*.jpg' {
  const src: string
  export default src
}

declare module '*.css' {}
declare module '*.scss' {}
