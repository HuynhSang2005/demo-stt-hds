#!/bin/bash
# Vietnamese STT + Toxic Detection - Linux/macOS Setup Script
# Tự động hóa việc setup project trên Unix-like systems

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "🎙️  Vietnamese STT + Toxic Detection"
echo -e "    Linux/macOS Setup Script"
echo -e "========================================${NC}"
echo ""

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print step
print_step() {
    echo -e "${YELLOW}📋 $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check Python
print_step "Kiểm tra Python..."
if ! command_exists python3 && ! command_exists python; then
    print_error "Python chưa được cài đặt!"
    print_info "Cài đặt Python:"
    print_info "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    print_info "  macOS: brew install python@3.11"
    exit 1
fi

PYTHON_CMD="python3"
if ! command_exists python3; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
print_success "Python đã cài đặt: $PYTHON_VERSION"

# Check Node.js
print_step "Kiểm tra Node.js..."
if ! command_exists node; then
    print_error "Node.js chưa được cài đặt!"
    print_info "Cài đặt Node.js:"
    print_info "  Ubuntu/Debian: sudo apt-get install nodejs npm"
    print_info "  macOS: brew install node"
    print_info "Hoặc tải từ: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js đã cài đặt: $NODE_VERSION"

# Check FFmpeg
print_step "Kiểm tra FFmpeg..."
if ! command_exists ffmpeg; then
    print_error "FFmpeg chưa được cài đặt!"
    print_info "Cài đặt FFmpeg:"
    print_info "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    print_info "  macOS: brew install ffmpeg"
    exit 1
fi

FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n 1)
print_success "FFmpeg đã cài đặt: $FFMPEG_VERSION"

echo ""
echo -e "${CYAN}========================================"
echo -e "📦 Bắt đầu cài đặt dependencies..."
echo -e "========================================${NC}"
echo ""

# Setup Backend
print_step "Setup Backend..."
cd backend

if [ ! -d "venv" ]; then
    print_info "Tạo Python virtual environment..."
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment đã được tạo"
else
    print_info "Virtual environment đã tồn tại, skip..."
fi

print_info "Kích hoạt virtual environment..."
source venv/bin/activate

print_info "Cài đặt Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Backend dependencies đã được cài đặt"

cd ..

# Download Models
print_step "Download AI Models..."
if [ ! -f "PhoWhisper-small/config.json" ] || [ ! -f "phobert-vi-comment-4class/config.json" ]; then
    print_info "Downloading models từ Hugging Face (~2.5GB)..."
    print_info "Quá trình này có thể mất vài phút..."
    $PYTHON_CMD download_models.py
    print_success "Models đã được download"
else
    print_success "Models đã tồn tại, skip download"
fi

# Setup Frontend
print_step "Setup Frontend..."
cd frontend

print_info "Cài đặt Node.js dependencies..."
if command_exists pnpm; then
    print_info "Sử dụng pnpm..."
    pnpm install
elif command_exists yarn; then
    print_info "Sử dụng yarn..."
    yarn install
else
    print_info "Sử dụng npm..."
    npm install
fi
print_success "Frontend dependencies đã được cài đặt"

cd ..

# Create .env if not exists
print_step "Kiểm tra file .env..."
if [ ! -f "backend/.env" ]; then
    print_info "Tạo backend/.env từ .env.example..."
    cp backend/.env.example backend/.env
    print_success "File .env đã được tạo"
else
    print_info "File .env đã tồn tại, skip..."
fi

echo ""
echo -e "${GREEN}========================================"
echo -e "🎉 Setup hoàn tất!"
echo -e "========================================${NC}"
echo ""
echo -e "${CYAN}📝 Để chạy project:${NC}"
echo ""
echo -e "${YELLOW}1️⃣  Chạy Backend (Terminal 1):${NC}"
echo -e "   cd backend"
echo -e "   source venv/bin/activate"
echo -e "   python run_server.py"
echo ""
echo -e "${YELLOW}2️⃣  Chạy Frontend (Terminal 2):${NC}"
echo -e "   cd frontend"
echo -e "   npm run dev"
echo ""
echo -e "${YELLOW}3️⃣  Mở trình duyệt:${NC}"
echo -e "   http://localhost:5173"
echo ""
echo -e "${CYAN}📚 Xem thêm: README.md${NC}"
echo ""
