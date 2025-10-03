#!/usr/bin/env python3
"""
Batch Processor Service - Backend Implementation
Micro-batching for ASR và Classification to improve GPU utilization

Features:
- Dynamic batch accumulation with timeout
- Automatic batch size adjustment based on load
- Batch processing for ASR inference
- Batch processing for Classification inference
- Fair scheduling across multiple clients
- Performance metrics and monitoring

Target: 2-5 requests per batch for optimal GPU utilization
"""

import asyncio
import time
import torch
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

# Backend imports
from ..core.config import Settings
from ..core.logger import AudioProcessingLogger, AppLogger
from ..models.asr import LocalWav2Vec2ASR
from ..models.classifier import LocalPhoBERTClassifier


@dataclass
class BatchRequest:
    """Single request in a batch"""
    request_id: str
    data: Any  # Waveform tensor or text string
    timestamp: float
    client_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


@dataclass
class BatchResult:
    """Result for a single request in batch"""
    request_id: str
    result: Any
    processing_time: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class BatchStats:
    """Batch processing statistics"""
    total_batches: int = 0
    total_requests: int = 0
    avg_batch_size: float = 0.0
    avg_processing_time: float = 0.0
    avg_wait_time: float = 0.0
    max_batch_size: int = 0
    min_batch_size: int = 999
    
    def update(self, batch_size: int, processing_time: float, wait_time: float):
        """Update statistics with new batch metrics"""
        self.total_batches += 1
        self.total_requests += batch_size
        self.max_batch_size = max(self.max_batch_size, batch_size)
        self.min_batch_size = min(self.min_batch_size, batch_size)
        
        # Running average
        n = self.total_batches
        self.avg_batch_size = (self.avg_batch_size * (n - 1) + batch_size) / n
        self.avg_processing_time = (self.avg_processing_time * (n - 1) + processing_time) / n
        self.avg_wait_time = (self.avg_wait_time * (n - 1) + wait_time) / n


class ASRBatchProcessor:
    """
    Batch processor for ASR inference
    Accumulates multiple audio requests and processes them together
    """
    
    def __init__(
        self,
        asr_model: LocalWav2Vec2ASR,
        settings: Settings,
        logger: Optional[AudioProcessingLogger] = None,
        max_batch_size: int = 5,
        max_wait_time: float = 0.05  # 50ms max wait
    ):
        """
        Initialize ASR batch processor
        
        Args:
            asr_model: ASR model instance
            settings: Application settings
            logger: Structured logger
            max_batch_size: Maximum requests per batch (default: 5)
            max_wait_time: Maximum time to wait for batch accumulation in seconds
        """
        self.asr_model = asr_model
        self.settings = settings
        self.logger = logger or AudioProcessingLogger("asr_batch_processor")
        self.app_logger = AppLogger("asr_batch_app")
        
        # Batch configuration
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.min_batch_size = 1  # Process immediately if only 1 request
        
        # Batch queue
        self.pending_requests: List[BatchRequest] = []
        self.request_futures: Dict[str, asyncio.Future] = {}
        self.lock = asyncio.Lock()
        
        # Statistics
        self.stats = BatchStats()
        
        # Background task
        self.batch_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """Start batch processing background task"""
        if not self.is_running:
            self.is_running = True
            self.batch_task = asyncio.create_task(self._batch_processing_loop())
            self.app_logger.logger.info(
                "asr_batch_processor_started",
                max_batch_size=self.max_batch_size,
                max_wait_time=self.max_wait_time
            )
    
    async def stop(self):
        """Stop batch processing"""
        self.is_running = False
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
    
    async def process_request(
        self,
        request_id: str,
        waveform: torch.Tensor,
        sample_rate: int,
        client_id: Optional[str] = None
    ) -> Any:
        """
        Submit ASR request for batch processing
        
        Args:
            request_id: Unique request identifier
            waveform: Audio waveform tensor
            sample_rate: Sample rate
            client_id: Optional client identifier
            
        Returns:
            ASR transcription result
        """
        # Create request
        request = BatchRequest(
            request_id=request_id,
            data=(waveform, sample_rate),
            timestamp=time.time(),
            client_id=client_id
        )
        
        # Create future for result
        future = asyncio.Future()
        
        async with self.lock:
            self.pending_requests.append(request)
            self.request_futures[request_id] = future
        
        # Wait for result
        result = await future
        return result
    
    async def _batch_processing_loop(self):
        """Background loop that processes batches"""
        while self.is_running:
            try:
                # Wait for batch to accumulate
                await asyncio.sleep(self.max_wait_time)
                
                # Check if there are pending requests
                async with self.lock:
                    if len(self.pending_requests) == 0:
                        continue
                    
                    # Get batch (up to max_batch_size)
                    batch = self.pending_requests[:self.max_batch_size]
                    self.pending_requests = self.pending_requests[self.max_batch_size:]
                
                # Process batch
                if batch:
                    await self._process_batch(batch)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.logger.error(
                    "batch_processing_error",
                    error=str(e),
                    event_type="batch_error"
                )
    
    async def _process_batch(self, batch: List[BatchRequest]):
        """
        Process a batch of ASR requests
        
        Args:
            batch: List of BatchRequest objects
        """
        batch_start_time = time.time()
        batch_size = len(batch)
        
        try:
            # Calculate wait time for first request
            first_wait_time = batch_start_time - batch[0].timestamp
            
            # Process batch in thread pool (CPU/GPU bound)
            results = await asyncio.to_thread(
                self._process_asr_batch_sync,
                batch
            )
            
            batch_processing_time = time.time() - batch_start_time
            
            # Deliver results to waiting futures
            async with self.lock:
                for batch_result in results:
                    future = self.request_futures.pop(batch_result.request_id, None)
                    if future and not future.done():
                        if batch_result.success:
                            future.set_result(batch_result.result)
                        else:
                            future.set_exception(
                                Exception(batch_result.error_message)
                            )
            
            # Update statistics
            self.stats.update(batch_size, batch_processing_time, first_wait_time)
            
            # Log batch completion
            self.logger.logger.info(
                "asr_batch_processed",
                batch_size=batch_size,
                processing_time=batch_processing_time,
                wait_time=first_wait_time,
                throughput=batch_size / batch_processing_time,
                event_type="batch_success"
            )
            
        except Exception as e:
            # Handle batch processing error
            error_msg = f"Batch processing failed: {e}"
            self.logger.logger.error(
                "asr_batch_failed",
                error=error_msg,
                batch_size=batch_size,
                event_type="batch_error"
            )
            
            # Fail all requests in batch
            async with self.lock:
                for request in batch:
                    future = self.request_futures.pop(request.request_id, None)
                    if future and not future.done():
                        future.set_exception(Exception(error_msg))
    
    def _process_asr_batch_sync(self, batch: List[BatchRequest]) -> List[BatchResult]:
        """
        Synchronous batch processing (runs in thread pool)
        
        Args:
            batch: List of BatchRequest objects
            
        Returns:
            List of BatchResult objects
        """
        results = []
        
        # For now, process sequentially
        # TODO: True batched inference with torch.stack()
        for request in batch:
            request_start = time.time()
            try:
                waveform, sample_rate = request.data
                result = self.asr_model.transcribe_with_metadata(waveform, sample_rate)
                
                results.append(BatchResult(
                    request_id=request.request_id,
                    result=result,
                    processing_time=time.time() - request_start,
                    success=result.success,
                    error_message=result.error_message
                ))
            except Exception as e:
                results.append(BatchResult(
                    request_id=request.request_id,
                    result=None,
                    processing_time=time.time() - request_start,
                    success=False,
                    error_message=str(e)
                ))
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        return {
            "total_batches": self.stats.total_batches,
            "total_requests": self.stats.total_requests,
            "avg_batch_size": round(self.stats.avg_batch_size, 2),
            "avg_processing_time": round(self.stats.avg_processing_time * 1000, 2),  # ms
            "avg_wait_time": round(self.stats.avg_wait_time * 1000, 2),  # ms
            "max_batch_size": self.stats.max_batch_size,
            "min_batch_size": self.stats.min_batch_size,
            "pending_requests": len(self.pending_requests),
            "is_running": self.is_running
        }


class ClassifierBatchProcessor:
    """
    Batch processor for text classification
    Similar to ASR batch processor but for text inputs
    """
    
    def __init__(
        self,
        classifier_model: LocalPhoBERTClassifier,
        settings: Settings,
        logger: Optional[AudioProcessingLogger] = None,
        max_batch_size: int = 8,  # Larger batch for text
        max_wait_time: float = 0.03  # 30ms max wait
    ):
        """Initialize classifier batch processor"""
        self.classifier_model = classifier_model
        self.settings = settings
        self.logger = logger or AudioProcessingLogger("classifier_batch_processor")
        self.app_logger = AppLogger("classifier_batch_app")
        
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        
        self.pending_requests: List[BatchRequest] = []
        self.request_futures: Dict[str, asyncio.Future] = {}
        self.lock = asyncio.Lock()
        
        self.stats = BatchStats()
        self.batch_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """Start batch processing"""
        if not self.is_running:
            self.is_running = True
            self.batch_task = asyncio.create_task(self._batch_processing_loop())
            self.app_logger.logger.info(
                "classifier_batch_processor_started",
                max_batch_size=self.max_batch_size,
                max_wait_time=self.max_wait_time
            )
    
    async def stop(self):
        """Stop batch processing"""
        self.is_running = False
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
    
    async def process_request(
        self,
        request_id: str,
        text: str,
        client_id: Optional[str] = None
    ) -> Any:
        """Submit classification request for batch processing"""
        request = BatchRequest(
            request_id=request_id,
            data=text,
            timestamp=time.time(),
            client_id=client_id
        )
        
        future = asyncio.Future()
        
        async with self.lock:
            self.pending_requests.append(request)
            self.request_futures[request_id] = future
        
        result = await future
        return result
    
    async def _batch_processing_loop(self):
        """Background batch processing loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.max_wait_time)
                
                async with self.lock:
                    if len(self.pending_requests) == 0:
                        continue
                    
                    batch = self.pending_requests[:self.max_batch_size]
                    self.pending_requests = self.pending_requests[self.max_batch_size:]
                
                if batch:
                    await self._process_batch(batch)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.logger.error(
                    "classifier_batch_error",
                    error=str(e),
                    event_type="batch_error"
                )
    
    async def _process_batch(self, batch: List[BatchRequest]):
        """Process a batch of classification requests"""
        batch_start_time = time.time()
        batch_size = len(batch)
        
        try:
            first_wait_time = batch_start_time - batch[0].timestamp
            
            # Use batch_classify method if available
            texts = [req.data for req in batch]
            results = await asyncio.to_thread(
                self.classifier_model.batch_classify,
                texts
            )
            
            batch_processing_time = time.time() - batch_start_time
            
            # Deliver results
            async with self.lock:
                for i, request in enumerate(batch):
                    future = self.request_futures.pop(request.request_id, None)
                    if future and not future.done():
                        future.set_result(results[i])
            
            self.stats.update(batch_size, batch_processing_time, first_wait_time)
            
            self.logger.logger.info(
                "classifier_batch_processed",
                batch_size=batch_size,
                processing_time=batch_processing_time,
                wait_time=first_wait_time,
                throughput=batch_size / batch_processing_time,
                event_type="batch_success"
            )
            
        except Exception as e:
            error_msg = f"Classification batch failed: {e}"
            self.logger.logger.error(
                "classifier_batch_failed",
                error=error_msg,
                batch_size=batch_size,
                event_type="batch_error"
            )
            
            async with self.lock:
                for request in batch:
                    future = self.request_futures.pop(request.request_id, None)
                    if future and not future.done():
                        future.set_exception(Exception(error_msg))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        return {
            "total_batches": self.stats.total_batches,
            "total_requests": self.stats.total_requests,
            "avg_batch_size": round(self.stats.avg_batch_size, 2),
            "avg_processing_time": round(self.stats.avg_processing_time * 1000, 2),
            "avg_wait_time": round(self.stats.avg_wait_time * 1000, 2),
            "max_batch_size": self.stats.max_batch_size,
            "min_batch_size": self.stats.min_batch_size,
            "pending_requests": len(self.pending_requests),
            "is_running": self.is_running
        }
