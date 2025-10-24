#!/usr/bin/env python3
"""
Backend Runner - Vietnamese STT Demo
Script để chạy backend server với các tùy chọn khác nhau
"""

import sys
import subprocess
import argparse
from pathlib import Path

def check_models():
    """Kiểm tra models có sẵn"""
    models = [
        "../PhoWhisper-small",
        "../phobert-vi-comment-4class"
    ]

    missing_models = []
    for model in models:
        model_path = Path(model)
        if not model_path.exists():
            missing_models.append(model)
        else:
            # Check if it has required files
            if not (model_path / "config.json").exists():
                missing_models.append(model)

    return missing_models

def run_backend_dev():
    """Chạy backend trong development mode"""
    print("🚀 Starting Backend in Development Mode...")
    
    # Check models
    missing_models = check_models()
    if missing_models:
        print(f"⚠️  Missing models: {', '.join(missing_models)}")
        print("Run 'python ../setup.py' to download models first")
        return False
    
    try:
        # Run uvicorn with reload
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ], check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start backend: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
        return True

def run_backend_prod():
    """Chạy backend trong production mode"""
    print("🚀 Starting Backend in Production Mode...")
    
    # Check models
    missing_models = check_models()
    if missing_models:
        print(f"⚠️  Missing models: {', '.join(missing_models)}")
        print("Run 'python ../setup.py' to download models first")
        return False
    
    try:
        # Run uvicorn without reload
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--workers", "4",
            "--log-level", "info"
        ], check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start backend: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
        return True

def run_backend_https():
    """Chạy backend với HTTPS"""
    print("🚀 Starting Backend with HTTPS...")
    
    # Check models
    missing_models = check_models()
    if missing_models:
        print(f"⚠️  Missing models: {', '.join(missing_models)}")
        print("Run 'python ../setup.py' to download models first")
        return False
    
    # Check for SSL certificates
    cert_file = Path("ssl/cert.pem")
    key_file = Path("ssl/key.pem")
    
    if not cert_file.exists() or not key_file.exists():
        print("❌ SSL certificates not found!")
        print("Please generate SSL certificates first:")
        print("  mkdir ssl")
        print("  openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes")
        return False
    
    try:
        # Run uvicorn with SSL
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--reload",
            "--ssl-keyfile", str(key_file),
            "--ssl-certfile", str(cert_file),
            "--log-level", "info"
        ], check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start backend with HTTPS: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
        return True

def run_backend_simple():
    """Chạy backend đơn giản (fallback)"""
    print("🚀 Starting Backend in Simple Mode...")
    
    try:
        # Run simple backend
        subprocess.run([
            sys.executable, "simple_backend.py"
        ], check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start simple backend: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
        return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Vietnamese STT Demo Backend Runner")
    parser.add_argument(
        "--mode", 
        choices=["dev", "prod", "https", "simple"], 
        default="dev",
        help="Backend mode: dev (development), prod (production), https (with SSL), simple (fallback)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    print("🎤 Vietnamese STT Demo - Backend Runner")
    print("=" * 50)
    print(f"Mode: {args.mode}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    import os
    os.chdir(backend_dir)
    
    # Run based on mode
    success = False
    
    if args.mode == "dev":
        success = run_backend_dev()
    elif args.mode == "prod":
        success = run_backend_prod()
    elif args.mode == "https":
        success = run_backend_https()
    elif args.mode == "simple":
        success = run_backend_simple()
    
    if success:
        print("✅ Backend stopped successfully")
    else:
        print("❌ Backend stopped with errors")
        sys.exit(1)

if __name__ == "__main__":
    main()
