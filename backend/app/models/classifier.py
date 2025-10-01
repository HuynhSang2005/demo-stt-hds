#!/usr/bin/env python3
"""
Classifier Model Module - Backend Implementation
Vietnamese Text Classification with PhoBERT Model - FastAPI Backend

Migrated từ local_phobert_classifier.py với:
- Dependency injection pattern
- Integration với FastAPI configuration
- Structured logging
- Clean architecture compliance

Optimizations (Phase 1):
- Singleton pattern for model caching
- torch.inference_mode() for efficient inference
- Cached tokenizer/pipeline instances
- Thread-safe lazy loading
- Target: <50ms classification time
"""

import torch
import re
import time
import threading
from pathlib import Path
from typing import Dict, Optional, Union, List, Any
from dataclasses import dataclass
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Backend imports
from ..core.config import Settings
from ..core.logger import AudioProcessingLogger, AppLogger
from ..utils.toxic_keyword_detection import VietnameseToxicKeywordDetector

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
    
    Optimizations:
    - Singleton pattern: shared model instance
    - torch.inference_mode() for faster inference
    - Cached tokenizer and pipeline
    - Thread-safe operations
    """
    
    # Class-level cache for singleton pattern
    _instance: Optional['LocalPhoBERTClassifier'] = None
    _lock = threading.Lock()
    
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
        
        # Task 11: Configurable classification thresholds (lower = more sensitive)
        self.classification_thresholds = {
            "toxic": 0.55,      # Lower threshold for toxic detection
            "negative": 0.60,   # Slightly lower for negative
            "neutral": 0.50,    # Neutral default
            "positive": 0.60    # Normal positive threshold
        }
        
        # Task 11: Initialize keyword detector for ensemble
        self.keyword_detector = VietnameseToxicKeywordDetector(enable_fuzzy_matching=True)
        
        # Task 11: Ensemble weights (PhoBERT vs Keyword)
        self.ensemble_weights = {
            "model": 0.7,    # PhoBERT weight
            "keyword": 0.3   # Keyword detection weight
        }
        
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
                
                # Disable gradient computation for inference
                if self.model is not None:
                    for param in self.model.parameters():
                        param.requires_grad = False
            
            # Enable torch inference optimizations
            if hasattr(torch, 'set_float32_matmul_precision'):
                torch.set_float32_matmul_precision('high')
            
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
        
        # Return empty string for empty input - will be handled by caller
        if len(text.strip()) == 0:
            return ""
        
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
            # Handle empty text gracefully
            if not text or len(text.strip()) == 0:
                processing_time = time.time() - start_time
                return {
                    "text": text,
                    "label": "neutral",
                    "raw_label": "LABEL_2",
                    "confidence_score": 1.0,
                    "all_scores": {"neutral": 1.0, "positive": 0.0, "negative": 0.0, "toxic": 0.0},
                    "processing_time": processing_time,
                    "text_length": 0,
                    "warning": True,
                    "success": True,
                    "error_message": "Empty text provided"
                }
            
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
    
    def classify_ensemble(self, text: str) -> Dict[str, Any]:
        """
        Task 11: Ensemble classification combining PhoBERT + keyword detection
        
        This method combines model predictions with keyword-based detection
        for improved precision on toxic/negative content.
        
        Args:
            text: Vietnamese text to classify
            
        Returns:
            Classification result with ensemble scoring
        """
        if not self.is_loaded or self.classifier is None:
            raise ModelLoadError("Model chưa được load")
        
        self.audio_logger.log_classification_start(text_length=len(text))
        start_time = time.time()
        
        try:
            # Handle empty text gracefully
            if not text or len(text.strip()) == 0:
                processing_time = time.time() - start_time
                return {
                    "text": text,
                    "label": "neutral",
                    "raw_label": "LABEL_2",
                    "confidence_score": 1.0,
                    "all_scores": {"neutral": 1.0, "positive": 0.0, "negative": 0.0, "toxic": 0.0},
                    "processing_time": processing_time,
                    "text_length": 0,
                    "warning": True,
                    "success": True,
                    "error_message": "Empty text provided",
                    "ensemble_applied": False,
                    "keyword_matches": []
                }
            
            # Step 1: Get PhoBERT prediction
            model_result = self.classify(text)
            model_label = model_result["label"]
            model_confidence = model_result["confidence_score"]
            model_scores = model_result["all_scores"]
            
            # Step 2: Get keyword-based detection
            is_toxic_kw, toxicity_score, bad_keywords = self.keyword_detector.is_toxic(
                text, threshold=0.3  # Lower threshold for keyword detection
            )
            
            # Step 3: Ensemble logic
            final_label = model_label
            final_confidence = model_confidence
            ensemble_applied = False
            
            # If keywords indicate toxicity but model doesn't, boost toxic score
            if is_toxic_kw and model_label not in ["toxic", "negative"]:
                # Recalculate with keyword boost
                toxic_score = model_scores.get("toxic", 0.0)
                negative_score = model_scores.get("negative", 0.0)
                
                # Weighted ensemble
                boosted_toxic = (
                    toxic_score * self.ensemble_weights["model"] + 
                    toxicity_score * self.ensemble_weights["keyword"]
                )
                boosted_negative = (
                    negative_score * self.ensemble_weights["model"] + 
                    toxicity_score * 0.5 * self.ensemble_weights["keyword"]
                )
                
                # Check if boosted scores exceed threshold
                if boosted_toxic > self.classification_thresholds["toxic"]:
                    final_label = "toxic"
                    final_confidence = boosted_toxic
                    ensemble_applied = True
                elif boosted_negative > self.classification_thresholds["negative"]:
                    final_label = "negative"
                    final_confidence = boosted_negative
                    ensemble_applied = True
            
            # If model predicts toxic/negative, validate with keywords
            elif model_label in ["toxic", "negative"]:
                # If model says toxic but no keywords found, reduce confidence slightly
                if not is_toxic_kw and not bad_keywords:
                    final_confidence = model_confidence * 0.85  # 15% confidence penalty
            
            # Apply threshold filtering
            if final_confidence < self.classification_thresholds.get(final_label, 0.5):
                # Confidence too low, fallback to neutral
                final_label = "neutral"
                final_confidence = model_scores.get("neutral", 0.5)
            
            warning = final_label in self.warning_labels
            processing_time = time.time() - start_time
            
            # Log ensemble classification
            self.audio_logger.log_classification_success(
                text=text,
                label=final_label,
                confidence=final_confidence,
                warning=warning,
                processing_time=processing_time
            )
            
            return {
                "text": text,
                "label": final_label,
                "confidence_score": final_confidence,
                "all_scores": model_scores,
                "processing_time": processing_time,
                "text_length": len(text),
                "warning": warning,
                "success": True,
                "ensemble_applied": ensemble_applied,
                "keyword_toxicity_score": toxicity_score,
                "bad_keywords": bad_keywords,
                "model_label": model_label,  # Original model prediction
                "model_confidence": model_confidence
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Ensemble classification failed: {e}"
            
            self.audio_logger.log_classification_error(
                error=error_msg,
                processing_time=processing_time
            )
            
            raise TextProcessingError(error_msg) from e
    
    def classify_long_text(self, text: str, window_size: int = 400, overlap: int = 100) -> Dict[str, Any]:
        """
        Task 11: Sliding window classification for long texts (>512 tokens)
        
        Splits long text into overlapping windows and aggregates results.
        Uses "max severity" approach: if any window is toxic, entire text is toxic.
        
        Args:
            text: Long Vietnamese text
            window_size: Characters per window (default: 400 chars ≈ 100 tokens)
            overlap: Overlapping characters between windows
            
        Returns:
            Aggregated classification result
        """
        if not text or len(text.strip()) == 0:
            raise TextProcessingError("Text rỗng")
        
        text_length = len(text)
        
        # If text is short enough, use regular classification
        if text_length <= window_size:
            return self.classify_ensemble(text)
        
        start_time = time.time()
        self.audio_logger.log_classification_start(text_length=text_length)
        
        try:
            # Split text into windows
            windows = []
            step = window_size - overlap
            
            for i in range(0, text_length, step):
                window = text[i:i + window_size]
                if len(window.strip()) > 20:  # Skip very short windows
                    windows.append(window)
            
            if not windows:
                raise TextProcessingError("Không thể tạo windows từ text")
            
            # Classify each window
            window_results = []
            for window in windows:
                try:
                    result = self.classify_ensemble(window)
                    window_results.append(result)
                except Exception as e:
                    self.app_logger.logger.warning(
                        "classify_long_text_window_error",
                        window_length=len(window),
                        error=str(e)
                    )
                    continue
            
            if not window_results:
                raise TextProcessingError("Tất cả windows đều classify failed")
            
            # Aggregate results using "max severity" approach
            # Priority: toxic > negative > neutral > positive
            label_priority = {"toxic": 4, "negative": 3, "neutral": 2, "positive": 1}
            
            final_label = "neutral"
            final_confidence = 0.0
            max_priority = 0
            all_bad_keywords = set()
            max_toxicity_score = 0.0
            
            for result in window_results:
                label = result["label"]
                confidence = result["confidence_score"]
                priority = label_priority.get(label, 2)
                
                # Collect bad keywords
                if "bad_keywords" in result:
                    all_bad_keywords.update(result["bad_keywords"])
                
                # Track max toxicity score
                if "keyword_toxicity_score" in result:
                    max_toxicity_score = max(max_toxicity_score, result["keyword_toxicity_score"])
                
                # Update final prediction based on priority
                if priority > max_priority or (priority == max_priority and confidence > final_confidence):
                    final_label = label
                    final_confidence = confidence
                    max_priority = priority
            
            warning = final_label in self.warning_labels
            processing_time = time.time() - start_time
            
            # Log aggregated result
            self.audio_logger.log_classification_success(
                text=text[:100] + "..." if len(text) > 100 else text,
                label=final_label,
                confidence=final_confidence,
                warning=warning,
                processing_time=processing_time
            )
            
            return {
                "text": text,
                "label": final_label,
                "confidence_score": final_confidence,
                "processing_time": processing_time,
                "text_length": text_length,
                "warning": warning,
                "success": True,
                "num_windows": len(windows),
                "num_classified": len(window_results),
                "bad_keywords": list(all_bad_keywords),
                "max_toxicity_score": max_toxicity_score,
                "method": "sliding_window"
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Long text classification failed: {e}"
            
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

# Factory function với singleton pattern support
def create_classifier_model(
    settings: Settings, 
    logger: Optional[AudioProcessingLogger] = None,
    use_singleton: bool = True
) -> LocalPhoBERTClassifier:
    """
    Factory function để tạo LocalPhoBERTClassifier instance với singleton support
    
    Args:
        settings: Application settings
        logger: Optional structured logger
        use_singleton: If True, return cached instance (default: True for performance)
        
    Returns:
        LocalPhoBERTClassifier instance đã load model
        
    Note:
        Singleton pattern ensures model is loaded only once, reducing overhead
        from ~1-2s per request to <50ms amortized cost.
    """
    if use_singleton:
        with LocalPhoBERTClassifier._lock:
            if LocalPhoBERTClassifier._instance is None:
                LocalPhoBERTClassifier._instance = LocalPhoBERTClassifier(settings, logger)
            return LocalPhoBERTClassifier._instance
    else:
        return LocalPhoBERTClassifier(settings, logger)