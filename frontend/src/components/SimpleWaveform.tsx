import React, { useMemo } from 'react'
import { cn } from '@/lib/utils'
import type { SimpleWaveformProps } from '@/types/component-props'

/**
 * Simple Waveform Visualizer Component
 *
 * Displays a real-time audio waveform visualization using vertical bars.
 * Green bars indicate voice detection, gray bars show silence.
 * Bar height represents audio volume (RMS) with smooth CSS transitions.
 */
export const SimpleWaveform: React.FC<SimpleWaveformProps> = ({
  rmsValues,
  isRecording,
  isVoiceDetected,
  barCount = 20,
  className,
}) => {
  // Voice detection threshold
  const voiceActive = isVoiceDetected || rmsValues[rmsValues.length - 1] > 0.05

  // Ensure we have the right number of values (pad with zeros if needed)
  const normalizedValues = useMemo(() => {
    const values = [...rmsValues]
    while (values.length < barCount) {
      values.unshift(0) // Pad at start with zeros
    }
    const result = values.slice(-barCount) // Take last N values
    
    // Debug logging in development
    if (import.meta.env.DEV && isRecording && values.length > 0) {
      console.log(`[SimpleWaveform] RMS values: ${values.length} items, last: ${values[values.length - 1]?.toFixed(3)}`)
    }
    
    return result
  }, [rmsValues, barCount, isRecording])

  return (
    <div className={cn(
      "flex flex-col gap-2 p-4 rounded-lg border",
      isRecording 
        ? "bg-white border-gray-200" 
        : "bg-gray-50 border-gray-100",
      className
    )}>
      {/* Waveform title */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">
          Biểu đồ sóng âm thanh
        </h3>
        {isRecording && (
          <span className={cn(
            "text-xs font-medium px-2 py-1 rounded",
            voiceActive 
              ? "bg-green-100 text-green-700" 
              : "bg-gray-100 text-gray-500"
          )}>
            {voiceActive ? '🟢 Có giọng nói' : '⚪ Im lặng'}
          </span>
        )}
      </div>

      {/* Waveform bars */}
      <div className="flex items-end justify-between gap-1 h-20 px-2">
        {normalizedValues.map((value, index) => {
          // Calculate bar height (minimum 10%, maximum 100%)
          // RMS values are typically 0-1, multiply by 100 for percentage
          // Add extra amplification for visibility: value * 150
          const heightPercent = isRecording 
            ? Math.max(10, Math.min(100, value * 150)) // Amplify by 1.5x for better visibility
            : 10 // Flat baseline when not recording

          // Determine bar color based on voice detection and value
          let barColor = 'bg-gray-300' // Default: gray
          if (isRecording && value > 0.05) {
            if (voiceActive) {
              barColor = value > 0.15 ? 'bg-green-500' : 'bg-green-400'
            } else {
              barColor = 'bg-yellow-400'
            }
          }

          return (
            <div
              key={index}
              className={cn(
                "flex-1 transition-all duration-200 ease-out rounded-t-sm",
                barColor
              )}
              style={{
                height: `${heightPercent}%`,
                minWidth: '4px',
              }}
              title={`Bar ${index + 1}: ${value.toFixed(3)}`}
            />
          )
        })}
      </div>

      {/* RMS range indicator */}
      {isRecording && (
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>0.00</span>
          <span className="font-medium">
            Peak: {Math.max(...normalizedValues).toFixed(3)}
          </span>
          <span>1.00</span>
        </div>
      )}
    </div>
  )
}
