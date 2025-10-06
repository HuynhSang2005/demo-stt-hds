# 📁 Project Structure

Detailed overview of the project structure and organization.

## 🌳 Root Directory

```
demo-stt-hds/
├── 📄 README.md                 # Main documentation (Vietnamese)
├── 📄 QUICKSTART.md             # Quick setup guide
├── 📄 CONTRIBUTING.md           # Contribution guidelines
├── 📄 CHANGELOG.md              # Version history
├── 📄 LICENSE                   # MIT License
├── 📄 .gitignore                # Git ignore rules
│
├── 🐍 download_models.py        # Script to download AI models from HuggingFace
├── 🔍 check-dependencies.py    # Pre-setup dependency checker
├── ⚙️  setup.ps1                # Windows setup automation
├── ⚙️  setup.sh                 # Linux/macOS setup automation
│
├── 📂 .github/                  # GitHub specific files
│   └── copilot-instructions.md  # AI agent instructions
│
├── 🤖 PhoWhisper-small/         # ASR Model (~1.5GB) [gitignored]
│   ├── config.json
│   ├── pytorch_model.bin
│   ├── tokenizer.json
│   └── ...
│
├── 🤖 phobert-vi-comment-4class/ # Classifier Model (~500MB) [gitignored]
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer_config.json
│   └── ...
│
├── 📂 backend/                  # FastAPI Backend
└── 📂 frontend/                 # React Frontend
```

## 🔙 Backend Structure

```
backend/
├── 📄 requirements.txt          # Python dependencies
├── 📄 run_server.py             # Server entry point
├── 📄 .env.example              # Environment variables template
│
├── 📂 app/                      # Main application package
│   ├── 📄 __init__.py
│   ├── 📄 main.py               # FastAPI app initialization
│   │
│   ├── 📂 api/                  # API layer
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py     # WebSocket & REST endpoints
│   │
│   ├── 📂 core/                 # Core functionality
│   │   ├── config.py            # PydanticSettings configuration
│   │   ├── logger.py            # Structured logging (structlog)
│   │   ├── error_handling.py   # Custom exceptions
│   │   └── metrics.py           # Performance metrics
│   │
│   ├── 📂 models/               # AI Model wrappers
│   │   ├── phowhisper_asr.py   # PhoWhisper ASR wrapper
│   │   ├── classifier.py        # PhoBERT classifier wrapper
│   │   └── asr.py               # Legacy (Wav2Vec2, deprecated)
│   │
│   ├── 📂 schemas/              # Pydantic data models
│   │   ├── audio.py             # Audio-related schemas
│   │   └── ...
│   │
│   ├── 📂 services/             # Business logic
│   │   ├── audio_processor.py  # Main audio processing service
│   │   ├── session_processor.py # WebSocket session management
│   │   └── ...
│   │
│   └── 📂 utils/                # Utility functions
│       └── ...
│
├── 📂 configs/
│   └── default.json             # Default configuration
│
├── 📂 scripts/                  # Utility scripts
│   ├── check_models.py
│   ├── export_onnx_quantized.py
│   └── ...
│
└── 📂 tests/                    # Test files
    ├── test_audio_decode_only.py
    ├── test_webm_opus_decoding.py
    ├── ws_smoke_test.py
    └── test_audio/
        └── *.wav, *.webm
```

### Backend Key Components

#### 1. **main.py** - Application Entry Point
- FastAPI app initialization
- Lifespan events (startup/shutdown)
- Middleware setup (CORS, logging)
- Model loading during startup
- FFmpeg availability check

#### 2. **core/config.py** - Configuration Management
- `Settings` class with PydanticSettings
- Environment variables loading
- Model path validation
- Default values for all settings

#### 3. **models/** - AI Model Wrappers
- **phowhisper_asr.py**: PhoWhisper Speech-to-Text wrapper
  - Audio preprocessing (resample to 16kHz)
  - Inference with PyTorch
  - Error handling
- **classifier.py**: PhoBERT toxic detection wrapper
  - Text classification (4 classes)
  - Keyword-based ensemble
  - Confidence scoring

#### 4. **services/audio_processor.py** - Main Processing Logic
- Audio decoding (WebM, WAV, etc.)
- Format detection and conversion
- ASR inference orchestration
- Classification orchestration
- WebSocket message handling

#### 5. **api/v1/endpoints.py** - API Endpoints
- WebSocket endpoint: `/v1/ws`
  - Real-time audio streaming
  - Session management
  - Error handling
- REST endpoints:
  - `/health` - Health check
  - `/v1/status` - System status

## 🎨 Frontend Structure

```
frontend/
├── 📄 package.json              # Node.js dependencies
├── 📄 vite.config.ts            # Vite configuration
├── 📄 tsconfig.json             # TypeScript configuration
├── 📄 tailwind.config.ts        # Tailwind CSS configuration
├── 📄 components.json           # Shadcn UI configuration
│
├── 📄 index.html                # HTML entry point
├── 📂 public/                   # Static assets
│
└── 📂 src/
    ├── 📄 main.tsx              # React entry point
    ├── 📄 App.tsx               # Root component
    ├── 📄 index.css             # Global styles
    │
    ├── 📂 components/           # React components
    │   ├── ui/                  # Shadcn UI components
    │   │   ├── button.tsx
    │   │   ├── card.tsx
    │   │   ├── progress.tsx
    │   │   └── ...
    │   ├── AudioRecorder.tsx    # Main recording component
    │   ├── TranscriptDisplay.tsx
    │   ├── WaveformVisualizer.tsx
    │   └── ...
    │
    ├── 📂 hooks/                # Custom React hooks
    │   ├── useAudioRecorder.ts  # Audio recording logic
    │   ├── useWebSocket.ts      # WebSocket connection
    │   └── ...
    │
    ├── 📂 stores/               # Zustand state management
    │   ├── transcriptStore.ts   # Transcript state
    │   ├── audioStore.ts        # Audio state
    │   └── ...
    │
    ├── 📂 schemas/              # Zod validation schemas (1 per file)
    │   ├── audio.schema.ts
    │   ├── transcript.schema.ts
    │   └── ...
    │
    ├── 📂 types/                # TypeScript types (1 per file)
    │   ├── audio.types.ts
    │   ├── transcript.types.ts
    │   └── ...
    │
    ├── 📂 utils/                # Utility functions
    │   ├── audio.utils.ts
    │   ├── websocket.utils.ts
    │   └── ...
    │
    └── 📂 lib/                  # Third-party lib configs
        └── utils.ts             # cn() helper, etc.
```

### Frontend Key Components

#### 1. **main.tsx** - React Entry Point
- React root rendering
- Global providers setup

#### 2. **App.tsx** - Root Component
- Main layout
- Component composition
- Error boundaries

#### 3. **components/AudioRecorder.tsx** - Main Feature Component
- Audio recording UI
- Start/stop controls
- WebSocket integration
- Real-time feedback

#### 4. **hooks/useAudioRecorder.ts** - Recording Logic
- MediaRecorder API
- Audio chunk handling
- Format conversion (WebM Opus)
- Error handling

#### 5. **hooks/useWebSocket.ts** - WebSocket Communication
- Connection management
- Reconnection logic
- Message serialization
- Event handling

#### 6. **stores/** - State Management (Zustand)
- Global state for transcripts
- Audio recording state
- WebSocket connection state
- UI state (loading, errors)

#### 7. **schemas/** - Validation (Zod v4)
- Runtime validation
- Type inference
- API response validation
- Form validation

## 🔄 Data Flow

### Real-time Transcription Flow

```
User clicks "Record"
    ↓
useAudioRecorder hook starts MediaRecorder
    ↓
Audio chunks (2s intervals) → Base64 encoding
    ↓
useWebSocket sends chunks to backend
    ↓
Backend receives via WebSocket
    ↓
AudioProcessor decodes audio
    ↓
PhoWhisperASR.transcribe()
    ↓
LocalPhoBERTClassifier.classify()
    ↓
Backend sends result via WebSocket
    ↓
Frontend receives & validates (Zod)
    ↓
Zustand store updates
    ↓
UI re-renders with transcript
```

## 📝 File Naming Conventions

### Backend (Python)
- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`

### Frontend (TypeScript)
- **Components**: `PascalCase.tsx`
- **Hooks**: `useCamelCase.ts`
- **Utilities**: `camelCase.utils.ts`
- **Types**: `camelCase.types.ts`
- **Schemas**: `camelCase.schema.ts`
- **Stores**: `camelCaseStore.ts`

## 🔐 Environment Variables

### Backend (.env)
```bash
# Server
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Models
ASR_MODEL_PATH=../PhoWhisper-small
CLASSIFIER_MODEL_PATH=../phobert-vi-comment-4class
MODEL_DEVICE=cpu

# Audio
TARGET_SAMPLE_RATE=16000
AUDIO_CHUNK_DURATION=2.0

# CORS
BACKEND_CORS_ORIGINS=http://localhost:5173
```

### Frontend (configs/default.json)
```json
{
  "api": {
    "baseURL": "http://127.0.0.1:8000",
    "wsURL": "ws://127.0.0.1:8000/v1/ws"
  }
}
```

## 📦 Dependencies Overview

### Backend (Python)
- **FastAPI**: Web framework
- **PyTorch**: ML framework
- **Transformers**: HuggingFace models
- **torchaudio**: Audio processing
- **ONNX Runtime**: Inference optimization
- **structlog**: Structured logging

### Frontend (Node.js)
- **React 19**: UI framework
- **Vite**: Build tool
- **TypeScript**: Type safety
- **Zustand**: State management
- **Zod v4**: Schema validation
- **Tailwind CSS**: Styling
- **Shadcn UI**: UI components
- **WaveSurfer.js**: Audio visualization

## 🚀 Build & Deploy

### Development
```bash
# Backend
cd backend && python run_server.py

# Frontend
cd frontend && npm run dev
```

### Production (Future)
```bash
# Backend
cd backend && gunicorn app.main:app

# Frontend
cd frontend && npm run build
# Serve dist/ with nginx or similar
```

## 📊 Size Estimates

- **Models**: ~2.5GB (PhoWhisper + PhoBERT)
- **Backend dependencies**: ~1.5GB (PyTorch, etc.)
- **Frontend node_modules**: ~500MB
- **Total**: ~4.5GB

---

For more details, see:
- [README.md](README.md) - Main documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide
- [CHANGELOG.md](CHANGELOG.md) - Version history
