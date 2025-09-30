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
 * Optional transcript result metadata
 * Additional information about the STT processing
 */
export type TranscriptMetadata = NonNullable<TranscriptResult['metadata']>

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
  return result.warning || isWarningLabel(result.label)
}

/**
 * Helper type for transcript display components
 */
export type TranscriptDisplayItem = TranscriptResult & {
  displayIndex?: number
  isLatest?: boolean
}