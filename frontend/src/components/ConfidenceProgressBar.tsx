import React from 'react'
import { cn } from '@/lib/utils'
import type { ConfidenceProgressBarProps } from '@/types/component-props'

/**
 * Get color classes based on confidence level
 * - Red: < 50% (low confidence)
 * - Yellow/Orange: 50-75% (medium confidence)
 * - Green: > 75% (high confidence)
 */
const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.75) {
    return 'bg-green-500'
  } else if (confidence >= 0.50) {
    return 'bg-yellow-500'
  } else {
    return 'bg-red-500'
  }
}

/**
 * Get text color for percentage label
 */
const getTextColor = (confidence: number): string => {
  if (confidence >= 0.75) {
    return 'text-green-700'
  } else if (confidence >= 0.50) {
    return 'text-yellow-700'
  } else {
    return 'text-red-700'
  }
}

/**
 * Get size classes for the progress bar
 */
const getSizeClasses = (size: 'sm' | 'md' | 'lg'): { container: string; bar: string } => {
  switch (size) {
    case 'sm':
      return {
        container: 'h-1.5',
        bar: 'h-1.5'
      }
    case 'lg':
      return {
        container: 'h-3',
        bar: 'h-3'
      }
    case 'md':
    default:
      return {
        container: 'h-2',
        bar: 'h-2'
      }
  }
}

/**
 * ConfidenceProgressBar - Color-coded progress bar for confidence scores
 * 
 * Visual feedback component showing confidence level with color coding:
 * - Green (≥75%): High confidence, reliable transcription
 * - Yellow (50-75%): Medium confidence, acceptable quality
 * - Red (<50%): Low confidence, may need verification
 * 
 * @example
 * ```tsx
 * <ConfidenceProgressBar 
 *   confidence={0.937} 
 *   showLabel 
 *   showPercentage 
 * />
 * ```
 */
export const ConfidenceProgressBar: React.FC<ConfidenceProgressBarProps> = ({
  confidence,
  showLabel = false,
  showPercentage = true,
  size = 'md',
  animated = true,
  className
}) => {
  // Clamp confidence between 0 and 1
  const clampedConfidence = Math.max(0, Math.min(1, confidence))
  const percentage = Math.round(clampedConfidence * 100)
  
  const colorClass = getConfidenceColor(clampedConfidence)
  const textColorClass = getTextColor(clampedConfidence)
  const sizeClasses = getSizeClasses(size)
  
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Optional label */}
      {showLabel && (
        <span className="text-xs font-medium text-gray-600 whitespace-nowrap">
          Độ tin cậy:
        </span>
      )}
      
      {/* Progress bar container */}
      <div 
        className={cn(
          "flex-1 bg-gray-200 rounded-full overflow-hidden",
          sizeClasses.container
        )}
      >
        {/* Progress bar fill */}
        <div
          className={cn(
            colorClass,
            sizeClasses.bar,
            "rounded-full",
            animated && "transition-all duration-500 ease-out"
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Độ tin cậy ${percentage}%`}
        />
      </div>
      
      {/* Percentage label */}
      {showPercentage && (
        <span 
          className={cn(
            "text-xs font-bold tabular-nums whitespace-nowrap",
            textColorClass
          )}
        >
          {percentage}%
        </span>
      )}
    </div>
  )
}

/**
 * Export component as default
 */
export default ConfidenceProgressBar
