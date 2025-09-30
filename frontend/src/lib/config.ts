/**
 * Environment Configuration for Vietnamese STT Frontend
 * 
 * Loads configuration from Vite environment variables and provides
 * type-safe access to backend connection settings.
 * 
 * Environment Variables:
 * - VITE_API_HOST: Backend API host (default: 127.0.0.1)
 * - VITE_API_PORT: Backend API port (default: 8000)
 * - VITE_WS_PATH: WebSocket endpoint path (default: /v1/ws)
 * - VITE_WS_URL: Full WebSocket URL (overrides constructed URL)
 */

interface AppConfig {
  backend: {
    host: string
    port: number
    wsPath: string
    wsUrl: string
    httpUrl: string
  }
  development: boolean
}

/**
 * Load configuration from environment variables
 */
function loadConfig(): AppConfig {
  const host = import.meta.env.VITE_API_HOST || '127.0.0.1'
  const port = parseInt(import.meta.env.VITE_API_PORT || '8000', 10)
  const wsPath = import.meta.env.VITE_WS_PATH || '/v1/ws'
  
  // Use explicit WS URL if provided, otherwise construct from parts
  const wsUrl = import.meta.env.VITE_WS_URL || `ws://${host}:${port}${wsPath}`
  const httpUrl = `http://${host}:${port}`
  
  return {
    backend: {
      host,
      port,
      wsPath,
      wsUrl,
      httpUrl
    },
    development: import.meta.env.DEV
  }
}

/**
 * Application configuration singleton
 */
export const config = loadConfig()

/**
 * Development helper to log configuration
 */
if (config.development) {
  console.log('🔧 Frontend Configuration:', {
    backend: config.backend,
    environment: config.development ? 'development' : 'production'
  })
}