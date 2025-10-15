/**
 * Audio Conversion Utilities for Vietnamese STT
 * 
 * Handles conversion between different audio formats for frontend-backend compatibility
 */

/**
 * Convert ArrayBuffer to Base64 string for WebSocket transmission
 * @param arrayBuffer - Raw audio data as ArrayBuffer
 * @returns Base64 encoded string
 */
export function arrayBufferToBase64(arrayBuffer: ArrayBuffer): string {
  const bytes = new Uint8Array(arrayBuffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

/**
 * Convert Base64 string to ArrayBuffer for audio processing
 * @param base64 - Base64 encoded audio data
 * @returns ArrayBuffer containing audio data
 */
export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binaryString = atob(base64)
  const bytes = new Uint8Array(binaryString.length)
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }
  return bytes.buffer
}

/**
 * Calculate audio duration from ArrayBuffer
 * @param arrayBuffer - Audio data
 * @param sampleRate - Sample rate in Hz
 * @param channels - Number of channels
 * @returns Duration in seconds
 */
export function calculateAudioDuration(
  arrayBuffer: ArrayBuffer,
  sampleRate: number = 16000,
  channels: number = 1
): number {
  // For WebM format, this is an approximation
  // Real duration calculation would require proper audio decoding
  const bytesPerSample = 2 // 16-bit samples
  const totalSamples = arrayBuffer.byteLength / (bytesPerSample * channels)
  return totalSamples / sampleRate
}

/**
 * Validate audio data for Vietnamese STT processing
 * @param arrayBuffer - Audio data to validate
 * @param minDuration - Minimum duration in seconds (default: 0.1)
 * @param maxDuration - Maximum duration in seconds (default: 30)
 * @returns Validation result with success flag and error message
 */
export function validateAudioData(
  arrayBuffer: ArrayBuffer,
  minDuration: number = 0.1,
  maxDuration: number = 30
): { success: boolean; error?: string } {
  if (!arrayBuffer || arrayBuffer.byteLength === 0) {
    return { success: false, error: 'Audio data is empty' }
  }

  // Check minimum size (roughly 0.1 second at 16kHz mono)
  const minSize = minDuration * 16000 * 2 // 16kHz * 16-bit * 0.1s
  if (arrayBuffer.byteLength < minSize) {
    return { success: false, error: 'Audio too short for processing' }
  }

  // Check maximum size (roughly 30 seconds at 16kHz mono)
  const maxSize = maxDuration * 16000 * 2 // 16kHz * 16-bit * 30s
  if (arrayBuffer.byteLength > maxSize) {
    return { success: false, error: 'Audio too long for processing' }
  }

  return { success: true }
}

/**
 * Create audio chunk metadata for WebSocket transmission
 * @param arrayBuffer - Audio data
 * @param chunkIndex - Sequential chunk index
 * @param sampleRate - Sample rate in Hz
 * @param channels - Number of channels
 * @param isFinal - Whether this is the final chunk
 * @returns Audio chunk metadata
 */
export function createAudioChunkMetadata(
  arrayBuffer: ArrayBuffer,
  chunkIndex: number,
  sampleRate: number = 16000,
  channels: number = 1,
  isFinal: boolean = false
) {
  const audioData = arrayBufferToBase64(arrayBuffer)
  const duration = calculateAudioDuration(arrayBuffer, sampleRate, channels)
  
  return {
    chunk_id: chunkIndex,
    audio_data: audioData,
    sample_rate: sampleRate,
    channels: channels,
    duration: duration,
    is_final: isFinal,
    format: 'webm'
  }
}