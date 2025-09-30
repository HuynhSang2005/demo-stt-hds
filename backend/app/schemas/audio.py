#!/usr/bin/env python3
"""
Audio Processing Schemas - FastAPI Backend
Simple Pydantic models for API request/response validation

Defines schemas for:
- Audio processing requests and responses
- WebSocket message formats
- Error handling
- Real-time audio streaming
"""

from pydantic import BaseModel
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

# ================================
# Core Response Schemas
# ================================

class TranscriptResult(BaseModel):
    """
    Complete transcription và classification result
    API contract response cho processed audio
    """
    # ASR Results
    text: str
    asr_confidence: float  # 0.0 - 1.0
    
    # Classification Results  
    sentiment_label: str  # positive, negative, neutral, toxic
    sentiment_confidence: float  # 0.0 - 1.0
    
    # Warning Detection
    warning: bool  # True if toxic or negative
    
    # Bad Keywords Detection
    bad_keywords: Optional[List[str]] = None  # List of detected bad words
    
    # Performance Metrics
    processing_time: float  # seconds
    real_time_factor: float  # processing_time / audio_duration
    
    # Session Management
    session_id: Optional[str] = None  # For session-based processing
    
    # Audio Metadata
    audio_duration: float  # seconds
    sample_rate: int  # Hz
    
    # Detailed Scores (Optional)
    all_sentiment_scores: Optional[Dict[str, float]] = None
    
    # Timestamps
    timestamp: Optional[float] = None  # Unix timestamp (seconds since epoch)
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().timestamp()
        super().__init__(**data)

class ErrorResponse(BaseModel):
    """
    Standardized error response format
    """
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

# ================================
# WebSocket Message Schemas
# ================================

class AudioChunk(BaseModel):
    """
    WebSocket audio chunk message
    For real-time audio streaming
    """
    chunk_id: int
    audio_data: bytes
    sample_rate: int
    channels: int  # 1=mono, 2=stereo
    duration: Optional[float] = None
    is_final: bool = False

class WebSocketMessage(BaseModel):
    """
    Base WebSocket message format
    """
    message_type: str
    data: Union[Dict[str, Any], str, None] = None
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

class ConnectionStatus(BaseModel):
    """
    WebSocket connection status message
    """
    status: str  # connected, disconnected, error, ready
    client_id: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None

class ProcessingStatus(BaseModel):
    """
    Real-time processing status update
    """
    stage: str  # receiving, preprocessing, transcribing, classifying, completed, error
    progress: float  # 0.0 - 1.0
    message: Optional[str] = None

# ================================
# Model Information Schemas
# ================================

class ModelInfo(BaseModel):
    """
    Model information schema
    """
    model_type: str  # asr, classifier
    model_path: str
    loaded: bool
    parameters: Optional[int] = None
    vocab_size: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = None

class SystemStatus(BaseModel):
    """
    Overall system status
    """
    asr_model: ModelInfo
    classifier_model: ModelInfo
    system_ready: bool
    startup_time: Optional[float] = None
    memory_usage: Optional[Dict[str, float]] = None

# ================================
# Utility Functions
# ================================

def create_error_response(error_type: str, message: str, details: Optional[Dict] = None) -> ErrorResponse:
    """
    Helper function để tạo standardized error response
    
    Args:
        error_type: Error type identifier
        message: Human-readable error message
        details: Optional additional context
        
    Returns:
        ErrorResponse instance
    """
    return ErrorResponse(
        error=error_type,
        message=message,
        details=details
    )

def create_websocket_message(msg_type: str, data: Any = None) -> WebSocketMessage:
    """
    Helper function để tạo WebSocket message
    
    Args:
        msg_type: Message type
        data: Message payload
        
    Returns:
        WebSocketMessage instance
    """
    return WebSocketMessage(
        message_type=msg_type,
        data=data
    )

def create_transcript_result(
    text: str,
    asr_confidence: float,
    sentiment_label: str,
    sentiment_confidence: float,
    warning: bool,
    processing_time: float,
    audio_duration: float,
    sample_rate: int = 16000,
    all_scores: Optional[Dict[str, float]] = None,
    bad_keywords: Optional[List[str]] = None
) -> TranscriptResult:
    """
    Helper function để tạo complete transcript result
    
    Args:
        text: Transcribed text
        asr_confidence: ASR confidence score
        sentiment_label: Classification result
        sentiment_confidence: Classification confidence
        warning: Warning flag
        processing_time: Processing duration
        audio_duration: Audio duration
        sample_rate: Audio sample rate
        all_scores: All classification scores
        bad_keywords: List of detected bad words
        
    Returns:
        TranscriptResult instance
    """
    real_time_factor = processing_time / audio_duration if audio_duration > 0 else 0.0
    
    return TranscriptResult(
        text=text,
        asr_confidence=asr_confidence,
        sentiment_label=sentiment_label,
        sentiment_confidence=sentiment_confidence,
        warning=warning,
        bad_keywords=bad_keywords,
        processing_time=processing_time,
        real_time_factor=real_time_factor,
        audio_duration=audio_duration,
        sample_rate=sample_rate,
        all_sentiment_scores=all_scores
    )

# ================================
# Validation Helpers
# ================================

def validate_sentiment_label(label: str) -> bool:
    """Validate sentiment label"""
    allowed_labels = {'positive', 'negative', 'neutral', 'toxic'}
    return label in allowed_labels

def validate_message_type(msg_type: str) -> bool:
    """Validate WebSocket message type"""
    allowed_types = {
        'audio_chunk', 'transcription_result', 'error', 
        'connection_status', 'processing_status',
        'session_command', 'session_response'  # Session management
    }
    return msg_type in allowed_types


class SessionCommand(BaseModel):
    """WebSocket command for session management"""
    command: str  # start_session, end_session, get_session_info
    session_id: Optional[str] = None


class SessionResponse(BaseModel):
    """Response for session-related commands"""
    success: bool
    session_id: Optional[str] = None
    message: Optional[str] = None
    session_info: Optional[Dict[str, Any]] = None

def validate_connection_status(status: str) -> bool:
    """Validate connection status"""
    allowed_statuses = {'connected', 'disconnected', 'error', 'ready'}
    return status in allowed_statuses

def validate_processing_stage(stage: str) -> bool:
    """Validate processing stage"""
    allowed_stages = {
        'receiving', 'preprocessing', 'transcribing', 
        'classifying', 'completed', 'error'
    }
    return stage in allowed_stages