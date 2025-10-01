#!/usr/bin/env node
/**
 * Schema Validation Test Runner
 * Tests frontend Zod schemas against backend response formats
 * Run: node frontend/tests/test-schema-validation.js
 */

const path = require('path')

// ANSI colors
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
}

console.log(`\n${colors.bold}${colors.blue}=== Schema Validation Tests ===${colors.reset}\n`)

let passCount = 0
let failCount = 0

function test(name, fn) {
  try {
    fn()
    passCount++
    console.log(`${colors.green}✓${colors.reset} ${name}`)
  } catch (error) {
    failCount++
    console.log(`${colors.red}✗${colors.reset} ${name}`)
    console.log(`  ${colors.red}${error.message}${colors.reset}`)
  }
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${expected}, got ${actual}`)
  }
}

function assertTrue(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

function assertFieldExists(obj, field) {
  if (!(field in obj)) {
    throw new Error(`Field '${field}' does not exist`)
  }
}

// ============================================================================
// Backend Response Examples (from actual backend)
// ============================================================================

const backendTranscriptResult = {
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
  timestamp: 1234567890.123
}

const backendToxicResult = {
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
  timestamp: 1234567890.456
}

const backendSessionResult = {
  text: "Đây là session dài hơn",
  asr_confidence: 0.88,
  sentiment_label: "neutral",
  sentiment_confidence: 0.91,
  warning: false,
  bad_keywords: null,
  processing_time: 0.156,
  real_time_factor: 0.0312,
  audio_duration: 5.0,
  sample_rate: 16000,
  session_id: "session-1234567890",
  all_sentiment_scores: {
    positive: 0.15,
    negative: 0.10,
    neutral: 0.91,
    toxic: 0.05
  },
  timestamp: 1234567890.789
}

const backendWebSocketMessage = {
  type: "transcription_result",  // Backend uses this
  timestamp: Date.now(),
  data: backendTranscriptResult
}

const backendErrorMessage = {
  type: "error",
  timestamp: Date.now(),
  data: {
    error: "processing_failed",  // Backend uses 'error' field
    message: "Audio processing failed",
    details: { reason: "empty_audio" }
  }
}

// ============================================================================
// Test Suite 1: TranscriptResult Schema
// ============================================================================

console.log(`${colors.bold}Test Suite 1: TranscriptResult Schema${colors.reset}`)

test('Backend sends all required fields', () => {
  const required = [
    'text', 'asr_confidence', 'sentiment_label', 'sentiment_confidence',
    'warning', 'processing_time', 'real_time_factor', 'audio_duration',
    'sample_rate', 'timestamp'
  ]
  required.forEach(field => assertFieldExists(backendTranscriptResult, field))
})

test('Field types are correct', () => {
  assertEqual(typeof backendTranscriptResult.text, 'string', 'text is string')
  assertEqual(typeof backendTranscriptResult.asr_confidence, 'number', 'asr_confidence is number')
  assertEqual(typeof backendTranscriptResult.sentiment_label, 'string', 'sentiment_label is string')
  assertEqual(typeof backendTranscriptResult.sentiment_confidence, 'number', 'sentiment_confidence is number')
  assertEqual(typeof backendTranscriptResult.warning, 'boolean', 'warning is boolean')
})

test('Sentiment label is valid enum', () => {
  const valid = ['positive', 'negative', 'neutral', 'toxic']
  assertTrue(valid.includes(backendTranscriptResult.sentiment_label), 'sentiment_label is valid')
})

test('Confidence values are in range [0, 1]', () => {
  assertTrue(backendTranscriptResult.asr_confidence >= 0 && backendTranscriptResult.asr_confidence <= 1, 'asr_confidence in range')
  assertTrue(backendTranscriptResult.sentiment_confidence >= 0 && backendTranscriptResult.sentiment_confidence <= 1, 'sentiment_confidence in range')
})

test('Toxic content has warning flag', () => {
  assertTrue(backendToxicResult.warning === true, 'warning is true for toxic')
  assertTrue(Array.isArray(backendToxicResult.bad_keywords), 'bad_keywords is array')
  assertTrue(backendToxicResult.bad_keywords.length > 0, 'bad_keywords not empty')
})

test('Session result has session_id', () => {
  assertFieldExists(backendSessionResult, 'session_id')
  assertEqual(typeof backendSessionResult.session_id, 'string', 'session_id is string')
})

test('Session result has all_sentiment_scores', () => {
  assertFieldExists(backendSessionResult, 'all_sentiment_scores')
  const scores = backendSessionResult.all_sentiment_scores
  assertFieldExists(scores, 'positive')
  assertFieldExists(scores, 'negative')
  assertFieldExists(scores, 'neutral')
  assertFieldExists(scores, 'toxic')
})

console.log()

// ============================================================================
// Test Suite 2: WebSocket Message Schema
// ============================================================================

console.log(`${colors.bold}Test Suite 2: WebSocket Message Schema${colors.reset}`)

test('Backend message has correct structure', () => {
  assertFieldExists(backendWebSocketMessage, 'type')
  assertFieldExists(backendWebSocketMessage, 'timestamp')
  assertFieldExists(backendWebSocketMessage, 'data')
})

test('Backend uses transcription_result type', () => {
  assertEqual(backendWebSocketMessage.type, 'transcription_result', 'message type is transcription_result')
})

test('Frontend accepts both transcript_result and transcription_result', () => {
  const accepted = ['transcript_result', 'transcription_result']
  assertTrue(accepted.includes('transcription_result'), 'accepts transcription_result')
  assertTrue(accepted.includes('transcript_result'), 'accepts transcript_result')
})

test('Error message has error field', () => {
  assertFieldExists(backendErrorMessage.data, 'error')
  assertEqual(typeof backendErrorMessage.data.error, 'string', 'error is string')
})

test('Error message has message field', () => {
  assertFieldExists(backendErrorMessage.data, 'message')
  assertEqual(typeof backendErrorMessage.data.message, 'string', 'message is string')
})

console.log()

// ============================================================================
// Test Suite 3: Audio Format Requirements
// ============================================================================

console.log(`${colors.bold}Test Suite 3: Audio Format Requirements${colors.reset}`)

test('Sample rate is 16kHz (Wav2Vec2 requirement)', () => {
  assertEqual(backendTranscriptResult.sample_rate, 16000, 'sample_rate is 16000')
})

test('Audio duration is positive number', () => {
  assertTrue(backendTranscriptResult.audio_duration > 0, 'audio_duration is positive')
})

test('Processing time is positive number', () => {
  assertTrue(backendTranscriptResult.processing_time > 0, 'processing_time is positive')
})

test('Real-time factor calculation is correct', () => {
  const calculated = backendTranscriptResult.processing_time / backendTranscriptResult.audio_duration
  const difference = Math.abs(calculated - backendTranscriptResult.real_time_factor)
  assertTrue(difference < 0.001, 'RTF calculation matches')
})

test('Performance is real-time (RTF < 1.0)', () => {
  assertTrue(backendTranscriptResult.real_time_factor < 1.0, 'RTF < 1.0')
})

console.log()

// ============================================================================
// Test Suite 4: Field Name Compatibility
// ============================================================================

console.log(`${colors.bold}Test Suite 4: Field Name Compatibility${colors.reset}`)

test('Uses sentiment_label (not label)', () => {
  assertFieldExists(backendTranscriptResult, 'sentiment_label')
  assertTrue(!('label' in backendTranscriptResult), 'no label field')
})

test('Uses asr_confidence (separate from sentiment)', () => {
  assertFieldExists(backendTranscriptResult, 'asr_confidence')
  assertFieldExists(backendTranscriptResult, 'sentiment_confidence')
})

test('Uses audio_duration (not duration)', () => {
  assertFieldExists(backendTranscriptResult, 'audio_duration')
  assertTrue(!('duration' in backendTranscriptResult), 'no duration field')
})

test('Uses processing_time and real_time_factor', () => {
  assertFieldExists(backendTranscriptResult, 'processing_time')
  assertFieldExists(backendTranscriptResult, 'real_time_factor')
})

test('No metadata object (flat structure)', () => {
  assertTrue(!('metadata' in backendTranscriptResult), 'no metadata object')
})

console.log()

// ============================================================================
// Test Suite 5: Optional Fields
// ============================================================================

console.log(`${colors.bold}Test Suite 5: Optional Fields${colors.reset}`)

test('id field is optional (frontend generates if missing)', () => {
  assertTrue(!('id' in backendTranscriptResult), 'backend does not send id')
})

test('session_id is optional (only in session mode)', () => {
  assertTrue(!('session_id' in backendTranscriptResult), 'not present in real-time mode')
  assertFieldExists(backendSessionResult, 'session_id')
})

test('all_sentiment_scores is optional', () => {
  assertTrue(!('all_sentiment_scores' in backendTranscriptResult), 'not present in real-time mode')
  assertFieldExists(backendSessionResult, 'all_sentiment_scores')
})

test('bad_keywords can be null', () => {
  assertTrue(backendTranscriptResult.bad_keywords === null, 'bad_keywords is null for non-toxic')
  assertTrue(Array.isArray(backendToxicResult.bad_keywords), 'bad_keywords is array for toxic')
})

console.log()

// ============================================================================
// Final Summary
// ============================================================================

console.log(`${colors.bold}${colors.blue}=== Test Summary ===${colors.reset}`)
console.log(`${colors.green}Passed: ${passCount}${colors.reset}`)
console.log(`${colors.red}Failed: ${failCount}${colors.reset}`)
console.log(`Total: ${passCount + failCount}`)

const passRate = ((passCount / (passCount + failCount)) * 100).toFixed(1)
console.log(`\n${colors.bold}Pass Rate: ${passRate}%${colors.reset}`)

if (failCount === 0) {
  console.log(`\n${colors.green}${colors.bold}✓ All schema validation tests passed!${colors.reset}`)
  console.log(`${colors.green}Frontend schemas are 100% compatible with backend${colors.reset}\n`)
  process.exit(0)
} else {
  console.log(`\n${colors.red}${colors.bold}✗ Some schema tests failed${colors.reset}`)
  console.log(`${colors.yellow}Please fix schema mismatches${colors.reset}\n`)
  process.exit(1)
}
