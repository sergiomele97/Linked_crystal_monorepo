# connection_loop.py

import asyncio
import struct
import threading
import ssl
import websockets

from env import STATIC_TOKEN, ENV

class ConnectionLoop:
    def __init__(self, get_url_callback):
        """
        get_url_callback: función que devuelve el servidor elegido (wss://...)
        """
        self.get_url_callback = get_url_callback
        self.token = STATIC_TOKEN
        self.env = ENV

        self.ssl_context = None
        self.hostname = None

        if self.env != "local":
            self.ssl_context = ssl.create_default_context()
            self.hostname = None  # websockets autodetectará

        # Control
        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None

    # ------------------------------
    # Métodos públicos
    # ------------------------------

    def start(self):
        """Inicia el hilo y el loop asyncio."""
        if self.thread and self.thread.is_alive():
            return

        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Detiene el loop asyncio y el hilo."""
        self._stop_event.set()
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except:
                pass

    # ------------------------------
    # Loop asyncio en un thread
    # ------------------------------

    def _run_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self._main())

    # ------------------------------
    # Cliente WebSocket
    # ------------------------------

    async def _main(self):
        backoff = 1
        max_backoff = 30

        while not self._stop_event.is_set():
            base_url = self.get_url_callback()   # wss://example.com/ws
            if not base_url:
                await asyncio.sleep(1)
                continue

            # URL FINAL
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

                    x = y = z = 0

                    while not self._stop_event.is_set():
                        # Empaquetar mensaje binario igual que Go
                        msg = struct.pack("<3i", x, y, z)
                        await ws.send(msg)

                        # Intentar recibir un broadcast
                        try:
                            data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            # Si quieres, puedes notificar a Kivy aquí
                        except asyncio.TimeoutError:
                            pass

                        x += 1
                        y += 1
                        z += 1

                        await asyncio.sleep(0.1)

            except Exception as e:
                print(f"⚠ Error WebSocket: {e}")

            print(f"Reintentando en {backoff}s…")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
