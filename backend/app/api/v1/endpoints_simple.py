#!/usr/bin/env python3
"""
Simplified WebSocket endpoint for testing connectivity without ML models
"""

from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect
import time
import uuid
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_message(message_type: str, data: dict) -> dict:
    """Build standardized WebSocket message envelope."""
    return {
        "type": message_type,
        "timestamp": time.time(),
        "messageId": str(uuid.uuid4()),
        "data": data
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Simplified WebSocket endpoint for testing connectivity.
    
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
                # Mock processing - simulate transcript result
                mock_result = {
                    "transcript": "Xin chào, đây là một thử nghiệm",
                    "confidence": 0.95,
                    "language": "vi",
                    "sentiment": {
                        "label": "neutral",
                        "confidence": 0.85,
                        "is_toxic": False
                    },
                    "processing_time": 0.123
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