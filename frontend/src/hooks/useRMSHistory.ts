import { useState, useEffect, useRef } from 'react'

/**
 * Props for useRMSHistory hook
 */
interface UseRMSHistoryOptions {
  /** Current RMS value from audio recorder */
  currentRMS: number
  /** Whether recording is active */
  isRecording: boolean
  /** Maximum number of RMS values to store (default: 20) */
  maxHistory?: number
  /** Update interval in milliseconds (default: 100ms) */
  updateInterval?: number
}

/**
 * Hook return type
 */
interface UseRMSHistoryReturn {
  /** Array of historical RMS values */
  rmsHistory: number[]
  /** Current peak RMS value in history */
  peakRMS: number
  /** Average RMS value in history */
  averageRMS: number
  /** Whether voice is currently detected (RMS > threshold) */
  isVoiceDetected: boolean
  /** Clear RMS history */
  clearHistory: () => void
}

/**
 * Voice detection threshold
 * Values above this are considered voice activity
 */
const VOICE_DETECTION_THRESHOLD = 0.05

/**
 * useRMSHistory Hook
 * 
 * Tracks historical RMS (volume) values for waveform visualization
 * 
 * Features:
 * - Maintains a rolling window of RMS values
 * - Calculates peak and average RMS
 * - Voice detection based on threshold
 * - Auto-clears when recording stops
 * - Rate-limited updates to prevent excessive re-renders
 * 
 * Part of Phase 1: Recording Visual Feedback Enhancement
 * 
 * @example
 * ```tsx
 * const { rmsHistory, isVoiceDetected, peakRMS } = useRMSHistory({
 *   currentRMS: volume,
 *   isRecording: audioRecording,
 *   maxHistory: 20,
 *   updateInterval: 100
 * })
 * ```
 */
export function useRMSHistory({
  currentRMS,
  isRecording,
  maxHistory = 20,
  updateInterval = 100,
}: UseRMSHistoryOptions): UseRMSHistoryReturn {
  const [rmsHistory, setRmsHistory] = useState<number[]>(
    Array(maxHistory).fill(0)
  )
  const lastUpdateRef = useRef<number>(0)

  // Update RMS history when recording
  useEffect(() => {
    if (!isRecording) {
      // Clear history when not recording
      setRmsHistory(Array(maxHistory).fill(0))
      return
    }

    // Rate-limit updates to prevent excessive re-renders
    const now = Date.now()
    if (now - lastUpdateRef.current < updateInterval) {
      return
    }
    lastUpdateRef.current = now

    // Add new RMS value and remove oldest
    setRmsHistory(prev => {
      const newHistory = [...prev.slice(1), currentRMS]
      return newHistory
    })
  }, [currentRMS, isRecording, maxHistory, updateInterval])

  // Calculate peak RMS
  const peakRMS = Math.max(...rmsHistory)

  // Calculate average RMS (excluding zeros)
  const nonZeroValues = rmsHistory.filter(v => v > 0)
  const averageRMS = nonZeroValues.length > 0
    ? nonZeroValues.reduce((sum, v) => sum + v, 0) / nonZeroValues.length
    : 0

  // Voice detection
  const isVoiceDetected = currentRMS > VOICE_DETECTION_THRESHOLD

  // Clear history function
  const clearHistory = () => {
    setRmsHistory(Array(maxHistory).fill(0))
  }

  return {
    rmsHistory,
    peakRMS,
    averageRMS,
    isVoiceDetected,
    clearHistory,
  }
}
