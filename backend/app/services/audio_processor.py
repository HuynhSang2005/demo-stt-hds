#!/usr/bin/env python3
"""
Audio Processing Service - FastAPI Backend
Core service orchestrating ASR + Classification pipeline

Features:
- Binary audio input processing
- Real-time audio chunk handling  
- End-to-end pipeline: audio → transcription → sentiment analysis
- Comprehensive error handling và structured logging
- Performance monitoring và metrics
- Integration với WebSocket real-time streaming
"""

import io
import time
import torch
import torchaudio
from typing import Optional, Dict, Any, Tuple, Union
from pathlib import Path

# Backend imports
from ..core.config import Settings
from ..core.logger import AudioProcessingLogger, AppLogger
from ..models.asr import LocalWav2Vec2ASR, create_asr_model, TranscriptionResult
from ..models.classifier import LocalPhoBERTClassifier, create_classifier_model, ClassificationResult
from ..schemas.audio import TranscriptResult, ErrorResponse, create_transcript_result, create_error_response

class AudioProcessorError(Exception):
    """Base exception cho AudioProcessor"""
    pass

class AudioDecodingError(AudioProcessorError):
    """Lỗi khi decode audio data"""
    pass

class PipelineError(AudioProcessorError):
    """Lỗi trong quá trình xử lý pipeline"""
    pass

class AudioProcessor:
    """
    Core audio processing service
    Orchestrates ASR + Classification pipeline với real-time capabilities
    
    Features:
    - Binary audio processing (WebM, WAV, etc.)
    - Automatic audio preprocessing và resampling
    - End-to-end pipeline với error recovery
    - Performance tracking và structured logging
    - Thread-safe operations
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize AudioProcessor với dependency injection
        
        Args:
            settings: Application settings với model paths
        """
        self.settings = settings
        self.audio_logger = AudioProcessingLogger("audio_processor")
        self.app_logger = AppLogger("audio_processor_app")
        
        # Initialize models
        self.asr_model: Optional[LocalWav2Vec2ASR] = None
        self.classifier_model: Optional[LocalPhoBERTClassifier] = None
        
        # Performance tracking
        self.processed_chunks = 0
        self.total_processing_time = 0.0
        self.total_audio_duration = 0.0
        
        # Load models
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize ASR và Classifier models với error handling"""
        try:
            self.app_logger.log_startup({
                "service": "audio_processor",
                "asr_model_path": self.settings.ASR_MODEL_PATH,
                "classifier_model_path": self.settings.CLASSIFIER_MODEL_PATH
            })
            
            # Load ASR model
            self.asr_model = create_asr_model(
                settings=self.settings,
                logger=self.audio_logger
            )
            
            # Load Classifier model
            self.classifier_model = create_classifier_model(
                settings=self.settings,
                logger=self.audio_logger
            )
            
            # Verify models loaded successfully
            if not self.asr_model.is_loaded or not self.classifier_model.is_loaded:
                raise PipelineError("Failed to load required models")
            
            self.audio_logger.logger.info(
                "audio_processor_initialized",
                asr_loaded=self.asr_model.is_loaded,
                classifier_loaded=self.classifier_model.is_loaded,
                event_type="processor_ready"
            )
            
        except Exception as e:
            error_msg = f"AudioProcessor initialization failed: {e}"
            self.app_logger.logger.error(
                "processor_init_error", 
                error=error_msg
            )
            raise PipelineError(error_msg) from e
    
    def _decode_audio_bytes(self, audio_data: bytes) -> Tuple[torch.Tensor, int]:
        """
        Decode binary audio data thành waveform tensor
        
        Args:
            audio_data: Binary audio data (WebM, WAV, MP3, etc.)
            
        Returns:
            Tuple of (waveform tensor, sample_rate)
            
        Raises:
            AudioDecodingError: Nếu không thể decode audio
        """
        try:
            # Create BytesIO object từ binary data
            audio_buffer = io.BytesIO(audio_data)
            
            # Decode using torchaudio
            waveform, sample_rate = torchaudio.load(audio_buffer)
            
            # Validate decoded audio
            if waveform.numel() == 0:
                raise AudioDecodingError("Decoded waveform is empty")
            
            if sample_rate <= 0:
                raise AudioDecodingError(f"Invalid sample rate: {sample_rate}")
            
            # Log successful decoding
            duration = waveform.shape[-1] / sample_rate
            self.audio_logger.log_audio_chunk_received(
                chunk_size=len(audio_data),
                chunk_duration=duration
            )
            
            return waveform, sample_rate
            
        except Exception as e:
            error_msg = f"Audio decoding failed: {e}"
            self.audio_logger.logger.error(
                "audio_decoding_error",
                error=error_msg,
                data_size=len(audio_data),
                event_type="decode_error"
            )
            raise AudioDecodingError(error_msg) from e
    
    def _validate_audio_input(self, waveform: torch.Tensor, sample_rate: int) -> None:
        """
        Validate audio input parameters
        
        Args:
            waveform: Audio tensor
            sample_rate: Sample rate
            
        Raises:
            AudioProcessorError: Nếu input không hợp lệ
        """
        if not isinstance(waveform, torch.Tensor):
            raise AudioProcessorError("Waveform must be torch.Tensor")
        
        if waveform.dim() == 0 or waveform.numel() == 0:
            raise AudioProcessorError("Waveform cannot be empty")
        
        if sample_rate <= 0:
            raise AudioProcessorError("Sample rate must be positive")
        
        # Check audio duration limits
        duration = waveform.shape[-1] / sample_rate
        if duration > self.settings.MAX_AUDIO_DURATION:
            raise AudioProcessorError(f"Audio too long: {duration:.1f}s > {self.settings.MAX_AUDIO_DURATION}s")
        
        if duration < self.settings.MIN_AUDIO_DURATION:
            raise AudioProcessorError(f"Audio too short: {duration:.1f}s < {self.settings.MIN_AUDIO_DURATION}s")
    
    def process_audio_bytes(self, audio_data: bytes) -> TranscriptResult:
        """
        Process binary audio data through complete pipeline
        
        Args:
            audio_data: Binary audio data from WebSocket/HTTP
            
        Returns:
            TranscriptResult với transcription và classification
            
        Raises:
            AudioProcessorError: Nếu processing fails
        """
        if not self.asr_model or not self.classifier_model:
            raise PipelineError("Models not initialized")
        
        pipeline_start_time = time.time()
        
        try:
            # 1. Decode binary audio
            waveform, sample_rate = self._decode_audio_bytes(audio_data)
            
            # 2. Validate audio input
            self._validate_audio_input(waveform, sample_rate)
            
            # Calculate audio duration
            audio_duration = waveform.shape[-1] / sample_rate
            
            # 3. ASR Processing
            asr_start_time = time.time()
            asr_result = self.asr_model.transcribe_with_metadata(waveform, sample_rate)
            asr_processing_time = time.time() - asr_start_time
            
            if not asr_result.success:
                raise PipelineError(f"ASR failed: {asr_result.error_message}")
            
            # 4. Classification Processing  
            classification_start_time = time.time()
            classifier_result = self.classifier_model.classify_with_metadata(asr_result.text)
            classification_processing_time = time.time() - classification_start_time
            
            if not classifier_result.success:
                raise PipelineError(f"Classification failed: {classifier_result.error_message}")
            
            # 5. Create final result
            total_processing_time = time.time() - pipeline_start_time
            
            transcript_result = create_transcript_result(
                text=asr_result.text,
                asr_confidence=asr_result.confidence_score,
                sentiment_label=classifier_result.label,
                sentiment_confidence=classifier_result.confidence_score,
                warning=classifier_result.warning,
                processing_time=total_processing_time,
                audio_duration=audio_duration,
                sample_rate=asr_result.sample_rate,
                all_scores=classifier_result.all_scores
            )
            
            # 6. Log successful pipeline completion
            self.audio_logger.log_pipeline_success(
                total_processing_time=total_processing_time,
                audio_duration=audio_duration,
                asr_time=asr_processing_time,
                classification_time=classification_processing_time
            )
            
            # 7. Update statistics
            self.processed_chunks += 1
            self.total_processing_time += total_processing_time
            self.total_audio_duration += audio_duration
            
            return transcript_result
            
        except Exception as e:
            processing_time = time.time() - pipeline_start_time
            error_msg = f"Audio processing pipeline failed: {e}"
            
            self.audio_logger.logger.error(
                "pipeline_processing_error",
                error=error_msg,
                processing_time=processing_time,
                event_type="pipeline_error"
            )
            
            raise PipelineError(error_msg) from e
    
    def process_audio_chunk_safe(self, audio_data: bytes) -> Union[TranscriptResult, ErrorResponse]:
        """
        Safe wrapper cho process_audio_bytes với comprehensive error handling
        
        Args:
            audio_data: Binary audio data
            
        Returns:
            TranscriptResult on success, ErrorResponse on failure
        """
        try:
            return self.process_audio_bytes(audio_data)
            
        except AudioDecodingError as e:
            return create_error_response(
                error_type="audio_decoding_error",
                message=str(e),
                details={"data_size": len(audio_data)}
            )
            
        except AudioProcessorError as e:
            return create_error_response(
                error_type="audio_processing_error", 
                message=str(e),
                details={"processor_stage": "validation"}
            )
            
        except PipelineError as e:
            return create_error_response(
                error_type="pipeline_error",
                message=str(e),
                details={"processor_stage": "pipeline"}
            )
            
        except Exception as e:
            return create_error_response(
                error_type="unknown_error",
                message=f"Unexpected error: {e}",
                details={"processor_stage": "unknown"}
            )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics và performance metrics
        
        Returns:
            Dictionary với processing stats
        """
        avg_processing_time = (
            self.total_processing_time / self.processed_chunks 
            if self.processed_chunks > 0 else 0.0
        )
        
        avg_real_time_factor = (
            self.total_processing_time / self.total_audio_duration
            if self.total_audio_duration > 0 else 0.0
        )
        
        return {
            "processed_chunks": self.processed_chunks,
            "total_processing_time": self.total_processing_time,
            "total_audio_duration": self.total_audio_duration,
            "average_processing_time": avg_processing_time,
            "average_real_time_factor": avg_real_time_factor,
            "asr_model_loaded": self.asr_model.is_loaded if self.asr_model else False,
            "classifier_model_loaded": self.classifier_model.is_loaded if self.classifier_model else False
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information về loaded models
        
        Returns:
            Dictionary với model information
        """
        asr_info = self.asr_model.get_model_info() if self.asr_model else {"loaded": False}
        classifier_info = self.classifier_model.get_model_info() if self.classifier_model else {"loaded": False}
        
        return {
            "asr_model": asr_info,
            "classifier_model": classifier_info,
            "processor_ready": (
                asr_info.get("loaded", False) and 
                classifier_info.get("loaded", False)
            )
        }
    
    def reset_stats(self) -> None:
        """Reset processing statistics"""
        self.processed_chunks = 0
        self.total_processing_time = 0.0
        self.total_audio_duration = 0.0
        
        self.audio_logger.logger.info(
            "processing_stats_reset",
            event_type="stats_reset"
        )

# Factory function để tạo AudioProcessor instance
def create_audio_processor(settings: Settings) -> AudioProcessor:
    """
    Factory function để tạo AudioProcessor instance
    
    Args:
        settings: Application settings
        
    Returns:
        AudioProcessor instance with loaded models
    """
    return AudioProcessor(settings)

# Global processor instance (singleton pattern)
_processor_instance: Optional[AudioProcessor] = None

def get_audio_processor(settings: Optional[Settings] = None) -> AudioProcessor:
    """
    Get singleton AudioProcessor instance
    
    Args:
        settings: Application settings (required for first call)
        
    Returns:
        AudioProcessor singleton instance
    """
    global _processor_instance
    
    if _processor_instance is None:
        if settings is None:
            raise ValueError("Settings required for first AudioProcessor initialization")
        _processor_instance = create_audio_processor(settings)
    
    return _processor_instance