import { z } from 'zod'
import { TranscriptResultSchema } from './transcript.schema'

/**
 * WebSocket message types for Vietnamese STT real-time communication
 * ⚠️ UPDATED: Added 'transcription_result' for backend compatibility
 */
export const WebSocketMessageTypeSchema = z.enum([
  'audio_chunk',           // Client sending audio data
  'transcript_result',     // Server sending transcription result (preferred)
  'transcription_result',  // Backend alias (for compatibility)
  'error',                 // Error message
  'connection_status',     // Connection status update
  'ping',                  // Heartbeat ping
  'pong'                   // Heartbeat pong
]).describe('WebSocket message types for real-time Vietnamese STT')

/**
 * WebSocket connection status
 */
export const ConnectionStatusSchema = z.enum([
  'connecting',
  'connected', 
  'disconnected',
  'reconnecting',
  'failed'
]).describe('WebSocket connection status states')

/**
 * Base WebSocket message structure
 */
export const BaseWebSocketMessageSchema = z.object({
  type: WebSocketMessageTypeSchema
    .describe('Type of the WebSocket message'),
  
  timestamp: z.number()
    .positive()
    .describe('Unix timestamp when message was created'),
  
  messageId: z.string()
    .optional()
    .describe('Optional unique message identifier')
}).describe('Base structure for all WebSocket messages')

/**
 * Audio chunk message from client to server
 */
export const AudioChunkMessageSchema = BaseWebSocketMessageSchema.extend({
  type: z.literal('audio_chunk'),
  
  data: z.object({
    chunk_id: z.number()
      .min(0)
      .describe('Sequential index of this audio chunk'),
    
    audio_data: z.string()
      .describe('Base64 encoded audio data for backend compatibility'),
    
    sample_rate: z.number()
      .positive()
      .default(16000)
      .describe('Audio sample rate in Hz'),
    
    channels: z.number()
      .positive()
      .default(1)
      .describe('Number of audio channels'),
    
    duration: z.number()
      .positive()
      .optional()
      .describe('Audio duration in seconds'),
    
    is_final: z.boolean()
      .default(false)
      .describe('Whether this is the final chunk of a recording session'),
    
    format: z.string()
      .default('webm')
      .describe('Audio format/codec')
  }).describe('Audio chunk data payload compatible with backend')
}).describe('WebSocket message containing audio data for Vietnamese STT')

/**
 * Transcript result message from server to client
 */
export const TranscriptResultMessageSchema = BaseWebSocketMessageSchema.extend({
  type: z.literal('transcript_result'),
  
  data: TranscriptResultSchema
    .describe('Vietnamese STT transcript result')
}).describe('WebSocket message containing transcript result')

/**
 * Error message
 * ⚠️ UPDATED: Uses 'error' field instead of 'code' for backend compatibility
 */
export const ErrorMessageSchema = BaseWebSocketMessageSchema.extend({
  type: z.literal('error'),
  
  data: z.object({
    error: z.string()
      .describe('Error type identifier (backend uses this instead of code)'),
    
    code: z.string()
      .optional()
      .describe('Error code identifier (optional, for frontend compatibility)'),
    
    message: z.string()
      .describe('Human-readable error message'),
    
    details: z.record(z.string(), z.unknown())
      .optional()
      .describe('Optional error details'),
    
    timestamp: z.union([z.number(), z.string()])
      .optional()
      .describe('Error timestamp (backend may send datetime)')
  }).describe('Error information')
}).describe('WebSocket error message')

/**
 * Connection status message
 */
export const ConnectionStatusMessageSchema = BaseWebSocketMessageSchema.extend({
  type: z.literal('connection_status'),
  
  data: z.object({
    status: ConnectionStatusSchema
      .describe('Current connection status'),
    
    reason: z.string()
      .optional()
      .describe('Optional reason for status change')
  }).describe('Connection status data')
}).describe('WebSocket connection status message')

/**
 * Union of all possible WebSocket messages
 */
export const WebSocketMessageSchema = z.discriminatedUnion('type', [
  AudioChunkMessageSchema,
  TranscriptResultMessageSchema, 
  ErrorMessageSchema,
  ConnectionStatusMessageSchema,
  BaseWebSocketMessageSchema.extend({ type: z.literal('ping') }),
  BaseWebSocketMessageSchema.extend({ type: z.literal('pong') })
]).describe('Union type for all Vietnamese STT WebSocket messages')

/**
 * WebSocket connection configuration
 */
export const WebSocketConfigSchema = z.object({
  url: z.string()
    .url()
    .describe('WebSocket server URL'),
  
  reconnectAttempts: z.number()
    .min(0)
    .default(3)
    .describe('Maximum number of reconnection attempts'),
  
  reconnectDelay: z.number()
    .positive()
    .default(1000)
    .describe('Delay between reconnection attempts in milliseconds'),
  
  heartbeatInterval: z.number()
    .positive()
    .default(30000)
    .describe('Heartbeat ping interval in milliseconds'),
  
  maxMessageSize: z.number()
    .positive()
    .default(1024 * 1024)
    .describe('Maximum message size in bytes')
}).describe('Configuration for Vietnamese STT WebSocket connection')

export default WebSocketMessageSchema