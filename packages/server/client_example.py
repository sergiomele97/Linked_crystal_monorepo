import asyncio
import struct
import websockets

SERVER_URL = "ws://localhost:8080/ws"

# Empaqueta (X, Y, Z) en formato binario little-endian (igual que Go)
def make_message(x, y, z):
    return struct.pack("<3i", x, y, z)

async def run_client():
    x = y = z = 0
    backoff = 1
    max_backoff = 30

    while True:
        try:
            async with websockets.connect(
                SERVER_URL,
                ping_interval=10,   # manda ping cada 10s
                ping_timeout=5,     # espera pong máximo 5s
                close_timeout=3,    # tiempo máximo para cierre limpio
            ) as ws:
                print("Conectado al servidor WebSocket")
                backoff = 1  # reinicia backoff tras conexión exitosa

                while True:
                    msg = make_message(x, y, z)
                    await ws.send(msg)

                    try:
                        data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                        print("Broadcast recibido:", len(data), "bytes")
                    except asyncio.TimeoutError:
                        pass

                    x += 1
                    y += 1
                    z += 1
                    await asyncio.sleep(0.1)

        except (websockets.ConnectionClosedError, OSError) as e:
            print(f"Conexión perdida: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")

        print(f"Reintentando conexión en {backoff}s...")
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)

if __name__ == "__main__":
    asyncio.run(run_client())
