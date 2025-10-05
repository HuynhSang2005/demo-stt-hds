import React from 'react'
import { AlertTriangle, AlertOctagon, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ToxicWarningAlertProps } from '@/types/component-props'

/**
 * Warning level configuration
 */
const WARNING_CONFIG: Record<'toxic' | 'negative', {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
  bgColor: string
  borderColor: string
  textColor: string
  iconColor: string
}> = {
  toxic: {
    icon: AlertOctagon,
    title: '⚠️ Nội dung độc hại phát hiện',
    description: 'Văn bản chứa ngôn từ không phù hợp, độc hại hoặc xúc phạm',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-300',
    textColor: 'text-red-900',
    iconColor: 'text-red-600'
  },
  negative: {
    icon: AlertTriangle,
    title: '⚠️ Nội dung tiêu cực',
    description: 'Văn bản có xu hướng tiêu cực hoặc không tích cực',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-300',
    textColor: 'text-orange-900',
    iconColor: 'text-orange-600'
  }
}

/**
 * Get variant-specific styles
 */
const getVariantStyles = (variant: 'banner' | 'inline' | 'card') => {
  switch (variant) {
    case 'banner':
      return 'p-4 rounded-lg border-2'
    case 'inline':
      return 'px-3 py-2 rounded border'
    case 'card':
      return 'p-6 rounded-xl border-2 shadow-lg'
    default:
      return 'p-4 rounded-lg border-2'
  }
}

/**
 * ToxicWarningAlert - Prominent warning display for toxic/negative content
 * 
 * Displays highly visible alerts when harmful or negative content is detected:
 * - Red background for toxic content (harmful, offensive language)
 * - Orange background for negative content (negative sentiment)
 * - Large warning icons
 * - Clear Vietnamese warning messages
 * - Optional keyword count display
 * - Optional dismiss functionality
 * 
 * This component ensures users are immediately aware of problematic content
 * in their transcripts and can take appropriate action.
 * 
 * @example
 * ```tsx
 * // Toxic content warning
 * <ToxicWarningAlert 
 *   sentiment="toxic"
 *   badKeywordsCount={3}
 *   variant="banner"
 * />
 * 
 * // Negative content warning
 * <ToxicWarningAlert 
 *   sentiment="negative"
 *   variant="inline"
 * />
 * ```
 */
export const ToxicWarningAlert: React.FC<ToxicWarningAlertProps> = ({
  sentiment,
  text,
  badKeywordsCount,
  onDismiss,
  showIcon = true,
  variant = 'banner',
  className
}) => {
  // Only show for toxic or negative content
  if (sentiment !== 'toxic' && sentiment !== 'negative') {
    return null
  }

  const config = WARNING_CONFIG[sentiment]
  const Icon = config.icon
  const variantStyles = getVariantStyles(variant)

  return (
    <div
      role="alert"
      aria-live="polite"
      className={cn(
        variantStyles,
        config.bgColor,
        config.borderColor,
        'flex items-start gap-3',
        className
      )}
    >
      {/* Warning Icon */}
      {showIcon && (
        <div className="flex-shrink-0">
          <Icon 
            className={cn(
              variant === 'card' ? 'w-8 h-8' : 'w-6 h-6',
              config.iconColor
            )} 
            aria-hidden="true"
          />
        </div>
      )}

      {/* Warning Content */}
      <div className="flex-1 min-w-0">
        {/* Title */}
        <h3 
          className={cn(
            variant === 'card' ? 'text-lg font-bold' : 'text-sm font-semibold',
            config.textColor,
            'mb-1'
          )}
        >
          {config.title}
        </h3>

        {/* Description or custom text */}
        <p 
          className={cn(
            'text-sm',
            config.textColor,
            'opacity-90'
          )}
        >
          {text || config.description}
        </p>

        {/* Bad keywords count */}
        {badKeywordsCount !== undefined && badKeywordsCount > 0 && (
          <div 
            className={cn(
              'mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
              sentiment === 'toxic' 
                ? 'bg-red-200 text-red-900' 
                : 'bg-orange-200 text-orange-900'
            )}
          >
            <XCircle className="w-3.5 h-3.5" />
            <span>
              {badKeywordsCount} từ khóa không phù hợp
            </span>
          </div>
        )}
      </div>

      {/* Optional Dismiss Button */}
      {onDismiss && (
        <button
          onClick={onDismiss}
          className={cn(
            'flex-shrink-0 p-1 rounded hover:bg-black/5 transition-colors',
            config.textColor
          )}
          aria-label="Đóng cảnh báo"
        >
          <XCircle className="w-5 h-5" />
        </button>
      )}
    </div>
  )
}

/**
 * Export component as default
 */
export default ToxicWarningAlert
