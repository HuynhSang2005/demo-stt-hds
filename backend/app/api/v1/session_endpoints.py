#!/usr/bin/env python3
"""
Session-based WebSocket API Endpoints - FastAPI Backend
Real-time WebSocket endpoints with session management for complete recording processing

Features:
- Session-based audio accumulation
- WebSocket endpoint /v1/ws/session for session mode
- Binary audio chunk collection
- Complete session processing
- Connection management và error handling
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import time
from typing import Dict, Any, Optional
import asyncio

# Backend imports
from ...core.config import get_settings
from ...core.logger import WebSocketLogger, AudioProcessingLogger
from ...services.audio_processor import AudioProcessor, get_audio_processor
from ...services.session_processor import SessionAudioProcessor
from ...schemas.audio import (
    TranscriptResult, 
    SessionCommand,
    SessionResponse,
    create_websocket_message,
    create_error_response
)

# Initialize router
router = APIRouter()

# Initialize loggers
websocket_logger = WebSocketLogger("session_websocket")
audio_logger = AudioProcessingLogger("session_audio")

# Global session processor instance
_session_processor: Optional[SessionAudioProcessor] = None


async def get_session_processor() -> SessionAudioProcessor:
    """Get or create session processor instance"""
    global _session_processor
    
    if _session_processor is None:
        # Get AudioProcessor instance which has the models
        audio_processor = get_audio_processor()
        
        # Ensure models are loaded
        if not audio_processor.asr_model or not audio_processor.classifier_model:
            raise RuntimeError("Audio processor models not initialized")
        
        # Create session processor using models from audio processor
        _session_processor = SessionAudioProcessor(
            asr_model=audio_processor.asr_model,
            classifier=audio_processor.classifier_model,
            session_timeout=30.0,  # 30 seconds
            max_session_duration=300.0  # 5 minutes
        )
        
        print("✅ Session processor initialized")
    
    return _session_processor


class SessionConnectionManager:
    """WebSocket connection manager for sessions"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_sessions: Dict[str, str] = {}  # client_id -> session_id
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect new client"""
        self.active_connections[client_id] = websocket
        print(f"Session client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Disconnect client"""
        self.active_connections.pop(client_id, None)
        self.client_sessions.pop(client_id, None)
        print(f"Session client {client_id} disconnected")
    
    def set_client_session(self, client_id: str, session_id: Optional[str]):
        """Associate client with session"""
        if session_id is None:
            self.client_sessions.pop(client_id, None)
        else:
            self.client_sessions[client_id] = session_id
    
    def get_client_session(self, client_id: str) -> Optional[str]:
        """Get session ID for client"""
        return self.client_sessions.get(client_id)


# Global connection manager
session_manager = SessionConnectionManager()


@router.websocket("/session")
async def session_websocket_endpoint(
    websocket: WebSocket,
):
    """
    Session-based WebSocket endpoint for audio processing
    Accumulates audio chunks and processes complete recordings
    """
    # Generate unique client ID
    import uuid
    client_id = str(uuid.uuid4())
    
    try:
        print(f"🔗 Session WebSocket connection attempt for client {client_id}...")
        await websocket.accept()
        print(f"✅ Session WebSocket accepted for client {client_id}")
        
        # Get session processor
        session_processor = await get_session_processor()
        
        # Register connection
        await session_manager.connect(websocket, client_id)
        
        # Send connection status
        try:
            await websocket.send_json({
                "type": "connection_status",
                "status": "connected", 
                "message": "Session WebSocket ready for audio processing",
                "mode": "session"
            })
        except Exception as e:
            print(f"❌ Failed to send connection status: {e}")
            return
        
        # Main processing loop
        while True:
            try:
                # Check if WebSocket is still connected
                if websocket.client_state.name != "CONNECTED":
                    print(f"❌ WebSocket not connected (state: {websocket.client_state.name})")
                    break
                    
                # Receive data - use receive() to auto-detect message type
                message = await websocket.receive()
                
                # Handle based on message type
                if message["type"] == "websocket.receive" and "text" in message:
                    # JSON message (session command)
                    try:
                        import json
                        data = json.loads(message["text"])
                        
                        if data.get("type") == "session_command":
                            await handle_session_command(
                                websocket, client_id, data, session_processor
                            )
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "error_type": "unknown_message_type",
                                "message": "Expected session_command or audio data"
                            })
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "error_type": "json_decode_error",
                            "message": f"Invalid JSON: {str(e)}"
                        })
                        
                elif message["type"] == "websocket.receive" and "bytes" in message:
                    # Binary message (audio data)
                    audio_data = message["bytes"]
                    
                    # Handle audio chunk
                    current_session = session_manager.get_client_session(client_id)
                    
                    if current_session is None:
                        # Auto-create session for audio chunks
                        current_session = session_processor.create_session()
                        session_manager.set_client_session(client_id, current_session)
                        
                        # Notify client of new session
                        try:
                            await websocket.send_json({
                                "type": "session_response",
                                "success": True,
                                "session_id": current_session,
                                "message": "Auto-created session for audio chunk"
                            })
                        except Exception as e:
                            print(f"⚠️ Failed to send auto-session response: {e}")
                            break
                    
                    # Add chunk to session
                    success = session_processor.add_chunk(current_session, audio_data)
                    
                    if success:
                        print(f"📩 Added {len(audio_data)} bytes to session {current_session}")
                        
                        # Send acknowledgment
                        try:
                            await websocket.send_json({
                                "type": "processing_status",
                                "status": "chunk_received",
                                "session_id": current_session,
                                "chunk_size": len(audio_data)
                            })
                        except Exception as e:
                            print(f"⚠️ Failed to send chunk acknowledgment: {e}")
                            break
                    else:
                        try:
                            await websocket.send_json({
                                "type": "error",
                                "error_type": "invalid_session",
                                "message": f"Failed to add chunk to session {current_session}"
                            })
                        except Exception as e:
                            print(f"⚠️ Failed to send error response: {e}")
                            break
                            
                else:
                    print(f"❌ Unknown message type: {message.get('type')}")
                    break
                
            except WebSocketDisconnect:
                print(f"🔌 Session client {client_id} disconnected")
                break
            except Exception as e:
                print(f"❌ Session processing error: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "error_type": "processing_error",
                        "message": str(e)
                    })
                except:
                    # Connection might be closed, break the loop
                    break
    
    finally:
        # Clean up
        current_session = session_manager.get_client_session(client_id)
        if current_session:
            # Finalize session if exists
            try:
                session_processor = await get_session_processor()
                result = await session_processor.finalize_session(current_session)
                if result:
                    # Try to send final result
                    try:
                        await websocket.send_json({
                            "type": "transcription_result",
                            "result": result.dict()
                        })
                    except:
                        pass  # Connection might be closed
            except Exception as e:
                print(f"Error finalizing session {current_session}: {e}")
        
        session_manager.disconnect(client_id)
        print(f"🧹 Cleaned up session client {client_id}")


async def handle_session_command(
    websocket: WebSocket, 
    client_id: str, 
    message: Dict[str, Any],
    session_processor: SessionAudioProcessor
):
    """Handle session management commands"""
    
    try:
        command = message.get("command")
        session_id = message.get("session_id")
        
        if command == "start_session":
            # Create new session
            new_session_id = session_processor.create_session()
            session_manager.set_client_session(client_id, new_session_id)
            
            try:
                await websocket.send_json({
                    "type": "session_response",
                    "success": True,
                    "session_id": new_session_id,
                    "message": "New session created"
                })
            except Exception as e:
                print(f"⚠️ Failed to send session start response: {e}")
                raise
        
        elif command == "end_session":
            current_session = session_manager.get_client_session(client_id)
            
            if current_session:
                # Process and finalize session
                result = await session_processor.finalize_session(current_session)
                session_manager.set_client_session(client_id, None)
                
                if result:
                    # Only send transcription_result, not separate session_response
                    await websocket.send_json({
                        "type": "transcription_result",
                        "result": result.dict()
                    })
                else:
                    # Send error if no result
                    await websocket.send_json({
                        "type": "session_response",
                        "success": False,
                        "session_id": current_session,
                        "message": "Session processed but no result available"
                    })
            else:
                await websocket.send_json({
                    "type": "session_response",
                    "success": False,
                    "message": "No active session to end"
                })
        
        elif command == "get_session_info":
            current_session = session_manager.get_client_session(client_id)
            
            if current_session:
                session_info = session_processor.get_session_info(current_session)
                await websocket.send_json({
                    "type": "session_response",
                    "success": True,
                    "session_id": current_session,
                    "session_info": session_info
                })
            else:
                await websocket.send_json({
                    "type": "session_response",
                    "success": False,
                    "message": "No active session"
                })
        
        else:
            await websocket.send_json({
                "type": "session_response",
                "success": False,
                "message": f"Unknown command: {command}"
            })
    
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error_type": "command_error",
            "message": f"Error processing command: {str(e)}"
        })


# Health check endpoint
@router.get("/session/health")
async def session_health_check():
    """Health check for session processor"""
    try:
        session_processor = await get_session_processor()
        active_sessions = session_processor.list_active_sessions()
        
        return {
            "status": "healthy",
            "session_processor": "initialized",
            "active_sessions": len(active_sessions),
            "timestamp": int(time.time() * 1000)
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": int(time.time() * 1000)
        }