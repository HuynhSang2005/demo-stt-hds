import React from 'react'
import { Info } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * Props for ConfidenceBreakdown component
 */
interface ConfidenceBreakdownProps {
  asrConfidence: number // 0.0 - 1.0, ASR (speech recognition) confidence
  sentimentConfidence: number // 0.0 - 1.0, sentiment classification confidence
  overallConfidence?: number // Optional pre-calculated overall confidence
  showFormula?: boolean // Show the calculation formula
  showWeights?: boolean // Show ASR 60% + Sentiment 40% weights
  layout?: 'horizontal' | 'vertical'
  className?: string
}

/**
 * Configuration for confidence weights
 * ASR: 60% - Primary importance on speech recognition accuracy
 * Sentiment: 40% - Secondary importance on sentiment classification
 */
const CONFIDENCE_WEIGHTS = {
  asr: 0.6,
  sentiment: 0.4
} as const

/**
 * Calculate overall confidence using weighted formula
 */
const calculateOverallConfidence = (asr: number, sentiment: number): number => {
  return (asr * CONFIDENCE_WEIGHTS.asr) + (sentiment * CONFIDENCE_WEIGHTS.sentiment)
}

/**
 * Get color class based on confidence level
 */
const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.75) return 'text-green-600'
  if (confidence >= 0.50) return 'text-yellow-600'
  return 'text-red-600'
}

/**
 * Get background color class based on confidence level
 */
const getConfidenceBgColor = (confidence: number): string => {
  if (confidence >= 0.75) return 'bg-green-50'
  if (confidence >= 0.50) return 'bg-yellow-50'
  return 'bg-red-50'
}

/**
 * Individual confidence row component
 */
interface ConfidenceRowProps {
  label: string
  confidence: number
  weight?: number
  showWeight?: boolean
}

const ConfidenceRow: React.FC<ConfidenceRowProps> = ({ 
  label, 
  confidence, 
  weight,
  showWeight = false
}) => {
  const percentage = Math.round(confidence * 100)
  const colorClass = getConfidenceColor(confidence)
  
  return (
    <div className="flex items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        {showWeight && weight !== undefined && (
          <span className="text-xs text-gray-500">
            (×{Math.round(weight * 100)}%)
          </span>
        )}
      </div>
      <span className={cn("text-sm font-bold tabular-nums", colorClass)}>
        {percentage}%
      </span>
    </div>
  )
}

/**
 * ConfidenceBreakdown - Detailed breakdown of ASR vs Sentiment confidence
 * 
 * Shows the weighted confidence calculation:
 * - ASR Confidence: 60% weight (speech recognition accuracy)
 * - Sentiment Confidence: 40% weight (classification confidence)
 * - Overall Confidence: Weighted average
 * 
 * Formula: Overall = (ASR × 0.6) + (Sentiment × 0.4)
 * 
 * Example from console logs:
 * - ASR: 95% (0.95)
 * - Sentiment: 91.6% (0.916)
 * - Overall: 93.7% = (0.95 × 0.6) + (0.916 × 0.4)
 * 
 * @example
 * ```tsx
 * <ConfidenceBreakdown 
 *   asrConfidence={0.95}
 *   sentimentConfidence={0.916}
 *   showFormula
 *   showWeights
 * />
 * ```
 */
export const ConfidenceBreakdown: React.FC<ConfidenceBreakdownProps> = ({
  asrConfidence,
  sentimentConfidence,
  overallConfidence,
  showFormula = false,
  showWeights = false,
  layout = 'vertical',
  className
}) => {
  // Calculate overall confidence if not provided
  const overall = overallConfidence ?? calculateOverallConfidence(asrConfidence, sentimentConfidence)
  const overallPercentage = Math.round(overall * 100)
  const overallColorClass = getConfidenceColor(overall)
  const overallBgClass = getConfidenceBgColor(overall)
  
  if (layout === 'horizontal') {
    return (
      <div className={cn("flex items-center gap-4", className)}>
        {/* ASR */}
        <div className="flex items-center gap-1">
          <span className="text-xs text-gray-600">ASR:</span>
          <span className={cn("text-xs font-bold tabular-nums", getConfidenceColor(asrConfidence))}>
            {Math.round(asrConfidence * 100)}%
          </span>
        </div>
        
        {/* Separator */}
        <span className="text-gray-300">|</span>
        
        {/* Sentiment */}
        <div className="flex items-center gap-1">
          <span className="text-xs text-gray-600">Cảm xúc:</span>
          <span className={cn("text-xs font-bold tabular-nums", getConfidenceColor(sentimentConfidence))}>
            {Math.round(sentimentConfidence * 100)}%
          </span>
        </div>
        
        {/* Separator */}
        <span className="text-gray-300">|</span>
        
        {/* Overall */}
        <div className="flex items-center gap-1">
          <span className="text-xs text-gray-600">Tổng:</span>
          <span className={cn("text-xs font-bold tabular-nums", overallColorClass)}>
            {overallPercentage}%
          </span>
        </div>
      </div>
    )
  }
  
  // Vertical layout (default)
  return (
    <div className={cn("space-y-2", className)}>
      {/* Header with info icon */}
      <div className="flex items-center gap-2 mb-1">
        <Info className="w-4 h-4 text-gray-400" />
        <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
          Phân tích độ tin cậy
        </span>
      </div>
      
      {/* Individual confidence scores */}
      <div className="space-y-1.5">
        <ConfidenceRow 
          label="Nhận diện giọng nói (ASR)"
          confidence={asrConfidence}
          weight={CONFIDENCE_WEIGHTS.asr}
          showWeight={showWeights}
        />
        
        <ConfidenceRow 
          label="Phân loại cảm xúc"
          confidence={sentimentConfidence}
          weight={CONFIDENCE_WEIGHTS.sentiment}
          showWeight={showWeights}
        />
      </div>
      
      {/* Divider */}
      <div className="border-t border-gray-200 my-2" />
      
      {/* Overall confidence */}
      <div className={cn(
        "flex items-center justify-between gap-2 p-2 rounded-lg",
        overallBgClass
      )}>
        <span className="text-sm font-bold text-gray-900">Độ tin cậy tổng thể</span>
        <span className={cn("text-lg font-bold tabular-nums", overallColorClass)}>
          {overallPercentage}%
        </span>
      </div>
      
      {/* Optional formula explanation */}
      {showFormula && (
        <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-200">
          <div className="text-xs text-gray-600 font-mono">
            <div className="font-semibold mb-1">Công thức:</div>
            <div>
              Tổng = (ASR × 60%) + (Cảm xúc × 40%)
            </div>
            <div className="mt-1 text-gray-500">
              = ({Math.round(asrConfidence * 100)}% × 0.6) + ({Math.round(sentimentConfidence * 100)}% × 0.4)
            </div>
            <div className="mt-1 font-semibold text-gray-700">
              = {overallPercentage}%
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Export component as default
 */
export default ConfidenceBreakdown
