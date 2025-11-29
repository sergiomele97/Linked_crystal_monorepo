import asyncio
import struct
import websockets
import os
import ssl
from dotenv import load_dotenv
from packet import Packet   


# Cargar variables desde .env
load_dotenv()

# Variables de entorno
ENV = os.getenv("ENV", "local")
STATIC_TOKEN = os.getenv("STATIC_TOKEN", "demo_token")
SSL_URL = os.getenv("SSL_URL")  # Not needed in local
SERVER_URL = os.getenv("SERVER_URL", "ws://localhost:8080/ws")
FULL_URL = f"{SERVER_URL}?token={STATIC_TOKEN}"

ssl_context = None
server_hostname = None

if ENV != "local":
    ssl_context = ssl.create_default_context()
    server_hostname = SSL_URL


# ---------------------------
# Cliente principal
# ---------------------------
async def run_client():
    pkt = Packet()   # paquete inicial
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
                backoff = 1  # reinicia backoff

                while True:
                    # Enviar paquete actual
                    await ws.send(pkt.to_bytes())

                    # Intentar leer broadcast
                    try:
                        data = await asyncio.wait_for(ws.recv(), timeout=0.1)

                        # Cada paquete tiene exactamente 20 bytes
                        packet_size = 20

                        print(f"Broadcast recibido: {len(data)} bytes")

                        # Procesar todos los paquetes concatenados
                        for i in range(0, len(data), packet_size):
                            chunk = data[i:i + packet_size]
                            if len(chunk) == packet_size:
                                p = Packet.from_bytes(chunk)
                                print(
                                    f"  → Packet: X={p.player_x_coord}, "
                                    f"Y={p.player_y_coord}, "
                                    f"Map={p.map_number}:{p.map_bank}, "
                                    f"Playing={p.isPlaying}"
                                )

                    except asyncio.TimeoutError:
                        pass

                    # Cambiar datos del paquete para test (como tu ejemplo original)
                    pkt.player_x_coord += 1
                    pkt.player_y_coord += 1
                    pkt.map_number += 1
                    pkt.map_bank += 1
                    pkt.isPlaying = 1

                    await asyncio.sleep(0.1)

        except (websockets.ConnectionClosedError, OSError) as e:
            print(f"Conexión perdida: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")

        print(f"Reintentando conexión en {backoff}s...")
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)


# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    asyncio.run(run_client())
