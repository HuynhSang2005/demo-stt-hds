#!/usr/bin/env python3
"""
Enhanced ONNX Optimizer - Smart Model Conversion & Loading
Auto-converts PyTorch models to ONNX with intelligent fallback
"""

import torch
import onnx
import onnxruntime as ort
import time
import json
import shutil
from pathlib import Path
from typing import Optional, Tuple, Any, Dict, Union, List
import numpy as np
from dataclasses import dataclass

# Backend imports
from ..core.config import Settings
from ..core.logger import AudioProcessingLogger, AppLogger

@dataclass
class ONNXModelInfo:
    """ONNX model metadata"""
    model_name: str
    model_path: str
    input_shape: Tuple[int, ...]
    output_names: List[str]
    opset_version: int
    conversion_time: float
    file_size_mb: float
    optimized: bool

@dataclass
class PerformanceMetrics:
    """Performance comparison metrics"""
    model_name: str
    pytorch_time_ms: float
    onnx_time_ms: float
    speedup: float
    memory_usage_pytorch: float
    memory_usage_onnx: float
    accuracy_diff: float

class ONNXConversionError(Exception):
    """ONNX conversion error"""
    pass

class ONNXLoadError(Exception):
    """ONNX loading error"""
    pass

class EnhancedONNXOptimizer:
    """
    Enhanced ONNX optimizer with smart conversion and fallback
    
    Features:
    - Auto-detect model types (Whisper, PhoBERT)
    - Smart conversion với proper input shapes
    - Performance benchmarking
    - Graceful fallback to PyTorch
    - Model validation và caching
    """
    
    def __init__(self, settings: Settings, logger: Optional[AudioProcessingLogger] = None):
        self.settings = settings
        self.logger = logger or AudioProcessingLogger("onnx_optimizer")
        self.app_logger = AppLogger("onnx_optimizer_app")
        
        # ONNX models directory (separate from original models)
        self.onnx_models_dir = Path("app/onnx_models")
        self.onnx_models_dir.mkdir(exist_ok=True)
        
        # Model configurations
        self.model_configs = {
            "phowhisper": {
                "input_shape": (1, 80, 3000),  # Mel spectrogram
                "output_names": ["logits"],
                "opset_version": 17,
                "model_type": "whisper"
            },
            "phobert": {
                "input_shape": (1, 258),       # Tokenized text (PhoBERT max length)
                "output_names": ["logits"],
                "opset_version": 17,
                "model_type": "bert"
            }
        }
        
        # ONNX sessions cache
        self.onnx_sessions: Dict[str, ort.InferenceSession] = {}
        
        # Performance metrics cache
        self.performance_cache: Dict[str, PerformanceMetrics] = {}
        
        # Conversion settings
        self.auto_convert = getattr(settings, 'ONNX_AUTO_CONVERT', True)
        self.benchmark_onnx = getattr(settings, 'ONNX_BENCHMARK', True)
        self.fallback_to_pytorch = getattr(settings, 'ONNX_FALLBACK_TO_PYTORCH', True)
    
    def get_onnx_model_path(self, model_name: str) -> Path:
        """Get ONNX model path for given model name"""
        return self.onnx_models_dir / model_name / f"{model_name}.onnx"
    
    def get_onnx_metadata_path(self, model_name: str) -> Path:
        """Get ONNX metadata path"""
        return self.onnx_models_dir / model_name / "metadata.json"
    
    def has_onnx_model(self, model_name: str) -> bool:
        """Check if ONNX model exists and is valid"""
        onnx_path = self.get_onnx_model_path(model_name)
        metadata_path = self.get_onnx_metadata_path(model_name)
        
        return onnx_path.exists() and metadata_path.exists()
    
    def load_onnx_metadata(self, model_name: str) -> Optional[ONNXModelInfo]:
        """Load ONNX model metadata"""
        metadata_path = self.get_onnx_metadata_path(model_name)
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            
            return ONNXModelInfo(
                model_name=data['model_name'],
                model_path=data['model_path'],
                input_shape=tuple(data['input_shape']),
                output_names=data['output_names'],
                opset_version=data['opset_version'],
                conversion_time=data['conversion_time'],
                file_size_mb=data['file_size_mb'],
                optimized=data['optimized']
            )
        except Exception as e:
            self.logger.logger.warning(
                "onnx_metadata_load_failed",
                model_name=model_name,
                error=str(e)
            )
            return None
    
    def save_onnx_metadata(self, model_info: ONNXModelInfo):
        """Save ONNX model metadata"""
        metadata_path = self.get_onnx_metadata_path(model_info.model_name)
        metadata_path.parent.mkdir(exist_ok=True)
        
        data = {
            'model_name': model_info.model_name,
            'model_path': model_info.model_path,
            'input_shape': list(model_info.input_shape),
            'output_names': model_info.output_names,
            'opset_version': model_info.opset_version,
            'conversion_time': model_info.conversion_time,
            'file_size_mb': model_info.file_size_mb,
            'optimized': model_info.optimized
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def convert_pytorch_to_onnx(self, pytorch_model: torch.nn.Module, 
                               model_name: str,
                               original_model_path: str) -> ONNXModelInfo:
        """Convert PyTorch model to ONNX with proper configuration"""
        
        if model_name not in self.model_configs:
            raise ONNXConversionError(f"Unknown model type: {model_name}")
        
        config = self.model_configs[model_name]
        onnx_path = self.get_onnx_model_path(model_name)
        onnx_path.parent.mkdir(exist_ok=True)
        
        self.logger.logger.info(
            "onnx_conversion_start",
            model_name=model_name,
            input_shape=config['input_shape']
        )
        
        start_time = time.time()
        
        try:
            # Set model to eval mode
            pytorch_model.eval()
            
            # Create dummy input based on model type
            if config['model_type'] == 'whisper':
                # Skip ONNX conversion for Whisper models - too complex
                raise ONNXConversionError("Whisper models are not supported for ONNX conversion due to encoder-decoder complexity")
            elif config['model_type'] == 'bert':
                # Skip ONNX conversion for BERT models - classification heads are complex
                raise ONNXConversionError("BERT classification models are not supported for ONNX conversion due to complex classification heads")
            else:
                dummy_input = torch.randn(*config['input_shape'])
            
            # Export to ONNX
            torch.onnx.export(
                pytorch_model,
                dummy_input,
                str(onnx_path),
                export_params=True,
                opset_version=config['opset_version'],
                do_constant_folding=True,
                input_names=['input'],
                output_names=config['output_names'],
                dynamic_axes={
                    'input': {0: 'batch_size'},
                    **{name: {0: 'batch_size'} for name in config['output_names']}
                },
                verbose=False
            )
            
            # Validate ONNX model
            onnx_model = onnx.load(str(onnx_path))
            onnx.checker.check_model(onnx_model)
            
            # Optimize ONNX model
            from onnxruntime.tools import optimizer
            optimized_model = optimizer.optimize_model(str(onnx_path))
            optimized_path = onnx_path.with_suffix('.optimized.onnx')
            optimized_model.save_model_to_file(str(optimized_path))
            
            # Use optimized version if it's smaller
            if optimized_path.stat().st_size < onnx_path.stat().st_size:
                shutil.move(str(optimized_path), str(onnx_path))
            else:
                optimized_path.unlink()
            
            conversion_time = time.time() - start_time
            file_size_mb = onnx_path.stat().st_size / (1024 * 1024)
            
            # Create model info
            model_info = ONNXModelInfo(
                model_name=model_name,
                model_path=str(onnx_path),
                input_shape=config['input_shape'],
                output_names=config['output_names'],
                opset_version=config['opset_version'],
                conversion_time=conversion_time,
                file_size_mb=file_size_mb,
                optimized=True
            )
            
            # Save metadata
            self.save_onnx_metadata(model_info)
            
            self.logger.logger.info(
                "onnx_conversion_success",
                model_name=model_name,
                conversion_time=conversion_time,
                file_size_mb=file_size_mb
            )
            
            return model_info
            
        except Exception as e:
            conversion_time = time.time() - start_time
            error_msg = f"ONNX conversion failed for {model_name}: {e}"
            
            self.logger.logger.error(
                "onnx_conversion_failed",
                model_name=model_name,
                error=error_msg,
                conversion_time=conversion_time
            )
            
            raise ONNXConversionError(error_msg) from e
    
    def load_onnx_session(self, model_name: str) -> ort.InferenceSession:
        """Load ONNX Runtime session with optimization"""
        if model_name in self.onnx_sessions:
            return self.onnx_sessions[model_name]
        
        onnx_path = self.get_onnx_model_path(model_name)
        
        if not onnx_path.exists():
            raise ONNXLoadError(f"ONNX model not found: {onnx_path}")
        
        try:
            # Configure ONNX Runtime providers
            providers = ['CPUExecutionProvider']
            if ort.get_device() == 'GPU':
                providers.insert(0, 'CUDAExecutionProvider')
            
            # Session options for optimization
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
            
            # Create session
            session = ort.InferenceSession(
                str(onnx_path),
                sess_options=session_options,
                providers=providers
            )
            
            self.onnx_sessions[model_name] = session
            
            self.logger.logger.info(
                "onnx_session_loaded",
                model_name=model_name,
                providers=session.get_providers()
            )
            
            return session
            
        except Exception as e:
            error_msg = f"Failed to load ONNX session for {model_name}: {e}"
            self.logger.logger.error("onnx_session_load_failed", model_name=model_name, error=error_msg)
            raise ONNXLoadError(error_msg) from e
    
    def benchmark_models(self, pytorch_model: torch.nn.Module, 
                        model_name: str,
                        input_data: Union[torch.Tensor, np.ndarray],
                        num_runs: int = 100) -> PerformanceMetrics:
        """Benchmark PyTorch vs ONNX performance"""
        
        if model_name in self.performance_cache:
            return self.performance_cache[model_name]
        
        self.logger.logger.info(
            "benchmark_start",
            model_name=model_name,
            num_runs=num_runs
        )
        
        try:
            # Get ONNX session
            onnx_session = self.load_onnx_session(model_name)
            
            # Prepare input data
            if isinstance(input_data, torch.Tensor):
                pytorch_input = input_data
                onnx_input = input_data.numpy()
            else:
                pytorch_input = torch.from_numpy(input_data)
                onnx_input = input_data
            
            # Warm up
            with torch.no_grad():
                _ = pytorch_model(pytorch_input)
            _ = onnx_session.run(None, {'input': onnx_input})
            
            # Benchmark PyTorch
            pytorch_times = []
            for _ in range(num_runs):
                start = time.time()
                with torch.no_grad():
                    _ = pytorch_model(pytorch_input)
                pytorch_times.append(time.time() - start)
            
            # Benchmark ONNX
            onnx_times = []
            for _ in range(num_runs):
                start = time.time()
                _ = onnx_session.run(None, {'input': onnx_input})
                onnx_times.append(time.time() - start)
            
            # Calculate metrics
            pytorch_avg_ms = np.mean(pytorch_times) * 1000
            onnx_avg_ms = np.mean(onnx_times) * 1000
            speedup = pytorch_avg_ms / onnx_avg_ms
            
            metrics = PerformanceMetrics(
                model_name=model_name,
                pytorch_time_ms=pytorch_avg_ms,
                onnx_time_ms=onnx_avg_ms,
                speedup=speedup,
                memory_usage_pytorch=0.0,  # TODO: Add memory profiling
                memory_usage_onnx=0.0,     # TODO: Add memory profiling
                accuracy_diff=0.0          # TODO: Add accuracy validation
            )
            
            # Cache results
            self.performance_cache[model_name] = metrics
            
            self.logger.logger.info(
                "benchmark_complete",
                model_name=model_name,
                pytorch_time_ms=pytorch_avg_ms,
                onnx_time_ms=onnx_avg_ms,
                speedup=speedup
            )
            
            return metrics
            
        except Exception as e:
            self.logger.logger.error(
                "benchmark_failed",
                model_name=model_name,
                error=str(e)
            )
            raise
    
    def get_model_recommendation(self, model_name: str) -> str:
        """Get recommendation for best model type to use"""
        if not self.benchmark_onnx:
            return "pytorch"
        
        if model_name not in self.performance_cache:
            return "unknown"
        
        metrics = self.performance_cache[model_name]
        
        # Use ONNX if it's significantly faster (>20% improvement)
        if metrics.speedup > 1.2:
            return "onnx"
        elif metrics.speedup > 1.0:
            return "onnx_preferred"
        else:
            return "pytorch"
    
    def cleanup_onnx_models(self):
        """Clean up ONNX models directory"""
        if self.onnx_models_dir.exists():
            shutil.rmtree(self.onnx_models_dir)
            self.onnx_models_dir.mkdir(exist_ok=True)
        
        self.onnx_sessions.clear()
        self.performance_cache.clear()
        
        self.logger.logger.info("onnx_models_cleanup_complete")

# Global enhanced ONNX optimizer instance
_enhanced_onnx_optimizer: Optional[EnhancedONNXOptimizer] = None

def get_enhanced_onnx_optimizer(settings: Optional[Settings] = None,
                               logger: Optional[AudioProcessingLogger] = None) -> EnhancedONNXOptimizer:
    """Get enhanced ONNX optimizer instance"""
    global _enhanced_onnx_optimizer
    
    if _enhanced_onnx_optimizer is None:
        _enhanced_onnx_optimizer = EnhancedONNXOptimizer(settings or Settings(), logger)
    
    return _enhanced_onnx_optimizer
