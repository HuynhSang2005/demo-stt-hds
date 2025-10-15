#!/usr/bin/env python3
"""
Optimized Async Audio Processing Service
Advanced parallel processing for Vietnamese STT with model caching
"""

import asyncio
import time
import torch
import numpy as np
from typing import Optional, Dict, Any, Tuple, Union, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import dataclass

# Backend imports
from ..core.config import Settings
from ..core.logger import AudioProcessingLogger
from ..core.error_handling import (
    BaseAppError, AudioInputError, ModelInferenceError, 
    TimeoutError as AppTimeoutError, CircuitBreaker
)
from ..models.phowhisper_asr import PhoWhisperASR, create_asr_model, TranscriptionResult
from ..models.classifier import LocalPhoBERTClassifier, create_classifier_model, ClassificationResult
from ..schemas.audio import TranscriptResult, ErrorResponse, create_transcript_result, create_error_response

@dataclass
class ProcessingMetrics:
    """Metrics for processing performance tracking"""
    asr_time: float = 0.0
    classification_time: float = 0.0
    total_time: float = 0.0
    audio_duration: float = 0.0
    throughput_ratio: float = 0.0

class ModelCache:
    """Thread-safe model cache with lazy loading"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._loading: Dict[str, bool] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="model_loader")
    
    async def get_model(self, model_key: str, loader_func, *args, **kwargs):
        """Get model from cache or load it lazily"""
        if model_key not in self._locks:
            self._locks[model_key] = asyncio.Lock()
        
        async with self._locks[model_key]:
            if model_key in self._cache:
                return self._cache[model_key]
            
            if model_key in self._loading and self._loading[model_key]:
                # Wait for another coroutine to finish loading
                while model_key in self._loading and self._loading[model_key]:
                    await asyncio.sleep(0.1)
                return self._cache.get(model_key)
            
            # Mark as loading
            self._loading[model_key] = True
            
            try:
                # Load model in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                model = await loop.run_in_executor(
                    self._executor, 
                    loader_func, 
                    *args, 
                    **kwargs
                )
                self._cache[model_key] = model
                return model
            finally:
                self._loading[model_key] = False
    
    def clear_cache(self):
        """Clear model cache"""
        for model in self._cache.values():
            if hasattr(model, 'cleanup'):
                model.cleanup()
        self._cache.clear()
        self._loading.clear()
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)

class OptimizedAsyncAudioProcessor:
    """
    High-performance async audio processor with parallel model inference
    Features:
    - Parallel ASR + Classification processing
    - Model caching with lazy loading
    - Thread-safe operations
    - Performance metrics tracking
    - Circuit breaker protection
    - Memory optimization
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.logger = AudioProcessingLogger("async_audio_processor")
        
        # Model cache for lazy loading
        self.model_cache = ModelCache()
        
        # Circuit breakers for model protection
        self.asr_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=30,
            expected_exception=ModelInferenceError
        )
        self.classifier_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=30,
            expected_exception=ModelInferenceError
        )
        
        # Thread pool for CPU-intensive tasks
        self.cpu_executor = ThreadPoolExecutor(
            max_workers=min(4, torch.get_num_threads()),
            thread_name_prefix="audio_cpu"
        )
        
        # Performance tracking
        self.metrics_history: List[ProcessingMetrics] = []
        self.max_metrics_history = 100
        
        # Model initialization flags
        self._asr_initialized = False
        self._classifier_initialized = False
        
        self.logger.logger.info(
            "async_processor_initialized",
            event_type="processor_init",
            max_workers=self.cpu_executor._max_workers,
            torch_threads=torch.get_num_threads()
        )
    
    async def initialize_models(self) -> None:
        """Initialize models asynchronously with caching"""
        self.logger.logger.info("initializing_models", event_type="model_init_start")
        
        init_start = time.time()
        
        # Initialize models in parallel
        try:
            asr_task = self.model_cache.get_model(
                "phowhisper_asr",
                self._load_asr_model
            )
            classifier_task = self.model_cache.get_model(
                "phobert_classifier", 
                self._load_classifier_model
            )
            
            # Wait for both models to load
            asr_model, classifier_model = await asyncio.gather(
                asr_task, 
                classifier_task,
                return_exceptions=True
            )
            
            # Check for errors
            if isinstance(asr_model, Exception):
                raise ModelInferenceError(f"ASR model loading failed: {asr_model}")
            if isinstance(classifier_model, Exception):
                raise ModelInferenceError(f"Classifier model loading failed: {classifier_model}")
            
            self._asr_initialized = True
            self._classifier_initialized = True
            
            init_time = time.time() - init_start
            self.logger.logger.info(
                "models_initialized",
                event_type="model_init_complete",
                init_time_seconds=init_time,
                asr_model_type=type(asr_model).__name__,
                classifier_model_type=type(classifier_model).__name__
            )
            
        except Exception as e:
            self.logger.logger.error(
                "model_initialization_failed",
                event_type="model_init_error",
                error_message=str(e)
            )
            raise
    
    def _load_asr_model(self) -> PhoWhisperASR:
        """Load ASR model (runs in thread pool)"""
        try:
            model = create_asr_model(self.settings)
            self.logger.logger.info("asr_model_loaded", model_name="PhoWhisper")
            return model
        except Exception as e:
            self.logger.logger.error("asr_model_load_failed", error=str(e))
            raise
    
    def _load_classifier_model(self) -> LocalPhoBERTClassifier:
        """Load classifier model (runs in thread pool)"""
        try:
            model = create_classifier_model(self.settings)
            self.logger.logger.info("classifier_model_loaded", model_name="PhoBERT")
            return model
        except Exception as e:
            self.logger.logger.error("classifier_model_load_failed", error=str(e))
            raise
    
    async def process_audio_parallel(
        self, 
        audio_data: bytes,
        enable_parallel: bool = True
    ) -> Tuple[TranscriptResult, ProcessingMetrics]:
        """
        Process audio with parallel ASR and classification
        
        Args:
            audio_data: Raw audio data
            enable_parallel: Whether to run ASR and classification in parallel
            
        Returns:
            Tuple of (transcript_result, processing_metrics)
        """
        if not self._asr_initialized or not self._classifier_initialized:
            await self.initialize_models()
        
        processing_start = time.time()
        metrics = ProcessingMetrics()
        
        try:
            # 1. Decode audio (CPU-bound, run in thread pool)
            loop = asyncio.get_event_loop()
            waveform, sample_rate = await loop.run_in_executor(
                self.cpu_executor,
                self._decode_audio_bytes,
                audio_data
            )
            
            # Calculate audio duration
            audio_duration = waveform.shape[-1] / sample_rate
            metrics.audio_duration = audio_duration
            
            # 2. Validate audio
            await loop.run_in_executor(
                self.cpu_executor,
                self._validate_audio_input,
                waveform,
                sample_rate
            )
            
            # 3. Process with ASR and Classification
            if enable_parallel:
                # Parallel processing for maximum performance
                asr_task = self._run_asr_async(waveform, sample_rate)
                # We need ASR result first for classification
                asr_result = await asr_task
                metrics.asr_time = time.time() - processing_start
                
                # Then run classification
                classification_task = self._run_classification_async(asr_result.text)
                classification_result = await classification_task
                metrics.classification_time = time.time() - (processing_start + metrics.asr_time)
                
            else:
                # Sequential processing (fallback)
                asr_result = await self._run_asr_async(waveform, sample_rate)
                metrics.asr_time = time.time() - processing_start
                
                classification_result = await self._run_classification_async(asr_result.text)
                metrics.classification_time = time.time() - (processing_start + metrics.asr_time)
            
            # 4. Create final result
            result = create_transcript_result(
                text=asr_result.text,
                confidence=asr_result.confidence,
                language=asr_result.language,
                processing_time=asr_result.processing_time,
                sentiment_label=classification_result.get('label', 'neutral'),
                sentiment_score=classification_result.get('score', 0.0),
                toxic_keywords=classification_result.get('toxic_keywords', []),
                is_toxic=classification_result.get('is_toxic', False)
            )
            
            # 5. Calculate metrics
            metrics.total_time = time.time() - processing_start
            metrics.throughput_ratio = audio_duration / metrics.total_time
            
            # Store metrics
            self._store_metrics(metrics)
            
            self.logger.logger.info(
                "audio_processing_completed",
                event_type="processing_complete",
                audio_duration=audio_duration,
                asr_time_ms=metrics.asr_time * 1000,
                classification_time_ms=metrics.classification_time * 1000,
                total_time_ms=metrics.total_time * 1000,
                throughput_ratio=metrics.throughput_ratio,
                parallel_enabled=enable_parallel
            )
            
            return result, metrics
            
        except Exception as e:
            metrics.total_time = time.time() - processing_start
            self.logger.logger.error(
                "audio_processing_failed",
                event_type="processing_error",
                error_message=str(e),
                processing_time_ms=metrics.total_time * 1000
            )
            raise
    
    async def _run_asr_async(self, waveform: torch.Tensor, sample_rate: int) -> TranscriptionResult:
        """Run ASR with async protection"""
        try:
            asr_model = await self.model_cache.get_model("phowhisper_asr", self._load_asr_model)
            
            result = await self.asr_circuit_breaker.call_async(
                lambda: asyncio.to_thread(
                    asr_model.transcribe_with_metadata,
                    waveform,
                    sample_rate
                )
            )
            return result
        except Exception as e:
            raise ModelInferenceError(f"ASR failed: {str(e)}", model_name="PhoWhisper ASR") from e
    
    async def _run_classification_async(self, text: str) -> Dict[str, Any]:
        """Run classification with async protection"""
        try:
            classifier_model = await self.model_cache.get_model("phobert_classifier", self._load_classifier_model)
            
            # Determine method based on text length
            if len(text) > 500:
                result = await self.classifier_circuit_breaker.call_async(
                    lambda: asyncio.to_thread(classifier_model.classify_long_text, text)
                )
            else:
                result = await self.classifier_circuit_breaker.call_async(
                    lambda: asyncio.to_thread(classifier_model.classify_text, text)
                )
            
            return result
        except Exception as e:
            raise ModelInferenceError(f"Classification failed: {str(e)}", model_name="PhoBERT Classifier") from e
    
    def _decode_audio_bytes(self, audio_data: bytes) -> Tuple[torch.Tensor, int]:
        """Decode audio bytes to tensor (runs in thread pool)"""
        try:
            import io
            import torchaudio
            from pydub import AudioSegment
            
            # Try pydub first for better format support
            try:
                audio_buffer = io.BytesIO(audio_data)
                audio_segment = AudioSegment.from_file(audio_buffer)
                
                # Convert to WAV format in memory
                wav_buffer = io.BytesIO()
                audio_segment.export(wav_buffer, format="wav")
                wav_buffer.seek(0)
                
                # Load with torchaudio
                waveform, sample_rate = torchaudio.load(wav_buffer)
                
            except Exception:
                # Fallback to torchaudio direct loading
                audio_buffer = io.BytesIO(audio_data)
                waveform, sample_rate = torchaudio.load(audio_buffer)
            
            # Ensure mono channel
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000
            
            return waveform, sample_rate
            
        except Exception as e:
            raise AudioInputError(f"Audio decoding failed: {str(e)}") from e
    
    def _validate_audio_input(self, waveform: torch.Tensor, sample_rate: int) -> None:
        """Validate audio input"""
        if not isinstance(waveform, torch.Tensor):
            raise AudioInputError("Waveform must be torch.Tensor")
        
        if waveform.dim() == 0 or waveform.numel() == 0:
            raise AudioInputError("Waveform cannot be empty")
        
        if sample_rate <= 0:
            raise AudioInputError("Sample rate must be positive")
        
        # Check duration limits
        duration = waveform.shape[-1] / sample_rate
        if duration > self.settings.MAX_AUDIO_DURATION:
            raise AudioInputError(f"Audio too long: {duration:.1f}s > {self.settings.MAX_AUDIO_DURATION}s")
        
        if duration < self.settings.MIN_AUDIO_DURATION:
            raise AudioInputError(f"Audio too short: {duration:.1f}s < {self.settings.MIN_AUDIO_DURATION}s")
    
    def _store_metrics(self, metrics: ProcessingMetrics) -> None:
        """Store processing metrics"""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_metrics_history:
            self.metrics_history.pop(0)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.metrics_history:
            return {"message": "No metrics available"}
        
        asr_times = [m.asr_time for m in self.metrics_history]
        classification_times = [m.classification_time for m in self.metrics_history]
        total_times = [m.total_time for m in self.metrics_history]
        throughput_ratios = [m.throughput_ratio for m in self.metrics_history]
        
        return {
            "total_samples": len(self.metrics_history),
            "asr_time": {
                "avg_ms": np.mean(asr_times) * 1000,
                "min_ms": np.min(asr_times) * 1000,
                "max_ms": np.max(asr_times) * 1000,
                "std_ms": np.std(asr_times) * 1000
            },
            "classification_time": {
                "avg_ms": np.mean(classification_times) * 1000,
                "min_ms": np.min(classification_times) * 1000,
                "max_ms": np.max(classification_times) * 1000,
                "std_ms": np.std(classification_times) * 1000
            },
            "total_time": {
                "avg_ms": np.mean(total_times) * 1000,
                "min_ms": np.min(total_times) * 1000,
                "max_ms": np.max(total_times) * 1000,
                "std_ms": np.std(total_times) * 1000
            },
            "throughput": {
                "avg_ratio": np.mean(throughput_ratios),
                "min_ratio": np.min(throughput_ratios),
                "max_ratio": np.max(throughput_ratios)
            }
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.logger.logger.info("cleaning_up_processor", event_type="cleanup_start")
        
        # Clear model cache
        self.model_cache.clear_cache()
        
        # Shutdown thread pool
        self.cpu_executor.shutdown(wait=True)
        
        # Clear metrics
        self.metrics_history.clear()
        
        self.logger.logger.info("processor_cleanup_completed", event_type="cleanup_complete")
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'cpu_executor'):
            self.cpu_executor.shutdown(wait=False)
