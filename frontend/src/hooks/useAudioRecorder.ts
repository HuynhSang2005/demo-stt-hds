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
 */
const DEFAULT_VIETNAMESE_STT_CONFIG: AudioRecorderConfig = {
  format: {
    mimeType: 'audio/wav', // Changed to WAV for better torchaudio compatibility
    sampleRate: 16000, // Required for Wav2Vec2 Vietnamese model
    channels: 1, // Mono audio for better processing
  },
  chunkConfig: {
    chunkDuration: 2000, // 2 seconds for real-time processing
    maxChunkSize: 1024 * 512, // 512KB max chunk size
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
    chunkDuration = 2000,
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
      const constraints: MediaStreamConstraints = {
        audio: {
          deviceId: preferredDeviceId ? { exact: preferredDeviceId } : undefined,
          sampleRate: config.format.sampleRate,
          channelCount: config.format.channels,
          echoCancellation: config.echoCancellation,
          noiseSuppression: config.enableNoiseReduction,
          autoGainControl: true,
        },
        video: false,
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
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
      const audioContext = new (window.AudioContext || (window as typeof window & { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
      const analyser = audioContext.createAnalyser()
      const source = audioContext.createMediaStreamSource(stream)
      
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.8
      source.connect(analyser)

      audioContextRef.current = audioContext
      analyserRef.current = analyser

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

      mediaStreamRef.current = stream

      // Setup audio context for volume detection
      setupAudioContext(stream)

      // Determine best supported audio format for Vietnamese STT
      let mimeType = config.format.mimeType
      const supportedTypes = [
        'audio/wav',
        'audio/webm;codecs=pcm',
        'audio/webm;codecs=opus',
        'audio/mp4;codecs=mp4a.40.2'
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