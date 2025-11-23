import asyncio
import struct
import threading
import ssl
import websockets
from kivy.clock import Clock

from env import STATIC_TOKEN, ENV

class ConnectionLoop:
    def __init__(self, get_url_callback):
        self.get_url_callback = get_url_callback
        self.token = STATIC_TOKEN
        self.env = ENV

        self.ssl_context = None
        self.hostname = None

        if self.env != "local":
            self.ssl_context = ssl.create_default_context()

        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None

        # Callbacks que seteará MenuScreen
        self.on_connected = None
        self.on_disconnected = None

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
        was_connected = False

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
                    ping_interval=10,
                    ping_timeout=5,
                    close_timeout=3,
                ) as ws:

                    # Evento conexión OK
                    if not was_connected and self.on_connected:
                        Clock.schedule_once(lambda dt: self.on_connected())
                    was_connected = True

                    x = y = z = 0

                    while not self._stop_event.is_set():
                        msg = struct.pack("<3i", x, y, z)
                        await ws.send(msg)

                        try:
                            await asyncio.wait_for(ws.recv(), timeout=0.1)
                        except asyncio.TimeoutError:
                            pass

                        x += 1
                        y += 1
                        z += 1
                        await asyncio.sleep(0.1)

            except Exception as e:
                if was_connected and self.on_disconnected:
                    Clock.schedule_once(lambda dt, err=str(e): self.on_disconnected(err))
                was_connected = False

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
