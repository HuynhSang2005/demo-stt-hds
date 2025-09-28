#!/usr/bin/env python3
"""
Unit Tests cho LocalWav2Vec2ASR - Prompt 2.1
Comprehensive testing với mock và real model
"""

import unittest
import torch
import torchaudio
import numpy as np
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path để import LocalWav2Vec2ASR
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from local_wav2vec2_asr import (
    LocalWav2Vec2ASR, 
    ModelLoadError, 
    AudioProcessingError,
    TranscriptionResult,
    create_vietnamese_asr
)

class TestLocalWav2Vec2ASR(unittest.TestCase):
    """Test cases cho LocalWav2Vec2ASR class"""
    
    def setUp(self):
        """Setup cho mỗi test"""
        self.model_path = "./wav2vec2-base-vietnamese-250h"
        self.sample_rate = 16000
        
        # Tạo sample audio data
        self.duration = 2.0  # 2 seconds
        self.num_samples = int(self.sample_rate * self.duration)
        self.sample_waveform = torch.randn(self.num_samples) * 0.1  # Low amplitude
    
    def test_init_without_real_model(self):
        """Test initialization khi không có model thật"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            with self.assertRaises(ModelLoadError):
                LocalWav2Vec2ASR("./non_existent_model")
    
    @patch('local_wav2vec2_asr.Wav2Vec2Processor.from_pretrained')
    @patch('local_wav2vec2_asr.Wav2Vec2ForCTC.from_pretrained') 
    @patch('pathlib.Path.exists')
    def test_init_with_mocked_model(self, mock_exists, mock_model, mock_processor):
        """Test initialization với mocked model"""
        # Setup mocks
        mock_exists.return_value = True
        mock_processor_instance = Mock()
        mock_model_instance = Mock()
        mock_model_instance.parameters.return_value = [torch.randn(100), torch.randn(50)]
        mock_model_instance.eval.return_value = None
        
        mock_processor.return_value = mock_processor_instance
        mock_model.return_value = mock_model_instance
        
        # Test initialization
        asr = LocalWav2Vec2ASR("./test_model")
        
        self.assertTrue(asr.is_loaded)
        self.assertEqual(asr.target_sample_rate, 16000)
        self.assertIsNotNone(asr.processor)
        self.assertIsNotNone(asr.model)
        
        # Verify mock calls
        mock_processor.assert_called_once()
        mock_model.assert_called_once()
        mock_model_instance.eval.assert_called_once()
    
    def test_validate_input(self):
        """Test input validation"""
        # Create mock ASR instance
        asr = LocalWav2Vec2ASR.__new__(LocalWav2Vec2ASR)
        asr.is_loaded = False
        
        # Test valid input - không raise exception
        try:
            asr._validate_input(self.sample_waveform, self.sample_rate)
        except Exception:
            self.fail("Valid input should not raise exception")
        
        # Test invalid waveform type
        with self.assertRaises(AudioProcessingError):
            asr._validate_input("not_tensor", self.sample_rate)
        
        # Test empty waveform
        with self.assertRaises(AudioProcessingError):
            asr._validate_input(torch.tensor([]), self.sample_rate)
        
        # Test invalid sample rate
        with self.assertRaises(AudioProcessingError):
            asr._validate_input(self.sample_waveform, 0)
        
        # Test audio quá ngắn
        short_audio = torch.randn(100)  # < 0.1s at 16kHz
        with self.assertRaises(AudioProcessingError):
            asr._validate_input(short_audio, self.sample_rate)
    
    def test_preprocess_audio(self):
        """Test audio preprocessing"""
        asr = LocalWav2Vec2ASR.__new__(LocalWav2Vec2ASR)
        asr.target_sample_rate = 16000
        
        # Test mono audio (no change needed)
        processed = asr._preprocess_audio(self.sample_waveform, self.sample_rate)
        self.assertEqual(processed.shape, self.sample_waveform.shape)
        
        # Test stereo audio -> mono conversion
        stereo_audio = torch.stack([self.sample_waveform, self.sample_waveform])
        processed = asr._preprocess_audio(stereo_audio, self.sample_rate)
        self.assertEqual(processed.dim(), 1)  # Should be 1D now
        
        # Test resampling từ 8kHz -> 16kHz
        low_sr_audio = torch.randn(8000)  # 1 second at 8kHz
        processed = asr._preprocess_audio(low_sr_audio, 8000)
        expected_length = int(len(low_sr_audio) * 16000 / 8000)
        self.assertAlmostEqual(len(processed), expected_length, delta=10)
        
        # Test normalization của audio với amplitude > 1
        loud_audio = torch.randn(self.num_samples) * 5.0  # High amplitude
        processed = asr._preprocess_audio(loud_audio, self.sample_rate)
        self.assertLessEqual(torch.max(torch.abs(processed)).item(), 1.0)
    
    def test_confidence_score_computation(self):
        """Test confidence score calculation"""
        asr = LocalWav2Vec2ASR.__new__(LocalWav2Vec2ASR)
        
        # Create mock logits (batch_size=1, seq_len=100, vocab_size=110) 
        logits = torch.randn(100, 110)
        
        confidence = asr._compute_confidence_score(logits)
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        # Test với logits có high confidence
        high_conf_logits = torch.zeros(100, 110)
        high_conf_logits[:, 0] = 10.0  # High probability for class 0
        
        high_confidence = asr._compute_confidence_score(high_conf_logits)
        self.assertGreater(high_confidence, 0.9)
    
    @patch('local_wav2vec2_asr.Wav2Vec2Processor.from_pretrained')
    @patch('local_wav2vec2_asr.Wav2Vec2ForCTC.from_pretrained')
    @patch('pathlib.Path.exists')
    def test_transcribe_with_mocked_model(self, mock_exists, mock_model_class, mock_processor_class):
        """Test transcription với mocked model và processor"""
        # Setup mocks
        mock_exists.return_value = True
        
        # Mock processor
        mock_processor = Mock()
        mock_processor.__class__.__name__ = "Wav2Vec2Processor"
        mock_processor.return_value = Mock(input_values=torch.randn(1, 32000))
        mock_processor.batch_decode.return_value = ["xin chào"]
        mock_processor_class.return_value = mock_processor
        
        # Mock model
        mock_model = Mock()
        mock_model.__class__.__name__ = "Wav2Vec2ForCTC"
        mock_model.parameters.return_value = [torch.randn(100)]
        mock_model.eval.return_value = None
        
        # Mock model inference
        mock_logits = Mock()
        mock_logits.logits = torch.randn(1, 100, 110)
        mock_model.return_value = mock_logits
        mock_model_class.return_value = mock_model
        
        # Create ASR instance
        asr = LocalWav2Vec2ASR("./test_model")
        
        # Test transcription
        result = asr.transcribe(self.sample_waveform, self.sample_rate)
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, "xin chào")
        
        # Verify processor và model được gọi
        mock_processor.assert_called()
        mock_processor.batch_decode.assert_called_once()
        mock_model.assert_called()
    
    @patch('local_wav2vec2_asr.Wav2Vec2Processor.from_pretrained')
    @patch('local_wav2vec2_asr.Wav2Vec2ForCTC.from_pretrained')
    @patch('pathlib.Path.exists')
    def test_transcribe_with_metadata(self, mock_exists, mock_model_class, mock_processor_class):
        """Test transcribe_with_metadata method"""
        # Setup mocks
        mock_exists.return_value = True
        
        mock_processor = Mock()
        mock_processor.__class__.__name__ = "Wav2Vec2Processor"
        mock_processor.return_value = Mock(input_values=torch.randn(1, 32000))
        mock_processor.batch_decode.return_value = ["hello world"]
        mock_processor_class.return_value = mock_processor
        
        mock_model = Mock()
        mock_model.__class__.__name__ = "Wav2Vec2ForCTC"
        mock_model.parameters.return_value = [torch.randn(100)]
        mock_model.eval.return_value = None
        
        mock_logits = Mock()
        mock_logits.logits = torch.randn(1, 100, 110)
        mock_model.return_value = mock_logits
        mock_model_class.return_value = mock_model
        
        # Create ASR instance
        asr = LocalWav2Vec2ASR("./test_model")
        
        # Test transcribe with metadata
        result = asr.transcribe_with_metadata(self.sample_waveform, self.sample_rate)
        
        self.assertIsInstance(result, TranscriptionResult)
        self.assertTrue(result.success)
        self.assertEqual(result.text, "hello world")
        self.assertGreater(result.confidence_score, 0.0)
        self.assertGreater(result.processing_time, 0.0)
        self.assertAlmostEqual(result.audio_duration, self.duration, places=1)
        self.assertEqual(result.sample_rate, 16000)
    
    def test_transcribe_with_unloaded_model(self):
        """Test transcribe khi model chưa được load"""
        asr = LocalWav2Vec2ASR.__new__(LocalWav2Vec2ASR)
        asr.is_loaded = False
        asr.processor = None
        asr.model = None
        
        # Test transcribe should raise error
        with self.assertRaises(ModelLoadError):
            asr.transcribe(self.sample_waveform, self.sample_rate)
        
        # Test transcribe_with_metadata should return failed result
        result = asr.transcribe_with_metadata(self.sample_waveform, self.sample_rate)
        self.assertFalse(result.success)
        self.assertEqual(result.text, "")
        self.assertIsNotNone(result.error_message)
    
    @patch('local_wav2vec2_asr.Wav2Vec2Processor.from_pretrained')
    @patch('local_wav2vec2_asr.Wav2Vec2ForCTC.from_pretrained')
    @patch('pathlib.Path.exists')
    def test_get_model_info(self, mock_exists, mock_model_class, mock_processor_class):
        """Test get_model_info method"""
        # Setup mocks
        mock_exists.return_value = True
        
        mock_processor = Mock()
        mock_processor.__class__.__name__ = "Wav2Vec2Processor"
        mock_processor_class.return_value = mock_processor
        
        mock_model = Mock()
        mock_model.__class__.__name__ = "Wav2Vec2ForCTC"
        mock_model.parameters.return_value = [torch.randn(100), torch.randn(50)]
        mock_model.eval.return_value = None
        mock_model_class.return_value = mock_model
        
        # Create ASR instance
        asr = LocalWav2Vec2ASR("./test_model")
        
        # Test get_model_info
        info = asr.get_model_info()
        
        self.assertIsInstance(info, dict)
        self.assertTrue(info["loaded"])
        self.assertEqual(info["model_class"], "Wav2Vec2ForCTC")
        self.assertEqual(info["processor_class"], "Wav2Vec2Processor")
        self.assertEqual(info["target_sample_rate"], 16000)
        self.assertIsInstance(info["model_parameters"], int)
    
    def test_factory_function(self):
        """Test create_vietnamese_asr factory function"""
        with patch('local_wav2vec2_asr.LocalWav2Vec2ASR') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            result = create_vietnamese_asr("./test_path")
            
            mock_class.assert_called_once_with("./test_path")
            self.assertEqual(result, mock_instance)

class TestAudioProcessingEdgeCases(unittest.TestCase):
    """Test edge cases cho audio processing"""
    
    def setUp(self):
        self.asr = LocalWav2Vec2ASR.__new__(LocalWav2Vec2ASR)
        self.asr.target_sample_rate = 16000
    
    def test_various_audio_formats(self):
        """Test với different audio formats và shapes"""
        # Test 1D audio
        audio_1d = torch.randn(16000)
        processed = self.asr._preprocess_audio(audio_1d, 16000)
        self.assertEqual(processed.dim(), 1)
        
        # Test 2D single channel audio [1, samples]
        audio_2d_single = torch.randn(1, 16000)
        processed = self.asr._preprocess_audio(audio_2d_single, 16000)
        self.assertEqual(processed.dim(), 1)
        
        # Test 2D multi-channel audio [channels, samples]
        audio_2d_multi = torch.randn(2, 16000)
        processed = self.asr._preprocess_audio(audio_2d_multi, 16000)
        self.assertEqual(processed.dim(), 1)
    
    def test_extreme_sample_rates(self):
        """Test với extreme sample rates"""
        audio = torch.randn(8000)
        
        # Very low sample rate
        processed = self.asr._preprocess_audio(audio, 1000)
        expected_len = int(len(audio) * 16000 / 1000)
        self.assertAlmostEqual(len(processed), expected_len, delta=100)
        
        # Very high sample rate
        high_sr_audio = torch.randn(96000)  # 1 second at 96kHz
        processed = self.asr._preprocess_audio(high_sr_audio, 96000)
        expected_len = int(len(high_sr_audio) * 16000 / 96000)
        self.assertAlmostEqual(len(processed), expected_len, delta=100)
    
    def test_silent_audio(self):
        """Test với silent audio"""
        silent_audio = torch.zeros(16000)
        processed = self.asr._preprocess_audio(silent_audio, 16000)
        
        # Should not crash, chỉ normalize
        self.assertEqual(len(processed), len(silent_audio))
    
    def test_noisy_audio(self):
        """Test với very noisy audio"""
        noisy_audio = torch.randn(16000) * 100.0  # Very loud noise
        processed = self.asr._preprocess_audio(noisy_audio, 16000)
        
        # Should be normalized to [-1, 1]
        self.assertLessEqual(torch.max(torch.abs(processed)).item(), 1.0)

if __name__ == "__main__":
    # Chạy all tests
    print("🧪 RUNNING LocalWav2Vec2ASR Unit Tests - Prompt 2.1")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestLocalWav2Vec2ASR))
    suite.addTest(loader.loadTestsFromTestCase(TestAudioProcessingEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print results
    print(f"\n📊 TEST RESULTS:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, failure in result.failures:
            print(f"   {test}: {failure}")
    
    if result.errors:
        print(f"\n💥 ERRORS:")
        for test, error in result.errors:
            print(f"   {test}: {error}")
    
    if result.wasSuccessful():
        print(f"\n✅ ALL TESTS PASSED! LocalWav2Vec2ASR ready for production.")
    else:
        print(f"\n❌ Some tests failed. Fix issues before proceeding.")
    
    print(f"\n🚀 Ready for Prompt 2.2: LocalPhoBERTClassifier implementation!")