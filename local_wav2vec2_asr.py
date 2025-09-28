#!/usr/bin/env python3
"""
LocalWav2Vec2ASR - Prompt 2.1 Implementation
Offline Vietnamese Speech-to-Text with Wav2Vec2 Model

Clean Architecture implementation with:
- Load model + processor từ local path
- Phương thức transcribe(waveform: torch.Tensor, sample_rate: int) -> str  
- Tự động resample về 16kHz nếu cần
- Error handling và confidence scoring
- Audio preprocessing và validation
"""

import torch
import torchaudio
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    Features:
    - Offline-first với local_files_only=True
    - Auto resample về 16kHz 
    - Clean architecture với error handling
    - Confidence scoring
    - Audio preprocessing và validation
    """
    
    def __init__(self, model_path: str = "./wav2vec2-base-vietnamese-250h"):
        """
        Initialize LocalWav2Vec2ASR
        
        Args:
            model_path: Path tới folder chứa Wav2Vec2 model và processor
        """
        self.model_path = Path(model_path)
        self.processor: Optional[Wav2Vec2Processor] = None
        self.model: Optional[Wav2Vec2ForCTC] = None
        self.target_sample_rate = 16000  # Wav2Vec2 requires 16kHz
        self.is_loaded = False
        
        # Load model ngay khi khởi tạo
        self._load_model()
    
    def _load_model(self) -> None:
        """Load Wav2Vec2 model và processor từ local path"""
        try:
            logger.info(f"🔄 Loading Wav2Vec2 model từ {self.model_path}")
            
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
            
            # Đặt model về eval mode cho inference
            self.model.eval()
            
            self.is_loaded = True
            
            # Log model info
            num_params = sum(p.numel() for p in self.model.parameters())
            # Get vocab size from feature extractor instead of tokenizer
            vocab_size = len(getattr(self.processor, 'tokenizer', {'vocab': {}}).__dict__.get('encoder', {}))
            
            logger.info(f"✅ Model loaded successfully!")
            logger.info(f"   - Model parameters: {num_params:,}")
            logger.info(f"   - Vocab size estimated: {vocab_size}")
            logger.info(f"   - Target sample rate: {self.target_sample_rate}Hz")
            
        except Exception as e:
            self.is_loaded = False
            error_msg = f"Failed to load model: {e}"
            logger.error(f"❌ {error_msg}")
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
            logger.warning(f"⚠️ Audio dài {duration:.1f}s, có thể ảnh hưởng performance")
        
        if duration < 0.1:
            raise AudioProcessingError("Audio quá ngắn (< 0.1s)")
    
    def _preprocess_audio(self, waveform: torch.Tensor, sample_rate: int) -> torch.Tensor:
        """
        Preprocess audio: handle mono/stereo, resample, normalize
        
        Args:
            waveform: Input audio tensor
            sample_rate: Original sample rate
            
        Returns:
            Preprocessed waveform tensor
        """
        try:
            # Handle multi-channel audio -> convert to mono
            if waveform.dim() > 1 and waveform.shape[0] > 1:
                logger.debug("Converting multi-channel audio to mono")
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Ensure 1D tensor
            if waveform.dim() > 1:
                waveform = waveform.squeeze()
            
            # Resample về 16kHz nếu cần
            if sample_rate != self.target_sample_rate:
                logger.debug(f"Resampling {sample_rate}Hz → {self.target_sample_rate}Hz")
                waveform = torchaudio.functional.resample(
                    waveform, 
                    orig_freq=sample_rate, 
                    new_freq=self.target_sample_rate
                )
            
            # Normalize audio (clip to [-1, 1] range)
            if torch.max(torch.abs(waveform)) > 1.0:
                logger.debug("Normalizing audio amplitude")
                waveform = waveform / torch.max(torch.abs(waveform))
            
            # Remove DC offset  
            waveform = waveform - torch.mean(waveform)
            
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
            logger.warning(f"Failed to compute confidence: {e}")
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
            
        start_time = time.time()
        
        try:
            # Validate input
            self._validate_input(waveform, sample_rate)
            
            # Preprocess audio
            processed_waveform = self._preprocess_audio(waveform, sample_rate)
            
            # Calculate audio duration
            audio_duration = len(processed_waveform) / self.target_sample_rate
            
            # Process với Wav2Vec2Processor
            inputs = self.processor(
                processed_waveform.numpy(),
                sampling_rate=self.target_sample_rate,
                return_tensors="pt",
                padding=True
            )
            
            # Inference với model
            with torch.no_grad():
                logits = self.model(inputs.input_values).logits
            
            # Decode predictions
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]
            
            processing_time = time.time() - start_time
            
            logger.debug(f"Transcription: '{transcription}' (duration: {audio_duration:.2f}s, processing: {processing_time:.2f}s)")
            
            return transcription
            
        except Exception as e:
            processing_time = time.time() - start_time 
            error_msg = f"Transcription failed: {e}"
            logger.error(f"❌ {error_msg} (processing time: {processing_time:.2f}s)")
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
            
            audio_duration = len(processed_waveform) / self.target_sample_rate
            
            # Process với processor
            inputs = self.processor(
                processed_waveform.numpy(),
                sampling_rate=self.target_sample_rate,
                return_tensors="pt",
                padding=True
            )
            
            # Model inference
            with torch.no_grad():
                logits = self.model(inputs.input_values).logits
            
            # Decode predictions
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]
            
            # Compute confidence score
            confidence_score = self._compute_confidence_score(logits[0])
            
            processing_time = time.time() - start_time
            real_time_factor = processing_time / audio_duration if audio_duration > 0 else 0.0
            
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
            
            return TranscriptionResult(
                text="",
                confidence_score=0.0,
                processing_time=processing_time,
                audio_duration=0.0,
                real_time_factor=0.0,
                sample_rate=sample_rate,
                success=False,
                error_message=str(e)
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

# Factory function để tạo instance dễ dàng
def create_vietnamese_asr(model_path: str = "./wav2vec2-base-vietnamese-250h") -> LocalWav2Vec2ASR:
    """
    Factory function để tạo LocalWav2Vec2ASR instance
    
    Args:
        model_path: Path tới model directory
        
    Returns:
        LocalWav2Vec2ASR instance đã load model
    """
    return LocalWav2Vec2ASR(model_path)

if __name__ == "__main__":
    # Example usage
    print("🚀 TESTING LocalWav2Vec2ASR - Prompt 2.1")
    print("=" * 60)
    
    try:
        # Tạo ASR instance
        asr = create_vietnamese_asr()
        
        # Show model info
        info = asr.get_model_info()
        print(f"📊 Model Info:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        print(f"\n✅ LocalWav2Vec2ASR ready for Prompt 2.2!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Make sure wav2vec2-base-vietnamese-250h folder exists with model files")