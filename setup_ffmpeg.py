#!/usr/bin/env python3
"""
FFmpeg Setup Helper for Vietnamese STT Demo
Tự động download và setup FFmpeg cho Windows
"""

import subprocess
import sys
import os
import urllib.request
import zipfile
import shutil
from pathlib import Path

def run_command(command, cwd=None, check=True, capture_output=True):
    """Chạy command và xử lý kết quả"""
    print(f"Running: {' '.join(command)}")
    try:
        shell = os.name == 'nt'
        result = subprocess.run(
            command,
            cwd=cwd,
            check=check,
            capture_output=capture_output,
            text=True,
            shell=shell
        )
        if result.stdout and not capture_output:
            print(result.stdout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False, "", str(e)
    except FileNotFoundError as e:
        print(f"Command not found: {e}")
        return False, "", str(e)

def check_ffmpeg():
    """Kiểm tra FFmpeg đã có chưa"""
    print("🔍 Checking for existing FFmpeg...")

    # Try common paths
    ffmpeg_paths = [
        'ffmpeg',  # In PATH
        'C:\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
    ]

    for ffmpeg_path in ffmpeg_paths:
        try:
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"✅ FFmpeg found: {version}")
                print(f"   Location: {ffmpeg_path}")
                return True, ffmpeg_path
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            continue

    print("❌ FFmpeg not found")
    return False, None

def download_ffmpeg():
    """Download và cài đặt FFmpeg"""
    print("📥 Downloading FFmpeg for Windows...")

    # FFmpeg download URL (gyan.dev provides reliable Windows builds)
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    ffmpeg_zip = "ffmpeg-release-essentials.zip"
    ffmpeg_dir = Path("C:\\ffmpeg")

    try:
        # Download FFmpeg
        print(f"Downloading from: {ffmpeg_url}")
        urllib.request.urlretrieve(ffmpeg_url, ffmpeg_zip)

        # Extract to C:\ffmpeg
        print("Extracting FFmpeg...")
        with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
            # Find the ffmpeg directory inside the zip
            for member in zip_ref.namelist():
                if member.startswith('ffmpeg-') and member.endswith('/bin/ffmpeg.exe'):
                    # Extract the ffmpeg folder
                    ffmpeg_folder = member.split('/')[0]
                    zip_ref.extractall(".")

                    # Move to C:\ffmpeg
                    if ffmpeg_dir.exists():
                        shutil.rmtree(ffmpeg_dir)
                    shutil.move(ffmpeg_folder, ffmpeg_dir)
                    break

        # Clean up
        if Path(ffmpeg_zip).exists():
            Path(ffmpeg_zip).unlink()

        # Verify installation
        ffmpeg_exe = ffmpeg_dir / "bin" / "ffmpeg.exe"
        if ffmpeg_exe.exists():
            print(f"✅ FFmpeg installed successfully at: {ffmpeg_exe}")

            # Test FFmpeg
            result = subprocess.run(
                [str(ffmpeg_exe), '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"✅ FFmpeg working: {version}")
                return True
            else:
                print("❌ FFmpeg installation failed - not working")
                return False
        else:
            print("❌ FFmpeg installation failed - exe not found")
            return False

    except Exception as e:
        print(f"❌ FFmpeg download/installation failed: {e}")
        return False

def add_to_path():
    """Thêm FFmpeg vào PATH (optional)"""
    ffmpeg_bin = "C:\\ffmpeg\\bin"
    print(f"\\n💡 To add FFmpeg to PATH permanently:")
    print(f"   1. Search for 'Environment Variables' in Windows search")
    print(f"   2. Click 'Environment Variables...'")
    print(f"   3. Under 'System variables', find 'Path' and click 'Edit'")
    print(f"   4. Click 'New' and add: {ffmpeg_bin}")
    print(f"   5. Click 'OK' and restart your command prompt")

def main():
    """Main setup function"""
    print("🎬 FFmpeg Setup Helper for Vietnamese STT Demo")
    print("=" * 60)

    # Check if already installed
    found, path = check_ffmpeg()
    if found:
        print("\\n🎉 FFmpeg is already working!")
        print("You can now run the backend without issues.")
        return

    # Download and install
    print("\\n🚀 Installing FFmpeg...")
    if download_ffmpeg():
        print("\\n🎉 FFmpeg setup completed successfully!")
        print("You can now run: python run_backend.py")

        # Optional: Add to PATH
        add_to_path()
    else:
        print("\\n❌ FFmpeg setup failed!")
        print("\\nManual installation options:")
        print("1. Download from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip")
        print("2. Extract to C:\\ffmpeg")
        print("3. Add C:\\ffmpeg\\bin to PATH")
        print("4. Or use Chocolatey: choco install ffmpeg")

if __name__ == "__main__":
    main()