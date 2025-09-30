import { z } from 'zod'
import { TranscriptResultSchema } from './transcript.schema'

/**
 * WebSocket message types for Vietnamese STT real-time communication
 */
export const WebSocketMessageTypeSchema = z.enum([
  'audio_chunk',      // Client sending audio data
  'transcript_result', // Server sending transcription result
  'error',            // Error message
  'connection_status', // Connection status update
  'ping',             // Heartbeat ping
  'pong'              // Heartbeat pong
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
    audioData: z.instanceof(ArrayBuffer)
      .describe('Raw audio data as ArrayBuffer'),
    
    chunkIndex: z.number()
      .min(0)
      .describe('Sequential index of this audio chunk'),
    
    sampleRate: z.number()
      .positive()
      .default(16000)
      .describe('Audio sample rate in Hz'),
    
    channels: z.number()
      .positive()
      .default(1)
      .describe('Number of audio channels'),
    
    format: z.string()
      .default('webm')
      .describe('Audio format/codec')
  }).describe('Audio chunk data payload')
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
 */
export const ErrorMessageSchema = BaseWebSocketMessageSchema.extend({
  type: z.literal('error'),
  
  data: z.object({
    code: z.string()
      .describe('Error code identifier'),
    
    message: z.string()
      .describe('Human-readable error message'),
    
    details: z.any()
      .optional()
      .describe('Optional error details')
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