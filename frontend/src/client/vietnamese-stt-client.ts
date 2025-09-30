/**
 * Vietnamese STT Client Wrapper
 * 
 * This module provides a high-level interface for the Vietnamese Speech-to-Text API,
 * wrapping the auto-generated OpenAPI client with Vietnamese STT specific functionality.
 * 
 * @example
 * ```typescript
 * import { vietnameseSttClient } from '@/client/vietnamese-stt-client'
 * 
 * // Initialize client
 * const client = vietnameseSttClient({
 *   baseUrl: 'http://localhost:8000',
 *   timeout: 30000
 * })
 * 
 * // Transcribe audio
 * const result = await client.transcribe(audioFile)
 * 
 * // Connect WebSocket
 * const ws = client.connectWebSocket({
 *   onTranscript: (transcript) => console.log(transcript),
 *   onError: (error) => console.error(error)
 * })
 * ```
 */

import type { 
  TranscriptResult, 
  VietnameseSentiment
} from '@/types/transcript'
import type { AudioError } from '@/types/audio'
import type { WebSocketMessage } from '@/types/websocket'

// Note: These imports will be available after running `npm run generate-client`
// import { ... } from './sdk.gen'
// import { ... } from './types.gen'
// import { ... } from './client.gen'

/**
 * Vietnamese STT Client Configuration
 */
export interface VietnameseSTTClientConfig {
  /** Base URL for the Vietnamese STT API */
  baseUrl?: string
  /** Request timeout in milliseconds */
  timeout?: number
  /** WebSocket URL for real-time transcription */
  wsUrl?: string
  /** API key for authentication (if required) */
  apiKey?: string
  /** Custom headers to include in requests */
  headers?: Record<string, string>
}

/**
 * WebSocket connection options for real-time transcription
 */
export interface WebSocketOptions {
  /** Callback for transcript results */
  onTranscript?: (transcript: TranscriptResult) => void
  /** Callback for connection open */
  onOpen?: () => void
  /** Callback for connection close */
  onClose?: (code: number, reason: string) => void
  /** Callback for errors */
  onError?: (error: AudioError) => void
  /** Callback for raw WebSocket messages */
  onMessage?: (message: WebSocketMessage) => void
  /** Auto-reconnect on connection loss */
  autoReconnect?: boolean
  /** Reconnection delay in milliseconds */
  reconnectDelay?: number
  /** Maximum reconnection attempts */
  maxReconnectAttempts?: number
}

/**
 * Audio transcription options
 */
export interface TranscriptionOptions {
  /** Include sentiment analysis (toxic detection) */
  includeSentiment?: boolean
  /** Audio format hint for better processing */
  format?: 'wav' | 'webm' | 'ogg' | 'mp4'
  /** Sample rate of the audio (16kHz recommended) */
  sampleRate?: number
  /** Language hint (default: Vietnamese) */
  language?: string
  /** Enable noise reduction */
  enableNoiseReduction?: boolean
}

/**
 * Vietnamese STT Client Interface
 */
export interface VietnameseSTTClient {
  /**
   * Transcribe audio file or blob
   * @param audio - Audio file, blob, or buffer
   * @param options - Transcription options
   * @returns Promise with transcript result and sentiment analysis
   */
  transcribe(audio: File | Blob | ArrayBuffer, options?: TranscriptionOptions): Promise<TranscriptResult>
  
  /**
   * Check API health status
   * @returns Promise with health status
   */
  healthCheck(): Promise<{ status: string; timestamp: number }>
  
  /**
   * Connect to WebSocket for real-time transcription
   * @param options - WebSocket connection options
   * @returns WebSocket connection manager
   */
  connectWebSocket(options?: WebSocketOptions): WebSocketConnection
  
  /**
   * Get supported audio formats
   * @returns List of supported MIME types
   */
  getSupportedFormats(): string[]
  
  /**
   * Validate audio file before transcription
   * @param audio - Audio file to validate
   * @returns Validation result
   */
  validateAudio(audio: File | Blob): { valid: boolean; error?: string }
}

/**
 * WebSocket connection manager interface
 */
export interface WebSocketConnection {
  /** Send audio chunk for real-time processing */
  sendAudioChunk(chunk: ArrayBuffer, metadata?: Record<string, unknown>): void
  /** Close WebSocket connection */
  disconnect(): void
  /** Get current connection state */
  getState(): 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'
  /** Check if connection is active */
  isConnected(): boolean
  /** Reconnect if connection is lost */
  reconnect(): void
}

/**
 * Create Vietnamese STT Client instance
 * 
 * @param config - Client configuration
 * @returns Configured Vietnamese STT client
 */
export function vietnameseSttClient(config: VietnameseSTTClientConfig = {}): VietnameseSTTClient {
  // Store configuration for future REST API implementation
  console.debug('Vietnamese STT client created with config:', config)

  // TODO: Import and configure generated client when available
  // const generatedClient = createClient({ baseUrl, timeout, headers: { ...headers, ...(apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {}) } })

  return {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    async transcribe(_audio: File | Blob | ArrayBuffer, _options?: TranscriptionOptions): Promise<TranscriptResult> {
      // TODO: Implement using generated SDK
      // For now, return mock implementation
      console.warn('Vietnamese STT Client: Generated client not available yet. Run `npm run generate-client` first.')
      
      // Mock implementation for development
      return Promise.resolve({
        id: `mock-${Date.now()}`,
        text: 'Mock transcript result',
        label: 'neutral' as VietnameseSentiment,
        confidence: 0.95,
        timestamp: Date.now(),
        warning: false,
        duration: 3000,
        metadata: {
          processingTime: 1500,
          modelVersion: 'mock-v1.0'
        }
      } satisfies TranscriptResult)
    },

    async healthCheck() {
      // TODO: Implement using generated SDK
      console.warn('Vietnamese STT Client: Generated client not available yet. Run `npm run generate-client` first.')
      
      return Promise.resolve({
        status: 'healthy',
        timestamp: Date.now()
      })
    },

    connectWebSocket(options: WebSocketOptions = {}): WebSocketConnection {
      // TODO: Implement using generated WebSocket client or custom implementation
      console.warn('Vietnamese STT Client: WebSocket client not implemented yet.', { options })
      
      // Mock implementation
      return {
        sendAudioChunk: (chunk: ArrayBuffer) => {
          console.log('Mock: Sending audio chunk', chunk.byteLength, 'bytes')
        },
        disconnect: () => {
          console.log('Mock: Disconnecting WebSocket')
        },
        getState: () => 'CLOSED' as const,
        isConnected: () => false,
        reconnect: () => {
          console.log('Mock: Reconnecting WebSocket')
        }
      }
    },

    getSupportedFormats(): string[] {
      return ['audio/wav', 'audio/webm', 'audio/webm;codecs=opus', 'audio/ogg', 'audio/mp4']
    },

    validateAudio(audio: File | Blob): { valid: boolean; error?: string } {
      // Basic validation
      const maxSize = 10 * 1024 * 1024 // 10MB
      const supportedTypes = this.getSupportedFormats()
      
      if (audio.size > maxSize) {
        return { valid: false, error: 'File size exceeds 10MB limit' }
      }
      
      if (!supportedTypes.includes(audio.type)) {
        return { valid: false, error: `Unsupported audio format: ${audio.type}` }
      }
      
      return { valid: true }
    }
  }
}

/**
 * Default Vietnamese STT client instance
 * Ready to use with default configuration
 */
export const defaultVietnameseSttClient = vietnameseSttClient()

/**
 * Re-export types for convenience
 */
export type {
  TranscriptResult,
  VietnameseSentiment,
  AudioError,
  WebSocketMessage
}