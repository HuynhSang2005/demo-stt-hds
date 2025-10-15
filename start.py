#!/usr/bin/env python3
"""
Vietnamese STT Demo - Quick Start Script
Khởi động cả backend và frontend cho demo
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_requirements():
    """Kiểm tra requirements cần thiết"""
    print("🔍 Checking requirements...")
    
    # Check Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check Node.js (with shell=True for Windows)
    try:
        shell = os.name == 'nt'
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, shell=shell)
        if result.returncode != 0:
            print("❌ Node.js not found")
            return False
        print(f"✅ Node.js {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Node.js not found")
        return False
    
    # Check npm (with shell=True for Windows)
    try:
        shell = os.name == 'nt'
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, shell=shell)
        if result.returncode != 0:
            print("❌ npm not found")
            return False
        print(f"✅ npm {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ npm not found")
        return False
    
    return True

def check_dependencies():
    """Kiểm tra dependencies đã cài đặt chưa"""
    print("\n📦 Checking dependencies...")
    
    # Check backend dependencies
    backend_dir = Path("backend")
    if backend_dir.exists():
        requirements_file = backend_dir / "requirements.txt"
        if not requirements_file.exists():
            print("❌ Backend requirements.txt not found")
            return False
        print("✅ Backend requirements.txt found")
    
    # Check frontend dependencies
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        package_json = frontend_dir / "package.json"
        node_modules = frontend_dir / "node_modules"
        if not package_json.exists():
            print("❌ Frontend package.json not found")
            return False
        if not node_modules.exists():
            print("⚠️  Frontend dependencies not installed")
            print("   Run: cd frontend && npm install")
            return False
        print("✅ Frontend dependencies found")
    
    return True

def start_backend():
    """Khởi động backend"""
    print("\n🚀 Starting backend...")
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return None
    
    # Start backend in new process
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ], cwd=backend_dir)
    
    print("✅ Backend starting on http://localhost:8000")
    return process

def start_frontend():
    """Khởi động frontend"""
    print("\n🎨 Starting frontend...")
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return None
    
    # Start frontend in new process (with shell=True for Windows)
    shell = os.name == 'nt'
    process = subprocess.Popen([
        "npm", "run", "dev"
    ], cwd=frontend_dir, shell=shell)
    
    print("✅ Frontend starting on http://localhost:5173")
    return process

def main():
    """Main function"""
    print("🎤 Vietnamese STT Demo - Quick Start")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies check failed")
        print("Please run setup first:")
        print("  python setup.py")
        return
    
    # Start services
    backend_process = start_backend()
    if backend_process is None:
        return
    
    # Wait a bit for backend to start
    print("\n⏳ Waiting for backend to start...")
    time.sleep(5)
    
    frontend_process = start_frontend()
    if frontend_process is None:
        backend_process.terminate()
        return
    
    print("\n🎉 Demo is ready!")
    print("📱 Frontend: http://localhost:5173")
    print("🔧 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop...")
    
    try:
        # Wait for processes
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print("✅ Services stopped")

if __name__ == "__main__":
    main()
