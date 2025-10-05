/**
 * Centralized component props types for Vietnamese STT frontend
 *
 * This file contains all component Props interfaces that were previously
 * defined inline within each component file. Centralizing these types here
 * improves maintainability, type safety, and code organization.
 */

import type { VietnameseSentiment } from '@/types/transcript'
import type { TranscriptEntry } from '@/stores/vietnameseSTT.store'

/**
 * Props for AudioRecorder component
 * Main audio recording component for Vietnamese STT with session management
 */
export interface AudioRecorderProps {
  /** WebSocket URL for real-time audio streaming */
  websocketUrl: string
  /** Optional error handler callback */
  onError?: (error: Error) => void
  /** Optional CSS class name for styling */
  className?: string
  /** Whether to show settings panel (default: true) */
  showSettings?: boolean
  /** Whether to show volume indicator (default: true) */
  showVolumeIndicator?: boolean
  /** Whether to auto-connect on mount (default: false) */
  autoConnect?: boolean
}

/**
 * Props for TranscriptDisplay component
 * Displays and manages transcript entries with filtering and search capabilities
 */
export interface TranscriptDisplayProps {
  /** Optional CSS class name for styling */
  className?: string
  /** Whether to show search functionality (default: true) */
  showSearch?: boolean
  /** Whether to show filter controls (default: true) */
  showFilters?: boolean
  /** Whether to auto-scroll to new transcripts (default: true) */
  autoScroll?: boolean
  /** Auto-scroll position: 'top' shows newest first, 'bottom' shows oldest first */
  autoScrollPosition?: 'top' | 'bottom'
  /** Maximum height constraint for the display area */
  maxHeight?: string
  /** Callback when a transcript is selected */
  onTranscriptSelect?: (transcript: TranscriptEntry | null) => void
}

/**
 * Props for SimpleWaveform component
 * Real-time audio waveform visualization using vertical bars
 */
export interface SimpleWaveformProps {
  /** Array of RMS (volume) values to display (typically last 20 values) */
  rmsValues: number[]
  /** Whether recording is currently active */
  isRecording: boolean
  /** Whether voice is currently detected (based on volume threshold) */
  isVoiceDetected: boolean
  /** Number of bars to display (default: 20) */
  barCount?: number
  /** Optional CSS class name for custom styling */
  className?: string
}

/**
 * Props for WarningIndicator component
 * Displays toxic content warnings with severity levels and history
 */
export interface WarningIndicatorProps {
  /** Optional CSS class name for styling */
  className?: string
  /** Whether to show detailed warning information */
  showDetails?: boolean
  /** Whether to show warning history */
  showHistory?: boolean
  /** Whether to auto-hide warnings after delay */
  autoHide?: boolean
  /** Auto-hide delay in milliseconds */
  hideDelay?: number
  /** Callback when a warning is clicked */
  onWarningClick?: (warningType: VietnameseSentiment) => void
}

/**
 * Props for VietnameseSTTDashboard component
 * Main dashboard component that orchestrates all STT functionality
 */
export interface VietnameseSTTDashboardProps {
  /** Optional CSS class name for styling */
  className?: string
  /** WebSocket URL override (uses config default if not provided) */
  websocketUrl?: string
  /** Dashboard title */
  title?: string
  /** Whether to show settings panel */
  showSettings?: boolean
  /** Callback for exporting transcripts */
  onExport?: (transcripts: import('@/types/transcript').TranscriptResult[]) => void
  /** Error handler callback */
  onError?: (error: Error) => void
}

/**
 * Props for ToxicWarningAlert component
 * Alert component for displaying toxic content warnings
 */
export interface ToxicWarningAlertProps {
  /** Sentiment classification result */
  sentiment: VietnameseSentiment
  /** Optional warning message text */
  text?: string
  /** Number of bad keywords detected */
  badKeywordsCount?: number
  /** Optional dismiss handler */
  onDismiss?: () => void
  /** Whether to show warning icon (default: true) */
  showIcon?: boolean
  /** Display style variant */
  variant?: 'banner' | 'inline' | 'card'
  /** Optional CSS class name for styling */
  className?: string
}

/**
 * Props for SentimentBadge component
 * Badge component displaying sentiment classification with confidence
 */
export interface SentimentBadgeProps {
  /** Sentiment classification result */
  sentiment: VietnameseSentiment
  /** Optional confidence score (0.0 - 1.0) */
  confidence?: number
  /** Whether to show emoji in the badge */
  showEmoji?: boolean
  /** Whether to show confidence percentage */
  showConfidence?: boolean
  /** Badge size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Badge style variant */
  variant?: 'default' | 'outline' | 'solid'
  /** Optional CSS class name for styling */
  className?: string
}

/**
 * Props for RecordingStatusIndicator component
 * Visual indicator showing current recording status and audio levels
 */
export interface RecordingStatusIndicatorProps {
  /** Whether recording is currently active */
  isRecording: boolean
  /** Current audio volume level (0.0 to 1.0) */
  currentVolume: number
  /** Whether voice is currently detected (based on volume threshold) */
  isVoiceDetected: boolean
  /** Optional CSS class name for custom styling */
  className?: string
}

/**
 * Props for ConfidenceProgressBar component
 * Progress bar displaying confidence scores with color coding
 */
export interface ConfidenceProgressBarProps {
  /** Confidence score (0.0 - 1.0) */
  confidence: number
  /** Whether to show label text */
  showLabel?: boolean
  /** Whether to show percentage value */
  showPercentage?: boolean
  /** Progress bar size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Whether to animate the progress bar */
  animated?: boolean
  /** Optional CSS class name for styling */
  className?: string
}

/**
 * Props for ConfidenceBreakdown component
 * Detailed breakdown of ASR and sentiment confidence scores
 */
export interface ConfidenceBreakdownProps {
  /** ASR (speech recognition) confidence score (0.0 - 1.0) */
  asrConfidence: number
  /** Sentiment classification confidence score (0.0 - 1.0) */
  sentimentConfidence: number
  /** Optional pre-calculated overall confidence */
  overallConfidence?: number
  /** Whether to show the calculation formula */
  showFormula?: boolean
  /** Whether to show ASR 60% + Sentiment 40% weights */
  showWeights?: boolean
  /** Layout orientation */
  layout?: 'horizontal' | 'vertical'
  /** Optional CSS class name for styling */
  className?: string
}

/**
 * Props for BadKeywordsList component
 * List component displaying detected bad keywords with blur options
 */
export interface BadKeywordsListProps {
  /** Array of detected bad keywords */
  keywords: string[]
  /** Whether to show keywords blurred initially (default: false) */
  showBlurred?: boolean
  /** Maximum keywords to display before "show more" (default: no limit) */
  maxDisplay?: number
  /** Display style variant */
  variant?: 'default' | 'compact' | 'detailed'
  /** Severity level affecting color scheme */
  severity?: 'high' | 'medium'
  /** Optional CSS class name for styling */
  className?: string
}

/**
 * Warning severity levels for Vietnamese toxic content
 * Used by WarningIndicator component for severity classification
 */
export type WarningSeverity = 'low' | 'medium' | 'high' | 'critical'