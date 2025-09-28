# Backend: FastAPI AI Worker – Offline-First, Local Models

## 🗂️ Folder Structure
```
project/
├── models/                                     ← ĐÃ TỒN TẠI ở root folder có tên là phobert-vi-comment-4class và wav2vec2-base-vietnamese-250h nên có lựa chọn những model này với các file phù hợp.
│   ├── wav2vec2-base-vietnamese-250h/
│   └── phobert-vi-comment-4class/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── logger.py
│   │   ├── models/
│   │   │   ├── asr.py          # Load Wav2Vec2 từ local
│   │   │   └── classifier.py   # Load PhoBERT từ local
│   │   ├── schemas/
│   │   │   └── audio.py
│   │   ├── services/
│   │   │   └── audio_processor.py
│   │   └── api/v1/endpoints.py
│   └── tests/...
├── scripts/
│   └── export_onnx_local.py    # (Tùy chọn) Export ONNX từ model local
└── requirements.txt
```

## ⚙️ Framework & Libs
- **FastAPI** v0.110+
- **torch**, **transformers**, **torchaudio**
- **onnxruntime** (nếu dùng ONNX)
- **pydantic**, **pytest**, **httpx**

## 🧠 Load model từ local (offline)
```python
# ASR
processor = Wav2Vec2Processor.from_pretrained(
    "./models/wav2vec2-base-vietnamese-250h",
    local_files_only=True
)
model = Wav2Vec2ForCTC.from_pretrained(
    "./models/wav2vec2-base-vietnamese-250h",
    local_files_only=True
)

# Classifier
classifier = pipeline(
    "text-classification",
    model="./models/phobert-vi-comment-4class",
    tokenizer="./models/phobert-vi-comment-4class",
    local_files_only=True
)
```

## 🔄 Real-time Workflow
1. Nhận `bytes` (webm/opus) qua WebSocket
2. Dùng `torchaudio.load(io.BytesIO(...))` → waveform + sample rate
3. Resample về **16000 Hz** nếu cần
4. ASR → text
5. Classify → label
6. Trả `{text, label, warning: label in ["toxic", "negative"]}`

## 🧪 Testing
- **Unit**: Mock `torchaudio.load`, test logic
- **E2E**: Gửi audio chunk thật → kiểm tra output

## 📜 License Compliance
- Model ASR: **CC BY-NC 4.0** → chỉ dùng phi thương mại
- Trích dẫn Zenodo khi demo/public:
  ```bibtex
  @misc{Thai_Binh_Nguyen_wav2vec2_vi_2021, ...}
  ```
- Tác giả PhoBERT: Hà Văn Hải (vanhai11203@gmail.com) – ghi nhận trong README
```

---
