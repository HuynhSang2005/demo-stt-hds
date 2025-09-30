#!/usr/bin/env python3
"""
Additional REST API Endpoints for Client Generation Demo
Demonstrates various HTTP methods and response types
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import time

# Module-level variable to track system start time
_SYSTEM_START_TIME = time.time()

# Backend imports
from ...core.config import Settings, get_settings
from ...services.audio_processor import get_audio_processor

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["api"])

# Pydantic models for request/response
class ModelInfo(BaseModel):
    """Model information response"""
    model_type: str = Field(..., description="Type of model (asr/classifier)")
    loaded: bool = Field(..., description="Whether model is loaded")
    parameters: int = Field(..., description="Number of model parameters")
    device: str = Field(..., description="Device model is running on")
    
class ProcessingStats(BaseModel):
    """Processing statistics response"""
    processed_chunks: int = Field(..., description="Number of audio chunks processed")
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    average_processing_time: float = Field(..., description="Average processing time per chunk")
    real_time_factor: float = Field(..., description="Real-time factor (processing_time/audio_duration)")

class SystemStatus(BaseModel):
    """System status response"""
    status: str = Field(..., description="System status (healthy/degraded/error)")
    uptime: float = Field(..., description="System uptime in seconds")
    models: Dict[str, ModelInfo] = Field(..., description="Model information")
    processing: ProcessingStats = Field(..., description="Processing statistics")
    
class ConfigurationUpdate(BaseModel):
    """Configuration update request"""
    log_level: Optional[str] = Field(None, description="New log level")
    enable_debug: Optional[bool] = Field(None, description="Enable debug mode")
    
# REST API Endpoints

@router.get("/models", response_model=Dict[str, ModelInfo], tags=["models"])
async def get_models_info():
    """
    Get detailed information about loaded models
    
    Returns:
        Dictionary with ASR and classifier model information
    """
    try:
        audio_processor = get_audio_processor()
        model_info = audio_processor.get_model_info()
        
        response = {}
        
        # ASR Model Info
        asr_info = model_info.get("asr_model", {})
        if asr_info:
            response["asr"] = ModelInfo(
                model_type="wav2vec2_vietnamese",
                loaded=asr_info.get("loaded", False),
                parameters=asr_info.get("parameters", 0),
                device=asr_info.get("device", "unknown")
            )
        
        # Classifier Model Info
        classifier_info = model_info.get("classifier_model", {})
        if classifier_info:
            response["classifier"] = ModelInfo(
                model_type="phobert_toxic_detection", 
                loaded=classifier_info.get("loaded", False),
                parameters=classifier_info.get("parameters", 0),
                device=classifier_info.get("device", "unknown")
            )
            
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get model info: {str(e)}"
        )

@router.get("/status", response_model=SystemStatus, tags=["system"])
async def get_system_status():
    """
    Get comprehensive system status including models and processing stats
    
    Returns:
        Complete system status information
    """
    try:
        audio_processor = get_audio_processor()
        model_info = audio_processor.get_model_info()
        processing_stats = audio_processor.get_processing_stats()
        
        # Calculate uptime (simplified)
        uptime = time.time() - _SYSTEM_START_TIME
        
        # Build models info
        models = {}
        
        asr_info = model_info.get("asr_model", {})
        if asr_info:
            models["asr"] = ModelInfo(
                model_type="wav2vec2_vietnamese",
                loaded=asr_info.get("loaded", False),
                parameters=asr_info.get("parameters", 0),
                device=asr_info.get("device", "unknown")
            )
        
        classifier_info = model_info.get("classifier_model", {})
        if classifier_info:
            models["classifier"] = ModelInfo(
                model_type="phobert_toxic_detection",
                loaded=classifier_info.get("loaded", False),
                parameters=classifier_info.get("parameters", 0),
                device=classifier_info.get("device", "unknown")
            )
        
        # Build processing stats
        processing = ProcessingStats(
            processed_chunks=processing_stats.get("processed_chunks", 0),
            total_processing_time=processing_stats.get("total_processing_time", 0.0),
            average_processing_time=processing_stats.get("average_processing_time", 0.0),
            real_time_factor=processing_stats.get("real_time_factor", 0.0)
        )
        
        # Determine overall status
        all_models_loaded = all(model.loaded for model in models.values()) if models else False
        system_status = "healthy" if all_models_loaded else "degraded"
        
        return SystemStatus(
            status=system_status,
            uptime=uptime,
            models=models,
            processing=processing
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get system status: {str(e)}"
        )

# System start time initialized at module level for uptime calculation

@router.post("/configuration", tags=["system"])
async def update_configuration(
    config: ConfigurationUpdate = Body(..., description="Configuration updates to apply"),
    settings: Settings = Depends(get_settings)
):
    """
    Update system configuration (demo endpoint)
    
    Args:
        config: Configuration parameters to update
        
    Returns:
        Status of configuration update
    """
    try:
        updated_fields = []
        
        if config.log_level is not None:
            # In real implementation, would update log level
            updated_fields.append(f"log_level -> {config.log_level}")
            
        if config.enable_debug is not None:
            # In real implementation, would toggle debug mode
            updated_fields.append(f"debug_mode -> {config.enable_debug}")
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "updated_fields": updated_fields,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update configuration: {str(e)}"
        )

@router.get("/models/{model_type}/performance", tags=["models"])
async def get_model_performance(
    model_type: str = Path(..., description="Model type (asr or classifier)"),
    include_details: bool = Query(False, description="Include detailed performance metrics")
):
    """
    Get performance metrics for a specific model
    
    Args:
        model_type: Type of model to query (asr/classifier)
        include_details: Whether to include detailed metrics
        
    Returns:
        Performance metrics for the specified model
    """
    if model_type not in ["asr", "classifier"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model type must be 'asr' or 'classifier'"
        )
    
    try:
        audio_processor = get_audio_processor()
        processing_stats = audio_processor.get_processing_stats()
        
        # Simulate model-specific performance data
        base_metrics = {
            "model_type": model_type,
            "processed_requests": processing_stats.get("processed_chunks", 0),
            "average_processing_time": processing_stats.get("average_processing_time", 0.0),
            "success_rate": 0.98,  # Simulated
            "timestamp": time.time()
        }
        
        if include_details:
            base_metrics.update({
                "detailed_metrics": {
                    "min_processing_time": 0.05,  # Simulated
                    "max_processing_time": 2.1,   # Simulated
                    "p95_processing_time": 0.8,   # Simulated
                    "memory_usage_mb": 512 if model_type == "asr" else 256,
                    "gpu_utilization": 0.75 if model_type == "asr" else 0.45
                }
            })
        
        return base_metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get {model_type} performance metrics: {str(e)}"
        )