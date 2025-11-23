import asyncio
import struct
import websockets
import os
import ssl
from dotenv import load_dotenv 


# Cargar variables desde .env
load_dotenv()

# Variables de entorno
ENV = os.getenv("ENV", "local")
STATIC_TOKEN = os.getenv("STATIC_TOKEN", "demo_token")
SSL_URL = os.getenv("SSL_URL") # Not needed in local
SERVER_URL = os.getenv("SERVER_URL", "ws://localhost:8080/ws")
FULL_URL = f"{SERVER_URL}?token={STATIC_TOKEN}"

ssl_context = None
server_hostname = None

if (ENV != "local"):
    ssl_context = ssl.create_default_context()
    server_hostname=SSL_URL



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
                FULL_URL,
                ssl=ssl_context,
                server_hostname=server_hostname,
                ping_interval=10,
                ping_timeout=5,
                close_timeout=3,
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
