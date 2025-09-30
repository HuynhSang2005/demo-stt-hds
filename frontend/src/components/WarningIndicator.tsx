import React, { useState, useCallback, useEffect } from 'react'
import { AlertTriangle, X, Eye, EyeOff, TrendingUp, Clock, Shield } from 'lucide-react'
import { cn } from '@/lib/utils'
import { 
  useWarnings, 
  useWarningActions, 
  useTranscripts,
  useTranscriptUI 
} from '@/stores/vietnameseSTT.store'
import type { VietnameseSentiment } from '@/types/transcript'

/**
 * Props for WarningIndicator component
 */
interface WarningIndicatorProps {
  className?: string
  showDetails?: boolean
  showHistory?: boolean
  autoHide?: boolean
  hideDelay?: number
  onWarningClick?: (warningType: VietnameseSentiment) => void
}

/**
 * Warning severity levels for Vietnamese toxic content
 */
type WarningSeverity = 'low' | 'medium' | 'high' | 'critical'

/**
 * Get warning severity based on Vietnamese sentiment label
 */
const getWarningSeverity = (label: VietnameseSentiment): WarningSeverity => {
  switch (label) {
    case 'toxic': return 'critical'
    case 'negative': return 'high'
    default: return 'low'
  }
}

/**
 * Get appropriate CSS classes for warning severity
 */
const getSeverityStyles = (severity: WarningSeverity, isActive: boolean = false) => {
  const baseStyles = "transition-all duration-200"
  
  switch (severity) {
    case 'critical':
      return cn(baseStyles, 
        isActive 
          ? "bg-red-500 text-white border-red-600 shadow-lg animate-pulse" 
          : "bg-red-100 text-red-800 border-red-200 hover:bg-red-200"
      )
    case 'high':
      return cn(baseStyles,
        isActive 
          ? "bg-orange-500 text-white border-orange-600 shadow-md" 
          : "bg-orange-100 text-orange-800 border-orange-200 hover:bg-orange-200"
      )
    case 'medium':
      return cn(baseStyles,
        isActive 
          ? "bg-yellow-500 text-white border-yellow-600" 
          : "bg-yellow-100 text-yellow-800 border-yellow-200 hover:bg-yellow-200"
      )
    default:
      return cn(baseStyles,
        isActive 
          ? "bg-gray-500 text-white border-gray-600" 
          : "bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-200"
      )
  }
}

/**
 * Format Vietnamese warning message
 */
const getVietnameseWarningMessage = (label: VietnameseSentiment, count: number): string => {
  if (count === 1) {
    switch (label) {
      case 'toxic': return 'Phát hiện nội dung độc hại'
      case 'negative': return 'Phát hiện nội dung tiêu cực'
      default: return 'Phát hiện nội dung cần chú ý'
    }
  }
  
  switch (label) {
    case 'toxic': return `${count} cảnh báo độc hại`
    case 'negative': return `${count} cảnh báo tiêu cực`
    default: return `${count} cảnh báo`
  }
}

/**
 * Warning statistics component
 */
const WarningStats: React.FC<{
  warnings: ReturnType<typeof useWarnings>
  onClose: () => void
}> = ({ warnings, onClose }) => {
  return (
    <div className="absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 p-4 z-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Shield className="w-5 h-5 text-red-500" />
          Thống kê cảnh báo
        </h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      
      {/* Statistics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-red-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-red-600">{warnings.criticalWarnings}</div>
          <div className="text-sm text-red-700">Độc hại</div>
        </div>
        
        <div className="bg-orange-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">{warnings.total - warnings.criticalWarnings}</div>
          <div className="text-sm text-orange-700">Tiêu cực</div>
        </div>
        
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{warnings.recent}</div>
          <div className="text-sm text-blue-700">Gần đây (1 phút)</div>
        </div>
        
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-gray-600">{warnings.total}</div>
          <div className="text-sm text-gray-700">Tổng cộng</div>
        </div>
      </div>
      
      {/* Trend indicator */}
      {warnings.recent > 0 && (
        <div className="flex items-center gap-2 p-2 bg-yellow-50 rounded-lg">
          <TrendingUp className="w-4 h-4 text-yellow-600" />
          <span className="text-sm text-yellow-800">
            Tăng hoạt động cảnh báo trong phút qua
          </span>
        </div>
      )}
      
      {/* Last warning time */}
      {warnings.lastWarningTime && (
        <div className="flex items-center gap-2 mt-3 text-sm text-gray-600">
          <Clock className="w-4 h-4" />
          <span>
            Cảnh báo cuối: {new Intl.DateTimeFormat('vi-VN', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
            }).format(new Date(warnings.lastWarningTime))}
          </span>
        </div>
      )}
    </div>
  )
}

/**
 * Warning history component showing recent warning transcripts
 */
const WarningHistory: React.FC<{
  onClose: () => void
}> = ({ onClose }) => {
  const transcripts = useTranscripts()
  const { setFilterByWarnings } = useTranscriptUI()
  
  // Get recent warning transcripts (last 10)
  const recentWarnings = transcripts
    .filter(t => t.warning)
    .slice(0, 10)
  
  const handleViewAllWarnings = useCallback(() => {
    setFilterByWarnings(true)
    onClose()
  }, [setFilterByWarnings, onClose])
  
  return (
    <div className="absolute top-full right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 p-4 z-50 max-h-80 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Cảnh báo gần đây
        </h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      
      {/* Warning list */}
      {recentWarnings.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Shield className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>Chưa có cảnh báo nào</p>
        </div>
      ) : (
        <div className="space-y-3">
          {recentWarnings.map((transcript) => (
            <div 
              key={transcript.id}
              className="p-3 rounded-lg border border-gray-200 hover:bg-gray-50"
            >
              <div className="flex items-start justify-between mb-2">
                <span className={cn(
                  "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium",
                  getSeverityStyles(getWarningSeverity(transcript.label))
                )}>
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  {transcript.label}
                </span>
                
                <span className="text-xs text-gray-500">
                  {new Intl.DateTimeFormat('vi-VN', {
                    hour: '2-digit',
                    minute: '2-digit'
                  }).format(new Date(transcript.timestamp))}
                </span>
              </div>
              
              <p className="text-sm text-gray-900 line-clamp-2">
                {transcript.text}
              </p>
              
              <div className="mt-2 text-xs text-gray-500">
                Độ tin cậy: {Math.round(transcript.confidence * 100)}%
              </div>
            </div>
          ))}
          
          {/* View all button */}
          <button
            onClick={handleViewAllWarnings}
            className="w-full py-2 text-sm text-blue-600 hover:text-blue-800 font-medium border-t border-gray-200 pt-3 mt-3"
          >
            Xem tất cả cảnh báo →
          </button>
        </div>
      )}
    </div>
  )
}

/**
 * Vietnamese STT Warning Indicator Component
 * Shows real-time warnings for toxic and negative content detection
 */
export const WarningIndicator: React.FC<WarningIndicatorProps> = ({
  className,
  showDetails = true,
  showHistory = true,
  autoHide = false,
  hideDelay = 5000,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onWarningClick: _onWarningClick,
}) => {
  const [showStats, setShowStats] = useState(false)
  const [showHistoryPanel, setShowHistoryPanel] = useState(false)
  const [isVisible, setIsVisible] = useState(true)
  
  const warnings = useWarnings()
  const { clearWarnings, hasRecentWarnings } = useWarningActions()
  
  // Auto-hide functionality
  useEffect(() => {
    if (autoHide && warnings.recent > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false)
      }, hideDelay)
      
      return () => clearTimeout(timer)
    }
  }, [autoHide, hideDelay, warnings.recent])
  
  // Reset visibility when new warnings arrive
  useEffect(() => {
    if (warnings.recent > 0) {
      setIsVisible(true)
    }
  }, [warnings.recent])
  
  // Warning click handler available via onWarningClick prop
  
  // Handle stats toggle
  const handleStatsToggle = useCallback(() => {
    setShowStats(!showStats)
    setShowHistoryPanel(false)
  }, [showStats])
  
  // Handle history toggle
  const handleHistoryToggle = useCallback(() => {
    setShowHistoryPanel(!showHistoryPanel)
    setShowStats(false)
  }, [showHistoryPanel])
  
  // Handle clear warnings
  const handleClearWarnings = useCallback(() => {
    clearWarnings()
    setShowStats(false)
    setShowHistoryPanel(false)
  }, [clearWarnings])
  
  // Handle hide
  const handleHide = useCallback(() => {
    setIsVisible(false)
  }, [])
  
  // Don't render if no warnings and not forced visible
  if (warnings.total === 0 && !isVisible) {
    return null
  }
  
  // Don't render if explicitly hidden
  if (!isVisible) {
    return null
  }
  
  const hasActiveWarnings = hasRecentWarnings()
  const primarySeverity: WarningSeverity = warnings.criticalWarnings > 0 ? 'critical' : 
                                         warnings.recent > 0 ? 'high' : 'medium'
  
  return (
    <div className={cn("relative", className)}>
      {/* Main warning indicator */}
      <div className={cn(
        "flex items-center gap-3 px-4 py-3 rounded-lg border",
        getSeverityStyles(primarySeverity, hasActiveWarnings)
      )}>
        {/* Warning icon */}
        <AlertTriangle className={cn(
          "w-5 h-5",
          hasActiveWarnings ? "animate-pulse" : ""
        )} />
        
        {/* Warning text */}
        <div className="flex-1 min-w-0">
          {warnings.recent > 0 ? (
            <div>
              <div className="font-medium">
                {getVietnameseWarningMessage(
                  warnings.criticalWarnings > 0 ? 'toxic' : 'negative',
                  warnings.recent
                )}
              </div>
              {warnings.total > warnings.recent && (
                <div className="text-sm opacity-75">
                  Tổng cộng: {warnings.total} cảnh báo
                </div>
              )}
            </div>
          ) : warnings.total > 0 ? (
            <div className="font-medium">
              {warnings.total} cảnh báo đã được ghi nhận
            </div>
          ) : (
            <div className="font-medium text-green-700">
              Không có cảnh báo
            </div>
          )}
        </div>
        
        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* Stats button */}
          {showDetails && warnings.total > 0 && (
            <button
              onClick={handleStatsToggle}
              className="p-2 rounded hover:bg-white hover:bg-opacity-20 transition-colors"
              title="Xem thống kê"
            >
              <TrendingUp className="w-4 h-4" />
            </button>
          )}
          
          {/* History button */}
          {showHistory && warnings.total > 0 && (
            <button
              onClick={handleHistoryToggle}
              className="p-2 rounded hover:bg-white hover:bg-opacity-20 transition-colors"
              title="Xem lịch sử cảnh báo"
            >
              <Eye className="w-4 h-4" />
            </button>
          )}
          
          {/* Clear button */}
          {warnings.recent > 0 && (
            <button
              onClick={handleClearWarnings}
              className="p-2 rounded hover:bg-white hover:bg-opacity-20 transition-colors"
              title="Xóa cảnh báo gần đây"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          
          {/* Hide button */}
          <button
            onClick={handleHide}
            className="p-2 rounded hover:bg-white hover:bg-opacity-20 transition-colors"
            title="Ẩn"
          >
            <EyeOff className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Stats panel */}
      {showStats && (
        <WarningStats 
          warnings={warnings} 
          onClose={() => setShowStats(false)}
        />
      )}
      
      {/* History panel */}
      {showHistoryPanel && (
        <WarningHistory 
          onClose={() => setShowHistoryPanel(false)}
        />
      )}
    </div>
  )
}

export default WarningIndicator