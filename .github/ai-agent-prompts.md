# AI Agent Task Prompts – Offline-First Local Demo

> Mục tiêu: Dùng **model đã download offline** để chạy **offline**, **real-time**, 
---

## 🔹 GIAI ĐOẠN 1: XÁC MINH MODEL LOCAL

### Prompt 1.1
> "Kiểm tra folder `./models/wav2vec2-base-vietnamese-250h/` có đủ file:
> - `config.json`, `pytorch_model.bin`, `processor_config.json`, `vocab.json`
> Tương tự với `phobert-vi-comment-4class`"

### Prompt 1.2
> "Viết script Python kiểm tra load model offline:
> ```python
> from transformers import Wav2Vec2Processor, pipeline
> processor = Wav2Vec2Processor.from_pretrained('./models/...', local_files_only=True)
> classifier = pipeline('text-classification', model='./models/...', local_files_only=True)
> print('✅ Load thành công')
> ```"

---

## 🔹 GIAI ĐOẠN 2: BACKEND – OFFLINE INFERENCE

### Prompt 2.1
> "Viết class `LocalWav2Vec2ASR`:
> - Load model + processor từ `./models/wav2vec2-base-vietnamese-250h`
> - Phương thức `transcribe(waveform: torch.Tensor, sample_rate: int) -> str`
> - Tự động resample về 16kHz nếu cần"

### Prompt 2.2
> "Viết class `LocalPhoBERTClassifier`:
> - Load từ `./models/phobert-vi-comment-4class`
> - Trả về `{label, score}` cho input text
> - Xử lý text rỗng → trả `neutral`"

---

## 🔹 GIAI ĐOẠN 3: FRONTEND – REAL-TIME UI

### Prompt 3.1
> "Tạo React component `RecordingPanel`:
> - Nút Start/Stop
> - Dùng `useAudioRecorder` (MediaRecorder)
> - Gửi chunk qua WebSocket mỗi 2s"

### Prompt 3.2
> "Tạo component `TranscriptList`:
> - Hiển thị các dòng transcript
> - Nếu `warning: true` → nền đỏ nhẹ, icon ⚠️
> - Dùng Shadcn `Badge` với variant='destructive' cho label 'toxic'"

---

## 🔹 GIAI ĐOẠN 4: INTEGRATION

### Prompt 4.1
> "Kết nối FE ↔ BE qua WebSocket:
> - FE gửi: raw `ArrayBuffer` (không encode)
> - BE trả: JSON đúng schema
> - Test bằng cách nói: 'Đồ ngốc!' → phải ra `label: 'toxic'`"

### Prompt 4.2
> "Viết README.md:
> - Hướng dẫn chạy: `cd backend && uvicorn app.main:app`
> - `cd frontend && npm run dev`
> - Ghi rõ: 'Chỉ dùng cho mục đích học tập – CC BY-NC 4.0'"