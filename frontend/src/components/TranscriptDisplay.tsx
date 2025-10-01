import React, { useCallback, useEffect, useRef, useState, useMemo } from 'react'
import { Clock, AlertTriangle, Search, Filter, Volume2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { 
  VIETNAMESE_UI_TEXT, 
  formatVietnameseDateTime, 
  formatVietnameseNumbers,
  vietnameseUI 
} from '@/utils/vietnamese'
import { 
  useTranscripts, 
  useTranscriptUI, 
  useWarnings,
  useCurrentTranscript 
} from '@/stores/vietnameseSTT.store'
import type { VietnameseSentiment, TranscriptResult } from '@/types/transcript'

// Import TranscriptEntry type from store where it's defined  
type TranscriptEntry = TranscriptResult & {
  id: string
  sessionId: string
  timestamp: number
  text: string
  label: VietnameseSentiment
  confidence: number
  warning: boolean
  bad_keywords?: string[]
  isProcessing: boolean
  metadata?: { 
    audioChunkSize?: number
    processingTime?: number
    modelVersion?: string
  }
}

/**
 * Props for TranscriptDisplay component
 */
interface TranscriptDisplayProps {
  className?: string
  showSearch?: boolean
  showFilters?: boolean
  autoScroll?: boolean
  maxHeight?: string
  onTranscriptSelect?: (transcript: TranscriptEntry | null) => void
}

/**
 * Get appropriate CSS classes for sentiment labels
 */
const getSentimentStyles = (label: VietnameseSentiment, isWarning: boolean) => {
  const baseStyles = "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
  
  if (isWarning) {
    return cn(baseStyles, {
      'bg-red-100 text-red-800 border border-red-200': label === 'toxic',
      'bg-orange-100 text-orange-800 border border-orange-200': label === 'negative',
    })
  }
  
  return cn(baseStyles, {
    'bg-green-100 text-green-800 border border-green-200': label === 'positive',
    'bg-gray-100 text-gray-800 border border-gray-200': label === 'neutral',
  })
}

/**
 * Use Vietnamese formatting utilities
 */

/**
 * Individual transcript entry component
 * Task 9: Memoized to prevent unnecessary re-renders
 */
const TranscriptEntryComponent = React.memo<{
  transcript: TranscriptEntry
  isSelected: boolean
  onSelect: () => void
}>(({ transcript, isSelected, onSelect }) => {
  return (
    <div
      onClick={onSelect}
      className={cn(
        "p-4 rounded-lg border transition-all duration-200 cursor-pointer hover:shadow-md",
        isSelected 
          ? "border-blue-500 bg-blue-50 shadow-sm" 
          : "border-gray-200 hover:border-gray-300 bg-white",
        transcript.warning && "ring-2 ring-red-200 ring-opacity-50"
      )}
    >
      {/* Header with timestamp and warning indicator */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Clock className="w-4 h-4" />
          <span className="font-mono">
            {formatVietnameseDateTime.time(transcript.timestamp)}
          </span>
          {transcript.warning && (
            <AlertTriangle className="w-4 h-4 text-red-500" />
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Confidence indicator */}
          <span className="text-xs text-gray-500">
            {formatVietnameseNumbers.percentage(transcript.confidence)}
          </span>
          
          {/* Sentiment label */}
          <span className={getSentimentStyles(transcript.label, transcript.warning)}>
            {transcript.label}
          </span>
        </div>
      </div>
      
      {/* Vietnamese text content */}
      <div className="mb-2">
        <p className={cn(
          vietnameseUI.getTextClasses('transcript'),
          "text-gray-900 leading-relaxed font-medium text-base",
          // Highlight warnings with subtle background
          transcript.warning && "bg-red-50 px-2 py-1 rounded"
        )}>
          {transcript.text || (
            <span className="italic text-gray-400">
              {VIETNAMESE_UI_TEXT.transcripts.processing}
            </span>
          )}
        </p>
      </div>
      
      {/* Bad keywords warning */}
      {transcript.bad_keywords && transcript.bad_keywords.length > 0 && (
        <div className="mb-2">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span className="text-sm font-medium text-red-700">Từ khóa không phù hợp:</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {transcript.bad_keywords.map((keyword: string, index: number) => (
              <span 
                key={index}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Processing indicator */}
      {transcript.isProcessing && (
        <div className="flex items-center gap-2 text-sm text-blue-600">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Đang phân tích...</span>
        </div>
      )}
      
      {/* Metadata info */}
      {transcript.metadata && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <div className="flex items-center gap-4 text-xs text-gray-500">
            {transcript.metadata.audioChunkSize && (
              <span>
                <Volume2 className="w-3 h-3 inline mr-1" />
                {Math.round(transcript.metadata.audioChunkSize / 1024)}KB
              </span>
            )}
            {transcript.metadata.processingTime && (
              <span>
                Xử lý: {transcript.metadata.processingTime}ms
              </span>
            )}
            {transcript.metadata.modelVersion && (
              <span>
                Model: {transcript.metadata.modelVersion}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}, (prevProps, nextProps) => {
  // Task 9: Custom comparison function for React.memo
  // Only re-render if transcript content, selection, or warning state changes
  return (
    prevProps.transcript.id === nextProps.transcript.id &&
    prevProps.transcript.text === nextProps.transcript.text &&
    prevProps.transcript.label === nextProps.transcript.label &&
    prevProps.transcript.warning === nextProps.transcript.warning &&
    prevProps.transcript.isProcessing === nextProps.transcript.isProcessing &&
    prevProps.isSelected === nextProps.isSelected
  )
})

TranscriptEntryComponent.displayName = 'TranscriptEntryComponent'

/**
 * Vietnamese STT Transcript Display Component
 * Shows real-time transcript results with Vietnamese text support
 */
export const TranscriptDisplay: React.FC<TranscriptDisplayProps> = ({
  className,
  showSearch = true,
  showFilters = true,
  autoScroll = true,
  maxHeight = "500px",
  onTranscriptSelect,
}) => {
  const transcripts = useTranscripts()
  const currentTranscript = useCurrentTranscript()
  const warnings = useWarnings()
  const {
    selectedTranscriptId,
    searchQuery,
    filterByWarnings,
    showWarnings,
    selectTranscript,
    setSearchQuery,
    setFilterByWarnings,
  } = useTranscriptUI()
  
  const containerRef = useRef<HTMLDivElement>(null)
  const lastTranscriptCount = useRef(transcripts.length)
  
  // Task 9: Local state for debounced search input
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery)
  const searchDebounceTimer = useRef<number | null>(null)
  
  // Auto-scroll to bottom when new transcripts arrive
  useEffect(() => {
    if (autoScroll && transcripts.length > lastTranscriptCount.current && containerRef.current) {
      const container = containerRef.current
      container.scrollTop = container.scrollHeight
    }
    lastTranscriptCount.current = transcripts.length
  }, [transcripts.length, autoScroll])
  
  // Handle transcript selection
  const handleTranscriptSelect = useCallback((transcript: TranscriptEntry) => {
    selectTranscript(transcript.id)
    onTranscriptSelect?.(transcript)
  }, [selectTranscript, onTranscriptSelect])
  
  // Task 9: Debounced search input handler (300ms delay)
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setLocalSearchQuery(value)
    
    // Clear existing timer
    if (searchDebounceTimer.current) {
      clearTimeout(searchDebounceTimer.current)
    }
    
    // Set new timer to update store after 300ms
    searchDebounceTimer.current = window.setTimeout(() => {
      setSearchQuery(value)
    }, 300)
  }, [setSearchQuery])
  
  // Task 9: Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (searchDebounceTimer.current) {
        clearTimeout(searchDebounceTimer.current)
      }
    }
  }, [])
  
  // Task 9: Memoize filtered transcripts to avoid recalculation on every render
  const filteredTranscripts = useMemo(() => {
    let results = transcripts
    
    // Apply warning filter
    if (filterByWarnings) {
      results = results.filter(t => t.warning)
    }
    
    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      results = results.filter(t => 
        t.text.toLowerCase().includes(query) ||
        t.label.toLowerCase().includes(query)
      )
    }
    
    return results
  }, [transcripts, filterByWarnings, searchQuery])
  
  // Handle filter toggle
  const handleFilterToggle = useCallback(() => {
    setFilterByWarnings(!filterByWarnings)
  }, [filterByWarnings, setFilterByWarnings])
  
  // Clear selection
  const handleClearSelection = useCallback(() => {
    selectTranscript(null)
    onTranscriptSelect?.(null)
  }, [selectTranscript, onTranscriptSelect])
  
  return (
    <div className={cn("bg-white rounded-lg shadow-lg border border-gray-200", className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className={cn("text-lg font-semibold text-gray-900", vietnameseUI.getTextClasses('heading'))}>
            {VIETNAMESE_UI_TEXT.transcripts.title}
          </h2>
          
          <div className="flex items-center gap-2">
            {/* Warning indicator */}
            {warnings.recent > 0 && showWarnings && (
              <div className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                <AlertTriangle className="w-4 h-4" />
                <span>{warnings.recent} cảnh báo</span>
              </div>
            )}
            
            {/* Transcript count */}
            <span className="text-sm text-gray-500">
              {transcripts.length} bản ghi
            </span>
          </div>
        </div>
        
        {/* Search and filters */}
        {(showSearch || showFilters) && (
          <div className="flex items-center gap-2">
            {/* Search input */}
            {showSearch && (
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder={VIETNAMESE_UI_TEXT.transcripts.searchPlaceholder}
                  value={localSearchQuery}
                  onChange={handleSearchChange}
                  className={cn(
                    "w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm",
                    vietnameseUI.getTextClasses('ui')
                  )}
                />
              </div>
            )}
            
            {/* Filter controls */}
            {showFilters && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleFilterToggle}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    filterByWarnings 
                      ? "bg-red-100 text-red-700 border border-red-200" 
                      : "bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200"
                  )}
                >
                  <Filter className="w-4 h-4" />
                  {filterByWarnings ? "Chỉ cảnh báo" : "Tất cả"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Transcript list */}
      <div 
        ref={containerRef}
        className="overflow-y-auto"
        style={{ maxHeight }}
      >
        {filteredTranscripts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Volume2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium mb-2">
              {transcripts.length === 0 ? "Chưa có bản ghi nào" : "Không tìm thấy kết quả"}
            </p>
            <p className="text-sm">
              {searchQuery ? 
                `Không tìm thấy kết quả cho "${searchQuery}"` :
                filterByWarnings ?
                  "Không có cảnh báo nào" :
                  "Bắt đầu ghi âm để xem kết quả phiên âm"
              }
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {/* Task 9: Use filtered and memoized transcripts */}
            {filteredTranscripts.map((transcript) => (
              <TranscriptEntryComponent
                key={transcript.id}
                transcript={transcript}
                isSelected={selectedTranscriptId === transcript.id}
                onSelect={() => handleTranscriptSelect(transcript)}
              />
            ))}
            
            {/* Current processing indicator */}
            {currentTranscript?.isProcessing && (
              <div className="flex items-center justify-center p-4 text-blue-600">
                <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2" />
                <span className="text-sm">Đang phân tích văn bản mới...</span>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Footer with selection info */}
      {selectedTranscriptId && (
        <div className="p-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
          <span className="text-sm text-gray-600">
            Đã chọn 1 bản ghi
          </span>
          <button
            onClick={handleClearSelection}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Bỏ chọn
          </button>
        </div>
      )}
    </div>
  )
}

export default TranscriptDisplay