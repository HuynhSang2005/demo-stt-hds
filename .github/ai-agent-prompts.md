# AI Agent Task Prompts – Offline-First Speech-to-Text + Toxic Detection (Vietnamese)

> **Mục tiêu**: Xây dựng webapp local, **offline**, **real-time**, dùng **2 mô hình đã clone sẵn**:
> - `./models/wav2vec2-base-vietnamese-250h/`
> - `./models/phobert-vi-comment-4class/`
> 
> **Yêu cầu chung**:
> - Không gọi Hugging Face Hub (offline-only)
> - 
> - Real-time qua WebSocket (chunk ~2s)
> - Chỉ cảnh báo khi label = `"toxic"` hoặc `"negative"`

---

## 🔹 GIAI ĐOẠN 1: XÁC MINH MODEL LOCAL

### ✅ Prompt 1.1 – Kiểm tra tính toàn vẹn model
> "Kiểm tra folder `./models/wav2vec2-base-vietnamese-250h/` có đủ các file sau:
> - `config.json`
> - `pytorch_model.bin`
> - `processor_config.json`
> - `vocab.json`
> - `tokenizer_config.json`
> 
> Tương tự, kiểm tra `./models/phobert-vi-comment-4class/` có:
> - `config.json`
> - `pytorch_model.bin`
> - `tokenizer_config.json`
> - `special_tokens_map.json`
> 
> Nếu thiếu file nào → báo lỗi rõ ràng."

### ✅ Prompt 1.2 – Xác minh load model offline
> "Viết script Python `verify_models.py`:
> - Dùng `Wav2Vec2Processor.from_pretrained(local_path, local_files_only=True)`
> - Dùng `Wav2Vec2ForCTC.from_pretrained(...)` tương tự
> - Dùng `pipeline('text-classification', model=..., local_files_only=True)`
> - In ra: `'✅ ASR loaded'`, `'✅ Classifier loaded'`
> - Nếu lỗi → in traceback và dừng"

---

## 🔹 GIAI ĐOẠN 2: BACKEND – OFFLINE INFERENCE & FASTAPI SETUP

### ✅ Prompt 2.1 – Cấu hình dự án FastAPI
> "Tạo thư mục `backend/` với cấu trúc:
> ```
> backend/
> ├── app/
> │   ├── main.py
> │   ├── core/
> │   │   ├── __init__.py
> │   │   ├── config.py        # PydanticSettings: model_paths
> │   │   └── logger.py        # JSON structured logger
> │   ├── models/
> │   │   ├── __init__.py
> │   │   ├── asr.py           # LocalWav2Vec2ASR
> │   │   └── classifier.py    # LocalPhoBERTClassifier
> │   ├── schemas/
> │   │   └── audio.py         # Pydantic: TranscriptResult
> │   ├── services/
> │   │   └── audio_processor.py  # resample + pipeline
> │   └── api/
> │       └── v1/
> │           └── endpoints.py # WebSocket route
> ├── requirements.txt
> └── README.md
> ```
> - `requirements.txt` phải có: `fastapi`, `uvicorn`, `torch`, `transformers`, `torchaudio`, `onnxruntime` (tùy chọn)
> - `config.py`: định nghĩa `ASR_MODEL_PATH = './models/wav2vec2-base-vietnamese-250h'`, `CLASSIFIER_MODEL_PATH = './models/phobert-vi-comment-4class'`"

### ✅ Prompt 2.2 – Triển khai ASR model từ local
> "Trong `backend/app/models/asr.py`, viết class `LocalWav2Vec2ASR`:
> - `__init__(self, model_path: str)`: load processor + model với `local_files_only=True`
> - `transcribe(self, audio_bytes: bytes) -> str`:
>   1. Dùng `io.BytesIO(audio_bytes)` → `torchaudio.load()`
>   2. Nếu sample rate ≠ 16000 → resample bằng `torchaudio.functional.resample`
>   3. Đảm bảo waveform shape = `(1, T)`
>   4. Dùng processor → input_values → model → argmax → decode
>   5. Trả về text (str), không có dấu ngoặc, không log
> - Xử lý exception → trả `'[ASR_ERROR]'`"

### ✅ Prompt 2.3 – Triển khai classifier từ local
> "Trong `backend/app/models/classifier.py`, viết class `LocalPhoBERTClassifier`:
> - `__init__(self, model_path: str)`: load pipeline với `local_files_only=True`
> - `predict(self, text: str) -> dict`:
>   - Nếu text rỗng → trả `{'label': 'neutral', 'score': 1.0}`
>   - Gọi pipeline → trả `{'label': str, 'score': float}`
>   - Chỉ chấp nhận 4 label: `positive|negative|neutral|toxic`"

### ✅ Prompt 2.4 – WebSocket endpoint real-time
> "Trong `backend/app/api/v1/endpoints.py`:
> - Viết endpoint `websocket_endpoint(websocket: WebSocket)`:
>   1. `await websocket.accept()`
>   2. Vòng lặp `while True`:
>      - `data = await websocket.receive_bytes()`
>      - Gọi `audio_processor.process(data)` → trả `TranscriptResult`
>      - `await websocket.send_json(result.dict())`
>   3. Bắt exception → log lỗi, không crash
> - Đăng ký route: `@app.websocket('/v1/ws')` trong `main.py`"

---

## 🔹 GIAI ĐOẠN 3: FRONTEND – REAL-TIME UI & WEBSOCKET

### ✅ Prompt 3.1 – Cấu hình dự án React + Vite
> "Tạo thư mục `frontend/` với:
> ```
> frontend/
> ├── src/
> │   ├── app/page.tsx
> │   ├── hooks/
> │   │   ├── useAudioRecorder.ts
> │   │   └── useWebSocket.ts
> │   ├── store/useStore.ts     # Zustand
> │   ├── components/
> │   │   ├── TranscriptDisplay.tsx
> │   │   └── RecordingButton.tsx
> │   └── types/index.ts        # TranscriptResult
> ├── tailwind.config.ts
> └── package.json
> ```
> - Cài: `react`, `vite`, `zustand`, `wavesurfer.js`, `@radix-ui/react-*`, `shadcn-ui`
> - Không cài đặt `axios` (chỉ dùng WebSocket)"

### ⚠️ FE: Zod v4 + folder-pattern rules (MANDATORY)

- Thêm dependency `zod` (v4) và `@hookform/resolvers` vào `frontend/package.json`.
- Sử dụng Zod v4 cho runtime schema validation và infer types cho TypeScript.
- Pattern bắt buộc về file/folder:
	- `src/schemas/` → mỗi file chứa 1 Zod schema (ví dụ `transcript.schema.ts` exporting `TranscriptSchema`).
	- `src/types/` hoặc `src/interfaces/` → mỗi file chứa 1 TypeScript type/interface. Không định nghĩa types trong cùng file với schema. Ví dụ: `src/types/transcript.ts` có `export type Transcript = z.infer<typeof TranscriptSchema>`.
	- Không gom nhiều schema/type vào một file.

### 🔗 React Hook Form + Zod (recommended integration)

- Install: `npm i react-hook-form @hookform/resolvers zod`
- Usage pattern:
	- define schema in `src/schemas/transcript.schema.ts`:
		```ts
		import { z } from 'zod'
		export const TranscriptSchema = z.object({
			text: z.string(),
			label: z.enum(['positive','negative','neutral','toxic']),
			confidence: z.number().min(0).max(1),
			timestamp: z.number().optional()
		})
		```
	- infer types in `src/types/transcript.ts`:
		```ts
		import { z } from 'zod'
		import { TranscriptSchema } from '../schemas/transcript.schema'
		export type Transcript = z.infer<typeof TranscriptSchema>
		```
	- use in component with react-hook-form:
		```ts
		const form = useForm({ resolver: zodResolver(TranscriptSchema) })
		```

### 🎨 Shadcn UI guidance (templates & components)

- Use official site `https://ui.shadcn.com/docs` to pick components and templates.
- Recommended components for this project: `Badge`, `Alert`, `Toast`, `List`, `Card`, `Button`, `Form` components.
- Keep UI wrappers in `src/components/ui/` so you can swap underlying implementations easily.

### 🔎 Research rule for AI agent

- BEFORE making FE changes, the AI agent must research and cite official docs (Zod v4 API, React Hook Form + Zod resolver, Shadcn UI components) in the commit/PR description. Include minimal usage snippets where helpful.

### ✅ Prompt 3.2 – Hook ghi âm real-time
> "Viết `useAudioRecorder.ts`:
> - Trả về: `{ isRecording: boolean, startRecording: () => void, stopRecording: () => void }`
> - Bên trong:
>   - `useRef<MediaRecorder | null>(null)`
>   - `navigator.mediaDevices.getUserMedia({ audio: true })`
>   - `new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })`
>   - `ondataavailable`: gửi `e.data.arrayBuffer()` qua callback `onChunk`
>   - `onstop`: cleanup
> - Chunk interval: 2000ms"

### ✅ Prompt 3.3 – Hook WebSocket client
> "Viết `useWebSocket.ts`:
> - Nhận `onMessage: (data: TranscriptResult) => void`
> - Tự động connect đến `ws://localhost:8000/v1/ws`
> - Phương thức `sendAudioChunk(chunk: ArrayBuffer)`
> - Xử lý reconnect (3 lần, delay 1s)
> - Dùng `useRef<WebSocket>` để tránh re-create"

### ✅ Prompt 3.4 – UI hiển thị real-time
> "Tạo component `TranscriptDisplay.tsx`:
> - Dùng Zustand store: `transcripts: { id: string; text: string; label: string; warning: boolean }[]`
> - Map qua mảng → render từng dòng
> - Nếu `warning: true`:
>   - Dùng `<Badge variant='destructive'>{label}</Badge>`
>   - Dòng text có nền `bg-red-50/20`
> - Cuộn tự động xuống cuối khi có dòng mới"

---

## 🔹 GIAI ĐOẠN 4: INTEGRATION & VALIDATION

### ✅ Prompt 4.1 – Test end-to-end real-time
> "Viết hướng dẫn test:
> 1. Chạy BE: `cd backend && uvicorn app.main:app --reload --port 8000`
> 2. Chạy FE: `cd frontend && npm run dev`
> 3. Mở `http://localhost:5173`
> 4. Nhấn 'Start Recording'
> 5. Nói: 'Đồ ngốc, mày thật là tệ!'
> 6. Kiểm tra:
>    - FE hiển thị text phải đúng
>    - Có badge 'toxic' màu đỏ
>    - Latency < 2.5s
> 7. Log BE không có lỗi decode"

### ✅ Prompt 4.2 – Viết README.md chuẩn dev Việt
> "Tạo `README.md` ở root:
> - Tiêu đề: 'Demo Local: Speech-to-Text + Phát hiện nội dung độc hại (Tiếng Việt)'
> - Mục 'Yêu cầu':
>   - Python 3.11+, Node 22+
>   - Đã clone 2 model vào `./models/`
> - Mục 'Cách chạy':
>   ```bash
>   # Backend
>   cd backend
>   pip install -r requirements.txt
>   uvicorn app.main:app --port 8000
> 
>   # Frontend
>   cd frontend
>   npm install
>   npm run dev
>   ```
> - Mục 'License':
>   - 'Mô hình ASR: CC BY-NC 4.0 – chỉ dùng phi thương mại'
>   - Trích dẫn Zenodo và email tác giả PhoBERT
> - Mục 'Demo': ảnh minh họa (placeholder)"

---

## 🚫 CẤM
- Gọi Hugging Face Hub
- Dùng librosa (phải dùng torchaudio)
- Dùng Axios hoặc REST API

## ✅ HOÀN THÀNH KHI
- [ ] Chạy local không cần internet
- [ ] Nói → ra text → phát hiện 'toxic'
- [ ] Có test đơn vị (BE + FE)
- [ ] Có README rõ ràng, trích dẫn đầy đủ