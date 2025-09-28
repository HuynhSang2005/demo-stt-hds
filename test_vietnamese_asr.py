#!/usr/bin/env python3
"""
Comprehensive ASR Testing Script cho Wav2Vec2 Vietnamese
Test kỹ lưỡng speech-to-text tiếng Việt với audio samples có sẵn
"""

import torch
import torchaudio
import numpy as np
import time
import json
from pathlib import Path
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from typing import List, Dict, Tuple, Optional

class VietnameseASRTester:
    """Class test comprehensive cho ASR tiếng Việt"""
    
    def __init__(self, model_path: str = "./wav2vec2-base-vietnamese-250h"):
        self.model_path = model_path
        self.processor = None
        self.model = None
        self.test_results = []
        
    def load_model(self) -> bool:
        """Load Wav2Vec2 model và processor offline"""
        try:
            print("🔄 Loading Wav2Vec2 Vietnamese ASR model...")
            
            self.processor = Wav2Vec2Processor.from_pretrained(
                self.model_path, 
                local_files_only=True
            )
            
            self.model = Wav2Vec2ForCTC.from_pretrained(
                self.model_path,
                local_files_only=True
            )
            
            print("✅ Model loaded successfully!")
            print(f"   - Vocab size: {self.processor.tokenizer.vocab_size}")
            print(f"   - Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def preprocess_audio(self, audio_path: str) -> Tuple[torch.Tensor, int]:
        """
        Load và preprocess audio
        - Load file audio
        - Resample về 16kHz nếu cần
        - Convert sang tensor phù hợp
        """
        try:
            # Load audio
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Đảm bảo mono channel
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample về 16kHz nếu cần
            if sample_rate != 16000:
                print(f"⚠️  Resampling {sample_rate}Hz → 16kHz")
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000
            
            # Flatten tensor
            waveform = waveform.squeeze()
            
            return waveform, sample_rate
            
        except Exception as e:
            print(f"❌ Error processing audio {audio_path}: {e}")
            return None, None
    
    def transcribe_audio(self, waveform: torch.Tensor, sample_rate: int) -> Dict:
        """
        Transcribe audio thành text với timing info
        """
        start_time = time.time()
        
        try:
            # Normalize audio
            if torch.max(torch.abs(waveform)) > 1.0:
                waveform = waveform / torch.max(torch.abs(waveform))
            
            # Process với Wav2Vec2
            inputs = self.processor(
                waveform.numpy(), 
                sampling_rate=sample_rate, 
                return_tensors="pt", 
                padding=True
            )
            
            # Inference
            with torch.no_grad():
                logits = self.model(inputs.input_values).logits
            
            # Decode predictions
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]
            
            # Tính toán confidence score (trung bình của max probabilities)
            probabilities = torch.softmax(logits, dim=-1)
            max_probs = torch.max(probabilities, dim=-1)[0]
            confidence_score = torch.mean(max_probs).item()
            
            processing_time = time.time() - start_time
            audio_duration = len(waveform) / sample_rate
            
            return {
                "transcription": transcription,
                "confidence_score": confidence_score,
                "processing_time": processing_time,
                "audio_duration": audio_duration,
                "real_time_factor": processing_time / audio_duration,
                "success": True
            }
            
        except Exception as e:
            return {
                "transcription": "",
                "confidence_score": 0.0,
                "processing_time": time.time() - start_time,
                "audio_duration": 0.0,
                "real_time_factor": 0.0,
                "success": False,
                "error": str(e)
            }
    
    def test_sample_audios(self) -> List[Dict]:
        """Test với các file audio mẫu có sẵn"""
        
        print("\n🎤 TESTING SAMPLE AUDIOS")
        print("=" * 60)
        
        audio_test_path = Path(self.model_path) / "audio-test"
        audio_files = list(audio_test_path.glob("*.wav"))
        
        if not audio_files:
            print("❌ Không tìm thấy file audio test!")
            return []
        
        results = []
        
        for audio_file in audio_files:
            print(f"\n🔊 Testing: {audio_file.name}")
            print("-" * 40)
            
            # Load and preprocess
            waveform, sample_rate = self.preprocess_audio(str(audio_file))
            
            if waveform is None:
                continue
                
            # Audio info
            duration = len(waveform) / sample_rate
            print(f"📊 Duration: {duration:.2f}s, Sample rate: {sample_rate}Hz")
            
            # Transcribe
            result = self.transcribe_audio(waveform, sample_rate)
            result["audio_file"] = audio_file.name
            result["audio_duration"] = duration
            
            # Display results
            if result["success"]:
                print(f"📝 Transcription: \"{result['transcription']}\"")
                print(f"🎯 Confidence: {result['confidence_score']:.3f}")
                print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
                print(f"🚀 Real-time factor: {result['real_time_factor']:.2f}x")
                
                if result['real_time_factor'] < 1.0:
                    print("✅ Faster than real-time!")
                else:
                    print("⚠️  Slower than real-time")
            else:
                print(f"❌ Transcription failed: {result.get('error', 'Unknown error')}")
            
            results.append(result)
        
        return results
    
    def test_audio_quality_scenarios(self) -> List[Dict]:
        """Test với các scenario chất lượng audio khác nhau"""
        
        print("\n🔧 TESTING AUDIO QUALITY SCENARIOS") 
        print("=" * 60)
        
        # Sử dụng file audio đầu tiên làm base
        audio_test_path = Path(self.model_path) / "audio-test"
        base_audio = list(audio_test_path.glob("*.wav"))[0]
        
        waveform, sample_rate = self.preprocess_audio(str(base_audio))
        if waveform is None:
            return []
        
        scenarios = []
        
        # 1. Original audio
        print("\n📊 1. Original Audio")
        result = self.transcribe_audio(waveform, sample_rate)
        result["scenario"] = "original"
        scenarios.append(result)
        print(f"   Transcription: \"{result['transcription']}\"")
        
        # 2. Lower volume (simulate quiet speech)
        print("\n🔉 2. Lower Volume (0.3x)")
        quiet_waveform = waveform * 0.3
        result = self.transcribe_audio(quiet_waveform, sample_rate)
        result["scenario"] = "low_volume"
        scenarios.append(result)
        print(f"   Transcription: \"{result['transcription']}\"")
        
        # 3. Add noise (simulate noisy environment) 
        print("\n🎧 3. Added Noise")
        noise = torch.randn_like(waveform) * 0.05
        noisy_waveform = waveform + noise
        result = self.transcribe_audio(noisy_waveform, sample_rate)
        result["scenario"] = "noisy"
        scenarios.append(result)
        print(f"   Transcription: \"{result['transcription']}\"")
        
        # 4. Speed up (simulate faster speech)
        print("\n⏩ 4. Speed Up (1.2x faster)")
        # Resample to simulate speed change
        speed_factor = 1.2
        new_length = int(len(waveform) / speed_factor)
        fast_waveform = torch.nn.functional.interpolate(
            waveform.unsqueeze(0).unsqueeze(0), 
            size=new_length, 
            mode='linear'
        ).squeeze()
        result = self.transcribe_audio(fast_waveform, sample_rate)
        result["scenario"] = "fast_speech"
        scenarios.append(result)
        print(f"   Transcription: \"{result['transcription']}\"")
        
        # 5. Truncate (simulate short audio)
        print("\n✂️  5. Truncated (first 2 seconds)")
        truncated_length = min(2 * sample_rate, len(waveform))
        truncated_waveform = waveform[:truncated_length]
        result = self.transcribe_audio(truncated_waveform, sample_rate)
        result["scenario"] = "truncated"
        scenarios.append(result)
        print(f"   Transcription: \"{result['transcription']}\"")
        
        return scenarios
    
    def run_comprehensive_test(self) -> Dict:
        """Chạy toàn bộ test suite và tạo report"""
        
        print("🚀 VIETNAMESE ASR COMPREHENSIVE TEST")
        print("=" * 60)
        
        if not self.load_model():
            return {"success": False, "error": "Failed to load model"}
        
        # Test 1: Sample audios
        sample_results = self.test_sample_audios()
        
        # Test 2: Quality scenarios
        scenario_results = self.test_audio_quality_scenarios()
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        successful_samples = len([r for r in sample_results if r["success"]])
        total_samples = len(sample_results)
        
        print(f"🎤 Sample Audio Tests: {successful_samples}/{total_samples} successful")
        
        if sample_results:
            avg_confidence = np.mean([r["confidence_score"] for r in sample_results if r["success"]])
            avg_rt_factor = np.mean([r["real_time_factor"] for r in sample_results if r["success"]])
            
            print(f"📊 Average confidence: {avg_confidence:.3f}")
            print(f"⚡ Average real-time factor: {avg_rt_factor:.2f}x")
            
            if avg_rt_factor < 1.0:
                print("✅ Model runs faster than real-time!")
            
        print(f"🔧 Quality scenario tests: {len(scenario_results)} scenarios tested")
        
        # Overall assessment
        overall_success = successful_samples == total_samples and len(scenario_results) > 0
        
        if overall_success:
            print("\n🎉 OVERALL: Vietnamese ASR model working excellent!")
        else:
            print("\n⚠️  OVERALL: Some issues detected, check individual results")
        
        # Save results
        final_results = {
            "success": overall_success,
            "sample_audio_results": sample_results,
            "quality_scenario_results": scenario_results,
            "summary": {
                "successful_samples": successful_samples,
                "total_samples": total_samples,
                "avg_confidence": avg_confidence if sample_results else 0,
                "avg_real_time_factor": avg_rt_factor if sample_results else 0
            }
        }
        
        # Save to JSON
        with open("asr_test_results.json", "w", encoding="utf-8") as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 Results saved to asr_test_results.json")
        
        return final_results

if __name__ == "__main__":
    tester = VietnameseASRTester()
    results = tester.run_comprehensive_test()
    
    print("\n🎯 READY FOR PROMPT 2.1: LocalWav2Vec2ASR class implementation!")