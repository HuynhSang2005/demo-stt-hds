#!/usr/bin/env python3
"""
Minimal WebSocket test để debug connection
"""

import asyncio
import websockets
import json


async def minimal_test():
    """Minimal connection test"""
    ws_url = "ws://127.0.0.1:8000/v1/ws"
    
    try:
        print(f"🔗 Connecting to {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ Connected!")
            
            # Just wait for any initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📩 Received: {message[:200]}...")
                
                # Send a small test message
                test_data = b"hello"
                print(f"📤 Sending test data: {len(test_data)} bytes")
                await websocket.send(test_data)
                print(f"✅ Test data sent")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"🎉 Response: {response[:200]}...")
                
            except asyncio.TimeoutError:
                print(f"⏱️ No initial message received (timeout)")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(minimal_test())