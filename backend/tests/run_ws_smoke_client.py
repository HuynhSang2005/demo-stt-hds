import sys
import os
from fastapi.testclient import TestClient

# Ensure backend package is importable when running this script from repo root
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.main import app


def main():
    # Use TestClient as a context manager to trigger lifespan startup (model loading)
    with TestClient(app) as client:
        with client.websocket_connect('/v1/ws') as websocket:
            print('connected to /v1/ws')
            msg = websocket.receive_json()
            print('received:', msg)

            # send ping and read reply
            websocket.send_text('ping')
            resp = websocket.receive_json()
            print('ping reply:', resp)

            # try sending a tiny invalid binary payload (should get error but not close)
            websocket.send_bytes(b'xx')
            resp2 = websocket.receive_json()
            print('binary reply:', resp2)

            websocket.close()
            print('closed')

if __name__ == '__main__':
    main()
