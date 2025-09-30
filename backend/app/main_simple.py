#!/usr/bin/env python3
"""
Simple main.py for testing WebSocket connectivity without ML models
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Create FastAPI app
app = FastAPI(
    title="Vietnamese STT + Toxic Detection API",
    description="Offline-first Vietnamese speech-to-text with sentiment analysis",
    version="1.0.0"
)

# Configure CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Vietnamese STT Backend is running"}

# Include WebSocket router
from .api.v1.endpoints_simple_test import router as websocket_router
app.include_router(websocket_router, prefix="/v1")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Vietnamese STT Backend Started Successfully")
    logger.info("📡 WebSocket endpoint available at: ws://127.0.0.1:8000/v1/ws")
    logger.info("📚 API Documentation available at: http://127.0.0.1:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Vietnamese STT Backend Shutting Down")