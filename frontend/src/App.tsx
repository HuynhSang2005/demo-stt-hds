
import { VietnameseSTTDashboard } from './components/VietnameseSTTDashboard'
import { useWarningCleanup } from './stores/vietnameseSTT.store'
import { config } from './lib/config'
import type { TranscriptResult } from './types/transcript'
import './App.css'
import './styles/vietnamese.css'

function App() {
  // Auto-cleanup recent warnings
  useWarningCleanup()
  
  // Handle export functionality
  const handleExport = (transcripts: TranscriptResult[]) => {
    console.log('Exported transcripts:', transcripts.length)
  }
  
  // Handle errors
  const handleError = (error: Error) => {
    console.error('Vietnamese STT Error:', error)
    // Could integrate with error tracking service here
  }

  return (
    <div className="App vietnamese-text">
      <VietnameseSTTDashboard
        websocketUrl={config.backend.wsUrl}
        title="Vietnamese Speech-to-Text với Phát hiện Độc hại"
        onExport={handleExport}
        onError={handleError}
      />
    </div>
  )
}

export default App
