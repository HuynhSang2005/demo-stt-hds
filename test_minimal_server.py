#!/usr/bin/env python3
"""
Minimal FastAPI server để test WebSocket route riêng biệt
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import asyncio
import uvicorn

app = FastAPI(title="Minimal WebSocket Test")

@app.get("/")
async def root():
    return {"message": "Minimal WebSocket Test Server"}

@app.websocket("/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Simple WebSocket test endpoint"""
    try:
        print("🔗 WebSocket connection attempt...")
        await websocket.accept()
        print("✅ WebSocket accepted")
        
        while True:
            try:
                # Receive any data
                data = await websocket.receive_bytes()
                print(f"📩 Received {len(data)} bytes")
                
                # Send back simple response
                response = {
                    "text": "Test response",
                    "bytes_received": len(data),
                    "status": "success"
                }
                
                await websocket.send_json(response)
                print(f"📤 Sent response: {response}")
                
            except Exception as e:
                print(f"❌ WebSocket loop error: {e}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting minimal WebSocket test server...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")