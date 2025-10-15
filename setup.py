#!/usr/bin/env python3
"""
Vietnamese STT Demo - Setup Script
Cài đặt và cấu hình môi trường cho demo
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil

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

def download_model_from_huggingface(model_name: str, model_path: str, local_dir: str) -> bool:
    """Download model từ Hugging Face Hub"""
    try:
        print(f"Downloading {model_name} from {model_path}...")
        
        # Check if already exists
        if Path(local_dir).exists():
            print(f"OK: {model_name} already exists, skipping download")
            return True
        
        # Create local directory
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        
        # Download using huggingface-hub
        from huggingface_hub import snapshot_download
        
        snapshot_download(
            repo_id=model_path,
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        
        print(f"OK: {model_name} downloaded successfully")
        return True
        
    except ImportError:
        print(f"ERROR: huggingface_hub not installed. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], 
                         check=True, capture_output=True)
            
            # Retry download
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id=model_path,
                local_dir=local_dir,
                local_dir_use_symlinks=False
            )
            print(f"OK: {model_name} downloaded successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to install huggingface_hub: {e}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to download {model_name}: {e}")
        return False

def download_models():
    """Download required models từ Hugging Face"""
    print("\nDownloading AI models from Hugging Face...")
    
    models_to_download = [
        {
            "name": "PhoWhisper",
            "path": "vinai/PhoWhisper-small",  # Correct model: PhoWhisper-small
            "local_dir": "PhoWhisper-small"    # Keep same directory name for compatibility
        },
        {
            "name": "PhoBERT Classifier", 
            "path": "vanhai123/phobert-vi-comment-4class",
            "local_dir": "phobert-vi-comment-4class"
        }
    ]
    
    success_count = 0
    
    for model in models_to_download:
        if download_model_from_huggingface(model["name"], model["path"], model["local_dir"]):
            success_count += 1
    
    if success_count == len(models_to_download):
        print("OK: All models downloaded successfully")
        return True
    else:
        print(f"WARNING: Only {success_count}/{len(models_to_download)} models downloaded")
        return False

def check_models():
    """Kiểm tra models có sẵn"""
    print("\nChecking AI models...")
    
    models = [
        "PhoWhisper-small",
        "phobert-vi-comment-4class"
    ]
    
    missing_models = []
    for model in models:
        model_path = Path(model)
        if model_path.exists():
            # Check if it has required files
            required_files = ["config.json"]
            has_required = all((model_path / file).exists() for file in required_files)
            
            if has_required:
                print(f"OK: {model} found and valid")
            else:
                print(f"WARNING: {model} exists but missing required files")
                missing_models.append(model)
        else:
            print(f"ERROR: {model} missing")
            missing_models.append(model)
    
    if missing_models:
        print(f"\nWARNING: Missing or invalid models: {', '.join(missing_models)}")
        return False
    
    print("OK: All models found and valid")
    return True

def main():
    """Main setup function"""
    print("Vietnamese STT Demo - Setup")
    print("=" * 40)
    
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
    
    # Download models if missing
    if not check_models():
        print("\nModels missing, attempting to download from Hugging Face...")
        if download_models():
            print("Models downloaded successfully")
        else:
            print("WARNING: Failed to download models")
            print("You can still run the demo, but it may not work properly")
    else:
        # Convert models to ONNX for better performance
        print("\nConverting models to ONNX for optimal performance...")
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "convert_models_to_onnx.py"
            ], cwd="backend", capture_output=True, text=True)
            
            if result.returncode == 0:
                print("OK: ONNX conversion completed")
            else:
                print("WARNING: ONNX conversion failed, will use PyTorch models")
                print(f"Error: {result.stderr}")
        except Exception as e:
            print(f"WARNING: Could not convert to ONNX: {e}")
            print("Models will use PyTorch mode")
    
    print("\nSUCCESS: Setup completed!")
    print("\nTo start the demo, run:")
    print("  python start.py")
    print("\nOr start services separately:")
    print("  Backend: cd backend && python -m uvicorn app.main:app --reload")
    print("  Frontend: cd frontend && npm run dev")

if __name__ == "__main__":
    main()
