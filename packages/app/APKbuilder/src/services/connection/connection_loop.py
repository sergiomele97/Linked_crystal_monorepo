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
        self.serverPackets = app.appData.serverPackets  # lista compartida

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

                    while not self._stop_event.is_set():
                        # Enviar snapshot de localPacket
                        pkt_bytes = self.localPacket.to_bytes()
                        await ws.send(pkt_bytes)

                        # Recibir y reemplazar serverPackets
                        try:
                            data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            if isinstance(data, (bytes, bytearray)):
                                PACKET_SIZE = 20
                                n = len(data) // PACKET_SIZE
                                latest_packets = []
                                for i in range(n):
                                    start = i * PACKET_SIZE
                                    chunk = data[start:start + PACKET_SIZE]
                                    if len(chunk) == PACKET_SIZE:
                                        try:
                                            p = Packet.from_bytes(chunk)
                                            latest_packets.append(p)
                                        except Exception:
                                            continue
                                # Reemplazar todo el contenido anterior
                                self.serverPackets[:] = latest_packets
                        except asyncio.TimeoutError:
                            pass

                        await asyncio.sleep(0.1)

            except Exception as e:
                print(f"⚠ Error WebSocket: {e}")

            print(f"Reintentando en {backoff}s…")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
