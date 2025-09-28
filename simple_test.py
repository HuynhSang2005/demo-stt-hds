#!/usr/bin/env python3
"""
Simple WebSocket test để debug connection
"""

import asyncio
import websockets
import json
import pathlib


async def simple_test():
    """Simple WebSocket connection test"""
    ws_url = "ws://127.0.0.1:8000/v1/ws"
    
    try:
        print(f"🔗 Connecting to {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ Connected successfully!")
            
            # Test với file audio nhỏ nhất
            audio_path = pathlib.Path("./wav2vec2-base-vietnamese-250h/audio-test/t2_0000006682.wav")
            if not audio_path.exists():
                print(f"❌ File not found: {audio_path}")
                return
                
            audio_data = audio_path.read_bytes()
            print(f"📤 Sending {len(audio_data)} bytes audio data...")
            
            await websocket.send(audio_data)
            print(f"✅ Data sent, waiting for response...")
            
            # Wait longer for response
            response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
            result = json.loads(response)
            
            print(f"🎉 SUCCESS! Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except asyncio.TimeoutError:
        print(f"⏱️ Timeout waiting for response")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_test())