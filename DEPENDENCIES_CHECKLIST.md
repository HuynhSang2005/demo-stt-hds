# ✅ Dependencies Checklist

Danh sách kiểm tra đầy đủ tất cả dependencies cần thiết để chạy project Vietnamese STT + Toxic Detection.

## 📋 System Requirements

### 1. Python
- ✅ **Version:** 3.9 - 3.13
- ✅ **Kiểm tra:** `python --version`
- ✅ **Download:** https://www.python.org/downloads/
- ⚠️ **Lưu ý:** Chọn "Add Python to PATH" khi cài đặt trên Windows

### 2. Node.js
- ✅ **Version:** 18.x hoặc cao hơn
- ✅ **Kiểm tra:** `node --version`
- ✅ **Download:** https://nodejs.org/
- 💡 **Khuyến nghị:** Cài LTS version

### 3. FFmpeg (BẮT BUỘC)
- ❌ **THIẾU** - Cần cài đặt ngay
- ✅ **Mục đích:** Xử lý audio WebM/Opus từ browser
- ✅ **Kiểm tra:** `ffmpeg -version`
- 📖 **Hướng dẫn:** Xem file `HƯỚNG_DẪN_CÀI_FFMPEG.md`

#### Cài đặt nhanh:
```bash
# Windows (Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg
```

### 4. Git
- ✅ **Version:** Latest
- ✅ **Kiểm tra:** `git --version`
- ✅ **Download:** https://git-scm.com/
- 💡 **Lưu ý:** Không bắt buộc nếu đã clone repo

### 5. pip (Python Package Manager)
- ✅ **Kiểm tra:** `pip --version` hoặc `python -m pip --version`
- ✅ **Cài đặt:** `python -m ensurepip --upgrade`

### 6. venv (Python Virtual Environment)
- ✅ **Kiểm tra:** `python -m venv --help`
- ✅ **Cài đặt:** 
  - Windows: Có sẵn với Python
  - Linux: `sudo apt-get install python3-venv`

## 📦 Backend Dependencies

### Python Packages (từ requirements.txt)

#### Core Framework
- ✅ `fastapi[all]==0.104.1` - Web framework
- ✅ `uvicorn[standard]==0.24.0` - ASGI server
- ✅ `websockets==12.0` - WebSocket support
- ✅ `pydantic-settings==2.0.3` - Configuration management

#### Machine Learning
- ✅ `torch>=2.6.0` - PyTorch (Python 3.13 compatible)
- ✅ `torchvision>=0.21.0` - Vision utilities
- ✅ `torchaudio>=2.6.0` - Audio processing
- ✅ `transformers>=4.50.0` - Hugging Face transformers
- ✅ `optimum[onnxruntime]>=1.16.0` - ONNX optimization
- ✅ `onnxruntime>=1.20.0` - ONNX Runtime

#### Audio Processing
- ✅ `librosa==0.10.1` - Audio analysis
- ✅ `soundfile==0.12.1` - Audio file I/O
- ⚠️ **Cần FFmpeg:** torchaudio sử dụng FFmpeg backend cho WebM/Opus

#### Logging & Monitoring
- ✅ `structlog==23.2.0` - Structured logging
- ✅ `psutil==5.9.6` - System metrics

#### Development
- ✅ `pytest==7.4.3` - Testing framework
- ✅ `pytest-asyncio==0.21.1` - Async testing
- ✅ `httpx==0.25.2` - HTTP client for testing

#### Utilities
- ✅ `python-multipart==0.0.6` - Form data parsing
- ✅ `python-dotenv==1.0.0` - Environment variables
- ✅ `click==8.1.7` - CLI utilities
- ✅ `huggingface-hub>=0.26.0` - Model download

### Cài Đặt Backend Dependencies

```bash
cd backend

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## 🎨 Frontend Dependencies

### Node.js Packages (từ package.json)

#### Core Framework
- ✅ `react@19.1.1` - UI library
- ✅ `react-dom@19.1.1` - React DOM renderer
- ✅ `vite` (rolldown-vite) - Build tool

#### UI Components
- ✅ `@radix-ui/*` - Headless UI components
- ✅ `tailwindcss@4.0.0` - CSS framework
- ✅ `lucide-react@0.544.0` - Icon library
- ✅ `framer-motion@12.23.22` - Animation library

#### State Management
- ✅ `zustand@5.0.8` - State management
- ✅ `zod@4.1.11` - Schema validation
- ✅ `react-hook-form@7.63.0` - Form handling

#### Audio & WebSocket
- ✅ `wavesurfer.js@7.10.3` - Audio visualization
- ✅ `ws@8.18.3` - WebSocket client

#### Development Tools
- ✅ `typescript@5.8.3` - Type checking
- ✅ `eslint@9.36.0` - Linting
- ✅ `@vitejs/plugin-react@5.0.3` - React plugin for Vite

### Cài Đặt Frontend Dependencies

```bash
cd frontend

# Sử dụng npm
npm install

# Hoặc yarn
yarn install

# Hoặc pnpm (khuyến nghị - nhanh hơn)
pnpm install
```

## 🤖 AI Models

### 1. PhoWhisper-small (ASR Model)
- ✅ **Size:** ~1.2GB
- ✅ **Path:** `PhoWhisper-small/`
- ✅ **Download:** `python download_models.py`
- 💡 **Mục đích:** Speech-to-Text cho tiếng Việt

### 2. phobert-vi-comment-4class (Sentiment Classifier)
- ✅ **Size:** ~1.3GB
- ✅ **Path:** `phobert-vi-comment-4class/`
- ✅ **Download:** `python download_models.py`
- 💡 **Mục đích:** Phân loại sentiment (positive, negative, neutral, toxic)

### Download Models

```bash
# Từ thư mục gốc project
python download_models.py
```

Output mong đợi:
```
🔄 Checking PhoWhisper-small (Speech-to-Text)...
📥 Downloading PhoWhisper-small from HuggingFace...
✅ PhoWhisper-small downloaded successfully!

🔄 Checking phobert-vi-comment-4class (Sentiment Analysis)...
📥 Downloading phobert-vi-comment-4class from HuggingFace...
✅ phobert-vi-comment-4class downloaded successfully!

🎉 Hoàn thành download models!
```

## 💾 Disk Space

- ✅ **Yêu cầu:** 5GB+ trống
- 📊 **Phân bố:**
  - Models: ~2.5GB
  - Python dependencies: ~1.5GB
  - Node.js dependencies: ~500MB
  - Cache & temp: ~500MB

## 🔍 Kiểm Tra Tổng Hợp

### Automated Check Script

```bash
# Chạy script kiểm tra dependencies tự động
python check-dependencies.py
```

Kết quả mong đợi:
```
========================================
Dependency Checker
    Vietnamese STT + Toxic Detection
========================================

[*] Kiểm tra Python...
[OK] Python 3.13.7 - OK

[*] Kiểm tra pip...
[OK] pip 25.2 - OK

[*] Kiểm tra venv module...
[OK] venv module - OK

[*] Kiểm tra Node.js...
[OK] Node.js v22.17.0 - OK

[*] Kiểm tra FFmpeg...
[OK] FFmpeg ffmpeg version 4.4.2 - OK

[*] Kiểm tra Git...
[OK] Git git version 2.50.0 - OK

[*] Kiểm tra dung lượng đĩa...
[OK] Dung lượng trống: 98GB - OK

[*] Kiểm tra AI models...
[OK] AI models đã được download

========================================
Ket qua kiem tra
========================================

[OK] Python
[OK] pip
[OK] venv
[OK] Node.js
[OK] FFmpeg
[OK] Git
[OK] Disk Space
[OK] Models

Kết quả: 8/8 checks passed

[OK] Tat ca dependencies BAT BUOC da san sang!
[INFO] Ban co the chay script setup:
[INFO]   .\setup.ps1  # Windows
[INFO]   bash setup.sh  # Linux/macOS
```

## ❌ Common Issues

### Issue 1: FFmpeg Missing
**Error:** `FFmpeg chưa được cài đặt!`

**Solution:** Xem file `HƯỚNG_DẪN_CÀI_FFMPEG.md`

### Issue 2: Python Version Incompatible
**Error:** `Python X.X.X - Không hỗ trợ!`

**Solution:** 
- Cài đặt Python 3.9 - 3.13
- Download từ: https://www.python.org/downloads/

### Issue 3: Node.js Version Too Old
**Error:** `Node.js vXX.X - Phiên bản thấp`

**Solution:**
- Cài đặt Node.js 18.x+
- Download từ: https://nodejs.org/

### Issue 4: Models Not Downloaded
**Error:** `Chưa có models (sẽ download trong quá trình setup)`

**Solution:**
```bash
python download_models.py
```

### Issue 5: Disk Space Insufficient
**Error:** `Dung lượng trống: XGB - Thấp!`

**Solution:**
- Giải phóng ít nhất 5GB dung lượng
- Xóa cache: `pip cache purge` và `npm cache clean --force`

## 📚 Next Steps

Sau khi tất cả dependencies đã sẵn sàng:

1. ✅ **Automated Setup:**
   ```bash
   # Windows
   .\setup.ps1
   
   # Linux/macOS
   bash setup.sh
   ```

2. ✅ **Manual Setup:**
   - Xem `README.md` cho hướng dẫn chi tiết
   - Hoặc `QUICKSTART.md` cho hướng dẫn nhanh

3. ✅ **Run Project:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python run_server.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

4. ✅ **Access Application:**
   - Frontend: http://localhost:5173
   - Backend API: http://127.0.0.1:8000
   - API Docs: http://127.0.0.1:8000/docs

## 🎉 Success Indicators

Khi mọi thứ đã setup đúng:

### Backend Started Successfully
```
[STARTUP] FASTAPI BACKEND STARTED SUCCESSFULLY
   - Startup time: 5.23s
   - ASR model loaded: True
   - Classifier model loaded: True
   - WebSocket endpoint: /v1/ws
   - Server: http://127.0.0.1:8000
```

### Frontend Running
```
VITE v7.1.12  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### WebSocket Connected
- Frontend hiển thị: "Đã kết nối" (màu xanh)
- Console không có lỗi WebSocket
- Có thể record và nhận transcription

---

**✅ Hoàn tất checklist này để đảm bảo project chạy mượt mà!**

