/**
 * Centralized hook types for Vietnamese STT frontend
 *
 * This file contains all hook-related interfaces and types that were previously
 * defined inline within each hook file. Centralizing these types here
 * improves maintainability, type safety, and code organization.
 */

import type { TranscriptResult } from '@/types/transcript'

// Re-export already exported hook options for consistency
export type { UseAudioRecorderOptions } from '@/hooks/useAudioRecorder'
export type { UseWebSocketOptions } from '@/hooks/useWebSocket'

/**
 * Options for useSessionWebSocket hook
 * Configuration for session-based WebSocket connections with Vietnamese STT
 */
export interface SessionWebSocketOptions {
  /** Callback when transcript result is received */
  onTranscriptResult?: (result: TranscriptResult) => void
  /** Callback when connection status changes */
  onConnectionStatusChange?: (status: string, reason?: string) => void
  /** Callback when WebSocket error occurs */
  onError?: (error: Event) => void
  /** Whether to enable automatic reconnection (default: true) */
  autoReconnect?: boolean
  /** Maximum number of reconnection attempts (default: 3) */
  maxReconnectAttempts?: number
  /** Whether to enable debug logging */
  enableDebug?: boolean
}

/**
 * Response structure for session WebSocket messages
 * Used for session management communication with the backend
 */
export interface SessionResponse {
  /** Message type identifier */
  type: string
  /** Whether the operation was successful */
  success?: boolean
  /** Session ID if applicable */
  session_id?: string
  /** Human-readable message */
  message?: string
  /** Additional session information */
  session_info?: Record<string, unknown>
}

/**
 * Internal connection state for WebSocket management
 * Tracks connection status, reconnection attempts, and health monitoring
 */
export interface ConnectionState {
  /** Current WebSocket instance */
  socket: WebSocket | null
  /** Number of reconnection attempts made */
  reconnectAttempts: number
  /** Timer ID for reconnection scheduling */
  reconnectTimer: number | null
  /** Timer ID for connection timeout */
  connectionTimer: number | null
  /** Timer ID for ping/pong health check */
  pingTimer: number | null
  /** Timestamp of last ping sent */
  lastPingTime: number | null
  /** Timestamp of last pong received */
  lastPongTime: number | null
  /** Timestamp of last successful connection */
  lastConnectedAt: number | null
  /** Timestamp of last disconnection */
  lastDisconnectedAt: number | null
  /** Queue of pending requests during reconnection */
  requestQueue: Array<{data: ArrayBuffer | string, timestamp: number}>
}

/**
 * Options for useRMSHistory hook
 * Configuration for RMS (volume) history tracking and voice detection
 */
export interface UseRMSHistoryOptions {
  /** Current RMS value from audio recorder */
  currentRMS: number
  /** Whether recording is currently active */
  isRecording: boolean
  /** Maximum number of RMS values to store (default: 20) */
  maxHistory?: number
  /** Update interval in milliseconds (default: 100ms) */
  updateInterval?: number
}

/**
 * Return type for useRMSHistory hook
 * Provides access to RMS history data and voice detection state
 */
export interface UseRMSHistoryReturn {
  /** Array of historical RMS values for waveform display */
  rmsHistory: number[]
  /** Current peak RMS value in the history */
  peakRMS: number
  /** Average RMS value across the history */
  averageRMS: number
  /** Whether voice is currently detected (RMS > threshold) */
  isVoiceDetected: boolean
  /** Function to clear the RMS history */
  clearHistory: () => void
}