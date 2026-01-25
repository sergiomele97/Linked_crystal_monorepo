import asyncio
import threading
from kivy.app import App
from kivy.clock import Clock
from services.connection.components.socket_client import SocketClient
from services.connection.components.packet_dispatcher import PacketDispatcher

class ConnectionLoop:
    def __init__(self, get_url_callback):
        self.get_url_callback = get_url_callback
        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None

        # Components
        self.client = SocketClient()
        self.dispatcher = PacketDispatcher()
        self.chat_queue = None
        
        # Access local packet for sending
        self.localPacket = App.get_running_app().appData.packet

        # UI Callbacks
        self.on_connected = lambda: Clock.schedule_once(
            lambda dt: App.get_running_app().root.connection_status.show_ok()
        )
        self.on_disconnected = lambda err="": Clock.schedule_once(
            lambda dt: App.get_running_app().root.connection_status.show_nok()
        )

    def set_chat_manager(self, chat_manager):
        self.dispatcher.set_chat_manager(chat_manager)

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
        self.chat_queue = asyncio.Queue()
        self.loop.run_until_complete(self._main())

    def send_chat(self, message):
        if self.chat_queue and self.loop:
            self.loop.call_soon_threadsafe(self.chat_queue.put_nowait, message)

    async def send_loop(self, ws):
        while not self._stop_event.is_set():
            try:
                # 1. Chat
                while not self.chat_queue.empty():
                    msg = self.chat_queue.get_nowait()
                    await ws.send(b'\x02' + msg.encode('utf-8'))

                # 2. Game
                pkt_bytes = self.localPacket.to_bytes()
                await ws.send(b'\x01' + pkt_bytes)
            except Exception as e:
                print("❌ Send Error:", e)
                return
            await asyncio.sleep(0.1)

    async def recv_loop(self, ws):
        while not self._stop_event.is_set():
            try:
                data = await ws.recv()
                self.dispatcher.handle_data(data)
            except Exception as e:
                print("❌ Recv Error:", e)
                return

    async def _main(self):
        backoff = 1
        max_backoff = 30
        was_connected = False

        while not self._stop_event.is_set():
            base_url = self.get_url_callback()
            if not base_url:
                await asyncio.sleep(1)
                continue

            try:
                async with await self.client.connect(base_url) as ws:
                    print("✔ Connected")
                    if not was_connected:
                        self.on_connected()
                    was_connected = True

                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))

                    done, pending = await asyncio.wait(
                        {send_task, recv_task},
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for t in pending:
                        t.cancel()

            except Exception as e:
                print(f"⚠ WebSocket Error: {e}")
                if was_connected:
                    self.on_disconnected(str(e))
                was_connected = False
            
            print(f"Retrying in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
