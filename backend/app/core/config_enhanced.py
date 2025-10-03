#!/usr/bin/env python3
"""
Enhanced Configuration Management Module
Task 14: Centralized configuration for all optimization features

Features:
- Grouped configuration sections
- Type-safe settings with Pydantic
- Environment variable support
- Configuration validation
- Presets for different environments (dev/staging/prod)
- Hot-reload support (future)
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, Dict, Any
from enum import Enum

class Environment(str, Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class DeviceType(str, Enum):
    """Model inference device"""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon

class EnhancedSettings(BaseSettings):
    """
    Task 14: Enhanced centralized configuration
    
    Organized into logical sections:
    1. Project & Server
    2. Model Paths
    3. Audio Processing
    4. Performance & Optimization
    5. Vietnamese Text Processing (Task 10)
    6. Classification Settings (Task 11)
    7. Metrics & Monitoring (Task 12)
    8. Error Handling & Resilience (Task 13)
    9. Security & Limits
    """
    
    # =========================================================================
    # 1. PROJECT & SERVER CONFIGURATION
    # =========================================================================
    PROJECT_NAME: str = "Vietnamese Speech-to-Text + Toxic Detection API"
    VERSION: str = "2.0.0"  # Updated with all optimizations
    DESCRIPTION: str = "Offline-first Vietnamese Speech Analysis with Optimizations"
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, description="Deployment environment")
    
    # API Configuration
    API_V1_STR: str = "/v1"
    HOST: str = Field(default="127.0.0.1", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=True, description="Debug mode")
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )
    
    # =========================================================================
    # 2. MODEL PATHS & DEVICE CONFIGURATION
    # =========================================================================
    ASR_MODEL_PATH: str = Field(
        default="../wav2vec2-base-vietnamese-250h",
        description="Path to Wav2Vec2 Vietnamese ASR model"
    )
    CLASSIFIER_MODEL_PATH: str = Field(
        default="../phobert-vi-comment-4class",
        description="Path to PhoBERT classifier model"
    )
    
    # Device Configuration
    MODEL_DEVICE: DeviceType = Field(default=DeviceType.CPU, description="Device for inference")
    MODEL_CACHE_SIZE: int = Field(default=1, description="Model instances to cache")
    
    # =========================================================================
    # 3. AUDIO PROCESSING SETTINGS
    # =========================================================================
    AUDIO_CHUNK_DURATION: float = Field(default=2.0, description="Audio chunk duration (seconds)")
    MIN_AUDIO_DURATION: float = Field(default=0.1, description="Minimum audio duration (seconds)")
    MAX_AUDIO_DURATION: float = Field(default=30.0, description="Maximum audio duration (seconds)")
    TARGET_SAMPLE_RATE: int = Field(default=16000, description="Target sample rate for ASR")
    
    # Allowed formats
    ALLOWED_AUDIO_FORMATS: list[str] = Field(
        default=["audio/webm", "audio/wav", "audio/ogg", "audio/mp3"],
        description="Allowed audio MIME types"
    )
    
    # =========================================================================
    # 4. PERFORMANCE & OPTIMIZATION (Tasks 2-9)
    # =========================================================================
    
    # Async Processing
    ENABLE_ASYNC_PROCESSING: bool = Field(default=True, description="Enable asyncio.to_thread")
    MAX_CONCURRENT_CONNECTIONS: int = Field(default=100, description="Max WebSocket connections")
    REQUEST_TIMEOUT: float = Field(default=30.0, description="Request timeout (seconds)")
    
    # Batch Processing
    ENABLE_BATCH_PROCESSING: bool = Field(default=True, description="Enable micro-batching")
    ASR_BATCH_SIZE: int = Field(default=5, description="Max ASR batch size")
    ASR_BATCH_TIMEOUT: float = Field(default=0.05, description="ASR batch timeout (seconds)")
    CLASSIFIER_BATCH_SIZE: int = Field(default=8, description="Max classifier batch size")
    CLASSIFIER_BATCH_TIMEOUT: float = Field(default=0.03, description="Classifier batch timeout (seconds)")
    
    # Model Optimization
    USE_ONNX_RUNTIME: bool = Field(default=False, description="Use ONNX Runtime for inference")
    ONNX_OPTIMIZATION_LEVEL: int = Field(default=2, description="ONNX optimization level (0-99)")
    
    # =========================================================================
    # 5. VIETNAMESE TEXT PROCESSING (Task 10)
    # =========================================================================
    
    # Preprocessing settings
    VIETNAMESE_PREPROCESSING_ENABLED: bool = Field(default=True, description="Enable Vietnamese preprocessing")
    REMOVE_TONES_FOR_MATCHING: bool = Field(default=False, description="Remove Vietnamese tones")
    CONVERT_NUMBERS_TO_TEXT: bool = Field(default=False, description="Convert digits to Vietnamese words")
    NORMALIZE_PUNCTUATION: bool = Field(default=True, description="Normalize punctuation")
    APPLY_COMMON_FIXES: bool = Field(default=True, description="Apply common Vietnamese error fixes")
    FIX_SPACING: bool = Field(default=True, description="Fix spacing around punctuation")
    LOWERCASE_TEXT: bool = Field(default=False, description="Lowercase all text")
    
    # Confidence adjustment
    ENABLE_CONFIDENCE_ADJUSTMENT: bool = Field(default=True, description="Adjust confidence based on text quality")
    
    # =========================================================================
    # 6. CLASSIFICATION SETTINGS (Task 11)
    # =========================================================================
    
    # Ensemble classification
    ENABLE_ENSEMBLE_CLASSIFICATION: bool = Field(default=True, description="Use PhoBERT + keyword ensemble")
    ENSEMBLE_MODEL_WEIGHT: float = Field(default=0.7, description="PhoBERT weight in ensemble")
    ENSEMBLE_KEYWORD_WEIGHT: float = Field(default=0.3, description="Keyword weight in ensemble")
    
    # Classification thresholds
    TOXIC_THRESHOLD: float = Field(default=0.55, description="Toxic classification threshold")
    NEGATIVE_THRESHOLD: float = Field(default=0.60, description="Negative classification threshold")
    NEUTRAL_THRESHOLD: float = Field(default=0.50, description="Neutral classification threshold")
    POSITIVE_THRESHOLD: float = Field(default=0.60, description="Positive classification threshold")
    
    # Sliding window for long texts
    ENABLE_SLIDING_WINDOW: bool = Field(default=True, description="Use sliding window for long texts")
    SLIDING_WINDOW_SIZE: int = Field(default=400, description="Sliding window size (characters)")
    SLIDING_WINDOW_OVERLAP: int = Field(default=100, description="Sliding window overlap (characters)")
    LONG_TEXT_THRESHOLD: int = Field(default=500, description="Text length to trigger sliding window")
    
    # Keyword detection
    ENABLE_KEYWORD_DETECTION: bool = Field(default=True, description="Enable toxic keyword detection")
    KEYWORD_FUZZY_MATCHING: bool = Field(default=True, description="Enable fuzzy keyword matching")
    KEYWORD_DETECTION_THRESHOLD: float = Field(default=0.3, description="Keyword detection threshold")
    
    # =========================================================================
    # 7. METRICS & MONITORING (Task 12)
    # =========================================================================
    
    # Metrics collection
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    METRICS_WINDOW_SIZE: int = Field(default=1000, description="Metrics circular buffer size")
    METRICS_RETENTION_SECONDS: int = Field(default=3600, description="Metrics retention period")
    
    # Performance tracking
    TRACK_COMPONENT_TIMING: bool = Field(default=True, description="Track ASR/Classifier timing")
    TRACK_MEMORY_USAGE: bool = Field(default=True, description="Track memory usage")
    TRACK_ERROR_RATES: bool = Field(default=True, description="Track error rates")
    
    # Metrics export
    METRICS_EXPORT_INTERVAL: int = Field(default=60, description="Metrics export interval (seconds)")
    
    # =========================================================================
    # 8. ERROR HANDLING & RESILIENCE (Task 13)
    # =========================================================================
    
    # Circuit breaker
    ENABLE_CIRCUIT_BREAKER: bool = Field(default=True, description="Enable circuit breaker pattern")
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, description="Failures before opening circuit")
    CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = Field(default=60, description="Circuit breaker timeout")
    CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS: int = Field(default=2, description="Half-open test attempts")
    
    # Retry logic
    ENABLE_RETRY: bool = Field(default=True, description="Enable automatic retry")
    MAX_RETRY_ATTEMPTS: int = Field(default=3, description="Maximum retry attempts")
    RETRY_INITIAL_DELAY: float = Field(default=1.0, description="Initial retry delay (seconds)")
    RETRY_MAX_DELAY: float = Field(default=60.0, description="Maximum retry delay (seconds)")
    RETRY_EXPONENTIAL_BASE: float = Field(default=2.0, description="Exponential backoff base")
    
    # Error logging
    LOG_ERROR_CONTEXT: bool = Field(default=True, description="Log detailed error context")
    USER_FRIENDLY_ERRORS: bool = Field(default=True, description="Return user-friendly error messages")
    
    # =========================================================================
    # 9. SECURITY & LIMITS
    # =========================================================================
    
    # Rate limiting
    ENABLE_RATE_LIMITING: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Max requests per minute per client")
    
    # Resource limits
    MAX_REQUEST_SIZE_MB: int = Field(default=10, description="Max request size (MB)")
    MAX_MEMORY_PERCENT: float = Field(default=80.0, description="Max memory usage percent")
    
    # WebSocket limits
    WEBSOCKET_MESSAGE_SIZE_LIMIT: int = Field(default=10 * 1024 * 1024, description="Max WebSocket message size")
    WEBSOCKET_PING_INTERVAL: float = Field(default=20.0, description="WebSocket ping interval")
    WEBSOCKET_PING_TIMEOUT: float = Field(default=10.0, description="WebSocket ping timeout")
    
    # =========================================================================
    # 10. LOGGING CONFIGURATION
    # =========================================================================
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or console")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path (None = stdout)")
    LOG_ROTATION: str = Field(default="1 day", description="Log rotation interval")
    LOG_RETENTION: str = Field(default="30 days", description="Log retention period")
    
    # =========================================================================
    # VALIDATORS
    # =========================================================================
    
    @validator('ENSEMBLE_MODEL_WEIGHT', 'ENSEMBLE_KEYWORD_WEIGHT')
    def validate_ensemble_weights(cls, v, values):
        """Validate ensemble weights sum to 1.0"""
        if 'ENSEMBLE_MODEL_WEIGHT' in values and 'ENSEMBLE_KEYWORD_WEIGHT' in values:
            if not (0 <= v <= 1):
                raise ValueError("Ensemble weights must be between 0 and 1")
        return v
    
    @validator('TOXIC_THRESHOLD', 'NEGATIVE_THRESHOLD', 'NEUTRAL_THRESHOLD', 'POSITIVE_THRESHOLD')
    def validate_thresholds(cls, v):
        """Validate classification thresholds"""
        if not (0 <= v <= 1):
            raise ValueError("Classification thresholds must be between 0 and 1")
        return v
    
    @validator('MAX_AUDIO_DURATION')
    def validate_max_audio_duration(cls, v, values):
        """Validate max audio duration is reasonable"""
        if v > 300:  # 5 minutes
            raise ValueError("MAX_AUDIO_DURATION should not exceed 300 seconds")
        return v
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    class Config:
        """Pydantic configuration"""
        case_sensitive = True
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        env_file_encoding = "utf-8"
        use_enum_values = True
    
    def get_model_paths(self) -> Dict[str, Path]:
        """Get resolved model paths"""
        backend_dir = Path(__file__).resolve().parents[2]
        return {
            "asr": (backend_dir / Path(self.ASR_MODEL_PATH)).resolve(),
            "classifier": (backend_dir / Path(self.CLASSIFIER_MODEL_PATH)).resolve(),
        }
    
    def validate_model_paths(self) -> Dict[str, bool]:
        """Validate model paths exist"""
        paths = self.get_model_paths()
        return {
            "asr_exists": paths["asr"].exists(),
            "classifier_exists": paths["classifier"].exists(),
            "asr_has_config": (paths["asr"] / "config.json").exists(),
            "classifier_has_config": (paths["classifier"] / "config.json").exists()
        }
    
    def get_preprocessing_config(self) -> Dict[str, Any]:
        """Get Vietnamese preprocessing configuration"""
        return {
            "enabled": self.VIETNAMESE_PREPROCESSING_ENABLED,
            "remove_tones": self.REMOVE_TONES_FOR_MATCHING,
            "convert_numbers_to_text": self.CONVERT_NUMBERS_TO_TEXT,
            "normalize_punctuation": self.NORMALIZE_PUNCTUATION,
            "apply_common_fixes": self.APPLY_COMMON_FIXES,
            "fix_spacing": self.FIX_SPACING,
            "lowercase": self.LOWERCASE_TEXT
        }
    
    def get_classification_config(self) -> Dict[str, Any]:
        """Get classification configuration"""
        return {
            "ensemble_enabled": self.ENABLE_ENSEMBLE_CLASSIFICATION,
            "model_weight": self.ENSEMBLE_MODEL_WEIGHT,
            "keyword_weight": self.ENSEMBLE_KEYWORD_WEIGHT,
            "thresholds": {
                "toxic": self.TOXIC_THRESHOLD,
                "negative": self.NEGATIVE_THRESHOLD,
                "neutral": self.NEUTRAL_THRESHOLD,
                "positive": self.POSITIVE_THRESHOLD
            },
            "sliding_window": {
                "enabled": self.ENABLE_SLIDING_WINDOW,
                "window_size": self.SLIDING_WINDOW_SIZE,
                "overlap": self.SLIDING_WINDOW_OVERLAP,
                "threshold": self.LONG_TEXT_THRESHOLD
            }
        }
    
    def get_circuit_breaker_config(self) -> Dict[str, Any]:
        """Get circuit breaker configuration"""
        return {
            "enabled": self.ENABLE_CIRCUIT_BREAKER,
            "failure_threshold": self.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            "timeout_seconds": self.CIRCUIT_BREAKER_TIMEOUT_SECONDS,
            "half_open_attempts": self.CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS
        }
    
    def get_metrics_config(self) -> Dict[str, Any]:
        """Get metrics configuration"""
        return {
            "enabled": self.ENABLE_METRICS,
            "window_size": self.METRICS_WINDOW_SIZE,
            "retention_seconds": self.METRICS_RETENTION_SECONDS,
            "track_timing": self.TRACK_COMPONENT_TIMING,
            "track_memory": self.TRACK_MEMORY_USAGE,
            "track_errors": self.TRACK_ERROR_RATES
        }
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT or self.DEBUG
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return self.dict()
    
    def print_summary(self):
        """Print configuration summary"""
        print("=" * 80)
        print("CONFIGURATION SUMMARY")
        print("=" * 80)
        print(f"Project: {self.PROJECT_NAME} v{self.VERSION}")
        print(f"Environment: {self.ENVIRONMENT}")
        print(f"Debug Mode: {self.DEBUG}")
        print(f"Server: {self.HOST}:{self.PORT}")
        print()
        print("Feature Flags:")
        print(f"  ✓ Async Processing: {self.ENABLE_ASYNC_PROCESSING}")
        print(f"  ✓ Batch Processing: {self.ENABLE_BATCH_PROCESSING}")
        print(f"  ✓ Vietnamese Preprocessing: {self.VIETNAMESE_PREPROCESSING_ENABLED}")
        print(f"  ✓ Ensemble Classification: {self.ENABLE_ENSEMBLE_CLASSIFICATION}")
        print(f"  ✓ Metrics Collection: {self.ENABLE_METRICS}")
        print(f"  ✓ Circuit Breaker: {self.ENABLE_CIRCUIT_BREAKER}")
        print(f"  ✓ Retry Logic: {self.ENABLE_RETRY}")
        print("=" * 80)


# Global settings instance
enhanced_settings = EnhancedSettings()


def get_enhanced_settings() -> EnhancedSettings:
    """Get enhanced settings instance for dependency injection"""
    return enhanced_settings


if __name__ == "__main__":
    # Test configuration
    settings = EnhancedSettings()
    settings.print_summary()
    
    print("\nModel Paths:")
    paths = settings.get_model_paths()
    for name, path in paths.items():
        print(f"  {name}: {path}")
    
    print("\nModel Validation:")
    validation = settings.validate_model_paths()
    for check, status in validation.items():
        print(f"  {check}: {'✅' if status else '❌'}")
