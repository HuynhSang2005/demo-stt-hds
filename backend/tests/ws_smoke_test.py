import asyncio
import websockets

async def run_test():
    uri = "ws://127.0.0.1:8000/v1/ws"
    try:
        async with websockets.connect(uri) as ws:
            print("connected")
            msg = await ws.recv()
            print("recv:", msg)
            await ws.send("ping")
            msg2 = await ws.recv()
            print("recv2:", msg2)
            await ws.close()
            print("closed")
    except Exception as e:
        print("error:", e)

if __name__ == '__main__':
    asyncio.run(run_test())
