#!/usr/bin/env python3
"""
Error Handling Enhancement Module
Task 13: Robust error handling with retry, circuit breaker, and graceful degradation

Features:
- Retry with exponential backoff
- Circuit breaker pattern
- Graceful degradation
- Custom exception hierarchy
- Error context preservation
- User-friendly error messages
"""

import time
import asyncio
import functools
from typing import Optional, Callable, Any, TypeVar, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

T = TypeVar('T')

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Recoverable, no action needed
    MEDIUM = "medium"     # Needs attention but not critical
    HIGH = "high"         # Critical, needs immediate attention
    CRITICAL = "critical" # System failure, immediate action required

class ErrorCategory(Enum):
    """Error categories for better handling"""
    AUDIO_INPUT = "audio_input"           # Invalid audio format/data
    MODEL_INFERENCE = "model_inference"   # Model processing errors
    NETWORK = "network"                   # Network/WebSocket errors
    RESOURCE = "resource"                 # Memory/CPU/disk errors
    VALIDATION = "validation"             # Input validation errors
    TIMEOUT = "timeout"                   # Operation timeouts
    UNKNOWN = "unknown"                   # Unclassified errors

@dataclass
class ErrorContext:
    """
    Comprehensive error context for debugging and monitoring
    """
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: float
    user_message: str  # Friendly message for end users
    technical_details: Optional[str] = None
    retry_count: int = 0
    recoverable: bool = True
    suggested_action: Optional[str] = None

class BaseAppError(Exception):
    """
    Base exception class with enhanced context
    """
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        technical_details: Optional[str] = None,
        recoverable: bool = True,
        suggested_action: Optional[str] = None
    ):
        super().__init__(message)
        self.context = ErrorContext(
            error_type=self.__class__.__name__,
            error_message=message,
            category=category,
            severity=severity,
            timestamp=time.time(),
            user_message=user_message or self._generate_user_message(message),
            technical_details=technical_details,
            recoverable=recoverable,
            suggested_action=suggested_action
        )
    
    def _generate_user_message(self, technical_message: str) -> str:
        """Generate user-friendly message from technical message"""
        # Override in subclasses for better messages
        return "An error occurred while processing your request. Please try again."

class AudioInputError(BaseAppError):
    """Audio input related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUDIO_INPUT,
            severity=ErrorSeverity.LOW,
            user_message="Invalid audio input. Please ensure your microphone is working and try again.",
            suggested_action="Check microphone permissions and audio quality",
            **kwargs
        )

class ModelInferenceError(BaseAppError):
    """Model inference errors"""
    def __init__(self, message: str, model_name: str = "Unknown", **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.MODEL_INFERENCE,
            severity=ErrorSeverity.HIGH,
            user_message=f"Speech processing temporarily unavailable. Please try again in a moment.",
            technical_details=f"Model: {model_name}, Error: {message}",
            suggested_action="Retry request or contact support if issue persists",
            **kwargs
        )

class NetworkError(BaseAppError):
    """Network and WebSocket errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            user_message="Connection issue detected. Attempting to reconnect...",
            suggested_action="Check internet connection",
            recoverable=True,
            **kwargs
        )

class ResourceExhaustedError(BaseAppError):
    """Resource limitation errors"""
    def __init__(self, message: str, resource_type: str = "Unknown", **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.CRITICAL,
            user_message="Service temporarily overloaded. Please try again in a few moments.",
            technical_details=f"Resource: {resource_type}, Error: {message}",
            suggested_action="Wait and retry, or contact support",
            recoverable=False,
            **kwargs
        )

class ValidationError(BaseAppError):
    """Input validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = f"Field: {field}, Error: {message}" if field else message
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            user_message=f"Invalid input: {message}",
            technical_details=details,
            suggested_action="Check input and try again",
            **kwargs
        )

class TimeoutError(BaseAppError):
    """Operation timeout errors"""
    def __init__(self, message: str, operation: str = "Unknown", timeout: float = 0, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            user_message="Operation took too long. Please try again with shorter audio.",
            technical_details=f"Operation: {operation}, Timeout: {timeout}s",
            suggested_action="Reduce audio length or check network connection",
            recoverable=True,
            **kwargs
        )

class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    
    Prevents cascading failures by temporarily disabling requests
    to a failing service after threshold is reached.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered
    """
    
    class State(Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_attempts: int = 1
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: How long to wait before attempting recovery
            half_open_attempts: Number of test requests in half-open state
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_attempts = half_open_attempts
        
        self.state = self.State.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            ResourceExhaustedError: If circuit is open
        """
        if self.state == self.State.OPEN:
            if self._should_attempt_reset():
                self.state = self.State.HALF_OPEN
                self.success_count = 0
            else:
                raise ResourceExhaustedError(
                    "Service temporarily unavailable due to repeated failures",
                    resource_type="CircuitBreaker"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Async version of call()"""
        if self.state == self.State.OPEN:
            if self._should_attempt_reset():
                self.state = self.State.HALF_OPEN
                self.success_count = 0
            else:
                raise ResourceExhaustedError(
                    "Service temporarily unavailable due to repeated failures",
                    resource_type="CircuitBreaker"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.timeout_seconds
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == self.State.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_attempts:
                self.state = self.State.CLOSED
                self.failure_count = 0
        elif self.state == self.State.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = self.State.OPEN
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.state = self.State.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry
        
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def unstable_function():
            # May fail occasionally
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Log retry attempt
                    print(f"Retry attempt {attempt + 1}/{max_attempts} after {delay:.1f}s: {e}")
                    
                    await asyncio.sleep(delay)
            
            # All retries exhausted
            if last_exception:
                raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        break
                    
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    print(f"Retry attempt {attempt + 1}/{max_attempts} after {delay:.1f}s: {e}")
                    
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def safe_execute(
    func: Callable[..., T],
    *args,
    default_value: Optional[T] = None,
    log_errors: bool = True,
    **kwargs
) -> Union[T, None]:
    """
    Execute function safely with error handling
    
    Args:
        func: Function to execute
        *args, **kwargs: Function arguments
        default_value: Value to return on error
        log_errors: Whether to log errors
        
    Returns:
        Function result or default_value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            print(f"Error in {func.__name__}: {e}")
        return default_value

async def safe_execute_async(
    func: Callable[..., Any],
    *args,
    default_value: Optional[Any] = None,
    log_errors: bool = True,
    **kwargs
) -> Union[Any, None]:
    """Async version of safe_execute"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            print(f"Error in {func.__name__}: {e}")
        return default_value

if __name__ == '__main__':
    # Test circuit breaker
    print("Testing Circuit Breaker...")
    
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=2)
    
    def failing_function():
        raise Exception("Test failure")
    
    # Cause failures to open circuit
    for i in range(5):
        try:
            cb.call(failing_function)
        except Exception as e:
            print(f"Attempt {i+1}: {e}")
    
    print(f"Circuit state: {cb.state}")
    
    # Test retry decorator
    print("\nTesting Retry Decorator...")
    
    attempt_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def sometimes_fails():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception(f"Failure #{attempt_count}")
        return "Success!"
    
    result = sometimes_fails()
    print(f"Result: {result}")
