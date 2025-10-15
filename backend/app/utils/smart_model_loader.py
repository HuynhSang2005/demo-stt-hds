#!/usr/bin/env python3
"""
Smart Model Loader - Intelligent Model Loading with ONNX/PyTorch Fallback
Automatically selects best performing model type (ONNX or PyTorch)
"""

import torch
import time
from pathlib import Path
from typing import Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass

# Backend imports
from ..core.config import Settings
from ..core.logger import AudioProcessingLogger, AppLogger
from .enhanced_onnx_optimizer import (
    EnhancedONNXOptimizer, 
    get_enhanced_onnx_optimizer,
    ONNXConversionError,
    ONNXLoadError,
    PerformanceMetrics
)

@dataclass
class ModelLoadResult:
    """Result of smart model loading"""
    model_type: str  # 'pytorch', 'onnx', or 'fallback'
    model: Any
    processor: Any = None
    performance_metrics: Optional[PerformanceMetrics] = None
    load_time: float = 0.0
    success: bool = False
    error_message: Optional[str] = None

class SmartModelLoader:
    """
    Smart model loader with automatic ONNX/PyTorch selection
    
    Features:
    - Auto-detect available model types
    - Performance-based model selection
    - Graceful fallback mechanisms
    - Caching and optimization
    """
    
    def __init__(self, settings: Settings, logger: Optional[AudioProcessingLogger] = None):
        self.settings = settings
        self.logger = logger or AudioProcessingLogger("smart_model_loader")
        self.app_logger = AppLogger("smart_model_loader_app")
        
        # Get enhanced ONNX optimizer
        self.onnx_optimizer = get_enhanced_onnx_optimizer(settings, logger)
        
        # Model loading cache
        self.loaded_models: Dict[str, ModelLoadResult] = {}
        
        # Configuration
        self.prefer_onnx = getattr(settings, 'PREFER_ONNX', True)
        self.auto_convert = getattr(settings, 'ONNX_AUTO_CONVERT', True)
        self.benchmark_models = getattr(settings, 'ONNX_BENCHMARK', True)
    
    def load_phowhisper_model(self, original_model_path: str) -> ModelLoadResult:
        """Load PhoWhisper model with smart ONNX/PyTorch selection"""
        model_name = "phowhisper"
        
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        start_time = time.time()
        
        try:
            self.logger.logger.info(
                "smart_phowhisper_load_start",
                original_path=original_model_path,
                prefer_onnx=self.prefer_onnx
            )
            
            # Strategy 1: Try ONNX first (if preferred)
            if self.prefer_onnx:
                result = self._try_load_onnx_phowhisper(model_name, original_model_path)
                if result.success:
                    result.load_time = time.time() - start_time
                    self.loaded_models[model_name] = result
                    return result
            
            # Strategy 2: Load PyTorch model
            result = self._load_pytorch_phowhisper(original_model_path)
            
            # Strategy 3: Convert to ONNX (if auto-convert enabled)
            if self.auto_convert and result.success:
                onnx_result = self._convert_and_load_onnx_phowhisper(
                    result.model, result.processor, model_name, original_model_path
                )
                if onnx_result.success:
                    # Benchmark and decide which is better
                    if self.benchmark_models:
                        onnx_result.performance_metrics = self._benchmark_phowhisper(
                            result.model, onnx_result.model, model_name
                        )
                        
                        # Use ONNX if it's significantly better
                        if (onnx_result.performance_metrics and 
                            onnx_result.performance_metrics.speedup > 1.2):
                            result = onnx_result
            
            result.load_time = time.time() - start_time
            self.loaded_models[model_name] = result
            
            self.logger.logger.info(
                "smart_phowhisper_load_complete",
                model_type=result.model_type,
                load_time=result.load_time,
                success=result.success
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Smart PhoWhisper loading failed: {e}"
            self.logger.logger.error(
                "smart_phowhisper_load_failed",
                error=error_msg,
                load_time=time.time() - start_time
            )
            
            return ModelLoadResult(
                model_type="error",
                model=None,
                success=False,
                error_message=error_msg,
                load_time=time.time() - start_time
            )
    
    def load_phobert_model(self, original_model_path: str) -> ModelLoadResult:
        """Load PhoBERT model with smart ONNX/PyTorch selection"""
        model_name = "phobert"
        
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        start_time = time.time()
        
        try:
            self.logger.logger.info(
                "smart_phobert_load_start",
                original_path=original_model_path,
                prefer_onnx=self.prefer_onnx
            )
            
            # Strategy 1: Try ONNX first (if preferred)
            if self.prefer_onnx:
                result = self._try_load_onnx_phobert(model_name, original_model_path)
                if result.success:
                    result.load_time = time.time() - start_time
                    self.loaded_models[model_name] = result
                    return result
            
            # Strategy 2: Load PyTorch model
            result = self._load_pytorch_phobert(original_model_path)
            
            # Strategy 3: Convert to ONNX (if auto-convert enabled)
            if self.auto_convert and result.success:
                onnx_result = self._convert_and_load_onnx_phobert(
                    result.model, result.processor, model_name, original_model_path
                )
                if onnx_result.success:
                    # Benchmark and decide which is better
                    if self.benchmark_models:
                        onnx_result.performance_metrics = self._benchmark_phobert(
                            result.model, onnx_result.model, model_name
                        )
                        
                        # Use ONNX if it's significantly better
                        if (onnx_result.performance_metrics and 
                            onnx_result.performance_metrics.speedup > 1.2):
                            result = onnx_result
            
            result.load_time = time.time() - start_time
            self.loaded_models[model_name] = result
            
            self.logger.logger.info(
                "smart_phobert_load_complete",
                model_type=result.model_type,
                load_time=result.load_time,
                success=result.success
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Smart PhoBERT loading failed: {e}"
            self.logger.logger.error(
                "smart_phobert_load_failed",
                error=error_msg,
                load_time=time.time() - start_time
            )
            
            return ModelLoadResult(
                model_type="error",
                model=None,
                success=False,
                error_message=error_msg,
                load_time=time.time() - start_time
            )
    
    def _try_load_onnx_phowhisper(self, model_name: str, original_model_path: str) -> ModelLoadResult:
        """Try to load existing ONNX PhoWhisper model"""
        try:
            if not self.onnx_optimizer.has_onnx_model(model_name):
                return ModelLoadResult(
                    model_type="pytorch",  # Will fallback to PyTorch
                    model=None,
                    success=False,
                    error_message="No ONNX model available"
                )
            
            # Load ONNX session
            onnx_session = self.onnx_optimizer.load_onnx_session(model_name)
            
            # Load processor from original model (still needed for preprocessing)
            from transformers import WhisperProcessor
            processor = WhisperProcessor.from_pretrained(
                original_model_path,
                local_files_only=True,
                use_auth_token=False
            )
            
            return ModelLoadResult(
                model_type="onnx",
                model=onnx_session,
                processor=processor,
                success=True
            )
            
        except Exception as e:
            return ModelLoadResult(
                model_type="pytorch",
                model=None,
                success=False,
                error_message=f"ONNX load failed: {e}"
            )
    
    def _try_load_onnx_phobert(self, model_name: str, original_model_path: str) -> ModelLoadResult:
        """Try to load existing ONNX PhoBERT model"""
        try:
            if not self.onnx_optimizer.has_onnx_model(model_name):
                return ModelLoadResult(
                    model_type="pytorch",
                    model=None,
                    success=False,
                    error_message="No ONNX model available"
                )
            
            # Load ONNX session
            onnx_session = self.onnx_optimizer.load_onnx_session(model_name)
            
            # Load tokenizer from original model (still needed for preprocessing)
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                original_model_path,
                local_files_only=True,
                use_auth_token=False
            )
            
            return ModelLoadResult(
                model_type="onnx",
                model=onnx_session,
                processor=tokenizer,
                success=True
            )
            
        except Exception as e:
            return ModelLoadResult(
                model_type="pytorch",
                model=None,
                success=False,
                error_message=f"ONNX load failed: {e}"
            )
    
    def _load_pytorch_phowhisper(self, model_path: str) -> ModelLoadResult:
        """Load PyTorch PhoWhisper model"""
        try:
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            
            processor = WhisperProcessor.from_pretrained(
                model_path,
                local_files_only=True,
                use_auth_token=False
            )
            
            model = WhisperForConditionalGeneration.from_pretrained(
                model_path,
                local_files_only=True,
                use_auth_token=False
            )
            
            model.eval()
            model = model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
            
            # Disable gradients for inference
            for param in model.parameters():
                param.requires_grad = False
            
            return ModelLoadResult(
                model_type="pytorch",
                model=model,
                processor=processor,
                success=True
            )
            
        except Exception as e:
            return ModelLoadResult(
                model_type="error",
                model=None,
                success=False,
                error_message=f"PyTorch load failed: {e}"
            )
    
    def _load_pytorch_phobert(self, model_path: str) -> ModelLoadResult:
        """Load PyTorch PhoBERT model"""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True,
                use_auth_token=False
            )
            
            model = AutoModelForSequenceClassification.from_pretrained(
                model_path,
                local_files_only=True,
                use_auth_token=False
            )
            
            model.eval()
            model = model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
            
            # Disable gradients for inference
            for param in model.parameters():
                param.requires_grad = False
            
            return ModelLoadResult(
                model_type="pytorch",
                model=model,
                processor=tokenizer,
                success=True
            )
            
        except Exception as e:
            return ModelLoadResult(
                model_type="error",
                model=None,
                success=False,
                error_message=f"PyTorch load failed: {e}"
            )
    
    def _convert_and_load_onnx_phowhisper(self, pytorch_model, processor, 
                                         model_name: str, original_model_path: str) -> ModelLoadResult:
        """Convert PyTorch PhoWhisper to ONNX and load"""
        try:
            # Convert to ONNX
            model_info = self.onnx_optimizer.convert_pytorch_to_onnx(
                pytorch_model, model_name, original_model_path
            )
            
            # Load ONNX session
            onnx_session = self.onnx_optimizer.load_onnx_session(model_name)
            
            return ModelLoadResult(
                model_type="onnx_converted",
                model=onnx_session,
                processor=processor,
                success=True
            )
            
        except Exception as e:
            return ModelLoadResult(
                model_type="pytorch",
                model=pytorch_model,
                processor=processor,
                success=True,  # Fallback to PyTorch
                error_message=f"ONNX conversion failed, using PyTorch: {e}"
            )
    
    def _convert_and_load_onnx_phobert(self, pytorch_model, tokenizer, 
                                      model_name: str, original_model_path: str) -> ModelLoadResult:
        """Convert PyTorch PhoBERT to ONNX and load"""
        try:
            # Convert to ONNX
            model_info = self.onnx_optimizer.convert_pytorch_to_onnx(
                pytorch_model, model_name, original_model_path
            )
            
            # Load ONNX session
            onnx_session = self.onnx_optimizer.load_onnx_session(model_name)
            
            return ModelLoadResult(
                model_type="onnx_converted",
                model=onnx_session,
                processor=tokenizer,
                success=True
            )
            
        except Exception as e:
            return ModelLoadResult(
                model_type="pytorch",
                model=pytorch_model,
                processor=tokenizer,
                success=True,  # Fallback to PyTorch
                error_message=f"ONNX conversion failed, using PyTorch: {e}"
            )
    
    def _benchmark_phowhisper(self, pytorch_model, onnx_model, model_name: str) -> Optional[PerformanceMetrics]:
        """Benchmark PhoWhisper models"""
        try:
            # Create dummy mel spectrogram input
            dummy_input = torch.randn(1, 80, 3000)
            
            return self.onnx_optimizer.benchmark_models(
                pytorch_model, model_name, dummy_input
            )
        except Exception as e:
            self.logger.logger.warning(
                "phowhisper_benchmark_failed",
                error=str(e)
            )
            return None
    
    def _benchmark_phobert(self, pytorch_model, onnx_model, model_name: str) -> Optional[PerformanceMetrics]:
        """Benchmark PhoBERT models"""
        try:
            # Create dummy tokenized input
            dummy_input = torch.randint(0, 30000, (1, 512), dtype=torch.long)
            
            return self.onnx_optimizer.benchmark_models(
                pytorch_model, model_name, dummy_input
            )
        except Exception as e:
            self.logger.logger.warning(
                "phobert_benchmark_failed",
                error=str(e)
            )
            return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all loaded models"""
        status = {
            "loaded_models": {},
            "onnx_available": {},
            "performance_metrics": {}
        }
        
        for model_name, result in self.loaded_models.items():
            status["loaded_models"][model_name] = {
                "type": result.model_type,
                "success": result.success,
                "load_time": result.load_time,
                "error": result.error_message
            }
        
        # Check ONNX availability
        for model_name in ["phowhisper", "phobert"]:
            status["onnx_available"][model_name] = self.onnx_optimizer.has_onnx_model(model_name)
        
        # Get performance metrics
        for model_name in ["phowhisper", "phobert"]:
            if model_name in self.onnx_optimizer.performance_cache:
                metrics = self.onnx_optimizer.performance_cache[model_name]
                status["performance_metrics"][model_name] = {
                    "speedup": metrics.speedup,
                    "pytorch_time_ms": metrics.pytorch_time_ms,
                    "onnx_time_ms": metrics.onnx_time_ms,
                    "recommendation": self.onnx_optimizer.get_model_recommendation(model_name)
                }
        
        return status

# Global smart model loader instance
_smart_model_loader: Optional[SmartModelLoader] = None

def get_smart_model_loader(settings: Optional[Settings] = None,
                          logger: Optional[AudioProcessingLogger] = None) -> SmartModelLoader:
    """Get smart model loader instance"""
    global _smart_model_loader
    
    if _smart_model_loader is None:
        _smart_model_loader = SmartModelLoader(settings or Settings(), logger)
    
    return _smart_model_loader
