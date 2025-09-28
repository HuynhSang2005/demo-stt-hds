#!/usr/bin/env python3
"""
FastAPI Main Application
Entry point cho Vietnamese Speech-to-Text + Toxic Detection API

Features:
- FastAPI application setup với CORS middleware
- Lifespan events để load models during startup
- WebSocket và REST API routing
- Structured logging integration
- Health checks và monitoring endpoints
- Error handling và middleware
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Backend imports
from .core.config import Settings, get_settings, print_model_status
from .core.logger import configure_structlog, AppLogger, WebSocketLogger
from .services.audio_processor import get_audio_processor, AudioProcessor
from .api.v1.endpoints import router as websocket_router

# Initialize settings
settings = get_settings()

# Configure logging
configure_structlog(
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT
)

# Initialize loggers
app_logger = AppLogger("fastapi_main")
websocket_logger = WebSocketLogger("fastapi_websocket")

# Global references
audio_processor: Optional[AudioProcessor] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager
    Handles startup và shutdown events cho model loading
    """
    startup_start = time.time()
    
    try:
        app_logger.log_startup({
            "service": "fastapi_backend",
            "version": settings.VERSION,
            "debug_mode": settings.DEBUG,
            "asr_model_path": settings.ASR_MODEL_PATH,
            "classifier_model_path": settings.CLASSIFIER_MODEL_PATH
        })
        
        # Validate model paths before loading
        validation = settings.validate_model_paths()
        if not all([
            validation["asr_exists"],
            validation["classifier_exists"], 
            validation["asr_has_config"],
            validation["classifier_has_config"]
        ]):
            error_msg = f"Model validation failed: {validation}"
            app_logger.logger.error("model_validation_failed", validation=validation)
            raise RuntimeError(error_msg)
        
        # Initialize audio processor (loads models)
        app_logger.logger.info("initializing_audio_processor", event_type="startup_models")
        global audio_processor
        audio_processor = get_audio_processor(settings)
        
        # Verify models loaded successfully
        model_info = audio_processor.get_model_info()
        if not model_info.get("processor_ready", False):
            raise RuntimeError("Audio processor not ready after initialization")
        
        startup_time = time.time() - startup_start
        
        app_logger.logger.info(
            "fastapi_startup_complete",
            startup_time=startup_time,
            models_loaded=model_info["processor_ready"],
            asr_parameters=model_info["asr_model"].get("parameters", 0),
            classifier_parameters=model_info["classifier_model"].get("parameters", 0),
            event_type="startup_complete"
        )
        
        print("🚀 FASTAPI BACKEND STARTED SUCCESSFULLY!")
        print(f"   - Startup time: {startup_time:.2f}s")
        print(f"   - ASR model: {model_info['asr_model']['loaded']}")  
        print(f"   - Classifier model: {model_info['classifier_model']['loaded']}")
        print(f"   - WebSocket endpoint: {settings.WEBSOCKET_ENDPOINT}")
        print(f"   - Server: http://{settings.HOST}:{settings.PORT}")
        
        # Application is ready
        yield
        
    except Exception as e:
        app_logger.logger.error(
            "fastapi_startup_failed",
            error=str(e),
            event_type="startup_error"
        )
        print(f"❌ FASTAPI STARTUP FAILED: {e}")
        raise
    
    finally:
        # Shutdown cleanup
        app_logger.log_shutdown()
        print("🛑 FASTAPI BACKEND SHUTDOWN COMPLETE")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted host middleware (security)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[settings.HOST, "localhost", "127.0.0.1"]
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests với structured logging"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Log request details
    process_time = time.time() - start_time
    
    app_logger.logger.info(
        "http_request",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
        client_host=request.client.host if request.client else None,
        event_type="http_request"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Include WebSocket router
app.include_router(
    websocket_router,
    prefix=settings.API_V1_STR,
    tags=["WebSocket Audio Processing"]
)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint với service information
    """
    try:
        # Get audio processor status
        processor_info = {}
        if audio_processor:
            processor_info = audio_processor.get_model_info()
            processing_stats = audio_processor.get_processing_stats()
        else:
            processing_stats = {}
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "service": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "status": "online",
                "description": settings.DESCRIPTION,
                "endpoints": {
                    "websocket": f"{settings.API_V1_STR}/ws",
                    "websocket_status": f"{settings.API_V1_STR}/ws/status", 
                    "health": f"{settings.API_V1_STR}/health",
                    "docs": "/docs" if settings.DEBUG else None
                },
                "models": processor_info,
                "processing_stats": processing_stats,
                "timestamp": time.time()
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "service_info_failed",
                "message": f"Failed to get service information: {e}"
            }
        )

# System info endpoint
@app.get("/info")
async def system_info():
    """
    Detailed system information endpoint
    """
    try:
        # Model validation
        validation = settings.validate_model_paths()
        model_paths = settings.get_model_paths()
        
        # Audio processor info
        processor_ready = False
        processor_stats = {}
        model_details = {}
        
        if audio_processor:
            model_details = audio_processor.get_model_info()
            processor_stats = audio_processor.get_processing_stats()
            processor_ready = model_details.get("processor_ready", False)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "system": {
                    "service": settings.PROJECT_NAME,
                    "version": settings.VERSION,
                    "debug_mode": settings.DEBUG,
                    "host": settings.HOST,
                    "port": settings.PORT
                },
                "models": {
                    "asr_path": str(model_paths["asr"]),
                    "classifier_path": str(model_paths["classifier"]),
                    "validation": validation,
                    "details": model_details,
                    "processor_ready": processor_ready
                },
                "configuration": {
                    "target_sample_rate": settings.TARGET_SAMPLE_RATE,
                    "min_audio_duration": settings.MIN_AUDIO_DURATION,
                    "max_audio_duration": settings.MAX_AUDIO_DURATION,
                    "cors_origins": settings.cors_origins_list,
                    "websocket_endpoint": settings.WEBSOCKET_ENDPOINT
                },
                "statistics": processor_stats,
                "timestamp": time.time()
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "system_info_failed", 
                "message": f"Failed to get system information: {e}"
            }
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler với structured logging
    """
    app_logger.logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
        method=request.method,
        event_type="global_exception"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.DEBUG else None
        }
    )

# Development helper function
def print_startup_info():
    """Print startup information for development"""
    print("=" * 60)
    print("🚀 VIETNAMESE SPEECH-TO-TEXT + TOXIC DETECTION API")
    print("=" * 60)
    print(f"Service: {settings.PROJECT_NAME}")
    print(f"Version: {settings.VERSION}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"WebSocket: ws://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}/ws")
    print(f"Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)
    print("📊 MODEL CONFIGURATION:")
    print_model_status()
    print("=" * 60)

# Main entry point
if __name__ == "__main__":
    # Print startup info
    print_startup_info()
    
    # Run server
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG
    )