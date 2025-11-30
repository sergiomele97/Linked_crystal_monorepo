# connection_loop_packet.py

import asyncio
import threading
import ssl
import websockets
from kivy.app import App
from env import STATIC_TOKEN, ENV
from models.packet import Packet  # tu clase Packet

class ConnectionLoop:
    def __init__(self, get_url_callback):
        self.get_url_callback = get_url_callback
        self.token = STATIC_TOKEN
        self.env = ENV

        self.ssl_context = None
        self.hostname = None
        if self.env != "local":
            self.ssl_context = ssl.create_default_context()
            self.hostname = None

        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None

        app = App.get_running_app()
        self.localPacket = app.appData.packet
        self.serverPackets = app.appData.serverPackets  

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except:
                pass

    def _run_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self._main())

    # ---------------------------------------------------------------------
    # ✔ NUEVO: Bucle únicamente de envío
    # ---------------------------------------------------------------------
    async def send_loop(self, ws):
        while not self._stop_event.is_set():
            try:
                pkt_bytes = self.localPacket.to_bytes()
                await ws.send(pkt_bytes)
            except Exception as e:
                print("❌ Error en send_loop:", e)
                return 

            await asyncio.sleep(0.1)

    # ---------------------------------------------------------------------
    # ✔ NUEVO: Bucle únicamente de recepción
    # ---------------------------------------------------------------------
    async def recv_loop(self, ws):
        PACKET_SIZE = 20

        while not self._stop_event.is_set():
            try:
                data = await ws.recv()

                if isinstance(data, (bytes, bytearray)):
                    n = len(data) // PACKET_SIZE
                    latest_packets = []

                    for i in range(n):
                        start = i * PACKET_SIZE
                        chunk = data[start:start + PACKET_SIZE]
                        if len(chunk) == PACKET_SIZE:
                            try:
                                p = Packet.from_bytes(chunk)
                                latest_packets.append(p)
                            except:
                                continue

                    # Reemplazar el contenido anterior
                    self.serverPackets[:] = latest_packets
                    print(self.serverPackets)

            except websockets.exceptions.ConnectionClosed:
                print("❌ Conexión cerrada en recv_loop")
                return

            except Exception as e:
                print("❌ Error en recv_loop:", e)
                return

    # ---------------------------------------------------------------------
    # ✔ MODIFICADO: ahora main lanza send_loop + recv_loop en paralelo
    # ---------------------------------------------------------------------
    async def _main(self):
        backoff = 1
        max_backoff = 30

        while not self._stop_event.is_set():
            base_url = self.get_url_callback()
            if not base_url:
                await asyncio.sleep(1)
                continue

            full_url = f"{base_url}?token={self.token}"

            try:
                async with websockets.connect(
                    full_url,
                    ssl=self.ssl_context,
                    server_hostname=self.hostname,
                    ping_interval=10,
                    ping_timeout=5,
                    close_timeout=3,
                ) as ws:

                    print("✔ Conectado:", full_url)
                    backoff = 1

                    # Lanzamos envío y recepción simultáneos en la misma conexión
                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))

                    # Esperamos a que una falle (o stop_event)
                    done, pending = await asyncio.wait(
                        {send_task, recv_task},
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # Cancelar las otras
                    for task in pending:
                        task.cancel()

            except Exception as e:
                print(f"⚠ Error WebSocket: {e}")

            print(f"Reintentando en {backoff}s…")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
