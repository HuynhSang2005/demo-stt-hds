/**
 * useAudioRecorder Hook - Simplified Version for Vietnamese STT
 * 
 * Custom React hook for audio recording with MediaRecorder API
 * Optimized for Vietnamese Speech-to-Text processing with real-time features
 */

import { useState, useRef, useCallback, useEffect, useMemo } from 'react'
import type { 
  UseAudioRecorderReturn, 
  AudioRecorderConfig, 
  AudioChunk, 
  RecordingState, 
  AudioError 
} from '@/types/audio'

/**
 * Audio recorder hook configuration options
 */
export interface UseAudioRecorderOptions {
  /** Callback when audio chunk is available for processing */
  onAudioChunk?: (chunk: AudioChunk) => void | Promise<void>
  /** Callback when recording starts */
  onRecordingStart?: () => void
  /** Callback when recording stops */
  onRecordingStop?: () => void
  /** Callback when error occurs */
  onError?: (error: AudioError) => void
  /** Callback when volume level changes */
  onVolumeChange?: (volume: number) => void
  /** Callback when permission state changes */
  onPermissionChange?: (granted: boolean) => void
  
  /** Duration of each audio chunk in milliseconds (default: 2000ms for Vietnamese STT) */
  chunkDuration?: number
  /** Enable real-time volume detection */
  enableVolumeDetection?: boolean
  /** Maximum recording time in milliseconds */
  maxRecordingTime?: number
  /** Auto-start recording when initialized */
  autoStart?: boolean
  /** Preferred audio device ID */
  deviceId?: string
  /** Custom audio recorder configuration */
  config?: Partial<AudioRecorderConfig>
}

/**
 * Default audio configuration optimized for Vietnamese STT
 * Task 7 Optimizations:
 * - Changed to Opus codec for 30-40% better compression
 * - Reduced chunk duration from 2000ms to 1000ms for lower latency
 * - Prepared for VAD (Voice Activity Detection) integration
 */
const DEFAULT_VIETNAMESE_STT_CONFIG: AudioRecorderConfig = {
  format: {
    mimeType: 'audio/webm;codecs=opus', // Opus codec for superior compression & quality
    sampleRate: 16000, // Required for Wav2Vec2 Vietnamese model
    channels: 1, // Mono audio for better processing
  },
  chunkConfig: {
    chunkDuration: 1000, // 1 second for lower latency (Task 7 optimization)
    maxChunkSize: 1024 * 256, // 256KB max chunk size (reduced for 1s chunks)
    overlap: 0.1, // 10% overlap for smoother processing
    bufferSize: 4096, // Audio buffer size
  },
  autoStart: false,
  enableNoiseReduction: true,
  echoCancellation: true,
  maxRecordingTime: 300000, // 5 minutes maximum
}

/**
 * Create audio error object
 */
const createAudioError = (
  code: AudioError['code'],
  message: string,
  details?: Record<string, unknown>
): AudioError => ({
  code,
  message,
  details,
})

/**
 * Vietnamese STT optimized audio recorder hook
 */
export function useAudioRecorder(options: UseAudioRecorderOptions = {}): UseAudioRecorderReturn {
  const {
    onAudioChunk,
    onRecordingStart,
    onRecordingStop,
    onError,
    onVolumeChange,
    onPermissionChange,
    chunkDuration = 1000, // Task 7: Changed from 2000ms to 1000ms for lower latency
    enableVolumeDetection = true,
    maxRecordingTime = 300000,
    autoStart = false,
    deviceId,
    config: customConfig = {}
  } = options

  // Merge custom config with defaults
  const config: AudioRecorderConfig = useMemo(() => ({
    ...DEFAULT_VIETNAMESE_STT_CONFIG,
    ...customConfig,
    chunkConfig: {
      ...DEFAULT_VIETNAMESE_STT_CONFIG.chunkConfig,
      ...customConfig.chunkConfig,
      chunkDuration,
    },
  }), [customConfig, chunkDuration])

  // State management
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingState, setProcessingState] = useState<RecordingState>('inactive')
  const [audioChunks, setAudioChunks] = useState<AudioChunk[]>([])
  const [currentVolume, setCurrentVolume] = useState(0)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [availableDevices, setAvailableDevices] = useState<MediaDeviceInfo[]>([])
  const [selectedDevice, setSelectedDevice] = useState<MediaDeviceInfo | null>(null)
  const [error, setError] = useState<AudioError | null>(null)
  const [permissionGranted, setPermissionGranted] = useState(false)

  // Refs for audio context and timers
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const recordingTimerRef = useRef<number | null>(null)
  const volumeDetectionRef = useRef<number | null>(null)
  const startTimeRef = useRef<number>(0)
  const chunkIndexRef = useRef<number>(0)

  /**
   * Get available audio devices
   */
  const getAvailableDevices = useCallback(async (): Promise<MediaDeviceInfo[]> => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      const audioInputs = devices.filter(device => device.kind === 'audioinput')
      
      setAvailableDevices(audioInputs)
      
      // Auto-select first device if none selected
      if (audioInputs.length > 0 && !selectedDevice) {
        setSelectedDevice(audioInputs[0])
      }
      
      return audioInputs
    } catch (err) {
      console.error('Failed to get available devices:', err)
      return []
    }
  }, [selectedDevice])

  /**
   * Get media stream with Vietnamese STT optimized constraints
   */
  const getMediaStream = useCallback(async (preferredDeviceId?: string): Promise<MediaStream | null> => {
    try {
      // Stop any existing stream first to avoid resource conflicts
      if (mediaStreamRef.current) {
        console.log('[AudioRecorder] Stopping previous stream before creating new one')
        mediaStreamRef.current.getTracks().forEach(track => track.stop())
        mediaStreamRef.current = null
      }

      const constraints: MediaStreamConstraints = {
        audio: {
          deviceId: preferredDeviceId ? { exact: preferredDeviceId } : undefined,
          // CRITICAL FIX: Disable aggressive audio processing on Bluetooth headsets
          // These features reduce amplitude too much, causing low RMS values
          sampleRate: { ideal: 48000 },  // Higher sample rate for better quality
          channelCount: config.format.channels,
          echoCancellation: false,  // Changed from true - reduces amplitude
          noiseSuppression: false,  // Changed from true - kills voice activity
          autoGainControl: false,   // Changed from true - Bluetooth has its own AGC
        },
        video: false,
      }

      console.log('[AudioRecorder] Requesting new media stream with constraints:', constraints)
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      console.log('[AudioRecorder] Got new stream:', stream.id, 'with', stream.getAudioTracks().length, 'audio tracks')
      
      setPermissionGranted(true)
      onPermissionChange?.(true)
      
      return stream
    } catch (err) {
      let audioError: AudioError

      if (err instanceof Error) {
        switch (err.name) {
          case 'NotAllowedError':
            audioError = createAudioError(
              'PERMISSION_DENIED',
              'Microphone permission denied. Please allow microphone access to use Vietnamese STT.',
              { error: err }
            )
            break
          case 'NotFoundError':
            audioError = createAudioError(
              'DEVICE_NOT_FOUND',
              'No microphone device found. Please connect a microphone.',
              { error: err }
            )
            break
          default:
            audioError = createAudioError(
              'RECORDING_FAILED',
              `Failed to access microphone: ${err.message}`,
              { error: err }
            )
        }
      } else {
        audioError = createAudioError(
          'RECORDING_FAILED',
          'Unknown error accessing microphone',
          { error: err }
        )
      }

      setError(audioError)
      setPermissionGranted(false)
      onError?.(audioError)
      onPermissionChange?.(false)
      return null
    }
  }, [config, onError, onPermissionChange])

  /**
   * Setup audio context for volume detection
   */
  const setupAudioContext = useCallback((stream: MediaStream) => {
    if (!enableVolumeDetection) return

    try {
      // Clean up existing audio context if any
      if (audioContextRef.current) {
        try {
          audioContextRef.current.close()
        } catch (err) {
          console.warn('[AudioRecorder] Failed to close previous audio context:', err)
        }
      }

      const audioContext = new (window.AudioContext || (window as typeof window & { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
      const analyser = audioContext.createAnalyser()
      const source = audioContext.createMediaStreamSource(stream)
      
      // CRITICAL FIX: Add gain node to amplify low-amplitude Bluetooth audio
      // Bluetooth headsets often have aggressive noise suppression
      const gainNode = audioContext.createGain()
      gainNode.gain.value = 2.5  // Amplify by 2.5x for better VAD detection
      
      // Optimized for time-domain VAD (waveform analysis)
      analyser.fftSize = 2048 // Increased from 256 for better time resolution
      analyser.smoothingTimeConstant = 0.1 // Further reduced for instant response
      
      // Audio chain: source → gain → analyser
      source.connect(gainNode)
      gainNode.connect(analyser)

      audioContextRef.current = audioContext
      analyserRef.current = analyser

      console.log('[AudioRecorder] Audio context initialized for stream:', stream.id)

      // Start volume detection
      const detectVolume = () => {
        if (!analyserRef.current) return

        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
        analyserRef.current.getByteFrequencyData(dataArray)

        // Calculate RMS volume
        let sum = 0
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i] * dataArray[i]
        }
        const rms = Math.sqrt(sum / dataArray.length)
        const volume = Math.min(1, rms / 128) // Normalize to 0-1

        setCurrentVolume(volume)
        onVolumeChange?.(volume)

        if (isRecording) {
          volumeDetectionRef.current = window.setTimeout(detectVolume, 100)
        }
      }

      detectVolume()
    } catch (err) {
      console.warn('Failed to setup audio context for volume detection:', err)
    }
  }, [enableVolumeDetection, isRecording, onVolumeChange])

  /**
   * Check if audio chunk contains voice activity (VAD)
   * Task 7: Skip silent chunks to reduce bandwidth and processing
   * 
   * IMPROVED: Uses time-domain analysis (waveform amplitude) instead of frequency-domain
   * This works MUCH BETTER for detecting high-pitch voices and abnormal tones
   */
  const checkVoiceActivity = useCallback((): boolean => {
    if (!analyserRef.current) return true // If no analyser, process all chunks

    // Use TIME-DOMAIN data (waveform) instead of FREQUENCY-DOMAIN
    // This is more reliable for detecting ALL types of voices
    const bufferLength = analyserRef.current.fftSize
    const dataArray = new Uint8Array(bufferLength)
    analyserRef.current.getByteTimeDomainData(dataArray) // Changed from getByteFrequencyData!

    // Calculate RMS (Root Mean Square) energy from waveform amplitude
    let sum = 0
    let maxAmplitude = 0
    for (let i = 0; i < dataArray.length; i++) {
      // Convert from Uint8 (0-255, centered at 128) to amplitude (-128 to +127)
      const amplitude = dataArray[i] - 128
      sum += amplitude * amplitude
      maxAmplitude = Math.max(maxAmplitude, Math.abs(amplitude))
    }
    let rms = Math.sqrt(sum / dataArray.length)
    
    // CRITICAL FIX: Apply gain compensation for low-amplitude Bluetooth audio
    // Bluetooth headsets often have aggressive noise suppression that reduces amplitude
    // Amplify the RMS by 2x to compensate
    rms = rms * 2.0

    // ULTRA-SENSITIVE threshold for Bluetooth headsets with heavy audio processing
    // Original: 15 (too high) → 5 (still too high for BT) → 3 (catches everything)
    // With 2x gain compensation, effective threshold is ~1.5 raw RMS
    const VAD_THRESHOLD = 3
    const hasVoice = rms > VAD_THRESHOLD
    
    // Additional check: if max amplitude is high, definitely has voice
    const hasHighPeak = maxAmplitude > 10
    const finalHasVoice = hasVoice || hasHighPeak

    debugLog(`VAD check: RMS=${rms.toFixed(2)} (max=${maxAmplitude.toFixed(1)}), hasVoice=${finalHasVoice}`)
    return finalHasVoice
  }, [])

  /**
   * Debug logging helper (defined inline for VAD)
   */
  const debugLog = useCallback((message: string) => {
    // Only log in development mode (Vite sets import.meta.env.DEV)
    if (import.meta.env.DEV) {
      console.log(`[AudioRecorder] ${message}`)
    }
  }, [])

  /**
   * Create audio chunk from blob data
   */
  const createAudioChunk = useCallback((data: Blob): AudioChunk => {
    const timestamp = Date.now()
    const sessionId = `session-${startTimeRef.current}`
    const chunkIndex = chunkIndexRef.current++
    const duration = timestamp - startTimeRef.current

    return {
      data: data,
      chunkIndex,
      timestamp,
      duration,
      size: data.size,
      sessionId,
    }
  }, [])

  /**
   * Stop audio recording
   */
  const stopRecording = useCallback((): void => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }

    // Stop all tracks
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
      mediaStreamRef.current = null
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Clear timers
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current)
      recordingTimerRef.current = null
    }

    if (volumeDetectionRef.current) {
      clearTimeout(volumeDetectionRef.current)
      volumeDetectionRef.current = null
    }

    setCurrentVolume(0)
    setRecordingDuration(0)
    setIsRecording(false)
    setProcessingState('inactive')
  }, [])

  /**
   * Start audio recording
   */
  const startRecording = useCallback(async (): Promise<void> => {
    try {
      setError(null)
      setIsProcessing(true)
      setProcessingState('recording')

      // Get media stream
      const stream = await getMediaStream(deviceId || selectedDevice?.deviceId)
      if (!stream) {
        setIsProcessing(false)
        setProcessingState('inactive')
        return
      }

      // Verify audio track is active
      const audioTracks = stream.getAudioTracks()
      if (audioTracks.length === 0) {
        throw new Error('No audio tracks found in media stream')
      }
      
      const activeTrack = audioTracks.find(track => track.enabled && track.readyState === 'live')
      if (!activeTrack) {
        throw new Error('No active audio track found')
      }

      console.log('[AudioRecorder] Starting with active audio track:', {
        label: activeTrack.label,
        enabled: activeTrack.enabled,
        readyState: activeTrack.readyState,
        settings: activeTrack.getSettings()
      })

      mediaStreamRef.current = stream

      // Setup audio context for volume detection
      setupAudioContext(stream)

      // Determine best supported audio format for Vietnamese STT
      // Task 7: Prioritize Opus codec for best compression/quality balance
      let mimeType = config.format.mimeType
      const supportedTypes = [
        'audio/webm;codecs=opus', // Best option: ~30-40% better compression than WAV
        'audio/webm;codecs=pcm',  // Fallback: uncompressed but compatible
        'audio/wav',               // Fallback: widely supported
        'audio/mp4;codecs=mp4a.40.2' // Fallback: AAC codec
      ]
      
      // Use first supported format if current format not supported
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = supportedTypes.find(type => MediaRecorder.isTypeSupported(type)) || mimeType
        console.log(`[AudioRecorder] Using fallback format: ${mimeType}`)
      }

      // Create MediaRecorder with Vietnamese STT optimized settings
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      })

      // Setup event handlers
      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          // Task 7: Check voice activity before processing chunk
          const hasVoice = checkVoiceActivity()
          
          if (!hasVoice) {
            debugLog(`Skipping silent chunk (size: ${event.data.size} bytes)`)
            return // Skip silent chunks to save bandwidth
          }

          const chunk = createAudioChunk(event.data)
          
          setAudioChunks(prev => [...prev, chunk])
          onAudioChunk?.(chunk)
        }
      }

      mediaRecorder.onstart = () => {
        startTimeRef.current = Date.now()
        chunkIndexRef.current = 0
        setIsRecording(true)
        setIsProcessing(false)
        onRecordingStart?.()

        // Start recording duration timer
        recordingTimerRef.current = window.setInterval(() => {
          setRecordingDuration(Date.now() - startTimeRef.current)
        }, 100)

        // Auto-stop after max recording time
        setTimeout(() => {
          if (mediaRecorderRef.current?.state === 'recording') {
            stopRecording()
          }
        }, maxRecordingTime)
      }

      mediaRecorder.onstop = () => {
        setIsRecording(false)
        setProcessingState('inactive')
        
        if (recordingTimerRef.current) {
          clearInterval(recordingTimerRef.current)
          recordingTimerRef.current = null
        }

        onRecordingStop?.()
      }

      mediaRecorder.onerror = (event) => {
        const audioError = createAudioError(
          'RECORDING_FAILED',
          'Recording failed due to MediaRecorder error',
          { event }
        )
        setError(audioError)
        onError?.(audioError)
      }

      mediaRecorderRef.current = mediaRecorder

      // Start recording with chunking
      mediaRecorder.start(chunkDuration)

    } catch (err) {
      const audioError = createAudioError(
        'RECORDING_FAILED',
        err instanceof Error ? err.message : 'Failed to start recording',
        { error: err }
      )
      
      setError(audioError)
      setIsProcessing(false)
      setProcessingState('inactive')
      onError?.(audioError)
    }
  }, [
    deviceId,
    selectedDevice,
    config,
    chunkDuration,
    maxRecordingTime,
    getMediaStream,
    setupAudioContext,
    createAudioChunk,
    onAudioChunk,
    onRecordingStart,
    onRecordingStop,
    onError,
    stopRecording
  ])

  /**
   * Pause recording
   */
  const pauseRecording = useCallback((): void => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause()
      setProcessingState('paused')
    }
  }, [])

  /**
   * Resume recording
   */
  const resumeRecording = useCallback((): void => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume()
      setProcessingState('recording')
    }
  }, [])

  /**
   * Select audio device
   */
  const selectDevice = useCallback((deviceId: string): void => {
    const device = availableDevices.find((d: MediaDeviceInfo) => d.deviceId === deviceId)
    setSelectedDevice(device || null)
  }, [availableDevices])

  /**
   * Cleanup resources
   */
  const cleanup = useCallback((): void => {
    stopRecording()
    setAudioChunks([])
    setError(null)
    setAvailableDevices([])
    setSelectedDevice(null)
  }, [stopRecording])

  // Initialize devices on mount
  useEffect(() => {
    getAvailableDevices()
  }, [getAvailableDevices])

  // Handle auto-start separately to avoid circular dependencies
  useEffect(() => {
    if (autoStart) {
      startRecording()
    }
  }, [autoStart, startRecording])

  // FIX #4: Auto-detect audio devices on mount
  useEffect(() => {
    let isMounted = true // Prevent state updates after unmount
    
    const detectDevices = async () => {
      try {
        console.log('[useAudioRecorder] Auto-detecting audio devices...')
        
        // Request permission first to get device labels
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        
        if (!isMounted) {
          stream.getTracks().forEach(track => track.stop())
          return
        }
        
        // Enumerate devices after permission granted
        const allDevices = await navigator.mediaDevices.enumerateDevices()
        const audioInputs = allDevices.filter(device => device.kind === 'audioinput')
        
        console.log('[useAudioRecorder] Found audio devices:', audioInputs.length)
        
        if (isMounted) {
          setAvailableDevices(audioInputs)
          
          // Auto-select default device
          const defaultDevice = audioInputs.find(d => d.deviceId === 'default') || audioInputs[0]
          if (defaultDevice) {
            setSelectedDevice(defaultDevice)
            console.log('[useAudioRecorder] Auto-selected device:', defaultDevice.label)
          }
          
          setPermissionGranted(true)
          onPermissionChange?.(true)
        }
        
        // Stop the permission stream (we'll create new one when recording)
        stream.getTracks().forEach(track => track.stop())
      } catch (err) {
        console.error('[useAudioRecorder] Device detection failed:', err)
        
        if (isMounted) {
          const audioError = createAudioError(
            'PERMISSION_DENIED',
            'Không thể truy cập thiết bị thu âm. Vui lòng cấp quyền microphone.',
            { error: err }
          )
          
          setError(audioError)
          setPermissionGranted(false)
          onPermissionChange?.(false)
          onError?.(audioError)
        }
      }
    }
    
    detectDevices()
    
    return () => {
      isMounted = false
    }
  }, []) // Empty dependency array - run only once on mount

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Direct cleanup without circular dependencies
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }
      
      // Stop all tracks
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop())
      }
      
      // Close audio context
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
      
      // Clear timers
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
      
      if (volumeDetectionRef.current) {
        clearTimeout(volumeDetectionRef.current)
      }
    }
  }, []) // Empty dependency array for unmount cleanup

  // Return hook interface
  return {
    // Recording state
    isRecording,
    isProcessing,
    processingState,
    
    // Recording controls
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    
    // Audio data
    audioChunks,
    currentVolume,
    recordingDuration,
    
    // Device management
    availableDevices,
    selectedDevice,
    selectDevice,
    
    // Error handling
    error,
    permissionGranted,
    
    // Cleanup
    cleanup,
  }
}

export default useAudioRecorder