# API Contract: FE ↔ BE (WebSocket)

## 🌐 Endpoint
- **URL**: `ws://localhost:8000/v1/ws`
- **Protocol**: WebSocket (không có REST fallback)

## 📤 Gửi từ FE → BE
- **Dạng**: `ArrayBuffer` (raw audio bytes, định dạng `webm/opus`)
- **Tần suất**: mỗi 2 giây (hoặc khi `MediaRecorder` emit `dataavailable`)
- **Không có JSON wrapper** → tiết kiệm băng thông

## 📥 Nhận từ BE → FE
- **Dạng**: JSON
- **Schema**:
  ```ts
  interface TranscriptResult {
    text: string;          // "Đây là nội dung độc hại"
    label: "positive" | "negative" | "neutral" | "toxic";
    warning: boolean;      // true nếu label = "negative" hoặc "toxic"
    timestamp: number;     // Date.now()
  }
  ```

## 🪵 Logging (BE)
- Dùng **structured JSON log** (Python `structlog`)
- Log: `{"event": "asr_success", "text": "...", "latency_ms": 320}`
- Log error: `{"event": "audio_decode_failed", "error": "..."}`

## ❌ Xử lý lỗi
- **FE**: Nếu WebSocket disconnect → thử reconnect 3 lần, sau đó báo lỗi
- **BE**: Nếu audio không decode được → gửi `{text: "[ERROR]", label: "neutral", warning: false}`

## 🚫 Không có REST API
- Toàn bộ giao tiếp real-time qua **WebSocket**
- Không cần Axios, không cần HTTP route

## ✅ Đảm bảo contract
- Cả FE và BE dùng **cùng interface `TranscriptResult`**
- BE validate input bằng `try/except` → không crash
- FE luôn kiểm tra `typeof data === 'object'` trước khi dùng
```
