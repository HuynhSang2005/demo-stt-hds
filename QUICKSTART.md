# 🚀 Quick Start Guide

Hướng dẫn setup nhanh cho Vietnamese STT + Toxic Detection system.

## 📦 Setup nhanh 1 lệnh

### Windows (PowerShell):
```powershell
# Kiểm tra dependencies
python check-dependencies.py

# Nếu pass tất cả checks, chạy setup
.\setup.ps1
```

### Linux/macOS:
```bash
# Kiểm tra dependencies
python3 check-dependencies.py

# Nếu pass tất cả checks, chạy setup
chmod +x setup.sh
./setup.sh
```

## ⚡ Chạy project

### Option 1: Chạy manual (2 terminals)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# hoặc: .\venv\Scripts\Activate.ps1  # Windows
python run_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Một terminal (background)

**Windows:**
```powershell
# Chạy backend background
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; python run_server.py"

# Chạy frontend
cd frontend
npm run dev
```

**Linux/macOS:**
```bash
# Chạy backend background
cd backend && source venv/bin/activate && python run_server.py &

# Chạy frontend
cd frontend && npm run dev
```

## 🌐 Truy cập

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs
- **WebSocket**: ws://127.0.0.1:8000/v1/ws

## 🔧 Troubleshooting nhanh

### 1. FFmpeg error
```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### 2. Models không load
```bash
python download_models.py
```

### 3. Port đã được sử dụng

**Backend (port 8000):**
```bash
# Thay đổi trong backend/.env
PORT=8001
```

**Frontend (port 5173):**
```bash
# Thay đổi trong frontend/vite.config.ts
server: {
  port: 5174
}
```

### 4. Virtual environment issues
```bash
# Xóa và tạo lại
rm -rf backend/venv  # Linux/Mac
# hoặc: Remove-Item -Recurse backend\venv  # Windows

cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📚 Chi tiết đầy đủ

Xem [README.md](README.md) để biết thêm chi tiết về:
- Kiến trúc hệ thống
- API documentation
- Cấu hình nâng cao
- Deployment guide

## ✅ Checklist sau khi setup

- [ ] `python check-dependencies.py` - Pass tất cả checks
- [ ] Models đã download (PhoWhisper-small, phobert-vi-comment-4class)
- [ ] Backend chạy thành công trên port 8000
- [ ] Frontend chạy thành công trên port 5173
- [ ] Mở http://localhost:5173 thấy UI
- [ ] Test record audio và nhận được transcript

## 🆘 Cần giúp đỡ?

1. Kiểm tra logs trong terminal
2. Xem [Troubleshooting section](README.md#-troubleshooting) trong README
3. Tạo issue trên GitHub với:
   - Output của `python check-dependencies.py`
   - Error logs từ backend/frontend
   - OS và phiên bản Python/Node
