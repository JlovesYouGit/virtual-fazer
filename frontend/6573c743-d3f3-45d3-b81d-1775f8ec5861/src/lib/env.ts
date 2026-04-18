// Environment variables configuration
export const env = {
  // API Configuration
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:3000',
  APP_URL: import.meta.env.VITE_APP_URL || 'http://localhost:5173',
  
  // Google OAuth
  GOOGLE_CLIENT_ID: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
  
  // Feature Flags
  ENABLE_ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  ENABLE_NEURAL_FEATURES: import.meta.env.VITE_ENABLE_NEURAL_FEATURES === 'true',
  ENABLE_REALTIME_CHAT: import.meta.env.VITE_ENABLE_REALTIME_CHAT === 'true',
  
  // Development Settings
  DEBUG_MODE: import.meta.env.VITE_DEBUG_MODE === 'true',
  LOG_LEVEL: import.meta.env.VITE_LOG_LEVEL || 'info',
  
  // App Version
  APP_VERSION: (globalThis as any).__APP_VERSION__ || '1.0.0'
};

// Validation helper
export function validateEnv() {
  const required = ['API_BASE_URL', 'WS_URL', 'APP_URL'];
  const missing = required.filter(key => !env[key as keyof typeof env]);
  
  if (missing.length > 0) {
    console.warn('Missing environment variables:', missing);
  }
  
  if (env.DEBUG_MODE) {
    console.log('Environment variables:', env);
  }
  
  return missing.length === 0;
}
