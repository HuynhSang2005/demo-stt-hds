#!/usr/bin/env python3
"""
Vietnamese STT Demo - Setup Script
Cài đặt và cấu hình môi trường cho demo (backend + frontend only)
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Chạy command và xử lý kết quả"""
    print(f"Running: {' '.join(command)}")
    try:
        # On Windows, ensure we use the correct shell
        shell = os.name == 'nt'
        result = subprocess.run(command, cwd=cwd, check=check, capture_output=True, text=True, shell=shell)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError as e:
        print(f"Command not found: {e}")
        return False

def setup_backend():
    """Setup backend"""
    print("\nSetting up backend...")

    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("ERROR: Backend directory not found")
        return False

    # Install Python dependencies
    print("Installing Python dependencies...")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=backend_dir):
        print("ERROR: Failed to install backend dependencies")
        return False

    print("OK: Backend setup completed")
    return True

def setup_frontend():
    """Setup frontend"""
    print("\nSetting up frontend...")

    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("ERROR: Frontend directory not found")
        return False

    # Check if npm is available
    try:
        # On Windows, use shell=True to access npm through PATH
        shell = os.name == 'nt'
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, shell=shell)
        if result.returncode != 0:
            print("ERROR: npm not found. Please install Node.js first.")
            print("Download from: https://nodejs.org/")
            return False
        print(f"OK: npm {result.stdout.strip()} found")
    except FileNotFoundError:
        print("ERROR: npm not found. Please install Node.js first.")
        print("Download from: https://nodejs.org/")
        return False

    # Install Node.js dependencies
    print("Installing Node.js dependencies...")
    if not run_command(["npm", "install"], cwd=frontend_dir):
        print("ERROR: Failed to install frontend dependencies")
        return False

    print("OK: Frontend setup completed")
    return True

def main():
    """Main setup function"""
    print("Vietnamese STT Demo - Setup")
    print("=" * 40)
    print("This script sets up backend and frontend only.")
    print("Use setup_models.py for AI model setup.")

    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required")
        return

    print(f"OK: Python {sys.version.split()[0]}")

    # Setup backend
    if not setup_backend():
        print("\nERROR: Backend setup failed")
        return

    # Setup frontend
    if not setup_frontend():
        print("\nERROR: Frontend setup failed")
        print("You can still run backend only with: python setup_backend_only.py")
        return

    print("\nSUCCESS: Backend and frontend setup completed!")
    print("\nNext steps:")
    print("1. Set up AI models: python setup_models.py")
    print("2. Start the demo: python start.py")
    print("\nOr start services separately:")
    print("  Backend: cd backend && python -m uvicorn app.main:app --reload")
    print("  Frontend: cd frontend && npm run dev")

if __name__ == "__main__":
    main()