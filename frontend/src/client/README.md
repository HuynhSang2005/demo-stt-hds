# Vietnamese STT TypeScript Client

This directory contains auto-generated TypeScript client code from the FastAPI backend OpenAPI specification.

## 🔄 Generation Process

The client is generated using `@hey-api/openapi-ts` from the FastAPI backend's OpenAPI schema.

### Prerequisites

1. **Backend Running**: Ensure the Vietnamese STT FastAPI backend is running on `http://localhost:8000`
2. **OpenAPI Spec Available**: The backend must serve its OpenAPI specification at `http://localhost:8000/openapi.json`

### Generation Commands

```bash
# Generate client from running backend
npm run generate-client

# Or manually run openapi-ts
npm run openapi-ts

# Development with auto-client generation
npm run dev:with-client
```

## 📁 Generated Files

After running the generation, this directory will contain:

- `types.gen.ts` - TypeScript interfaces for all API schemas
- `sdk.gen.ts` - SDK functions for all API endpoints  
- `client.gen.ts` - Fetch API client configuration
- `schemas.gen.ts` - Zod schemas for runtime validation (if backend supports it)

## 🔗 Integration

The generated client integrates with our Vietnamese STT frontend:

### API Endpoints
- `transcribeVietnameseAudio()` - Send audio for Vietnamese STT processing
- `checkHealthStatus()` - Backend health check
- WebSocket helpers for real-time transcript streaming

### Type Safety
- All API request/response types
- Error response interfaces
- Vietnamese STT specific data structures

### Usage Example

```typescript
import { transcribeVietnameseAudio, connectWebSocket } from '@/client/sdk.gen'
import { TranscriptResult, VietnameseSentiment } from '@/client/types.gen'

// REST API usage
const result = await transcribeVietnameseAudio({
  body: audioFormData
})

// WebSocket usage (if supported by generated client)
const ws = connectWebSocket({
  url: 'ws://localhost:8000/v1/ws'
})
```

## 📝 Notes

- **Auto-generated**: Do not manually edit files in this directory
- **Version Control**: Generated files can be gitignored or committed based on team preference
- **Regeneration**: Re-run generation when backend API changes
- **Offline Development**: For offline development, ensure backend is accessible or use mock server

## 🔧 Configuration

Client generation is configured in `openapi-ts.config.ts` at the project root:

- **Input**: `http://localhost:8000/openapi.json`
- **Output**: `src/client/`
- **Plugins**: TypeScript types, SDK, Fetch client, Zod schemas
- **Format**: Prettier formatting applied

## 🚀 Next Steps

1. Start the Vietnamese STT FastAPI backend
2. Run `npm run generate-client` to create the client
3. Import and use the generated client in React components
4. Integrate with our custom WebSocket hooks and Zustand store