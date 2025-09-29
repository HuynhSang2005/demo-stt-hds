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
 - **Zod v4 (latest)** for runtime schema validation + TypeScript type inference
   - Use `zod` together with `@hookform/resolvers/zod` when integrating with React Hook Form
   - Prefer `.safeParse()` or `.parse()` depending on sync/async needs

## 🎙️ Audio Handling
- **Ghi âm**: `MediaRecorder` (mimeType: `audio/webm;codecs=opus`) 
- **Không resample ở FE** → gửi raw chunk → BE xử lý
- **Chunk interval**: 2000ms → cân bằng latency/accuracy

## � Form & Schema Validation (Zod v4)
- Use Zod v4 for runtime validation and static type inference.
- Integration pattern with React Hook Form:
  - Install: `npm install zod @hookform/resolvers`
  - Use `useForm({ resolver: zodResolver(schema) })` from `react-hook-form`.
- Rules:
  - DO NOT define all Zod schemas in a single file. Place each schema in `src/schemas/` with a one-to-one mapping between schema and file (e.g., `transcript.schema.ts`, `user.schema.ts`).
  - DO NOT define TypeScript types/interfaces in the same file as Zod schemas. Place TS types or interface declarations in `src/types/` or `src/interfaces/` with matching filenames (e.g., `transcript.ts`, `user.ts`).
  - Use `export type Transcript = z.infer<typeof TranscriptSchema>` in the types file to keep types and schemas separate yet linked.

## 🗂️ Updated Folder Structure (FE)
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/                  # Shadcn UI wrappers + theme
│   │   ├── AudioVisualizer.tsx
│   │   └── TranscriptDisplay.tsx
│   ├── hooks/
│   │   ├── useAudioRecorder.ts
│   │   └── useWebSocket.ts
│   ├── store/
│   │   └── useStore.ts
│   ├── schemas/                 # Zod schema files (one schema per file)
│   │   ├── transcript.schema.ts
│   │   └── form.schema.ts
│   ├── types/                   # TS types & interfaces (one file per type)
│   │   ├── transcript.ts
│   │   └── user.ts
│   ├── lib/
│   │   └── utils.ts
│   └── styles/
│       └── tailwind.css
├── public/
│   └── logo.svg
├── tests/
└── vite.config.ts
```

## �🧪 Testing Strategy
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

## 🎨 Shadcn UI guidance
- Use Shadcn UI components and copy templates from `ui.shadcn.com` for rapid UI assembly.
- Recommended components for this project:
  - Forms: `Form`, `Input`, `Textarea`, `Badge`, `Button` (for settings/login)
  - Layout: `Card`, `Tabs`, `Alert` (for warnings), `Avatar` (user)
  - Data display: `List`, `Toolbar`, `Toast` (for warnings)
- Templates to consider copying/adapting from Shadcn:
  - Dashboard / Tasks examples (for transcript list + stats)
  - Authentication example (if you add an opt-in UI)
- Keep Shadcn components in `src/components/ui/` and wrap them if you need app-specific props or accessibility adjustments.
```

---
