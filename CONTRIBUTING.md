# 🤝 Contributing Guide

Cảm ơn bạn quan tâm đến việc đóng góp cho Vietnamese STT + Toxic Detection project!

## 📋 Quy trình đóng góp

### 1. Fork và Clone

```bash
# Fork repo trên GitHub, sau đó clone
git clone https://github.com/YOUR_USERNAME/demo-stt-hds.git
cd demo-stt-hds

# Add upstream remote
git remote add upstream https://github.com/HuynhSang2005/demo-stt-hds.git
```

### 2. Tạo Branch mới

```bash
# Tạo branch từ main
git checkout -b feature/your-feature-name

# Hoặc cho bugfix
git checkout -b fix/bug-description
```

**Naming conventions:**
- `feature/` - Tính năng mới
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 3. Setup Development Environment

```bash
# Kiểm tra dependencies
python check-dependencies.py

# Setup với script tự động
# Windows:
.\setup.ps1

# Linux/Mac:
bash setup.sh
```

### 4. Development Workflow

#### Backend Development

```bash
cd backend

# Kích hoạt venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Install dev dependencies (nếu có)
pip install pytest pytest-asyncio black ruff mypy

# Run tests
pytest tests/

# Code formatting
black app/
ruff check app/

# Type checking
mypy app/
```

#### Frontend Development

```bash
cd frontend

# Run dev server
npm run dev

# Type checking
npm run build  # TypeScript compilation check

# Linting
npm run lint
```

### 5. Coding Standards

#### Backend (Python)

- **Style**: PEP 8, sử dụng `black` formatter
- **Type hints**: Bắt buộc cho public functions
- **Docstrings**: Google style cho classes và functions
- **Imports**: Sorted alphabetically, grouped (stdlib, third-party, local)

```python
# Good example
from typing import Optional
import torch
from fastapi import FastAPI

from app.core.config import get_settings

def process_audio(audio_data: bytes, sample_rate: int = 16000) -> Optional[str]:
    """
    Process audio data and return transcription.
    
    Args:
        audio_data: Raw audio bytes
        sample_rate: Audio sample rate in Hz
        
    Returns:
        Transcribed text or None if processing fails
    """
    pass
```

#### Frontend (TypeScript)

- **Style**: ESLint config trong project
- **Types**: Strict TypeScript, avoid `any`
- **Components**: Functional components với TypeScript
- **Schemas**: Zod v4 cho validation (1 schema/file trong `src/schemas/`)
- **Types**: TypeScript types riêng biệt (1 type/file trong `src/types/`)

```typescript
// src/schemas/audio.schema.ts - Good example
import { z } from 'zod';

export const audioConfigSchema = z.object({
  chunkDuration: z.number().positive(),
  maxDuration: z.number().positive(),
});

// src/types/audio.types.ts
import type { audioConfigSchema } from '@/schemas/audio.schema';

export type AudioConfig = z.infer<typeof audioConfigSchema>;
```

### 6. Testing

#### Backend Tests

```bash
cd backend

# Activate venv first
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Run all tests
pytest

# Run specific test file
pytest tests/test_audio_processor.py

# Run with coverage (optional)
pytest --cov=app tests/
```

#### Frontend Tests

```bash
cd frontend

# Run tests (khi được implement)
npm test
```

### 7. Commit Guidelines

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: Tính năng mới
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, không thay đổi logic)
- `refactor`: Refactoring
- `test`: Tests
- `chore`: Build, dependencies, etc.

**Examples:**
```bash
feat(backend): add batch processing for ASR inference

- Implement micro-batching strategy
- Add configurable batch size and timeout
- Improve throughput by 2-3x

Closes #123
```

```bash
fix(frontend): resolve WebSocket reconnection loop

The WebSocket client was not properly handling connection
errors, causing infinite reconnection attempts.

- Add exponential backoff
- Add max retry limit
- Improve error logging

Fixes #456
```

### 8. Pull Request

```bash
# Commit changes
git add .
git commit -m "feat(backend): your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

**Tạo PR trên GitHub với:**

1. **Title**: Clear và concise
2. **Description**:
   - Mô tả thay đổi
   - Lý do thay đổi
   - Screenshots (nếu UI changes)
   - Testing notes
3. **Checklist**:
   - [ ] Tests pass
   - [ ] Code formatted
   - [ ] Documentation updated
   - [ ] No breaking changes (hoặc noted)

### 9. Review Process

- Maintainer sẽ review PR trong vòng 2-3 ngày
- Có thể yêu cầu changes
- Sau khi approve, PR sẽ được merge

## 🎯 Areas to Contribute

### High Priority

- [ ] **Unit tests coverage** - Backend coverage < 50%
- [ ] **Integration tests** - WebSocket flow tests
- [ ] **ONNX optimization** - Export models to ONNX
- [ ] **GPU support** - Better CUDA integration
- [ ] **Docker setup** - Containerization

### Medium Priority

- [ ] **UI/UX improvements** - Better audio visualization
- [ ] **Error handling** - More robust error messages
- [ ] **Logging improvements** - Structured logging enhancement
- [ ] **Documentation** - API docs, architecture docs
- [ ] **Performance monitoring** - Add metrics dashboard

### Nice to Have

- [ ] **Multi-language support** - UI i18n
- [ ] **Audio file upload** - Support file upload besides recording
- [ ] **Export transcripts** - Download as TXT/JSON
- [ ] **Browser compatibility** - Test on more browsers
- [ ] **Mobile responsive** - Better mobile UI

## 🐛 Bug Reports

**Tạo issue với:**

1. **Title**: Mô tả ngắn gọn bug
2. **Description**:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Screenshots/logs
3. **Environment**:
   - OS version
   - Python version
   - Node version
   - Browser (nếu frontend bug)

**Template:**
```markdown
### Bug Description
Clear description of the bug

### Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. See error

### Expected Behavior
What should happen

### Actual Behavior
What actually happens

### Environment
- OS: Windows 11
- Python: 3.11.5
- Node: 20.10.0
- Browser: Chrome 120

### Logs
```
[Error logs here]
```

## 💡 Feature Requests

**Tạo issue với:**

1. **Title**: Feature name
2. **Description**:
   - Use case
   - Proposed solution
   - Alternatives considered
   - Additional context

## 📞 Questions?

- **GitHub Discussions**: Tốt nhất cho questions
- **Issues**: Cho bugs và feature requests
- **Email**: [your-email@example.com]

## 🙏 Thank You!

Mọi contribution đều được đánh giá cao, từ bug reports, feature requests, đến code contributions!

---

**Happy Coding!** 🎉
