import React from 'react'
import { cn } from '@/lib/utils'

interface VietnameseHighlightedTextProps {
  text: string
  keywords: string[]
  highlightClassName?: string
  className?: string
  severity?: 'low' | 'medium' | 'high'
}

/**
 * Vietnamese-specific text highlighting component
 * Handles Vietnamese text with proper accent matching and highlighting
 */
export const VietnameseHighlightedText: React.FC<VietnameseHighlightedTextProps> = ({
  text,
  keywords,
  highlightClassName,
  className,
  severity = 'medium'
}) => {
  if (!keywords || keywords.length === 0) {
    return <span className={className}>{text}</span>
  }

  // Get highlight styling based on severity
  const getHighlightStyles = (severity: 'low' | 'medium' | 'high') => {
    switch (severity) {
      case 'high':
        return "bg-red-300 text-red-950 font-bold px-1.5 py-0.5 rounded-md border-2 border-red-400 shadow-sm"
      case 'medium':
        return "bg-orange-200 text-orange-900 font-semibold px-1 py-0.5 rounded border border-orange-300"
      case 'low':
        return "bg-yellow-200 text-yellow-800 font-medium px-1 py-0.5 rounded border border-yellow-300"
      default:
        return "bg-red-200 text-red-900 font-semibold px-1 py-0.5 rounded border border-red-300"
    }
  }

  const highlightStyle = highlightClassName || getHighlightStyles(severity)

  // Normalize Vietnamese text for better matching
  const normalizeVietnamese = (str: string) => {
    return str
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // Remove diacritics
      .replace(/đ/g, 'd')
      .replace(/Đ/g, 'D')
  }

  // Create a more sophisticated matching function for Vietnamese
  const createVietnameseMatcher = (keywords: string[]) => {
    const normalizedKeywords = keywords.map(normalizeVietnamese)
    
    return (text: string) => {
      const normalizedText = normalizeVietnamese(text)
      const matches: Array<{ start: number; end: number; original: string; normalized: string }> = []
      
      normalizedKeywords.forEach((keyword, keywordIndex) => {
        let index = 0
        while ((index = normalizedText.indexOf(keyword, index)) !== -1) {
          // Find the original text at this position
          let originalStart = index
          let originalEnd = index + keywords[keywordIndex].length
          
          // Adjust for potential length differences due to normalization
          const originalKeyword = keywords[keywordIndex]
          
          // Try to find the exact original match
          const textSegment = text.substring(Math.max(0, index - 10), Math.min(text.length, index + keyword.length + 10))
          const originalMatch = textSegment.match(new RegExp(originalKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'))
          
          if (originalMatch && originalMatch.index !== undefined) {
            originalStart = Math.max(0, index - 10) + originalMatch.index
            originalEnd = originalStart + originalMatch[0].length
          }
          
          matches.push({
            start: originalStart,
            end: originalEnd,
            original: text.substring(originalStart, originalEnd),
            normalized: keyword
          })
          
          index += keyword.length
        }
      })
      
      // Sort matches by position and remove overlaps
      matches.sort((a, b) => a.start - b.start)
      const nonOverlappingMatches = []
      let lastEnd = 0
      
      for (const match of matches) {
        if (match.start >= lastEnd) {
          nonOverlappingMatches.push(match)
          lastEnd = match.end
        }
      }
      
      return nonOverlappingMatches
    }
  }

  const matcher = createVietnameseMatcher(keywords)
  const matches = matcher(text)

  if (matches.length === 0) {
    return <span className={className}>{text}</span>
  }

  // Split text into parts based on matches
  const parts: Array<{ text: string; isHighlighted: boolean; keyword?: string }> = []
  let lastIndex = 0

  matches.forEach((match) => {
    // Add text before match
    if (match.start > lastIndex) {
      parts.push({
        text: text.substring(lastIndex, match.start),
        isHighlighted: false
      })
    }
    
    // Add highlighted match
    parts.push({
      text: match.original,
      isHighlighted: true,
      keyword: match.original
    })
    
    lastIndex = match.end
  })

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({
      text: text.substring(lastIndex),
      isHighlighted: false
    })
  }

  return (
    <span className={className}>
      {parts.map((part, index) => {
        if (part.isHighlighted) {
          return (
            <span
              key={index}
              className={cn(highlightStyle)}
              title={`Từ ngữ không phù hợp: ${part.keyword}`}
            >
              {part.text}
            </span>
          )
        }
        
        return part.text
      })}
    </span>
  )
}

export default VietnameseHighlightedText
