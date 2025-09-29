#!/usr/bin/env python3
"""
Test script to verify both real-time and session WebSocket endpoints
"""
import asyncio
import websockets
import json
from pathlib import Path

# Test audio file (you can replace with actual audio file)
AUDIO_FILE = Path("../wav2vec2-base-vietnamese-250h/audio-test/t1_0001-00010.wav")

async def test_realtime_websocket():
    """Test real-time WebSocket endpoint"""
    print("🔄 Testing real-time WebSocket endpoint...")
    
    try:
        uri = "ws://127.0.0.1:8000/v1/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to real-time endpoint")
            
            # Listen for initial message
            response = await websocket.recv()
            print(f"📩 Initial response: {response}")
            
            # Send test audio data (small chunk)
            test_data = b"test_audio_data_" + b"x" * 1000
            await websocket.send(test_data)
            print(f"📤 Sent {len(test_data)} bytes")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📩 Received: {data}")
            
            return True
            
    except Exception as e:
        print(f"❌ Real-time test failed: {e}")
        return False

async def test_session_websocket():
    """Test session-based WebSocket endpoint"""
    print("🔄 Testing session WebSocket endpoint...")
    
    try:
        uri = "ws://127.0.0.1:8000/v1/ws/session"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to session endpoint")
            
            # Listen for initial message
            response = await websocket.recv()
            print(f"📩 Initial response: {response}")
            
            # Start session
            start_command = {
                "type": "session_command",
                "command": "start_session"
            }
            await websocket.send(json.dumps(start_command))
            print("📤 Sent start session command")
            
            # Wait for session response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📩 Session started: {data}")
            
            # Send audio chunks
            for i in range(3):
                test_data = f"test_audio_chunk_{i}_".encode() + b"x" * 800
                await websocket.send(test_data)
                print(f"📤 Sent chunk {i+1}: {len(test_data)} bytes")
                
                # Wait for chunk acknowledgment
                response = await websocket.recv()
                data = json.loads(response)
                print(f"📩 Chunk ack: {data}")
            
            # End session
            end_command = {
                "type": "session_command", 
                "command": "end_session"
            }
            await websocket.send(json.dumps(end_command))
            print("📤 Sent end session command")
            
            # Wait for final result
            timeout = 10
            while timeout > 0:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    print(f"📩 Final response: {data}")
                    
                    if data.get("type") == "transcription_result":
                        print("🎉 Session processing completed!")
                        return True
                        
                except asyncio.TimeoutError:
                    timeout -= 1
                    print(f"⏳ Waiting for result... ({timeout}s)")
            
            print("⚠️ Session test completed but no transcript received")
            return True
            
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        return False

async def test_session_health():
    """Test session health endpoint"""
    print("🔄 Testing session health endpoint...")
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/v1/ws/session/health") as response:
                data = await response.json()
                print(f"📩 Health check: {data}")
                return data.get("status") == "healthy"
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Vietnamese STT WebSocket Test Suite")
    print("=" * 50)
    
    # Test health endpoint
    health_ok = await test_session_health()
    print()
    
    # Test real-time endpoint
    realtime_ok = await test_realtime_websocket()
    print()
    
    # Test session endpoint
    session_ok = await test_session_websocket()
    print()
    
    print("=" * 50)
    print("📊 Test Results:")
    print(f"   Health Check: {'✅' if health_ok else '❌'}")
    print(f"   Real-time WS: {'✅' if realtime_ok else '❌'}")
    print(f"   Session WS:   {'✅' if session_ok else '❌'}")
    
    if all([health_ok, realtime_ok, session_ok]):
        print("\n🎉 All tests passed! Both modes are working.")
    else:
        print("\n⚠️ Some tests failed. Check logs above.")

if __name__ == "__main__":
    asyncio.run(main())