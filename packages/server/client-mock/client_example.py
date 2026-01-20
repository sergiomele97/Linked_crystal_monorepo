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
    pkt = Packet()

    pkt.player_x_coord = 5
    pkt.player_y_coord = 4
    pkt.map_number = 4
    pkt.map_bank = 24
    pkt.IsOverworld = True
    pkt.player_id = 0

    # Ruta cerrada
    path = [
        (2, 4),
        (2, 6),
        (4, 6),
        (4, 4),
    ]

    current_target = 1
    ticks_per_step = 16
    tick_duration = 1 / 60  # 60 ticks por segundo
    tick_count = 0

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

                backoff = 1

                while True:
                    # Enviar estado actual
                    await ws.send(pkt.to_bytes())

                    # Movimiento cada 16 ticks
                    tick_count += 1
                    if tick_count >= ticks_per_step:
                        tick_count = 0

                        target_x, target_y = path[current_target]

                        # mover 1 casilla por eje
                        if pkt.player_x_coord < target_x:
                            pkt.player_x_coord += 1
                        elif pkt.player_x_coord > target_x:
                            pkt.player_x_coord -= 1
                        elif pkt.player_y_coord < target_y:
                            pkt.player_y_coord += 1
                        elif pkt.player_y_coord > target_y:
                            pkt.player_y_coord -= 1
                        else:
                            # alcanzado el target → siguiente
                            current_target = (current_target + 1) % len(path)

                    # Leer broadcast sin bloquear
                    try:
                        await asyncio.wait_for(ws.recv(), timeout=0.01)
                    except asyncio.TimeoutError:
                        pass

                    await asyncio.sleep(tick_duration)

        except (websockets.ConnectionClosedError, OSError):
            pass
        except Exception as e:
            print(f"Error inesperado: {e}")

        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)

# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    asyncio.run(run_client())