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
import uuid
from typing import Dict, Any, Optional, List
import asyncio

# Backend imports
from ...core.config import Settings, get_settings
from ...core.logger import WebSocketLogger, AudioProcessingLogger
from ...services.audio_processor import AudioProcessor, get_audio_processor, AudioProcessorError
from ...services.async_audio_processor import OptimizedAsyncAudioProcessor
from ...services.processor_factory import get_audio_processor as get_optimized_processor
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

# Global optimized processor instance
_optimized_processor: Optional[OptimizedAsyncAudioProcessor] = None

async def get_optimized_audio_processor() -> OptimizedAsyncAudioProcessor:
    """Get optimized audio processor instance"""
    global _optimized_processor
    if _optimized_processor is None:
        _optimized_processor = await get_optimized_processor()
    return _optimized_processor

# Initialize loggers
websocket_logger = WebSocketLogger("websocket_endpoints")
audio_logger = AudioProcessingLogger("websocket_audio")

# Active connections tracking
class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[str, Dict[str, Any]] = {}
        # Session buffer: session_id -> List[audio_bytes]
        self.session_buffers: Dict[str, List[bytes]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """Register WebSocket connection (already accepted by endpoint)"""
        # NOTE: websocket.accept() is called by the endpoint BEFORE this method
        # Do NOT accept here to avoid ASGI protocol violation (double accept)
        self.active_connections.append(websocket)
        
        # Generate client ID if not provided
        if client_id is None:
            client_id = f"client_{int(time.time() * 1000)}"
        
        # Store connection info
        self.connection_info[client_id] = {
            "websocket": websocket,
            "connected_at": time.time(),
            "processed_chunks": 0,
            "total_processing_time": 0.0,
            "current_session_id": None  # Track active session for this connection
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
            data=error.model_dump(mode='json')
        )
        await self.send_message(websocket, error_message.model_dump(mode='json'))
    
    async def send_transcript_result(self, websocket: WebSocket, result: TranscriptResult) -> None:
        """Send transcript result to WebSocket"""
        result_message = create_websocket_message(
            msg_type="transcription_result",
            data=result.model_dump(mode='json')
        )
        await self.send_message(websocket, result_message.model_dump(mode='json'))
    
    async def send_status(self, websocket: WebSocket, status: ConnectionStatus) -> None:
        """Send connection status to WebSocket"""
        status_message = create_websocket_message(
            msg_type="connection_status",
            data=status.model_dump(mode='json')
        )
        await self.send_message(websocket, status_message.model_dump(mode='json'))
    
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
    client_id = str(uuid.uuid4())
    
    try:
        print(f"🔗 WebSocket connection attempt for client {client_id}...")
        await websocket.accept()
        print(f"✅ WebSocket accepted for client {client_id}")
        
        # Register connection with manager
        client_id = await connection_manager.connect(websocket, client_id)
        
        # Send connection status in expected format
        await websocket.send_json({
            "type": "connection_status",
            "status": "connected",
            "message": "WebSocket ready"
        })
        print("📤 Sent connection status message")
        
        # Main processing loop
        while True:
            try:
                # Receive message (can be text or binary)
                message = await websocket.receive()
                
                # Handle text messages (JSON commands)
                if "text" in message:
                    try:
                        command_data = json.loads(message["text"])
                        print(f"📥 Received JSON command: {command_data}")
                        
                        # Handle session commands
                        if command_data.get("type") == "session_command":
                            command = command_data.get("command")
                            session_id = command_data.get("session_id")
                            
                            if command == "start_session":
                                # Generate new session ID
                                new_session_id = str(uuid.uuid4())
                                
                                # Initialize session buffer
                                connection_manager.session_buffers[new_session_id] = []
                                
                                # Set as current session for this connection
                                if client_id in connection_manager.connection_info:
                                    connection_manager.connection_info[client_id]["current_session_id"] = new_session_id
                                
                                # Send session response
                                await websocket.send_json({
                                    "type": "session_response",
                                    "success": True,
                                    "session_id": new_session_id,
                                    "message": "Session started successfully"
                                })
                                print(f"✅ Started new session: {new_session_id}, buffer created")
                                
                            elif command == "end_session":
                                print(f"🔚 Ending session: {session_id}")
                                print(f"📊 Available session buffers: {list(connection_manager.session_buffers.keys())}")
                                
                                # Get buffered audio chunks
                                if session_id in connection_manager.session_buffers:
                                    chunks = connection_manager.session_buffers[session_id]
                                    print(f"📦 Processing {len(chunks)} buffered chunks for session {session_id}")
                                    
                                    if len(chunks) > 0:
                                        # Concatenate all chunks
                                        combined_audio = b''.join(chunks)
                                        print(f"🔄 Processing {len(combined_audio)} bytes of combined audio")
                                        
                                        try:
                                            # Process combined audio
                                            result = await audio_processor.process_audio_bytes_async(combined_audio)
                                            
                                            if isinstance(result, TranscriptResult):
                                                # Send transcript result using consistent format
                                                await websocket.send_json({
                                                    "message_type": "transcription_result",
                                                    "data": result.model_dump(mode='json'),
                                                    "timestamp": time.time()
                                                })
                                                print(f"✅ Sent transcript: '{result.text[:50]}...'")
                                            else:
                                                print(f"⚠️ No transcript result from processing")
                                                await websocket.send_json({
                                                    "type": "session_response",
                                                    "success": False,
                                                    "session_id": session_id,
                                                    "message": "Failed to process audio"
                                                })
                                        except Exception as proc_error:
                                            print(f"❌ Processing error: {proc_error}")
                                            await websocket.send_json({
                                                "type": "session_response",
                                                "success": False,
                                                "session_id": session_id,
                                                "message": f"Processing failed: {str(proc_error)}"
                                            })
                                    else:
                                        print(f"⚠️ No audio chunks in session {session_id}")
                                        await websocket.send_json({
                                            "type": "session_response",
                                            "success": False,
                                            "session_id": session_id,
                                            "message": "No audio data received"
                                        })
                                    
                                    # Clean up buffer and clear current session
                                    del connection_manager.session_buffers[session_id]
                                    if client_id in connection_manager.connection_info:
                                        connection_manager.connection_info[client_id]["current_session_id"] = None
                                else:
                                    print(f"⚠️ Session {session_id} not found in buffers")
                                    await websocket.send_json({
                                        "type": "session_response",
                                        "success": False,
                                        "session_id": session_id,
                                        "message": "Session not found"
                                    })
                                
                                print(f"✅ Session {session_id} ended")
                            
                            else:
                                # Unknown command
                                await websocket.send_json({
                                    "type": "session_response",
                                    "success": False,
                                    "message": f"Unknown session command: {command}"
                                })
                                print(f"⚠️ Unknown session command: {command}")
                        
                        continue
                    except json.JSONDecodeError:
                        print(f"⚠️ Invalid JSON received: {message['text']}")
                        continue
                
                # Handle disconnect message
                if "type" in message and message["type"] == "websocket.disconnect":
                    print(f"📴 Client disconnected with code: {message.get('code', 'unknown')}")
                    break
                
                # Handle binary messages (audio data)
                if "bytes" not in message:
                    print(f"⚠️ Unexpected message format: {message}")
                    continue
                
                audio_data = message["bytes"]
                
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
                
                # Check if there's an active session for buffering
                current_session = None
                if client_id in connection_manager.connection_info:
                    current_session = connection_manager.connection_info[client_id].get("current_session_id")
                
                if current_session and current_session in connection_manager.session_buffers:
                    # Buffer audio for session processing
                    connection_manager.session_buffers[current_session].append(audio_data)
                    print(f"📦 Buffered {len(audio_data)} bytes for session {current_session} (total chunks: {len(connection_manager.session_buffers[current_session])})")
                    # Continue to process buffered audio in session mode
                    continue
                else:
                    print(f"📊 No active session - processing audio in real-time mode")
                    print(f"📊 Current session: {current_session}")
                    print(f"📊 Available buffers: {list(connection_manager.session_buffers.keys())}")
                    
                    # Process audio immediately in real-time mode
                
                # Process audio chunk (OPTIMIZED: Use async version)
                processing_start = time.time()
                
                try:
                    # Structured logging for audio processing
                    audio_logger.log_audio_chunk_received(len(audio_data))
                    audio_logger.logger.info("processing_started", event_type="pipeline_start")
                    
                    # Use ASYNC processing for better performance
                    try:
                        result = await audio_processor.process_audio_bytes_async(audio_data)
                        audio_logger.logger.info("processing_completed", event_type="pipeline_complete")
                    except Exception as async_error:
                        # Fallback to sync version if async fails
                        audio_logger.logger.error(
                            "processing_error",
                            error_message=f"Async processing failed, using sync: {async_error}",
                            error_type="async_fallback",
                            event_type="pipeline_error"
                        )
                        result = audio_processor.process_audio_chunk_safe(audio_data)
                        audio_logger.logger.info("processing_completed", event_type="pipeline_complete")
                except Exception as process_error:
                    audio_logger.logger.error(
                        "processing_error",
                        error_message=f"Audio processing failed: {str(process_error)}",
                        error_type="processing_failed",
                        event_type="pipeline_error"
                    )
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
            
            except RuntimeError as e:
                # WebSocket already closed (e.g., "Cannot call 'receive' once a disconnect message has been received")
                error_msg = str(e)
                if "disconnect" in error_msg.lower() or "close" in error_msg.lower():
                    websocket_logger.log_error(
                        error=f"WebSocket already closed: {error_msg}",
                        error_type="websocket_closed"
                    )
                    break  # Exit loop immediately without trying to send
                # Re-raise if it's a different RuntimeError
                raise
                
            except Exception as e:
                # Handle other processing errors
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
                await connection_manager.send_message(websocket, message.model_dump(mode='json'))
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

@router.websocket("/ws/optimized")
async def optimized_websocket_endpoint(
    websocket: WebSocket,
    optimized_processor: OptimizedAsyncAudioProcessor = Depends(get_optimized_audio_processor)
):
    """
    Optimized WebSocket endpoint with parallel processing
    Features:
    - Parallel ASR + Classification
    - Model caching
    - Performance metrics
    - Enhanced error handling
    """
    client_id = f"optimized_{int(time.time() * 1000)}_{id(websocket)}"
    
    try:
        await websocket.accept()
        audio_logger.logger.info(
            "optimized_websocket_connected",
            event_type="connection_established",
            client_id=client_id,
            endpoint="optimized"
        )
        
        # Add to connection manager
        connection_manager.add_connection(websocket, client_id)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_status",
            "status": "connected",
            "client_id": client_id,
            "endpoint": "optimized",
            "features": [
                "parallel_processing",
                "model_caching",
                "performance_metrics",
                "enhanced_error_handling"
            ]
        })
        
        # Process messages
        while True:
            try:
                # Receive message (text or binary)
                message = await websocket.receive()
                
                if message["type"] == "websocket.receive" and "bytes" in message:
                    # Binary message (audio data)
                    audio_data = message["bytes"]
                    
                    processing_start = time.time()
                    
                    try:
                        # Use optimized parallel processing
                        result, metrics = await optimized_processor.process_audio_parallel(
                            audio_data,
                            enable_parallel=True
                        )
                        
                        processing_time = time.time() - processing_start
                        
                        # Update connection stats
                        if client_id in connection_manager.connection_info:
                            connection_manager.connection_info[client_id]["processed_chunks"] += 1
                            connection_manager.connection_info[client_id]["total_processing_time"] += processing_time
                        
                        # Send result with performance metrics
                        response = {
                            "type": "transcript_result",
                            "data": {
                                "text": result.text,
                                "confidence": result.confidence,
                                "language": result.language,
                                "sentiment": {
                                    "label": result.sentiment_label,
                                    "score": result.sentiment_score,
                                    "is_toxic": result.is_toxic,
                                    "toxic_keywords": result.toxic_keywords
                                },
                                "processing_metrics": {
                                    "total_time_ms": metrics.total_time * 1000,
                                    "asr_time_ms": metrics.asr_time * 1000,
                                    "classification_time_ms": metrics.classification_time * 1000,
                                    "audio_duration": metrics.audio_duration,
                                    "throughput_ratio": metrics.throughput_ratio
                                }
                            },
                            "timestamp": time.time()
                        }
                        
                        await websocket.send_json(response)
                        
                        audio_logger.logger.info(
                            "optimized_processing_completed",
                            event_type="processing_complete",
                            client_id=client_id,
                            processing_time_ms=processing_time * 1000,
                            throughput_ratio=metrics.throughput_ratio
                        )
                        
                    except Exception as process_error:
                        audio_logger.logger.error(
                            "optimized_processing_failed",
                            event_type="processing_error",
                            client_id=client_id,
                            error=str(process_error)
                        )
                        
                        error_response = create_error_response(
                            error_type="processing_failed",
                            message=f"Optimized audio processing failed: {str(process_error)}"
                        )
                        await connection_manager.send_error(websocket, error_response)
                        continue
                
                elif message["type"] == "websocket.receive" and "text" in message:
                    # Text message (commands)
                    try:
                        data = json.loads(message["text"])
                        
                        if data.get("type") == "get_performance_stats":
                            # Return performance statistics
                            stats = optimized_processor.get_performance_stats()
                            await websocket.send_json({
                                "type": "performance_stats",
                                "data": stats,
                                "timestamp": time.time()
                            })
                        
                        elif data.get("type") == "ping":
                            # Heartbeat response
                            await websocket.send_json({
                                "type": "pong",
                                "timestamp": time.time()
                            })
                        
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid JSON format",
                            "timestamp": time.time()
                        })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                audio_logger.logger.error(
                    "optimized_websocket_error",
                    event_type="websocket_error",
                    client_id=client_id,
                    error=str(e)
                )
                break
    
    except Exception as e:
        audio_logger.logger.error(
            "optimized_websocket_fatal_error",
            event_type="fatal_error",
            client_id=client_id,
            error=str(e)
        )
    
    finally:
        # Cleanup
        connection_manager.remove_connection(websocket, client_id)
        audio_logger.logger.info(
            "optimized_websocket_disconnected",
            event_type="connection_closed",
            client_id=client_id
        )