import { useRef, useCallback, useState, useEffect } from 'react'
import { webSocketManager, type ConnectionStatus } from '@/lib/websocket-manager'
import type { TranscriptResult } from '@/types/transcript'

interface SessionWebSocketOptions {
  onTranscriptResult?: (result: TranscriptResult) => void
  onConnectionStatusChange?: (status: string, reason?: string) => void
  onError?: (error: Event) => void
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  enableDebug?: boolean
}

interface SessionResponse {
  type: string
  success?: boolean
  session_id?: string
  message?: string
  session_info?: any
}

export const useSessionWebSocket = (
  url: string,
  options: SessionWebSocketOptions = {}
) => {
  const {
    onTranscriptResult,
    onConnectionStatusChange,
    onError,
    autoReconnect = true,
    maxReconnectAttempts = 3,
    enableDebug = false
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [lastError, setLastError] = useState<Error | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  
  const connectionIdRef = useRef<string | null>(null)
  const isMounted = useRef(true)

  const log = useCallback((message: string, ...args: any[]) => {
    if (enableDebug) {
      console.log(`[SessionWebSocket:${connectionIdRef.current}]`, message, ...args)
    }
  }, [enableDebug])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMounted.current = false
      if (connectionIdRef.current) {
        webSocketManager.removeConnection(connectionIdRef.current)
        connectionIdRef.current = null
      }
    }
  }, [])

  // Connection management
  const connectToWebSocket = useCallback(() => {
    if (!isMounted.current) return
    
    // Clean up existing connection
    if (connectionIdRef.current) {
      webSocketManager.removeConnection(connectionIdRef.current)
    }
    
    // Create new connection
    const connectionId = webSocketManager.createConnection(url, {
      autoReconnect,
      maxReconnectAttempts
    })
    
    connectionIdRef.current = connectionId
    
    // Set up event listeners
    webSocketManager.addStatusListener(connectionId, handleStatusChange)
    webSocketManager.addMessageListener(connectionId, handleMessage)
    webSocketManager.addErrorListener(connectionId, handleError)
    
    // Connect
    webSocketManager.connect(connectionId)
  }, [url, autoReconnect, maxReconnectAttempts])

  // Status change handler
  const handleStatusChange = useCallback((status: ConnectionStatus, reason?: string) => {
    if (!isMounted.current) return
    
    log('Status changed:', status, reason)
    setIsConnected(status === 'connected')
    onConnectionStatusChange?.(status, reason)
  }, [log, onConnectionStatusChange])

  // Message handler
  const handleMessage = useCallback((event: MessageEvent) => {
    if (!isMounted.current) return
    
    try {
      const data = JSON.parse(event.data)
      log('Received message:', data)

      // Handle different message types
      if (data.type === 'transcription_result' && data.result) {
        onTranscriptResult?.(data.result)
      } else if (data.type === 'connection_status') {
        onConnectionStatusChange?.(data.status, data.message)
      } else if (data.type === 'processing_status') {
        log('Processing status:', data)
      } else if (data.type === 'error') {
        const error = new Error(data.message || 'WebSocket error')
        setLastError(error)
      }
    } catch (error) {
      log('Failed to parse message:', event.data)
    }
  }, [log, onTranscriptResult, onConnectionStatusChange])

  // Error handler
  const handleError = useCallback((event: Event) => {
    if (!isMounted.current) return
    
    log('WebSocket error:', event)
    const error = new Error('WebSocket connection error')
    setLastError(error)
    onError?.(event)
  }, [log, onError])

  // Send session command
  const sendSessionCommand = useCallback((command: string, sessionId?: string) => {
    if (!connectionIdRef.current || !isConnected) {
      log('Cannot send command - not connected')
      throw new Error('WebSocket not connected')
    }

    const message = {
      type: "session_command",
      command,
      session_id: sessionId
    }

    const success = webSocketManager.send(connectionIdRef.current, JSON.stringify(message))
    if (!success) {
      throw new Error('Failed to send message')
    }
    
    log('Sent session command:', message)
  }, [isConnected, log])

  // Send audio chunk
  const sendAudioChunk = useCallback((audioData: ArrayBuffer, chunkIndex: number = 0) => {
    if (!connectionIdRef.current || !isConnected) {
      throw new Error('WebSocket not connected')
    }

    const success = webSocketManager.send(connectionIdRef.current, audioData)
    if (!success) {
      throw new Error('Failed to send audio chunk')
    }
    
    log('Sent audio chunk:', audioData.byteLength, 'bytes, index:', chunkIndex)
  }, [isConnected, log])

  // Start session with connection check
  const startSession = useCallback(async (): Promise<string> => {
    // Wait for connection if not ready
    if (!isConnected) {
      log('Waiting for WebSocket connection before starting session...')
      await new Promise((resolve, reject) => {
        let attempts = 0
        const maxAttempts = 50 // 5 seconds max wait
        const checkConnection = () => {
          if (isConnected) {
            resolve(true)
          } else {
            attempts++
            if (attempts >= maxAttempts) {
              reject(new Error('Connection timeout'))
            } else {
              setTimeout(checkConnection, 100)
            }
          }
        }
        checkConnection()
      })
    }

    return new Promise((resolve, reject) => {
      try {
        // Listen for response first, then send command
        const handleMessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data) as SessionResponse
            log('Received session response:', data)
            
            // Handle both session_response and auto-session creation
            if ((data.type === 'session_response' || data.type === 'session_created') && 
                data.success && data.session_id) {
              setCurrentSessionId(data.session_id)
              if (connectionIdRef.current) {
                webSocketManager.removeMessageListener(connectionIdRef.current, handleMessage)
              }
              resolve(data.session_id)
            } else if (data.type === 'session_response' && !data.success) {
              if (connectionIdRef.current) {
                webSocketManager.removeMessageListener(connectionIdRef.current, handleMessage)
              }
              reject(new Error(data.message || 'Session start failed'))
            }
          } catch (error) {
            log('Failed to parse session response:', error)
          }
        }
        
        if (connectionIdRef.current) {
          webSocketManager.addMessageListener(connectionIdRef.current, handleMessage)
        }
        
        // Send command after setting up listener
        sendSessionCommand('start_session')
        
        // Timeout after 3 seconds (reduced from 5)
        setTimeout(() => {
          if (connectionIdRef.current) {
            webSocketManager.removeMessageListener(connectionIdRef.current, handleMessage)
          }
          reject(new Error('Session start timeout'))
        }, 3000)
        
      } catch (error) {
        reject(error)
      }
    })
  }, [sendSessionCommand, isConnected, log])

  // End session
  const endSession = useCallback(async (): Promise<TranscriptResult | null> => {
    if (!currentSessionId) {
      return null
    }

    return new Promise((resolve) => {
      try {
        sendSessionCommand('end_session', currentSessionId)
        
        // Listen for transcript result
        const handleMessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data)
            
            if (data.type === 'transcription_result' && data.result) {
              setCurrentSessionId(null)
              if (connectionIdRef.current) {
                webSocketManager.removeMessageListener(connectionIdRef.current, handleMessage)
              }
              resolve(data.result)
            } else if (data.type === 'session_response') {
              // Session ended without transcript
              setCurrentSessionId(null)
              if (connectionIdRef.current) {
                webSocketManager.removeMessageListener(connectionIdRef.current, handleMessage)
              }
              resolve(null)
            }
          } catch (error) {
            // Ignore non-JSON messages
          }
        }
        
        if (connectionIdRef.current) {
          webSocketManager.addMessageListener(connectionIdRef.current, handleMessage)
        }
        
        // Timeout after 10 seconds
        setTimeout(() => {
          if (connectionIdRef.current) {
            webSocketManager.removeMessageListener(connectionIdRef.current, handleMessage)
          }
          setCurrentSessionId(null)
          resolve(null)
        }, 10000)
        
      } catch (error) {
        setCurrentSessionId(null)
        resolve(null)
      }
    })
  }, [currentSessionId, sendSessionCommand])

  // Disconnect function
  const disconnect = useCallback(() => {
    if (connectionIdRef.current) {
      log('Disconnecting WebSocket')
      webSocketManager.removeConnection(connectionIdRef.current)
      connectionIdRef.current = null
    }
    
    setIsConnected(false)
    setCurrentSessionId(null)
    setLastError(null)
  }, [log])

  // Auto-connect on mount with StrictMode compatibility
  useEffect(() => {
    isMounted.current = true
    
    // Add a small delay to prevent race conditions in StrictMode
    const timer = setTimeout(() => {
      if (isMounted.current) {
        connectToWebSocket()
      }
    }, 10)
    
    return () => {
      log('Cleaning up session WebSocket')
      isMounted.current = false
      clearTimeout(timer)
      
      // Clean up connection
      if (connectionIdRef.current) {
        webSocketManager.removeConnection(connectionIdRef.current)
        connectionIdRef.current = null
      }
      
      setIsConnected(false)
      setCurrentSessionId(null)
    }
  }, [connectToWebSocket, log])

  return {
    isConnected,
    lastError,
    currentSessionId,
    connect: connectToWebSocket,
    disconnect,
    sendAudioChunk,
    startSession,
    endSession,
    sendSessionCommand
  }
}