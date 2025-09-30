import { z } from 'zod'

/**
 * Error severity levels for Vietnamese STT system
 */
export const ErrorSeveritySchema = z.enum([
  'low',        // Minor issues, system can continue
  'medium',     // Moderate issues, some features affected
  'high',       // Serious issues, major functionality impacted
  'critical'    // System failure, complete functionality loss
]).describe('Error severity levels for Vietnamese STT application')

/**
 * Error categories specific to Vietnamese STT + Toxic Detection
 */
export const ErrorCategorySchema = z.enum([
  'AUDIO_RECORDING',     // Issues with audio capture/recording
  'AUDIO_PROCESSING',    // Issues with audio processing/format
  'WEBSOCKET_CONNECTION', // WebSocket connection issues
  'WEBSOCKET_COMMUNICATION', // WebSocket message/protocol issues
  'STT_MODEL',           // Vietnamese STT model errors
  'CLASSIFICATION_MODEL', // Toxic detection model errors
  'VALIDATION',          // Data validation errors
  'AUTHENTICATION',      // Auth/permission errors
  'NETWORK',            // General network connectivity
  'SYSTEM',             // System/browser compatibility
  'USER_INPUT',         // User input validation errors
  'CONFIGURATION'       // Configuration/setup errors
]).describe('Error categories for Vietnamese STT system')

/**
 * Base error schema for all errors in the system
 */
export const BaseErrorSchema = z.object({
  id: z.string()
    .describe('Unique error identifier'),
  
  code: z.string()
    .describe('Error code (e.g., "STT_001", "WS_CONNECTION_FAILED")'),
  
  category: ErrorCategorySchema
    .describe('Category of the error'),
  
  severity: ErrorSeveritySchema
    .describe('Severity level of the error'),
  
  message: z.string()
    .min(1)
    .describe('Human-readable error message'),
  
  timestamp: z.number()
    .positive()
    .describe('Unix timestamp when error occurred'),
  
  userAgent: z.string()
    .optional()
    .describe('Browser user agent (for debugging)'),
  
  url: z.string()
    .optional()
    .describe('URL where error occurred')
}).describe('Base error information for Vietnamese STT system')

/**
 * Audio recording specific errors
 */
export const AudioErrorSchema = BaseErrorSchema.extend({
  category: z.literal('AUDIO_RECORDING'),
  
  details: z.object({
    permissionState: z.enum(['denied', 'granted', 'prompt']).optional(),
    deviceId: z.string().optional(),
    constraints: z.any().optional(),
    mediaError: z.string().optional()
  }).optional()
}).describe('Audio recording error details')

/**
 * WebSocket connection errors
 */
export const WebSocketErrorSchema = BaseErrorSchema.extend({
  category: z.literal('WEBSOCKET_CONNECTION'),
  
  details: z.object({
    url: z.string().optional(),
    readyState: z.number().optional(),
    closeCode: z.number().optional(),
    closeReason: z.string().optional(),
    reconnectAttempt: z.number().optional()
  }).optional()
}).describe('WebSocket connection error details')

/**
 * Vietnamese STT model errors
 */
export const STTModelErrorSchema = BaseErrorSchema.extend({
  category: z.literal('STT_MODEL'),
  
  details: z.object({
    modelType: z.string().optional(),
    audioFormat: z.string().optional(),
    audioDuration: z.number().optional(),
    processingTime: z.number().optional(),
    modelResponse: z.any().optional()
  }).optional()
}).describe('Vietnamese STT model error details')

/**
 * Toxic detection classification errors
 */
export const ClassificationErrorSchema = BaseErrorSchema.extend({
  category: z.literal('CLASSIFICATION_MODEL'),
  
  details: z.object({
    modelType: z.string().optional(),
    inputText: z.string().optional(),
    processingTime: z.number().optional(),
    modelResponse: z.any().optional()
  }).optional()
}).describe('Toxic detection classification error details')

/**
 * Validation errors for data/input validation
 */
export const ValidationErrorSchema = BaseErrorSchema.extend({
  category: z.literal('VALIDATION'),
  
  details: z.object({
    field: z.string().optional(),
    value: z.any().optional(),
    constraint: z.string().optional(),
    schema: z.string().optional()
  }).optional()
}).describe('Data validation error details')

/**
 * Union of all specific error types
 */
export const ErrorSchema = z.discriminatedUnion('category', [
  AudioErrorSchema,
  WebSocketErrorSchema,
  STTModelErrorSchema,
  ClassificationErrorSchema,
  ValidationErrorSchema,
  BaseErrorSchema.extend({ category: z.literal('AUDIO_PROCESSING') }),
  BaseErrorSchema.extend({ category: z.literal('WEBSOCKET_COMMUNICATION') }),
  BaseErrorSchema.extend({ category: z.literal('AUTHENTICATION') }),
  BaseErrorSchema.extend({ category: z.literal('NETWORK') }),
  BaseErrorSchema.extend({ category: z.literal('SYSTEM') }),
  BaseErrorSchema.extend({ category: z.literal('USER_INPUT') }),
  BaseErrorSchema.extend({ category: z.literal('CONFIGURATION') })
]).describe('Union type for all Vietnamese STT system errors')

/**
 * Error collection for multiple errors
 */
export const ErrorCollectionSchema = z.object({
  errors: z.array(ErrorSchema)
    .describe('Collection of errors'),
  
  sessionId: z.string()
    .describe('Session ID when errors occurred'),
  
  context: z.string()
    .optional()
    .describe('Additional context about when/where errors occurred'),
  
  totalCount: z.number()
    .min(0)
    .describe('Total number of errors in this collection')
}).describe('Collection of multiple errors from Vietnamese STT session')

/**
 * Error handler configuration
 */
export const ErrorHandlerConfigSchema = z.object({
  maxErrorsInMemory: z.number()
    .positive()
    .default(100)
    .describe('Maximum number of errors to keep in memory'),
  
  autoReport: z.boolean()
    .default(false)
    .describe('Whether to automatically report errors to monitoring service'),
  
  retryableCategories: z.array(ErrorCategorySchema)
    .default(['WEBSOCKET_CONNECTION', 'NETWORK'])
    .describe('Error categories that should trigger automatic retry'),
  
  suppressDuplicates: z.boolean()
    .default(true)
    .describe('Whether to suppress duplicate errors within a time window'),
  
  duplicateWindow: z.number()
    .positive()
    .default(5000)
    .describe('Time window for duplicate error suppression in milliseconds')
}).describe('Configuration for error handling in Vietnamese STT system')

export default ErrorSchema