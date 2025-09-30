/**
 * Global WebSocket Connection Manager
 * Prevents multiple WebSocket connections in React StrictMode
 */

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting'

interface WebSocketConnection {
  ws: WebSocket | null
  status: ConnectionStatus
  url: string
  listeners: Set<(status: ConnectionStatus, reason?: string) => void>
  messageListeners: Set<(event: MessageEvent) => void>
  errorListeners: Set<(event: Event) => void>
  reconnectAttempts: number
  reconnectTimer: number | null
  maxReconnectAttempts: number
}

class WebSocketManager {
  private connections = new Map<string, WebSocketConnection>()

  createConnection(
    url: string,
    options: {
      autoReconnect?: boolean
      maxReconnectAttempts?: number
    } = {}
  ): string {
    const connectionId = Math.random().toString(36).substr(2, 9)
    
    const connection: WebSocketConnection = {
      ws: null,
      status: 'disconnected',
      url,
      listeners: new Set(),
      messageListeners: new Set(),
      errorListeners: new Set(),
      reconnectAttempts: 0,
      reconnectTimer: null,
      maxReconnectAttempts: options.maxReconnectAttempts || 3
    }
    
    this.connections.set(connectionId, connection)
    return connectionId
  }

  connect(connectionId: string): void {
    const connection = this.connections.get(connectionId)
    if (!connection) {
      console.warn(`[WebSocketManager] Connection ${connectionId} not found`)
      return
    }
    
    // Check if already connected or connecting
    if (connection.status === 'connected' || connection.status === 'connecting') {
      console.log(`[WebSocketManager] Connection ${connectionId} already ${connection.status}`)
      return
    }

    console.log(`[WebSocketManager] Connecting ${connectionId} to ${connection.url}`)
    connection.status = 'connecting'
    this.notifyStatusListeners(connection, 'connecting')

    try {
      // Close existing WebSocket if any
      if (connection.ws) {
        connection.ws.close()
        connection.ws = null
      }
      
      connection.ws = new WebSocket(connection.url)
      connection.ws.binaryType = 'arraybuffer' // For audio data

      connection.ws.onopen = () => {
        console.log(`[WebSocketManager] Connected ${connectionId}`)
        connection.status = 'connected'
        connection.reconnectAttempts = 0
        
        // Clear reconnect timer on successful connection
        if (connection.reconnectTimer) {
          clearTimeout(connection.reconnectTimer)
          connection.reconnectTimer = null
        }
        
        this.notifyStatusListeners(connection, 'connected')
      }

      connection.ws.onclose = (event) => {
        console.log(`[WebSocketManager] Disconnected ${connectionId}:`, event.code, event.reason)
        connection.status = 'disconnected'
        connection.ws = null
        this.notifyStatusListeners(connection, 'disconnected', event.reason)

        // Auto-reconnect logic - only for unexpected disconnections
        if (connection.reconnectAttempts < connection.maxReconnectAttempts && 
            event.code !== 1000 && // Normal close
            event.code !== 1001) { // Going away
          const delay = Math.min(1000 * Math.pow(2, connection.reconnectAttempts), 10000)
          console.log(`[WebSocketManager] Reconnecting ${connectionId} in ${delay}ms`)
          
          connection.status = 'reconnecting'
          this.notifyStatusListeners(connection, 'reconnecting')
          
          connection.reconnectTimer = setTimeout(() => {
            connection.reconnectAttempts++
            this.connect(connectionId)
          }, delay)
        }
      }

      connection.ws.onerror = (event) => {
        console.log(`[WebSocketManager] Error ${connectionId}:`, event)
        connection.errorListeners.forEach(listener => listener(event))
      }

      connection.ws.onmessage = (event) => {
        connection.messageListeners.forEach(listener => listener(event))
      }

    } catch (error) {
      console.error(`[WebSocketManager] Connection failed ${connectionId}:`, error)
      connection.status = 'disconnected'
      this.notifyStatusListeners(connection, 'disconnected', String(error))
    }
  }

  disconnect(connectionId: string): void {
    const connection = this.connections.get(connectionId)
    if (!connection) return

    if (connection.reconnectTimer) {
      clearTimeout(connection.reconnectTimer)
      connection.reconnectTimer = null
    }

    if (connection.ws) {
      connection.ws.close(1000, 'Manual disconnect')
      connection.ws = null
    }

    connection.status = 'disconnected'
    this.notifyStatusListeners(connection, 'disconnected', 'Manual disconnect')
  }

  removeConnection(connectionId: string): void {
    const connection = this.connections.get(connectionId)
    if (connection) {
      this.disconnect(connectionId)
      this.connections.delete(connectionId)
    }
  }

  send(connectionId: string, data: string | ArrayBuffer): boolean {
    const connection = this.connections.get(connectionId)
    if (!connection || !connection.ws || connection.ws.readyState !== WebSocket.OPEN) {
      return false
    }

    try {
      connection.ws.send(data)
      return true
    } catch (error) {
      console.error(`[WebSocketManager] Send failed ${connectionId}:`, error)
      return false
    }
  }

  addStatusListener(connectionId: string, listener: (status: ConnectionStatus, reason?: string) => void): void {
    const connection = this.connections.get(connectionId)
    if (connection) {
      connection.listeners.add(listener)
    }
  }

  removeStatusListener(connectionId: string, listener: (status: ConnectionStatus, reason?: string) => void): void {
    const connection = this.connections.get(connectionId)
    if (connection) {
      connection.listeners.delete(listener)
    }
  }

  addMessageListener(connectionId: string, listener: (event: MessageEvent) => void): void {
    const connection = this.connections.get(connectionId)
    if (connection) {
      connection.messageListeners.add(listener)
    }
  }

  removeMessageListener(connectionId: string, listener: (event: MessageEvent) => void): void {
    const connection = this.connections.get(connectionId)
    if (connection) {
      connection.messageListeners.delete(listener)
    }
  }

  addErrorListener(connectionId: string, listener: (event: Event) => void): void {
    const connection = this.connections.get(connectionId)
    if (connection) {
      connection.errorListeners.add(listener)
    }
  }

  removeErrorListener(connectionId: string, listener: (event: Event) => void): void {
    const connection = this.connections.get(connectionId)
    if (connection) {
      connection.errorListeners.delete(listener)
    }
  }

  private notifyStatusListeners(connection: WebSocketConnection, status: ConnectionStatus, reason?: string): void {
    connection.listeners.forEach(listener => {
      try {
        listener(status, reason)
      } catch (error) {
        console.error('[WebSocketManager] Status listener error:', error)
      }
    })
  }
}

export const webSocketManager = new WebSocketManager()
export type { ConnectionStatus }