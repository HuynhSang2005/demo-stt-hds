#!/usr/bin/env python3
"""
ONNX Optimization Utilities
Convert PyTorch models to ONNX for faster inference
"""

import torch
import onnx
import onnxruntime as ort
from pathlib import Path
from typing import Optional, Tuple, Any, Dict
import numpy as np
import time

class ONNXModelOptimizer:
    """Optimize models using ONNX Runtime"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.onnx_sessions: Dict[str, ort.InferenceSession] = {}
    
    def convert_to_onnx(self, pytorch_model: torch.nn.Module, 
                       model_name: str, 
                       input_shape: Tuple[int, ...],
                       opset_version: int = 11) -> str:
        """Convert PyTorch model to ONNX"""
        
        onnx_path = self.model_dir / f"{model_name}.onnx"
        
        if onnx_path.exists():
            print(f"ONNX model already exists: {onnx_path}")
            return str(onnx_path)
        
        print(f"Converting {model_name} to ONNX...")
        
        # Create dummy input
        dummy_input = torch.randn(1, *input_shape)
        
        # Set model to eval mode
        pytorch_model.eval()
        
        # Export to ONNX
        torch.onnx.export(
            pytorch_model,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=opset_version,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        
        print(f"ONNX model saved to: {onnx_path}")
        return str(onnx_path)
    
    def load_onnx_session(self, model_name: str) -> ort.InferenceSession:
        """Load ONNX Runtime session"""
        if model_name in self.onnx_sessions:
            return self.onnx_sessions[model_name]
        
        onnx_path = self.model_dir / f"{model_name}.onnx"
        if not onnx_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {onnx_path}")
        
        # Create ONNX Runtime session
        session = ort.InferenceSession(str(onnx_path))
        self.onnx_sessions[model_name] = session
        
        print(f"Loaded ONNX session for {model_name}")
        return session
    
    def run_inference(self, model_name: str, input_data: np.ndarray) -> np.ndarray:
        """Run inference using ONNX Runtime"""
        session = self.load_onnx_session(model_name)
        
        # Run inference
        outputs = session.run(None, {'input': input_data})
        return outputs[0]
    
    def benchmark_performance(self, pytorch_model: torch.nn.Module,
                            onnx_session: ort.InferenceSession,
                            input_data: torch.Tensor,
                            num_runs: int = 100) -> Dict[str, float]:
        """Benchmark PyTorch vs ONNX performance"""
        
        # Warm up
        for _ in range(10):
            with torch.no_grad():
                _ = pytorch_model(input_data)
            _ = onnx_session.run(None, {'input': input_data.numpy()})
        
        # Benchmark PyTorch
        torch_times = []
        for _ in range(num_runs):
            start = time.time()
            with torch.no_grad():
                _ = pytorch_model(input_data)
            torch_times.append(time.time() - start)
        
        # Benchmark ONNX
        onnx_times = []
        for _ in range(num_runs):
            start = time.time()
            _ = onnx_session.run(None, {'input': input_data.numpy()})
            onnx_times.append(time.time() - start)
        
        return {
            "pytorch_avg_ms": np.mean(torch_times) * 1000,
            "onnx_avg_ms": np.mean(onnx_times) * 1000,
            "speedup": np.mean(torch_times) / np.mean(onnx_times)
        }

# Global ONNX optimizer instance
onnx_optimizer = ONNXModelOptimizer()
