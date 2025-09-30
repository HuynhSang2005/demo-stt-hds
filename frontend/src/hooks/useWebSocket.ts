/**
 * useWebSocket Hook
 * 
 * Custom React hook for WebSocket connections with Vietnamese STT optimization
 * Features:
 * - Auto-reconnection with exponential backoff
 * - Binary audio data transmission (ArrayBuffer)
 * - Vietnamese STT protocol message handling
 * - Connection state management
 * - Error recovery and retry mechanisms
 * - Real-time transcript and warning processing
 * 
 * @example
 * ```typescript
 * const {
 *   connectionStatus,
 *   sendAudioChunk,
 *   lastTranscript,
 *   isConnected,
 *   connect,
 *   disconnect
 * } = useWebSocket('ws://localhost:8000/v1/ws', {
 *   onTranscript: (result) => {
 *     console.log('Vietnamese STT Result:', result.text)
 *     if (result.warning) {
 *       showWarning(result.label)
 *     }
 *   },
 *   autoReconnect: true,
 *   maxReconnectAttempts: 5
 * })
 * ```
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import type { 
  UseWebSocketReturn,
  WebSocketEventHandlers,
  WebSocketConfig,
  WebSocketMessage,
  ConnectionStatus,
  TranscriptResultMessage,
  ErrorMessage,
  ConnectionStatusMessage
} from '@/types/websocket'
// TranscriptResult handled via callback pattern
import type { WebSocketError } from '@/types/error'

/**
 * WebSocket hook configuration options
 */
export interface UseWebSocketOptions extends Partial<WebSocketEventHandlers> {
  /** Enable automatic reconnection on connection loss */
  autoReconnect?: boolean
  /** Maximum number of reconnection attempts (default: 5) */
  maxReconnectAttempts?: number
  /** Initial reconnection delay in milliseconds (default: 1000) */
  reconnectDelay?: number
  /** Maximum reconnection delay in milliseconds (default: 30000) */
  maxReconnectDelay?: number
  /** Whether to reconnect with exponential backoff (default: true) */
  exponentialBackoff?: boolean
  /** Connection timeout in milliseconds (default: 10000) */
  connectionTimeout?: number
  /** Enable debug logging for development */
  enableDebug?: boolean
  /** Custom WebSocket protocols */
  protocols?: string[]
  /** Additional WebSocket configuration */
  config?: Partial<WebSocketConfig>
}

/**
 * Internal connection state tracking
 */
interface ConnectionState {
  socket: WebSocket | null
  reconnectAttempts: number
  reconnectTimer: number | null
  connectionTimer: number | null
  lastConnectedAt: number | null
  lastDisconnectedAt: number | null
}

/**
 * Default Vietnamese STT WebSocket configuration
 */
const DEFAULT_CONFIG: Required<Omit<UseWebSocketOptions, keyof WebSocketEventHandlers | 'config' | 'protocols'>> = {
  autoReconnect: true,
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,
  maxReconnectDelay: 30000,
  exponentialBackoff: true,
  connectionTimeout: 10000,
  enableDebug: false,
}

/**
 * Vietnamese STT WebSocket connection hook
 */
export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    onOpen,
    onClose,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onError: _onError,
    onMessage,
    onTranscriptResult,
    onConnectionStatusChange,
    autoReconnect = DEFAULT_CONFIG.autoReconnect,
    maxReconnectAttempts = DEFAULT_CONFIG.maxReconnectAttempts,
    reconnectDelay = DEFAULT_CONFIG.reconnectDelay,
    maxReconnectDelay = DEFAULT_CONFIG.maxReconnectDelay,
    exponentialBackoff = DEFAULT_CONFIG.exponentialBackoff,
    connectionTimeout = DEFAULT_CONFIG.connectionTimeout,
    enableDebug = DEFAULT_CONFIG.enableDebug,
    protocols,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    config: _customConfig = {} // Reserved for future configuration options
  } = options

  // State management
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const [lastError, setLastError] = useState<ErrorMessage | null>(null)
  // State for managing transcript results via callback

  // Connection state ref (mutable without causing re-renders)
  const connectionStateRef = useRef<ConnectionState>({
    socket: null,
    reconnectAttempts: 0,
    reconnectTimer: null,
    connectionTimer: null,
    lastConnectedAt: null,
    lastDisconnectedAt: null,
  })

  // Ref to store connect function to avoid circular dependencies
  const connectRef = useRef<(() => void) | null>(null)
  
  // React StrictMode compatibility
  const hasInitialized = useRef(false)
  const shouldConnect = useRef(true) // Flag to control connection attempts

  // WebSocket configuration handled inline

  /**
   * Debug logging helper
   */
  const debugLog = useCallback((message: string, data?: Record<string, unknown>) => {
    if (enableDebug) {
      console.log(`[useWebSocket] ${message}`, data || '')
    }
  }, [enableDebug])

  /**
   * Create WebSocket error
   */
  const createWebSocketError = useCallback((
    code: string,
    message: string,
    details?: Record<string, unknown>
  ): WebSocketError => ({
    id: `ws-${Date.now()}`,
    code: code as WebSocketError['code'],
    category: 'WEBSOCKET_CONNECTION' as const,
    severity: 'high' as const,
    message,
    timestamp: Date.now(),
    details,
  }), [])

  /**
   * Update connection status and notify listeners
   */
  const updateConnectionStatus = useCallback((
    status: ConnectionStatus,
    reason?: string
  ) => {
    debugLog(`Connection status: ${status}`, { reason })
    setConnectionStatus(status)
    onConnectionStatusChange?.(status, reason)
  }, [debugLog, onConnectionStatusChange])

  /**
   * Handle WebSocket message parsing and routing
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      debugLog('Received message', { type: typeof event.data, size: event.data.length })

      // Handle binary data (should not happen for Vietnamese STT responses)
      if (event.data instanceof ArrayBuffer) {
        debugLog('Received binary data - unexpected for Vietnamese STT')
        return
      }

      // Parse JSON message
      let message: WebSocketMessage
      try {
        message = JSON.parse(event.data)
      } catch (parseError) {
        debugLog('Failed to parse WebSocket message as JSON', {
          error: parseError,
          data: event.data
        })
        return
      }

      debugLog('Parsed message', { type: message.type, message })

      // Route message based on type
      switch (message.type) {
        case 'transcript_result': {
          const transcriptMsg = message as TranscriptResultMessage
          try {
            // Transcript handled via callback - no internal state needed
            onTranscriptResult?.(transcriptMsg.data)
            debugLog('Transcript result processed successfully', {
              text: transcriptMsg.data.text?.substring(0, 30) + '...',
              label: transcriptMsg.data.label,
              warning: transcriptMsg.data.warning
            })
          } catch (callbackError) {
            debugLog('Error in transcript result callback', {
              error: callbackError,
              transcriptData: transcriptMsg.data
            })
            throw callbackError // Re-throw to be caught by outer error handler
          }
          break
        }

        case 'error': {
          const errorMsg = message as ErrorMessage
          setLastError(errorMsg)
          // Error message already in proper format from server
          debugLog('Error handled internally, check lastError state')
          debugLog('Server error', errorMsg)
          break
        }

        case 'connection_status': {
          const statusMsg = message as ConnectionStatusMessage
          updateConnectionStatus(statusMsg.data.status, statusMsg.data.reason)
          debugLog('Connection status update', statusMsg)
          break
        }

        default:
          debugLog('Unknown message type', { type: (message as Record<string, unknown>).type })
          onMessage?.(message)
          break
      }
    } catch (error) {
      debugLog('Error handling WebSocket message', { error, data: event.data })
      const wsError = createWebSocketError(
        'MESSAGE_PROCESSING_FAILED',
        'Failed to process WebSocket message',
        { error, data: event.data }
      )
      // Store error internally, onError expects Event type
      setLastError({
        type: 'error',
        timestamp: Date.now(),
        data: {
          code: wsError.code,
          message: wsError.message,
          details: wsError.details
        }
      })
    }
  }, [debugLog, onTranscriptResult, onMessage, createWebSocketError, updateConnectionStatus])

  /**
   * Calculate reconnect delay with exponential backoff
   */
  const calculateReconnectDelay = useCallback((attempt: number): number => {
    if (!exponentialBackoff) {
      return reconnectDelay
    }

    const delay = Math.min(
      reconnectDelay * Math.pow(2, attempt),
      maxReconnectDelay
    )
    
    // Add jitter to prevent thundering herd
    const jitter = delay * 0.1 * Math.random()
    return Math.floor(delay + jitter)
  }, [exponentialBackoff, reconnectDelay, maxReconnectDelay])

  /**
   * Attempt to reconnect with backoff strategy
   */
  const attemptReconnect = useCallback(() => {
    const state = connectionStateRef.current

    if (!autoReconnect || state.reconnectAttempts >= maxReconnectAttempts) {
      debugLog('Reconnection disabled or max attempts reached', {
        autoReconnect,
        attempts: state.reconnectAttempts,
        maxAttempts: maxReconnectAttempts
      })
      updateConnectionStatus('failed', 'Maximum reconnection attempts exceeded')
      return
    }

    state.reconnectAttempts++
    const delay = calculateReconnectDelay(state.reconnectAttempts - 1)
    
    debugLog(`Reconnecting in ${delay}ms (attempt ${state.reconnectAttempts}/${maxReconnectAttempts})`)
    updateConnectionStatus('reconnecting', `Reconnecting in ${Math.ceil(delay / 1000)}s`)

    state.reconnectTimer = setTimeout(() => {
      debugLog(`Reconnection attempt ${state.reconnectAttempts}`)
      connectRef.current?.()
    }, delay) as ReturnType<typeof setTimeout>
  }, [
    autoReconnect,
    maxReconnectAttempts,
    debugLog,
    updateConnectionStatus,
    calculateReconnectDelay
  ])

  /**
   * Clear reconnection timer
   */
  const clearReconnectTimer = useCallback(() => {
    const state = connectionStateRef.current
    if (state.reconnectTimer) {
      clearTimeout(state.reconnectTimer)
      state.reconnectTimer = null
    }
  }, [])

  /**
   * Clear connection timeout timer
   */
  const clearConnectionTimer = useCallback(() => {
    const state = connectionStateRef.current
    if (state.connectionTimer) {
      clearTimeout(state.connectionTimer)
      state.connectionTimer = null
    }
  }, [])

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    // Prevent connection if component is being cleaned up
    if (!shouldConnect.current) {
      debugLog('Skipping connection - component cleaning up')
      return
    }
    
    debugLog('Attempting to connect', { url })
    
    const state = connectionStateRef.current

    // Clear existing connection
    if (state.socket) {
      state.socket.close()
      state.socket = null
    }

    clearReconnectTimer()
    clearConnectionTimer()

    try {
      // Create WebSocket connection
      const socket = protocols && protocols.length > 0 
        ? new WebSocket(url, protocols)
        : new WebSocket(url)

      // Configure binary type for audio data
      socket.binaryType = 'arraybuffer' // Set directly for audio data

      state.socket = socket
      updateConnectionStatus('connecting')

      // Setup connection timeout
      state.connectionTimer = setTimeout(() => {
        debugLog('Connection timeout')
        socket.close()
        updateConnectionStatus('failed', 'Connection timeout')
        
        if (autoReconnect) {
          attemptReconnect()
        }
      }, connectionTimeout) as ReturnType<typeof setTimeout>

      // WebSocket event handlers
      socket.onopen = (event) => {
        debugLog('WebSocket connected')
        clearConnectionTimer()
        
        state.reconnectAttempts = 0
        state.lastConnectedAt = Date.now()
        
        // Clear any previous errors when connection succeeds
        setLastError(null)
        
        updateConnectionStatus('connected')
        onOpen?.(event)
      }

      socket.onmessage = handleMessage

      socket.onclose = (event) => {
        debugLog('WebSocket closed', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        })

        clearConnectionTimer()
        state.socket = null
        state.lastDisconnectedAt = Date.now()

        // Determine if reconnection should be attempted
        const shouldReconnect = autoReconnect && 
          event.code !== 1000 && // Normal closure
          event.code !== 1001 && // Going away
          event.code !== 1005    // No status code

        if (shouldReconnect) {
          updateConnectionStatus('disconnected', `Connection lost: ${event.reason || 'Unknown'}`)
          attemptReconnect()
        } else {
          updateConnectionStatus('disconnected', event.reason || 'Connection closed')
        }

        onClose?.(event)
      }

      socket.onerror = (event) => {
        debugLog('WebSocket error', { event })
        clearConnectionTimer()

        const wsError = createWebSocketError(
          'CONNECTION_ERROR',
          'WebSocket connection error occurred',
          { event }
        )
        setLastError({
          type: 'error',
          timestamp: Date.now(),
          data: {
            code: wsError.code,
            message: wsError.message,
            details: wsError.details
          }
        })
        // Store error internally, let user check via lastError state
        debugLog('Connection error handled internally')
      }

    } catch (error) {
      debugLog('Failed to create WebSocket', { error })
      const wsError = createWebSocketError(
        'CONNECTION_FAILED',
        error instanceof Error ? error.message : 'Failed to create WebSocket connection',
        { error }
      )
      setLastError({
        type: 'error',
        timestamp: Date.now(),
        data: {
          code: wsError.code,
          message: wsError.message,
          details: wsError.details
        }
      })
      updateConnectionStatus('failed', wsError.message)
      // Error handled internally via lastError state
    }
  }, [
    url,
    protocols,
    connectionTimeout,
    autoReconnect,
    debugLog,
    updateConnectionStatus,
    clearReconnectTimer,
    clearConnectionTimer,
    attemptReconnect,
    handleMessage,
    createWebSocketError,
    onOpen,
    onClose
  ])

  // Store connect function in ref to avoid circular dependencies
  connectRef.current = connect

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    debugLog('Disconnecting WebSocket')
    
    const state = connectionStateRef.current
    clearReconnectTimer()
    clearConnectionTimer()

    if (state.socket) {
      state.socket.close(1000, 'Client disconnect')
      state.socket = null
    }

    updateConnectionStatus('disconnected', 'Manually disconnected')
  }, [debugLog, clearReconnectTimer, clearConnectionTimer, updateConnectionStatus])

  /**
   * Reconnect WebSocket manually
   */
  const reconnect = useCallback(() => {
    debugLog('Manual reconnect requested')
    connectionStateRef.current.reconnectAttempts = 0
    disconnect()
    setTimeout(connect, 100) // Brief delay before reconnecting
  }, [debugLog, disconnect, connect])

  /**
   * Send audio chunk for Vietnamese STT processing
   */
  const sendAudioChunk = useCallback((
    audioData: ArrayBuffer,
    chunkIndex: number
  ): void => {
    const state = connectionStateRef.current

    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
      debugLog('Cannot send audio chunk - WebSocket not connected', {
        socketState: state.socket?.readyState,
        chunkIndex,
        dataSize: audioData.byteLength
      })
      return
    }

    try {
      // Send binary audio data directly
      // The backend expects raw audio chunks as ArrayBuffer
      state.socket.send(audioData)
      
      debugLog('Sent audio chunk', {
        chunkIndex,
        size: audioData.byteLength
      })
    } catch (error) {
      debugLog('Failed to send audio chunk', {
        error,
        chunkIndex,
        dataSize: audioData.byteLength
      })
      
      const wsError = createWebSocketError(
        'SEND_FAILED',
        'Failed to send audio chunk',
        { error, chunkIndex, dataSize: audioData.byteLength }
      )
      // Store error internally via lastError state
      setLastError({
        type: 'error',
        timestamp: Date.now(),
        data: {
          code: wsError.code,
          message: wsError.message,
          details: wsError.details
        }
      })
    }
  }, [debugLog, createWebSocketError])

  /**
   * Send JSON message
   */
  const sendMessage = useCallback((message: WebSocketMessage): void => {
    const state = connectionStateRef.current

    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
      debugLog('Cannot send message - WebSocket not connected', {
        socketState: state.socket?.readyState,
        messageType: message.type
      })
      return
    }

    try {
      const messageStr = JSON.stringify(message)
      state.socket.send(messageStr)
      
      debugLog('Sent message', {
        type: message.type,
        size: messageStr.length
      })
    } catch (error) {
      debugLog('Failed to send message', {
        error,
        messageType: message.type
      })
      
      const wsError = createWebSocketError(
        'SEND_MESSAGE_FAILED',
        'Failed to send WebSocket message',
        { error, messageType: message.type }
      )
      // Store error internally via lastError state
      setLastError({
        type: 'error',
        timestamp: Date.now(),
        data: {
          code: wsError.code,
          message: wsError.message,
          details: wsError.details
        }
      })
    }
  }, [debugLog, createWebSocketError])

  /**
   * Check if WebSocket is connected
   */
  const isConnected = connectionStatus === 'connected'
  const isConnecting = connectionStatus === 'connecting' || connectionStatus === 'reconnecting'

  /**
   * Auto-connect on mount if autoConnect is enabled
   * Uses a ref to prevent double connections in React StrictMode
   */
  useEffect(() => {
    if (!hasInitialized.current && autoReconnect && shouldConnect.current) { // Re-enable auto-connect
      hasInitialized.current = true
      debugLog('Auto-connecting WebSocket on mount')
      connectRef.current?.()
    }
  }, [autoReconnect, debugLog])

  /**
   * Cleanup on unmount - prevent reconnection attempts
   * Fixed for React StrictMode compatibility
   */
  useEffect(() => {
    return () => {
      debugLog('Cleaning up WebSocket hook - preventing further connections')
      shouldConnect.current = false // Prevent further connection attempts
      // Clean up without causing infinite loops
      if (connectionStateRef.current.socket) {
        connectionStateRef.current.socket.close()
        connectionStateRef.current.socket = null
      }
      if (connectionStateRef.current.reconnectTimer) {
        clearTimeout(connectionStateRef.current.reconnectTimer)
        connectionStateRef.current.reconnectTimer = null
      }
      if (connectionStateRef.current.connectionTimer) {
        clearTimeout(connectionStateRef.current.connectionTimer)
        connectionStateRef.current.connectionTimer = null
      }
      setConnectionStatus('disconnected')
    }
  }, [debugLog]) // Empty dependency array to prevent StrictMode issues

  // Return hook interface
  return {
    connectionStatus,
    sendAudioChunk,
    sendMessage,
    connect,
    disconnect,
    reconnect,
    isConnected,
    isConnecting,
    lastError,
  }
}