#!/usr/bin/env python3
"""
Model Cache Utility
Singleton pattern for model caching and lazy loading
"""

import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path
import torch

class ModelCache:
    """Thread-safe singleton model cache"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._models: Dict[str, Any] = {}
        self._model_locks: Dict[str, threading.Lock] = {}
        self._initialized = True
        
        print("ModelCache initialized")
    
    def get_model(self, model_name: str, model_loader_func, *args, **kwargs):
        """Get model from cache or load if not cached"""
        if model_name not in self._models:
            with self._lock:
                if model_name not in self._models:
                    # Create lock for this model
                    if model_name not in self._model_locks:
                        self._model_locks[model_name] = threading.Lock()
                    
                    with self._model_locks[model_name]:
                        print(f"Loading model: {model_name}")
                        start_time = time.time()
                        
                        # Load model
                        model = model_loader_func(*args, **kwargs)
                        
                        # Set to eval mode for inference
                        if hasattr(model, 'eval'):
                            model.eval()
                        
                        # Cache the model
                        self._models[model_name] = model
                        
                        load_time = time.time() - start_time
                        print(f"Model {model_name} loaded in {load_time:.2f}s")
        
        return self._models[model_name]
    
    def clear_cache(self, model_name: Optional[str] = None):
        """Clear model cache"""
        with self._lock:
            if model_name:
                if model_name in self._models:
                    del self._models[model_name]
                    print(f"Cleared cache for {model_name}")
            else:
                self._models.clear()
                print("Cleared all model cache")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        return {
            "cached_models": list(self._models.keys()),
            "cache_size": len(self._models),
            "memory_usage": self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage of cached models"""
        try:
            total_params = 0
            for model in self._models.values():
                if hasattr(model, 'parameters'):
                    total_params += sum(p.numel() for p in model.parameters())
            
            # Rough estimate: 4 bytes per parameter (float32)
            memory_mb = (total_params * 4) / (1024 * 1024)
            return f"{memory_mb:.2f} MB"
        except:
            return "Unknown"

# Global model cache instance
model_cache = ModelCache()
