#!/usr/bin/env python3
"""
Simple WebSocket API Endpoints - FastAPI Backend (Debug Version)
Simplified for debugging WebSocket connection issues
"""

from fastapi import APIRouter, WebSocket
import asyncio

# Initialize router
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint with audio processing integration
    """
    try:
        print("🔗 WebSocket connection attempt...")
        await websocket.accept()
        print("✅ WebSocket accepted")
        
        # Get audio processor from global instance
        from app.main import audio_processor
        
        if audio_processor is None:
            await websocket.send_json({
                "error": "Audio processor not ready",
                "status": "error"
            })
            return
            
        # Send ready status
        await websocket.send_json({"status": "connected", "message": "Vietnamese STT + Toxic Detection ready"})
        print("📤 Sent status message")
        
        while True:
            try:
                # Receive audio data
                message = await websocket.receive()
                
                # Handle different message types
                if message['type'] == 'websocket.receive' and 'bytes' in message:
                    audio_data = message['bytes']
                    print(f"📩 Received {len(audio_data)} bytes audio")
                    
                    if len(audio_data) == 0:
                        continue
                    
                    try:
                        # Process audio with real pipeline
                        print("🔄 Processing audio...")
                        result = audio_processor.process_audio_bytes(audio_data)
                        
                        # Convert to dict for JSON response
                        response = {
                            "text": result.text,
                            "label": result.sentiment_label,
                            "confidence": result.sentiment_confidence,
                            "is_toxic": result.warning,  # True if toxic/negative
                            "processing_time": result.processing_time,
                            "timestamp": result.timestamp
                        }
                        
                        await websocket.send_json(response)
                        print(f"✅ Sent result: text='{result.text[:50]}...', toxic={result.warning}")
                        
                    except Exception as process_error:
                        print(f"❌ Audio processing error: {process_error}")
                        # Send error response
                        error_response = {
                            "text": "[PROCESSING_ERROR]",
                            "label": "error", 
                            "confidence": 0.0,
                            "is_toxic": False,
                            "processing_time": 0.0,
                            "error": str(process_error),
                            "timestamp": 0
                        }
                        await websocket.send_json(error_response)
                
            except Exception as loop_error:
                print(f"❌ WebSocket loop error: {loop_error}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

@router.get("/status")
async def websocket_status():
    """Simple status endpoint"""
    return {"websocket_status": "available", "endpoint": "/v1/ws"}