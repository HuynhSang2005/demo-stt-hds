#!/usr/bin/env python3
"""
Performance Metrics Collection Module
Task 12: Add metrics collection and performance tracking

Features:
- Request/response timing
- Model inference latency tracking
- Throughput monitoring (requests/sec)
- WebSocket connection metrics
- Audio processing pipeline metrics
- Memory usage tracking
- Error rate monitoring
"""

import time
import threading
import psutil
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta
from enum import Enum

class MetricType(Enum):
    """Types of metrics collected"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY = "memory"
    COUNT = "count"

@dataclass
class MetricPoint:
    """Single metric measurement"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""
    # Latency metrics (milliseconds)
    avg_latency: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    min_latency: float = 0.0
    max_latency: float = 0.0
    
    # Throughput metrics
    requests_per_second: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Error metrics
    error_rate: float = 0.0
    
    # Memory metrics (MB)
    memory_usage_mb: float = 0.0
    memory_percent: float = 0.0
    
    # Timing breakdown
    avg_asr_time: float = 0.0
    avg_classifier_time: float = 0.0
    avg_preprocessing_time: float = 0.0
    avg_websocket_time: float = 0.0

class MetricsCollector:
    """
    Task 12: Centralized metrics collection
    
    Tracks performance metrics for:
    - Overall request latency
    - ASR model inference time
    - Classifier inference time
    - WebSocket communication
    - Memory usage
    - Error rates
    """
    
    def __init__(self, window_size: int = 1000, retention_seconds: int = 3600):
        """
        Initialize metrics collector
        
        Args:
            window_size: Number of recent measurements to keep for statistics
            retention_seconds: How long to retain metrics (default: 1 hour)
        """
        self.window_size = window_size
        self.retention_seconds = retention_seconds
        
        # Thread-safe storage for metrics
        self._lock = threading.Lock()
        
        # Circular buffers for different metric types
        self._latencies: deque = deque(maxlen=window_size)
        self._asr_times: deque = deque(maxlen=window_size)
        self._classifier_times: deque = deque(maxlen=window_size)
        self._preprocessing_times: deque = deque(maxlen=window_size)
        self._websocket_times: deque = deque(maxlen=window_size)
        
        # Counters
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._start_time = time.time()
        
        # Error tracking
        self._errors: deque = deque(maxlen=100)  # Last 100 errors
        
        # Process info
        self._process = psutil.Process(os.getpid())
    
    def record_request_latency(self, latency_ms: float, success: bool = True):
        """
        Record overall request latency
        
        Args:
            latency_ms: Request latency in milliseconds
            success: Whether request was successful
        """
        with self._lock:
            self._latencies.append(MetricPoint(
                timestamp=time.time(),
                value=latency_ms,
                labels={"success": str(success)}
            ))
            
            self._total_requests += 1
            if success:
                self._successful_requests += 1
            else:
                self._failed_requests += 1
    
    def record_asr_time(self, time_ms: float):
        """Record ASR model inference time"""
        with self._lock:
            self._asr_times.append(MetricPoint(
                timestamp=time.time(),
                value=time_ms
            ))
    
    def record_classifier_time(self, time_ms: float):
        """Record classifier inference time"""
        with self._lock:
            self._classifier_times.append(MetricPoint(
                timestamp=time.time(),
                value=time_ms
            ))
    
    def record_preprocessing_time(self, time_ms: float):
        """Record preprocessing time"""
        with self._lock:
            self._preprocessing_times.append(MetricPoint(
                timestamp=time.time(),
                value=time_ms
            ))
    
    def record_websocket_time(self, time_ms: float):
        """Record WebSocket communication time"""
        with self._lock:
            self._websocket_times.append(MetricPoint(
                timestamp=time.time(),
                value=time_ms
            ))
    
    def record_error(self, error_type: str, error_message: str):
        """
        Record an error occurrence
        
        Args:
            error_type: Type of error (e.g., "ASR_ERROR", "CLASSIFIER_ERROR")
            error_message: Error message
        """
        with self._lock:
            self._errors.append({
                "timestamp": time.time(),
                "type": error_type,
                "message": error_message
            })
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile from list of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _get_recent_values(self, buffer: deque, max_age_seconds: Optional[int] = None) -> List[float]:
        """Get recent values from buffer, optionally filtered by age"""
        if not max_age_seconds:
            return [point.value for point in buffer]
        
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds
        
        return [
            point.value for point in buffer 
            if point.timestamp >= cutoff_time
        ]
    
    def get_metrics(self, window_seconds: Optional[int] = None) -> PerformanceMetrics:
        """
        Get aggregated performance metrics
        
        Args:
            window_seconds: Only consider metrics from last N seconds (None = all)
            
        Returns:
            PerformanceMetrics with aggregated statistics
        """
        with self._lock:
            # Get recent latencies
            latencies = self._get_recent_values(self._latencies, window_seconds)
            asr_times = self._get_recent_values(self._asr_times, window_seconds)
            classifier_times = self._get_recent_values(self._classifier_times, window_seconds)
            preprocessing_times = self._get_recent_values(self._preprocessing_times, window_seconds)
            websocket_times = self._get_recent_values(self._websocket_times, window_seconds)
            
            # Calculate latency statistics
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                p50_latency = self._calculate_percentile(latencies, 50)
                p95_latency = self._calculate_percentile(latencies, 95)
                p99_latency = self._calculate_percentile(latencies, 99)
                min_latency = min(latencies)
                max_latency = max(latencies)
            else:
                avg_latency = p50_latency = p95_latency = p99_latency = 0.0
                min_latency = max_latency = 0.0
            
            # Calculate throughput
            elapsed_time = time.time() - self._start_time
            requests_per_second = self._total_requests / elapsed_time if elapsed_time > 0 else 0.0
            
            # Calculate error rate
            error_rate = (self._failed_requests / self._total_requests * 100) if self._total_requests > 0 else 0.0
            
            # Get memory usage
            memory_info = self._process.memory_info()
            memory_usage_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            memory_percent = self._process.memory_percent()
            
            # Calculate component timings
            avg_asr_time = sum(asr_times) / len(asr_times) if asr_times else 0.0
            avg_classifier_time = sum(classifier_times) / len(classifier_times) if classifier_times else 0.0
            avg_preprocessing_time = sum(preprocessing_times) / len(preprocessing_times) if preprocessing_times else 0.0
            avg_websocket_time = sum(websocket_times) / len(websocket_times) if websocket_times else 0.0
            
            return PerformanceMetrics(
                avg_latency=avg_latency,
                p50_latency=p50_latency,
                p95_latency=p95_latency,
                p99_latency=p99_latency,
                min_latency=min_latency,
                max_latency=max_latency,
                requests_per_second=requests_per_second,
                total_requests=self._total_requests,
                successful_requests=self._successful_requests,
                failed_requests=self._failed_requests,
                error_rate=error_rate,
                memory_usage_mb=memory_usage_mb,
                memory_percent=memory_percent,
                avg_asr_time=avg_asr_time,
                avg_classifier_time=avg_classifier_time,
                avg_preprocessing_time=avg_preprocessing_time,
                avg_websocket_time=avg_websocket_time
            )
    
    def get_metrics_summary(self, window_seconds: Optional[int] = None) -> str:
        """
        Get human-readable metrics summary
        
        Args:
            window_seconds: Only consider metrics from last N seconds (None = all)
            
        Returns:
            Formatted string with metrics summary
        """
        metrics = self.get_metrics(window_seconds)
        
        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║           PERFORMANCE METRICS SUMMARY                        ║
╠══════════════════════════════════════════════════════════════╣
║ LATENCY METRICS (ms)                                         ║
║  Average: {metrics.avg_latency:8.2f} ms                                  ║
║  P50:     {metrics.p50_latency:8.2f} ms                                  ║
║  P95:     {metrics.p95_latency:8.2f} ms                                  ║
║  P99:     {metrics.p99_latency:8.2f} ms                                  ║
║  Min:     {metrics.min_latency:8.2f} ms                                  ║
║  Max:     {metrics.max_latency:8.2f} ms                                  ║
╠══════════════════════════════════════════════════════════════╣
║ THROUGHPUT METRICS                                           ║
║  Requests/sec: {metrics.requests_per_second:6.2f}                                  ║
║  Total:        {metrics.total_requests:6d}                                     ║
║  Success:      {metrics.successful_requests:6d}                                     ║
║  Failed:       {metrics.failed_requests:6d}                                     ║
║  Error Rate:   {metrics.error_rate:6.2f}%                                  ║
╠══════════════════════════════════════════════════════════════╣
║ COMPONENT TIMING (ms)                                        ║
║  ASR:           {metrics.avg_asr_time:8.2f} ms                               ║
║  Classifier:    {metrics.avg_classifier_time:8.2f} ms                               ║
║  Preprocessing: {metrics.avg_preprocessing_time:8.2f} ms                               ║
║  WebSocket:     {metrics.avg_websocket_time:8.2f} ms                               ║
╠══════════════════════════════════════════════════════════════╣
║ MEMORY USAGE                                                 ║
║  RSS:     {metrics.memory_usage_mb:8.2f} MB                                 ║
║  Percent: {metrics.memory_percent:7.2f}%                                   ║
╚══════════════════════════════════════════════════════════════╝
        """
        return summary
    
    def get_recent_errors(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent errors
        
        Args:
            count: Number of recent errors to return
            
        Returns:
            List of error dictionaries
        """
        with self._lock:
            errors = list(self._errors)[-count:]
            return errors
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._latencies.clear()
            self._asr_times.clear()
            self._classifier_times.clear()
            self._preprocessing_times.clear()
            self._websocket_times.clear()
            self._errors.clear()
            
            self._total_requests = 0
            self._successful_requests = 0
            self._failed_requests = 0
            self._start_time = time.time()

# Global singleton instance
_metrics_collector: Optional[MetricsCollector] = None
_metrics_lock = threading.Lock()

def get_metrics_collector() -> MetricsCollector:
    """
    Get or create global metrics collector singleton
    
    Returns:
        Global MetricsCollector instance
    """
    global _metrics_collector
    
    if _metrics_collector is None:
        with _metrics_lock:
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
    
    return _metrics_collector

def reset_metrics_collector():
    """Reset the global metrics collector"""
    global _metrics_collector
    
    with _metrics_lock:
        if _metrics_collector is not None:
            _metrics_collector.reset()

if __name__ == '__main__':
    # Test metrics collector
    collector = MetricsCollector()
    
    print("Testing MetricsCollector...")
    
    # Simulate some requests
    import random
    for i in range(100):
        latency = random.uniform(50, 200)
        success = random.random() > 0.05  # 5% error rate
        
        collector.record_request_latency(latency, success)
        collector.record_asr_time(random.uniform(30, 100))
        collector.record_classifier_time(random.uniform(20, 80))
        
        if not success:
            collector.record_error("TEST_ERROR", f"Test error {i}")
    
    # Print metrics
    print(collector.get_metrics_summary())
    
    # Print recent errors
    print("\nRecent Errors:")
    for error in collector.get_recent_errors(5):
        print(f"  [{datetime.fromtimestamp(error['timestamp'])}] {error['type']}: {error['message']}")
