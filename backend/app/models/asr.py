#!/usr/bin/env python3
"""
ASR Model Module - Backend Implementation
Vietnamese Speech-to-Text with Wav2Vec2 Model - FastAPI Backend

Migrated từ local_wav2vec2_asr.py với:
- Dependency injection pattern
- Integration với FastAPI configuration
- Structured logging
- Clean architecture compliance
"""

import torch
import torchaudio
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

# Backend imports
from ..core.config import Settings
from ..core.logger import AudioProcessingLogger, AppLogger

@dataclass
class TranscriptionResult:
    """Kết quả transcription với metadata"""
    text: str
    confidence_score: float
    processing_time: float
    audio_duration: float  
    real_time_factor: float
    sample_rate: int
    success: bool
    error_message: Optional[str] = None

class LocalWav2Vec2ASRError(Exception):
    """Base exception cho LocalWav2Vec2ASR"""
    pass

class ModelLoadError(LocalWav2Vec2ASRError):
    """Lỗi khi load model"""
    pass

class AudioProcessingError(LocalWav2Vec2ASRError):
    """Lỗi khi xử lý audio"""
    pass

class LocalWav2Vec2ASR:
    """
    Offline Vietnamese ASR sử dụng Wav2Vec2 model từ local path
    Backend version với dependency injection và structured logging
    
    Features:
    - Offline-first với local_files_only=True
    - Auto resample về 16kHz 
    - Clean architecture với error handling
    - Confidence scoring
    - Structured logging integration
    - Configuration-driven paths
    """
    
    def __init__(self, settings: Settings, logger: Optional[AudioProcessingLogger] = None):
        """
        Initialize LocalWav2Vec2ASR với dependency injection
        
        Args:
            settings: Application settings với model paths
            logger: Structured logger instance
        """
        self.settings = settings
        self.audio_logger = logger or AudioProcessingLogger("asr_model")
        self.app_logger = AppLogger("asr_app")
        
        # Get model path from settings
        self.model_path = Path(settings.ASR_MODEL_PATH)
        
        self.processor: Optional[Wav2Vec2Processor] = None
        self.model: Optional[Wav2Vec2ForCTC] = None
        self.target_sample_rate = 16000  # Wav2Vec2 requires 16kHz
        self.is_loaded = False
        
        # Pre-create reusable resample transform cache (expensive to create each time)
        self._resampler_cache = {}
        
        # Determine device for optimal performance
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model during initialization
        self._load_model()
    
    def _load_model(self) -> None:
        """Load Wav2Vec2 model và processor từ local path với structured logging"""
        load_start_time = time.time()
        
        try:
            self.app_logger.log_model_loading_start(
                model_type="wav2vec2_asr",
                model_path=str(self.model_path)
            )
            
            # Kiểm tra model path tồn tại
            if not self.model_path.exists():
                raise ModelLoadError(f"Model path không tồn tại: {self.model_path}")
                
            # Kiểm tra các file cần thiết
            required_files = ["config.json", "preprocessor_config.json", "vocab.json"]
            for file_name in required_files:
                if not (self.model_path / file_name).exists():
                    raise ModelLoadError(f"Thiếu file cần thiết: {file_name}")
            
            # Load processor với local_files_only=True
            self.processor = Wav2Vec2Processor.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                use_auth_token=False
            )
            
            # Load model với local_files_only=True  
            self.model = Wav2Vec2ForCTC.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                use_auth_token=False
            )
            
            # Đặt model về eval mode cho inference và move to device
            self.model.eval()
            # Move model to device - type: ignore due to transformers library type inference issue
            self.model = self.model.to(self.device)  # type: ignore[assignment]
            
            self.is_loaded = True
            
            # Calculate model parameters
            num_params = sum(p.numel() for p in self.model.parameters())
            loading_time = time.time() - load_start_time
            
            # Log successful loading
            self.app_logger.log_model_loading_success(
                model_type="wav2vec2_asr",
                loading_time=loading_time,
                model_params=num_params
            )
            
        except Exception as e:
            self.is_loaded = False
            loading_time = time.time() - load_start_time
            error_msg = f"Failed to load ASR model: {e}"
            
            self.app_logger.log_model_loading_error(
                model_type="wav2vec2_asr",
                error=error_msg,
                loading_time=loading_time
            )
            
            raise ModelLoadError(error_msg) from e
    
    def _validate_input(self, waveform: torch.Tensor, sample_rate: int) -> None:
        """Validate input waveform và sample_rate"""
        if not isinstance(waveform, torch.Tensor):
            raise AudioProcessingError("Waveform phải là torch.Tensor")
            
        if waveform.dim() == 0 or waveform.numel() == 0:
            raise AudioProcessingError("Waveform không được rỗng")
            
        if sample_rate <= 0:
            raise AudioProcessingError("Sample rate phải > 0")
            
        # Kiểm tra độ dài audio (không quá 30s để tránh memory issues)
        duration = waveform.shape[-1] / sample_rate
        if duration > 30.0:
            self.audio_logger.logger.warning(
                "long_audio_warning",
                duration=duration,
                max_duration=30.0
            )
        
        if duration < 0.1:
            raise AudioProcessingError("Audio quá ngắn (< 0.1s)")
    
    def _preprocess_audio(self, waveform: torch.Tensor, sample_rate: int) -> torch.Tensor:
        """
        Preprocess audio: handle mono/stereo, resample, normalize
        Optimized for real-time performance with cached resamplers
        
        Args:
            waveform: Input audio tensor
            sample_rate: Original sample rate
            
        Returns:
            Preprocessed waveform tensor
        """
        try:
            # Handle multi-channel audio -> convert to mono
            if waveform.dim() > 1 and waveform.shape[0] > 1:
                self.audio_logger.logger.debug(
                    "audio_preprocessing",
                    operation="convert_to_mono",
                    original_channels=waveform.shape[0]
                )
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Ensure 1D tensor
            if waveform.dim() > 1:
                waveform = waveform.squeeze()
            
            # Resample về 16kHz nếu cần với cached resampler
            if sample_rate != self.target_sample_rate:
                self.audio_logger.logger.debug(
                    "audio_preprocessing",
                    operation="resample",
                    original_sample_rate=sample_rate,
                    target_sample_rate=self.target_sample_rate
                )
                
                # Use cached resampler for better performance
                resampler_key = (sample_rate, self.target_sample_rate)
                if resampler_key not in self._resampler_cache:
                    self._resampler_cache[resampler_key] = torchaudio.transforms.Resample(
                        orig_freq=sample_rate,
                        new_freq=self.target_sample_rate
                    ).to(self.device)
                
                resampler = self._resampler_cache[resampler_key]
                waveform = resampler(waveform.to(self.device))
            else:
                waveform = waveform.to(self.device)
            
            # Normalize audio (clip to [-1, 1] range) - in-place for memory efficiency
            max_amplitude = torch.max(torch.abs(waveform))
            if max_amplitude > 1.0:
                self.audio_logger.logger.debug(
                    "audio_preprocessing",
                    operation="normalize",
                    original_max_amplitude=max_amplitude.item()
                )
                waveform.div_(max_amplitude)  # In-place division
            
            # Remove DC offset - in-place
            waveform.sub_(torch.mean(waveform))  # In-place subtraction
            
            return waveform
            
        except Exception as e:
            raise AudioProcessingError(f"Audio preprocessing failed: {e}") from e
    
    def _compute_confidence_score(self, logits: torch.Tensor) -> float:
        """
        Tính confidence score từ logits
        
        Args:
            logits: Model output logits
            
        Returns:
            Average confidence score (0.0 - 1.0)
        """
        try:
            # Convert logits to probabilities
            probabilities = torch.softmax(logits, dim=-1)
            
            # Lấy max probability cho mỗi frame
            max_probs = torch.max(probabilities, dim=-1)[0]
            
            # Tính average confidence
            confidence = torch.mean(max_probs).item()
            
            return confidence
            
        except Exception as e:
            self.audio_logger.logger.warning(
                "confidence_computation_failed",
                error=str(e)
            )
            return 0.0
    
    def transcribe(self, waveform: torch.Tensor, sample_rate: int) -> str:
        """
        Transcribe audio waveform thành text
        
        Args:
            waveform: Audio tensor, có thể là 1D hoặc 2D
            sample_rate: Sample rate của audio
            
        Returns:
            Transcribed text
            
        Raises:
            ModelLoadError: Nếu model chưa được load
            AudioProcessingError: Nếu có lỗi xử lý audio
        """
        if not self.is_loaded or self.processor is None or self.model is None:
            raise ModelLoadError("Model chưa được load. Gọi _load_model() trước.")
        
        # Calculate audio duration for logging
        audio_duration = len(waveform) / sample_rate if waveform.numel() > 0 else 0.0
        
        self.audio_logger.log_asr_start(
            audio_duration=audio_duration,
            sample_rate=sample_rate
        )
        
        start_time = time.time()
        
        try:
            # Validate input
            self._validate_input(waveform, sample_rate)
            
            # Preprocess audio
            processed_waveform = self._preprocess_audio(waveform, sample_rate)
            
            # Recalculate duration after preprocessing
            audio_duration = len(processed_waveform) / self.target_sample_rate
            
            # Process với Wav2Vec2Processor
            inputs = self.processor(
                processed_waveform.numpy(),
                sampling_rate=self.target_sample_rate,
                return_tensors="pt",
                padding=True
            )
            
            # Inference với model - torch.inference_mode() faster than no_grad()
            with torch.inference_mode():
                logits = self.model(inputs.input_values.to(self.device)).logits
            
            # Decode predictions
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]
            
            # Compute metrics
            processing_time = time.time() - start_time
            confidence_score = self._compute_confidence_score(logits[0])
            real_time_factor = processing_time / audio_duration if audio_duration > 0 else 0.0
            
            # Log successful transcription
            self.audio_logger.log_asr_success(
                text=transcription,
                confidence=confidence_score,
                processing_time=processing_time,
                real_time_factor=real_time_factor
            )
            
            return transcription
            
        except Exception as e:
            processing_time = time.time() - start_time 
            error_msg = f"Transcription failed: {e}"
            
            self.audio_logger.log_asr_error(
                error=error_msg,
                processing_time=processing_time
            )
            
            raise AudioProcessingError(error_msg) from e
    
    def transcribe_with_metadata(self, waveform: torch.Tensor, sample_rate: int) -> TranscriptionResult:
        """
        Transcribe với metadata đầy đủ
        
        Args:
            waveform: Audio tensor
            sample_rate: Sample rate của audio
            
        Returns:
            TranscriptionResult với text và metadata
        """
        if not self.is_loaded:
            return TranscriptionResult(
                text="",
                confidence_score=0.0,
                processing_time=0.0,
                audio_duration=0.0,
                real_time_factor=0.0,
                sample_rate=sample_rate,
                success=False,
                error_message="Model chưa được load"
            )
        
        # Calculate initial audio duration
        audio_duration = len(waveform) / sample_rate if waveform.numel() > 0 else 0.0
        
        self.audio_logger.log_asr_start(
            audio_duration=audio_duration,
            sample_rate=sample_rate
        )
        
        start_time = time.time()
        
        try:
            # Ensure model và processor loaded
            if not self.is_loaded or self.processor is None or self.model is None:
                return TranscriptionResult(
                    text="",
                    confidence_score=0.0,
                    processing_time=0.0,
                    audio_duration=0.0,
                    real_time_factor=0.0,
                    sample_rate=sample_rate,
                    success=False,
                    error_message="Model chưa được load"
                )
            
            # Validate và preprocess
            self._validate_input(waveform, sample_rate)
            processed_waveform = self._preprocess_audio(waveform, sample_rate)
            
            # Recalculate duration after preprocessing
            audio_duration = len(processed_waveform) / self.target_sample_rate
            
            # Process với processor
            inputs = self.processor(
                processed_waveform.numpy(),
                sampling_rate=self.target_sample_rate,
                return_tensors="pt",
                padding=True
            )
            
            # Model inference - torch.inference_mode() faster than no_grad()
            with torch.inference_mode():
                logits = self.model(inputs.input_values.to(self.device)).logits
            
            # Decode predictions
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]
            
            # Compute confidence score
            confidence_score = self._compute_confidence_score(logits[0])
            
            processing_time = time.time() - start_time
            real_time_factor = processing_time / audio_duration if audio_duration > 0 else 0.0
            
            # Log successful transcription
            self.audio_logger.log_asr_success(
                text=transcription,
                confidence=confidence_score,
                processing_time=processing_time,
                real_time_factor=real_time_factor
            )
            
            return TranscriptionResult(
                text=transcription,
                confidence_score=confidence_score,
                processing_time=processing_time,
                audio_duration=audio_duration,
                real_time_factor=real_time_factor,
                sample_rate=self.target_sample_rate,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            self.audio_logger.log_asr_error(
                error=error_msg,
                processing_time=processing_time
            )
            
            return TranscriptionResult(
                text="",
                confidence_score=0.0,
                processing_time=processing_time,
                audio_duration=audio_duration,
                real_time_factor=0.0,
                sample_rate=sample_rate,
                success=False,
                error_message=error_msg
            )
    
    def get_model_info(self) -> Dict[str, Union[str, int, bool]]:
        """
        Lấy thông tin về model
        
        Returns:
            Dictionary chứa thông tin model
        """
        if not self.is_loaded:
            return {"loaded": False, "error": "Model chưa được load"}
        
        # Safe access to model info with proper null checks
        vocab_size = 0
        model_params = 0
        model_class = "Unknown"
        processor_class = "Unknown"
        
        if self.processor is not None:
            processor_class = self.processor.__class__.__name__
            # Try to get vocab size safely using getattr
            try:
                tokenizer = getattr(self.processor, 'tokenizer', None)
                if tokenizer and hasattr(tokenizer, 'vocab_size'):
                    vocab_size = tokenizer.vocab_size
                else:
                    feature_extractor = getattr(self.processor, 'feature_extractor', None)
                    if feature_extractor:
                        vocab_size = getattr(feature_extractor, 'vocab_size', 0)
            except Exception:
                vocab_size = 0
        
        if self.model is not None:
            model_class = self.model.__class__.__name__
            try:
                model_params = sum(p.numel() for p in self.model.parameters())
            except:
                model_params = 0
        
        return {
            "loaded": True,
            "model_path": str(self.model_path),
            "vocab_size": vocab_size,
            "target_sample_rate": self.target_sample_rate,
            "model_parameters": model_params,
            "model_class": model_class,
            "processor_class": processor_class
        }

# Factory function để tạo instance với dependency injection
def create_asr_model(settings: Settings, logger: Optional[AudioProcessingLogger] = None) -> LocalWav2Vec2ASR:
    """
    Factory function để tạo LocalWav2Vec2ASR instance với dependency injection
    
    Args:
        settings: Application settings
        logger: Optional structured logger
        
    Returns:
        LocalWav2Vec2ASR instance đã load model
    """
    return LocalWav2Vec2ASR(settings, logger)
