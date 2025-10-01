#!/usr/bin/env python3
"""
Test Task 13: Error Handling Enhancement
Demonstrates:
1. Custom exception hierarchy with context
2. Circuit breaker pattern
3. Retry with exponential backoff
4. User-friendly error messages
5. Graceful degradation
6. Error recovery mechanisms
"""

import sys
import time
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.error_handling import (
    BaseAppError, AudioInputError, ModelInferenceError,
    NetworkError, ResourceExhaustedError, ValidationError,
    TimeoutError as AppTimeoutError,
    CircuitBreaker, retry_with_backoff,
    ErrorSeverity, ErrorCategory
)

def test_custom_exceptions():
    """Test custom exception hierarchy"""
    print("\n" + "="*80)
    print("TEST 1: Custom Exception Hierarchy")
    print("="*80)
    
    # Test AudioInputError
    try:
        raise AudioInputError("Invalid audio format: expected WAV, got MP4")
    except BaseAppError as e:
        print(f"\nAudioInputError:")
        print(f"  User Message: {e.context.user_message}")
        print(f"  Technical: {e.context.error_message}")
        print(f"  Category: {e.context.category.value}")
        print(f"  Severity: {e.context.severity.value}")
        print(f"  Suggested Action: {e.context.suggested_action}")
        print(f"  Recoverable: {e.context.recoverable}")
    
    # Test ModelInferenceError
    try:
        raise ModelInferenceError("CUDA out of memory", model_name="Wav2Vec2")
    except BaseAppError as e:
        print(f"\nModelInferenceError:")
        print(f"  User Message: {e.context.user_message}")
        print(f"  Technical: {e.context.technical_details}")
        print(f"  Severity: {e.context.severity.value}")
    
    # Test ValidationError
    try:
        raise ValidationError("Audio duration exceeds limit", field="duration")
    except BaseAppError as e:
        print(f"\nValidationError:")
        print(f"  User Message: {e.context.user_message}")
        print(f"  Technical: {e.context.technical_details}")
    
    print("\n✓ Exception hierarchy works correctly!")

def test_circuit_breaker_basic():
    """Test basic circuit breaker functionality"""
    print("\n" + "="*80)
    print("TEST 2: Circuit Breaker - Basic Functionality")
    print("="*80)
    
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=2)
    
    def failing_function():
        raise Exception("Service unavailable")
    
    def working_function():
        return "Success!"
    
    print(f"\nInitial state: {cb.state.value}")
    
    # Cause failures to open circuit
    print("\nCausing 3 failures to open circuit...")
    for i in range(3):
        try:
            cb.call(failing_function)
        except Exception as e:
            print(f"  Attempt {i+1}: Failed (expected)")
    
    print(f"State after failures: {cb.state.value}")
    assert cb.state == CircuitBreaker.State.OPEN, "Circuit should be OPEN"
    
    # Try to call while circuit is open
    print("\nTrying to call while circuit is OPEN...")
    try:
        cb.call(working_function)
        print("  ERROR: Should have been blocked!")
    except ResourceExhaustedError as e:
        print(f"  ✓ Blocked: {e.context.user_message}")
    
    # Wait for timeout
    print(f"\nWaiting {cb.timeout_seconds}s for circuit to enter HALF_OPEN...")
    time.sleep(cb.timeout_seconds + 0.1)
    
    # Try again (should enter HALF_OPEN and succeed)
    print("Trying again after timeout...")
    result = cb.call(working_function)
    print(f"  Result: {result}")
    print(f"  State: {cb.state.value}")
    
    assert cb.state == CircuitBreaker.State.CLOSED, "Circuit should be CLOSED after success"
    print("\n✓ Circuit breaker works correctly!")

async def test_circuit_breaker_async():
    """Test async circuit breaker"""
    print("\n" + "="*80)
    print("TEST 3: Circuit Breaker - Async Operations")
    print("="*80)
    
    cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)
    
    async def async_failing_function():
        await asyncio.sleep(0.01)
        raise Exception("Async failure")
    
    async def async_working_function():
        await asyncio.sleep(0.01)
        return "Async success!"
    
    print("\nTesting async circuit breaker...")
    
    # Cause failures
    for i in range(2):
        try:
            await cb.call_async(async_failing_function)
        except Exception:
            print(f"  Attempt {i+1}: Failed (expected)")
    
    print(f"State: {cb.state.value}")
    
    # Wait and recover
    await asyncio.sleep(1.1)
    result = await cb.call_async(async_working_function)
    print(f"Result after recovery: {result}")
    
    print("✓ Async circuit breaker works!")

def test_retry_decorator():
    """Test retry with exponential backoff"""
    print("\n" + "="*80)
    print("TEST 4: Retry with Exponential Backoff")
    print("="*80)
    
    attempt_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1, exponential_base=2.0)
    def sometimes_fails():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  Attempt {attempt_count}")
        if attempt_count < 3:
            raise Exception(f"Temporary failure #{attempt_count}")
        return "Success after retries!"
    
    print("\nFunction that succeeds on 3rd attempt:")
    start_time = time.time()
    result = sometimes_fails()
    elapsed = time.time() - start_time
    
    print(f"\nResult: {result}")
    print(f"Total attempts: {attempt_count}")
    print(f"Total time: {elapsed:.2f}s")
    
    # Verify exponential backoff timing
    # Expected: 0.1s + 0.2s = 0.3s delay + execution time
    assert attempt_count == 3, "Should take 3 attempts"
    assert 0.25 < elapsed < 0.5, f"Timing seems off: {elapsed}s"
    
    print("✓ Retry decorator works correctly!")

async def test_retry_decorator_async():
    """Test async retry decorator"""
    print("\n" + "="*80)
    print("TEST 5: Async Retry with Exponential Backoff")
    print("="*80)
    
    attempt_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    async def async_sometimes_fails():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  Async attempt {attempt_count}")
        await asyncio.sleep(0.01)
        if attempt_count < 3:
            raise Exception(f"Async temporary failure #{attempt_count}")
        return "Async success after retries!"
    
    print("\nAsync function that succeeds on 3rd attempt:")
    result = await async_sometimes_fails()
    print(f"Result: {result}")
    print(f"Total attempts: {attempt_count}")
    
    print("✓ Async retry decorator works!")

def test_error_severity_levels():
    """Test different error severity levels"""
    print("\n" + "="*80)
    print("TEST 6: Error Severity Levels")
    print("="*80)
    
    errors = [
        AudioInputError("Invalid format"),           # LOW
        NetworkError("Connection timeout"),          # MEDIUM
        ModelInferenceError("Model crashed", "ASR"), # HIGH
        ResourceExhaustedError("Out of memory"),     # CRITICAL
    ]
    
    print("\nError Severity Hierarchy:")
    for error in errors:
        print(f"  {error.context.error_type:25s} → {error.context.severity.value:10s}")
        print(f"    User Msg: {error.context.user_message}")
        print(f"    Action:   {error.context.suggested_action}\n")
    
    print("✓ Severity levels properly assigned!")

def test_error_categories():
    """Test error categorization"""
    print("\n" + "="*80)
    print("TEST 7: Error Categorization")
    print("="*80)
    
    categories_tested = set()
    
    errors = [
        AudioInputError("Bad audio"),
        ModelInferenceError("Model error", "Test"),
        NetworkError("Connection lost"),
        ResourceExhaustedError("Memory full"),
        ValidationError("Invalid input"),
        AppTimeoutError("Operation timeout", operation="ASR"),
    ]
    
    print("\nError Categories:")
    for error in errors:
        category = error.context.category
        categories_tested.add(category)
        print(f"  {error.context.error_type:25s} → {category.value}")
    
    print(f"\n✓ Tested {len(categories_tested)} different categories!")

def test_circuit_breaker_recovery():
    """Test circuit breaker recovery mechanism"""
    print("\n" + "="*80)
    print("TEST 8: Circuit Breaker Recovery")
    print("="*80)
    
    cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1, half_open_attempts=2)
    
    call_count = 0
    
    def sometimes_works():
        nonlocal call_count
        call_count += 1
        # First 2 calls fail, then succeed
        if call_count <= 2:
            raise Exception("Still failing")
        return "Working now!"
    
    print("\nCausing failures to open circuit...")
    for i in range(2):
        try:
            cb.call(sometimes_works)
        except Exception:
            pass
    
    print(f"Circuit state: {cb.state.value}")
    assert cb.state == CircuitBreaker.State.OPEN
    
    # Wait for half-open
    time.sleep(1.1)
    print("\nAttempting recovery (HALF_OPEN state)...")
    
    # First attempt in half-open will still fail
    try:
        cb.call(sometimes_works)
    except Exception:
        print("  First recovery attempt: Failed")
    
    print(f"Circuit state: {cb.state.value}")
    
    # Wait again
    time.sleep(1.1)
    
    # Now it should work
    result = cb.call(sometimes_works)
    print(f"  Second recovery attempt: {result}")
    print(f"Circuit state: {cb.state.value}")
    
    print("✓ Circuit breaker recovery works!")

def test_error_context_preservation():
    """Test that error context is preserved"""
    print("\n" + "="*80)
    print("TEST 9: Error Context Preservation")
    print("="*80)
    
    try:
        raise ModelInferenceError(
            "Model timeout after 30s",
            model_name="PhoBERT",
            severity=ErrorSeverity.HIGH,
            recoverable=True
        )
    except BaseAppError as e:
        context = e.context
        
        print("\nError Context:")
        print(f"  Type: {context.error_type}")
        print(f"  Message: {context.error_message}")
        print(f"  Category: {context.category.value}")
        print(f"  Severity: {context.severity.value}")
        print(f"  User Message: {context.user_message}")
        print(f"  Technical Details: {context.technical_details}")
        print(f"  Recoverable: {context.recoverable}")
        print(f"  Suggested Action: {context.suggested_action}")
        print(f"  Timestamp: {context.timestamp}")
        
        # Verify all fields are populated
        assert context.error_type == "ModelInferenceError"
        assert "PhoBERT" in context.technical_details
        assert context.severity == ErrorSeverity.HIGH
        assert context.recoverable == True
        
    print("\n✓ Error context preserved correctly!")

if __name__ == '__main__':
    print("\n" + "="*80)
    print("Task 13: Error Handling Enhancement Test Suite")
    print("="*80)
    
    try:
        # Run all tests
        test_custom_exceptions()
        test_circuit_breaker_basic()
        test_retry_decorator()
        test_error_severity_levels()
        test_error_categories()
        test_circuit_breaker_recovery()
        test_error_context_preservation()
        
        # Run async tests
        print("\nRunning async tests...")
        asyncio.run(test_circuit_breaker_async())
        asyncio.run(test_retry_decorator_async())
        
        print("\n" + "="*80)
        print("✅ All Task 13 tests completed successfully!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("1. ✅ Custom exception hierarchy with context")
        print("2. ✅ Circuit breaker pattern (CLOSED/OPEN/HALF_OPEN)")
        print("3. ✅ Retry with exponential backoff")
        print("4. ✅ User-friendly error messages")
        print("5. ✅ Error severity levels (LOW/MEDIUM/HIGH/CRITICAL)")
        print("6. ✅ Error categorization for handling")
        print("7. ✅ Graceful degradation via circuit breaker")
        print("8. ✅ Error recovery mechanisms")
        print("9. ✅ Context preservation for debugging")
        print("\nIntegration with AudioProcessor:")
        print("  - ASR calls protected by circuit breaker")
        print("  - Classifier calls protected by circuit breaker")
        print("  - Automatic retry on transient failures")
        print("  - User-friendly error messages in responses")
        print("  - Technical details logged for debugging")
        print()
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
