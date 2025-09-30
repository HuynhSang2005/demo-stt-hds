import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  // Input: Local FastAPI OpenAPI specification URL
  // Note: This assumes your FastAPI backend is running on localhost:8000
  input: 'http://localhost:8000/openapi.json',
  
  // Output: Generate client files in src/client directory
  output: {
    path: 'src/client',
    // Keep generated files organized and clean
    format: 'prettier',
  },
  
  // Plugins configuration for Vietnamese STT project
  plugins: [
    // Generate TypeScript types from OpenAPI schemas
    {
      name: '@hey-api/typescript',
      // Generate comprehensive types including:
      // - Request/Response interfaces
      // - Error response types  
      // - WebSocket message types
      // - Vietnamese STT specific types
      enums: 'typescript', // Use TypeScript enums instead of unions
    },
    
    // Generate SDK with all API endpoints
    {
      name: '@hey-api/sdk', 
      // Generate function-based SDK for:
      // - REST API endpoints (/v1/transcribe, /v1/health)
      // - WebSocket connection helpers
      // - Vietnamese STT service methods
    },
    
    // Generate Fetch API client for HTTP requests
    {
      name: '@hey-api/client-fetch',
      // Optimized for Vietnamese STT WebSocket + HTTP hybrid approach
      // Handles both REST endpoints and WebSocket upgrade requests
    },
    
    // Generate Zod schemas for runtime validation
    {
      name: 'zod',
      // Generate Zod schemas that complement our existing schema structure
      // This ensures consistency between frontend validation and OpenAPI spec
    }
  ],
})