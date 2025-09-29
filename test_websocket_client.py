#!/usr/bin/env python3
"""
Simple WebSocket client to test audio chunk transmission
"""

import asyncio
import websockets
import json

async def test_audio_transmission():
    uri = "ws://127.0.0.1:8000/v1/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Send some dummy audio data
            dummy_audio = b'\x00' * 1024  # 1KB of dummy audio data
            await websocket.send(dummy_audio)
            print(f"Sent {len(dummy_audio)} bytes of dummy audio data")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received response: {response_data}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_audio_transmission())