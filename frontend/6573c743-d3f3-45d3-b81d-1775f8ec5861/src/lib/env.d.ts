interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_APP_URL: string
  readonly VITE_GOOGLE_CLIENT_ID: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_ENABLE_NEURAL_FEATURES: string
  readonly VITE_ENABLE_REALTIME_CHAT: string
  readonly VITE_DEBUG_MODE: string
  readonly VITE_LOG_LEVEL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
