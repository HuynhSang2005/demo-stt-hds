import React, { useState, useCallback, useEffect, useMemo } from 'react'
import { Mic, Square, Play, Pause, Settings, Volume2, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { config } from '@/lib/config'
import { useAudioRecorder } from '@/hooks/useAudioRecorder'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useSessionWebSocket } from '@/hooks/useSessionWebSocket'
import { useRMSHistory } from '@/hooks/useRMSHistory'
import { 
  useConnectionStatus,
  useCurrentSession, 
  useSessionActions,
  useTranscriptActions 
} from '@/stores/vietnameseSTT.store'
import { RecordingStatusIndicator } from './RecordingStatusIndicator'
import { SimpleWaveform } from './SimpleWaveform'
import type { TranscriptResult } from '@/types/transcript'

/**
 * Props for AudioRecorder component
 */
interface AudioRecorderProps {
  className?: string
  websocketUrl?: string
  showSettings?: boolean
  showVolumeIndicator?: boolean
  autoConnect?: boolean  // Currently unused but kept for future use
  onError?: (error: Error) => void
}

/**
 * Recording status indicator styles
 */
const getStatusStyles = (isRecording: boolean, isConnected: boolean) => {
  if (!isConnected) {
    return "bg-red-100 text-red-700 border-red-200"
  }
  
  if (isRecording) {
    return "bg-green-100 text-green-700 border-green-200"
  }
  
  return "bg-yellow-100 text-yellow-700 border-yellow-200"
}

/**
 * Format recording duration for display
 */
const formatDuration = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

/**
 * Volume level indicator component
 */
const VolumeIndicator: React.FC<{ volume: number }> = ({ volume }) => {
  const bars = Array.from({ length: 10 }, (_, i) => {
    const threshold = (i + 1) / 10
    const isActive = volume >= threshold
    
    return (
      <div
        key={i}
        className={cn(
          "w-1 transition-colors duration-150 rounded-full",
          isActive 
            ? volume > 0.7 ? "bg-red-500 h-4" :
              volume > 0.4 ? "bg-yellow-500 h-3" : "bg-green-500 h-2"
            : "bg-gray-300 h-1"
        )}
      />
    )
  })
  
  return (
    <div className="flex items-end gap-0.5 h-4">
      {bars}
    </div>
  )
}

/**
 * Vietnamese STT Audio Recorder Component
 * Handles audio recording, WebSocket communication, and real-time transcript processing
 */
export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  className,
  websocketUrl = config.backend.wsUrl,
  showSettings = true,
  showVolumeIndicator = true,
  autoConnect: _autoConnect = true,
  onError,
}) => {
  const [duration, setDuration] = useState(0)
  const [showDeviceSettings, setShowDeviceSettings] = useState(false)
  const [sessionMode, setSessionMode] = useState(true) // Session-based processing
  const [accumulatedChunks, setAccumulatedChunks] = useState<ArrayBuffer[]>([])
  const [isStarting, setIsStarting] = useState(false) // Prevent double-click
  
  // Store state
  const connectionStatus = useConnectionStatus()
  const currentSession = useCurrentSession()
  const { startSession, endSession, pauseSession, resumeSession } = useSessionActions()
  const { addTranscript } = useTranscriptActions()
  
  // Determine WebSocket URL based on mode
  const effectiveWebsocketUrl = sessionMode 
    ? websocketUrl.replace('/ws', '/ws/session')
    : websocketUrl
  
  // WebSocket event handlers - memoized to prevent infinite re-renders
  const handleTranscriptResult = useCallback((result: TranscriptResult) => {
    console.log('[AudioRecorder] Transcript received:', result)
    try {
      addTranscript(result)
      console.log('[AudioRecorder] Transcript added to store successfully')
    } catch (error) {
      console.error('[AudioRecorder] Error adding transcript to store:', error)
      throw error
    }
  }, [addTranscript])
  
  const handleConnectionStatusChange = useCallback((status: string, reason?: string) => {
    console.log('[AudioRecorder] WebSocket status:', status, reason)
  }, [])
  
  const handleWebSocketError = useCallback((event: Event) => {
    console.error('[AudioRecorder] WebSocket error:', event)
  }, [])
  
  // Audio recorder hook
  const {
    isRecording: audioRecording,
    processingState,
    currentVolume: volume,
    availableDevices: devices,
    selectedDevice,
    error: audioError,
    permissionGranted,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    selectDevice,
  } = useAudioRecorder({
    chunkDuration: 2000, // 2-second chunks
    enableVolumeDetection: true,
    onAudioChunk: async (chunk) => {
      // Handle different modes
      if (sessionMode) {
        // Session mode: accumulate chunks - convert Blob to ArrayBuffer
        let audioData: ArrayBuffer
        if (chunk.data instanceof Blob) {
          audioData = await chunk.data.arrayBuffer()
        } else {
          audioData = chunk.data as ArrayBuffer
        }
        setAccumulatedChunks(prev => [...prev, audioData])
        console.log('[AudioRecorder] Chunk accumulated for session, total chunks:', accumulatedChunks.length + 1, 'bytes:', audioData.byteLength)
      } else {
        // Real-time mode: send chunks immediately
        if (isConnected && chunk) {
          // Convert blob to ArrayBuffer for WebSocket transmission
          if (chunk.data instanceof Blob) {
            chunk.data.arrayBuffer().then((arrayBuffer: ArrayBuffer) => {
              sendAudioChunk(arrayBuffer, chunk.chunkIndex)
            }).catch(console.error)
          } else {
            // Already ArrayBuffer
            sendAudioChunk(chunk.data as ArrayBuffer, chunk.chunkIndex)
          }
        }
      }
    },
    onError: (error) => {
      console.error('[AudioRecorder] Recording error:', error)
      onError?.(new Error(error.message))
    },
  })
  
  // Calculate paused state
  const audioPaused = processingState === 'paused'
  
  // Track RMS history for waveform visualization (Phase 1 enhancement)
  const { rmsHistory, isVoiceDetected } = useRMSHistory({
    currentRMS: volume,
    isRecording: audioRecording,
    maxHistory: 20,
    updateInterval: 100,
  })
  
  // Stabilize websocketUrl to prevent useWebSocket re-creation
  const stableWebsocketUrl = useMemo(() => effectiveWebsocketUrl, [effectiveWebsocketUrl])
  
  // Memoize WebSocket options to prevent infinite re-renders
  const webSocketOptions = useMemo(() => ({
    autoReconnect: true, // Re-enable auto-reconnect 
    maxReconnectAttempts: 3, // Reduce attempts to prevent connection loops
    onTranscriptResult: handleTranscriptResult,
    onConnectionStatusChange: handleConnectionStatusChange,
    onError: handleWebSocketError,
    enableDebug: false,  // Disable debug for cleaner logs
  }), [handleTranscriptResult, handleConnectionStatusChange, handleWebSocketError])
  
  // WebSocket connection for Vietnamese STT - choose between session and real-time
  const sessionWebSocket = useSessionWebSocket(effectiveWebsocketUrl, webSocketOptions)
  const realtimeWebSocket = useWebSocket(stableWebsocketUrl, webSocketOptions)
  
  // Use appropriate WebSocket based on mode
  const {
    isConnected,
    sendAudioChunk,
    connect,
    lastError: wsError,
  } = sessionMode ? {
    isConnected: sessionWebSocket.isConnected,
    sendAudioChunk: sessionWebSocket.sendAudioChunk,
    connect: sessionWebSocket.connect,
    lastError: sessionWebSocket.lastError
  } : {
    isConnected: realtimeWebSocket.isConnected,
    sendAudioChunk: realtimeWebSocket.sendAudioChunk,
    connect: realtimeWebSocket.connect,
    lastError: realtimeWebSocket.lastError
  }
  
  // Duration timer
  useEffect(() => {
    let interval: number | undefined
    
    if (audioRecording && !audioPaused) {
      interval = setInterval(() => {
        setDuration(prev => prev + 1)
      }, 1000)
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [audioRecording, audioPaused])
  
  // Handle start recording
  const handleStartRecording = useCallback(async () => {
    try {
      if (!isConnected) {
        throw new Error('WebSocket not connected - please check server connection')
      }
      
      // Prevent double-click/double-start
      if (isStarting || audioRecording) {
        console.log('[AudioRecorder] Recording already starting or active, preventing duplicate')
        return
      }
      
      setIsStarting(true)
      
      // Start audio recording
      await startRecording()
      
      // Start session in store
      const sessionId = startSession()
      console.log('[AudioRecorder] Started recording session:', sessionId)
      
      // If session mode, start backend session
      if (sessionMode) {
        try {
          const backendSessionId = await sessionWebSocket.startSession()
          console.log('[AudioRecorder] Started backend session:', backendSessionId)
        } catch (error) {
          console.warn('[AudioRecorder] Failed to start backend session:', error)
        }
      }
      
      setDuration(0)
      setAccumulatedChunks([]) // Clear any previous chunks
    } catch (error) {
      console.error('[AudioRecorder] Failed to start recording:', error)
      onError?.(error as Error)
    } finally {
      setIsStarting(false)
    }
  }, [isConnected, startRecording, startSession, onError, sessionMode, sessionWebSocket, isStarting, audioRecording])
  
  // Handle stop recording
  const handleStopRecording = useCallback(async () => {
    try {
      // Stop audio recording
      stopRecording()
      
      // Session mode: process accumulated chunks and end session
      if (sessionMode && accumulatedChunks.length > 0) {
        console.log('[AudioRecorder] Processing session with', accumulatedChunks.length, 'chunks')
        
        try {
          // Send all accumulated chunks
          for (const chunk of accumulatedChunks) {
            sessionWebSocket.sendAudioChunk(chunk, 0)
          }
          
          // CRITICAL FIX (Bug 1): endSession() RETURNS transcript via Promise
          // Must explicitly handle the result to display transcript in UI
          const transcriptResult = await sessionWebSocket.endSession()
          console.log('[AudioRecorder] Backend session ended, transcript:', transcriptResult)
          
          // BUG FIX: Call handleTranscriptResult with the returned transcript
          // This ensures transcript is added to store even if WebSocket message is missed
          if (transcriptResult) {
            console.log('[AudioRecorder] Adding transcript from Promise return value')
            handleTranscriptResult(transcriptResult)
          } else {
            console.warn('[AudioRecorder] No transcript returned from endSession()')
          }
        } catch (error) {
          console.error('[AudioRecorder] Failed to process session:', error)
        }
        
        // Clear accumulated chunks
        setAccumulatedChunks([])
      }
      
      // End session in store
      if (currentSession) {
        endSession(currentSession.id)
      }
      
      console.log('[AudioRecorder] Stopped recording')
    } catch (error) {
      console.error('[AudioRecorder] Failed to stop recording:', error)
      onError?.(error as Error)
    }
  }, [stopRecording, endSession, currentSession, onError, sessionMode, accumulatedChunks, sessionWebSocket, handleTranscriptResult])
  
  // Handle pause/resume
  const handlePauseResume = useCallback(() => {
    try {
      if (audioPaused) {
        resumeRecording()
        if (currentSession) {
          resumeSession(currentSession.id)
        }
      } else {
        pauseRecording()
        if (currentSession) {
          pauseSession(currentSession.id)
        }
      }
    } catch (error) {
      console.error('[AudioRecorder] Failed to pause/resume:', error)
      onError?.(error as Error)
    }
  }, [audioPaused, resumeRecording, pauseRecording, currentSession, resumeSession, pauseSession, onError])
  
  // Handle device selection
  const handleDeviceSelect = useCallback((deviceId: string) => {
    selectDevice(deviceId)
    setShowDeviceSettings(false)
  }, [selectDevice])
  
  // audioPaused already calculated above
  
  // Connection status text
  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Đã kết nối'
      case 'connecting': return 'Đang kết nối...'
      case 'reconnecting': return 'Đang kết nối lại...'
      case 'disconnected': return 'Chưa kết nối'
      case 'failed': return 'Kết nối thất bại'
      default: return 'Không xác định'
    }
  }
  
  return (
    <div className={cn("bg-white rounded-lg shadow-lg border border-gray-200 p-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">
          Ghi âm tiếng Việt
        </h2>
        
        <div className="flex items-center gap-3">
          {/* Session Mode Toggle */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">
              Session Mode:
            </label>
            <button
              onClick={() => setSessionMode(!sessionMode)}
              disabled={audioRecording}
              className={cn(
                "px-3 py-1 text-xs font-medium rounded-full border transition-colors",
                sessionMode 
                  ? "bg-blue-100 text-blue-700 border-blue-300" 
                  : "bg-gray-100 text-gray-700 border-gray-300",
                audioRecording ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:opacity-80"
              )}
            >
              {sessionMode ? "Session" : "Real-time"}
            </button>
          </div>
          
          {/* Settings button */}
          {showSettings && (
            <button
              onClick={() => setShowDeviceSettings(!showDeviceSettings)}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
      
      {/* Connection status */}
      <div className="mb-4">
        <div className={cn(
          "inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium border",
          getStatusStyles(audioRecording, isConnected)
        )}>
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-green-500" : "bg-red-500"
          )} />
          <span>{getConnectionStatusText()}</span>
        </div>
        
        {/* Error indicators */}
        {(audioError || wsError) && (
          <div className="mt-2 flex items-center gap-2 text-sm text-red-600">
            <AlertTriangle className="w-4 h-4" />
            <span>
              {audioError?.message || (wsError && 'WebSocket connection error')}
            </span>
          </div>
        )}
      </div>
      
      {/* Recording Status Indicator - Phase 1 Enhancement */}
      <div className="mb-4">
        <RecordingStatusIndicator
          isRecording={audioRecording}
          currentVolume={volume}
          isVoiceDetected={isVoiceDetected}
        />
      </div>
      
      {/* Recording controls - Enhanced for Phase 1 */}
      <div className="flex items-center justify-center gap-4 mb-6">
        {!audioRecording ? (
          // Start recording button - Enhanced with gradient and larger size
          <button
            onClick={handleStartRecording}
            disabled={!isConnected || isStarting}
            className={cn(
              "flex items-center justify-center rounded-full transition-all duration-300 relative group",
              // Phase 1 Enhancement: Larger button (20x20 -> 80px x 80px)
              "w-20 h-20",
              isConnected && !isStarting
                ? "bg-gradient-to-br from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white hover:scale-110 shadow-xl hover:shadow-2xl"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            )}
          >
            {/* Pulse effect when ready */}
            {isConnected && !isStarting && (
              <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-20" />
            )}
            <Mic className="w-10 h-10 relative z-10" />
          </button>
        ) : (
          // Recording controls
          <div className="flex items-center gap-4">
            {/* Pause/Resume */}
            <button
              onClick={handlePauseResume}
              className="flex items-center justify-center w-14 h-14 rounded-full bg-yellow-500 hover:bg-yellow-600 text-white transition-all duration-200 hover:scale-105 shadow-lg"
            >
              {audioPaused ? <Play className="w-7 h-7" /> : <Pause className="w-7 h-7" />}
            </button>
            
            {/* Stop */}
            <button
              onClick={handleStopRecording}
              className="flex items-center justify-center w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 text-white transition-all duration-200 hover:scale-105 shadow-lg"
            >
              <Square className="w-7 h-7 fill-current" />
            </button>
          </div>
        )}
      </div>
      
      {/* Recording status and duration */}
      {audioRecording && (
        <div className="text-center mb-4">
          <div className="text-2xl font-mono font-bold text-gray-900 mb-2">
            {formatDuration(duration)}
          </div>
          <div className={cn(
            "text-sm font-medium",
            audioPaused ? "text-yellow-600" : "text-red-600"
          )}>
            {audioPaused ? "Tạm dừng" : "Đang ghi âm..."}
          </div>
        </div>
      )}
      
      {/* Waveform Visualizer - Phase 1 Enhancement */}
      <div className="mb-4">
        <SimpleWaveform
          rmsValues={rmsHistory}
          isRecording={audioRecording}
          isVoiceDetected={isVoiceDetected}
          barCount={20}
        />
      </div>
      
      {/* Volume indicator */}
      {showVolumeIndicator && audioRecording && (
        <div className="flex items-center justify-center gap-3 mb-4">
          <Volume2 className="w-5 h-5 text-gray-500" />
          <VolumeIndicator volume={volume} />
          <span className="text-sm text-gray-500 font-mono min-w-[3ch]">
            {Math.round(volume * 100)}%
          </span>
        </div>
      )}
      
      {/* Device settings */}
      {showDeviceSettings && (
        <div className="border-t border-gray-200 pt-4 mt-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Chọn thiết bị ghi âm
          </h3>
          
          {!permissionGranted || devices.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-sm text-gray-500 mb-3">
                {!permissionGranted ? "Chưa có quyền truy cập microphone" : "Không tìm thấy thiết bị ghi âm"}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
              >
                Làm mới
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {devices.map((device: MediaDeviceInfo) => (
                <button
                  key={device.deviceId}
                  onClick={() => handleDeviceSelect(device.deviceId)}
                  className={cn(
                    "w-full text-left p-3 rounded-lg border transition-colors text-sm",
                    selectedDevice?.deviceId === device.deviceId
                      ? "border-blue-500 bg-blue-50 text-blue-900"
                      : "border-gray-200 hover:border-gray-300 text-gray-900"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Mic className="w-4 h-4" />
                    <span className="font-medium">
                      {device.label || `Microphone ${device.deviceId.slice(0, 8)}...`}
                    </span>
                    {selectedDevice?.deviceId === device.deviceId && (
                      <span className="ml-auto text-xs text-blue-600">
                        ✓ Đang sử dụng
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Connection retry button */}
      {!isConnected && (
        <div className="text-center border-t border-gray-200 pt-4 mt-4">
          <button
            onClick={connect}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
          >
            Kết nối
          </button>
        </div>
      )}
    </div>
  )
}

export default AudioRecorder