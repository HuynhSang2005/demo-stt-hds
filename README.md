## 📋 Mục lục

> 🚀 **Muốn setup nhanh?** Xem [QUICKSTART.md](QUICKSTART.md)

- [Tính năng chính](#-tính-năng-chính)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Kiến trúc](#-kiến-trúc)
- [Hướng dẫn cài đặt](#-hướng-dẫn-cài-đặt)
- [Hướng dẫn chạy](#-hướng-dẫn-chạy)
- [Cấu hình](#-cấu-hình)
- [Troubleshooting](#-troubleshooting)
- [API Documentation](#-api-documentation)se Speech-to-Text + Toxic Detection System

Hệ thống **Speech-to-Text (STT)** kết hợp **phát hiện ngôn từ tiêu cực** cho tiếng Việt, hoạt động **offline-first** với khả năng real-time.

## 📋 Mục lục

- [Tính năng chính](#-tính-năng-chính)
- [Yêu cầu hệ thống](#-yêu cầu-hệ-thống)
- [Kiến trúc](#-kiến-trúc)
- [Hướng dẫn cài đặt](#-hướng-dẫn-cài-đặt)
- [Hướng dẫn chạy](#-hướng-dẫn-chạy)
- [Cấu hình](#-cấu-hình)
- [Troubleshooting](#-troubleshooting)
- [API Documentation](#-api-documentation)

## ✨ Tính năng chính

- 🎯 **Speech-to-Text tiếng Việt**: Sử dụng **PhoWhisper-small** (244M params) cho độ chính xác cao
- 🛡️ **Phát hiện ngôn từ tiêu cực**: PhoBERT classifier 4 classes (positive, neutral, negative, toxic)
- 🔌 **Offline-first**: Models chạy hoàn toàn local, không cần internet sau khi setup
- ⚡ **Real-time processing**: WebSocket connection với latency thấp
- 🎨 **Modern UI**: React + TypeScript + Tailwind CSS + Shadcn UI
- 📊 **Audio visualization**: Waveform với WaveSurfer.js
- 🔄 **Batch processing**: Micro-batching cho hiệu suất tốt hơn

## 💻 Yêu cầu hệ thống

### Phần mềm bắt buộc

| Phần mềm | Phiên bản | Mục đích |
|----------|-----------|----------|
| **Python** | 3.9 - 3.13 | Backend runtime |
| **Node.js** | 18.x hoặc cao hơn | Frontend build tool |
| **FFmpeg** | 4.x hoặc cao hơn | Xử lý audio WebM/Opus |
| **Git** | Latest | Clone repository |

### Phần cứng khuyến nghị

- **RAM**: 8GB+ (models load ~2GB)
- **Disk**: 5GB+ trống (models + dependencies)
- **CPU**: 4 cores+ (hoặc GPU CUDA nếu có)

### Hệ điều hành hỗ trợ

- ✅ **Windows 10/11**
- ✅ **macOS 11+** (Big Sur trở lên)
- ✅ **Linux** (Ubuntu 20.04+, Debian 11+)

## 🏗️ Kiến trúc

```
┌─────────────────┐         WebSocket           ┌─────────────────┐
│                 │  ←────────────────────────→ │                 │
│  React Frontend │      (audio chunks)         │  FastAPI Backend│
│  (Port 5173)    │                             │  (Port 8000)    │
│                 │  ────────────────────────→  │                 │
└─────────────────┘      HTTP REST API          └─────────────────┘
                                                         │
                                                         ↓
                                         ┌──────────────────────────┐
                                         │   Local AI Models        │
                                         ├──────────────────────────┤
                                         │ • PhoWhisper-small       │
                                         │   (Speech-to-Text)       │
                                         │ • PhoBERT Classifier     │
                                         │   (Toxic Detection)      │
                                         └──────────────────────────┘
```

### Tech Stack

**Backend:**
- FastAPI 0.104.1 (Web framework)
- PyTorch 2.1.1 (ML framework)
- Transformers 4.35.2 (HuggingFace)
- torchaudio 2.1.1 (Audio processing)
- ONNX Runtime 1.16.3 (Inference optimization)

**Frontend:**
- React 19.1.1
- TypeScript 5.8.3
- Vite (Rolldown) 7.1.12
- Zustand 5.0.8 (State management)
- Zod 4.1.11 (Validation)
- Tailwind CSS 4.0 + Shadcn UI

## 📦 Hướng dẫn cài đặt

> 💡 **Tip**: Có thể dùng script tự động `setup.ps1` (Windows) hoặc `setup.sh` (Linux/Mac) để skip các bước manual!

### Bước 0: Kiểm tra dependencies (Recommended)

```bash
# Clone repo trước
git clone https://github.com/HuynhSang2005/demo-stt-hds.git
cd demo-stt-hds

# Kiểm tra dependencies
python check-dependencies.py
```

Script này sẽ kiểm tra:
- ✅ Python version (3.9-3.13)
- ✅ Node.js version (18+)
- ✅ FFmpeg installation
- ✅ pip và venv module
- ✅ Disk space (5GB+)

Nếu pass tất cả checks, bạn có thể chạy:
- **Windows**: `.\setup.ps1`
- **Linux/Mac**: `bash setup.sh`

Hoặc tiếp tục với setup manual bên dưới.

### Bước 1: Clone repository (Nếu chưa clone)

```bash
git clone https://github.com/HuynhSang2005/demo-stt-hds.git
cd demo-stt-hds
```

### Bước 2: Cài đặt FFmpeg

#### Windows:
```powershell
# Dùng Chocolatey (khuyến nghị)
choco install ffmpeg

# Hoặc download manual từ: https://ffmpeg.org/download.html
# Sau đó thêm vào PATH
```

#### macOS:
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Kiểm tra FFmpeg:**
```bash
ffmpeg -version
```

### Bước 3: Setup Backend

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

### Bước 4: Download AI Models

Models sẽ được download từ Hugging Face về local (~2.5GB):

```bash
# Từ thư mục gốc (demo-stt-hds/)
cd ..
python download_models.py
```

**Output mong đợi:**
```
🔄 Checking PhoWhisper-small (Speech-to-Text)...
📥 Downloading PhoWhisper-small from HuggingFace...
✅ PhoWhisper-small downloaded successfully!

🔄 Checking phobert-vi-comment-4class (Sentiment Analysis)...
📥 Downloading phobert-vi-comment-4class from HuggingFace...
✅ phobert-vi-comment-4class downloaded successfully!

🎉 Hoàn thành download models!
```

### Bước 5: Setup Frontend

```bash
cd frontend

# Cài đặt dependencies với npm
npm install

# Hoặc với yarn
yarn install

# Hoặc với pnpm (khuyến nghị, nhanh hơn)
pnpm install
```

### Bước 6: Tạo file .env (Optional)

Backend sẽ dùng default config nếu không có `.env`. Nếu muốn customize:

```bash
cd backend
cp .env.example .env
# Sau đó chỉnh sửa .env theo nhu cầu
```

## 🚀 Hướng dẫn chạy

### Chạy Backend (Terminal 1)

```bash
cd backend

# Kích hoạt venv (nếu chưa)
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Chạy server
python run_server.py
```

**Backend sẽ chạy tại:**
- API: http://127.0.0.1:8000
- WebSocket: ws://127.0.0.1:8000/v1/ws
- API Docs: http://127.0.0.1:8000/docs

### Chạy Frontend (Terminal 2)

```bash
cd frontend

# Chạy dev server
npm run dev
```

**Frontend sẽ chạy tại:** http://localhost:5173

### Mở trình duyệt

Truy cập: **http://localhost:5173**

## ⚙️ Cấu hình

### Backend Configuration

Chỉnh sửa `backend/.env` (hoặc dùng default):

```bash
# Server
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Model paths (relative to backend/)
ASR_MODEL_PATH=../PhoWhisper-small
CLASSIFIER_MODEL_PATH=../phobert-vi-comment-4class

# Device: cpu, cuda, mps (Apple Silicon)
MODEL_DEVICE=cpu

# Audio settings
AUDIO_CHUNK_DURATION=2.0
MIN_AUDIO_DURATION=0.1
MAX_AUDIO_DURATION=30.0
TARGET_SAMPLE_RATE=16000

# CORS (Frontend URLs)
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend Configuration

Chỉnh sửa `frontend/configs/default.json`:

```json
{
  "api": {
    "baseURL": "http://127.0.0.1:8000",
    "wsURL": "ws://127.0.0.1:8000/v1/ws"
  },
  "audio": {
    "chunkDuration": 2000,
    "maxDuration": 30000
  }
}
```

## 🔧 Troubleshooting

### 1. FFmpeg không tìm thấy

**Lỗi:**
```
FFmpeg not found or not working!
```

**Giải pháp:**
- Cài đặt FFmpeg (xem Bước 2)
- Kiểm tra FFmpeg trong PATH: `ffmpeg -version`
- Windows: Restart terminal sau khi cài FFmpeg

### 2. Models không load được

**Lỗi:**
```
OSError: Model path not found: ../PhoWhisper-small
```

**Giải pháp:**
```bash
# Chạy lại download script
python download_models.py

# Kiểm tra models đã tồn tại
ls PhoWhisper-small/
ls phobert-vi-comment-4class/
```

### 3. Import error: ModuleNotFoundError

**Lỗi:**
```
ModuleNotFoundError: No module named 'transformers'
```

**Giải pháp:**
```bash
# Đảm bảo venv đã được kích hoạt
cd backend
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows

# Cài lại dependencies
pip install -r requirements.txt
```

### 4. WebSocket connection failed

**Lỗi:**
```
WebSocket connection to 'ws://127.0.0.1:8000/v1/ws' failed
```

**Giải pháp:**
- Kiểm tra backend đang chạy: http://127.0.0.1:8000/docs
- Kiểm tra CORS trong `backend/.env`
- Tắt VPN/Proxy nếu có
- Thử đổi port trong config

### 5. Out of memory (OOM)

**Lỗi:**
```
RuntimeError: CUDA out of memory
```

**Giải pháp:**
```bash
# Chuyển sang CPU mode
# Trong backend/.env:
MODEL_DEVICE=cpu

# Giảm batch size (nếu dùng GPU)
ASR_BATCH_SIZE=2
CLASSIFIER_BATCH_SIZE=4
```

### 6. Audio không được nhận diện

**Kiểm tra:**
- Microphone permissions trong browser
- Audio format: WebM Opus codec (modern browsers)
- Thử record audio ngắn (2-3 giây) trước

### 7. Frontend build error

**Lỗi:**
```
Cannot find module '@/components/...'
```

**Giải pháp:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 API Documentation

### REST API

Xem đầy đủ tại: **http://127.0.0.1:8000/docs** (khi backend đang chạy)

#### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-10-06T10:30:00Z"
}
```

### WebSocket API

**Endpoint:** `ws://127.0.0.1:8000/v1/ws`

#### Message Format

**Client → Server (Audio chunk):**
```json
{
  "type": "audio",
  "data": "<base64_audio_data>",
  "format": "webm",
  "sampleRate": 48000
}
```

**Server → Client (Transcript result):**
```json
{
  "type": "transcript",
  "text": "Xin chào các bạn",
  "sentiment": {
    "label": "positive",
    "confidence": 0.95,
    "warning": false
  },
  "processingTime": 0.234
}
```

**Server → Client (Error):**
```json
{
  "type": "error",
  "message": "Audio processing failed",
  "code": "AUDIO_DECODE_ERROR"
}
```

## 🗂️ Cấu trúc Project

```
demo-stt-hds/
├── backend/                      # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/              # API endpoints
│   │   ├── core/                # Config, logger, metrics
│   │   ├── models/              # AI model wrappers
│   │   │   ├── phowhisper_asr.py
│   │   │   └── classifier.py
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   └── main.py              # FastAPI app
│   ├── requirements.txt
│   ├── run_server.py
│   └── .env.example
├── frontend/                    # React Frontend
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── schemas/            # Zod validation schemas
│   │   ├── stores/             # Zustand stores
│   │   ├── types/              # TypeScript types
│   │   └── utils/              # Utilities
│   ├── package.json
│   └── vite.config.ts
├── PhoWhisper-small/           # AI Model (ASR)
├── phobert-vi-comment-4class/  # AI Model (Classifier)
├── download_models.py          # Model download script
└── README.md
```

## 📚 Additional Documentation

- 📖 [QUICKSTART.md](QUICKSTART.md) - Quick setup guide (< 5 min read)
- 🏗️ [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Detailed architecture overview
- 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- 📋 [CHANGELOG.md](CHANGELOG.md) - Version history

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development workflow
- Coding standards
- Testing guidelines
- PR process

Quick start:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest` (backend) / `npm test` (frontend)
5. Submit a Pull Request

## 📄 License

[MIT License](LICENSE) - xem file LICENSE để biết thêm chi tiết.

This project uses AI models from VinAI Research (PhoWhisper, PhoBERT) which are licensed separately. See LICENSE file for details.

## 👨‍💻 Author

**HuynhSang2005**
- GitHub: [@HuynhSang2005](https://github.com/HuynhSang2005)

## 🙏 Acknowledgments

- [PhoWhisper](https://huggingface.co/vinai/PhoWhisper-small) - VinAI Research
- [PhoBERT](https://github.com/VinAIResearch/PhoBERT) - VinAI Research
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Shadcn UI](https://ui.shadcn.com/)

---

**🎉 Happy Coding!** Nếu gặp vấn đề, vui lòng tạo issue trên GitHub.
