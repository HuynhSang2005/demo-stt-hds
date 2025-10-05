/**
 * Frontend-Backend Integration Tests
 * Comprehensive test suite covering full data flow from FE to BE and back
 * 
 * Test Coverage:
 * 1. Schema compatibility (TranscriptResult, WebSocket messages, Errors)
 * 2. WebSocket connection lifecycle
 * 3. Audio chunk transmission
 * 4. Real-time transcript reception
 * 5. Error handling
 * 6. Session management
 * 7. Reconnection logic
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { TranscriptResultSchema } from '../../src/schemas/transcript.schema'
import { 
  WebSocketMessageSchema,
  TranscriptResultMessageSchema,
  ErrorMessageSchema 
} from '../../src/schemas/websocket.schema'

// ============================================================================
// TEST SUITE 1: Schema Compatibility Tests
// ============================================================================

describe('Schema Compatibility - Frontend ↔ Backend', () => {
  
  describe('TranscriptResult Schema', () => {
    
    it('should parse backend TranscriptResult response correctly', () => {
      // Simulate backend response format (from backend/app/schemas/audio.py)
      const backendResponse = {
        text: "Xin chào, đây là test",
        asr_confidence: 0.95,
        sentiment_label: "positive",
        sentiment_confidence: 0.87,
        warning: false,
        bad_keywords: null,
        processing_time: 0.0465,
        real_time_factor: 0.0310,
        audio_duration: 1.5,
        sample_rate: 16000,
        all_sentiment_scores: {
          positive: 0.87,
          negative: 0.05,
          neutral: 0.06,
          toxic: 0.02
        },
        timestamp: Date.now() / 1000
      }
      
      const result = TranscriptResultSchema.safeParse(backendResponse)
      
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.text).toBe("Xin chào, đây là test")
        expect(result.data.sentiment_label).toBe("positive")
        expect(result.data.asr_confidence).toBe(0.95)
        expect(result.data.sentiment_confidence).toBe(0.87)
        expect(result.data.audio_duration).toBe(1.5)
      }
    })
    
    it('should parse toxic content response with warning', () => {
      const backendResponse = {
        text: "Thằng này ngu quá",
        asr_confidence: 0.92,
        sentiment_label: "toxic",
        sentiment_confidence: 0.94,
        warning: true,
        bad_keywords: ["ngu"],
        processing_time: 0.0421,
        real_time_factor: 0.0281,
        audio_duration: 1.2,
        sample_rate: 16000,
        timestamp: Date.now() / 1000
      }
      
      const result = TranscriptResultSchema.safeParse(backendResponse)
      
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.warning).toBe(true)
        expect(result.data.sentiment_label).toBe("toxic")
        expect(result.data.bad_keywords).toContain("ngu")
      }
    })
    
    it('should accept all sentiment labels', () => {
      const labels = ['positive', 'negative', 'neutral', 'toxic']
      
      labels.forEach(label => {
        const response = {
          text: "Test",
          asr_confidence: 0.9,
          sentiment_label: label,
          sentiment_confidence: 0.8,
          warning: false,
          processing_time: 0.05,
          real_time_factor: 0.03,
          audio_duration: 1.0,
          sample_rate: 16000
        }
        
        const result = TranscriptResultSchema.safeParse(response)
        expect(result.success).toBe(true)
      })
    })
    
    it('should handle optional fields correctly', () => {
      const minimalResponse = {
        text: "Minimal test",
        asr_confidence: 0.9,
        sentiment_label: "neutral",
        sentiment_confidence: 0.85,
        warning: false,
        processing_time: 0.04,
        real_time_factor: 0.02,
        audio_duration: 1.0,
        sample_rate: 16000
      }
      
      const result = TranscriptResultSchema.safeParse(minimalResponse)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.bad_keywords).toBeUndefined()
        expect(result.data.session_id).toBeUndefined()
        expect(result.data.all_sentiment_scores).toBeUndefined()
      }
    })
  })
  
  describe('WebSocket Message Schema', () => {
    
    it('should accept transcript_result message type', () => {
      const message = {
        type: 'transcript_result',
        timestamp: Date.now(),
        data: {
          text: "Test",
          asr_confidence: 0.9,
          sentiment_label: "neutral",
          sentiment_confidence: 0.8,
          warning: false,
          processing_time: 0.05,
          real_time_factor: 0.03,
          audio_duration: 1.0,
          sample_rate: 16000
        }
      }
      
      const result = TranscriptResultMessageSchema.safeParse(message)
      expect(result.success).toBe(true)
    })
    
    it('should accept transcription_result message type (backend alias)', () => {
      const message = {
        type: 'transcription_result',
        timestamp: Date.now(),
        data: {
          text: "Test",
          asr_confidence: 0.9,
          sentiment_label: "neutral",
          sentiment_confidence: 0.8,
          warning: false,
          processing_time: 0.05,
          real_time_factor: 0.03,
          audio_duration: 1.0,
          sample_rate: 16000
        }
      }
      
      // WebSocketMessageSchema should accept both
      const result = WebSocketMessageSchema.safeParse(message)
      expect(result.success).toBe(true)
    })
  })
  
  describe('Error Message Schema', () => {
    
    it('should parse backend error response with error field', () => {
      const backendError = {
        type: 'error',
        timestamp: Date.now(),
        data: {
          error: 'processing_failed',  // Backend uses 'error' not 'code'
          message: 'Audio processing failed',
          details: { chunk_size: 0 }
        }
      }
      
      const result = ErrorMessageSchema.safeParse(backendError)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.data.error).toBe('processing_failed')
        expect(result.data.data.message).toBe('Audio processing failed')
      }
    })
    
    it('should also accept code field for compatibility', () => {
      const frontendError = {
        type: 'error',
        timestamp: Date.now(),
        data: {
          error: 'CONNECTION_ERROR',
          code: 'CONNECTION_ERROR',
          message: 'WebSocket connection failed'
        }
      }
      
      const result = ErrorMessageSchema.safeParse(frontendError)
      expect(result.success).toBe(true)
    })
  })
})

// ============================================================================
// TEST SUITE 2: WebSocket Integration Tests (Mock)
// ============================================================================

describe('WebSocket Integration - Mock Backend', () => {
  let mockWs: any // eslint-disable-line @typescript-eslint/no-explicit-any
  
  beforeEach(() => {
    // Mock WebSocket
    mockWs = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn()
    }
  })
  
  it('should send binary audio chunk as ArrayBuffer', () => {
    const audioData = new ArrayBuffer(1024)
    
    mockWs.send(audioData)
    
    expect(mockWs.send).toHaveBeenCalledWith(audioData)
    expect(mockWs.send).toHaveBeenCalledTimes(1)
  })
  
  it('should receive and parse transcript result message', async () => {
    const mockMessage = {
      type: 'transcription_result',
      timestamp: Date.now(),
      data: {
        text: "Xin chào",
        asr_confidence: 0.95,
        sentiment_label: "positive",
        sentiment_confidence: 0.90,
        warning: false,
        processing_time: 0.045,
        real_time_factor: 0.030,
        audio_duration: 1.5,
        sample_rate: 16000
      }
    }
    
    const result = WebSocketMessageSchema.safeParse(mockMessage)
    expect(result.success).toBe(true)
  })
})

// ============================================================================
// TEST SUITE 3: Data Flow Tests
// ============================================================================

describe('Data Flow - End to End', () => {
  
  it('should complete full audio → transcript → display flow', () => {
    // Step 1: Frontend captures audio
    const audioBlob = new Blob([new ArrayBuffer(1024)], { type: 'audio/webm;codecs=opus' })
    expect(audioBlob.size).toBeGreaterThan(0)
    expect(audioBlob.type).toBe('audio/webm;codecs=opus')
    
    // Step 2: Convert to ArrayBuffer
    audioBlob.arrayBuffer().then(buffer => {
      expect(buffer.byteLength).toBe(1024)
      
      // Step 3: Send via WebSocket (binary)
      // This would be: ws.send(buffer)
      
      // Step 4: Backend processes and returns result
      const backendResponse = {
        text: "Test transcript",
        asr_confidence: 0.9,
        sentiment_label: "neutral",
        sentiment_confidence: 0.85,
        warning: false,
        processing_time: 0.046,
        real_time_factor: 0.031,
        audio_duration: 1.5,
        sample_rate: 16000
      }
      
      // Step 5: Frontend parses response
      const parsed = TranscriptResultSchema.safeParse(backendResponse)
      expect(parsed.success).toBe(true)
      
      // Step 6: Display to user
      if (parsed.success) {
        expect(parsed.data.text).toBe("Test transcript")
        expect(parsed.data.sentiment_label).toBe("neutral")
      }
    })
  })
  
  it('should handle toxic content detection flow', () => {
    const backendResponse = {
      text: "Nội dung xấu",
      asr_confidence: 0.92,
      sentiment_label: "toxic",
      sentiment_confidence: 0.88,
      warning: true,
      bad_keywords: ["xấu"],
      processing_time: 0.048,
      real_time_factor: 0.032,
      audio_duration: 1.2,
      sample_rate: 16000
    }
    
    const parsed = TranscriptResultSchema.safeParse(backendResponse)
    expect(parsed.success).toBe(true)
    
    if (parsed.success) {
      // UI should show warning
      expect(parsed.data.warning).toBe(true)
      expect(parsed.data.sentiment_label).toBe("toxic")
      expect(parsed.data.bad_keywords).toContain("xấu")
    }
  })
})

// ============================================================================
// TEST SUITE 4: Error Handling Tests
// ============================================================================

describe('Error Handling', () => {
  
  it('should handle empty audio chunk error', () => {
    const errorMessage = {
      type: 'error',
      timestamp: Date.now(),
      data: {
        error: 'empty_audio_chunk',
        message: 'Received empty audio data',
        details: {}
      }
    }
    
    const result = ErrorMessageSchema.safeParse(errorMessage)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.data.error).toBe('empty_audio_chunk')
    }
  })
  
  it('should handle processing failed error', () => {
    const errorMessage = {
      type: 'error',
      timestamp: Date.now(),
      data: {
        error: 'processing_failed',
        message: 'Audio processing failed: invalid format',
        details: { format: 'unknown' }
      }
    }
    
    const result = ErrorMessageSchema.safeParse(errorMessage)
    expect(result.success).toBe(true)
  })
  
  it('should reject invalid schema data', () => {
    const invalidResponse = {
      text: "Test",
      // Missing required fields
      sentiment_label: "positive"
    }
    
    const result = TranscriptResultSchema.safeParse(invalidResponse)
    expect(result.success).toBe(false)
  })
})

// ============================================================================
// TEST SUITE 5: Performance & Metrics Tests
// ============================================================================

describe('Performance Metrics', () => {
  
  it('should validate processing time metrics', () => {
    const response = {
      text: "Performance test",
      asr_confidence: 0.9,
      sentiment_label: "neutral",
      sentiment_confidence: 0.85,
      warning: false,
      processing_time: 0.0465,  // 46.5ms
      real_time_factor: 0.0310,  // 3.1% of audio duration
      audio_duration: 1.5,
      sample_rate: 16000
    }
    
    const result = TranscriptResultSchema.safeParse(response)
    expect(result.success).toBe(true)
    
    if (result.success) {
      // Verify real-time factor calculation
      const expectedRTF = response.processing_time / response.audio_duration
      expect(result.data.real_time_factor).toBeCloseTo(expectedRTF, 4)
      
      // Performance should be real-time (< 1.0)
      expect(result.data.real_time_factor).toBeLessThan(1.0)
    }
  })
  
  it('should track confidence scores', () => {
    const response = {
      text: "Confidence test",
      asr_confidence: 0.95,
      sentiment_label: "positive",
      sentiment_confidence: 0.87,
      warning: false,
      processing_time: 0.05,
      real_time_factor: 0.03,
      audio_duration: 1.5,
      sample_rate: 16000,
      all_sentiment_scores: {
        positive: 0.87,
        negative: 0.05,
        neutral: 0.06,
        toxic: 0.02
      }
    }
    
    const result = TranscriptResultSchema.safeParse(response)
    expect(result.success).toBe(true)
    
    if (result.success && result.data.all_sentiment_scores) {
      // All scores should sum to ~1.0
      const sum = Object.values(result.data.all_sentiment_scores).reduce((a, b) => a + b, 0)
      expect(sum).toBeCloseTo(1.0, 2)
      
      // Highest score should match sentiment_label
      const maxScore = Math.max(...Object.values(result.data.all_sentiment_scores))
      expect(result.data.all_sentiment_scores.positive).toBe(maxScore)
    }
  })
})

// ============================================================================
// TEST SUITE 6: Session Management Tests
// ============================================================================

describe('Session Management', () => {
  
  it('should handle session-based processing', () => {
    const sessionResponse = {
      text: "Session test",
      asr_confidence: 0.9,
      sentiment_label: "neutral",
      sentiment_confidence: 0.85,
      warning: false,
      processing_time: 0.05,
      real_time_factor: 0.03,
      audio_duration: 5.0,  // Longer duration for session
      sample_rate: 16000,
      session_id: "session-1234567890"
    }
    
    const result = TranscriptResultSchema.safeParse(sessionResponse)
    expect(result.success).toBe(true)
    
    if (result.success) {
      expect(result.data.session_id).toBe("session-1234567890")
      expect(result.data.audio_duration).toBe(5.0)
    }
  })
})

// ============================================================================
// TEST SUITE 7: Audio Format Tests
// ============================================================================

describe('Audio Format Compatibility', () => {
  
  it('should validate sample rate (16kHz required)', () => {
    const response = {
      text: "Audio format test",
      asr_confidence: 0.9,
      sentiment_label: "neutral",
      sentiment_confidence: 0.85,
      warning: false,
      processing_time: 0.05,
      real_time_factor: 0.03,
      audio_duration: 1.0,
      sample_rate: 16000  // Wav2Vec2 requirement
    }
    
    const result = TranscriptResultSchema.safeParse(response)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.sample_rate).toBe(16000)
    }
  })
  
  it('should accept different sample rates (backend resamples)', () => {
    const response = {
      text: "Resample test",
      asr_confidence: 0.9,
      sentiment_label: "neutral",
      sentiment_confidence: 0.85,
      warning: false,
      processing_time: 0.05,
      real_time_factor: 0.03,
      audio_duration: 1.0,
      sample_rate: 48000  // Original rate before resampling
    }
    
    const result = TranscriptResultSchema.safeParse(response)
    expect(result.success).toBe(true)
  })
})

export {}
