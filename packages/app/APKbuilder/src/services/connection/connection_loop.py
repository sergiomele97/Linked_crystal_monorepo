import asyncio
import threading
from kivy.clock import Clock
from .connection_ws import ConnectionWS 

class ConnectionLoop:
    def __init__(self, get_url_callback):
        self.get_url_callback = get_url_callback
        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None
        self.connection_ws = ConnectionWS()

        # Callbacks para UI
        self.on_connected = lambda: Clock.schedule_once(
            lambda dt: App.get_running_app().root.connection_status.show_ok()
        )
        self.on_disconnected = lambda err: Clock.schedule_once(
            lambda dt: App.get_running_app().root.connection_status.show_nok()
        )

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

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

            full_url = f"{base_url}?token={self.connection_ws.token}"

            try:
                await self.connection_ws.connect(full_url)
                if not was_connected and self.on_connected:
                    Clock.schedule_once(lambda dt: self.on_connected())
                was_connected = True
            except Exception as e:
                if was_connected and self.on_disconnected:
                    Clock.schedule_once(lambda dt: self.on_disconnected(str(e)))
                was_connected = False

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
