import { z } from 'zod'

/**
 * Vietnamese sentiment labels for speech-to-text classification
 * Based on PhoBERT 4-class classification model
 */
export const VietnameseSentimentSchema = z.enum(['positive', 'negative', 'neutral', 'toxic'])
  .describe('Vietnamese sentiment classification labels from PhoBERT model')

/**
 * Transcript result schema for Vietnamese STT + Toxic Detection
 * ⚠️ UPDATED to match backend Pydantic schema (2024)
 * Backend sends: sentiment_label, asr_confidence, sentiment_confidence, audio_duration, etc.
 */
export const TranscriptResultSchema = z.object({
  // Core text result
  text: z.string()
    .min(1)
    .describe('Transcribed Vietnamese text from Wav2Vec2 ASR model'),
  
  // ASR metrics
  asr_confidence: z.number()
    .min(0)
    .max(1)
    .describe('ASR model confidence score (0-1)'),
  
  // Classification results - using backend field names
  sentiment_label: VietnameseSentimentSchema
    .describe('Sentiment classification label from PhoBERT model'),
  
  sentiment_confidence: z.number()
    .min(0)
    .max(1)
    .describe('Classification confidence score (0-1)'),
  
  // Warning flag
  warning: z.boolean()
    .default(false)
    .describe('Whether this result should display warning (toxic/negative content)'),
  
  // Detected bad keywords
  bad_keywords: z.array(z.string())
    .optional()
    .describe('List of detected Vietnamese toxic/bad keywords'),
  
  // Performance metrics
  processing_time: z.number()
    .positive()
    .describe('Processing time in seconds'),
  
  real_time_factor: z.number()
    .describe('processing_time / audio_duration ratio'),
  
  // Audio metadata
  audio_duration: z.number()
    .positive()
    .describe('Duration of the audio chunk in seconds'),
  
  sample_rate: z.number()
    .positive()
    .default(16000)
    .describe('Audio sample rate in Hz'),
  
  // Session management
  session_id: z.string()
    .optional()
    .describe('Session identifier for session-based processing'),
  
  // Timing
  timestamp: z.number()
    .positive()
    .optional()
    .describe('Unix timestamp when the transcription was generated'),
  
  // Detailed sentiment scores
  all_sentiment_scores: z.record(z.string(), z.number())
    .optional()
    .describe('All classification scores for each sentiment label'),
  
  // Frontend-generated ID (if needed)
  id: z.string()
    .optional()
    .describe('Frontend-generated unique identifier (optional)')
}).describe('Complete transcript result from Vietnamese STT + Toxic Detection pipeline (Backend-compatible schema)')

/**
 * Batch transcript results for multiple audio chunks
 */
export const TranscriptBatchSchema = z.object({
  results: z.array(TranscriptResultSchema)
    .describe('Array of transcript results'),
  
  sessionId: z.string()
    .describe('Unique session identifier'),
  
  totalProcessed: z.number()
    .min(0)
    .describe('Total number of audio chunks processed in this session'),
  
  averageLatency: z.number()
    .positive()
    .optional()
    .describe('Average processing latency in milliseconds')
}).describe('Batch results for multiple Vietnamese STT transcriptions')

export default TranscriptResultSchema