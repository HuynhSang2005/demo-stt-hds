import { z } from 'zod'

/**
 * Audio recording format and codec configuration
 */
export const AudioFormatSchema = z.object({
  mimeType: z.string()
    .default('audio/webm;codecs=opus')
    .describe('MIME type for audio recording, optimized for Vietnamese STT'),
  
  sampleRate: z.number()
    .positive()
    .default(16000)
    .describe('Audio sample rate in Hz (16kHz required for Wav2Vec2)'),
  
  channels: z.number()
    .positive()
    .default(1)
    .describe('Number of audio channels (mono recommended)'),
  
  bitRate: z.number()
    .positive()
    .optional()
    .describe('Audio bit rate (optional, auto-determined by codec)')
}).describe('Audio format configuration for Vietnamese STT recording')

/**
 * Audio chunk configuration for real-time processing
 */
export const AudioChunkConfigSchema = z.object({
  chunkDuration: z.number()
    .positive()
    .default(2000)
    .describe('Duration of each audio chunk in milliseconds'),
  
  maxChunkSize: z.number()
    .positive()
    .default(1024 * 512)
    .describe('Maximum size of audio chunk in bytes'),
  
  overlap: z.number()
    .min(0)
    .max(1)
    .default(0.1)
    .describe('Overlap between consecutive chunks (0-1)'),
  
  bufferSize: z.number()
    .positive()
    .default(4096)
    .describe('Audio buffer size for processing')
}).describe('Configuration for audio chunking in Vietnamese STT')

/**
 * MediaRecorder state for audio recording
 */
export const RecordingStateSchema = z.enum([
  'inactive',
  'recording', 
  'paused'
]).describe('MediaRecorder state for audio recording')

/**
 * Audio recording session information
 */
export const AudioSessionSchema = z.object({
  sessionId: z.string()
    .describe('Unique identifier for this recording session'),
  
  startTime: z.number()
    .positive()
    .describe('Unix timestamp when recording started'),
  
  endTime: z.number()
    .positive()
    .optional()
    .describe('Unix timestamp when recording ended'),
  
  totalDuration: z.number()
    .min(0)
    .optional()
    .describe('Total recording duration in milliseconds'),
  
  chunksRecorded: z.number()
    .min(0)
    .default(0)
    .describe('Number of audio chunks recorded'),
  
  format: AudioFormatSchema
    .describe('Audio format used for this session'),
  
  status: RecordingStateSchema
    .describe('Current recording status')
}).describe('Audio recording session metadata')

/**
 * Audio chunk data structure
 */
export const AudioChunkSchema = z.object({
  data: z.union([z.instanceof(ArrayBuffer), z.instanceof(Blob)])
    .describe('Raw audio data as ArrayBuffer or Blob'),
  
  chunkIndex: z.number()
    .min(0)
    .describe('Sequential index of this chunk in the session'),
  
  timestamp: z.number()
    .positive()
    .describe('Unix timestamp when chunk was recorded'),
  
  duration: z.number()
    .positive()
    .describe('Duration of this chunk in milliseconds'),
  
  size: z.number()
    .positive()
    .describe('Size of audio data in bytes'),
  
  sessionId: z.string()
    .describe('ID of the recording session this chunk belongs to')
}).describe('Individual audio chunk for Vietnamese STT processing')

/**
 * Audio recorder configuration
 */
export const AudioRecorderConfigSchema = z.object({
  format: AudioFormatSchema
    .describe('Audio format configuration'),
  
  chunkConfig: AudioChunkConfigSchema
    .describe('Audio chunking configuration'),
  
  autoStart: z.boolean()
    .default(false)
    .describe('Whether to automatically start recording when initialized'),
  
  enableNoiseReduction: z.boolean()
    .default(true)
    .describe('Enable noise reduction for better Vietnamese STT accuracy'),
  
  echoCancellation: z.boolean()
    .default(true)
    .describe('Enable echo cancellation'),
  
  maxRecordingTime: z.number()
    .positive()
    .default(300000)
    .describe('Maximum recording time in milliseconds (5 minutes default)')
}).describe('Configuration for Vietnamese STT audio recorder')

/**
 * Audio recorder error types
 */
export const AudioErrorSchema = z.object({
  code: z.enum([
    'PERMISSION_DENIED',
    'DEVICE_NOT_FOUND',
    'RECORDING_FAILED',
    'FORMAT_NOT_SUPPORTED',
    'CHUNK_TOO_LARGE',
    'SESSION_EXPIRED'
  ]).describe('Audio error code'),
  
  message: z.string()
    .describe('Human-readable error message'),
  
  details: z.any()
    .optional()
    .describe('Additional error details')
}).describe('Audio recording error information')

export default AudioRecorderConfigSchema