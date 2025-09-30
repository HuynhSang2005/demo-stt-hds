import { z } from 'zod'
import {
  ErrorSeveritySchema,
  ErrorCategorySchema,
  BaseErrorSchema,
  AudioErrorSchema,
  WebSocketErrorSchema,
  STTModelErrorSchema,
  ClassificationErrorSchema,
  ValidationErrorSchema,
  ErrorSchema,
  ErrorCollectionSchema,
  ErrorHandlerConfigSchema
} from '../schemas/error.schema'

/**
 * Error severity levels for Vietnamese STT system
 */
export type ErrorSeverity = z.infer<typeof ErrorSeveritySchema>

/**
 * Error categories for Vietnamese STT classification
 */
export type ErrorCategory = z.infer<typeof ErrorCategorySchema>

/**
 * Base error structure for all Vietnamese STT errors
 */
export type BaseError = z.infer<typeof BaseErrorSchema>

/**
 * Audio recording and processing error
 */
export type AudioError = z.infer<typeof AudioErrorSchema>

/**
 * WebSocket connection and communication error
 */
export type WebSocketError = z.infer<typeof WebSocketErrorSchema>

/**
 * Vietnamese STT model processing error
 */
export type STTModelError = z.infer<typeof STTModelErrorSchema>

/**
 * Toxic detection classification error
 */
export type ClassificationError = z.infer<typeof ClassificationErrorSchema>

/**
 * Input validation error with field-specific details
 */
export type ValidationError = z.infer<typeof ValidationErrorSchema>

/**
 * Union of all Vietnamese STT system errors
 */
export type SystemError = z.infer<typeof ErrorSchema>

/**
 * Collection of multiple errors
 */
export type ErrorCollection = z.infer<typeof ErrorCollectionSchema>

/**
 * Error handler configuration
 */
export type ErrorHandlerConfig = z.infer<typeof ErrorHandlerConfigSchema>

/**
 * Union type for all possible Vietnamese STT errors
 */
export type VietnameseSTTError = SystemError

/**
 * Error handler function type
 */
export type ErrorHandler = (error: VietnameseSTTError) => void

/**
 * Error recovery strategy function type
 */
export type ErrorRecoveryStrategy = (error: VietnameseSTTError) => Promise<boolean>

/**
 * Error logging context interface
 */
export interface ErrorContext {
  userId?: string
  sessionId: string
  timestamp: number
  userAgent: string
  url: string
  additionalData?: Record<string, unknown>
}

/**
 * Error management utilities interface
 */
export interface ErrorManager {
  /**
   * Handle and log error with appropriate strategy
   */
  handleError: (error: VietnameseSTTError, context: ErrorContext) => Promise<void>
  
  /**
   * Register error recovery strategy for specific error codes
   */
  registerRecoveryStrategy: (errorCode: string, strategy: ErrorRecoveryStrategy) => void
  
  /**
   * Get user-friendly error message for display
   */
  getUserFriendlyMessage: (error: VietnameseSTTError) => string
  
  /**
   * Check if error is recoverable
   */
  isRecoverable: (error: VietnameseSTTError) => boolean
  
  /**
   * Retry failed operation with backoff strategy
   */
  retryWithBackoff: <T>(operation: () => Promise<T>, maxRetries: number) => Promise<T>
}

/**
 * Type guard to check if error is validation error
 * @param error - Error to check
 * @returns true if error is validation error
 */
export function isValidationError(error: VietnameseSTTError): error is ValidationError {
  return error.category === 'VALIDATION'
}

/**
 * Type guard to check if error is audio processing error
 * @param error - Error to check
 * @returns true if error is audio processing error
 */
export function isAudioProcessingError(error: VietnameseSTTError): boolean {
  return error.category === 'AUDIO_PROCESSING'
}

/**
 * Type guard to check if error is network error
 * @param error - Error to check
 * @returns true if error is network error
 */
export function isNetworkError(error: VietnameseSTTError): boolean {
  return error.category === 'NETWORK'
}

/**
 * Type guard to check if error is audio recording error
 * @param error - Error to check
 * @returns true if error is audio recording error
 */
export function isAudioRecordingError(error: VietnameseSTTError): error is AudioError {
  return error.category === 'AUDIO_RECORDING'
}

/**
 * Type guard to check if error is STT model error
 * @param error - Error to check
 * @returns true if error is STT model error
 */
export function isSTTModelError(error: VietnameseSTTError): error is STTModelError {
  return error.category === 'STT_MODEL'
}

/**
 * Type guard to check if error is WebSocket error
 * @param error - Error to check
 * @returns true if error is WebSocket error
 */
export function isWebSocketError(error: VietnameseSTTError): error is WebSocketError {
  return error.category === 'WEBSOCKET_CONNECTION' || error.category === 'WEBSOCKET_COMMUNICATION'
}

/**
 * Type guard to check if error severity is critical
 * @param error - Error to check
 * @returns true if error is critical severity
 */
export function isCriticalError(error: VietnameseSTTError): boolean {
  return error.severity === 'critical'
}

/**
 * Type guard to check if error is user-facing
 * @param error - Error to check
 * @returns true if error should be shown to user
 */
export function isUserFacingError(error: VietnameseSTTError): boolean {
  return error.severity === 'medium' || error.severity === 'high' || error.severity === 'critical'
}

/**
 * Helper to create user-friendly error message
 * @param error - Error to format
 * @returns User-friendly error message in Vietnamese
 */
export function formatErrorMessage(error: VietnameseSTTError): string {
  // Use the message from the error object as it's already human-readable
  if (error.message) {
    return error.message
  }

  // Default Vietnamese error messages based on category
  switch (error.category) {
    case 'AUDIO_RECORDING':
      return 'Vui lòng cấp quyền truy cập microphone để sử dụng tính năng ghi âm'
    case 'WEBSOCKET_CONNECTION':
    case 'NETWORK':
      return 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối mạng'
    case 'STT_MODEL':
    case 'CLASSIFICATION_MODEL':
      return 'Lỗi xử lý âm thanh. Vui lòng thử lại'
    case 'AUDIO_PROCESSING':
      return 'Định dạng âm thanh không được hỗ trợ'
    case 'VALIDATION':
      return 'Dữ liệu đầu vào không hợp lệ'
    default:
      return 'Đã xảy ra lỗi không mong muốn. Vui lòng thử lại'
  }
}

/**
 * Helper to determine if error should trigger retry
 * @param error - Error to check
 * @returns true if operation should be retried
 */
export function shouldRetry(error: VietnameseSTTError): boolean {
  const retryableCategories: ErrorCategory[] = [
    'WEBSOCKET_CONNECTION',
    'NETWORK',
    'WEBSOCKET_COMMUNICATION'
  ]
  
  return retryableCategories.includes(error.category) && error.severity !== 'critical'
}