import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Temporarily disable StrictMode for WebSocket development to avoid double connections
// Re-enable after fixing WebSocket connection management
const isDevelopment = import.meta.env.DEV

createRoot(document.getElementById('root')!).render(
  isDevelopment ? (
    <App />
  ) : (
    <StrictMode>
      <App />
    </StrictMode>
  ),
)
