import React, { useState, useEffect, useRef } from 'react';

const WebSocketDebugger: React.FC = () => {
  const [status, setStatus] = useState('disconnected');
  const [messages, setMessages] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const addMessage = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setMessages(prev => [...prev, `[${timestamp}] ${message}`]);
  };

  const connect = () => {
    try {
      const wsUrl = 'ws://127.0.0.1:8000/v1/ws';
      addMessage(`Connecting to: ${wsUrl}`);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = (event) => {
        setStatus('connected');
        addMessage('✅ WebSocket connected successfully!');
        console.log('WebSocket onopen:', event);
      };

      ws.onmessage = (event) => {
        addMessage(`📨 Message received: ${event.data}`);
        console.log('WebSocket onmessage:', event);
      };

      ws.onclose = (event) => {
        setStatus('disconnected');
        addMessage(`❌ WebSocket closed: Code=${event.code}, Reason="${event.reason}", Clean=${event.wasClean}`);
        console.log('WebSocket onclose:', event);
      };

      ws.onerror = (event) => {
        setStatus('error');
        addMessage(`🚨 WebSocket error occurred`);
        console.error('WebSocket onerror:', event);
      };

    } catch (error) {
      addMessage(`❌ Connection failed: ${error}`);
      console.error('WebSocket connection error:', error);
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const sendTestMessage = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Send test binary data (simulating audio)
      const testData = new ArrayBuffer(1024);
      wsRef.current.send(testData);
      addMessage('📤 Sent test binary data (1024 bytes)');
    } else {
      addMessage('❌ WebSocket not connected');
    }
  };

  const clearMessages = () => {
    setMessages([]);
  };

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  return (
    <div style={{ padding: '20px', border: '2px solid #ccc', margin: '10px', borderRadius: '8px' }}>
      <h3>🔧 WebSocket Debugger</h3>
      
      <div style={{ marginBottom: '10px' }}>
        <strong>Status:</strong> 
        <span style={{ 
          color: status === 'connected' ? 'green' : status === 'error' ? 'red' : 'orange',
          marginLeft: '10px',
          fontWeight: 'bold'
        }}>
          {status.toUpperCase()}
        </span>
      </div>

      <div style={{ marginBottom: '10px' }}>
        <button onClick={connect} style={{ marginRight: '10px', padding: '5px 10px' }}>
          🔌 Connect
        </button>
        <button onClick={disconnect} style={{ marginRight: '10px', padding: '5px 10px' }}>
          ❌ Disconnect
        </button>
        <button onClick={sendTestMessage} style={{ marginRight: '10px', padding: '5px 10px' }}>
          📤 Send Test
        </button>
        <button onClick={clearMessages} style={{ padding: '5px 10px' }}>
          🧹 Clear
        </button>
      </div>

      <div style={{ 
        background: '#f0f0f0', 
        padding: '10px', 
        height: '200px', 
        overflow: 'auto',
        fontFamily: 'monospace',
        fontSize: '12px'
      }}>
        {messages.map((msg, index) => (
          <div key={index}>{msg}</div>
        ))}
      </div>
    </div>
  );
};

export default WebSocketDebugger;