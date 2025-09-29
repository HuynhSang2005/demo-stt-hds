#!/usr/bin/env python3
"""
Test script to verify end-to-end Vietnamese STT + toxic detection pipeline
"""

import asyncio
import websockets
import json
import struct
from pathlib import Path

async def test_audio_file_processing():
    """Test processing a real Vietnamese audio file"""
    audio_file = Path("wav2vec2-base-vietnamese-250h/audio-test/t1_0001-00010.wav")
    
    if not audio_file.exists():
        print(f"Audio file not found: {audio_file}")
        return
    
    # Read the audio file
    with open(audio_file, 'rb') as f:
        audio_data = f.read()
    
    print(f"Loaded audio file: {audio_file}")
    print(f"Audio data size: {len(audio_data)} bytes")
    
    # Test session-based processing
    uri = "ws://127.0.0.1:8000/v1/ws/session"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Start session
            start_message = {
                "type": "session_command",
                "command": "start",
                "session_id": None
            }
            await websocket.send(json.dumps(start_message))
            
            # Wait for session start response
            response = await websocket.recv()
            session_data = json.loads(response)
            print(f"Session started: {session_data}")
            
            session_id = session_data.get('data', {}).get('session_id')
            if not session_id:
                print("Failed to get session ID")
                return
            
            # Send audio data in chunks (simulate real-time)
            chunk_size = 4096  # 4KB chunks
            total_chunks = (len(audio_data) + chunk_size - 1) // chunk_size
            
            print(f"Sending audio in {total_chunks} chunks...")
            
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                await websocket.send(chunk)
                print(f"Sent chunk {i//chunk_size + 1}/{total_chunks} ({len(chunk)} bytes)")
                
                # Small delay to simulate real-time streaming
                await asyncio.sleep(0.1)
            
            # End session
            end_message = {
                "type": "session_command", 
                "command": "end",
                "session_id": session_id
            }
            await websocket.send(json.dumps(end_message))
            
            # Wait for final result
            response = await websocket.recv()
            result_data = json.loads(response)
            print(f"Final result: {result_data}")
            
            # Analyze the result
            if 'data' in result_data:
                data = result_data['data']
                transcript = data.get('transcript', 'No transcript')
                sentiment = data.get('sentiment', {})
                
                print(f"\n=== PROCESSING RESULTS ===")
                print(f"Transcript: {transcript}")
                print(f"Confidence: {data.get('confidence', 'N/A')}")
                print(f"Language: {data.get('language', 'N/A')}")
                print(f"Sentiment: {sentiment.get('label', 'N/A')}")
                print(f"Sentiment Confidence: {sentiment.get('confidence', 'N/A')}")
                print(f"Is Toxic: {sentiment.get('is_toxic', 'N/A')}")
                print(f"Processing Time: {data.get('processing_time', 'N/A')}s")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_audio_file_processing())