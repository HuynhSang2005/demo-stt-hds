#!/usr/bin/env python3
"""
Standalone test server for WebSocket connectivity
No imports from app module to avoid ML dependencies
"""

from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
import json
import logging

# Create FastAPI app
app = FastAPI(
    title="Vietnamese STT Test Server",
    description="Simple test server for WebSocket connectivity",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_message(message_type: str, data: dict) -> dict:
    """Build standardized WebSocket message envelope."""
    return {
        "type": message_type,
        "timestamp": time.time(),
        "messageId": str(uuid.uuid4()),
        "data": data
    }


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Vietnamese STT Test Backend is running"}


@app.websocket("/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Test WebSocket endpoint for connectivity validation.
    
    Accepts binary audio data and returns mock transcript results
    to test the full pipeline without heavy ML models.
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        while True:
            # Wait for binary audio data
            audio_data = await websocket.receive_bytes()
            
            try:
                # Mock processing - simulate transcript result matching frontend schema
                import time
                import uuid
                
                mock_result = {
                    "id": str(uuid.uuid4()),
                    "text": "Xin chào, đây là một thử nghiệm WebSocket",  # Changed from "transcript"
                    "label": "neutral",  # Direct label, not nested in "sentiment"
                    "confidence": 0.85,
                    "timestamp": int(time.time() * 1000),  # Unix timestamp in milliseconds
                    "warning": False,  # Add warning field
                    "metadata": {
                        "audioChunkSize": len(audio_data),
                        "processingTime": 0.123,
                        "modelVersion": "mock-v1.0"
                    }
                }
                
                # Send structured response
                message = _build_message("transcript_result", mock_result)
                
                await websocket.send_text(json.dumps(message))
                logger.info(f"Mock processed audio data of {len(audio_data)} bytes")
                
            except Exception as e:
                # Send error response
                error_message = _build_message("error", {
                    "message": str(e),
                    "type": "processing_error"
                })
                await websocket.send_text(json.dumps(error_message))
                logger.error(f"Audio processing error: {e}")
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            error_message = _build_message("error", {
                "message": "WebSocket connection error",
                "type": "connection_error"
            })
            await websocket.send_text(json.dumps(error_message))
        except:
            pass  # Connection already closed
    finally:
        logger.info("WebSocket connection closed")


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Vietnamese STT Test Backend Started Successfully")
    logger.info("📡 WebSocket endpoint available at: ws://127.0.0.1:8000/v1/ws")
    logger.info("📚 API Documentation available at: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 STARTING VIETNAMESE STT TEST SERVER (No ML Models)")
    print("=" * 70)
    print("🌐 Server URL: http://127.0.0.1:8000")
    print("📡 WebSocket: ws://127.0.0.1:8000/v1/ws")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True
    )