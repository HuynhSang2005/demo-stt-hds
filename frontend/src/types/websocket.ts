import { z } from 'zod'
import {
  WebSocketMessageTypeSchema,
  ConnectionStatusSchema,
  BaseWebSocketMessageSchema,
  AudioChunkMessageSchema,
  TranscriptResultMessageSchema,
  ErrorMessageSchema,
  ConnectionStatusMessageSchema,
  WebSocketMessageSchema,
  WebSocketConfigSchema
} from '../schemas/websocket.schema'

/**
 * WebSocket message types for Vietnamese STT communication
 */
export type WebSocketMessageType = z.infer<typeof WebSocketMessageTypeSchema>

/**
 * WebSocket connection status states
 */
export type ConnectionStatus = z.infer<typeof ConnectionStatusSchema>

/**
 * Base WebSocket message structure
 */
export type BaseWebSocketMessage = z.infer<typeof BaseWebSocketMessageSchema>

/**
 * Audio chunk message from client to server
 * Contains raw audio data for Vietnamese STT processing
 */
export type AudioChunkMessage = z.infer<typeof AudioChunkMessageSchema>

/**
 * Transcript result message from server to client
 * Contains Vietnamese STT + toxic detection results
 */
export type TranscriptResultMessage = z.infer<typeof TranscriptResultMessageSchema>

/**
 * Error message for WebSocket communication issues
 */
export type ErrorMessage = z.infer<typeof ErrorMessageSchema>

/**
 * Connection status change message
 */
export type ConnectionStatusMessage = z.infer<typeof ConnectionStatusMessageSchema>

/**
 * Union of all possible WebSocket messages
 */
export type WebSocketMessage = z.infer<typeof WebSocketMessageSchema>

/**
 * WebSocket connection configuration
 */
export type WebSocketConfig = z.infer<typeof WebSocketConfigSchema>

/**
 * WebSocket event handlers interface
 */
export interface WebSocketEventHandlers {
  onOpen?: (event: Event) => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
  onMessage?: (message: WebSocketMessage) => void
  onTranscriptResult?: (result: TranscriptResultMessage['data']) => void
  onConnectionStatusChange?: (status: ConnectionStatus, reason?: string) => void
}

/**
 * WebSocket hook return type
 */
export interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus
  sendAudioChunk: (audioData: ArrayBuffer, chunkIndex: number) => void
  sendMessage: (message: WebSocketMessage) => void
  connect: () => void
  disconnect: () => void
  reconnect: () => void
  isConnected: boolean
  isConnecting: boolean
  lastError: ErrorMessage | null
}

/**
 * Type guard to check if message is transcript result
 * @param message - WebSocket message to check
 * @returns true if message contains transcript result
 */
export function isTranscriptResultMessage(message: WebSocketMessage): message is TranscriptResultMessage {
  return message.type === 'transcript_result'
}

/**
 * Type guard to check if message is audio chunk
 * @param message - WebSocket message to check  
 * @returns true if message is audio chunk
 */
export function isAudioChunkMessage(message: WebSocketMessage): message is AudioChunkMessage {
  return message.type === 'audio_chunk'
}

/**
 * Type guard to check if message is error
 * @param message - WebSocket message to check
 * @returns true if message is error
 */
export function isErrorMessage(message: WebSocketMessage): message is ErrorMessage {
  return message.type === 'error'
}

/**
 * Type guard to check if message is connection status
 * @param message - WebSocket message to check
 * @returns true if message is connection status
 */
export function isConnectionStatusMessage(message: WebSocketMessage): message is ConnectionStatusMessage {
  return message.type === 'connection_status'
}