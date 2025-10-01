#!/usr/bin/env node
/**
 * Real Backend Connection Test
 * Tests actual WebSocket connection to running backend server
 * 
 * Prerequisites:
 * 1. Backend must be running: cd backend && python -m uvicorn app.main:app
 * 2. Run this test: node frontend/tests/test-real-backend-connection.cjs
 */

const WebSocket = require('ws')
const fs = require('fs')
const path = require('path')

// ANSI colors
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
}

let passCount = 0
let failCount = 0
const WS_URL = 'ws://localhost:8000/v1/ws'
const TIMEOUT = 10000 // 10 seconds

console.log(`\n${colors.bold}${colors.blue}=== Real Backend Connection Test ===${colors.reset}`)
console.log(`${colors.cyan}Connecting to: ${WS_URL}${colors.reset}\n`)

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`)
}

function pass(message) {
  passCount++
  log(`✓ ${message}`, 'green')
}

function fail(message, error) {
  failCount++
  log(`✗ ${message}`, 'red')
  if (error) {
    log(`  Error: ${error.message || error}`, 'red')
  }
}

// Test 1: WebSocket Connection
async function testConnection() {
  return new Promise((resolve) => {
    log('\nTest 1: WebSocket Connection', 'bold')
    
    const ws = new WebSocket(WS_URL)
    let connected = false
    
    const timeout = setTimeout(() => {
      if (!connected) {
        fail('Connection timeout (10s)', new Error('Backend not responding'))
        ws.close()
        resolve(false)
      }
    }, TIMEOUT)
    
    ws.on('open', () => {
      connected = true
      clearTimeout(timeout)
      pass('WebSocket connection established')
      ws.close()
      resolve(true)
    })
    
    ws.on('error', (error) => {
      clearTimeout(timeout)
      fail('WebSocket connection failed', error)
      resolve(false)
    })
  })
}

// Test 2: Send Audio Chunk
async function testSendAudioChunk() {
  return new Promise((resolve) => {
    log('\nTest 2: Send Audio Chunk', 'bold')
    
    const ws = new WebSocket(WS_URL)
    let messageReceived = false
    
    const timeout = setTimeout(() => {
      if (!messageReceived) {
        fail('No response from backend', new Error('Timeout waiting for response'))
        ws.close()
        resolve(false)
      }
    }, TIMEOUT)
    
    ws.on('open', () => {
      // Send empty audio chunk (will trigger error response)
      const emptyBuffer = Buffer.alloc(0)
      ws.send(emptyBuffer)
      pass('Sent audio chunk to backend')
    })
    
    ws.on('message', (data) => {
      messageReceived = true
      clearTimeout(timeout)
      
      try {
        const message = JSON.parse(data.toString())
        pass(`Received message type: ${message.type}`)
        
        if (message.type === 'error') {
          pass('Backend correctly returned error for empty audio')
          if (message.data && message.data.error) {
            pass(`Error field present: ${message.data.error}`)
          }
        }
        
        ws.close()
        resolve(true)
      } catch (error) {
        fail('Failed to parse message', error)
        ws.close()
        resolve(false)
      }
    })
    
    ws.on('error', (error) => {
      clearTimeout(timeout)
      fail('WebSocket error', error)
      resolve(false)
    })
  })
}

// Test 3: Receive TranscriptResult
async function testReceiveTranscript() {
  return new Promise((resolve) => {
    log('\nTest 3: Receive TranscriptResult (with real audio)', 'bold')
    
    // Check if test audio file exists
    const audioPath = path.join(__dirname, '../../wav2vec2-base-vietnamese-250h/audio-test/t1_0001-00010.wav')
    
    if (!fs.existsSync(audioPath)) {
      log(`⚠ Test audio not found: ${audioPath}`, 'yellow')
      log('  Skipping real audio test', 'yellow')
      resolve(true)
      return
    }
    
    const ws = new WebSocket(WS_URL)
    let transcriptReceived = false
    
    const timeout = setTimeout(() => {
      if (!transcriptReceived) {
        fail('No transcript received', new Error('Timeout waiting for transcript'))
        ws.close()
        resolve(false)
      }
    }, TIMEOUT)
    
    ws.on('open', () => {
      // Send real audio file
      const audioBuffer = fs.readFileSync(audioPath)
      ws.send(audioBuffer)
      pass(`Sent real audio file (${audioBuffer.length} bytes)`)
    })
    
    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString())
        
        if (message.type === 'transcription_result' || message.type === 'transcript_result') {
          transcriptReceived = true
          clearTimeout(timeout)
          
          pass(`Received transcript: "${message.data.text}"`)
          
          // Validate TranscriptResult schema
          const required = [
            'text', 'asr_confidence', 'sentiment_label', 'sentiment_confidence',
            'warning', 'processing_time', 'real_time_factor', 'audio_duration', 'sample_rate'
          ]
          
          let allFieldsPresent = true
          required.forEach(field => {
            if (!(field in message.data)) {
              fail(`Missing required field: ${field}`)
              allFieldsPresent = false
            }
          })
          
          if (allFieldsPresent) {
            pass('All required fields present in TranscriptResult')
          }
          
          // Validate field types
          if (message.data.sentiment_label && typeof message.data.sentiment_label === 'string') {
            pass(`Sentiment: ${message.data.sentiment_label} (confidence: ${message.data.sentiment_confidence.toFixed(2)})`)
          }
          
          if (message.data.real_time_factor && message.data.real_time_factor < 1.0) {
            pass(`Real-time performance: RTF = ${message.data.real_time_factor.toFixed(4)} < 1.0`)
          }
          
          if (message.data.sample_rate === 16000) {
            pass('Sample rate: 16kHz (Wav2Vec2 requirement)')
          }
          
          ws.close()
          resolve(true)
        }
      } catch (error) {
        clearTimeout(timeout)
        fail('Failed to parse transcript', error)
        ws.close()
        resolve(false)
      }
    })
    
    ws.on('error', (error) => {
      clearTimeout(timeout)
      fail('WebSocket error', error)
      resolve(false)
    })
  })
}

// Test 4: Ping/Pong
async function testPingPong() {
  return new Promise((resolve) => {
    log('\nTest 4: Ping/Pong Health Check', 'bold')
    
    const ws = new WebSocket(WS_URL)
    let pongReceived = false
    
    const timeout = setTimeout(() => {
      if (!pongReceived) {
        fail('No pong received', new Error('Backend not responding to ping'))
        ws.close()
        resolve(false)
      }
    }, TIMEOUT)
    
    ws.on('open', () => {
      const pingMessage = JSON.stringify({
        type: 'ping',
        timestamp: Date.now()
      })
      ws.send(pingMessage)
      pass('Sent ping message')
    })
    
    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString())
        
        if (message.type === 'pong') {
          pongReceived = true
          clearTimeout(timeout)
          pass('Received pong response')
          
          const latency = Date.now() - message.timestamp
          pass(`Latency: ${latency}ms`)
          
          ws.close()
          resolve(true)
        }
      } catch (error) {
        clearTimeout(timeout)
        fail('Failed to parse pong', error)
        ws.close()
        resolve(false)
      }
    })
    
    ws.on('error', (error) => {
      clearTimeout(timeout)
      fail('WebSocket error', error)
      resolve(false)
    })
  })
}

// Run all tests
async function runTests() {
  log(`${colors.bold}Prerequisites:${colors.reset}`, 'cyan')
  log('1. Backend server must be running:', 'cyan')
  log('   cd backend && python -m uvicorn app.main:app', 'yellow')
  log('2. Ensure models are loaded (may take a few seconds on first run)', 'cyan')
  log('')
  
  const results = []
  
  results.push(await testConnection())
  if (results[0]) {
    results.push(await testSendAudioChunk())
    results.push(await testReceiveTranscript())
    results.push(await testPingPong())
  }
  
  // Summary
  log(`\n${colors.bold}${colors.blue}=== Test Summary ===${colors.reset}`)
  log(`${colors.green}Passed: ${passCount}${colors.reset}`)
  log(`${colors.red}Failed: ${failCount}${colors.reset}`)
  log(`Total: ${passCount + failCount}`)
  
  const passRate = passCount + failCount > 0 
    ? ((passCount / (passCount + failCount)) * 100).toFixed(1)
    : 0
  
  log(`\n${colors.bold}Pass Rate: ${passRate}%${colors.reset}`)
  
  if (failCount === 0 && passCount > 0) {
    log(`\n${colors.green}${colors.bold}✓ All real backend tests passed!${colors.reset}`)
    log(`${colors.green}Frontend-Backend connection: VERIFIED${colors.reset}\n`)
    process.exit(0)
  } else if (passCount === 0 && failCount > 0) {
    log(`\n${colors.red}${colors.bold}✗ Backend connection failed${colors.reset}`)
    log(`${colors.yellow}Make sure backend is running:${colors.reset}`)
    log(`${colors.yellow}  cd backend && python -m uvicorn app.main:app${colors.reset}\n`)
    process.exit(1)
  } else {
    log(`\n${colors.yellow}${colors.bold}⚠ Some tests failed${colors.reset}`)
    log(`${colors.yellow}Please review the failures above${colors.reset}\n`)
    process.exit(1)
  }
}

// Run tests
runTests().catch((error) => {
  log(`\n${colors.red}${colors.bold}Fatal error:${colors.reset}`, 'red')
  log(error.message, 'red')
  process.exit(1)
})
