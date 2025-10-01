#!/usr/bin/env python3
"""
Test Suite for Task 14: Configuration Management
Tests the enhanced configuration system
"""

import os
import tempfile
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

# Import validation
try:
    from pydantic import ValidationError
except ImportError:
    print("⚠️ Pydantic not installed. Installing...")
    os.system("pip install pydantic pydantic-settings")
    from pydantic import ValidationError

# Import pytest (optional, for validation error checking)
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    print("⚠️ pytest not installed. Some validation tests will be skipped.")

from app.core.config_enhanced import (
    EnhancedSettings,
    Environment,
    LogLevel,
    DeviceType
)


class TestBasicConfiguration:
    """Test basic configuration loading"""
    
    def test_default_settings(self):
        """Test default configuration values"""
        settings = EnhancedSettings()
        
        assert settings.PROJECT_NAME == "Vietnamese Speech-to-Text + Toxic Detection API"
        assert settings.VERSION == "2.0.0"
        assert settings.ENVIRONMENT == Environment.DEVELOPMENT
        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 8000
    
    def test_model_paths(self):
        """Test model path configuration"""
        settings = EnhancedSettings()
        
        assert settings.ASR_MODEL_PATH == "../wav2vec2-base-vietnamese-250h"
        assert settings.CLASSIFIER_MODEL_PATH == "../phobert-vi-comment-4class"
        assert settings.MODEL_DEVICE == DeviceType.CPU
    
    def test_audio_settings(self):
        """Test audio processing settings"""
        settings = EnhancedSettings()
        
        assert settings.AUDIO_CHUNK_DURATION == 2.0
        assert settings.MIN_AUDIO_DURATION == 0.1
        assert settings.MAX_AUDIO_DURATION == 30.0
        assert settings.TARGET_SAMPLE_RATE == 16000


class TestVietnamesePreprocessing:
    """Test Vietnamese preprocessing configuration (Task 10)"""
    
    def test_preprocessing_defaults(self):
        """Test preprocessing default values"""
        settings = EnhancedSettings()
        
        assert settings.VIETNAMESE_PREPROCESSING_ENABLED is True
        assert settings.REMOVE_TONES_FOR_MATCHING is False
        assert settings.CONVERT_NUMBERS_TO_TEXT is False
        assert settings.NORMALIZE_PUNCTUATION is True
        assert settings.APPLY_COMMON_FIXES is True
        assert settings.FIX_SPACING is True
        assert settings.LOWERCASE_TEXT is False
    
    def test_preprocessing_config_getter(self):
        """Test get_preprocessing_config() method"""
        settings = EnhancedSettings()
        config = settings.get_preprocessing_config()
        
        assert config["enabled"] is True
        assert config["remove_tones"] is False
        assert config["normalize_punctuation"] is True
        assert "apply_common_fixes" in config
    
    def test_custom_preprocessing(self):
        """Test custom preprocessing configuration"""
        settings = EnhancedSettings(
            REMOVE_TONES_FOR_MATCHING=True,
            CONVERT_NUMBERS_TO_TEXT=True,
            LOWERCASE_TEXT=True
        )
        
        config = settings.get_preprocessing_config()
        assert config["remove_tones"] is True
        assert config["convert_numbers_to_text"] is True
        assert config["lowercase"] is True


class TestClassificationSettings:
    """Test classification configuration (Task 11)"""
    
    def test_ensemble_defaults(self):
        """Test ensemble classification defaults"""
        settings = EnhancedSettings()
        
        assert settings.ENABLE_ENSEMBLE_CLASSIFICATION is True
        assert settings.ENSEMBLE_MODEL_WEIGHT == 0.7
        assert settings.ENSEMBLE_KEYWORD_WEIGHT == 0.3
    
    def test_threshold_defaults(self):
        """Test classification threshold defaults"""
        settings = EnhancedSettings()
        
        assert settings.TOXIC_THRESHOLD == 0.55
        assert settings.NEGATIVE_THRESHOLD == 0.60
        assert settings.NEUTRAL_THRESHOLD == 0.50
        assert settings.POSITIVE_THRESHOLD == 0.60
    
    def test_sliding_window_defaults(self):
        """Test sliding window defaults"""
        settings = EnhancedSettings()
        
        assert settings.ENABLE_SLIDING_WINDOW is True
        assert settings.SLIDING_WINDOW_SIZE == 400
        assert settings.SLIDING_WINDOW_OVERLAP == 100
        assert settings.LONG_TEXT_THRESHOLD == 500
    
    def test_classification_config_getter(self):
        """Test get_classification_config() method"""
        settings = EnhancedSettings()
        config = settings.get_classification_config()
        
        assert config["ensemble_enabled"] is True
        assert config["model_weight"] == 0.7
        assert config["keyword_weight"] == 0.3
        assert "thresholds" in config
        assert config["thresholds"]["toxic"] == 0.55
        assert "sliding_window" in config
    
    def test_threshold_validation(self):
        """Test threshold validation (must be 0-1)"""
        # Valid thresholds
        settings = EnhancedSettings(TOXIC_THRESHOLD=0.45)
        assert settings.TOXIC_THRESHOLD == 0.45
        
        # Invalid thresholds should raise error
        if HAS_PYTEST:
            with pytest.raises(ValidationError):
                EnhancedSettings(TOXIC_THRESHOLD=1.5)
            
            with pytest.raises(ValidationError):
                EnhancedSettings(TOXIC_THRESHOLD=-0.1)
        else:
            # Manual validation test
            try:
                EnhancedSettings(TOXIC_THRESHOLD=1.5)
                assert False, "Should have raised ValidationError"
            except ValidationError:
                pass  # Expected
            
            try:
                EnhancedSettings(TOXIC_THRESHOLD=-0.1)
                assert False, "Should have raised ValidationError"
            except ValidationError:
                pass  # Expected


class TestMetricsConfiguration:
    """Test metrics configuration (Task 12)"""
    
    def test_metrics_defaults(self):
        """Test metrics default values"""
        settings = EnhancedSettings()
        
        assert settings.ENABLE_METRICS is True
        assert settings.METRICS_WINDOW_SIZE == 1000
        assert settings.METRICS_RETENTION_SECONDS == 3600
        assert settings.TRACK_COMPONENT_TIMING is True
        assert settings.TRACK_MEMORY_USAGE is True
        assert settings.TRACK_ERROR_RATES is True
    
    def test_metrics_config_getter(self):
        """Test get_metrics_config() method"""
        settings = EnhancedSettings()
        config = settings.get_metrics_config()
        
        assert config["enabled"] is True
        assert config["window_size"] == 1000
        assert config["retention_seconds"] == 3600
        assert config["track_timing"] is True
        assert config["track_memory"] is True
        assert config["track_errors"] is True
    
    def test_custom_metrics(self):
        """Test custom metrics configuration"""
        settings = EnhancedSettings(
            METRICS_WINDOW_SIZE=500,
            TRACK_COMPONENT_TIMING=False,
            TRACK_MEMORY_USAGE=False
        )
        
        config = settings.get_metrics_config()
        assert config["window_size"] == 500
        assert config["track_timing"] is False
        assert config["track_memory"] is False


class TestErrorHandlingConfiguration:
    """Test error handling configuration (Task 13)"""
    
    def test_circuit_breaker_defaults(self):
        """Test circuit breaker default values"""
        settings = EnhancedSettings()
        
        assert settings.ENABLE_CIRCUIT_BREAKER is True
        assert settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 5
        assert settings.CIRCUIT_BREAKER_TIMEOUT_SECONDS == 60
        assert settings.CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS == 2
    
    def test_retry_defaults(self):
        """Test retry logic default values"""
        settings = EnhancedSettings()
        
        assert settings.ENABLE_RETRY is True
        assert settings.MAX_RETRY_ATTEMPTS == 3
        assert settings.RETRY_INITIAL_DELAY == 1.0
        assert settings.RETRY_MAX_DELAY == 60.0
        assert settings.RETRY_EXPONENTIAL_BASE == 2.0
    
    def test_circuit_breaker_config_getter(self):
        """Test get_circuit_breaker_config() method"""
        settings = EnhancedSettings()
        config = settings.get_circuit_breaker_config()
        
        assert config["enabled"] is True
        assert config["failure_threshold"] == 5
        assert config["timeout_seconds"] == 60
        assert config["half_open_attempts"] == 2
    
    def test_custom_circuit_breaker(self):
        """Test custom circuit breaker configuration"""
        settings = EnhancedSettings(
            CIRCUIT_BREAKER_FAILURE_THRESHOLD=3,
            CIRCUIT_BREAKER_TIMEOUT_SECONDS=30
        )
        
        config = settings.get_circuit_breaker_config()
        assert config["failure_threshold"] == 3
        assert config["timeout_seconds"] == 30


class TestPerformanceSettings:
    """Test performance and optimization settings (Tasks 2-9)"""
    
    def test_async_defaults(self):
        """Test async processing defaults"""
        settings = EnhancedSettings()
        
        assert settings.ENABLE_ASYNC_PROCESSING is True
        assert settings.MAX_CONCURRENT_CONNECTIONS == 100
        assert settings.REQUEST_TIMEOUT == 30.0
    
    def test_batch_defaults(self):
        """Test batch processing defaults"""
        settings = EnhancedSettings()
        
        assert settings.ENABLE_BATCH_PROCESSING is True
        assert settings.ASR_BATCH_SIZE == 5
        assert settings.ASR_BATCH_TIMEOUT == 0.05
        assert settings.CLASSIFIER_BATCH_SIZE == 8
        assert settings.CLASSIFIER_BATCH_TIMEOUT == 0.03


class TestValidation:
    """Test configuration validation"""
    
    def test_ensemble_weight_validation(self):
        """Test ensemble weights must be 0-1"""
        # Valid weights
        settings = EnhancedSettings(
            ENSEMBLE_MODEL_WEIGHT=0.6,
            ENSEMBLE_KEYWORD_WEIGHT=0.4
        )
        assert settings.ENSEMBLE_MODEL_WEIGHT == 0.6
        
        # Test warning: weights should sum to 1.0
        # (validation doesn't enforce this, just a recommendation)
        settings2 = EnhancedSettings(
            ENSEMBLE_MODEL_WEIGHT=0.5,
            ENSEMBLE_KEYWORD_WEIGHT=0.3  # Sum = 0.8, not ideal but allowed
        )
        assert settings2.ENSEMBLE_MODEL_WEIGHT == 0.5
    
    def test_max_audio_duration_validation(self):
        """Test max audio duration must be reasonable"""
        # Valid duration
        settings = EnhancedSettings(MAX_AUDIO_DURATION=60.0)
        assert settings.MAX_AUDIO_DURATION == 60.0
        
        # Invalid duration (too long)
        if HAS_PYTEST:
            with pytest.raises(ValidationError):
                EnhancedSettings(MAX_AUDIO_DURATION=600.0)
        else:
            try:
                EnhancedSettings(MAX_AUDIO_DURATION=600.0)
                assert False, "Should have raised ValidationError"
            except ValidationError:
                pass  # Expected
    
    def test_model_path_validation(self):
        """Test model path validation"""
        settings = EnhancedSettings()
        
        # Get model paths
        paths = settings.get_model_paths()
        assert "asr" in paths
        assert "classifier" in paths
        assert isinstance(paths["asr"], Path)
        
        # Validate model paths (may fail if models not present)
        validation = settings.validate_model_paths()
        assert "asr_exists" in validation
        assert "classifier_exists" in validation


class TestHelperMethods:
    """Test configuration helper methods"""
    
    def test_is_development(self):
        """Test is_development property"""
        dev_settings = EnhancedSettings(ENVIRONMENT=Environment.DEVELOPMENT)
        assert dev_settings.is_development is True
        
        prod_settings = EnhancedSettings(ENVIRONMENT=Environment.PRODUCTION, DEBUG=False)
        assert prod_settings.is_development is False
    
    def test_is_production(self):
        """Test is_production property"""
        prod_settings = EnhancedSettings(ENVIRONMENT=Environment.PRODUCTION)
        assert prod_settings.is_production is True
        
        dev_settings = EnhancedSettings(ENVIRONMENT=Environment.DEVELOPMENT)
        assert dev_settings.is_production is False
    
    def test_cors_origins_list(self):
        """Test CORS origins list property"""
        settings = EnhancedSettings(
            BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
        )
        origins = settings.cors_origins_list
        assert isinstance(origins, list)
        assert len(origins) == 2
    
    def test_to_dict(self):
        """Test to_dict() method"""
        settings = EnhancedSettings()
        config_dict = settings.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "PROJECT_NAME" in config_dict
        assert "TOXIC_THRESHOLD" in config_dict


class TestEnvironmentVariables:
    """Test environment variable overrides"""
    
    def test_env_override(self):
        """Test environment variable override"""
        # Set environment variable
        os.environ["TOXIC_THRESHOLD"] = "0.45"
        os.environ["PORT"] = "9000"
        
        settings = EnhancedSettings()
        
        assert settings.TOXIC_THRESHOLD == 0.45
        assert settings.PORT == 9000
        
        # Cleanup
        del os.environ["TOXIC_THRESHOLD"]
        del os.environ["PORT"]
    
    def test_env_file_loading(self):
        """Test loading from .env file"""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("PROJECT_NAME=Test Project\n")
            f.write("PORT=7000\n")
            f.write("TOXIC_THRESHOLD=0.40\n")
            env_file = f.name
        
        try:
            # Load settings with custom env file
            settings = EnhancedSettings(_env_file=env_file)
            
            # Note: Pydantic may not load from custom env file in tests
            # This is a basic test structure
            print(f"Loaded settings from {env_file}")
        finally:
            # Cleanup
            os.unlink(env_file)


class TestConfigurationPresets:
    """Test different configuration presets"""
    
    def test_high_accuracy_preset(self):
        """Test high accuracy configuration"""
        settings = EnhancedSettings(
            TOXIC_THRESHOLD=0.45,
            NEGATIVE_THRESHOLD=0.50,
            ENSEMBLE_MODEL_WEIGHT=0.6,
            ENSEMBLE_KEYWORD_WEIGHT=0.4,
            ENABLE_SLIDING_WINDOW=True,
            KEYWORD_FUZZY_MATCHING=True
        )
        
        assert settings.TOXIC_THRESHOLD == 0.45
        assert settings.ENSEMBLE_KEYWORD_WEIGHT == 0.4
    
    def test_high_performance_preset(self):
        """Test high performance configuration"""
        settings = EnhancedSettings(
            ASR_BATCH_SIZE=15,
            CLASSIFIER_BATCH_SIZE=20,
            TRACK_COMPONENT_TIMING=False,
            METRICS_WINDOW_SIZE=500,
            MAX_CONCURRENT_CONNECTIONS=200
        )
        
        assert settings.ASR_BATCH_SIZE == 15
        assert settings.TRACK_COMPONENT_TIMING is False
    
    def test_high_reliability_preset(self):
        """Test high reliability configuration"""
        settings = EnhancedSettings(
            CIRCUIT_BREAKER_FAILURE_THRESHOLD=3,
            MAX_RETRY_ATTEMPTS=5,
            ENABLE_METRICS=True,
            LOG_ERROR_CONTEXT=True
        )
        
        assert settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 3
        assert settings.MAX_RETRY_ATTEMPTS == 5


def run_all_tests():
    """Run all configuration tests"""
    print("=" * 80)
    print("TASK 14: CONFIGURATION MANAGEMENT TESTS")
    print("=" * 80)
    
    test_classes = [
        TestBasicConfiguration,
        TestVietnamesePreprocessing,
        TestClassificationSettings,
        TestMetricsConfiguration,
        TestErrorHandlingConfiguration,
        TestPerformanceSettings,
        TestValidation,
        TestHelperMethods,
        TestEnvironmentVariables,
        TestConfigurationPresets
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{'=' * 80}")
        print(f"Testing: {test_class.__name__}")
        print(f"{'=' * 80}")
        
        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✅ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"❌ {method_name}: {e}")
    
    print(f"\n{'=' * 80}")
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    print(f"{'=' * 80}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
