#!/usr/bin/env python3
"""
Simplified Integration Test Suite for Task 15
Tests the actual API of Tasks 10-14 modules
"""

import os
import sys
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

print("="*80)
print("TASK 15: SIMPLIFIED INTEGRATION TEST SUITE")
print("Testing Tasks 10-14 Integration")
print("="*80)

# Test counters
total_tests = 0
passed_tests = 0

def test_result(name, passed, details=""):
    """Record test result"""
    global total_tests, passed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
    else:
        print(f"❌ {name}")
        if details:
            print(f"   Error: {details}")

# ============================================================================
# SUITE 1: Configuration Integration (Task 14)
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 1: Configuration Integration (Task 14)")
print(f"{'='*80}\n")

try:
    from app.core.config_enhanced import get_enhanced_settings, EnhancedSettings
    settings = get_enhanced_settings()
    test_result("1.1: Load enhanced configuration", True, f"Version: {settings.VERSION}")
except Exception as e:
    test_result("1.1: Load enhanced configuration", False, str(e))

try:
    preprocessing_config = settings.get_preprocessing_config()
    test_result("1.2: Get preprocessing config", True, f"Enabled: {preprocessing_config['enabled']}")
except Exception as e:
    test_result("1.2: Get preprocessing config", False, str(e))

try:
    classification_config = settings.get_classification_config()
    test_result("1.3: Get classification config", True, f"Ensemble: {classification_config['ensemble_enabled']}")
except Exception as e:
    test_result("1.3: Get classification config", False, str(e))

try:
    metrics_config = settings.get_metrics_config()
    test_result("1.4: Get metrics config", True, f"Enabled: {metrics_config['enabled']}")
except Exception as e:
    test_result("1.4: Get metrics config", False, str(e))

try:
    cb_config = settings.get_circuit_breaker_config()
    test_result("1.5: Get circuit breaker config", True, f"Threshold: {cb_config['failure_threshold']}")
except Exception as e:
    test_result("1.5: Get circuit breaker config", False, str(e))

# ============================================================================
# SUITE 2: Vietnamese Preprocessing (Task 10)
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 2: Vietnamese Preprocessing (Task 10)")
print(f"{'='*80}\n")

try:
    from app.utils.vietnamese_preprocessing import VietnameseTextPreprocessor, PreprocessingConfig
    config = PreprocessingConfig()
    preprocessor = VietnameseTextPreprocessor(config)
    test_result("2.1: Initialize Vietnamese preprocessor", True)
except Exception as e:
    test_result("2.1: Initialize Vietnamese preprocessor", False, str(e))

try:
    # Test normalization
    result = preprocessor.normalize("đc rồi nha")
    test_result("2.2: Normalize Vietnamese text", True, f"Result: '{result}'")
except Exception as e:
    test_result("2.2: Normalize Vietnamese text", False, str(e))

try:
    # Test confidence calculation
    confidence = preprocessor.calculate_confidence_adjustment("Xin chào!")
    test_result("2.3: Calculate confidence adjustment", True, f"Confidence: {confidence:.3f}")
except Exception as e:
    test_result("2.3: Calculate confidence adjustment", False, str(e))

# ============================================================================
# SUITE 3: Toxic Keyword Detection (Task 11)
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 3: Toxic Keyword Detection (Task 11)")
print(f"{'='*80}\n")

try:
    from app.utils.toxic_keyword_detection import VietnameseToxicKeywordDetector
    detector = VietnameseToxicKeywordDetector()
    test_result("3.1: Initialize toxic keyword detector", True)
except Exception as e:
    test_result("3.1: Initialize toxic keyword detector", False, str(e))

try:
    # Test detection method (check what method exists)
    if hasattr(detector, 'detect_toxic_keywords'):
        result = detector.detect_toxic_keywords("Bạn thật tốt")
        test_result("3.2: Detect toxic keywords (detect_toxic_keywords)", True, f"Found: {len(result)} keywords")
    elif hasattr(detector, 'detect'):
        result = detector.detect("Bạn thật tốt")
        test_result("3.2: Detect toxic keywords (detect)", True, f"Result: {result}")
    elif hasattr(detector, 'find_toxic_keywords'):
        result = detector.find_toxic_keywords("Bạn thật tốt")
        test_result("3.2: Detect toxic keywords (find_toxic_keywords)", True, f"Found: {len(result)} keywords")
    else:
        methods = [m for m in dir(detector) if not m.startswith('_')]
        test_result("3.2: Detect toxic keywords", False, f"Available methods: {', '.join(methods[:5])}")
except Exception as e:
    test_result("3.2: Detect toxic keywords", False, str(e))

try:
    # Test toxic score
    if hasattr(detector, 'calculate_toxic_score'):
        score = detector.calculate_toxic_score("test text")
        test_result("3.3: Calculate toxic score", True, f"Score: {score:.3f}")
    else:
        test_result("3.3: Calculate toxic score", False, "Method not found")
except Exception as e:
    test_result("3.3: Calculate toxic score", False, str(e))

# ============================================================================
# SUITE 4: Metrics Collection (Task 12)
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 4: Metrics Collection (Task 12)")
print(f"{'='*80}\n")

try:
    from app.core.metrics import get_metrics_collector
    metrics = get_metrics_collector()
    test_result("4.1: Initialize metrics collector", True)
except Exception as e:
    test_result("4.1: Initialize metrics collector", False, str(e))

try:
    # Test recording latency
    if hasattr(metrics, 'record_request_latency'):
        metrics.record_request_latency(0.150, success=True)
        test_result("4.2: Record request latency", True)
    elif hasattr(metrics, 'record_latency'):
        metrics.record_latency(0.150)
        test_result("4.2: Record request latency (record_latency)", True)
    else:
        methods = [m for m in dir(metrics) if not m.startswith('_') and 'record' in m.lower()]
        test_result("4.2: Record request latency", False, f"Available methods: {', '.join(methods[:5])}")
except Exception as e:
    test_result("4.2: Record request latency", False, str(e))

try:
    # Test getting metrics
    if hasattr(metrics, 'get_metrics'):
        summary = metrics.get_metrics()
        # Check if it's a dict or object
        if isinstance(summary, dict):
            test_result("4.3: Get metrics summary (dict)", True, f"Keys: {', '.join(list(summary.keys())[:5])}")
        else:
            # It's an object, get attributes
            attrs = [a for a in dir(summary) if not a.startswith('_')]
            test_result("4.3: Get metrics summary (object)", True, f"Attributes: {', '.join(attrs[:5])}")
    else:
        test_result("4.3: Get metrics summary", False, "Method not found")
except Exception as e:
    test_result("4.3: Get metrics summary", False, str(e))

# ============================================================================
# SUITE 5: Circuit Breaker (Task 13)
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 5: Circuit Breaker (Task 13)")
print(f"{'='*80}\n")

try:
    from app.core.error_handling import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=5, timeout_seconds=60, half_open_attempts=2)
    test_result("5.1: Initialize circuit breaker", True, f"State: {cb.state}")
except Exception as e:
    test_result("5.1: Initialize circuit breaker", False, str(e))

try:
    # Test state check
    if hasattr(cb, 'state'):
        state = cb.state
        test_result("5.2: Check circuit breaker state", True, f"State: {state}")
    else:
        test_result("5.2: Check circuit breaker state", False, "State attribute not found")
except Exception as e:
    test_result("5.2: Check circuit breaker state", False, str(e))

try:
    # Test recording (check what methods exist)
    if hasattr(cb, 'on_success'):
        cb.on_success()
        test_result("5.3: Record success (on_success)", True)
    elif hasattr(cb, 'record_success'):
        cb.record_success()
        test_result("5.3: Record success (record_success)", True)
    elif hasattr(cb, 'success'):
        cb.success()
        test_result("5.3: Record success (success)", True)
    else:
        methods = [m for m in dir(cb) if not m.startswith('_')]
        test_result("5.3: Record success", False, f"Available methods: {', '.join(methods[:5])}")
except Exception as e:
    test_result("5.3: Record success", False, str(e))

# ============================================================================
# SUITE 6: Error Handling (Task 13)
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 6: Error Handling (Task 13)")
print(f"{'='*80}\n")

try:
    from app.core.error_handling import (
        BaseAppError,
        AudioInputError,
        ModelInferenceError,
        ErrorContext
    )
    test_result("6.1: Import error classes", True)
except Exception as e:
    test_result("6.1: Import error classes", False, str(e))

try:
    # Test creating error context
    if 'ErrorContext' in locals():
        context = ErrorContext(
            error_type="TestError",
            message="Test message",
            category="test",
            severity="low"
        )
        test_result("6.2: Create error context", True, f"Type: {context.error_type}")
    else:
        test_result("6.2: Create error context", False, "ErrorContext not available")
except Exception as e:
    test_result("6.2: Create error context", False, str(e))

try:
    # Test creating custom error
    if 'AudioInputError' in locals():
        error = AudioInputError("Test audio error")
        test_result("6.3: Create AudioInputError", True, f"Message: {str(error)}")
    else:
        test_result("6.3: Create AudioInputError", False, "AudioInputError not available")
except Exception as e:
    test_result("6.3: Create AudioInputError", False, str(e))

# ============================================================================
# SUITE 7: End-to-End Integration
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 7: End-to-End Integration")
print(f"{'='*80}\n")

try:
    # Test all features can be enabled simultaneously
    test_settings = EnhancedSettings(
        ENABLE_ASYNC_PROCESSING=True,
        ENABLE_BATCH_PROCESSING=True,
        VIETNAMESE_PREPROCESSING_ENABLED=True,
        ENABLE_ENSEMBLE_CLASSIFICATION=True,
        ENABLE_METRICS=True,
        ENABLE_CIRCUIT_BREAKER=True,
        ENABLE_RETRY=True,
        ENABLE_KEYWORD_DETECTION=True
    )
    
    enabled_features = sum([
        test_settings.ENABLE_ASYNC_PROCESSING,
        test_settings.ENABLE_BATCH_PROCESSING,
        test_settings.VIETNAMESE_PREPROCESSING_ENABLED,
        test_settings.ENABLE_ENSEMBLE_CLASSIFICATION,
        test_settings.ENABLE_METRICS,
        test_settings.ENABLE_CIRCUIT_BREAKER,
        test_settings.ENABLE_RETRY,
        test_settings.ENABLE_KEYWORD_DETECTION
    ])
    
    test_result("7.1: Enable all features simultaneously", True, f"{enabled_features}/8 features enabled")
except Exception as e:
    test_result("7.1: Enable all features simultaneously", False, str(e))

try:
    # Test configuration presets
    high_accuracy = EnhancedSettings(
        TOXIC_THRESHOLD=0.45,
        ENSEMBLE_MODEL_WEIGHT=0.6,
        ENSEMBLE_KEYWORD_WEIGHT=0.4
    )
    test_result("7.2: High accuracy preset", True, f"Threshold: {high_accuracy.TOXIC_THRESHOLD}")
except Exception as e:
    test_result("7.2: High accuracy preset", False, str(e))

try:
    # Test feature toggling
    disabled = EnhancedSettings(ENABLE_METRICS=False, ENABLE_CIRCUIT_BREAKER=False)
    assert disabled.ENABLE_METRICS is False
    assert disabled.ENABLE_CIRCUIT_BREAKER is False
    test_result("7.3: Feature toggling via config", True)
except Exception as e:
    test_result("7.3: Feature toggling via config", False, str(e))

# ============================================================================
# SUMMARY
# ============================================================================

print(f"\n{'='*80}")
print("INTEGRATION TEST SUMMARY")
print(f"{'='*80}")
print(f"Total Tests: {total_tests}")
print(f"Passed: {passed_tests} ✅")
print(f"Failed: {total_tests - passed_tests} ❌")
print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
print(f"{'='*80}")

success = passed_tests == total_tests
sys.exit(0 if success else 1)
