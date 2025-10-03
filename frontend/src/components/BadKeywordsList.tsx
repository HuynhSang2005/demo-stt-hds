import React from 'react'
import { XCircle, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * Props for BadKeywordsList component
 */
interface BadKeywordsListProps {
  keywords: string[] // Array of detected bad keywords
  showBlurred?: boolean // Show keywords blurred initially (default: false)
  maxDisplay?: number // Maximum keywords to display before "show more" (default: no limit)
  variant?: 'default' | 'compact' | 'detailed' // Display style
  severity?: 'high' | 'medium' // Severity level affects color
  className?: string
}

/**
 * Individual keyword badge component
 */
interface KeywordBadgeProps {
  keyword: string
  isBlurred: boolean
  severity: 'high' | 'medium'
  variant: 'default' | 'compact' | 'detailed'
}

const KeywordBadge: React.FC<KeywordBadgeProps> = ({ 
  keyword, 
  isBlurred, 
  severity,
  variant 
}) => {
  const severityStyles = severity === 'high' 
    ? 'bg-red-100 text-red-900 border-red-300' 
    : 'bg-orange-100 text-orange-900 border-orange-300'
  
  const sizeStyles = variant === 'compact' 
    ? 'px-2 py-0.5 text-xs' 
    : 'px-3 py-1 text-sm'

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium border',
        severityStyles,
        sizeStyles,
        isBlurred && 'blur-sm hover:blur-none transition-all cursor-pointer',
        'select-none'
      )}
      title={isBlurred ? 'Nhấp để hiện' : keyword}
    >
      <XCircle className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
      <span className="font-mono">{keyword}</span>
    </span>
  )
}

/**
 * BadKeywordsList - Display list of detected toxic/bad keywords
 * 
 * Shows specific words or phrases that triggered toxic detection:
 * - Visual badge for each keyword
 * - Color-coded by severity (red = high, orange = medium)
 * - Optional blur effect for sensitive content
 * - Expandable list for many keywords
 * - Multiple display variants
 * 
 * Helps users understand exactly which words caused the warning
 * and allows them to review/edit problematic content.
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <BadKeywordsList 
 *   keywords={['cặt', 'chó', 'khốn nạn']}
 *   severity="high"
 * />
 * 
 * // With blur protection
 * <BadKeywordsList 
 *   keywords={['từ xấu 1', 'từ xấu 2']}
 *   showBlurred
 *   maxDisplay={5}
 * />
 * 
 * // Compact variant
 * <BadKeywordsList 
 *   keywords={['bad word']}
 *   variant="compact"
 *   severity="medium"
 * />
 * ```
 */
export const BadKeywordsList: React.FC<BadKeywordsListProps> = ({
  keywords,
  showBlurred = false,
  maxDisplay,
  variant = 'default',
  severity = 'high',
  className
}) => {
  const [isBlurred, setIsBlurred] = React.useState(showBlurred)
  const [isExpanded, setIsExpanded] = React.useState(false)

  // If no keywords, don't render
  if (!keywords || keywords.length === 0) {
    return null
  }

  // Determine which keywords to display
  const hasMore = maxDisplay && keywords.length > maxDisplay
  const displayedKeywords = isExpanded || !maxDisplay 
    ? keywords 
    : keywords.slice(0, maxDisplay)
  const remainingCount = keywords.length - displayedKeywords.length

  return (
    <div className={cn('space-y-2', className)}>
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertCircle 
            className={cn(
              'w-4 h-4',
              severity === 'high' ? 'text-red-600' : 'text-orange-600'
            )}
          />
          <span 
            className={cn(
              'text-sm font-semibold',
              severity === 'high' ? 'text-red-900' : 'text-orange-900'
            )}
          >
            Từ khóa không phù hợp phát hiện:
          </span>
          <span 
            className={cn(
              'text-xs font-bold px-2 py-0.5 rounded-full',
              severity === 'high' 
                ? 'bg-red-200 text-red-900' 
                : 'bg-orange-200 text-orange-900'
            )}
          >
            {keywords.length}
          </span>
        </div>

        {/* Toggle blur button */}
        {showBlurred && (
          <button
            onClick={() => setIsBlurred(!isBlurred)}
            className={cn(
              'flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors',
              severity === 'high'
                ? 'text-red-700 hover:bg-red-100'
                : 'text-orange-700 hover:bg-orange-100'
            )}
            aria-label={isBlurred ? 'Hiện từ khóa' : 'Ẩn từ khóa'}
          >
            {isBlurred ? (
              <>
                <Eye className="w-3.5 h-3.5" />
                <span>Hiện</span>
              </>
            ) : (
              <>
                <EyeOff className="w-3.5 h-3.5" />
                <span>Ẩn</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Keywords list */}
      <div className="flex flex-wrap gap-2">
        {displayedKeywords.map((keyword, index) => (
          <KeywordBadge
            key={`${keyword}-${index}`}
            keyword={keyword}
            isBlurred={isBlurred}
            severity={severity}
            variant={variant}
          />
        ))}

        {/* Show more button */}
        {hasMore && !isExpanded && (
          <button
            onClick={() => setIsExpanded(true)}
            className={cn(
              'inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium border transition-colors',
              severity === 'high'
                ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
                : 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100'
            )}
          >
            <span>+{remainingCount} từ nữa</span>
          </button>
        )}

        {/* Show less button */}
        {isExpanded && maxDisplay && (
          <button
            onClick={() => setIsExpanded(false)}
            className={cn(
              'inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium border transition-colors',
              severity === 'high'
                ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
                : 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100'
            )}
          >
            <span>Thu gọn</span>
          </button>
        )}
      </div>

      {/* Detailed variant: Add explanation */}
      {variant === 'detailed' && (
        <p className="text-xs text-gray-600 mt-2">
          💡 <strong>Gợi ý:</strong> Những từ này đã được phát hiện trong văn bản và có thể không phù hợp. 
          Vui lòng kiểm tra lại nội dung.
        </p>
      )}
    </div>
  )
}

/**
 * Export component as default
 */
export default BadKeywordsList
