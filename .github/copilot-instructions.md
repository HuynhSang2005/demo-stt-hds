# AI Agent Instructions – Local-First Speech-to-Text + Toxic Detection (Vietnamese)

## 🧠 Vai trò của AI Agent
- Hỗ trợ triển khai hệ thống **offline-first**, **real-time**.
- Ưu tiên **load model từ local path** (đã `git clone` từ Hugging Face).

## 📂 Cấu trúc model local (giả định)
- `./models/wav2vec2-base-vietnamese-250h/` → chứa `config.json`, `pytorch_model.bin`, `processor_config.json`, v.v.
- `./models/phobert-vi-comment-4class/` → chứa `config.json`, `pytorch_model.bin`, `tokenizer_config.json`, v.v.

## 🧱 Design Pattern & Nguyên tắc
- **Backend**: Clean Architecture, Strategy Pattern (dễ thay model), Dependency Injection.
- **Frontend**: Custom hooks (`useAudioRecorder`, `useWebSocket`), Zustand cho state real-time.
- **Model loading**: Dùng `from_pretrained(local_path, local_files_only=True)` để đảm bảo offline.

## 🔍 Kỹ thuật coding
- **Python**: `torchaudio` để resample → 16kHz, `onnxruntime` nếu đã export ONNX.
- **TypeScript**: Strict typing cho `TranscriptResult`.
- **Real-time**: Chunk audio ~2s, không buffer quá 5s.

## 🔁 Cách AI Agent research
- Khi cần export ONNX: tìm `transformers.onnx.export local model`
- Khi xử lý audio: tìm `torchaudio.load from bytes`
- Luôn kiểm tra: **model có chạy offline không?**

## ⚠️ Lưu ý đặc biệt
- **Không gọi Hugging Face Hub** – tất cả model đã có local.
- **Chỉ cảnh báo khi label = "toxic" hoặc "negative"**.
- **Audio input < 10s** (yêu cầu Wav2Vec2).
- **Resample ở BE** → dùng `torchaudio.functional.resample`.