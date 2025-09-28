#!/usr/bin/env python3
"""
LocalPhoBERTClassifier - Prompt 2.2 Implementation
Offline Vietnamese Text Classification with PhoBERT Model

Clean Architecture implementation with:
- Load PhoBERT model từ local path  
- Phương thức classify(text: str) -> dict
- Map LABEL_0/1/2/3 to positive/negative/neutral/toxic
- Text preprocessing và confidence scoring
"""

import torch
import re
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Union, List, Any
from dataclasses import dataclass
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    Features:
    - Offline-first với local_files_only=True
    - Label mapping: LABEL_0→positive, LABEL_1→negative, LABEL_2→neutral, LABEL_3→toxic
    - Text preprocessing cho Vietnamese
    - Confidence scoring và warning detection
    - Clean architecture với error handling
    """
    
    def __init__(self, model_path: str = "./phobert-vi-comment-4class"):
        """
        Initialize LocalPhoBERTClassifier
        
        Args:
            model_path: Path tới folder chứa PhoBERT model và tokenizer
        """
        self.model_path = Path(model_path)
        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.classifier: Optional[Any] = None
        self.is_loaded = False
        
        # Label mapping từ research đã confirm
        self.label_mapping = {
            "LABEL_0": "positive",
            "LABEL_1": "negative", 
            "LABEL_2": "neutral",
            "LABEL_3": "toxic"
        }
        
        # Warning labels 
        self.warning_labels = {"negative", "toxic"}
        
        # Load model ngay khi khởi tạo
        self._load_model()
    
    def _load_model(self) -> None:
        """Load PhoBERT model và tokenizer từ local path"""
        try:
            logger.info(f"🔄 Loading PhoBERT model từ {self.model_path}")
            
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
            
            # Tạo classifier pipeline
            self.classifier = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                return_all_scores=True,  # Trả về all class scores
                device=-1  # CPU only for consistency
            )
            
            # Set model to eval mode
            if self.model is not None:
                self.model.eval()
            
            self.is_loaded = True
            
            # Log model info
            num_params = sum(p.numel() for p in self.model.parameters()) if self.model else 0
            vocab_size = 0
            if self.tokenizer and hasattr(self.tokenizer, 'vocab'):
                vocab_size = len(getattr(self.tokenizer, 'vocab', {}))
            
            logger.info(f"✅ PhoBERT model loaded successfully!")
            logger.info(f"   - Model parameters: {num_params:,}")
            logger.info(f"   - Vocab size: {vocab_size:,}")
            logger.info(f"   - Labels: {list(self.label_mapping.values())}")
            logger.info(f"   - Warning labels: {self.warning_labels}")
            
        except Exception as e:
            self.is_loaded = False
            error_msg = f"Failed to load PhoBERT model: {e}"
            logger.error(f"❌ {error_msg}")
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
                logger.warning(f"⚠️ Text dài {len(text)} chars, có thể bị truncate")
                text = text[:2000] + "..."
            
            logger.debug(f"Preprocessing: {original_length} → {len(text)} chars")
            
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
            
            logger.debug(f"Classification: '{text[:50]}...' → {predicted_label} ({confidence_score:.3f})")
            
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
            logger.error(f"❌ {error_msg} (processing time: {processing_time:.2f}s)")
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
                error_message=str(e)
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
                logger.error(f"❌ Batch classify failed for text: {text[:50]}...")
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

# Factory function để tạo instance dễ dàng
def create_vietnamese_classifier(model_path: str = "./phobert-vi-comment-4class") -> LocalPhoBERTClassifier:
    """
    Factory function để tạo LocalPhoBERTClassifier instance
    
    Args:
        model_path: Path tới model directory
        
    Returns:
        LocalPhoBERTClassifier instance đã load model
    """
    return LocalPhoBERTClassifier(model_path)

if __name__ == "__main__":
    # Example usage
    print("🚀 TESTING LocalPhoBERTClassifier - Prompt 2.2")
    print("=" * 60)
    
    try:
        # Tạo classifier instance
        classifier = create_vietnamese_classifier()
        
        # Show model info
        info = classifier.get_model_info()
        print(f"📊 Model Info:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # Test với sample texts
        test_texts = [
            "Tôi rất hài lòng với sản phẩm này!",  # positive
            "Sản phẩm này tệ quá, tôi không thích",  # negative  
            "Hôm nay trời đẹp",  # neutral
            "Mày là thằng ngu, tao ghét mày"  # toxic
        ]
        
        print(f"\n🧪 Testing với {len(test_texts)} sample texts:")
        
        for i, text in enumerate(test_texts, 1):
            result = classifier.classify_with_metadata(text)
            warning_icon = "🚨" if result.warning else "✅"
            print(f"   {i}. {warning_icon} '{text}' → {result.label} ({result.confidence_score:.3f})")
        
        print(f"\n✅ LocalPhoBERTClassifier ready for integration!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Make sure phobert-vi-comment-4class folder exists with model files")