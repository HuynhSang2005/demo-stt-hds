# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-06

### 🎉 Major Changes

#### Migrated from Wav2Vec2 to PhoWhisper
- **Breaking**: Replaced `wav2vec2-base-vietnamese-250h` with `PhoWhisper-small`
- **Reason**: Better accuracy, auto punctuation, unlimited audio length
- **Model size**: 244M parameters (vs 95M in Wav2Vec2)
- **Performance**: Improved WER (Word Error Rate)

### ✨ Added

#### Documentation
- `README.md` - Comprehensive Vietnamese documentation with:
  - System requirements
  - Installation guide (Windows/Linux/macOS)
  - Troubleshooting section
  - API documentation
  - Architecture overview
- `QUICKSTART.md` - Quick setup guide for developers
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - This file

#### Setup Automation
- `check-dependencies.py` - Pre-setup dependency checker
  - Validates Python, Node.js, FFmpeg versions
  - Checks disk space
  - Verifies models existence
- `setup.ps1` - Windows PowerShell setup script
- `setup.sh` - Linux/macOS bash setup script

#### Backend Improvements
- Added `huggingface-hub==0.19.4` to requirements.txt (was missing)
- Updated `.env.example` with correct model paths
- Added FFmpeg availability check in startup
- Improved error messages for missing dependencies

#### Simplified for Beginners
- Removed CI/CD pipeline (not needed for local development)
- Focus on easy setup and clear documentation

#### Frontend
- Zod v4 schema validation
- TypeScript strict mode
- Improved type safety

### 🔧 Changed

#### Configuration
- Updated `ASR_MODEL_PATH` default from `../wav2vec2-base-vietnamese-250h` to `../PhoWhisper-small`
- Improved `.env.example` with clearer comments

#### .gitignore
- Restructured with clear sections
- Added AI models paths (phobert, PhoWhisper)
- Added test coverage folders
- Added ONNX files
- Better organization

### 📝 Documentation

- All docs now in Vietnamese for better accessibility
- Step-by-step installation guides
- Platform-specific instructions
- Common troubleshooting scenarios

### 🐛 Fixed

- Missing `huggingface-hub` dependency causing download_models.py to fail
- Inconsistent model path in config vs actual downloaded model name
- Missing FFmpeg check causing cryptic errors

---

## [1.0.0] - Initial Release

### ✨ Features

#### Backend (FastAPI)
- FastAPI REST API and WebSocket server
- Wav2Vec2 Vietnamese ASR (replaced in v2.0.0)
- PhoBERT toxic detection (4 classes)
- Real-time audio processing
- Batch inference support
- Structured logging with structlog
- CORS middleware
- Error handling

#### Frontend (React + TypeScript)
- Real-time audio recording
- WebSocket communication
- Audio waveform visualization (WaveSurfer.js)
- Sentiment-based UI feedback
- Zustand state management
- Tailwind CSS + Shadcn UI
- TypeScript strict mode

#### Features
- Offline-first architecture
- Local model inference
- WebM/Opus audio support (via FFmpeg)
- Real-time transcription
- Toxic content detection
- Audio chunk processing (2s chunks)

---

## Versioning Strategy

- **Major (X.0.0)**: Breaking changes, major features, architecture changes
- **Minor (x.X.0)**: New features, non-breaking changes
- **Patch (x.x.X)**: Bug fixes, documentation updates

## Links

- [Repository](https://github.com/HuynhSang2005/demo-stt-hds)
- [Issues](https://github.com/HuynhSang2005/demo-stt-hds/issues)
- [Pull Requests](https://github.com/HuynhSang2005/demo-stt-hds/pulls)
