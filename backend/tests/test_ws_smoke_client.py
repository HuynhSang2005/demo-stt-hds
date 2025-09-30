from fastapi.testclient import TestClient
from backend.app.main import app


def test_ws_smoke():
    client = TestClient(app)
    with client.websocket_connect('/v1/ws') as websocket:
        # receive connection_status
        msg = websocket.receive_json()
        print('received:', msg)
        assert msg.get('type') == 'connection_status'

        # send ping text
        websocket.send_text('ping')
        resp = websocket.receive_json()
        print('pong resp:', resp)
        assert resp.get('type') in ('pong', 'connection_status', 'error')

        # close
        websocket.close()
