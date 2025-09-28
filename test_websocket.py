#!/usr/bin/env python3
"""
WebSocket Client để test Vietnamese Speech-to-Text + Toxic Detection API
Test với audio files thật từ ./wav2vec2-base-vietnamese-250h/audio-test/
"""

import asyncio
import websockets
import json
import pathlib
import sys
from typing import Optional


class WebSocketAudioTester:
    def __init__(self, ws_url: str = "ws://127.0.0.1:8000/v1/ws"):
        self.ws_url = ws_url
        
    async def test_audio_file(self, audio_path: pathlib.Path) -> Optional[dict]:
        """Test audio file qua WebSocket"""
        if not audio_path.exists():
            print(f"❌ File không tồn tại: {audio_path}")
            return None
            
        print(f"🎤 Testing: {audio_path.name}")
        
        try:
            # Read binary audio
            audio_data = audio_path.read_bytes()
            print(f"   📊 Audio size: {len(audio_data):,} bytes")
            
            # Connect WebSocket
            async with websockets.connect(self.ws_url) as websocket:
                print(f"   🔗 Connected to {self.ws_url}")
                
                # Send binary audio
                await websocket.send(audio_data)
                print(f"   📤 Sent binary audio data")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                result = json.loads(response)
                
                print(f"   ✅ Response received:")
                print(f"      📝 Text: '{result.get('text', 'N/A')}'")
                print(f"      😡 Toxic: {result.get('is_toxic', False)}")
                print(f"      🏷️  Label: {result.get('label', 'N/A')}")
                print(f"      🎯 Confidence: {result.get('confidence', 0):.3f}")
                print(f"      ⏱️  Processing: {result.get('processing_time', 0):.3f}s")
                
                return result
                
        except asyncio.TimeoutError:
            print(f"   ⏱️  Timeout sau 30s")
            return None
        except Exception as ws_error:
            if "websocket" in str(ws_error).lower():
                print(f"   🔌 WebSocket error: {ws_error}")
            else:
                print(f"   🔌 Connection error: {ws_error}")
            return None
        except json.JSONDecodeError as e:
            print(f"   📄 JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return None

    async def test_all_samples(self):
        """Test tất cả audio samples"""
        audio_dir = pathlib.Path("./wav2vec2-base-vietnamese-250h/audio-test")
        
        if not audio_dir.exists():
            print(f"❌ Audio test directory không tồn tại: {audio_dir}")
            return
            
        wav_files = list(audio_dir.glob("*.wav"))
        if not wav_files:
            print(f"❌ Không tìm thấy .wav files trong {audio_dir}")
            return
            
        print(f"🧪 VIETNAMESE SPEECH-TO-TEXT + TOXIC DETECTION - WEBSOCKET TEST")
        print(f"{'='*70}")
        print(f"📂 Audio directory: {audio_dir}")
        print(f"🎵 Found {len(wav_files)} audio files")
        print(f"🌐 WebSocket URL: {self.ws_url}")
        print(f"{'='*70}")
        
        results = []
        for audio_file in sorted(wav_files):
            result = await self.test_audio_file(audio_file)
            if result:
                results.append({
                    "file": audio_file.name,
                    "result": result
                })
            print()  # Empty line for readability
        
        # Summary
        print(f"📊 TEST SUMMARY")
        print(f"{'='*50}")
        print(f"   Total files tested: {len(wav_files)}")
        print(f"   Successful responses: {len(results)}")
        print(f"   Success rate: {len(results)/len(wav_files)*100:.1f}%")
        
        if results:
            toxic_count = sum(1 for r in results if r["result"].get("is_toxic", False))
            avg_processing = sum(r["result"].get("processing_time", 0) for r in results) / len(results)
            print(f"   Toxic detections: {toxic_count}/{len(results)}")
            print(f"   Avg processing time: {avg_processing:.3f}s")
        
        return results


async def main():
    """Main test function"""
    if len(sys.argv) > 1:
        ws_url = sys.argv[1]
    else:
        ws_url = "ws://127.0.0.1:8000/v1/ws"
    
    tester = WebSocketAudioTester(ws_url)
    await tester.test_all_samples()


if __name__ == "__main__":
    asyncio.run(main())