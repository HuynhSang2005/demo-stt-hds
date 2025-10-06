#!/usr/bin/env pwsh
# Vietnamese STT + Toxic Detection - Windows Setup Script
# Tự động hóa việc setup project trên Windows

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎙️ Vietnamese STT + Toxic Detection" -ForegroundColor Cyan
Write-Host "    Windows Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check command exists
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Function to print step
function Write-Step {
    param($Message)
    Write-Host "📋 $Message" -ForegroundColor Yellow
}

# Function to print success
function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

# Function to print error
function Write-Error-Custom {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# Function to print info
function Write-Info {
    param($Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

# Check Python
Write-Step "Kiểm tra Python..."
if (-not (Test-Command "python")) {
    Write-Error-Custom "Python chưa được cài đặt!"
    Write-Info "Download Python từ: https://www.python.org/downloads/"
    Write-Info "Yêu cầu: Python 3.9 - 3.13"
    exit 1
}
$pythonVersion = python --version
Write-Success "Python đã cài đặt: $pythonVersion"

# Check Node.js
Write-Step "Kiểm tra Node.js..."
if (-not (Test-Command "node")) {
    Write-Error-Custom "Node.js chưa được cài đặt!"
    Write-Info "Download Node.js từ: https://nodejs.org/"
    Write-Info "Yêu cầu: Node.js 18.x trở lên"
    exit 1
}
$nodeVersion = node --version
Write-Success "Node.js đã cài đặt: $nodeVersion"

# Check FFmpeg
Write-Step "Kiểm tra FFmpeg..."
if (-not (Test-Command "ffmpeg")) {
    Write-Error-Custom "FFmpeg chưa được cài đặt!"
    Write-Info "Cài đặt FFmpeg với Chocolatey:"
    Write-Info "  choco install ffmpeg"
    Write-Info "Hoặc download manual từ: https://ffmpeg.org/download.html"
    exit 1
}
$ffmpegVersion = (ffmpeg -version 2>&1 | Select-Object -First 1)
Write-Success "FFmpeg đã cài đặt: $ffmpegVersion"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📦 Bắt đầu cài đặt dependencies..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Setup Backend
Write-Step "Setup Backend..."
Set-Location backend

if (-not (Test-Path "venv")) {
    Write-Info "Tạo Python virtual environment..."
    python -m venv venv
    Write-Success "Virtual environment đã được tạo"
} else {
    Write-Info "Virtual environment đã tồn tại, skip..."
}

Write-Info "Kích hoạt virtual environment..."
& ".\venv\Scripts\Activate.ps1"

Write-Info "Cài đặt Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
Write-Success "Backend dependencies đã được cài đặt"

Set-Location ..

# Download Models
Write-Step "Download AI Models..."
if (-not (Test-Path "PhoWhisper-small\config.json") -or -not (Test-Path "phobert-vi-comment-4class\config.json")) {
    Write-Info "Downloading models từ Hugging Face (~2.5GB)..."
    Write-Info "Quá trình này có thể mất vài phút..."
    python download_models.py
    Write-Success "Models đã được download"
} else {
    Write-Success "Models đã tồn tại, skip download"
}

# Setup Frontend
Write-Step "Setup Frontend..."
Set-Location frontend

Write-Info "Cài đặt Node.js dependencies..."
if (Test-Command "pnpm") {
    Write-Info "Sử dụng pnpm..."
    pnpm install
} elseif (Test-Command "yarn") {
    Write-Info "Sử dụng yarn..."
    yarn install
} else {
    Write-Info "Sử dụng npm..."
    npm install
}
Write-Success "Frontend dependencies đã được cài đặt"

Set-Location ..

# Create .env if not exists
Write-Step "Kiểm tra file .env..."
if (-not (Test-Path "backend\.env")) {
    Write-Info "Tạo backend/.env từ .env.example..."
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Success "File .env đã được tạo"
} else {
    Write-Info "File .env đã tồn tại, skip..."
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "🎉 Setup hoàn tất!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Để chạy project:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Chạy Backend (Terminal 1):" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "   python run_server.py" -ForegroundColor White
Write-Host ""
Write-Host "2️⃣  Chạy Frontend (Terminal 2):" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  Mở trình duyệt:" -ForegroundColor Yellow
Write-Host "   http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "📚 Xem thêm: README.md" -ForegroundColor Cyan
Write-Host ""
