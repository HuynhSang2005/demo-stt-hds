import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import React from 'react'
import type { TranscriptResult, VietnameseSentiment } from '@/types/transcript'
import type { ConnectionStatus } from '@/types/websocket'

/**
 * Audio session state for tracking recording sessions
 */
interface AudioSession {
  id: string
  startTime: number
  endTime?: number
  status: 'active' | 'paused' | 'stopped' | 'completed'
  totalDuration: number
  chunkCount: number
}

/**
 * Vietnamese STT transcript entry with metadata
 */
export interface TranscriptEntry {
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
    realTimeFactor?: number
    sampleRate?: number
    audioDuration?: number
    asrConfidence?: number
    sentimentConfidence?: number
  }
}

/**
 * Warning statistics for monitoring toxic content
 */
interface WarningStats {
  total: number
  recent: number // Last 1 minute
  lastWarningTime?: number
  criticalWarnings: number
}

/**
 * Vietnamese STT store state
 */
interface VietnameseSTTState {
  // Connection state
  connectionStatus: ConnectionStatus
  isRecording: boolean
  
  // Current session
  currentSession: AudioSession | null
  
  // Transcripts
  transcripts: TranscriptEntry[]
  currentTranscript: TranscriptEntry | null
  isProcessingTranscript: boolean
  
  // Warnings and monitoring
  warnings: WarningStats
  showWarnings: boolean
  
  // UI state
  selectedTranscriptId: string | null
  searchQuery: string
  filterByWarnings: boolean
  
  // Actions
  startSession: () => string
  endSession: (sessionId: string) => void
  pauseSession: (sessionId: string) => void
  resumeSession: (sessionId: string) => void
  
  addTranscript: (result: TranscriptResult) => void
  updateTranscript: (id: string, updates: Partial<TranscriptEntry>) => void
  clearTranscripts: () => void
  
  setConnectionStatus: (status: ConnectionStatus) => void
  setRecordingState: (isRecording: boolean) => void
  
  toggleWarnings: () => void
  clearWarnings: () => void
  
  selectTranscript: (id: string | null) => void
  setSearchQuery: (query: string) => void
  setFilterByWarnings: (filter: boolean) => void
  
  // Computed getters
  getSessionStats: (sessionId: string) => { duration: number; transcriptCount: number; warningCount: number }
  hasRecentWarnings: () => boolean
}

/**
 * Generate unique ID for sessions and transcripts
 */
const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Check if a transcript contains toxic content based on Vietnamese sentiment
 */
const isWarningContent = (label: VietnameseSentiment): boolean => {
  return label === 'toxic' || label === 'negative'
}

/**
 * Create Vietnamese STT store with Zustand
 * Manages real-time transcript state, warnings, and session tracking
 */
export const useVietnameseSTTStore = create<VietnameseSTTState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    connectionStatus: 'disconnected',
    isRecording: false,
    
    currentSession: null,
    
    transcripts: [],
    currentTranscript: null,
    isProcessingTranscript: false,
    
    warnings: {
      total: 0,
      recent: 0,
      criticalWarnings: 0,
    },
    showWarnings: true,
    
    selectedTranscriptId: null,
    searchQuery: '',
    filterByWarnings: false,
    
    // Session management actions
    startSession: () => {
      // Prevent duplicate sessions - check if already recording
      const currentState = get()
      if (currentState.isRecording || currentState.currentSession?.status === 'active') {
        console.log('[STT Store] Session already active, preventing duplicate')
        return currentState.currentSession?.id || ''
      }
      
      const sessionId = generateId()
      const session: AudioSession = {
        id: sessionId,
        startTime: Date.now(),
        status: 'active',
        totalDuration: 0,
        chunkCount: 0,
      }
      
      set(() => ({
        currentSession: session,
        isRecording: true,
        // Clear processing state for new session
        currentTranscript: null,
        isProcessingTranscript: false,
      }))
      
      console.log('[STT Store] Started session:', sessionId)
      return sessionId
    },
    
    endSession: (sessionId: string) => {
      set((state) => {
        if (state.currentSession?.id !== sessionId) {
          return state
        }
        
        const endTime = Date.now()
        const duration = endTime - state.currentSession.startTime
        
        return {
          currentSession: {
            ...state.currentSession,
            endTime,
            status: 'completed',
            totalDuration: duration,
          },
          isRecording: false,
        }
      })
      
      console.log('[STT Store] Ended session:', sessionId)
    },
    
    pauseSession: (sessionId: string) => {
      set((state) => {
        if (state.currentSession?.id !== sessionId || state.currentSession.status !== 'active') {
          return state
        }
        
        return {
          currentSession: {
            ...state.currentSession,
            status: 'paused',
          },
          isRecording: false,
        }
      })
      
      console.log('[STT Store] Paused session:', sessionId)
    },
    
    resumeSession: (sessionId: string) => {
      set((state) => {
        if (state.currentSession?.id !== sessionId || state.currentSession.status !== 'paused') {
          return state
        }
        
        return {
          currentSession: {
            ...state.currentSession,
            status: 'active',
          },
          isRecording: true,
        }
      })
      
      console.log('[STT Store] Resumed session:', sessionId)
    },
    
    // Transcript management actions
    addTranscript: (result: TranscriptResult) => {
      const state = get()
      
      if (!state.currentSession) {
        console.warn('[STT Store] No active session for transcript')
        return
      }
      
      // Debug: Log the exact response from backend
      console.log('[STT Store] Raw backend response:', result)
      console.log('  ↳ ASR confidence:', result.asr_confidence)
      console.log('  ↳ Sentiment confidence:', result.sentiment_confidence)
      console.log('  ↳ Sentiment label:', result.sentiment_label)
      
      const transcriptId = generateId()
      
      // FIXED: Use correct backend field names (no type casting needed)
      const isWarning = isWarningContent(result.sentiment_label)
      
      // Calculate overall confidence (ASR 60% + Sentiment 40%)
      const overallConfidence = (result.asr_confidence * 0.6) + (result.sentiment_confidence * 0.4)
      console.log('  ↳ Overall confidence:', `${(overallConfidence * 100).toFixed(1)}% = (${result.asr_confidence} * 0.6) + (${result.sentiment_confidence} * 0.4)`)
      
      const entry: TranscriptEntry = {
        id: transcriptId,
        sessionId: state.currentSession.id,
        timestamp: Date.now(),
        text: result.text,
        label: result.sentiment_label, // FIXED: correct field name
        confidence: overallConfidence, // FIXED: calculated weighted average
        warning: isWarning,
        bad_keywords: result.bad_keywords,
        isProcessing: false,
        metadata: {
          processingTime: result.processing_time, // FIXED: backend field name
          realTimeFactor: result.real_time_factor, // NEW: performance metric
          sampleRate: result.sample_rate, // NEW: audio metadata
          audioDuration: result.audio_duration, // NEW: audio metadata
          asrConfidence: result.asr_confidence, // NEW: separate ASR confidence
          sentimentConfidence: result.sentiment_confidence, // NEW: separate sentiment confidence
        },
      }
      
      set((currentState) => ({
        transcripts: [...currentState.transcripts, entry],
        currentTranscript: entry,
        isProcessingTranscript: false,
        
        // Update warning statistics
        warnings: {
          ...currentState.warnings,
          total: currentState.warnings.total + (isWarning ? 1 : 0),
          recent: currentState.warnings.recent + (isWarning ? 1 : 0),
          lastWarningTime: isWarning ? Date.now() : currentState.warnings.lastWarningTime,
          criticalWarnings: currentState.warnings.criticalWarnings + (result.sentiment_label === 'toxic' ? 1 : 0),
        },
        
        // Update session chunk count
        currentSession: currentState.currentSession ? {
          ...currentState.currentSession,
          chunkCount: currentState.currentSession.chunkCount + 1,
        } : currentState.currentSession,
      }))
      
      console.log('[STT Store] Added transcript:', {
        id: transcriptId,
        text: (result.text || '').substring(0, 50) + ((result.text || '').length > 50 ? '...' : ''),
        label: result.sentiment_label,
        warning: isWarning,
      })
      
      // Auto-select new transcript if none selected
      if (!state.selectedTranscriptId) {
        get().selectTranscript(transcriptId)
      }
    },
    
    updateTranscript: (id: string, updates: Partial<TranscriptEntry>) => {
      set((state) => ({
        transcripts: state.transcripts.map((transcript) =>
          transcript.id === id ? { ...transcript, ...updates } : transcript
        ),
        currentTranscript: state.currentTranscript?.id === id 
          ? { ...state.currentTranscript, ...updates } 
          : state.currentTranscript,
      }))
      
      console.log('[STT Store] Updated transcript:', id, updates)
    },
    
    clearTranscripts: () => {
      set({
        transcripts: [],
        currentTranscript: null,
        selectedTranscriptId: null,
        warnings: {
          total: 0,
          recent: 0,
          criticalWarnings: 0,
        },
      })
      
      console.log('[STT Store] Cleared all transcripts')
    },
    
    // Connection and recording state
    setConnectionStatus: (status: ConnectionStatus) => {
      set({ connectionStatus: status })
      console.log('[STT Store] Connection status:', status)
    },
    
    setRecordingState: (isRecording: boolean) => {
      set({ isRecording })
      console.log('[STT Store] Recording state:', isRecording)
    },
    
    // Warning management
    toggleWarnings: () => {
      set((state) => ({ showWarnings: !state.showWarnings }))
    },
    
    clearWarnings: () => {
      set((state) => ({
        warnings: {
          ...state.warnings,
          recent: 0,
          lastWarningTime: undefined,
        }
      }))
      
      console.log('[STT Store] Cleared recent warnings')
    },
    
    // UI state management
    selectTranscript: (id: string | null) => {
      set({ selectedTranscriptId: id })
    },
    
    setSearchQuery: (query: string) => {
      set({ searchQuery: query })
    },
    
    setFilterByWarnings: (filter: boolean) => {
      set({ filterByWarnings: filter })
    },
    
  // Computed getters
  getSessionStats: (sessionId: string) => {
      const state = get()
      const sessionTranscripts = state.transcripts.filter(t => t.sessionId === sessionId)
      
      return {
        duration: state.currentSession?.totalDuration || 0,
        transcriptCount: sessionTranscripts.length,
        warningCount: sessionTranscripts.filter(t => t.warning).length,
      }
    },
    
    hasRecentWarnings: () => {
      const state = get()
      const oneMinuteAgo = Date.now() - 60 * 1000
      
      return state.transcripts.some(t => 
        t.warning && t.timestamp > oneMinuteAgo
      )
    },
  }))
)

/**
 * Selector hooks for optimized component subscriptions
 */

// Connection and recording state
export const useConnectionStatus = () => useVietnameseSTTStore((state) => state.connectionStatus)
export const useRecordingState = () => useVietnameseSTTStore((state) => state.isRecording)

// Session management
export const useCurrentSession = () => useVietnameseSTTStore((state) => state.currentSession)
export const useSessionActions = () => {
  const startSession = useVietnameseSTTStore((state) => state.startSession)
  const endSession = useVietnameseSTTStore((state) => state.endSession)
  const pauseSession = useVietnameseSTTStore((state) => state.pauseSession)
  const resumeSession = useVietnameseSTTStore((state) => state.resumeSession)

  return React.useMemo(() => ({
    startSession,
    endSession,
    pauseSession,
    resumeSession,
  }), [startSession, endSession, pauseSession, resumeSession])
}

// Transcript management
export const useTranscripts = () => {
  const transcripts = useVietnameseSTTStore((state) => state.transcripts)
  const searchQuery = useVietnameseSTTStore((state) => state.searchQuery)
  const filterByWarnings = useVietnameseSTTStore((state) => state.filterByWarnings)

  return React.useMemo(() => {
    let filtered = transcripts

    // Filter by search query (Vietnamese text search)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter((transcript) =>
        transcript.text.toLowerCase().includes(query) ||
        transcript.label.toLowerCase().includes(query)
      )
    }

    // Filter by warnings
    if (filterByWarnings) {
      filtered = filtered.filter((transcript) => transcript.warning)
    }

    // Sort by timestamp (newest first)
    return [...filtered].sort((a, b) => b.timestamp - a.timestamp)
  }, [transcripts, searchQuery, filterByWarnings])
}
export const useCurrentTranscript = () => useVietnameseSTTStore((state) => state.currentTranscript)
export const useTranscriptActions = () => {
  const addTranscript = useVietnameseSTTStore((state) => state.addTranscript)
  const updateTranscript = useVietnameseSTTStore((state) => state.updateTranscript)
  const clearTranscripts = useVietnameseSTTStore((state) => state.clearTranscripts)

  return React.useMemo(() => ({
    addTranscript,
    updateTranscript,
    clearTranscripts,
  }), [addTranscript, updateTranscript, clearTranscripts])
}

// Warning management
export const useWarnings = () => useVietnameseSTTStore((state) => state.warnings)
export const useWarningActions = () => {
  const toggleWarnings = useVietnameseSTTStore((state) => state.toggleWarnings)
  const clearWarnings = useVietnameseSTTStore((state) => state.clearWarnings)
  const hasRecentWarnings = useVietnameseSTTStore((state) => state.hasRecentWarnings)

  return React.useMemo(() => ({
    toggleWarnings,
    clearWarnings,
    hasRecentWarnings,
  }), [toggleWarnings, clearWarnings, hasRecentWarnings])
}

// UI state
export const useTranscriptUI = () => {
  const selectedTranscriptId = useVietnameseSTTStore((state) => state.selectedTranscriptId)
  const searchQuery = useVietnameseSTTStore((state) => state.searchQuery)
  const filterByWarnings = useVietnameseSTTStore((state) => state.filterByWarnings)
  const showWarnings = useVietnameseSTTStore((state) => state.showWarnings)
  const selectTranscript = useVietnameseSTTStore((state) => state.selectTranscript)
  const setSearchQuery = useVietnameseSTTStore((state) => state.setSearchQuery)
  const setFilterByWarnings = useVietnameseSTTStore((state) => state.setFilterByWarnings)

  return React.useMemo(() => ({
    selectedTranscriptId,
    searchQuery,
    filterByWarnings,
    showWarnings,
    selectTranscript,
    setSearchQuery,
    setFilterByWarnings,
  }), [
    selectedTranscriptId,
    searchQuery,
    filterByWarnings,
    showWarnings,
    selectTranscript,
    setSearchQuery,
    setFilterByWarnings,
  ])
}

/**
 * Auto-cleanup recent warnings every minute
 * This should be handled by a React component, not global setInterval
 */
export const useWarningCleanup = () => {
  React.useEffect(() => {
    const interval = setInterval(() => {
      const state = useVietnameseSTTStore.getState()
      const oneMinuteAgo = Date.now() - 60 * 1000

      const recentWarnings = state.transcripts.filter(t =>
        t.warning && t.timestamp > oneMinuteAgo
      ).length

      if (recentWarnings !== state.warnings.recent) {
        useVietnameseSTTStore.setState((prevState) => ({
          warnings: {
            ...prevState.warnings,
            recent: recentWarnings,
          }
        }))
      }
    }, 10000) // Check every 10 seconds

    return () => clearInterval(interval)
  }, [])
}

export default useVietnameseSTTStore