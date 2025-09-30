import { z } from 'zod'

/**
 * Vietnamese sentiment labels for speech-to-text classification
 * Based on PhoBERT 4-class classification model
 */
export const VietnameseSentimentSchema = z.enum(['positive', 'negative', 'neutral', 'toxic'])
  .describe('Vietnamese sentiment classification labels from PhoBERT model')

/**
 * Transcript result schema for Vietnamese STT + Toxic Detection
 * Contains transcribed text, sentiment classification, and metadata
 */
export const TranscriptResultSchema = z.object({
  id: z.string()
    .describe('Unique identifier for this transcript result'),
  
  text: z.string()
    .min(1)
    .describe('Transcribed Vietnamese text from Wav2Vec2 ASR model'),
  
  label: VietnameseSentimentSchema
    .describe('Sentiment classification label from PhoBERT model'),
  
  confidence: z.number()
    .min(0)
    .max(1)
    .describe('Confidence score for the sentiment classification (0-1)'),
  
  timestamp: z.number()
    .positive()
    .describe('Unix timestamp when the transcription was generated'),
  
  duration: z.number()
    .positive()
    .optional()
    .describe('Duration of the audio chunk in seconds'),
  
  warning: z.boolean()
    .default(false)
    .describe('Whether this result should display warning (toxic/negative content)'),
  
  bad_keywords: z.array(z.string())
    .optional()
    .describe('List of detected Vietnamese toxic/bad keywords in the transcribed text'),
  
  metadata: z.object({
    audioChunkSize: z.number().positive().optional(),
    processingTime: z.number().positive().optional(),
    modelVersion: z.string().optional(),
  }).optional()
    .describe('Optional metadata about the processing')
}).describe('Complete transcript result from Vietnamese STT + Toxic Detection pipeline')

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