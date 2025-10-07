# Hướng Dẫn Cài Đặt FFmpeg

## 🎯 Tại Sao Cần FFmpeg?

FFmpeg là thư viện **BẮT BUỘC** để backend có thể xử lý audio WebM/Opus từ trình duyệt web. Nếu không có FFmpeg, backend sẽ không thể decode audio và báo lỗi khi khởi động.

## 📦 Cài Đặt FFmpeg

### Windows

#### Phương pháp 1: Sử dụng Chocolatey (Khuyến nghị)
```powershell
# Mở PowerShell với quyền Administrator
choco install ffmpeg

# Kiểm tra cài đặt
ffmpeg -version
```

#### Phương pháp 2: Cài đặt thủ công
1. Tải FFmpeg từ: https://ffmpeg.org/download.html#build-windows
2. Giải nén file zip vào thư mục (ví dụ: `C:\ffmpeg`)
3. Thêm vào PATH:
   - Mở **System Properties** → **Environment Variables**
   - Thêm `C:\ffmpeg\bin` vào biến **PATH**
   - Restart terminal
4. Kiểm tra:
   ```powershell
   ffmpeg -version
   ```

#### Phương pháp 3: Sử dụng Scoop
```powershell
scoop install ffmpeg
ffmpeg -version
```

### macOS

```bash
# Sử dụng Homebrew
brew install ffmpeg

# Kiểm tra cài đặt
ffmpeg -version
```

### Linux (Ubuntu/Debian)

```bash
# Cập nhật package list
sudo apt-get update

# Cài đặt FFmpeg
sudo apt-get install ffmpeg

# Kiểm tra cài đặt
ffmpeg -version
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install ffmpeg

# Kiểm tra cài đặt
ffmpeg -version
```

## ✅ Kiểm Tra Cài Đặt

Sau khi cài đặt xong, chạy lệnh sau để kiểm tra:

```bash
python check-dependencies.py
```

Bạn sẽ thấy:
```
[OK] FFmpeg ffmpeg version X.X.X - OK
```

## 🔧 Troubleshooting

### Lỗi "FFmpeg not found"

**Nguyên nhân:** FFmpeg chưa được thêm vào PATH hoặc chưa cài đặt đúng.

**Giải pháp:**
1. Kiểm tra FFmpeg đã cài chưa:
   ```bash
   where ffmpeg  # Windows
   which ffmpeg  # macOS/Linux
   ```

2. Nếu lệnh trên trả về kết quả → FFmpeg đã cài nhưng chưa trong PATH:
   - Windows: Thêm thư mục chứa `ffmpeg.exe` vào PATH
   - macOS/Linux: Kiểm tra lại `/usr/local/bin` hoặc `/opt/homebrew/bin`

3. Nếu lệnh trên không trả về gì → FFmpeg chưa cài:
   - Cài lại theo hướng dẫn ở trên

### Backend báo lỗi "FFmpeg not found or not working"

**Nguyên nhân:** Backend không tìm thấy FFmpeg khi khởi động.

**Giải pháp:**
1. Restart terminal/PowerShell sau khi cài FFmpeg
2. Kiểm tra lại bằng `ffmpeg -version`
3. Nếu vẫn lỗi, thử cài lại FFmpeg bằng phương pháp khác

### Windows: "choco not found"

**Nguyên nhân:** Chocolatey chưa được cài đặt.

**Giải pháp:**
1. Cài đặt Chocolatey trước:
   ```powershell
   # Mở PowerShell với quyền Administrator
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. Sau đó cài FFmpeg:
   ```powershell
   choco install ffmpeg
   ```

## 📚 Tài Liệu Thêm

- FFmpeg Official: https://ffmpeg.org/
- FFmpeg Documentation: https://ffmpeg.org/documentation.html
- Chocolatey: https://chocolatey.org/
- Homebrew: https://brew.sh/

## 💡 Lưu Ý

- FFmpeg là phần mềm mã nguồn mở, hoàn toàn miễn phí
- Sau khi cài đặt, không cần cấu hình thêm gì
- Backend sẽ tự động phát hiện và sử dụng FFmpeg
- Nếu gặp lỗi, hãy kiểm tra lại PATH environment variable

