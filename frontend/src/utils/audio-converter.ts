/**
 * Audio Format Converter Utilities
 * Converts WebM/Opus audio to WAV format for backend compatibility
 */

/**
 * Convert WebM/Opus Blob to WAV format ArrayBuffer
 * This is necessary because backend's ffmpeg has issues decoding raw WebM chunks
 * 
 * @param webmBlob - Audio blob from MediaRecorder (WebM/Opus format)
 * @param targetSampleRate - Target sample rate (default: 16000 for Wav2Vec2)
 * @returns ArrayBuffer containing WAV file data
 */
export async function convertWebMToWAV(
  webmBlob: Blob,
  targetSampleRate: number = 16000
): Promise<ArrayBuffer> {
  let audioContext: AudioContext | null = null
  
  try {
    // Validate input
    if (!webmBlob || webmBlob.size === 0) {
      throw new Error('Empty or invalid audio blob')
    }
    
    if (webmBlob.size < 1000) {
      throw new Error(`Audio blob too small (${webmBlob.size} bytes), likely incomplete`)
    }
    
    console.log('[Audio Converter] Converting WebM blob:', {
      size: webmBlob.size,
      type: webmBlob.type,
      targetSampleRate
    })
    
    // Create audio context for decoding
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
      sampleRate: targetSampleRate
    })

    // Decode WebM blob to AudioBuffer
    const arrayBuffer = await webmBlob.arrayBuffer()
    
    // Validate ArrayBuffer
    if (arrayBuffer.byteLength === 0) {
      throw new Error('ArrayBuffer is empty after blob conversion')
    }
    
    // Check for valid WebM header (EBML signature: 0x1A 0x45 0xDF 0xA3)
    const headerView = new Uint8Array(arrayBuffer.slice(0, 4))
    const isValidWebM = headerView[0] === 0x1A && headerView[1] === 0x45 && 
                        headerView[2] === 0xDF && headerView[3] === 0xA3
    
    if (!isValidWebM) {
      console.warn('[Audio Converter] WebM header validation failed, attempting decode anyway')
    }
    
    let audioBuffer: AudioBuffer
    try {
      audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
      console.log('[Audio Converter] Successfully decoded audio:', {
        duration: audioBuffer.duration,
        sampleRate: audioBuffer.sampleRate,
        channels: audioBuffer.numberOfChannels,
        length: audioBuffer.length
      })
    } catch (decodeError) {
      // Enhanced error message with debugging info
      const errorMsg = decodeError instanceof Error ? decodeError.message : 'Unknown decode error'
      console.error('[Audio Converter] Decode failed:', {
        error: errorMsg,
        blobSize: webmBlob.size,
        bufferSize: arrayBuffer.byteLength,
        hasValidHeader: isValidWebM,
        headerHex: Array.from(headerView).map(b => b.toString(16).padStart(2, '0')).join(' ')
      })
      throw new Error(`Failed to decode WebM audio (size: ${webmBlob.size}B). Possible causes: incomplete audio container, corrupted data, or unsupported codec. Try speaking longer or check microphone.`)
    }

    // Get audio data (convert to mono if stereo)
    let audioData: Float32Array
    if (audioBuffer.numberOfChannels > 1) {
      // Mix down to mono
      const left = audioBuffer.getChannelData(0)
      const right = audioBuffer.getChannelData(1)
      audioData = new Float32Array(left.length)
      for (let i = 0; i < left.length; i++) {
        audioData[i] = (left[i] + right[i]) / 2
      }
    } else {
      audioData = audioBuffer.getChannelData(0)
    }

    // Resample if needed
    let finalAudioData = audioData
    if (audioBuffer.sampleRate !== targetSampleRate) {
      finalAudioData = resampleAudio(audioData, audioBuffer.sampleRate, targetSampleRate)
    }

    // Convert Float32Array to Int16Array (WAV uses 16-bit PCM)
    const int16Data = new Int16Array(finalAudioData.length)
    for (let i = 0; i < finalAudioData.length; i++) {
      // Clamp to [-1, 1] and convert to 16-bit integer
      const s = Math.max(-1, Math.min(1, finalAudioData[i]))
      int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }

    // Create WAV file
    const wavBuffer = createWAVFile(int16Data, targetSampleRate)

    return wavBuffer
  } catch (error) {
    console.error('[Audio Converter] Failed to convert WebM to WAV:', error)
    throw new Error(`Audio conversion failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
  } finally {
    // CRITICAL: Always close audio context to prevent resource leaks
    if (audioContext) {
      try {
        await audioContext.close()
      } catch (closeError) {
        console.warn('[Audio Converter] Failed to close audio context:', closeError)
      }
    }
  }
}

/**
 * Simple linear resampling (for basic use cases)
 * For production, consider using a more sophisticated resampling library
 */
function resampleAudio(
  audioData: Float32Array,
  originalSampleRate: number,
  targetSampleRate: number
): Float32Array {
  if (originalSampleRate === targetSampleRate) {
    return audioData
  }

  const ratio = originalSampleRate / targetSampleRate
  const newLength = Math.round(audioData.length / ratio)
  const result = new Float32Array(newLength)

  for (let i = 0; i < newLength; i++) {
    const srcIndex = i * ratio
    const srcIndexInt = Math.floor(srcIndex)
    const frac = srcIndex - srcIndexInt

    // Linear interpolation
    if (srcIndexInt + 1 < audioData.length) {
      result[i] = audioData[srcIndexInt] * (1 - frac) + audioData[srcIndexInt + 1] * frac
    } else {
      result[i] = audioData[srcIndexInt]
    }
  }

  return result
}

/**
 * Create WAV file buffer from PCM data
 * WAV format: RIFF header + fmt chunk + data chunk
 */
function createWAVFile(pcmData: Int16Array, sampleRate: number): ArrayBuffer {
  const numChannels = 1 // Mono
  const bitsPerSample = 16
  const bytesPerSample = bitsPerSample / 8
  const blockAlign = numChannels * bytesPerSample
  const byteRate = sampleRate * blockAlign
  const dataSize = pcmData.length * bytesPerSample
  const fileSize = 44 + dataSize // 44 bytes WAV header + PCM data

  const buffer = new ArrayBuffer(fileSize)
  const view = new DataView(buffer)

  // RIFF chunk descriptor
  writeString(view, 0, 'RIFF')
  view.setUint32(4, fileSize - 8, true) // File size - 8
  writeString(view, 8, 'WAVE')

  // fmt sub-chunk
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true) // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true) // AudioFormat (1 for PCM)
  view.setUint16(22, numChannels, true) // NumChannels
  view.setUint32(24, sampleRate, true) // SampleRate
  view.setUint32(28, byteRate, true) // ByteRate
  view.setUint16(32, blockAlign, true) // BlockAlign
  view.setUint16(34, bitsPerSample, true) // BitsPerSample

  // data sub-chunk
  writeString(view, 36, 'data')
  view.setUint32(40, dataSize, true) // Subchunk2Size

  // Write PCM data
  const offset = 44
  for (let i = 0; i < pcmData.length; i++) {
    view.setInt16(offset + i * 2, pcmData[i], true)
  }

  return buffer
}

/**
 * Helper to write string to DataView
 */
function writeString(view: DataView, offset: number, string: string): void {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i))
  }
}

/**
 * Convert ArrayBuffer to Blob (for testing/debugging)
 */
export function arrayBufferToBlob(buffer: ArrayBuffer, mimeType: string = 'audio/wav'): Blob {
  return new Blob([buffer], { type: mimeType })
}

/**
 * Get audio info from WebM blob (for debugging)
 */
export async function getAudioInfo(blob: Blob): Promise<{
  duration: number
  sampleRate: number
  numberOfChannels: number
  length: number
}> {
  const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
  const arrayBuffer = await blob.arrayBuffer()
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
  
  const info = {
    duration: audioBuffer.duration,
    sampleRate: audioBuffer.sampleRate,
    numberOfChannels: audioBuffer.numberOfChannels,
    length: audioBuffer.length
  }
  
  await audioContext.close()
  return info
}
