#!/usr/bin/env python3
"""
Dependency Checker Script
Kiểm tra tất cả dependencies cần thiết trước khi setup project
"""

import sys
import subprocess
import platform
from pathlib import Path

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

def print_header():
    """Print script header"""
    print(f"{CYAN}========================================")
    print("🔍 Dependency Checker")
    print("    Vietnamese STT + Toxic Detection")
    print(f"========================================{NC}\n")

def print_step(message):
    """Print step message"""
    print(f"{YELLOW}📋 {message}{NC}")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✅ {message}{NC}")

def print_error(message):
    """Print error message"""
    print(f"{RED}❌ {message}{NC}")

def print_info(message):
    """Print info message"""
    print(f"{BLUE}ℹ️  {message}{NC}")

def print_warning(message):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {message}{NC}")

def check_command(command):
    """Check if a command exists"""
    try:
        result = subprocess.run(
            [command, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0, result.stdout.split('\n')[0]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""

def check_python():
    """Check Python installation"""
    print_step("Kiểm tra Python...")
    
    # Check current Python
    version = sys.version.split()[0]
    major, minor = sys.version_info[:2]
    
    if major == 3 and 9 <= minor <= 13:
        print_success(f"Python {version} - OK")
        return True
    else:
        print_error(f"Python {version} - Không hỗ trợ!")
        print_info("Yêu cầu: Python 3.9 - 3.13")
        print_info("Download: https://www.python.org/downloads/")
        return False

def check_node():
    """Check Node.js installation"""
    print_step("Kiểm tra Node.js...")
    
    exists, version = check_command('node')
    if exists:
        # Extract version number
        version_num = version.replace('v', '').split('.')[0]
        if int(version_num) >= 18:
            print_success(f"Node.js {version} - OK")
            return True
        else:
            print_warning(f"Node.js {version} - Phiên bản thấp")
            print_info("Khuyến nghị: Node.js 18.x trở lên")
            return False
    else:
        print_error("Node.js chưa được cài đặt!")
        print_info("Download: https://nodejs.org/")
        if platform.system() == "Darwin":
            print_info("macOS: brew install node")
        elif platform.system() == "Linux":
            print_info("Linux: sudo apt-get install nodejs npm")
        return False

def check_ffmpeg():
    """Check FFmpeg installation"""
    print_step("Kiểm tra FFmpeg...")
    
    exists, version = check_command('ffmpeg')
    if exists:
        print_success(f"FFmpeg {version[:50]}... - OK")
        return True
    else:
        print_error("FFmpeg chưa được cài đặt!")
        print_info("FFmpeg là BẮT BUỘC để xử lý audio WebM/Opus")
        
        if platform.system() == "Windows":
            print_info("Windows: choco install ffmpeg")
            print_info("Hoặc: https://ffmpeg.org/download.html")
        elif platform.system() == "Darwin":
            print_info("macOS: brew install ffmpeg")
        elif platform.system() == "Linux":
            print_info("Linux: sudo apt-get install ffmpeg")
        
        return False

def check_git():
    """Check Git installation"""
    print_step("Kiểm tra Git...")
    
    exists, version = check_command('git')
    if exists:
        print_success(f"Git {version} - OK")
        return True
    else:
        print_warning("Git chưa được cài đặt!")
        print_info("Git không bắt buộc nếu đã clone repo")
        print_info("Download: https://git-scm.com/downloads")
        return True  # Not critical

def check_pip():
    """Check pip installation"""
    print_step("Kiểm tra pip...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split()[1]
            print_success(f"pip {version} - OK")
            return True
        else:
            print_error("pip không hoạt động!")
            return False
    except Exception:
        print_error("pip chưa được cài đặt!")
        print_info("Cài đặt: python -m ensurepip --upgrade")
        return False

def check_venv():
    """Check venv module"""
    print_step("Kiểm tra venv module...")
    
    try:
        import venv
        print_success("venv module - OK")
        return True
    except ImportError:
        print_error("venv module không tìm thấy!")
        if platform.system() == "Linux":
            print_info("Linux: sudo apt-get install python3-venv")
        return False

def check_disk_space():
    """Check available disk space"""
    print_step("Kiểm tra dung lượng đĩa...")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(Path.cwd())
        
        free_gb = free // (2**30)
        if free_gb >= 5:
            print_success(f"Dung lượng trống: {free_gb}GB - OK")
            return True
        else:
            print_warning(f"Dung lượng trống: {free_gb}GB - Thấp!")
            print_info("Khuyến nghị: 5GB+ cho models và dependencies")
            return False
    except Exception:
        print_warning("Không thể kiểm tra dung lượng đĩa")
        return True

def check_models_exist():
    """Check if models are already downloaded"""
    print_step("Kiểm tra AI models...")
    
    phowhisper_path = Path("PhoWhisper-small")
    phobert_path = Path("phobert-vi-comment-4class")
    
    phowhisper_exists = (phowhisper_path / "config.json").exists()
    phobert_exists = (phobert_path / "config.json").exists()
    
    if phowhisper_exists and phobert_exists:
        print_success("AI models đã được download")
        return True
    elif phowhisper_exists or phobert_exists:
        print_warning("Một số models còn thiếu")
        if not phowhisper_exists:
            print_info("Thiếu: PhoWhisper-small")
        if not phobert_exists:
            print_info("Thiếu: phobert-vi-comment-4class")
        print_info("Chạy: python download_models.py")
        return False
    else:
        print_info("Chưa có models (sẽ download trong quá trình setup)")
        print_info("Kích thước: ~2.5GB")
        return True

def main():
    """Main function"""
    print_header()
    
    checks = {
        "Python": check_python(),
        "pip": check_pip(),
        "venv": check_venv(),
        "Node.js": check_node(),
        "FFmpeg": check_ffmpeg(),
        "Git": check_git(),
        "Disk Space": check_disk_space(),
        "Models": check_models_exist(),
    }
    
    print(f"\n{CYAN}========================================")
    print("📊 Kết quả kiểm tra")
    print(f"========================================{NC}\n")
    
    passed = sum(checks.values())
    total = len(checks)
    
    for name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    print(f"\n{CYAN}Kết quả: {passed}/{total} checks passed{NC}\n")
    
    # Critical checks
    critical = ["Python", "pip", "venv", "Node.js", "FFmpeg"]
    critical_failed = [name for name in critical if not checks[name]]
    
    if critical_failed:
        print_error("❌ Một số dependencies BẮT BUỘC còn thiếu!")
        print_info(f"Thiếu: {', '.join(critical_failed)}")
        print_info("Vui lòng cài đặt trước khi tiếp tục setup")
        sys.exit(1)
    else:
        print_success("🎉 Tất cả dependencies BẮT BUỘC đã sẵn sàng!")
        print_info("Bạn có thể chạy script setup:")
        
        if platform.system() == "Windows":
            print_info("  .\\setup.ps1")
        else:
            print_info("  bash setup.sh")
        
        sys.exit(0)

if __name__ == "__main__":
    main()
