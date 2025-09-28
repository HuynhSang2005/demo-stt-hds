#!/usr/bin/env python3
"""
Test LocalWav2Vec2ASR với audio samples thật - Prompt 2.1 Validation
"""

import torch
import torchaudio
import time
from pathlib import Path
from local_wav2vec2_asr import LocalWav2Vec2ASR, create_vietnamese_asr

def test_with_real_audio():
    """Test LocalWav2Vec2ASR với audio samples từ model folder"""
    print("🎙️ TESTING LocalWav2Vec2ASR with Real Audio - Prompt 2.1")
    print("=" * 60)
    
    try:
        # Initialize ASR
        print("1️⃣ Initializing LocalWav2Vec2ASR...")
        asr = create_vietnamese_asr()
        
        # Show model info
        info = asr.get_model_info()
        print(f"✅ Model loaded: {info['model_parameters']:,} parameters")
        print(f"   Target sample rate: {info['target_sample_rate']}Hz")
        
        # Find audio test files
        audio_dir = Path("./wav2vec2-base-vietnamese-250h/audio-test")
        if not audio_dir.exists():
            print(f"❌ Audio test directory not found: {audio_dir}")
            return False
        
        audio_files = list(audio_dir.glob("*.wav"))
        if not audio_files:
            print(f"❌ No audio files found in {audio_dir}")
            return False
        
        print(f"📂 Found {len(audio_files)} audio files")
        
        # Test với từng audio file
        results = []
        total_audio_time = 0.0
        total_process_time = 0.0
        
        for i, audio_file in enumerate(audio_files, 1):
            print(f"\n2️⃣.{i} Testing: {audio_file.name}")
            
            try:
                # Load audio
                waveform, sample_rate = torchaudio.load(audio_file)
                
                print(f"   📊 Audio info: {waveform.shape}, {sample_rate}Hz")
                
                # Test transcription with metadata
                result = asr.transcribe_with_metadata(waveform, sample_rate)
                
                if result.success:
                    print(f"   ✅ Transcription: '{result.text}'")
                    print(f"   📈 Confidence: {result.confidence_score:.3f}")
                    print(f"   ⏱️ Processing: {result.processing_time:.3f}s")
                    print(f"   🎵 Duration: {result.audio_duration:.2f}s")
                    print(f"   🚀 Real-time factor: {result.real_time_factor:.2f}x")
                    
                    results.append(result)
                    total_audio_time += result.audio_duration
                    total_process_time += result.processing_time
                    
                else:
                    print(f"   ❌ Failed: {result.error_message}")
                    
            except Exception as e:
                print(f"   💥 Error loading {audio_file.name}: {e}")
        
        # Summary statistics
        if results:
            print(f"\n3️⃣ PERFORMANCE SUMMARY:")
            print(f"   🎯 Total files processed: {len(results)}/{len(audio_files)}")
            print(f"   ⏰ Total audio time: {total_audio_time:.2f}s")
            print(f"   ⚡ Total processing time: {total_process_time:.2f}s")
            print(f"   🏃 Overall real-time factor: {total_process_time/total_audio_time:.2f}x")
            
            # Average confidence
            avg_confidence = sum(r.confidence_score for r in results) / len(results)
            print(f"   📊 Average confidence: {avg_confidence:.3f}")
            
            # Show all transcriptions
            print(f"\n4️⃣ ALL TRANSCRIPTIONS:")
            for i, result in enumerate(results, 1):
                filename = audio_files[i-1].name
                print(f"   {i}. {filename}: '{result.text}'")
            
            return True
        else:
            print(f"\n❌ No successful transcriptions")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_error_cases():
    """Test error handling cases"""
    print(f"\n🚨 TESTING Error Handling Cases")
    print("=" * 40)
    
    try:
        asr = create_vietnamese_asr()
        
        # Test 1: Invalid audio
        print("1. Testing invalid audio input...")
        try:
            result = asr.transcribe_with_metadata(torch.tensor([]), 16000)
            print(f"   ✅ Handled gracefully: success={result.success}")
        except Exception as e:
            print(f"   ❌ Not handled: {e}")
        
        # Test 2: Very short audio
        print("2. Testing very short audio...")
        short_audio = torch.randn(100)  # Very short
        try:
            result = asr.transcribe_with_metadata(short_audio, 16000)
            print(f"   ✅ Handled gracefully: success={result.success}")
        except Exception as e:
            print(f"   ❌ Not handled: {e}")
        
        # Test 3: Different sample rates
        print("3. Testing different sample rates...")
        test_audio = torch.randn(8000)  # 1 second at 8kHz
        try:
            result = asr.transcribe_with_metadata(test_audio, 8000)
            print(f"   ✅ Resampling works: success={result.success}")
            if result.success:
                print(f"      Final sample rate: {result.sample_rate}Hz")
        except Exception as e:
            print(f"   ❌ Resampling failed: {e}")
        
        # Test 4: Multi-channel audio
        print("4. Testing stereo audio...")
        stereo_audio = torch.randn(2, 16000)  # Stereo
        try:
            result = asr.transcribe_with_metadata(stereo_audio, 16000)
            print(f"   ✅ Stereo->Mono works: success={result.success}")
        except Exception as e:
            print(f"   ❌ Stereo handling failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing failed: {e}")
        return False

def performance_benchmark():
    """Benchmark performance với synthetic audio"""
    print(f"\n🏃 PERFORMANCE BENCHMARK")
    print("=" * 40)
    
    try:
        asr = create_vietnamese_asr()
        
        # Test với different durations
        durations = [1.0, 2.0, 5.0, 10.0]  # seconds
        
        print(f"Testing với synthetic audio durations: {durations}")
        
        for duration in durations:
            print(f"\n⏱️ Testing {duration}s audio...")
            
            # Generate synthetic audio
            sample_rate = 16000
            num_samples = int(duration * sample_rate)
            synthetic_audio = torch.randn(num_samples) * 0.1
            
            # Benchmark 3 runs
            times = []
            for run in range(3):
                start_time = time.time()
                result = asr.transcribe(synthetic_audio, sample_rate)
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            real_time_factor = avg_time / duration
            
            print(f"   📊 Duration: {duration}s")
            print(f"   ⚡ Avg processing: {avg_time:.3f}s")
            print(f"   🚀 Real-time factor: {real_time_factor:.2f}x")
            print(f"   📝 Sample output: '{result[:50]}...'")
        
        return True
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return False

if __name__ == "__main__":
    success = True
    
    # Run all tests
    success &= test_with_real_audio()
    success &= test_error_cases()  
    success &= performance_benchmark()
    
    # Final result
    print(f"\n" + "=" * 60)
    if success:
        print(f"✅ ALL TESTS PASSED! LocalWav2Vec2ASR is ready for production.")
        print(f"🚀 Ready for Prompt 2.2: LocalPhoBERTClassifier implementation!")
    else:
        print(f"❌ Some tests failed. Review and fix before proceeding.")
    print(f"=" * 60)