/**
 * AudioRecorder Component
 * Main audio recording component for Vietnamese STT with session management
 *
 * Handles real-time audio recording, WebSocket streaming, and session management.
 * Integrates with Vietnamese STT backend for live transcription and toxic content detection.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useAudioRecorder } from '@/hooks/useAudioRecorder'
import { useSessionWebSocket } from '@/hooks/useSessionWebSocket'
import { useVietnameseSTTStore } from '@/stores/vietnameseSTT.store'
import { RecordingStatusIndicator } from './RecordingStatusIndicator'
import { SimpleWaveform } from './SimpleWaveform'
// REMOVED: convertWebMToWAV - Backend handles WebM/Opus directly via FFmpeg
import type { AudioError, AudioChunk } from '@/types/audio'
import type { TranscriptResult } from '@/types/transcript'
import type { AudioRecorderProps } from '@/types/component-props'

export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  websocketUrl,
  onError,
  className = '',
  showSettings = true,
  showVolumeIndicator = true,
  autoConnect = false,
}) => {
  const addTranscript = useVietnameseSTTStore((state) => state.addTranscript)
  const startStoreSession = useVietnameseSTTStore((state) => state.startSession)
  const endStoreSession = useVietnameseSTTStore((state) => state.endSession)
  const [sessionMode, setSessionMode] = useState(true)
  const [accumulatedChunks, setAccumulatedChunks] = useState<AudioChunk[]>([])
  const [currentSession, setCurrentSession] = useState<{ id: string } | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [rmsHistory, setRmsHistory] = useState<number[]>([])
  const [isVoiceDetected, setIsVoiceDetected] = useState(false)

  const handleTranscriptResult = useCallback((result: TranscriptResult) => {
    console.log('[AudioRecorder] Processing transcript result:', result)
    
    if (!result || !result.text) {
      console.warn('[AudioRecorder] Empty transcript result, skipping')
      return
    }

    // Store handles transformation automatically
    addTranscript(result)

    console.log('[AudioRecorder] Transcript added to store')
  }, [addTranscript])

  // Stable callbacks for WebSocket to prevent reconnection loops
  const handleWSTranscriptResult = useCallback((result: TranscriptResult) => {
    console.log('[AudioRecorder] Transcript received via WebSocket:', result)
    handleTranscriptResult(result)
  }, [handleTranscriptResult])

  const handleWSError = useCallback((err: Event) => {
    console.error('[AudioRecorder] WebSocket error:', err)
    onError?.(err instanceof Error ? err : new Error(String(err)))
  }, [onError])

  const {
    startRecording,
    stopRecording,
    isRecording,
    currentVolume,
    error: audioError,
    permissionGranted,
    availableDevices,
    selectedDevice,
    selectDevice,
  } = useAudioRecorder({
    onAudioChunk: async (chunk: AudioChunk) => {
      if (sessionMode) {
        setAccumulatedChunks((prev) => [...prev, chunk])
      }
    },
    onRecordingStart: () => {
      console.log('[AudioRecorder] Recording started')
      setRmsHistory([])
    },
    onRecordingStop: () => {
      console.log('[AudioRecorder] Recording stopped')
      setRmsHistory([])
      setIsVoiceDetected(false)
    },
    onError: (err: AudioError) => {
      console.error('[AudioRecorder] Audio error:', err)
      onError?.(new Error(err.message))
    },
    onVolumeChange: (volume: number) => {
      // Debug logging (10% sample rate to avoid spam)
      if (import.meta.env.DEV && Math.random() < 0.1) {
        console.log(`[AudioRecorder] 🔊 onVolumeChange: ${(volume * 100).toFixed(1)}%`)
      }
      
      setRmsHistory((prev) => {
        const newHistory = [...prev, volume]
        return newHistory.slice(-20)
      })
      setIsVoiceDetected(volume > 0.05)
    },
    enableVolumeDetection: showVolumeIndicator,
    chunkDuration: 1000,
  })

  // Session WebSocket for backend communication
  const sessionWebSocket = useSessionWebSocket(websocketUrl, {
    onTranscriptResult: handleWSTranscriptResult,
    onConnectionStatusChange: (status, message) => {
      console.log('[AudioRecorder] WebSocket status:', status, message)
    },
    onError: handleWSError,
    autoReconnect: true,
    enableDebug: import.meta.env.DEV
  })

  // FIX INFINITY LOOP: Auto-connect ONCE on mount if enabled
  // Use ref to prevent re-runs when sessionWebSocket object changes
  const hasAutoConnectedRef = useRef(false)
  const sessionWebSocketRef = useRef(sessionWebSocket)
  
  // Update ref when sessionWebSocket changes (but don't trigger effect)
  sessionWebSocketRef.current = sessionWebSocket
  
  useEffect(() => {
    if (autoConnect && !hasAutoConnectedRef.current) {
      hasAutoConnectedRef.current = true
      console.log('[AudioRecorder] Auto-connecting WebSocket on mount (ONCE)')
      // Small delay to ensure component is fully mounted
      const timer = setTimeout(() => {
        sessionWebSocketRef.current.connect()
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [autoConnect]) // Only depend on autoConnect, not sessionWebSocket object

  const handleStartRecording = useCallback(async () => {
    try {
      if (!sessionWebSocket.isConnected) {
        console.warn('[AudioRecorder] WebSocket not connected, connecting...')
        await sessionWebSocket.connect()
      }

      if (sessionMode && !currentSession) {
        console.log('[AudioRecorder] Starting new session')
        const sessionId = await sessionWebSocket.startSession()
        
        // Register session with store to enable transcript storage
        const storeSessionId = startStoreSession()
        console.log('[AudioRecorder] Store session started:', storeSessionId)
        
        setCurrentSession({ id: sessionId })
        console.log('[AudioRecorder] Session started:', sessionId)
      }

      await startRecording()
      console.log('[AudioRecorder] Recording started successfully')
    } catch (error) {
      console.error('[AudioRecorder] Failed to start recording:', error)
      onError?.(error as Error)
    }
  }, [sessionMode, currentSession, sessionWebSocket, startRecording, startStoreSession, onError])

  const handleStopRecording = useCallback(async () => {
    try {
      stopRecording()
      
      // CRITICAL: Wait for MediaRecorder to fully stop and flush final data
      // Without this delay, combined WebM may be incomplete (missing footer/cues)
      await new Promise(resolve => setTimeout(resolve, 100))
      
      if (sessionMode && accumulatedChunks.length > 0) {
        console.log('[AudioRecorder] Processing session with', accumulatedChunks.length, 'chunks')
        
        try {
          setIsProcessing(true)
          
          // Combine all MediaRecorder chunks into a single complete WebM blob
          // MediaRecorder produces streaming fragments where only the first chunk has the complete WebM header
          console.log('[AudioRecorder] Combining all chunks into complete WebM blob...')
          const allChunkBlobs = accumulatedChunks.map(chunk =>
            chunk.data instanceof Blob ? chunk.data : new Blob([chunk.data], { type: 'audio/webm' })
          )
          const completeWebMBlob = new Blob(allChunkBlobs, { type: 'audio/webm;codecs=opus' })
          console.log(`[AudioRecorder] ✅ Combined blob size: ${completeWebMBlob.size} bytes`)
          
          // FIX: Send WebM directly to backend (NO CONVERSION NEEDED!)
          // Backend uses torchaudio + FFmpeg to decode WebM/Opus automatically
          // Converting to WAV in browser is unnecessary and causes errors
          console.log('[AudioRecorder] Sending WebM directly to backend (FFmpeg will decode)...')
          const webmArrayBuffer = await completeWebMBlob.arrayBuffer()
          console.log(`[AudioRecorder] ✅ WebM ArrayBuffer ready: ${webmArrayBuffer.byteLength} bytes`)
          
          // Send WebM file directly - backend handles decoding
          sessionWebSocket.sendAudioChunk(webmArrayBuffer, 0)
          
          // End session - transcript will arrive via WebSocket callback
          const transcriptResult = await sessionWebSocket.endSession()
          console.log('[AudioRecorder] Backend session ended, transcript via WebSocket:', transcriptResult)

          // Transcript is handled by WebSocket callback to avoid duplicates
          // Wait for WebSocket callback to complete before proceeding
          if (transcriptResult) {
            console.log('[AudioRecorder] Transcript received, handled by WebSocket callback')

            // Wait 100ms for WebSocket callback to complete adding transcript to store
            await new Promise(resolve => setTimeout(resolve, 100))
          } else {
            console.warn('[AudioRecorder] No transcript returned from endSession()')
          }
          
          // Clear session after transcript is fully processed
          if (currentSession) {
            console.log('[AudioRecorder] Clearing session after transcript processed')
            
            // End store session as well
            endStoreSession(currentSession.id)
            
            setCurrentSession(null)
          }
        } catch (error) {
          console.error('[AudioRecorder] Failed to process session:', error)
          onError?.(error as Error)
          // Clear session even on error to prevent stuck state
          if (currentSession) {
            endStoreSession(currentSession.id)
            setCurrentSession(null)
          }
        } finally {
          setIsProcessing(false)
        }
        
        setAccumulatedChunks([])
      } else if (currentSession) {
        // No chunks to process, just clear session
        endStoreSession(currentSession.id)
        setCurrentSession(null)
      }
      
      console.log('[AudioRecorder] Stopped recording')
    } catch (error) {
      console.error('[AudioRecorder] Failed to stop recording:', error)
      onError?.(error as Error)
    }
  }, [
    stopRecording,
    sessionMode,
    accumulatedChunks,
    sessionWebSocket,
    currentSession,
    endStoreSession,
    onError,
  ])



  const handleDeviceSelect = useCallback((deviceId: string) => {
    const device = availableDevices.find((d) => d.deviceId === deviceId)
    if (device) {
      selectDevice(deviceId)
      console.log('[AudioRecorder] Selected device:', device.label)
    }
  }, [availableDevices, selectDevice])

  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900"> Thu âm</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Session mode:</span>
          <button
            onClick={() => setSessionMode(!sessionMode)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              sessionMode ? 'bg-green-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                sessionMode ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {!sessionWebSocket.isConnected && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-800"> WebSocket đang kết nối...</p>
        </div>
      )}

      {!permissionGranted && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-800"> Cần quyền truy cập microphone để thu âm</p>
        </div>
      )}

      {audioError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-800"> {audioError.message}</p>
        </div>
      )}

      {showVolumeIndicator && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-gray-700">📊 Âm lượng:</span>
            <span className="text-sm font-mono font-bold text-blue-600">
              {(currentVolume * 100).toFixed(1)}%
            </span>
            {isRecording && (
              <span className="text-xs text-gray-500">
                ({isVoiceDetected ? '🟢 Có giọng' : '⚪ Im lặng'})
              </span>
            )}
          </div>
          <SimpleWaveform 
            rmsValues={rmsHistory} 
            isRecording={isRecording} 
            isVoiceDetected={isVoiceDetected}
          />
        </div>
      )}

      <div className="mb-4">
        <RecordingStatusIndicator
          isRecording={isRecording}
          currentVolume={currentVolume}
          isVoiceDetected={isVoiceDetected}
        />
      </div>

      <div className="flex items-center gap-3 mb-4">
        {!isRecording ? (
          <button
            onClick={handleStartRecording}
            disabled={!permissionGranted || !sessionWebSocket.isConnected || isProcessing}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
             Bắt đầu ghi
          </button>
        ) : (
          <button
            onClick={handleStopRecording}
            disabled={isProcessing}
            className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
             Dừng ghi
          </button>
        )}
      </div>

      {showSettings && availableDevices.length > 0 && (
        <div className="pt-4 border-t border-gray-200">
          <label htmlFor="audio-device" className="block text-sm font-medium text-gray-700 mb-2">
            Chọn microphone
          </label>
          <select
            id="audio-device"
            value={selectedDevice?.deviceId || ''}
            onChange={(e) => handleDeviceSelect(e.target.value)}
            disabled={isRecording}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {availableDevices.map((device) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label || `Microphone ${device.deviceId.slice(0, 8)}...`}
              </option>
            ))}
          </select>
        </div>
      )}

      {currentSession && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-xs text-green-800"> Session ID: {currentSession.id.slice(0, 8)}...</p>
          <p className="text-xs text-green-600 mt-1">{accumulatedChunks.length} chunks được ghi</p>
        </div>
      )}
    </div>
  )
}

export default AudioRecorder
