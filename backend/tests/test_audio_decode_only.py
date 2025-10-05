"""
Simple test: Generate WebM/Opus audio and test direct decoding
WITHOUT WebSocket - just test the audio_processor decode function
"""

import sys
import os
from pathlib import Path
import time
import numpy as np

# Add backend to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    import soundfile as sf
    import subprocess
    import torchaudio
    import torch
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def generate_test_audio(duration_seconds: float = 2.0, sample_rate: int = 16000):
    """Generate synthetic audio"""
    print(f"📊 Generating {duration_seconds}s test audio at {sample_rate}Hz...")
    
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    audio = (
        0.3 * np.sin(2 * np.pi * 440 * t) +
        0.2 * np.sin(2 * np.pi * 880 * t) +
        0.1 * np.random.randn(len(t))
    )
    audio = audio / np.max(np.abs(audio))
    
    return audio.astype(np.float32), sample_rate


def convert_to_webm_opus(audio_data: np.ndarray, sample_rate: int, output_path: Path):
    """Convert to WebM/Opus using ffmpeg"""
    print(f"🔄 Converting to WebM/Opus...")
    
    temp_wav = output_path.with_suffix('.temp.wav')
    sf.write(temp_wav, audio_data, sample_rate)
    
    try:
        cmd = [
            'ffmpeg', '-y', '-i', str(temp_wav),
            '-c:a', 'libopus',
            '-b:a', '24k',
            '-vbr', 'on',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        
        if result.returncode != 0:
            raise RuntimeError("FFmpeg conversion failed")
        
        print(f"✅ WebM created: {output_path.stat().st_size} bytes")
        
    finally:
        if temp_wav.exists():
            temp_wav.unlink()
    
    return output_path


def test_torchaudio_webm_decode():
    """Test torchaudio can decode WebM/Opus with ffmpeg backend"""
    print("\n" + "="*70)
    print("🧪 PHASE 1 TEST: TORCHAUDIO WEBM/OPUS DECODING")
    print("="*70 + "\n")
    
    # 1. Set torchaudio backend
    print("Step 1: Configure torchaudio backend")
    try:
        torchaudio.set_audio_backend('ffmpeg')
        print("   ✅ Torchaudio backend set to ffmpeg\n")
    except Exception as e:
        print(f"   ❌ Failed to set backend: {e}\n")
        return 1
    
    # 2. Generate audio
    print("Step 2: Generate test audio")
    audio_data, sample_rate = generate_test_audio(duration_seconds=2.0, sample_rate=16000)
    print(f"   ✅ Generated {len(audio_data)} samples\n")
    
    # 3. Convert to WebM
    print("Step 3: Convert to WebM/Opus")
    test_dir = Path(__file__).parent / "test_audio"
    test_dir.mkdir(exist_ok=True)
    webm_path = test_dir / "test_decode.webm"
    
    convert_to_webm_opus(audio_data, sample_rate, webm_path)
    webm_size = webm_path.stat().st_size
    print(f"   ✅ WebM size: {webm_size} bytes\n")
    
    # 4. Test decoding with torchaudio
    print("Step 4: Decode WebM with torchaudio+ffmpeg")
    
    try:
        # Read WebM bytes
        with open(webm_path, 'rb') as f:
            webm_bytes = f.read()
        
        # Decode using torchaudio.load() (simulating audio_processor behavior)
        import io
        audio_buffer = io.BytesIO(webm_bytes)
        
        decode_start = time.time()
        # Specify format explicitly to use ffmpeg backend for WebM
        waveform, decoded_sr = torchaudio.load(audio_buffer, format="webm")
        decode_time = (time.time() - decode_start) * 1000
        
        print(f"   ✅ DECODE SUCCESSFUL!")
        print(f"   ⏱️  Decode time: {decode_time:.2f}ms")
        print(f"   📊 Waveform shape: {waveform.shape}")
        print(f"   📊 Sample rate: {decoded_sr}Hz")
        print(f"   📊 Duration: {waveform.shape[-1] / decoded_sr:.2f}s")
        print(f"   📊 Channels: {waveform.shape[0]}\n")
        
        # Validate
        if waveform.numel() == 0:
            print("   ❌ ERROR: Waveform is empty!")
            return 1
        
        if decoded_sr <= 0:
            print(f"   ❌ ERROR: Invalid sample rate: {decoded_sr}")
            return 1
        
        # Performance check
        print("="*70)
        print("📊 PERFORMANCE ANALYSIS")
        print("="*70)
        print(f"Input size: {webm_size} bytes ({webm_size/1024:.2f} KB)")
        print(f"Decode time: {decode_time:.2f}ms")
        print(f"Audio duration: {waveform.shape[-1] / decoded_sr:.2f}s")
        print(f"Real-time factor: {decode_time / (waveform.shape[-1] / decoded_sr * 1000):.3f}")
        
        if decode_time < 50:
            print(f"\n✅ EXCELLENT: Decode time < 50ms (Phase 1 target achieved!)")
        elif decode_time < 100:
            print(f"\n✅ GOOD: Decode time < 100ms")
        else:
            print(f"\n⚠️  WARNING: Decode time > 100ms (slower than expected)")
        
        print("\n" + "="*70)
        print("🎉 PHASE 1 VERIFICATION PASSED!")
        print("="*70)
        print("Summary:")
        print("  ✅ Torchaudio+ffmpeg backend works")
        print("  ✅ WebM/Opus audio decoded successfully")
        print("  ✅ No pydub fallback needed")
        print("  ✅ Single-step decode pipeline")
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"   ❌ DECODE FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        
        print("\n" + "="*70)
        print("❌ PHASE 1 VERIFICATION FAILED")
        print("="*70)
        print("Torchaudio could not decode WebM/Opus audio.")
        print("This suggests ffmpeg backend is not working correctly.")
        print("="*70 + "\n")
        
        return 1


if __name__ == '__main__':
    try:
        exit_code = test_torchaudio_webm_decode()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
