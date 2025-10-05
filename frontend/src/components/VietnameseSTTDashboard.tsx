import React, { useState, useCallback, useEffect } from 'react'
import { Mic, Settings, Trash2, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { config } from '@/lib/config'
import { TranscriptDisplay } from '@/components/TranscriptDisplay'
import { AudioRecorder } from '@/components/AudioRecorder'
import { WarningIndicator } from '@/components/WarningIndicator'
import type { TranscriptEntry } from '@/stores/vietnameseSTT.store'
import type { VietnameseSTTDashboardProps } from '@/types/component-props'
import {
  useConnectionStatus,
  useCurrentSession,
  useTranscripts,
  useWarnings,
  useTranscriptActions,
  useTranscriptUI,
} from '@/stores/vietnameseSTT.store'

/**

/**
 * Connection status indicator
 */
const ConnectionStatusBadge: React.FC<{ status: ReturnType<typeof useConnectionStatus> }> = ({ status }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: 'bg-green-500',
          text: 'Đã kết nối',
          textColor: 'text-green-700'
        }
      case 'connecting':
      case 'reconnecting':
        return {
          color: 'bg-yellow-500 animate-pulse',
          text: 'Đang kết nối...',
          textColor: 'text-yellow-700'
        }
      case 'disconnected':
        return {
          color: 'bg-gray-500',
          text: 'Chưa kết nối',
          textColor: 'text-gray-700'
        }
      case 'failed':
        return {
          color: 'bg-red-500',
          text: 'Kết nối thất bại',
          textColor: 'text-red-700'
        }
      default:
        return {
          color: 'bg-gray-400',
          text: 'Không xác định',
          textColor: 'text-gray-600'
        }
    }
  }
  
  const config = getStatusConfig()
  
  return (
    <div className="flex items-center gap-2">
      <div className={cn("w-3 h-3 rounded-full", config.color)} />
      <span className={cn("text-sm font-medium", config.textColor)}>
        {config.text}
      </span>
    </div>
  )
}

/**
 * Session statistics component
 */
const SessionStats: React.FC<{ className?: string }> = ({ className }) => {
  const currentSession = useCurrentSession()
  const transcripts = useTranscripts()
  
  if (!currentSession) {
    return null
  }
  
  const sessionTranscripts = transcripts.filter(t => t.sessionId === currentSession.id)
  const sessionWarnings = sessionTranscripts.filter(t => t.warning).length
  const duration = currentSession.status === 'active' 
    ? Date.now() - currentSession.startTime 
    : currentSession.totalDuration
  
  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`
    }
    return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`
  }
  
  return (
    <div className={cn("bg-gray-50 rounded-lg p-4", className)}>
      <h3 className="text-sm font-medium text-gray-900 mb-3">Thống kê phiên</h3>
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-gray-600">Thời gian</div>
          <div className="font-medium text-gray-900">{formatDuration(duration)}</div>
        </div>
        
        <div>
          <div className="text-gray-600">Bản ghi</div>
          <div className="font-medium text-gray-900">{sessionTranscripts.length}</div>
        </div>
        
        <div>
          <div className="text-gray-600">Cảnh báo</div>
          <div className={cn(
            "font-medium",
            sessionWarnings > 0 ? "text-red-600" : "text-gray-900"
          )}>
            {sessionWarnings}
          </div>
        </div>
        
        <div>
          <div className="text-gray-600">Trạng thái</div>
          <div className={cn(
            "font-medium",
            {
              'text-green-600': currentSession.status === 'active',
              'text-yellow-600': currentSession.status === 'paused',
              'text-gray-600': currentSession.status === 'stopped',
              'text-blue-600': currentSession.status === 'completed',
            }
          )}>
            {currentSession.status === 'active' && 'Đang hoạt động'}
            {currentSession.status === 'paused' && 'Tạm dừng'}
            {currentSession.status === 'stopped' && 'Đã dừng'}
            {currentSession.status === 'completed' && 'Hoàn thành'}
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Export functionality - DISABLED per user request
 * Keep code commented for potential future use
 */
/*
const useExportTranscripts = () => {
  const transcripts = useTranscripts()
  
  const exportAsJSON = useCallback(() => {
    const dataStr = JSON.stringify(transcripts, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `vietnamese-stt-transcripts-${Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [transcripts])
  
  const exportAsText = useCallback(() => {
    const textContent = transcripts
      .map((t, i) => {
        const timestamp = new Intl.DateTimeFormat('vi-VN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }).format(new Date(t.timestamp))
        
        const warningFlag = t.warning ? ' [CẢNH BÁO]' : ''
        return `${i + 1}. [${timestamp}] ${t.text}${warningFlag}`
      })
      .join('\n\n')
    
    const dataBlob = new Blob([textContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `vietnamese-stt-transcripts-${Date.now()}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [transcripts])
  
  return { exportAsJSON, exportAsText }
}
*/

/**
 * Vietnamese STT Dashboard Component
 * Main interface for real-time Vietnamese speech-to-text with toxic detection
 */
export const VietnameseSTTDashboard: React.FC<VietnameseSTTDashboardProps> = ({
  className,
  websocketUrl = config.backend.wsUrl,
  title = 'Vietnamese Speech-to-Text với Phát hiện Độc hại',
  showSettings: showSettingsButton = true,
  onError,
}) => {
  const [showSettings, setShowSettings] = useState(false)
  
  // Store state
  const connectionStatus = useConnectionStatus()
  const transcripts = useTranscripts()
  const warnings = useWarnings()
  const { clearTranscripts } = useTranscriptActions()
  const { selectedTranscriptId, selectTranscript } = useTranscriptUI()
  
  // Derived state: find the selected transcript object
  const selectedTranscript = selectedTranscriptId 
    ? transcripts.find(t => t.id === selectedTranscriptId) || null
    : null
  
  // Export functionality (kept for future use, not exposed in UI)
  // const { exportAsJSON, exportAsText } = useExportTranscripts()
  
  // Stabilize websocketUrl to prevent child component re-renders
  const stableWebsocketUrl = React.useMemo(() => websocketUrl, [websocketUrl])
  
  // Handle transcript selection
  const handleTranscriptSelect = useCallback((transcript: TranscriptEntry | null) => {
    selectTranscript(transcript?.id || null)
  }, [selectTranscript])
  
  // Handle clear transcripts
  const handleClearTranscripts = useCallback(() => {
    if (window.confirm('Bạn có chắc chắn muốn xóa tất cả bản ghi? Hành động này không thể hoàn tác.')) {
      clearTranscripts()
      selectTranscript(null)
    }
  }, [clearTranscripts, selectTranscript])
  
  
  // Handle settings toggle
  const handleSettingsToggle = useCallback(() => {
    setShowSettings(!showSettings)
  }, [showSettings])
  
  // Handle refresh
 const handleRefresh = useCallback(() => {
    window.location.reload()
  }, [])
  
  // Auto-close settings when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element
      if (showSettings && !target.closest('.settings-panel')) {
        setShowSettings(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showSettings])
  
  return (
    <div className={cn("min-h-screen bg-gray-50", className)}>
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and title */}
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Mic className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
                <ConnectionStatusBadge status={connectionStatus} />
              </div>
            </div>
            
            {/* Action buttons */}
            <div className="flex items-center gap-3">
              {/* Clear button */}
              <button
                onClick={handleClearTranscripts}
                disabled={transcripts.length === 0}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Trash2 className="w-4 h-4" />
                Xóa tất cả
              </button>
              
              {/* Refresh button */}
              <button
                onClick={handleRefresh}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Làm mới
              </button>
              
              {/* Settings button */}
              {showSettingsButton && (
                <button
                  onClick={handleSettingsToggle}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                    showSettings 
                      ? "bg-blue-100 text-blue-700 border border-blue-200" 
                      : "text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                  )}
                >
                  <Settings className="w-4 h-4" />
                  Cài đặt
                </button>
              )}
            </div>
          </div>
        </div>
      </header>
      
      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Warning indicator */}
        {warnings.total > 0 && (
          <div className="mb-6 mx-auto max-w-3xl">
            <WarningIndicator 
              showDetails 
              showHistory
              className="max-w-2xl"
            />
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Audio recorder */}
          <div className="lg:col-span-1 space-y-6">
            <AudioRecorder 
              websocketUrl={stableWebsocketUrl}
              onError={onError}
              className="h-fit"
              showSettings={true}
              showVolumeIndicator={true}
              autoConnect={true}
            />
            
            {/* Session statistics */}
            <SessionStats />
          </div>
          
          {/* Right column - Transcript display */}
          <div className="lg:col-span-2">
            <TranscriptDisplay 
              onTranscriptSelect={handleTranscriptSelect}
              maxHeight="600px"
              autoScroll
            />
          </div>
        </div>
        
        {/* Selected transcript details */}
        {selectedTranscript && (
          <div className="mt-6">
            <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Chi tiết bản ghi
                </h3>
                <button
                  onClick={() => selectTranscript(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Nội dung</h4>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {selectedTranscript.text}
                  </p>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Thông tin</h4>
                    <dl className="mt-2 text-sm space-y-1">
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Thời gian:</dt>
                        <dd className="text-gray-900">
                          {new Intl.DateTimeFormat('vi-VN', {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit'
                          }).format(new Date(selectedTranscript.timestamp))}
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Nhãn cảm xúc:</dt>
                        <dd className={cn(
                          "font-medium",
                          {
                            'text-red-600': selectedTranscript.label === 'toxic',
                            'text-orange-600': selectedTranscript.label === 'negative',
                            'text-green-600': selectedTranscript.label === 'positive',
                            'text-gray-600': selectedTranscript.label === 'neutral',
                          }
                        )}>
                          {selectedTranscript.label}
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Độ tin cậy tổng:</dt>
                        <dd className="text-gray-900 font-medium">
                          {!isNaN(selectedTranscript.confidence) 
                            ? `${Math.round(selectedTranscript.confidence * 100)}%`
                            : 'N/A'
                          }
                        </dd>
                      </div>
                      {selectedTranscript.metadata?.asrConfidence && (
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">- ASR:</dt>
                          <dd className="text-gray-700">
                            {Math.round(selectedTranscript.metadata.asrConfidence * 100)}%
                          </dd>
                        </div>
                      )}
                      {selectedTranscript.metadata?.sentimentConfidence && (
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">- Cảm xúc:</dt>
                          <dd className="text-gray-700">
                            {Math.round(selectedTranscript.metadata.sentimentConfidence * 100)}%
                          </dd>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Cảnh báo:</dt>
                        <dd className={selectedTranscript.warning ? 'text-red-600' : 'text-green-600'}>
                          {selectedTranscript.warning ? 'Có' : 'Không'}
                        </dd>
                      </div>
                      {(() => {
                        // Debug logging
                        if (import.meta.env.DEV) {
                          console.log('[Dashboard] Selected transcript bad_keywords:', selectedTranscript.bad_keywords)
                        }
                        return null
                      })()}
                      {selectedTranscript.bad_keywords && selectedTranscript.bad_keywords.length > 0 && (
                        <div className="col-span-2 pt-2 border-t border-gray-200">
                          <dt className="text-gray-600 mb-2">Từ khóa độc hại:</dt>
                          <dd className="flex flex-wrap gap-2">
                            {selectedTranscript.bad_keywords.map((key: string, idx: number) => (
                              <span 
                                key={idx}
                                className="inline-flex items-center px-2 py-1 rounded-md bg-red-100 text-red-800 text-xs font-medium"
                              >
                                🚫 {key}
                              </span>
                            ))}
                          </dd>
                        </div>
                      )}
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
      
      {/* Settings panel */}
      {showSettings && (
        <div className="settings-panel fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Cài đặt</h2>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Kết nối</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        WebSocket URL
                      </label>
                      <input
                        type="text"
                        value={websocketUrl}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        readOnly
                      />
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      Trạng thái: <ConnectionStatusBadge status={connectionStatus} />
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Thống kê</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <div className="font-medium text-gray-900">{transcripts.length}</div>
                      <div className="text-gray-600">Tổng bản ghi</div>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <div className="font-medium text-red-600">{warnings.total}</div>
                      <div className="text-gray-600">Tổng cảnh báo</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default VietnameseSTTDashboard