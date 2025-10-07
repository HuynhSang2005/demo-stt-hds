# 📊 Tổng Quan Project: Vietnamese STT + Toxic Detection

## 🎯 Mô Tả Tổng Quan

Hệ thống **Speech-to-Text (STT)** kết hợp **phát hiện ngôn từ tiêu cực** cho tiếng Việt, hoạt động **offline-first** với khả năng real-time processing.

### Tính Năng Chính
- 🎤 **Speech-to-Text**: PhoWhisper-small (244M params, WER thấp)
- 🛡️ **Toxic Detection**: PhoBERT 4-class sentiment classifier
- 🔌 **Offline-First**: Models chạy hoàn toàn local
- ⚡ **Real-time**: WebSocket với latency < 500ms
- 🎨 **Modern UI**: React 19 + Tailwind CSS 4 + Shadcn UI
- 📊 **Metrics & Monitoring**: Performance tracking & health checks

## 🏗️ Kiến Trúc Hệ Thống

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    USER BROWSER                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          React Frontend (Port 5173)                  │  │
│  │  - Audio Recorder (WebM/Opus)                        │  │
│  │  - Zustand State Management                          │  │
│  │  - WaveSurfer.js Visualization                       │  │
│  │  - WebSocket Client                                  │  │
│  └─────────┬────────────────────────────────────┬───────┘  │
└────────────┼────────────────────────────────────┼──────────┘
             │ HTTP (REST API)          │ WebSocket (Binary)
             ↓                          ↓
┌─────────────────────────────────────────────────────────────┐
│             FastAPI Backend (Port 8000)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  WebSocket Handler                                   │  │
│  │  - Receive audio chunks (binary)                     │  │
│  │  - Send transcript results (JSON)                    │  │
│  │  - Health checks (ping/pong)                         │  │
│  └─────────┬────────────────────────────────────────────┘  │
│            ↓                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Audio Processor Service                             │  │
│  │  - Decode WebM/Opus (via FFmpeg)                     │  │
│  │  - Resample to 16kHz                                 │  │
│  │  - Pipeline orchestration                            │  │
│  └─────────┬────────────────────────────────────────────┘  │
│            ↓                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI Models Pipeline                                  │  │
│  │  ┌────────────────┐    ┌──────────────────────┐     │  │
│  │  │ PhoWhisper ASR │ →  │ PhoBERT Classifier   │     │  │
│  │  │ (244M params)  │    │ (4-class sentiment)  │     │  │
│  │  └────────────────┘    └──────────────────────┘     │  │
│  │  Audio → Text         Text → Sentiment + Keywords   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
```
1. USER speaks → Microphone captures audio
2. Browser MediaRecorder → WebM/Opus chunks (1-2s)
3. Frontend sends via WebSocket → Binary audio data
4. Backend decodes with FFmpeg → WAV/PCM waveform
5. Resamples to 16kHz mono → PyTorch tensor
6. PhoWhisper processes → Vietnamese text
7. PhoBERT classifies → Sentiment + Bad keywords
8. Backend sends JSON result → Frontend displays
```

## 📁 Cấu Trúc Source Code

### Backend (FastAPI + PyTorch)
```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── api/v1/
│   │   ├── endpoints.py        # WebSocket endpoints
│   │   ├── rest_endpoints.py  # REST API endpoints
│   │   ├── session_endpoints.py # Session-based WebSocket
│   │   └── metrics.py          # Performance metrics API
│   ├── core/
│   │   ├── config.py           # PydanticSettings configuration
│   │   ├── logger.py           # Structured logging (structlog)
│   │   ├── metrics.py          # Metrics collector
│   │   └── error_handling.py  # Circuit breaker & error handling
│   ├── models/
│   │   ├── phowhisper_asr.py  # PhoWhisper ASR model wrapper
│   │   ├── classifier.py       # PhoBERT classifier wrapper
│   │   └── asr.py              # ASR base interface
│   ├── services/
│   │   ├── audio_processor.py  # Main processing pipeline
│   │   └── session_processor.py # Session management
│   ├── schemas/
│   │   └── audio.py            # Pydantic schemas
│   └── utils/
│       ├── bad_words_detector.py      # Keyword detection
│       ├── toxic_keyword_detection.py # Enhanced toxic detection
│       └── vietnamese_preprocessing.py # Vietnamese NLP utils
├── configs/
│   └── default.json            # Default configuration
├── requirements.txt            # Python dependencies
└── run_server.py               # Server startup script
```

### Frontend (React 19 + TypeScript)
```
frontend/
├── src/
│   ├── App.tsx                 # Root component
│   ├── main.tsx                # Entry point
│   ├── components/
│   │   ├── VietnameseSTTDashboard.tsx  # Main dashboard
│   │   ├── AudioRecorder.tsx           # Recording controls
│   │   ├── TranscriptDisplay.tsx       # Results display
│   │   ├── SimpleWaveform.tsx          # Audio visualization
│   │   ├── SentimentBadge.tsx          # Sentiment indicator
│   │   ├── ToxicWarningAlert.tsx       # Toxic alert
│   │   ├── BadKeywordsList.tsx         # Keywords list
│   │   └── ui/                         # Shadcn UI components
│   ├── hooks/
│   │   ├── useWebSocket.ts             # WebSocket connection
│   │   ├── useAudioRecorder.ts         # Audio recording
│   │   └── useSessionWebSocket.ts      # Session WebSocket
│   ├── stores/
│   │   └── vietnameseSTT.store.ts      # Zustand state store
│   ├── types/
│   │   ├── audio.ts                    # Audio types
│   │   ├── transcript.ts               # Transcript types
│   │   └── websocket.ts                # WebSocket types
│   ├── schemas/
│   │   └── *.schema.ts                 # Zod validation schemas
│   └── utils/
│       ├── audio-converter.ts          # Audio format conversion
│       └── vietnamese.ts               # Vietnamese text utils
├── configs/
│   └── default.json            # Frontend configuration
├── package.json                # Node.js dependencies
└── vite.config.ts              # Vite build config
```

## 🔧 Dependencies Tổng Quan

### Critical Dependencies (BẮT BUỘC)

#### System-Level
1. **Python 3.9-3.13** - Backend runtime
2. **Node.js 18+** - Frontend build & dev server
3. **FFmpeg** - Audio decoding (WebM/Opus → WAV)
   - ⚠️ **THIẾU DEPENDENCY NÀY** - Cần cài đặt ngay!
   - Xem: `HƯỚNG_DẪN_CÀI_FFMPEG.md`

#### Backend Python Packages
- **FastAPI 0.104.1** - Web framework
- **PyTorch 2.6.0+** - ML framework (Python 3.13 compatible)
- **transformers 4.50.0+** - Hugging Face models
- **torchaudio 2.6.0+** - Audio processing
- **huggingface-hub 0.26.0+** - Model download
- **structlog 23.2.0** - Structured logging
- **pydantic-settings 2.0.3** - Configuration

#### Frontend Node.js Packages
- **React 19.1.1** - UI framework
- **Zustand 5.0.8** - State management
- **Zod 4.1.11** - Schema validation
- **Tailwind CSS 4.0** - Styling
- **WaveSurfer.js 7.10.3** - Audio visualization
- **Vite (Rolldown)** - Build tool

#### AI Models
1. **PhoWhisper-small** (~1.2GB)
   - Repo: `vinai/PhoWhisper-small`
   - Purpose: Vietnamese Speech-to-Text
   
2. **phobert-vi-comment-4class** (~1.3GB)
   - Repo: `vanhai123/phobert-vi-comment-4class`
   - Purpose: Sentiment classification (4 classes)

## 🚀 Quy Trình Chạy Project

### 1. Kiểm Tra Dependencies
```bash
python check-dependencies.py
```

### 2. Setup Tự Động (Khuyến nghị)
```bash
# Windows
.\setup.ps1

# Linux/macOS
bash setup.sh
```

### 3. Hoặc Setup Thủ Công

#### Backend Setup
```bash
cd backend

# Tạo virtual environment
python -m venv venv

# Kích hoạt venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/macOS

# Cài dependencies
pip install -r requirements.txt
```

#### Download Models
```bash
# Từ thư mục gốc
python download_models.py
```

#### Frontend Setup
```bash
cd frontend
npm install
```

### 4. Chạy Application

#### Terminal 1: Backend
```bash
cd backend
python run_server.py
```

Expected output:
```
[STARTUP] FASTAPI BACKEND STARTED SUCCESSFULLY
   - Startup time: 5.23s
   - ASR model loaded: True
   - Classifier model loaded: True
   - WebSocket endpoint: /v1/ws
   - Server: http://127.0.0.1:8000
```

#### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v7.1.12  ready in 1234 ms
  ➜  Local:   http://localhost:5173/
```

### 5. Access Application
- **Frontend UI**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs

## 🔍 Các Endpoint Quan Trọng

### REST API
- `GET /` - Service info
- `GET /info` - Detailed system info
- `GET /v1/health` - Health check
- `GET /v1/metrics` - Performance metrics

### WebSocket
- `ws://127.0.0.1:8000/v1/ws` - Real-time audio processing
- `ws://127.0.0.1:8000/v1/ws/session/{session_id}` - Session-based

## 📊 Performance Metrics

### ASR (PhoWhisper-small)
- **Model Size:** 244M parameters
- **Processing Speed:** ~2-3x real-time (RTF: 0.3-0.5)
- **WER:** ~15-20% (Vietnamese)
- **Latency:** ~200-400ms per 2s chunk

### Classifier (PhoBERT)
- **Model Size:** ~130M parameters
- **Processing Speed:** ~10-20ms per sentence
- **Accuracy:** ~85-90% (4-class sentiment)
- **Classes:** positive, negative, neutral, toxic

### System Performance
- **Total Latency:** 300-500ms (end-to-end)
- **Memory Usage:** ~2-3GB (models loaded)
- **CPU Usage:** 30-50% (1 active user)
- **Concurrent Users:** Up to 100 (WebSocket connections)

## 🛡️ Error Handling & Resilience

### Circuit Breaker Pattern
- **ASR Circuit Breaker**: 5 failures → 60s timeout
- **Classifier Circuit Breaker**: 5 failures → 60s timeout
- **Auto-recovery**: Half-open after timeout

### WebSocket Resilience
- **Auto-reconnect**: Exponential backoff (1s → 30s)
- **Ping/Pong**: 30s interval health checks
- **Request Queue**: Buffer during reconnection (max 50)

### Error Categories
1. **Audio Input Errors**: Format issues, decoding failures
2. **Model Inference Errors**: ASR/Classifier failures
3. **Connection Errors**: WebSocket disconnections
4. **Timeout Errors**: Processing exceeded limits

## 🔒 Security Features

### CORS Protection
- Configured origins: `http://localhost:5173`, `http://127.0.0.1:5173`
- Debug mode allows all origins

### Input Validation
- Audio duration limits: 0.1s - 30s
- File size limits: 256KB per chunk
- MIME type validation: WebM, WAV, OGG

### Rate Limiting
- Max concurrent connections: 100
- Request timeout: 30s
- Circuit breaker protection

## 🐛 Common Issues & Solutions

### Issue 1: FFmpeg Not Found
**Error:** `FFmpeg not found or not working!`

**Solution:**
```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### Issue 2: Models Not Loaded
**Error:** `Model validation failed`

**Solution:**
```bash
python download_models.py
```

### Issue 3: WebSocket Connection Failed
**Error:** `WebSocket connection failed`

**Solution:**
1. Kiểm tra backend đang chạy: http://127.0.0.1:8000/docs
2. Kiểm tra CORS settings trong `backend/.env`
3. Restart cả backend và frontend

### Issue 4: Audio Not Recognized
**Possible causes:**
- Microphone permission denied
- Browser không hỗ trợ MediaRecorder API
- Audio format không được backend hỗ trợ

**Solution:**
1. Cho phép microphone access trong browser
2. Sử dụng Chrome/Edge/Firefox modern versions
3. Kiểm tra backend logs để xem lỗi decoding

## 📈 Future Enhancements

### Phase 2 (Planned)
- [ ] ONNX quantization for 2-4x faster inference
- [ ] Batch processing for multiple concurrent users
- [ ] GPU acceleration support
- [ ] Model caching & warm-up optimization

### Phase 3 (Potential)
- [ ] Multi-language support
- [ ] Custom vocabulary injection
- [ ] Speaker diarization
- [ ] Real-time translation

## 📚 Tài Liệu Liên Quan

- `README.md` - Documentation chính
- `QUICKSTART.md` - Quick setup guide
- `SETUP.md` - Setup improvements log
- `DEPENDENCIES_CHECKLIST.md` - Dependencies checklist
- `HƯỚNG_DẪN_CÀI_FFMPEG.md` - FFmpeg installation guide
- `CONTRIBUTING.md` - Contribution guidelines
- `PROJECT_STRUCTURE.md` - Detailed structure
- `CHANGELOG.md` - Version history

## 🎯 Key Takeaways

1. ✅ **Offline-First**: Tất cả AI models chạy local, không cần internet sau setup
2. ⚡ **Real-time**: WebSocket streaming với latency < 500ms
3. 🛡️ **Production-Ready**: Circuit breakers, health checks, structured logging
4. 🎨 **Modern Stack**: React 19, FastAPI, PyTorch 2.6, Tailwind CSS 4
5. ❌ **Missing FFmpeg**: Cần cài đặt FFmpeg để backend hoạt động

## ⚠️ Critical Action Required

**TRƯỚC KHI CHẠY PROJECT, HÃY:**

1. ✅ Cài đặt FFmpeg (xem `HƯỚNG_DẪN_CÀI_FFMPEG.md`)
2. ✅ Chạy `python check-dependencies.py` để verify
3. ✅ Download models: `python download_models.py`
4. ✅ Setup backend và frontend
5. ✅ Test WebSocket connection

---

**📞 Support:** Nếu gặp vấn đề, tạo issue trên GitHub hoặc xem Troubleshooting section trong README.md

