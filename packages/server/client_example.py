import asyncio
import struct
import websockets

SERVER_URL = "ws://localhost:8080/ws"

# Empaqueta (ID, X, Y, Z) en formato binario little-endian (igual que Go)
def make_message(client_id, x, y, z):
    return struct.pack("<4i", client_id, x, y, z)

async def client():
    async with websockets.connect(SERVER_URL) as ws:
        print("Conectado al servidor WebSocket")

        client_id = 1
        x, y, z = 0, 0, 0

        while True:
            # enviamos datos cada 0.1s
            msg = make_message(client_id, x, y, z)
            await ws.send(msg)

            # intentamos recibir el broadcast (no bloqueante)
            try:
                data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                print("Broadcast recibido:", len(data), "bytes")
            except asyncio.TimeoutError:
                pass

            x += 1
            y += 1
            z += 1
            await asyncio.sleep(0.1)

asyncio.run(client())
