#!/usr/bin/env python3
"""
WebSocket API Endpoints - FastAPI Backend
Real-time WebSocket endpoints for audio processing

Features:
- WebSocket endpoint /v1/ws cho real-time audio streaming
- Binary audio chunk processing
- JSON response theo API contract
- Connection management và error handling
- Real-time status updates
- Performance monitoring
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import json
import time
from typing import Dict, Any, Optional, List
import asyncio

# Backend imports
from ...core.config import Settings, get_settings
from ...core.logger import WebSocketLogger, AudioProcessingLogger
from ...services.audio_processor import AudioProcessor, get_audio_processor, AudioProcessorError
from ...schemas.audio import (
    TranscriptResult, 
    ErrorResponse, 
    ConnectionStatus,
    ProcessingStatus,
    WebSocketMessage,
    create_websocket_message,
    create_error_response
)

# Initialize router
router = APIRouter()

# Initialize loggers
websocket_logger = WebSocketLogger("websocket_endpoints")
audio_logger = AudioProcessingLogger("websocket_audio")

# Active connections tracking
class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Generate client ID if not provided
        if client_id is None:
            client_id = f"client_{int(time.time() * 1000)}"
        
        # Store connection info
        self.connection_info[client_id] = {
            "websocket": websocket,
            "connected_at": time.time(),
            "processed_chunks": 0,
            "total_processing_time": 0.0
        }
        
        websocket_logger.log_connection_accepted(
            client_host=getattr(websocket.client, 'host', None) if websocket.client else None
        )
        
        return client_id
    
    def disconnect(self, websocket: WebSocket, client_id: Optional[str] = None) -> None:
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if client_id and client_id in self.connection_info:
            del self.connection_info[client_id]
        
        websocket_logger.log_websocket_disconnection(
            client_id=client_id,
            reason="client_disconnect"
        )
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Send JSON message to WebSocket"""
        try:
            await websocket.send_json(message)
            websocket_logger.log_message_sent(
                message_type=message.get('message_type', 'unknown'),
                message_size=len(json.dumps(message))
            )
        except Exception as e:
            websocket_logger.log_error(f"Failed to send message: {e}")
    
    async def send_error(self, websocket: WebSocket, error: ErrorResponse) -> None:
        """Send error response to WebSocket"""
        error_message = create_websocket_message(
            msg_type="error",
            data=error.dict()
        )
        await self.send_message(websocket, error_message.dict())
    
    async def send_transcript_result(self, websocket: WebSocket, result: TranscriptResult) -> None:
        """Send transcript result to WebSocket"""
        result_message = create_websocket_message(
            msg_type="transcription_result",
            data=result.dict()
        )
        await self.send_message(websocket, result_message.dict())
    
    async def send_status(self, websocket: WebSocket, status: ConnectionStatus) -> None:
        """Send connection status to WebSocket"""
        status_message = create_websocket_message(
            msg_type="connection_status",
            data=status.dict()
        )
        await self.send_message(websocket, status_message.dict())
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "total_connections": len(self.connection_info),
            "connection_details": {
                client_id: {
                    "connected_at": info["connected_at"],
                    "processed_chunks": info["processed_chunks"],
                    "total_processing_time": info["total_processing_time"]
                }
                for client_id, info in self.connection_info.items()
            }
        }

# Global connection manager
connection_manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    audio_processor: AudioProcessor = Depends(get_audio_processor)
):
    """
    Real-time WebSocket endpoint for audio processing
    """
    # Generate unique client ID for this connection
    import uuid
    client_id = str(uuid.uuid4())
    
    try:
        print(f"🔗 WebSocket connection attempt for client {client_id}...")
        await websocket.accept()
        print(f"✅ WebSocket accepted for client {client_id}")
        
        # Register connection with manager
        client_id = await connection_manager.connect(websocket, client_id)
        
        # Send simple status message
        await websocket.send_json({"status": "connected", "message": "WebSocket ready"})
        print("📤 Sent status message")
        
        while True:
            try:
                # Receive any data
                data = await websocket.receive_bytes()
                print(f"📩 Received {len(data)} bytes")
                
                # Send back simple response (just echo info, no processing)
                response = {
                    "text": "Debug response - no processing",
                    "bytes_received": len(data),
                    "status": "debug_mode"
                }
                
                await websocket.send_json(response)
                print(f"📤 Sent response: {response}")
                
            except Exception as loop_error:
                print(f"❌ WebSocket loop error: {loop_error}")
                break
        
        # Debug mode - simple connection
        
        # Main processing loop
        while True:
            try:
                # Receive binary audio data
                audio_data = await websocket.receive_bytes()
                
                websocket_logger.log_message_received(
                    message_type="audio_chunk",
                    message_size=len(audio_data)
                )
                
                # Validate audio data
                if len(audio_data) == 0:
                    error_response = create_error_response(
                        error_type="empty_audio_chunk",
                        message="Received empty audio data"
                    )
                    await connection_manager.send_error(websocket, error_response)
                    continue
                
                # Process audio chunk
                processing_start = time.time()
                
                try:
                    print(f"🔄 Processing {len(audio_data)} bytes audio...")
                    # Use safe processing wrapper
                    result = audio_processor.process_audio_chunk_safe(audio_data)
                    print(f"✅ Processing result: {type(result)}")
                except Exception as process_error:
                    print(f"❌ Processing error: {process_error}")
                    import traceback
                    traceback.print_exc()
                    error_response = create_error_response(
                        error_type="processing_failed",
                        message=f"Audio processing failed: {str(process_error)}"
                    )
                    await connection_manager.send_error(websocket, error_response)
                    continue
                
                processing_time = time.time() - processing_start
                
                # Update connection stats
                if client_id in connection_manager.connection_info:
                    connection_manager.connection_info[client_id]["processed_chunks"] += 1
                    connection_manager.connection_info[client_id]["total_processing_time"] += processing_time
                
                # Send result back to client
                if isinstance(result, TranscriptResult):
                    await connection_manager.send_transcript_result(websocket, result)
                    
                    audio_logger.logger.info(
                        "websocket_processing_success",
                        client_id=client_id,
                        text_length=len(result.text),
                        sentiment_label=result.sentiment_label,
                        warning=result.warning,
                        processing_time=processing_time,
                        event_type="ws_success"
                    )
                    
                elif isinstance(result, ErrorResponse):
                    await connection_manager.send_error(websocket, result)
                    
                    audio_logger.logger.error(
                        "websocket_processing_error",
                        client_id=client_id,
                        error_type=result.error,
                        error_message=result.message,
                        processing_time=processing_time,
                        event_type="ws_error"
                    )
                
            except WebSocketDisconnect:
                # Client disconnected
                break
                
            except Exception as e:
                # Handle processing errors
                error_response = create_error_response(
                    error_type="processing_error",
                    message=f"Audio processing failed: {e}",
                    details={"client_id": client_id}
                )
                
                try:
                    await connection_manager.send_error(websocket, error_response)
                except:
                    # WebSocket might be closed
                    break
                
                websocket_logger.log_error(
                    error=str(e),
                    error_type="processing_exception"
                )
    
    except WebSocketDisconnect:
        # Normal disconnection
        pass
        
    except Exception as e:
        # Connection error
        websocket_logger.log_error(
            error=f"WebSocket connection error: {e}",
            error_type="connection_error"
        )
        
    finally:
        # Cleanup connection
        connection_manager.disconnect(websocket, client_id)
        
        if client_id:
            websocket_logger.log_websocket_disconnection(
                client_id=client_id,
                reason="cleanup"
            )

@router.get("/ws/status", tags=["websocket"])
async def get_websocket_status():
    """
    Get WebSocket server status và connection statistics
    
    Returns:
        JSON với connection stats và server info
    """
    try:
        connection_stats = connection_manager.get_connection_stats()
        
        # Get audio processor stats
        try:
            audio_processor = get_audio_processor()
            processor_stats = audio_processor.get_processing_stats()
            model_info = audio_processor.get_model_info()
        except:
            processor_stats = {}
            model_info = {"processor_ready": False}
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "websocket_server": {
                    "status": "running",
                    "endpoint": "/v1/ws",
                    "connections": connection_stats
                },
                "audio_processor": {
                    "ready": model_info.get("processor_ready", False),
                    "statistics": processor_stats,
                    "models": model_info
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "status_retrieval_failed",
                "message": f"Failed to get WebSocket status: {e}"
            }
        )

@router.post("/ws/broadcast", tags=["websocket"])
async def broadcast_message(
    message: WebSocketMessage,
    settings: Settings = Depends(get_settings)
):
    """
    Broadcast message to all connected WebSocket clients
    (Useful for testing và admin operations)
    
    Args:
        message: WebSocket message to broadcast
        
    Returns:
        Status of broadcast operation
    """
    try:
        broadcast_count = 0
        failed_count = 0
        
        for websocket in connection_manager.active_connections:
            try:
                await connection_manager.send_message(websocket, message.dict())
                broadcast_count += 1
            except:
                failed_count += 1
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "broadcast_status": "completed",
                "messages_sent": broadcast_count,
                "failures": failed_count,
                "total_connections": len(connection_manager.active_connections)
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "broadcast_failed",
                "message": f"Failed to broadcast message: {e}"
            }
        )

@router.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint cho WebSocket service
    
    Returns:
        Service health status
    """
    try:
        # Check audio processor health
        try:
            audio_processor = get_audio_processor()
            processor_healthy = audio_processor.get_model_info().get("processor_ready", False)
        except:
            processor_healthy = False
        
        health_status = {
            "service": "websocket_endpoints",
            "status": "healthy" if processor_healthy else "degraded",
            "timestamp": time.time(),
            "checks": {
                "audio_processor": processor_healthy,
                "websocket_connections": len(connection_manager.active_connections)
            }
        }
        
        status_code = status.HTTP_200_OK if processor_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "service": "websocket_endpoints",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )