import React, { useCallback, useEffect, useRef, useState, useMemo } from 'react'
import { Clock, AlertTriangle, Search, Filter, Volume2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { 
  VIETNAMESE_UI_TEXT, 
  formatVietnameseDateTime, 
  vietnameseUI 
} from '@/utils/vietnamese'
import { 
  useTranscripts, 
  useTranscriptUI, 
  useWarnings,
  useCurrentTranscript 
} from '@/stores/vietnameseSTT.store'
import type { TranscriptEntry } from '@/stores/vietnameseSTT.store'
import type { TranscriptDisplayProps } from '@/types/component-props'
import { ConfidenceProgressBar } from './ConfidenceProgressBar'
import { SentimentBadge } from './SentimentBadge'
import { ConfidenceBreakdown } from './ConfidenceBreakdown'
import { ToxicWarningAlert } from './ToxicWarningAlert'
import { BadKeywordsList } from './BadKeywordsList'

/**
 * Use Vietnamese formatting utilities
 */

/**
 * Individual transcript entry component
 * Memoized to prevent unnecessary re-renders when parent state changes
 */
const TranscriptEntryComponent = React.memo<{
  transcript: import('@/stores/vietnameseSTT.store').TranscriptEntry
  isSelected: boolean
  onSelect: () => void
}>(({ transcript, isSelected, onSelect }) => {
  return (
    <div
      onClick={onSelect}
      className={cn(
        // Phase 4: Enhanced card styling
        "p-5 rounded-xl border-2 transition-all duration-300 cursor-pointer",
        "hover:shadow-xl hover:-translate-y-1",
        // Selected state
        isSelected 
          ? "border-blue-500 bg-blue-50 shadow-lg scale-[1.02]" 
          : "border-gray-200 hover:border-blue-300 bg-white",
        // Warning ring
        transcript.warning && "ring-2 ring-red-300 ring-opacity-60 shadow-red-100"
      )}
    >
      {/* Phase 4: Enhanced Header - Card header section */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-100">
        <div className="flex items-center gap-2.5">
          <Clock className="w-4 h-4 text-gray-500" />
          <span className="font-mono text-sm font-semibold text-gray-700">
            {formatVietnameseDateTime.time(transcript.timestamp)}
          </span>
          {transcript.warning && (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100">
              <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
              <span className="text-xs font-bold text-red-700">Cảnh báo</span>
            </div>
          )}
        </div>
        
        {/* Phase 2: New SentimentBadge component */}
        <SentimentBadge 
          sentiment={transcript.label}
          confidence={transcript.metadata?.sentimentConfidence}
          showEmoji
          showConfidence={!!transcript.metadata?.sentimentConfidence}
          size="md"
        />
      </div>
      
      {/* Phase 2: Confidence Progress Bar */}
      {transcript.confidence > 0 && (
        <div className="mb-3">
          <ConfidenceProgressBar 
            confidence={transcript.confidence}
            showLabel
            showPercentage
            size="md"
            animated
          />
        </div>
      )}
      
      {/* Phase 3: Toxic Warning Alert - Prominent banner for toxic/negative content */}
      {transcript.warning && (transcript.label === 'toxic' || transcript.label === 'negative') && (
        <div className="mb-3">
          <ToxicWarningAlert 
            sentiment={transcript.label}
            badKeywordsCount={transcript.bad_keywords?.length}
            variant="banner"
          />
        </div>
      )}
      
      {/* Phase 4: Enhanced Vietnamese text content - Body section */}
      <div className="mb-4">
        <p className={cn(
          vietnameseUI.getTextClasses('transcript'),
          // Phase 4: Larger text for better readability
          "text-gray-900 leading-relaxed font-medium text-lg",
          // Highlight warnings with subtle background
          transcript.warning && "bg-red-50 px-3 py-2 rounded-lg border-l-4 border-red-400"
        )}>
          {transcript.text || (
            <span className="italic text-gray-400 text-base">
              {VIETNAMESE_UI_TEXT.transcripts.processing}
            </span>
          )}
        </p>
      </div>
      
      {/* Phase 3: Bad Keywords List - Detailed keyword display */}
      {transcript.bad_keywords && transcript.bad_keywords.length > 0 && (
        <div className="mb-3">
          <BadKeywordsList 
            keywords={transcript.bad_keywords}
            severity={transcript.label === 'toxic' ? 'high' : 'medium'}
            variant="default"
            maxDisplay={5}
          />
        </div>
      )}
      
      {/* Processing indicator */}
      {transcript.isProcessing && (
        <div className="flex items-center gap-2 text-sm text-blue-600">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Đang phân tích...</span>
        </div>
      )}
      
      {/* Phase 4: Footer section - Metadata and confidence breakdown */}
      <div className="mt-4 pt-4 border-t-2 border-gray-100 space-y-3">
        {/* Phase 2: Confidence Breakdown - Detailed ASR vs Sentiment analysis */}
        {transcript.metadata?.asrConfidence && transcript.metadata?.sentimentConfidence && (
          <div className="bg-gray-50 rounded-lg p-3">
            <ConfidenceBreakdown 
              asrConfidence={transcript.metadata.asrConfidence}
              sentimentConfidence={transcript.metadata.sentimentConfidence}
              overallConfidence={transcript.confidence}
              showFormula={false}
              showWeights
              layout="vertical"
            />
          </div>
        )}
        
        {/* Phase 4: Enhanced Metadata info */}
        {transcript.metadata && (
          <div className="flex items-center justify-between flex-wrap gap-3 text-xs">
            <div className="flex items-center gap-4 text-gray-600">
              {transcript.metadata.audioChunkSize && (
                <span className="flex items-center gap-1.5 px-2 py-1 bg-gray-100 rounded-full">
                  <Volume2 className="w-3.5 h-3.5" />
                  <span className="font-medium">{Math.round(transcript.metadata.audioChunkSize / 1024)}KB</span>
                </span>
              )}
              {transcript.metadata.processingTime && (
                <span className="flex items-center gap-1 font-medium">
                  ⚡ Xử lý: {transcript.metadata.processingTime}ms
                </span>
              )}
            </div>
            {transcript.metadata.modelVersion && (
              <span className="text-gray-500 font-mono text-xs">
                {transcript.metadata.modelVersion}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}, (prevProps, nextProps) => {
  // Custom comparison function for React.memo optimization
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
  autoScrollPosition = 'top', // Default: scroll to top to show newest transcripts
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
  
  // Local state for debounced search input to improve UX
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery)
  const searchDebounceTimer = useRef<number | null>(null)
  
  // Auto-scroll when new transcripts arrive
  // 'top': scroll to top (shows newest first - recommended for reverse chronological order)
  // 'bottom': scroll to bottom (shows oldest first - traditional chat style)
  useEffect(() => {
    if (autoScroll && transcripts.length > lastTranscriptCount.current && containerRef.current) {
      const container = containerRef.current
      
      if (autoScrollPosition === 'top') {
        // Scroll to top to show newest transcript (default behavior)
        container.scrollTop = 0
      } else {
        // Scroll to bottom for traditional chat-style display
        container.scrollTop = container.scrollHeight
      }
    }
    lastTranscriptCount.current = transcripts.length
  }, [transcripts.length, autoScroll, autoScrollPosition])
  
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