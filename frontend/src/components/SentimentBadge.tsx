import React from 'react'
import { cn } from '@/lib/utils'
import type { VietnameseSentiment } from '@/types/transcript'
import type { SentimentBadgeProps } from '@/types/component-props'

/**
 * Sentiment configuration with emoji, colors, and labels
 */
const SENTIMENT_CONFIG: Record<VietnameseSentiment, {
  emoji: string
  label: string
  colorClasses: {
    default: string
    outline: string
    solid: string
  }
}> = {
  positive: {
    emoji: '😊',
    label: 'Tích cực',
    colorClasses: {
      default: 'bg-green-100 text-green-800 border-green-200',
      outline: 'bg-white text-green-700 border-green-300',
      solid: 'bg-green-600 text-white border-green-600'
    }
  },
  neutral: {
    emoji: '😐',
    label: 'Trung lập',
    colorClasses: {
      default: 'bg-gray-100 text-gray-800 border-gray-200',
      outline: 'bg-white text-gray-700 border-gray-300',
      solid: 'bg-gray-600 text-white border-gray-600'
    }
  },
  negative: {
    emoji: '😟',
    label: 'Tiêu cực',
    colorClasses: {
      default: 'bg-orange-100 text-orange-800 border-orange-200',
      outline: 'bg-white text-orange-700 border-orange-300',
      solid: 'bg-orange-600 text-white border-orange-600'
    }
  },
  toxic: {
    emoji: '⚠️',
    label: 'Độc hại',
    colorClasses: {
      default: 'bg-red-100 text-red-800 border-red-200',
      outline: 'bg-white text-red-700 border-red-300',
      solid: 'bg-red-600 text-white border-red-600'
    }
  }
}

/**
 * Get size classes for the badge
 */
const getSizeClasses = (size: 'sm' | 'md' | 'lg'): string => {
  switch (size) {
    case 'sm':
      return 'px-2 py-0.5 text-xs'
    case 'lg':
      return 'px-4 py-2 text-base'
    case 'md':
    default:
      return 'px-3 py-1 text-sm'
  }
}

/**
 * Get emoji size classes
 */
const getEmojiSize = (size: 'sm' | 'md' | 'lg'): string => {
  switch (size) {
    case 'sm':
      return 'text-xs'
    case 'lg':
      return 'text-xl'
    case 'md':
    default:
      return 'text-base'
  }
}

/**
 * SentimentBadge - Visual badge displaying sentiment with emoji and color coding
 * 
 * Displays Vietnamese sentiment classification with:
 * - Emoji indicator (😊 😐 😟 ⚠️)
 * - Color-coded background
 * - Vietnamese label
 * - Optional confidence score
 * 
 * Color scheme:
 * - Green: Positive sentiment
 * - Gray: Neutral sentiment
 * - Orange: Negative sentiment
 * - Red: Toxic/harmful content
 * 
 * @example
 * ```tsx
 * <SentimentBadge 
 *   sentiment="toxic" 
 *   confidence={0.949}
 *   showEmoji
 *   showConfidence
 * />
 * ```
 */
export const SentimentBadge: React.FC<SentimentBadgeProps> = ({
  sentiment,
  confidence,
  showEmoji = true,
  showConfidence = false,
  size = 'md',
  variant = 'default',
  className
}) => {
  const config = SENTIMENT_CONFIG[sentiment]
  const sizeClasses = getSizeClasses(size)
  const emojiSizeClass = getEmojiSize(size)
  const colorClasses = config.colorClasses[variant]
  
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-medium border whitespace-nowrap",
        sizeClasses,
        colorClasses,
        className
      )}
      role="status"
      aria-label={`Cảm xúc: ${config.label}${confidence ? `, độ tin cậy ${Math.round(confidence * 100)}%` : ''}`}
    >
      {/* Emoji indicator */}
      {showEmoji && (
        <span className={emojiSizeClass} aria-hidden="true">
          {config.emoji}
        </span>
      )}
      
      {/* Vietnamese label */}
      <span>{config.label}</span>
      
      {/* Optional confidence score */}
      {showConfidence && confidence !== undefined && (
        <span className="font-bold tabular-nums">
          ({Math.round(confidence * 100)}%)
        </span>
      )}
    </span>
  )
}

/**
 * Export component as default
 */
export default SentimentBadge
