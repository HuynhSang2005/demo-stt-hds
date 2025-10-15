import React from 'react'
import { cn } from '@/lib/utils'

interface HighlightedTextProps {
  text: string
  keywords: string[]
  highlightClassName?: string
  className?: string
}

/**
 * Component to highlight bad keywords in Vietnamese text
 * Highlights keywords with red background and styling
 */
export const HighlightedText: React.FC<HighlightedTextProps> = ({
  text,
  keywords,
  highlightClassName = "bg-red-200 text-red-900 font-semibold px-1 py-0.5 rounded border border-red-300",
  className
}) => {
  if (!keywords || keywords.length === 0) {
    return <span className={className}>{text}</span>
  }

  // Create a regex pattern to match keywords (case insensitive)
  // Escape special regex characters and join with | (OR operator)
  const escapedKeywords = keywords.map(keyword => 
    keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  )
  
  // Create regex pattern with word boundaries for better matching
  const pattern = new RegExp(
    `\\b(${escapedKeywords.join('|')})\\b`,
    'gi'
  )

  // Split text by keywords while preserving the keywords
  const parts = text.split(pattern)
  const matches = text.match(pattern) || []

  return (
    <span className={className}>
      {parts.map((part, index) => {
        const isKeyword = matches.includes(part)
        
        if (isKeyword) {
          return (
            <span
              key={index}
              className={cn(highlightClassName)}
              title={`Từ ngữ không phù hợp: ${part}`}
            >
              {part}
            </span>
          )
        }
        
        return part
      })}
    </span>
  )
}

export default HighlightedText
