import { z } from 'zod'
import { 
  VietnameseSentimentSchema,
  TranscriptResultSchema,
  TranscriptBatchSchema
} from '../schemas/transcript.schema'

/**
 * Vietnamese sentiment classification labels
 * Inferred from PhoBERT 4-class model schema
 */
export type VietnameseSentiment = z.infer<typeof VietnameseSentimentSchema>

/**
 * Complete transcript result from Vietnamese STT + Toxic Detection
 * Contains transcribed text, sentiment analysis, and metadata
 */
export type TranscriptResult = z.infer<typeof TranscriptResultSchema>

/**
 * Batch of transcript results for multiple audio chunks
 * Used for processing multiple Vietnamese STT results together
 */
export type TranscriptBatch = z.infer<typeof TranscriptBatchSchema>

/**
 * Type guard to check if sentiment label should trigger warning
 * @param label - Vietnamese sentiment label to check
 * @returns true if label is toxic or negative
 */
export function isWarningLabel(label: VietnameseSentiment): boolean {
  return label === 'toxic' || label === 'negative'
}

/**
 * Type guard to check if transcript result has warning
 * @param result - Transcript result to check
 * @returns true if result should show warning indicator
 */
export function hasWarning(result: TranscriptResult): boolean {
  return result.warning || isWarningLabel(result.sentiment_label)
}

/**
 * Get display label from TranscriptResult (for backward compatibility)
 * @param result - Transcript result
 * @returns sentiment label
 */
export function getLabel(result: TranscriptResult): VietnameseSentiment {
  return result.sentiment_label
}

/**
 * Get primary confidence score from TranscriptResult
 * @param result - Transcript result
 * @returns sentiment confidence score
 */
export function getConfidence(result: TranscriptResult): number {
  return result.sentiment_confidence
}

/**
 * Calculate overall confidence score (weighted average of ASR + Sentiment)
 * ASR confidence: 60% weight (more important for transcription accuracy)
 * Sentiment confidence: 40% weight
 * @param result - Transcript result with both confidence scores
 * @returns weighted average confidence between 0 and 1
 */
export function calculateOverallConfidence(result: TranscriptResult): number {
  const asrWeight = 0.6
  const sentimentWeight = 0.4
  return (result.asr_confidence * asrWeight) + (result.sentiment_confidence * sentimentWeight)
}

/**
 * Format confidence score as percentage string
 * @param confidence - Confidence value between 0 and 1
 * @returns formatted percentage string (e.g., "92.3%")
 */
export function formatConfidence(confidence: number): string {
  return `${(confidence * 100).toFixed(1)}%`
}

/**
 * Get formatted overall confidence from TranscriptResult
 * @param result - Transcript result
 * @returns formatted confidence percentage
 */
export function getFormattedConfidence(result: TranscriptResult): string {
  const overall = calculateOverallConfidence(result)
  return formatConfidence(overall)
}

/**
 * Get duration from TranscriptResult (backend uses audio_duration)
 * @param result - Transcript result
 * @returns audio duration in seconds
 */
export function getDuration(result: TranscriptResult): number {
  return result.audio_duration
}

/**
 * Helper type for transcript display components
 */
export type TranscriptDisplayItem = TranscriptResult & {
  displayIndex?: number
  isLatest?: boolean
}