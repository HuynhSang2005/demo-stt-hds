# Frontend: React 19 + Vite – Real-time Audio UI

## 🗂️ Folder Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx             # Main recording UI
│   ├── components/
│   │   ├── ui/                  # Shadcn UI
│   │   ├── AudioVisualizer.tsx  # wavesurfer.js wrapper
│   │   └── TranscriptDisplay.tsx
│   ├── hooks/
│   │   ├── useAudioRecorder.ts  # MediaRecorder + chunking
│   │   └── useWebSocket.ts      # Reconnect, send/recv
│   ├── store/
│   │   └── useStore.ts          # Zustand: isRecording, transcripts, warnings
│   ├── lib/
│   │   └── utils.ts             # format time, etc.
│   └── types/
│       └── index.ts             # TranscriptResult, etc.
├── public/
│   └── logo.svg
├── tests/
│   ├── unit/
│   │   └── useAudioRecorder.test.ts
│   └── e2e/
│       └── transcript-display.test.tsx
├── vite.config.ts
└── tailwind.config.ts
```

## ⚙️ Framework & Libs
- **React 19** (hoặc 18)
- **Vite**
- **Shadcn UI** + **Tailwind CSS**
- **Zustand**
- **wavesurfer.js** (visualization only)
- **Vitest**, **React Testing Library**, **jest-websocket-mock** [[32], [40]]

## 🎙️ Audio Handling
- **Ghi âm**: `MediaRecorder` (mimeType: `audio/webm;codecs=opus`) 
- **Không resample ở FE** → gửi raw chunk → BE xử lý
- **Chunk interval**: 2000ms → cân bằng latency/accuracy

## 🧪 Testing Strategy
- **Unit**: Mock `MediaRecorder` trong hook
- **E2E**: Dùng `jest-websocket-mock` để giả lập server [[32], [40]]:
  ```ts
  const server = new MockServer('ws://localhost:8000/v1/ws');
  server.on('connection', (socket) => {
    socket.on('message', () => {
      socket.send(JSON.stringify({ text: "Xấu quá!", label: "toxic", warning: true }));
    });
  });
  ```

## 🖥️ UI Logic
- Khi `warning: true` → hiển thị badge đỏ (Shadcn `Badge` variant="destructive")
- Hiển thị transcript theo thời gian thực
- Nút "Start/Stop Recording" điều khiển `MediaRecorder`
```

---
