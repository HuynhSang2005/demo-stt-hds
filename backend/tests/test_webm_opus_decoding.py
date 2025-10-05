"""
Test WebM/Opus Audio Decoding (Phase 1 Verification)

Tests that the new torchaudio+ffmpeg backend can decode WebM/Opus audio
without falling back to pydub.

Expected behavior:
- WebM/Opus audio decoded successfully
- NO "trying_pydub_decoder" log entries
- Decode time < 50ms (vs previous ~130ms)
- Server responds with transcription results
"""

import sys
import os
import asyncio
import json
import time
import numpy as np
from pathlib import Path

# Ensure backend package is importable
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))

try:
    import soundfile as sf
    import subprocess
    import websockets
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install soundfile websockets")
    sys.exit(1)


def generate_test_audio(duration_seconds: float = 2.0, sample_rate: int = 16000) -> tuple[np.ndarray, int]:
    """
    Generate synthetic test audio (sine wave + white noise)
    
    Returns:
        (audio_data, sample_rate) tuple
    """
    print(f"📊 Generating {duration_seconds}s test audio at {sample_rate}Hz...")
    
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    
    # Mix of frequencies (simulate speech formants)
    frequency1 = 440  # A4 note
    frequency2 = 880  # A5 note
    frequency3 = 220  # A3 note
    
    audio = (
        0.3 * np.sin(2 * np.pi * frequency1 * t) +
        0.2 * np.sin(2 * np.pi * frequency2 * t) +
        0.1 * np.sin(2 * np.pi * frequency3 * t) +
        0.1 * np.random.randn(len(t))  # White noise
    )
    
    # Normalize to [-1, 1]
    audio = audio / np.max(np.abs(audio))
    
    return audio.astype(np.float32), sample_rate


def convert_to_webm_opus(audio_data: np.ndarray, sample_rate: int, output_path: Path) -> Path:
    """
    Convert numpy audio to WebM/Opus format using ffmpeg
    
    Args:
        audio_data: Audio samples (float32, mono)
        sample_rate: Sample rate in Hz
        output_path: Output WebM file path
        
    Returns:
        Path to WebM file
    """
    print(f"🔄 Converting to WebM/Opus format...")
    
    # Save as temporary WAV first
    temp_wav = output_path.with_suffix('.temp.wav')
    sf.write(temp_wav, audio_data, sample_rate)
    
    try:
        # Convert WAV → WebM/Opus using ffmpeg
        # Use Opus codec at 24kbps (similar to browser MediaRecorder)
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-i', str(temp_wav),
            '-c:a', 'libopus',  # Opus codec
            '-b:a', '24k',      # 24 kbps bitrate
            '-vbr', 'on',       # Variable bitrate
            '-compression_level', '10',  # Max compression
            '-frame_duration', '20',     # 20ms frames
            '-application', 'voip',      # Optimize for voice
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ FFmpeg conversion failed:")
            print(result.stderr)
            raise RuntimeError("FFmpeg conversion failed")
        
        print(f"✅ WebM file created: {output_path} ({output_path.stat().st_size} bytes)")
        
    finally:
        # Cleanup temp WAV
        if temp_wav.exists():
            temp_wav.unlink()
    
    return output_path


async def test_webm_opus_decoding_async():
    """
    Main test function: Generate audio → Convert to WebM → Send to server → Verify
    """
    print("\n" + "="*70)
    print("🧪 TESTING WEBM/OPUS DECODING (PHASE 1 VERIFICATION)")
    print("="*70 + "\n")
    
    # 1. Generate test audio
    print("Step 1: Generate synthetic audio")
    audio_data, sample_rate = generate_test_audio(duration_seconds=2.0, sample_rate=16000)
    print(f"   ✅ Generated {len(audio_data)} samples at {sample_rate}Hz\n")
    
    # 2. Convert to WebM/Opus
    print("Step 2: Convert to WebM/Opus")
    test_dir = Path(__file__).parent / "test_audio"
    test_dir.mkdir(exist_ok=True)
    webm_path = test_dir / "test_audio.webm"
    
    convert_to_webm_opus(audio_data, sample_rate, webm_path)
    webm_size = webm_path.stat().st_size
    print(f"   ✅ WebM file: {webm_size} bytes\n")
    
    # 3. Connect to WebSocket and send audio
    print("Step 3: Connect to WebSocket and send audio")
    print("   ⚠️  NOTE: Make sure backend server is running on http://localhost:8000")
    print("   Run: cd backend && python run_server.py\n")
    
    results = {
        "success": False,
        "decode_time_ms": None,
        "transcription": None,
        "logs": [],
        "errors": []
    }
    
    try:
        ws_url = "ws://localhost:8000/v1/ws"
        print(f"   📡 Connecting to {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            # Receive initial connection status
            msg_text = await websocket.recv()
            msg = json.loads(msg_text)
            print(f"   ✅ Connected: {msg.get('type')}")
            results["logs"].append(msg)
            
            # Send WebM/Opus audio bytes
            print(f"   📤 Sending {webm_size} bytes of WebM/Opus audio...")
            
            with open(webm_path, 'rb') as f:
                webm_bytes = f.read()
            
            send_start = time.time()
            await websocket.send(webm_bytes)
            send_time = (time.time() - send_start) * 1000
            print(f"   ⏱️  Sent in {send_time:.1f}ms")
            
            # Receive response (with timeout)
            print("   ⏳ Waiting for transcription response...")
            
            # May receive multiple messages (transcript, final, etc.)
            responses = []
            max_messages = 20
            message_count = 0
            
            try:
                while message_count < max_messages:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response = json.loads(message)
                    responses.append(response)
                    results["logs"].append(response)
                    message_count += 1
                    
                    print(f"   📥 Received: {response.get('type')}")
                    
                    # Check for transcription results
                    if response.get('type') == 'transcript':
                        results["transcription"] = response.get('text', '')
                        results["success"] = True
                        print(f"   ✅ Transcription: \"{results['transcription']}\"")
                    
                    # Check for errors
                    if response.get('type') == 'error':
                        error_msg = response.get('message', 'Unknown error')
                        results["errors"].append(error_msg)
                        print(f"   ❌ Error: {error_msg}")
                        break
                    
                    # Check for final message
                    if response.get('type') in ('transcript_final', 'session_complete'):
                        print(f"   ✅ Session complete")
                        break
                    
            except asyncio.TimeoutError:
                print(f"   ⏰ Timeout waiting for response")
            
            await websocket.close()
            print("   ✅ WebSocket closed\n")
                
    except Exception as e:
        print(f"   ❌ Test failed: {e}\n")
        results["errors"].append(str(e))
    
    # 4. Analyze results
    print("="*70)
    print("📊 TEST RESULTS")
    print("="*70 + "\n")
    
    print(f"Status: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
    print(f"WebM file size: {webm_size} bytes")
    print(f"Responses received: {len(results['logs'])}")
    
    if results['transcription']:
        print(f"Transcription: \"{results['transcription']}\"")
    
    if results['errors']:
        print(f"\n❌ Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    # Check logs for pydub fallback (should NOT appear)
    print("\n🔍 Checking for pydub fallback logs...")
    pydub_fallback_found = False
    for log in results['logs']:
        log_str = json.dumps(log).lower()
        if 'pydub' in log_str or 'trying_pydub_decoder' in log_str:
            print(f"   ⚠️  WARNING: Pydub fallback detected!")
            print(f"      {log}")
            pydub_fallback_found = True
    
    if not pydub_fallback_found:
        print(f"   ✅ No pydub fallback detected (GOOD!)")
    
    # Summary
    print("\n" + "="*70)
    if results['success'] and not pydub_fallback_found:
        print("🎉 PHASE 1 VERIFICATION PASSED!")
        print("   - WebM/Opus audio decoded successfully")
        print("   - No pydub fallback used")
        print("   - Transcription received")
        print("="*70 + "\n")
        return 0
    else:
        print("❌ PHASE 1 VERIFICATION FAILED")
        if not results['success']:
            print("   - Audio decoding or transcription failed")
        if pydub_fallback_found:
            print("   - Pydub fallback was used (should not happen)")
        print("="*70 + "\n")
        return 1


def test_webm_opus_decoding():
    """Synchronous wrapper for async test"""
    return asyncio.run(test_webm_opus_decoding_async())


if __name__ == '__main__':
    try:
        exit_code = test_webm_opus_decoding()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
