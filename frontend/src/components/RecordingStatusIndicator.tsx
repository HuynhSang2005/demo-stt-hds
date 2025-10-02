import React from 'react'
import { cn } from '@/lib/utils'

/**
 * Props for RecordingStatusIndicator component
 */
interface RecordingStatusIndicatorProps {
  /** Whether recording is currently active */
  isRecording: boolean
  /** Current audio volume level (0.0 to 1.0) */
  currentVolume: number
  /** Whether voice is currently detected (based on volume threshold) */
  isVoiceDetected: boolean
  /** Optional className for custom styling */
  className?: string
}

/**
 * Recording Status Indicator Component
 * 
 * Displays real-time recording status with visual feedback:
 * - Pulsing red dot when recording
 * - Current RMS (volume) value
 * - Voice detection indicator (green when voice detected, gray when silent)
 * 
 * Part of Phase 1: Recording Visual Feedback Enhancement
 */
export const RecordingStatusIndicator: React.FC<RecordingStatusIndicatorProps> = ({
  isRecording,
  currentVolume,
  isVoiceDetected,
  className,
}) => {
  // Voice detection threshold (volume > 0.05 = voice detected)
  const voiceActive = isVoiceDetected || currentVolume > 0.05

  return (
    <div className={cn(
      "flex items-center gap-3 px-4 py-3 rounded-lg border transition-all duration-300",
      isRecording 
        ? "bg-red-50 border-red-200" 
        : "bg-gray-50 border-gray-200",
      className
    )}>
      {/* Recording dot indicator */}
      <div className="flex items-center gap-2">
        {isRecording ? (
          <>
            {/* Pulsing red dot when recording */}
            <div className="relative flex items-center justify-center">
              <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
              <div className="absolute w-3 h-3 bg-red-600 rounded-full animate-ping opacity-75" />
            </div>
            <span className="text-red-600 font-semibold text-sm">
              🔴 Đang ghi âm...
            </span>
          </>
        ) : (
          <>
            {/* Gray dot when not recording */}
            <div className="w-3 h-3 bg-gray-400 rounded-full" />
            <span className="text-gray-500 font-medium text-sm">
              ⚪ Chưa ghi âm
            </span>
          </>
        )}
      </div>

      {/* RMS value display (only when recording) */}
      {isRecording && (
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-xs text-gray-500 font-mono">
            RMS:
          </span>
          <span className={cn(
            "text-xs font-mono font-semibold px-2 py-1 rounded",
            voiceActive 
              ? "bg-green-100 text-green-700" 
              : "bg-gray-100 text-gray-600"
          )}>
            {currentVolume.toFixed(3)}
          </span>
          
          {/* Voice detection indicator */}
          {voiceActive ? (
            <span className="text-xs text-green-600 font-medium">
              🎤 Giọng nói phát hiện
            </span>
          ) : (
            <span className="text-xs text-gray-400 font-medium">
              🔇 Im lặng
            </span>
          )}
        </div>
      )}
    </div>
  )
}
