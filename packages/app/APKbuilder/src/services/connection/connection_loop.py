import asyncio
import struct
import threading
import ssl
import websockets
from kivy.clock import Clock

# ✅ Import certifi y fuerza SSL_CERT_FILE
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

from env import STATIC_TOKEN, ENV, SSL_URL

class ConnectionLoop:
    def __init__(self, get_url_callback):
        self.get_url_callback = get_url_callback
        self.token = STATIC_TOKEN
        self.env = ENV

        self.ssl_context = None
        self.hostname = None

        # ⚡ Usar certificados de certifi en Android
        if self.env != "local":
            self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.hostname = SSL_URL

        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None

        # Callbacks que seteará MenuScreen
        self.on_connected = None
        self.on_disconnected = None

        print("\n=== ANDROID_DEBUG: ConnectionLoop init ===")
        print("ENV:", self.env)
        print("SSL_URL (hostname):", self.hostname)
        print("STATIC_TOKEN:", self.token)
        print("SSL context exists:", self.ssl_context is not None)
        print("==========================================\n")

    def start(self):
        print("ANDROID_DEBUG: Starting connection thread...")
        if self.thread and self.thread.is_alive():
            print("ANDROID_DEBUG: Thread already running.")
            return
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        print("ANDROID_DEBUG: Stop called.")
        self._stop_event.set()
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except:
                print("ANDROID_DEBUG: Failed to stop loop safely.")

    def _run_loop(self):
        print("ANDROID_DEBUG: Creating new event loop for thread.")
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        print("ANDROID_DEBUG: Loop started.")
        self.loop.run_until_complete(self._main())

    async def _main(self):
        backoff = 1
        max_backoff = 30
        was_connected = False

        while not self._stop_event.is_set():

            base_url = self.get_url_callback()

            print("\n\n===== ANDROID_DEBUG NEW ITERATION =====")
            print("base_url from callback:", base_url)

            if not base_url:
                print("ANDROID_DEBUG: base_url is empty, retrying...")
                await asyncio.sleep(1)
                continue

            # Log esquema de URL
            if base_url.startswith("wss://"):
                print("ANDROID_DEBUG: base_url is WSS ✓")
            elif base_url.startswith("ws://"):
                print("ANDROID_DEBUG: base_url is WS (no SSL)")
            elif base_url.startswith("https://"):
                print("ANDROID_DEBUG ERROR: base_url is HTTPS ❌ should be WSS")
            elif base_url.startswith("http://"):
                print("ANDROID_DEBUG ERROR: base_url is HTTP ❌ should be WS/WSS")
            else:
                print("ANDROID_DEBUG WARNING: base_url has unknown scheme")

            full_url = f"{base_url}?token={self.token}"

            print("Full URL:", full_url)
            print("SSL Context is:", self.ssl_context)
            print("Server hostname:", self.hostname)
            print("========================================\n")

            try:
                async with websockets.connect(
                    full_url,
                    ssl=self.ssl_context,
                    server_hostname=self.hostname,
                    ping_interval=10,
                    ping_timeout=5,
                    close_timeout=3,
                ) as ws:

                    print("ANDROID_DEBUG: CONNECTED SUCCESSFULLY ✓")

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
                print("\n*** ANDROID_DEBUG EXCEPTION ***")
                print("URL used:", full_url)
                print("Exception type:", type(e))
                print("Exception message:", str(e))
                print("********************************\n")

                if was_connected and self.on_disconnected:
                    Clock.schedule_once(lambda dt, err=str(e): self.on_disconnected(err))
                was_connected = False

            print(f"ANDROID_DEBUG: Sleeping {backoff}s before reconnect...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
