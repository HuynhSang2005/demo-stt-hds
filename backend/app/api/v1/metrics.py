#!/usr/bin/env python3
"""
Metrics API Endpoints
Task 12: Expose performance metrics via HTTP endpoints

Provides:
- GET /v1/metrics - Current metrics summary
- GET /v1/metrics/detailed - Detailed metrics with breakdown
- GET /v1/metrics/errors - Recent errors
- POST /v1/metrics/reset - Reset metrics (admin only)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from ...core.metrics import get_metrics_collector, PerformanceMetrics

# Create router
router = APIRouter(prefix="/v1/metrics", tags=["metrics"])

class MetricsSummaryResponse(BaseModel):
    """Response model for metrics summary"""
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_second: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate_percent: float
    memory_usage_mb: float
    memory_percent: float

class DetailedMetricsResponse(BaseModel):
    """Response model for detailed metrics"""
    latency: Dict[str, float]
    throughput: Dict[str, Any]
    component_timing: Dict[str, float]
    memory: Dict[str, float]
    summary_text: str

class ErrorLogEntry(BaseModel):
    """Single error log entry"""
    timestamp: float
    error_type: str
    error_message: str

class ErrorsResponse(BaseModel):
    """Response model for errors"""
    recent_errors: List[ErrorLogEntry]
    total_errors: int

@router.get("/", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    window_seconds: Optional[int] = Query(None, description="Time window in seconds (None = all time)")
) -> MetricsSummaryResponse:
    """
    Get performance metrics summary
    
    Args:
        window_seconds: Optional time window to analyze (None = all time)
        
    Returns:
        MetricsSummaryResponse with key performance indicators
        
    Example:
        GET /v1/metrics
        GET /v1/metrics?window_seconds=300  # Last 5 minutes
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_metrics(window_seconds=window_seconds)
        
        return MetricsSummaryResponse(
            avg_latency_ms=metrics.avg_latency,
            p50_latency_ms=metrics.p50_latency,
            p95_latency_ms=metrics.p95_latency,
            p99_latency_ms=metrics.p99_latency,
            requests_per_second=metrics.requests_per_second,
            total_requests=metrics.total_requests,
            successful_requests=metrics.successful_requests,
            failed_requests=metrics.failed_requests,
            error_rate_percent=metrics.error_rate,
            memory_usage_mb=metrics.memory_usage_mb,
            memory_percent=metrics.memory_percent
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {e}")

@router.get("/detailed", response_model=DetailedMetricsResponse)
async def get_detailed_metrics(
    window_seconds: Optional[int] = Query(None, description="Time window in seconds (None = all time)")
) -> DetailedMetricsResponse:
    """
    Get detailed performance metrics with full breakdown
    
    Args:
        window_seconds: Optional time window to analyze (None = all time)
        
    Returns:
        DetailedMetricsResponse with comprehensive metrics
        
    Example:
        GET /v1/metrics/detailed
        GET /v1/metrics/detailed?window_seconds=3600  # Last hour
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_metrics(window_seconds=window_seconds)
        summary_text = collector.get_metrics_summary(window_seconds=window_seconds)
        
        return DetailedMetricsResponse(
            latency={
                "avg_ms": metrics.avg_latency,
                "p50_ms": metrics.p50_latency,
                "p95_ms": metrics.p95_latency,
                "p99_ms": metrics.p99_latency,
                "min_ms": metrics.min_latency,
                "max_ms": metrics.max_latency
            },
            throughput={
                "requests_per_second": metrics.requests_per_second,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "error_rate_percent": metrics.error_rate
            },
            component_timing={
                "avg_asr_ms": metrics.avg_asr_time,
                "avg_classifier_ms": metrics.avg_classifier_time,
                "avg_preprocessing_ms": metrics.avg_preprocessing_time,
                "avg_websocket_ms": metrics.avg_websocket_time
            },
            memory={
                "usage_mb": metrics.memory_usage_mb,
                "percent": metrics.memory_percent
            },
            summary_text=summary_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detailed metrics: {e}")

@router.get("/errors", response_model=ErrorsResponse)
async def get_recent_errors(
    count: int = Query(10, description="Number of recent errors to return", ge=1, le=100)
) -> ErrorsResponse:
    """
    Get recent error logs
    
    Args:
        count: Number of recent errors to return (1-100)
        
    Returns:
        ErrorsResponse with recent error entries
        
    Example:
        GET /v1/metrics/errors
        GET /v1/metrics/errors?count=50
    """
    try:
        collector = get_metrics_collector()
        errors = collector.get_recent_errors(count=count)
        
        error_entries = [
            ErrorLogEntry(
                timestamp=error["timestamp"],
                error_type=error["type"],
                error_message=error["message"]
            )
            for error in errors
        ]
        
        return ErrorsResponse(
            recent_errors=error_entries,
            total_errors=len(errors)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get errors: {e}")

@router.post("/reset")
async def reset_metrics() -> Dict[str, str]:
    """
    Reset all metrics counters
    
    WARNING: This will clear all collected metrics data.
    Use with caution, typically only in development/testing.
    
    Returns:
        Success message
        
    Example:
        POST /v1/metrics/reset
    """
    try:
        collector = get_metrics_collector()
        collector.reset()
        
        return {
            "status": "success",
            "message": "All metrics have been reset"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {e}")

@router.get("/health")
async def metrics_health() -> Dict[str, str]:
    """
    Check if metrics collection is working
    
    Returns:
        Health status
        
    Example:
        GET /v1/metrics/health
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_metrics()
        
        return {
            "status": "healthy",
            "total_requests": str(metrics.total_requests),
            "uptime_status": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Metrics service unavailable: {e}")
