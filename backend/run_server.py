#!/usr/bin/env python3
"""
Development server startup script
Run FastAPI server với proper module path resolution
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import và run main app
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    # Print startup info
    print("🚀 STARTING VIETNAMESE SPEECH-TO-TEXT + TOXIC DETECTION SERVER")
    print("=" * 70)
    print(f"📂 Working Directory: {current_dir}")
    print(f"🐍 Python Path: {sys.path[:2]}")
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