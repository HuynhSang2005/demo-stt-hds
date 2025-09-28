#!/usr/bin/env python3
"""
Structured JSON Logging Module
Sử dụng structlog cho consistent, structured logging trong production
"""

import sys
import logging
import structlog
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path

# Configure structlog for JSON structured logging
def configure_structlog(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Configure structlog cho JSON structured logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json hoặc console)
    """
    
    # Convert log level string to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Processors for structlog
    processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name  
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="ISO"),
        # Stack info processor
        structlog.processors.StackInfoRenderer(),
        # Exception processor
        structlog.processors.format_exc_info,
        # Add caller info
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]
    
    if log_format.lower() == "json":
        # JSON formatter cho production
        processors.extend([
            # Render as JSON
            structlog.processors.JSONRenderer(indent=None)
        ])
    else:
        # Console formatter cho development
        processors.extend([
            # Console colors
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=structlog.threadlocal.wrap_dict(dict),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )


class AudioProcessingLogger:
    """
    Specialized logger cho audio processing events
    Cung cấp structured logging cho ASR và classification
    """
    
    def __init__(self, name: str = "audio_processor"):
        """
        Initialize audio processing logger
        
        Args:
            name: Logger name
        """
        self.logger = structlog.get_logger(name)
    
    def log_asr_start(self, audio_duration: float, sample_rate: int) -> None:
        """Log ASR processing start"""
        self.logger.info(
            "asr_processing_start",
            audio_duration=audio_duration,
            sample_rate=sample_rate,
            event="asr_start"
        )
    
    def log_asr_success(self, text: str, confidence: float, processing_time: float, 
                       real_time_factor: float) -> None:
        """Log successful ASR processing"""
        self.logger.info(
            "asr_processing_success",
            text_length=len(text),
            confidence=confidence,
            processing_time=processing_time,
            real_time_factor=real_time_factor,
            event="asr_success"
        )
    
    def log_asr_error(self, error: str, processing_time: float) -> None:
        """Log ASR processing error"""
        self.logger.error(
            "asr_processing_error",
            error=error,
            processing_time=processing_time,
            event="asr_error"
        )
    
    def log_classification_start(self, text_length: int) -> None:
        """Log classification processing start"""
        self.logger.info(
            "classification_processing_start",
            text_length=text_length,
            event="classification_start"
        )
    
    def log_classification_success(self, text: str, label: str, confidence: float, 
                                 warning: bool, processing_time: float) -> None:
        """Log successful classification"""
        self.logger.info(
            "classification_processing_success",
            text_snippet=text[:50] + "..." if len(text) > 50 else text,
            label=label,
            confidence=confidence,
            warning=warning,
            processing_time=processing_time,
            event="classification_success"
        )
    
    def log_classification_error(self, error: str, processing_time: float) -> None:
        """Log classification processing error"""
        self.logger.error(
            "classification_processing_error",
            error=error,
            processing_time=processing_time,
            event="classification_error"
        )
    
    def log_pipeline_success(self, total_processing_time: float, audio_duration: float,
                           asr_time: float, classification_time: float) -> None:
        """Log successful end-to-end pipeline processing"""
        self.logger.info(
            "pipeline_processing_success",
            total_processing_time=total_processing_time,
            audio_duration=audio_duration,
            asr_processing_time=asr_time,
            classification_processing_time=classification_time,
            pipeline_real_time_factor=total_processing_time / audio_duration if audio_duration > 0 else 0,
            event="pipeline_success"
        )
    
    def log_websocket_connection(self, client_id: Optional[str] = None) -> None:
        """Log WebSocket connection"""
        self.logger.info(
            "websocket_connection",
            client_id=client_id,
            event="websocket_connect"
        )
    
    def log_websocket_disconnection(self, client_id: Optional[str] = None, reason: Optional[str] = None) -> None:
        """Log WebSocket disconnection"""
        self.logger.info(
            "websocket_disconnection", 
            client_id=client_id,
            reason=reason,
            event="websocket_disconnect"
        )
    
    def log_audio_chunk_received(self, chunk_size: int, chunk_duration: Optional[float] = None) -> None:
        """Log audio chunk received"""
        self.logger.debug(
            "audio_chunk_received",
            chunk_size=chunk_size,
            chunk_duration=chunk_duration,
            event="audio_chunk"
        )


class WebSocketLogger:
    """
    Specialized logger cho WebSocket events
    """
    
    def __init__(self, name: str = "websocket"):
        """Initialize WebSocket logger"""
        self.logger = structlog.get_logger(name)
    
    def log_connection_start(self, client_host: Optional[str] = None) -> None:
        """Log WebSocket connection attempt"""
        self.logger.info(
            "websocket_connection_attempt",
            client_host=client_host,
            event="ws_connection_start"
        )
    
    def log_connection_accepted(self, client_host: Optional[str] = None) -> None:
        """Log WebSocket connection accepted"""
        self.logger.info(
            "websocket_connection_accepted",
            client_host=client_host,
            event="ws_connection_accepted"
        )
    
    def log_message_sent(self, message_type: str, message_size: int) -> None:
        """Log WebSocket message sent"""
        self.logger.debug(
            "websocket_message_sent",
            message_type=message_type,
            message_size=message_size,
            event="ws_message_sent"
        )
    
    def log_message_received(self, message_type: str, message_size: int) -> None:
        """Log WebSocket message received"""
        self.logger.debug(
            "websocket_message_received",
            message_type=message_type,
            message_size=message_size,
            event="ws_message_received"
        )
    
    def log_error(self, error: str, error_type: Optional[str] = None) -> None:
        """Log WebSocket error"""
        self.logger.error(
            "websocket_error",
            error=error,
            error_type=error_type,
            event="ws_error"
        )


class AppLogger:
    """
    Main application logger
    """
    
    def __init__(self, name: str = "app"):
        """Initialize app logger"""
        self.logger = structlog.get_logger(name)
    
    def log_startup(self, config: Dict[str, Any]) -> None:
        """Log application startup"""
        self.logger.info(
            "application_startup",
            config=config,
            event="app_startup"
        )
    
    def log_shutdown(self) -> None:
        """Log application shutdown"""
        self.logger.info(
            "application_shutdown",
            event="app_shutdown"
        )
    
    def log_model_loading_start(self, model_type: str, model_path: str) -> None:
        """Log model loading start"""
        self.logger.info(
            "model_loading_start",
            model_type=model_type,
            model_path=model_path,
            event="model_loading_start"
        )
    
    def log_model_loading_success(self, model_type: str, loading_time: float, 
                                 model_params: Optional[int] = None) -> None:
        """Log successful model loading"""
        self.logger.info(
            "model_loading_success",
            model_type=model_type,
            loading_time=loading_time,
            model_parameters=model_params,
            event="model_loading_success"
        )
    
    def log_model_loading_error(self, model_type: str, error: str, loading_time: float) -> None:
        """Log model loading error"""
        self.logger.error(
            "model_loading_error",
            model_type=model_type,
            error=error,
            loading_time=loading_time,
            event="model_loading_error"
        )


# Global logger instances
def get_audio_logger() -> AudioProcessingLogger:
    """Get audio processing logger instance"""
    return AudioProcessingLogger()


def get_websocket_logger() -> WebSocketLogger:
    """Get WebSocket logger instance"""
    return WebSocketLogger()


def get_app_logger() -> AppLogger:
    """Get application logger instance"""
    return AppLogger()


# Initialize logging on module import
configure_structlog()

# Create global logger instances
audio_logger = get_audio_logger()
websocket_logger = get_websocket_logger()
app_logger = get_app_logger()


if __name__ == "__main__":
    # Test logging
    print("🧪 TESTING STRUCTURED LOGGING")
    print("=" * 50)
    
    # Test các logger instances
    audio_logger.log_asr_start(audio_duration=2.5, sample_rate=16000)
    audio_logger.log_asr_success(
        text="Xin chào, tôi đang test logging",
        confidence=0.95,
        processing_time=0.15,
        real_time_factor=0.06
    )
    
    audio_logger.log_classification_success(
        text="Xin chào, tôi đang test logging",
        label="positive",
        confidence=0.98,
        warning=False,
        processing_time=0.05
    )
    
    websocket_logger.log_connection_accepted(client_host="127.0.0.1:5173")
    
    app_logger.log_startup({"debug": True, "models_loaded": True})
    
    print("✅ Logging test completed!")