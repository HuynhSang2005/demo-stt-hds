# TypeScript Client Generation

This directory contains scripts and configurations for generating TypeScript clients from the FastAPI OpenAPI specification.

## Setup

1. Install dependencies:
```bash
npm install
```

## Usage

### Development (Server Running)
When the FastAPI server is running at localhost:8000:
```bash
npm run dev-client
```

### Production Build
Complete process with schema preprocessing:
```bash
npm run build-client
```

### Manual Steps

1. Download schema:
```bash
npm run download-schema
```

2. Preprocess for cleaner method names:
```bash
npm run preprocess-schema
```

3. Generate TypeScript client:
```bash
npm run generate-client-local
```

## Generated Client

The TypeScript client will be generated in `frontend/src/client/` with:
- Type-safe API client
- WebSocket connection helpers
- Request/response models
- Automatic error handling

## Client Usage Example

```typescript
import { WebsocketService, HealthService } from './client';

// Health check
const health = await HealthService.healthCheck();

// WebSocket status
const wsStatus = await WebsocketService.getWebsocketStatus();
```

## Optimization Features

- **Custom Operation IDs**: Clean method names without redundant prefixes
- **Tag-based Organization**: Services grouped by functionality
- **Type Safety**: Full TypeScript support with runtime validation
- **Auto-sync**: Schema changes automatically reflected in generated client