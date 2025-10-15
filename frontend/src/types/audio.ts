import { z } from 'zod'
import WaveSurfer from 'wavesurfer.js'
import {
  AudioFormatSchema,
  AudioRecorderConfigSchema,
  AudioChunkSchema,
  AudioChunkConfigSchema,
  AudioSessionSchema,
  RecordingStateSchema,
  AudioErrorSchema
} from '../schemas/audio.schema'

/**
 * Audio format configuration for Vietnamese STT
 */
export type AudioFormat = z.infer<typeof AudioFormatSchema>

/**
 * Audio recorder configuration for MediaRecorder API
 */
export type AudioRecorderConfig = z.infer<typeof AudioRecorderConfigSchema>

/**
 * Individual audio chunk for Vietnamese STT processing
 */
export type AudioChunk = z.infer<typeof AudioChunkSchema>

/**
 * Audio chunk configuration for real-time processing
 */
export type AudioChunkConfig = z.infer<typeof AudioChunkConfigSchema>

/**
 * Audio recording session metadata
 */
export type AudioSession = z.infer<typeof AudioSessionSchema>

/**
 * MediaRecorder state for audio recording
 */
export type RecordingState = z.infer<typeof RecordingStateSchema>

/**
 * Audio recording error information
 */
export type AudioError = z.infer<typeof AudioErrorSchema>

/**
 * Audio chunk data with metadata for WebSocket transmission
 * Currently extends AudioChunk without additional properties for future extensibility
 */
// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface AudioChunkData extends AudioChunk {
  // Extends the schema-based AudioChunk with additional runtime properties
  // Currently empty but kept for future API extensions
}

/**
 * Audio recorder hook return type
 */
export interface UseAudioRecorderReturn {
  // Recording state
  isRecording: boolean
  isProcessing: boolean
  processingState: RecordingState
  
  // Recording controls
  startRecording: () => Promise<void>
  stopRecording: () => void
  pauseRecording: () => void
  resumeRecording: () => void
  
  // Audio data
  audioChunks: AudioChunk[]
  currentVolume: number
  recordingDuration: number
  
  // Device management
  availableDevices: MediaDeviceInfo[]
  selectedDevice: MediaDeviceInfo | null
  selectDevice: (deviceId: string) => void
  getAvailableDevices: () => Promise<MediaDeviceInfo[]>
  
  // Error handling
  error: AudioError | null
  permissionGranted: boolean
  
  // Cleanup
  cleanup: () => void
}

/**
 * Audio visualization hook return type for WaveSurfer.js
 */
export interface UseAudioVisualizationReturn {
  // WaveSurfer instance
  waveSurfer: WaveSurfer | null
  
  // Visualization controls
  initializeWaveSurfer: (container: HTMLElement) => void
  updateVisualization: (audioData: Float32Array) => void
  
  // Playback controls
  play: () => void
  pause: () => void
  stop: () => void
  
  // State
  isPlaying: boolean
  currentTime: number
  duration: number
  
  // Cleanup
  destroy: () => void
}

/**
 * Audio processing utilities
 */
export interface AudioProcessingUtils {
  /**
   * Convert ArrayBuffer to Float32Array for visualization
   */
  bufferToFloat32Array: (buffer: ArrayBuffer) => Float32Array
  
  /**
   * Resample audio data to target sample rate (16kHz for Vietnamese STT)
   */
  resampleAudio: (audioData: Float32Array, currentSampleRate: number, targetSampleRate: number) => Float32Array
  
  /**
   * Calculate RMS volume for audio chunk
   */
  calculateVolume: (audioData: Float32Array) => number
  
  /**
   * Apply noise gate to reduce background noise
   */
  applyNoiseGate: (audioData: Float32Array, threshold: number) => Float32Array
  
  /**
   * Validate audio chunk for Vietnamese STT requirements
   */
  validateAudioChunk: (chunk: AudioChunkData) => boolean
}

/**
 * Type guard to check if MIME type is supported
 * @param mimeType - MIME type string to check
 * @returns true if MIME type is supported by Vietnamese STT
 */
export function isSupportedMimeType(mimeType: string): boolean {
  return ['audio/wav', 'audio/webm', 'audio/webm;codecs=opus', 'audio/ogg', 'audio/mp4'].includes(mimeType)
}

/**
 * Type guard to check if processing state indicates active recording
 * @param state - Processing state to check
 * @returns true if currently recording audio
 */
export function isRecordingState(state: RecordingState): boolean {
  return ['recording', 'paused'].includes(state)
}

/**
 * Type guard to check if processing state indicates completion
 * @param state - Processing state to check
 * @returns true if processing is complete
 */
export function isInactiveState(state: RecordingState): boolean {
  return state === 'inactive'
}

/**
 * Helper to get optimal audio configuration for Vietnamese STT
 * @returns Recommended audio recorder config
 */
export function getOptimalAudioConfig(): AudioRecorderConfig {
  return {
    format: {
      mimeType: 'audio/webm;codecs=opus',
      sampleRate: 16000,
      channels: 1
    },
    chunkConfig: {
      chunkDuration: 2000,
      maxChunkSize: 1024 * 512,
      overlap: 0.1,
      bufferSize: 4096
    },
    autoStart: false,
    enableNoiseReduction: true,
    echoCancellation: true,
    maxRecordingTime: 300000
  }
}

/**
 * Helper to validate audio device capabilities
 * @param device - Audio device to validate
 * @returns true if device supports Vietnamese STT requirements
 */
export function validateAudioDevice(device: MediaDeviceInfo): boolean {
  return device.kind === 'audioinput' && device.deviceId !== ''
}