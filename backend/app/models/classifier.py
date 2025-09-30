#!/usr/bin/env python3
"""
Classifier Model Module - Backend Implementation
Vietnamese Text Classification with PhoBERT Model - FastAPI Backend

Migrated từ local_phobert_classifier.py với:
- Dependency injection pattern
- Integration với FastAPI configuration
- Structured logging
- Clean architecture compliance
"""

import torch
import re
import time
from pathlib import Path
from typing import Dict, Optional, Union, List, Any
from dataclasses import dataclass
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Backend imports
from ..core.config import Settings
from ..core.logger import AudioProcessingLogger, AppLogger

@dataclass
class ClassificationResult:
    """Kết quả classification với metadata"""
    text: str
    label: str  # positive, negative, neutral, toxic
    raw_label: str  # LABEL_0, LABEL_1, etc.
    confidence_score: float
    all_scores: Dict[str, float]  # All class probabilities
    processing_time: float
    text_length: int
    warning: bool  # True if toxic or negative
    success: bool
    error_message: Optional[str] = None

class LocalPhoBERTClassifierError(Exception):
    """Base exception cho LocalPhoBERTClassifier"""
    pass

class ModelLoadError(LocalPhoBERTClassifierError):
    """Lỗi khi load model"""
    pass

class TextProcessingError(LocalPhoBERTClassifierError):
    """Lỗi khi xử lý text"""
    pass

class LocalPhoBERTClassifier:
    """
    Offline Vietnamese Text Classification sử dụng PhoBERT model từ local path
    Backend version với dependency injection và structured logging
    
    Features:
    - Offline-first với local_files_only=True
    - Label mapping: LABEL_0→positive, LABEL_1→negative, LABEL_2→neutral, LABEL_3→toxic
    - Text preprocessing cho Vietnamese
    - Confidence scoring và warning detection
    - Structured logging integration
    - Configuration-driven paths
    """
    
    def __init__(self, settings: Settings, logger: Optional[AudioProcessingLogger] = None):
        """
        Initialize LocalPhoBERTClassifier với dependency injection
        
        Args:
            settings: Application settings với model paths
            logger: Structured logger instance
        """
        self.settings = settings
        self.audio_logger = logger or AudioProcessingLogger("classifier_model")
        self.app_logger = AppLogger("classifier_app")
        
        # Get model path from settings; prefer resolved path from Settings.get_model_paths()
        try:
            resolved = settings.get_model_paths().get("classifier")
            if resolved:
                self.model_path = Path(resolved)
            else:
                self.model_path = Path(settings.CLASSIFIER_MODEL_PATH)
        except Exception:
            self.model_path = Path(settings.CLASSIFIER_MODEL_PATH)
        
        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.classifier: Optional[Any] = None
        self.is_loaded = False
        
        # Determine device for optimal performance
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device_id = 0 if torch.cuda.is_available() else -1  # GPU:0 or CPU:-1 for pipeline
        
        # Label mapping từ research đã confirm
        self.label_mapping = {
            "LABEL_0": "positive",
            "LABEL_1": "negative", 
            "LABEL_2": "neutral",
            "LABEL_3": "toxic"
        }
        
        # Warning labels 
        self.warning_labels = {"negative", "toxic"}
        
        # Load model during initialization
        self._load_model()
    
    def _load_model(self) -> None:
        """Load PhoBERT model và tokenizer từ local path với structured logging"""
        load_start_time = time.time()
        
        try:
            self.app_logger.log_model_loading_start(
                model_type="phobert_classifier",
                model_path=str(self.model_path)
            )
            
            # Kiểm tra model path tồn tại
            if not self.model_path.exists():
                raise ModelLoadError(f"Model path không tồn tại: {self.model_path}")
            
            # Kiểm tra các file cần thiết
            required_files = ["config.json", "vocab.txt", "bpe.codes"]
            for file_name in required_files:
                if not (self.model_path / file_name).exists():
                    raise ModelLoadError(f"Thiếu file cần thiết: {file_name}")
            
            # Load tokenizer với local_files_only=True (Auto classes để handle PhoBERT)
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                use_auth_token=False
            )
            
            # Load model với local_files_only=True
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                use_auth_token=False
            )
            
            # Tạo classifier pipeline with optimal device
            self.classifier = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                return_all_scores=True,  # Trả về all class scores
                device=self.device_id  # Use GPU if available, else CPU
            )
            
            # Set model to eval mode and move to device
            if self.model is not None:
                self.model.eval()
                self.model = self.model.to(self.device)
            
            self.is_loaded = True
            
            # Calculate model parameters
            num_params = sum(p.numel() for p in self.model.parameters()) if self.model else 0
            loading_time = time.time() - load_start_time
            
            # Log successful loading
            self.app_logger.log_model_loading_success(
                model_type="phobert_classifier",
                loading_time=loading_time,
                model_params=num_params
            )
            
        except Exception as e:
            self.is_loaded = False
            loading_time = time.time() - load_start_time
            error_msg = f"Failed to load PhoBERT model: {e}"
            
            self.app_logger.log_model_loading_error(
                model_type="phobert_classifier",
                error=error_msg,
                loading_time=loading_time
            )
            
            raise ModelLoadError(error_msg) from e
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess Vietnamese text cho PhoBERT
        
        Args:
            text: Input text cần classify
            
        Returns:
            Cleaned và preprocessed text
        """
        if not isinstance(text, str):
            raise TextProcessingError("Input phải là string")
        
        if len(text.strip()) == 0:
            raise TextProcessingError("Text không được rỗng")
        
        # Original text for reference
        original_length = len(text)
        
        try:
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove special characters but keep Vietnamese diacritics
            # Keep basic punctuation: . , ! ? : ; - ( ) 
            text = re.sub(r'[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ.,!?:;()\-]', ' ', text)
            
            # Remove excessive punctuation
            text = re.sub(r'[.,!?:;]{2,}', '.', text)
            
            # Fix spacing around punctuation
            text = re.sub(r'\s*([.,!?:;])\s*', r'\1 ', text)
            
            # Final cleanup
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Check length after preprocessing
            if len(text) == 0:
                raise TextProcessingError("Text trống sau khi preprocess")
                
            # Check if text too long (PhoBERT max length ~512 tokens)
            if len(text) > 2000:  # Conservative limit
                self.audio_logger.logger.warning(
                    "long_text_warning",
                    text_length=len(text),
                    max_length=2000
                )
                text = text[:2000] + "..."
            
            self.audio_logger.logger.debug(
                "text_preprocessing",
                original_length=original_length,
                processed_length=len(text)
            )
            
            return text
            
        except Exception as e:
            raise TextProcessingError(f"Text preprocessing failed: {e}") from e
    
    def _validate_input(self, text: str) -> None:
        """Validate input text"""
        if not isinstance(text, str):
            raise TextProcessingError("Input phải là string")
            
        if len(text.strip()) == 0:
            raise TextProcessingError("Text không được rỗng")
            
        # Check for very long text
        if len(text) > 10000:
            raise TextProcessingError("Text quá dài (> 10,000 chars)")
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify Vietnamese text
        
        Args:
            text: Vietnamese text cần classify
            
        Returns:
            Dictionary với classification result
            
        Raises:
            ModelLoadError: Nếu model chưa được load
            TextProcessingError: Nếu có lỗi xử lý text
        """
        if not self.is_loaded or self.classifier is None:
            raise ModelLoadError("Model chưa được load. Gọi _load_model() trước.")
        
        self.audio_logger.log_classification_start(text_length=len(text))
        
        start_time = time.time()
        
        try:
            # Validate input
            self._validate_input(text)
            
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Classify với pipeline
            results = self.classifier(processed_text)
            
            # Parse results
            all_scores = {}
            max_score = 0.0
            predicted_raw_label = "LABEL_0"
            
            for result in results[0]:  # results is list of list
                label = result['label']
                score = result['score']
                
                # Map to semantic label
                semantic_label = self.label_mapping.get(label, label)
                all_scores[semantic_label] = score
                
                # Find max score
                if score > max_score:
                    max_score = score
                    predicted_raw_label = label
            
            # Get final predictions
            predicted_label = self.label_mapping.get(predicted_raw_label, predicted_raw_label)
            confidence_score = max_score
            warning = predicted_label in self.warning_labels
            
            processing_time = time.time() - start_time
            
            # Log successful classification
            self.audio_logger.log_classification_success(
                text=text,
                label=predicted_label,
                confidence=confidence_score,
                warning=warning,
                processing_time=processing_time
            )
            
            return {
                "text": text,
                "label": predicted_label,
                "raw_label": predicted_raw_label,
                "confidence_score": confidence_score,
                "all_scores": all_scores,
                "processing_time": processing_time,
                "text_length": len(text),
                "warning": warning,
                "success": True
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Classification failed: {e}"
            
            self.audio_logger.log_classification_error(
                error=error_msg,
                processing_time=processing_time
            )
            
            raise TextProcessingError(error_msg) from e
    
    def classify_with_metadata(self, text: str) -> ClassificationResult:
        """
        Classify với metadata đầy đủ
        
        Args:
            text: Vietnamese text cần classify
            
        Returns:
            ClassificationResult với text và metadata
        """
        if not self.is_loaded or self.classifier is None:
            return ClassificationResult(
                text=text,
                label="neutral",
                raw_label="LABEL_2",
                confidence_score=0.0,
                all_scores={},
                processing_time=0.0,
                text_length=len(text),
                warning=False,
                success=False,
                error_message="Model chưa được load"
            )
        
        self.audio_logger.log_classification_start(text_length=len(text))
        
        start_time = time.time()
        
        try:
            # Validate và preprocess
            self._validate_input(text)
            processed_text = self._preprocess_text(text)
            
            # Classify
            results = self.classifier(processed_text)
            
            # Parse results
            all_scores = {}
            max_score = 0.0
            predicted_raw_label = "LABEL_0"
            
            for result in results[0]:
                label = result['label']
                score = result['score']
                
                semantic_label = self.label_mapping.get(label, label)
                all_scores[semantic_label] = score
                
                if score > max_score:
                    max_score = score
                    predicted_raw_label = label
            
            predicted_label = self.label_mapping.get(predicted_raw_label, predicted_raw_label)
            warning = predicted_label in self.warning_labels
            processing_time = time.time() - start_time
            
            # Log successful classification
            self.audio_logger.log_classification_success(
                text=text,
                label=predicted_label,
                confidence=max_score,
                warning=warning,
                processing_time=processing_time
            )
            
            return ClassificationResult(
                text=text,
                label=predicted_label,
                raw_label=predicted_raw_label,
                confidence_score=max_score,
                all_scores=all_scores,
                processing_time=processing_time,
                text_length=len(text),
                warning=warning,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            self.audio_logger.log_classification_error(
                error=error_msg,
                processing_time=processing_time
            )
            
            return ClassificationResult(
                text=text,
                label="neutral",
                raw_label="LABEL_2",
                confidence_score=0.0,
                all_scores={},
                processing_time=processing_time,
                text_length=len(text),
                warning=False,
                success=False,
                error_message=error_msg
            )
    
    def batch_classify(self, texts: List[str]) -> List[ClassificationResult]:
        """
        Classify multiple texts
        
        Args:
            texts: List of Vietnamese texts
            
        Returns:
            List of ClassificationResult
        """
        results = []
        
        for text in texts:
            try:
                result = self.classify_with_metadata(text)
                results.append(result)
            except Exception as e:
                self.audio_logger.logger.error(
                    "batch_classify_error",
                    text_snippet=text[:50] + "..." if len(text) > 50 else text,
                    error=str(e)
                )
                error_result = ClassificationResult(
                    text=text,
                    label="neutral",
                    raw_label="LABEL_2",
                    confidence_score=0.0,
                    all_scores={},
                    processing_time=0.0,
                    text_length=len(text),
                    warning=False,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin về model
        
        Returns:
            Dictionary chứa thông tin model
        """
        if not self.is_loaded:
            return {"loaded": False, "error": "Model chưa được load"}
        
        # Safe access to model info
        model_params = 0
        vocab_size = 0
        model_class = "Unknown"
        
        if self.model is not None:
            model_class = self.model.__class__.__name__
            try:
                model_params = sum(p.numel() for p in self.model.parameters())
            except Exception:
                model_params = 0
        
        if self.tokenizer is not None:
            try:
                vocab_attr = getattr(self.tokenizer, 'vocab', None)
                if vocab_attr is not None:
                    vocab_size = len(vocab_attr)
                else:
                    vocab_size = 0
            except Exception:
                vocab_size = 0
        
        return {
            "loaded": True,
            "model_path": str(self.model_path),
            "model_class": model_class,
            "model_parameters": model_params,
            "vocab_size": vocab_size,
            "label_mapping": self.label_mapping,
            "warning_labels": list(self.warning_labels),
            "max_length": getattr(self.tokenizer, 'model_max_length', 512) if self.tokenizer else 512
        }

# Factory function để tạo instance với dependency injection
def create_classifier_model(settings: Settings, logger: Optional[AudioProcessingLogger] = None) -> LocalPhoBERTClassifier:
    """
    Factory function để tạo LocalPhoBERTClassifier instance với dependency injection
    
    Args:
        settings: Application settings
        logger: Optional structured logger
        
    Returns:
        LocalPhoBERTClassifier instance đã load model
    """
    return LocalPhoBERTClassifier(settings, logger)