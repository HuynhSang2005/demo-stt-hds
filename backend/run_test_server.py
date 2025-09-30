#!/usr/bin/env python3
"""
Simple test server startup script
Run FastAPI server for testing WebSocket connectivity without ML models
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    import uvicorn
    from app.main_simple import app
    
    # Print startup info
    print("🚀 STARTING VIETNAMESE STT TEST SERVER (No ML Models)")
    print("=" * 70)
    print(f"📂 Working Directory: {current_dir}")
    print(f"🌐 Server URL: http://127.0.0.1:8000")
    print(f"📡 WebSocket: ws://127.0.0.1:8000/v1/ws")
    print(f"📚 API Docs: http://127.0.0.1:8000/docs")
    print("=" * 70)
    
    # Run server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True
    )