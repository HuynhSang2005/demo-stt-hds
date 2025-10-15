# 📋 Hướng Dẫn Sử Dụng Demo STT Tiếng Việt

<div align="center">

![Hướng Dẫn Sử Dụng](https://img.shields.io/badge/Hướng%20Dẫn-Sử%20Dụng-green?style=for-the-badge)
![Tiếng Việt](https://img.shields.io/badge/Ngôn%20Ngữ-Tiếng%20Việt-red?style=for-the-badge)

**Hướng dẫn chi tiết về cách cài đặt, cấu hình và xử lý sự cố**

[🏠 Về README](./README.md) • [🚀 Bắt Đầu Nhanh](#-hướng-dẫn-bắt-đầu-nhanh) • [🔧 Setup Nâng Cao](#-setup-nâng-cao)

</div>

## 📚 Mục Lục

- [🚀 Hướng Dẫn Bắt Đầu Nhanh](#-hướng-dẫn-bắt-đầu-nhanh)
- [🔧 Setup Nâng Cao](#-setup-nâng-cao)
- [⚙️ Cấu Hình](#️-cấu-hình)
- [🎯 Ví Dụ Sử Dụng](#-ví-dụ-sử-dụng)
- [🚨 Xử Lý Sự Cố](#-xử-lý-sự-cố)
- [🔍 Debug](#-debug)
- [📊 Tối Ưu Hiệu Suất](#-tối-ưu-hiệu-suất)
- [🔒 Bảo Mật](#-bảo-mật)

## 🚀 Hướng Dẫn Bắt Đầu Nhanh

### Kiểm Tra Yêu Cầu

Trước khi bắt đầu, đảm bảo bạn có:

```bash
# Kiểm tra phiên bản Python (3.10+ cần thiết)
python --version

# Kiểm tra phiên bản Node.js (22+ cần thiết)
node --version

# Kiểm tra phiên bản npm
npm --version
```

### Setup Một Lệnh

```bash
# Clone và setup tất cả
git clone https://github.com/your-username/vietnamese-stt-demo.git
cd vietnamese-stt-demo
python setup.py
```

Lệnh này sẽ tự động:
- ✅ Cài đặt tất cả dependencies Python
- ✅ Cài đặt tất cả dependencies Node.js  
- ✅ Tải mô hình AI từ Hugging Face
- ✅ Chuyển đổi mô hình sang ONNX để tăng hiệu suất
- ✅ Xác minh mọi thứ hoạt động

### Khởi Động Demo

```bash
# Khởi động cả backend và frontend
python start.py
```

Sau đó mở: http://localhost:5173

## 🔧 Setup Nâng Cao

### Setup Chỉ Backend

Nếu bạn chỉ cần API backend:

```bash
cd backend
pip install -r requirements.txt

# Tải mô hình thủ công
python -c "
from huggingface_hub import snapshot_download
snapshot_download('vinai/PhoWhisper-small', local_dir='../PhoWhisper-small')
snapshot_download('vanhai123/phobert-vi-comment-4class', local_dir='../phobert-vi-comment-4class')
"

# Chuyển đổi sang ONNX (tùy chọn nhưng khuyến nghị)
python convert_models_to_onnx.py

# Khởi động backend
python start.py
```

### Setup Chỉ Frontend

Nếu bạn đã có backend đang chạy:

```bash
cd frontend
npm install
npm run dev
```

### Setup Docker (Sắp Có)

```bash
# Build và chạy với Docker Compose
docker-compose up --build
```

## ⚙️ Cấu Hình

### Cấu Hình Backend

Chỉnh sửa `backend/app/core/config.py` cho các cài đặt nâng cao:

```python
class Settings(BaseSettings):
    # Cấu hình API
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "Demo STT Tiếng Việt"
    
    # Cấu hình mô hình
    ONNX_ENABLED: bool = True
    ONNX_AUTO_CONVERT: bool = True
    PREFER_ONNX: bool = True
    
    # Cài đặt hiệu suất
    MAX_AUDIO_CHUNK_SIZE: int = 1024 * 256  # 256KB
    AUDIO_PROCESSING_TIMEOUT: int = 30  # giây
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
```

### Cấu Hình Frontend

Chỉnh sửa `frontend/src/lib/config.ts` cho cài đặt frontend:

```typescript
export interface AppConfig {
  backend: {
    host: string
    port: number
    wsUrl: string
  }
  environment: 'development' | 'production'
}

// Cấu hình mặc định
const defaultConfig: AppConfig = {
  backend: {
    host: '127.0.0.1',
    port: 8000,
    wsUrl: 'ws://127.0.0.1:8000/v1/ws'
  },
  environment: 'development'
}
```

### Biến Môi Trường

Tạo file `.env` trong thư mục gốc:

```bash
# Cấu hình Backend
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
LOG_LEVEL=INFO
ONNX_ENABLED=true

# Cấu hình Frontend  
VITE_API_HOST=127.0.0.1
VITE_API_PORT=8000
VITE_WS_URL=ws://127.0.0.1:8000/v1/ws
```

## 🎯 Ví Dụ Sử Dụng

### Sử Dụng Cơ Bản

1. **Bắt Đầu Ghi Âm**
   - Nhấn nút "Bắt đầu ghi"
   - Cho phép truy cập microphone khi được yêu cầu
   - Nói tiếng Việt rõ ràng

2. **Xem Kết Quả**
   - Bản ghi thời gian thực xuất hiện
   - Phân tích sentiment hiển thị: Tích cực/Tiêu cực/Trung tính/Độc hại
   - Từ khóa xấu được tô đỏ
   - Điểm độ tin cậy được hiển thị

3. **Dừng Ghi Âm**
   - Nhấn nút "Dừng ghi"
   - Xem kết quả cuối cùng và tóm tắt phiên

### Tính Năng Nâng Cao

#### Chế Độ Phiên vs Thời Gian Thực

```typescript
// Chuyển đổi giữa chế độ phiên và thời gian thực
const [sessionMode, setSessionMode] = useState(true)

// Chế độ Phiên: Tích lũy các chunk audio để xử lý hoàn chỉnh
// Chế độ Thời gian thực: Xử lý các chunk audio ngay lập tức
```

#### Cài Đặt Audio Tùy Chỉnh

```typescript
// Điều chỉnh cài đặt ghi âm
const audioConfig = {
  chunkDuration: 1000,        // Chunk 1 giây
  enableVolumeDetection: true, // Giám sát volume thời gian thực
  autoStart: false,           // Bắt đầu/dừng thủ công
  deviceId: 'default'         // Thiết bị microphone cụ thể
}
```

#### Quản Lý Kết Nối WebSocket

```typescript
// Giám sát trạng thái kết nối
const { isConnected, connectionStatus } = useSessionWebSocket(wsUrl, {
  onConnectionStatusChange: (status, message) => {
    console.log(`Trạng thái WebSocket: ${status} - ${message}`)
  },
  autoReconnect: true,
  enableDebug: import.meta.env.DEV
})
```

## 🚨 Xử Lý Sự Cố

### Các Vấn Đề Thường Gặp và Giải Pháp

#### 1. Vấn Đề Quyền Truy Cập Microphone

**Vấn đề**: Lỗi "Quyền truy cập microphone bị từ chối"

**Giải pháp**:
```bash
# Kiểm tra quyền trình duyệt
# Chrome: Cài đặt > Bảo mật và quyền riêng tư > Cài đặt trang web > Microphone
# Firefox: about:preferences#privacy > Quyền > Microphone

# Cho phát triển localhost
# Đảm bảo bạn đang sử dụng http://localhost:5173 (không phải 127.0.0.1)

# Cho triển khai production
# HTTPS là bắt buộc cho truy cập microphone
```

#### 2. Mô Hình Không Tải Được

**Vấn đề**: Lỗi "Không tìm thấy mô hình" hoặc "Không thể tải mô hình"

**Giải pháp**:
```bash
# Tải lại mô hình
rm -rf PhoWhisper-small phobert-vi-comment-4class
python setup.py

# Kiểm tra dung lượng ổ đĩa (cần ~2GB cho mô hình)
df -h

# Xác minh files mô hình
ls -la PhoWhisper-small/
ls -la phobert-vi-comment-4class/

# Nên thấy các file như: config.json, pytorch_model.bin, v.v.
```

#### 3. Kết Nối WebSocket Thất Bại

**Vấn đề**: Lỗi "Kết nối WebSocket thất bại"

**Giải pháp**:
```bash
# Kiểm tra xem backend có đang chạy không
curl http://localhost:8000/health

# Kiểm tra cài đặt tường lửa
# Windows: Windows Defender Firewall
# macOS: Tùy chọn hệ thống > Bảo mật & quyền riêng tư > Tường lửa
# Linux: ufw status

# Xác minh ports không bị chặn
netstat -tulpn | grep :8000
netstat -tulpn | grep :5173
```

#### 4. Vấn Đề Hiệu Suất

**Vấn đề**: Xử lý chậm hoặc sử dụng CPU cao

**Giải pháp**:
```bash
# Bật tối ưu ONNX
cd backend
python convert_models_to_onnx.py

# Kiểm tra tài nguyên hệ thống
# Windows: Task Manager
# macOS: Activity Monitor  
# Linux: htop hoặc top

# Giảm kích thước chunk audio
# Chỉnh sửa backend/app/core/config.py
MAX_AUDIO_CHUNK_SIZE = 1024 * 128  # Giảm từ 256KB xuống 128KB
```

#### 5. Vấn Đề Chất Lượng Audio

**Vấn đề**: Độ chính xác nhận dạng kém

**Giải pháp**:
```bash
# Kiểm tra chất lượng microphone
# Sử dụng microphone ngoài thay vì tích hợp
# Nói rõ ràng và với âm lượng bình thường
# Giảm tiếng ồn nền

# Điều chỉnh cài đặt audio
# Chỉnh sửa frontend/src/hooks/useAudioRecorder.ts
const constraints = {
  audio: {
    sampleRate: { ideal: 16000 },  // Khớp với yêu cầu mô hình
    channelCount: { ideal: 1 },    // Audio mono
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true
  }
}
```

### Vấn Đề Theo Trình Duyệt

#### Chrome
- **Vấn đề**: Chính sách WebRTC chặn microphone
- **Giải pháp**: Thêm cờ `--use-fake-ui-for-media-stream` để test

#### Firefox  
- **Vấn đề**: Timeout kết nối WebSocket
- **Giải pháp**: Tăng `dom.websocket.timeout.ping.request` trong about:config

#### Safari
- **Vấn đề**: Audio context yêu cầu tương tác người dùng
- **Giải pháp**: Đảm bảo quyền microphone được cấp trước khi bắt đầu

#### Edge
- **Vấn đề**: Lỗi xử lý audio
- **Giải pháp**: Cập nhật lên phiên bản mới nhất hoặc sử dụng Chrome

## 🔍 Debug

### Bật Debug Logging

#### Chế Độ Debug Backend

```bash
# Đặt biến môi trường
export LOG_LEVEL=DEBUG

# Hoặc chỉnh sửa backend/app/core/config.py
LOG_LEVEL: str = "DEBUG"
```

#### Chế Độ Debug Frontend

```bash
# Chế độ phát triển tự động bật debug logs
npm run dev

# Kiểm tra console trình duyệt cho debug messages
# Tìm logs bắt đầu với [AudioRecorder], [WebSocket], v.v.
```

### Thu Thập Thông Tin Debug

```bash
# Thu thập thông tin hệ thống để debug
python -c "
import sys, platform, torch, transformers
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'PyTorch: {torch.__version__}')
print(f'Transformers: {transformers.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
"
```

### Phân Tích Log

```bash
# Logs backend
tail -f backend/logs/app.log

# Logs frontend (console trình duyệt)
# Nhấn F12 > Tab Console

# Logs WebSocket
# Tìm messages trạng thái kết nối WebSocket
```

## 📊 Tối Ưu Hiệu Suất

### Tối Ưu Backend

#### Bật ONNX Runtime
```bash
cd backend
python convert_models_to_onnx.py
```

#### Điều Chỉnh Cài Đặt Xử Lý
```python
# backend/app/core/config.py
class Settings:
    # Giảm sử dụng bộ nhớ
    MAX_AUDIO_CHUNK_SIZE: int = 1024 * 128  # 128KB thay vì 256KB
    
    # Tăng timeout xử lý
    AUDIO_PROCESSING_TIMEOUT: int = 60  # 60 giây
    
    # Bật cache mô hình
    MODEL_CACHE_ENABLED: bool = True
    MODEL_CACHE_SIZE: int = 2  # Giữ 2 mô hình trong bộ nhớ
```

#### Tối Ưu Tài Nguyên Hệ Thống
```bash
# Tăng giới hạn bộ nhớ Python
export PYTHONOPTIMIZE=1

# Sử dụng tối ưu CPU
export OMP_NUM_THREADS=4

# Bật tối ưu PyTorch
export TORCH_USE_CUDA_DSA=1
```

### Tối Ưu Frontend

#### Giảm Kích Thước Bundle
```bash
# Phân tích kích thước bundle
cd frontend
npm run build
npx vite-bundle-analyzer dist
```

#### Tối Ưu Xử Lý Audio
```typescript
// frontend/src/hooks/useAudioRecorder.ts
const optimizedConfig = {
  chunkDuration: 2000,        // Tăng kích thước chunk để ít WebSocket calls hơn
  enableVolumeDetection: true, // Giữ cho phản hồi thời gian thực
  audioBitsPerSecond: 64000,  // Giảm bitrate cho chunks nhỏ hơn
}
```

### Tối Ưu Phần Cứng

#### Tối Ưu CPU
- Sử dụng bộ xử lý đa lõi (4+ core khuyến nghị)
- Bật CPU turbo boost
- Đóng các ứng dụng không cần thiết

#### Tối Ưu Bộ Nhớ  
- 8GB+ RAM khuyến nghị cho hoạt động mượt mà
- Đóng các tab trình duyệt để giải phóng bộ nhớ
- Sử dụng SSD để tải mô hình nhanh hơn

#### Tối Ưu Mạng
- Sử dụng kết nối có dây thay vì WiFi
- Đảm bảo internet ổn định cho tải mô hình ban đầu
- Xử lý local (không phụ thuộc cloud)

## 🔒 Bảo Mật

### Triển Khai Production

#### Yêu Cầu HTTPS
```bash
# Tạo chứng chỉ SSL
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Cập nhật cấu hình frontend
VITE_WS_URL=wss://yourdomain.com/v1/ws
VITE_API_HOST=yourdomain.com
```

#### Bảo Mật Môi Trường
```bash
# Sử dụng biến môi trường cho dữ liệu nhạy cảm
export SECRET_KEY=your-secret-key
export DATABASE_URL=your-database-url
export REDIS_URL=your-redis-url

# Không bao giờ commit secrets vào version control
echo "*.env" >> .gitignore
echo "*.pem" >> .gitignore
```

#### Bảo Mật API
```python
# backend/app/core/config.py
class Settings:
    # Bật CORS cho origins cụ thể
    BACKEND_CORS_ORIGINS: List[str] = ["https://yourdomain.com"]
    
    # Bật rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # requests mỗi phút
    
    # Bật logging request
    REQUEST_LOGGING_ENABLED: bool = True
```

### Bảo Mật Dữ Liệu

#### Xử Lý Dữ Liệu Audio
- Audio được xử lý local (không truyền cloud)
- Không có dữ liệu audio nào được lưu trữ vĩnh viễn
- Kết nối WebSocket là tạm thời
- Mô hình chạy trên phần cứng của bạn

#### Bảo Mật Mô Hình
- Mô hình được tải từ Hugging Face (mã nguồn mở)
- Không có dữ liệu độc quyền nào được gửi đến dịch vụ bên ngoài
- Tất cả xử lý xảy ra offline sau khi tải ban đầu

## 📞 Nhận Hỗ Trợ

### Hỗ Trợ Cộng Đồng

- 🐛 **Báo lỗi**: [GitHub Issues](https://github.com/your-username/vietnamese-stt-demo/issues)
- 💬 **Thảo luận**: [GitHub Discussions](https://github.com/your-username/vietnamese-stt-demo/discussions)
- 📖 **Tài liệu**: [Project Wiki](https://github.com/your-username/vietnamese-stt-demo/wiki)

### Template Thông Tin Debug

Khi báo lỗi, vui lòng bao gồm:

```bash
# Thông tin hệ thống
python --version
node --version
npm --version
uname -a  # Linux/macOS
systeminfo  # Windows

# Logs ứng dụng
# Logs backend từ console output
# Logs frontend từ console trình duyệt
# Thông báo lỗi (nếu có)

# Các bước tái tạo
# 1. Bạn đã làm gì
# 2. Bạn mong đợi gì
# 3. Điều gì thực sự xảy ra
```

### Đóng Góp

Xem [CONTRIBUTING.md](./CONTRIBUTING.md) để biết hướng dẫn về:
- Đóng góp code
- Báo lỗi
- Yêu cầu tính năng
- Cải thiện tài liệu

---

<div align="center">

**Cần thêm trợ giúp?**

[🏠 Về README](./README.md) • [🐛 Báo lỗi](https://github.com/your-username/vietnamese-stt-demo/issues) • [💬 Tham gia thảo luận](https://github.com/your-username/vietnamese-stt-demo/discussions)

</div>
