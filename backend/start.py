#!/usr/bin/env python3
"""
Simple Backend Starter - Vietnamese STT Demo
Script đơn giản để chạy backend server
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Chạy backend server"""
    print("🎤 Vietnamese STT Demo - Backend")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the backend directory")
        print("   cd backend && python start.py")
        sys.exit(1)
    
    # Check models
    models = ["PhoWhisper-small", "phobert-vi-comment-4class"]
    missing_models = []
    
    for model in models:
        if not Path(model).exists():
            missing_models.append(model)
    
    if missing_models:
        print(f"⚠️  Missing models: {', '.join(missing_models)}")
        print("   Run 'python ../setup.py' to download models first")
        print("   Or run anyway to test without models")
        
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            sys.exit(1)
    
    print("🚀 Starting backend server...")
    print("   URL: http://127.0.0.1:8000")
    print("   API Docs: http://127.0.0.1:8000/docs")
    print("   WebSocket: ws://127.0.0.1:8000/v1/ws")
    print("\n   Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--reload"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
