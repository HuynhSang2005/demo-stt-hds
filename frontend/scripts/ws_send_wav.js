const fs = require('fs');
const WebSocket = require('ws');

const uri = 'ws://127.0.0.1:8000/v1/ws';
const wavPath = '../../wav2vec2-base-vietnamese-250h/audio-test/t1_0001-00010.wav';

(async () => {
  const absPath = require('path').resolve(__dirname, wavPath);
  const b = fs.readFileSync(absPath);
  console.log('sending file', absPath, b.length, 'bytes');
  const ws = new WebSocket(uri);
  ws.on('open', () => {
    console.log('ws open');
  });
  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data.toString());
      console.log('recv', msg.type);
    } catch (e) {
      console.log('recv raw', data.toString().slice(0,200));
    }
  });
  ws.on('close', () => console.log('closed'));
  ws.on('error', (e) => console.error('ws error', e));

  ws.on('open', () => {
    // send binary as soon as we get open
    ws.send(b);
  });
})();
