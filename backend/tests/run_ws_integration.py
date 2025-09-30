import sys
import os
import time
from fastapi.testclient import TestClient

# Make backend importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

from app.main import app
from app.core.config import get_settings


def run_integration_test(wav_relative_path=None, timeout=15.0):
    settings = get_settings()
    model_paths = settings.get_model_paths()

    # default WAV in the repo (from wav2vec2 model folder audio-test)
    if wav_relative_path is None:
        wav_relative_path = model_paths['asr'] / 'audio-test' / 't1_0001-00010.wav'

    wav_path = os.path.abspath(str(wav_relative_path))
    print('Using WAV file:', wav_path)
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    with TestClient(app) as client:
        with client.websocket_connect('/v1/ws') as ws:
            # Receive connection_status
            msg = ws.receive_json()
            print('connection message:', msg)
            assert msg.get('type') == 'connection_status'

            # Read file bytes
            with open(wav_path, 'rb') as f:
                b = f.read()

            print('Sending audio bytes (%d bytes)...' % len(b))
            ws.send_bytes(b)

            # Wait for transcript_result within timeout
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    r = ws.receive_json()
                except Exception as e:
                    print('Receive error:', e)
                    break

                print('received:', r)
                t = r.get('type')
                if t == 'transcript_result':
                    data = r.get('data') or {}
                    text = data.get('text')
                    label = data.get('label')
                    print('Transcript result received. label=', label, ' text=', (text or '')[:200])
                    return True
                if t == 'error':
                    print('Server returned error:', r.get('data'))
                    # keep waiting — in some pipelines server may return error then later transcript
                # otherwise loop

            print('Did not receive transcript_result within timeout')
            return False


if __name__ == '__main__':
    ok = run_integration_test()
    if not ok:
        print('\nINTEGRATION TEST FAILED')
        sys.exit(2)
    print('\nINTEGRATION TEST PASSED')
    sys.exit(0)
