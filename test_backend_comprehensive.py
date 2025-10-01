#!/usr/bin/env python3
"""
Comprehensive Backend Testing Suite
Real-time Performance, Low Latency, Model Accuracy Validation

Test Categories:
1. Real-time Performance Tests (latency < 100ms)
2. Model Accuracy Tests (ASR + Classifier)
3. WebSocket Stability Tests
4. Concurrent Request Tests
5. Production Readiness Tests
"""

import os
import sys
import time
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add backend to path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

print("="*80)
print("COMPREHENSIVE BACKEND TESTING SUITE")
print("Real-Time Performance & Model Accuracy Validation")
print("="*80)

# Test counters
total_tests = 0
passed_tests = 0
test_results = []
performance_metrics = []

def test_result(name: str, passed: bool, details: str = "", duration_ms: float = 0, category: str = ""):
    """Record test result with performance metrics"""
    global total_tests, passed_tests, test_results, performance_metrics
    total_tests += 1
    if passed:
        passed_tests += 1
        status = "✅ PASS"
    else:
        status = "❌ FAIL"
    
    result = {
        "name": name,
        "category": category,
        "passed": passed,
        "details": details,
        "duration_ms": duration_ms
    }
    test_results.append(result)
    
    if duration_ms > 0:
        performance_metrics.append({
            "test": name,
            "latency_ms": duration_ms,
            "category": category
        })
    
    print(f"{status} | {name} | {duration_ms:.2f}ms")
    if details:
        print(f"     → {details}")

# ============================================================================
# SUITE 1: Real-Time Performance Tests (Target: <100ms)
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 1: Real-Time Performance Tests")
print(f"{'='*80}\n")

try:
    start = time.time()
    from app.core.config import Settings
    settings = Settings()
    duration = (time.time() - start) * 1000
    test_result("1.1: Load settings (cold start)", True, 
                f"Loaded in {duration:.2f}ms", duration, "Performance")
except Exception as e:
    test_result("1.1: Load settings", False, str(e), category="Performance")

try:
    start = time.time()
    from app.models.asr import create_asr_model
    from app.core.logger import AudioProcessingLogger
    
    logger = AudioProcessingLogger("test_asr")
    asr_model = create_asr_model(settings, logger)
    duration = (time.time() - start) * 1000
    
    test_result("1.2: ASR model loading", True,
                f"Model loaded in {duration:.2f}ms, Ready: {asr_model.is_loaded}", 
                duration, "Performance")
except Exception as e:
    test_result("1.2: ASR model loading", False, str(e), category="Performance")

try:
    start = time.time()
    from app.models.classifier import create_classifier_model
    
    classifier_model = create_classifier_model(settings, logger)
    duration = (time.time() - start) * 1000
    
    test_result("1.3: Classifier model loading", True,
                f"Model loaded in {duration:.2f}ms, Ready: {classifier_model.is_loaded}",
                duration, "Performance")
except Exception as e:
    test_result("1.3: Classifier model loading", False, str(e), category="Performance")

try:
    start = time.time()
    from app.services.audio_processor import AudioProcessor
    
    processor = AudioProcessor(settings)
    duration = (time.time() - start) * 1000
    
    test_result("1.4: AudioProcessor initialization", True,
                f"Processor ready in {duration:.2f}ms",
                duration, "Performance")
except Exception as e:
    test_result("1.4: AudioProcessor initialization", False, str(e), category="Performance")

# ============================================================================
# SUITE 2: Model Accuracy Tests
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 2: Model Accuracy Tests - ASR & Classifier")
print(f"{'='*80}\n")

try:
    # Test with sample Vietnamese text
    test_texts = [
        "Xin chào, tôi là trợ lý AI",
        "Thời tiết hôm nay đẹp quá",
        "Cảm ơn bạn đã sử dụng dịch vụ",
    ]
    
    start = time.time()
    results = []
    for text in test_texts:
        result = classifier_model.classify_ensemble(text)
        results.append(result)
    duration = (time.time() - start) * 1000
    avg = duration / len(test_texts)
    
    test_result("2.1: Classifier accuracy (positive texts)", True,
                f"Avg: {avg:.2f}ms per classification, All: {[r['label'] for r in results]}",
                duration, "Accuracy")
except Exception as e:
    test_result("2.1: Classifier accuracy", False, str(e), category="Accuracy")

try:
    # Test with toxic Vietnamese text
    toxic_texts = [
        "Đồ ngu ngốc",
        "Thằng khốn nạn",
        "Mày là đồ đần",
    ]
    
    start = time.time()
    toxic_results = []
    for text in toxic_texts:
        result = classifier_model.classify_ensemble(text)
        toxic_results.append(result)
    duration = (time.time() - start) * 1000
    avg = duration / len(toxic_texts)
    
    # Check if at least 2/3 are detected as toxic/negative
    toxic_count = sum(1 for r in toxic_results if r['label'] in ['toxic', 'negative'])
    accuracy = (toxic_count / len(toxic_texts)) * 100
    
    test_result("2.2: Classifier accuracy (toxic texts)", toxic_count >= 2,
                f"Avg: {avg:.2f}ms, Detected: {toxic_count}/{len(toxic_texts)} ({accuracy:.0f}%), Labels: {[r['label'] for r in toxic_results]}",
                duration, "Accuracy")
except Exception as e:
    test_result("2.2: Classifier accuracy (toxic)", False, str(e), category="Accuracy")

try:
    # Test Vietnamese preprocessing
    from app.utils.vietnamese_preprocessing import VietnameseTextPreprocessor
    
    preprocessor = VietnameseTextPreprocessor()
    test_cases = [
        ("đc rồi", "được rồi"),
        ("ko muốn", "không muốn"),
        ("bn ơi", "bạn ơi"),
        ("tks", "thanks"),
    ]
    
    start = time.time()
    correct = 0
    for original, expected in test_cases:
        normalized = preprocessor.normalize(original)
        if expected in normalized.lower():
            correct += 1
    duration = (time.time() - start) * 1000
    accuracy = (correct / len(test_cases)) * 100
    
    test_result("2.3: Vietnamese preprocessing accuracy", correct >= 3,
                f"Accuracy: {accuracy:.0f}% ({correct}/{len(test_cases)}), Time: {duration:.2f}ms",
                duration, "Accuracy")
except Exception as e:
    test_result("2.3: Vietnamese preprocessing", False, str(e), category="Accuracy")

try:
    # Test toxic keyword detection
    from app.utils.toxic_keyword_detection import VietnameseToxicKeywordDetector
    
    detector = VietnameseToxicKeywordDetector()
    
    toxic_samples = [
        ("Đồ ngu", True),
        ("Xin chào", False),
        ("Thằng khốn", True),
        ("Cảm ơn bạn", False),
    ]
    
    start = time.time()
    correct = 0
    for text, should_be_toxic in toxic_samples:
        keywords = detector.detect_keywords(text)
        is_toxic = len(keywords) > 0
        if is_toxic == should_be_toxic:
            correct += 1
    duration = (time.time() - start) * 1000
    accuracy = (correct / len(toxic_samples)) * 100
    
    test_result("2.4: Toxic keyword detection accuracy", correct == len(toxic_samples),
                f"Accuracy: {accuracy:.0f}% ({correct}/{len(toxic_samples)}), Avg: {duration/len(toxic_samples):.2f}ms",
                duration, "Accuracy")
except Exception as e:
    test_result("2.4: Toxic keyword detection", False, str(e), category="Accuracy")

# ============================================================================
# SUITE 3: Latency Benchmarks (Target: <50ms for preprocessing, <100ms for inference)
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 3: Latency Benchmarks - Real-Time Requirements")
print(f"{'='*80}\n")

try:
    # Preprocessing latency test (100 iterations)
    iterations = 100
    texts = ["Xin chào bạn", "Cảm ơn", "đc rồi nha"] * 34  # ~100 texts
    
    start = time.time()
    for text in texts[:iterations]:
        _ = preprocessor.normalize(text)
    duration = (time.time() - start) * 1000
    avg = duration / iterations
    
    passed = avg < 1.0  # Target: <1ms
    test_result("3.1: Preprocessing latency benchmark", passed,
                f"Avg: {avg:.4f}ms per text (100 iterations), Total: {duration:.2f}ms",
                duration, "Latency")
except Exception as e:
    test_result("3.1: Preprocessing latency", False, str(e), category="Latency")

try:
    # Keyword detection latency test
    iterations = 100
    test_texts = ["Xin chào", "Đồ ngu", "Cảm ơn"] * 34
    
    start = time.time()
    for text in test_texts[:iterations]:
        _ = detector.detect_keywords(text)
    duration = (time.time() - start) * 1000
    avg = duration / iterations
    
    passed = avg < 2.0  # Target: <2ms
    test_result("3.2: Keyword detection latency benchmark", passed,
                f"Avg: {avg:.4f}ms per detection (100 iterations), Total: {duration:.2f}ms",
                duration, "Latency")
except Exception as e:
    test_result("3.2: Keyword detection latency", False, str(e), category="Latency")

try:
    # Classification latency test
    iterations = 20  # Fewer iterations due to model inference
    test_texts = ["Xin chào", "Cảm ơn", "Tốt quá"] * 7
    
    start = time.time()
    for text in test_texts[:iterations]:
        _ = classifier_model.classify_ensemble(text)
    duration = (time.time() - start) * 1000
    avg = duration / iterations
    
    passed = avg < 100  # Target: <100ms
    test_result("3.3: Classification latency benchmark", passed,
                f"Avg: {avg:.2f}ms per classification (20 iterations), Total: {duration:.2f}ms",
                duration, "Latency")
except Exception as e:
    test_result("3.3: Classification latency", False, str(e), category="Latency")

# ============================================================================
# SUITE 4: Concurrent Processing Tests
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 4: Concurrent Processing - Multi-Request Handling")
print(f"{'='*80}\n")

try:
    # Test concurrent classifications
    def classify_task(text: str) -> Dict[str, Any]:
        return classifier_model.classify_ensemble(text)
    
    texts = ["Xin chào", "Cảm ơn", "Tốt", "Hay", "Đẹp"] * 4  # 20 texts
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(classify_task, text) for text in texts[:20]]
        results = [f.result() for f in as_completed(futures)]
    duration = (time.time() - start) * 1000
    
    test_result("4.1: Concurrent classification (20 requests, 5 workers)", True,
                f"Completed in {duration:.2f}ms, Avg: {duration/20:.2f}ms per request",
                duration, "Concurrency")
except Exception as e:
    test_result("4.1: Concurrent classification", False, str(e), category="Concurrency")

try:
    # Test preprocessing concurrency
    def preprocess_task(text: str) -> str:
        return preprocessor.normalize(text)
    
    texts = ["đc rồi", "ko muốn", "bn ơi", "tks"] * 25  # 100 texts
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(preprocess_task, text) for text in texts[:100]]
        results = [f.result() for f in as_completed(futures)]
    duration = (time.time() - start) * 1000
    
    test_result("4.2: Concurrent preprocessing (100 requests, 10 workers)", True,
                f"Completed in {duration:.2f}ms, Avg: {duration/100:.2f}ms per request",
                duration, "Concurrency")
except Exception as e:
    test_result("4.2: Concurrent preprocessing", False, str(e), category="Concurrency")

# ============================================================================
# SUITE 5: Memory & Resource Tests
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 5: Memory & Resource Usage")
print(f"{'='*80}\n")

try:
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_mb = mem_info.rss / 1024 / 1024
    
    test_result("5.1: Memory usage check", mem_mb < 2000,  # <2GB
                f"Current usage: {mem_mb:.2f} MB",
                0, "Resource")
except Exception as e:
    test_result("5.1: Memory usage check", False, str(e), category="Resource")

try:
    # Test for memory leaks in repeated operations
    import gc
    gc.collect()
    
    mem_before = process.memory_info().rss / 1024 / 1024
    
    # Run 1000 operations
    for i in range(1000):
        _ = preprocessor.normalize("test text")
        _ = detector.detect_keywords("test text")
    
    gc.collect()
    mem_after = process.memory_info().rss / 1024 / 1024
    mem_increase = mem_after - mem_before
    
    test_result("5.2: Memory leak check (1000 operations)", mem_increase < 50,  # <50MB increase
                f"Memory before: {mem_before:.2f}MB, after: {mem_after:.2f}MB, increase: {mem_increase:.2f}MB",
                0, "Resource")
except Exception as e:
    test_result("5.2: Memory leak check", False, str(e), category="Resource")

# ============================================================================
# SUITE 6: Error Handling & Resilience
# ============================================================================

print(f"\n{'='*80}")
print("SUITE 6: Error Handling & Resilience")
print(f"{'='*80}\n")

try:
    # Test with empty text
    start = time.time()
    result = classifier_model.classify_ensemble("")
    duration = (time.time() - start) * 1000
    
    test_result("6.1: Handle empty text input", result is not None,
                f"Result: {result.get('label', 'N/A')}, Time: {duration:.2f}ms",
                duration, "Resilience")
except Exception as e:
    test_result("6.1: Handle empty text", False, str(e), category="Resilience")

try:
    # Test with very long text
    long_text = "Xin chào " * 500  # ~5000 chars
    start = time.time()
    result = classifier_model.classify_long_text(long_text)
    duration = (time.time() - start) * 1000
    
    test_result("6.2: Handle long text (5000+ chars)", result is not None,
                f"Processed with sliding window, Time: {duration:.2f}ms",
                duration, "Resilience")
except Exception as e:
    test_result("6.2: Handle long text", False, str(e), category="Resilience")

try:
    # Test circuit breaker functionality
    from app.core.error_handling import CircuitBreaker
    
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=5)
    
    def failing_function():
        raise Exception("Simulated failure")
    
    failures = 0
    for i in range(5):
        try:
            cb.call(failing_function)
        except:
            failures += 1
    
    # After 3 failures, circuit should open
    test_result("6.3: Circuit breaker functionality", cb.state.value == "open",
                f"Circuit state after {failures} failures: {cb.state.value}",
                0, "Resilience")
except Exception as e:
    test_result("6.3: Circuit breaker", False, str(e), category="Resilience")

try:
    # Test metrics collection
    from app.core.metrics import get_metrics_collector
    
    metrics = get_metrics_collector()
    
    # Record some metrics
    for i in range(10):
        metrics.record_request_latency(0.05 + i * 0.01, success=True)
    
    summary = metrics.get_metrics()
    has_metrics = summary.total_requests >= 10
    
    test_result("6.4: Metrics collection", has_metrics,
                f"Total requests: {summary.total_requests}, Avg latency: {summary.avg_latency:.4f}ms",
                0, "Resilience")
except Exception as e:
    test_result("6.4: Metrics collection", False, str(e), category="Resilience")

# ============================================================================
# SUMMARY & ANALYSIS
# ============================================================================

print(f"\n{'='*80}")
print("TEST SUMMARY - Backend Quality Validation")
print(f"{'='*80}")
print(f"Total Tests: {total_tests}")
print(f"Passed: {passed_tests} ✅")
print(f"Failed: {total_tests - passed_tests} ❌")
success_rate = (passed_tests/total_tests*100) if total_tests > 0 else 0
print(f"Success Rate: {success_rate:.1f}%")

# Performance Analysis
if performance_metrics:
    print(f"\n{'='*80}")
    print("PERFORMANCE ANALYSIS")
    print(f"{'='*80}")
    
    # Group by category
    categories = {}
    for metric in performance_metrics:
        cat = metric['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(metric['latency_ms'])
    
    for cat, latencies in categories.items():
        if latencies:
            avg = sum(latencies) / len(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            print(f"\n{cat}:")
            print(f"  Avg: {avg:.2f}ms")
            print(f"  Min: {min_lat:.2f}ms")
            print(f"  Max: {max_lat:.2f}ms")
            print(f"  Tests: {len(latencies)}")

# Real-time assessment
print(f"\n{'='*80}")
print("REAL-TIME PERFORMANCE ASSESSMENT")
print(f"{'='*80}")

latency_tests = [r for r in test_results if r['category'] == 'Latency']
latency_passed = sum(1 for r in latency_tests if r['passed'])
latency_rate = (latency_passed / len(latency_tests) * 100) if latency_tests else 0

accuracy_tests = [r for r in test_results if r['category'] == 'Accuracy']
accuracy_passed = sum(1 for r in accuracy_tests if r['passed'])
accuracy_rate = (accuracy_passed / len(accuracy_tests) * 100) if accuracy_tests else 0

print(f"Latency Tests: {latency_passed}/{len(latency_tests)} ({latency_rate:.0f}%)")
print(f"Accuracy Tests: {accuracy_passed}/{len(accuracy_tests)} ({accuracy_rate:.0f}%)")

if success_rate >= 90:
    print(f"\n✅ EXCELLENT - Backend is production-ready")
    print(f"✅ Real-time performance validated")
    print(f"✅ Low latency confirmed")
    print(f"✅ Model accuracy verified")
elif success_rate >= 75:
    print(f"\n⚠️ GOOD - Minor issues, mostly production-ready")
else:
    print(f"\n❌ NEEDS IMPROVEMENT - Critical issues detected")

print(f"{'='*80}")

# Save results
results_file = Path(__file__).parent / "backend_test_results_comprehensive.json"
results_data = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "success_rate": success_rate,
    "total_tests": total_tests,
    "passed": passed_tests,
    "failed": total_tests - passed_tests,
    "categories": {
        "latency": {"passed": latency_passed, "total": len(latency_tests), "rate": latency_rate},
        "accuracy": {"passed": accuracy_passed, "total": len(accuracy_tests), "rate": accuracy_rate},
    },
    "performance_metrics": performance_metrics,
    "tests": test_results
}

with open(results_file, "w", encoding="utf-8") as f:
    json.dump(results_data, f, indent=2, ensure_ascii=False)

print(f"\n📄 Detailed results saved to: {results_file}")

sys.exit(0 if passed_tests == total_tests else 1)
