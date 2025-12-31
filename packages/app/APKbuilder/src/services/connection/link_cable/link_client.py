import asyncio
import threading
import ssl
import os
import certifi
import websockets
import queue
import time

from env import STATIC_TOKEN, ENV, SSL_URL

class LinkClient:
    def __init__(self):
        self.token = STATIC_TOKEN
        self.env = ENV
        self.ssl_context = None
        self.hostname = None

        if self.env != "local":
            os.environ["SSL_CERT_FILE"] = certifi.where()
            self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.hostname = SSL_URL
        else:
            self.ssl_context = None
            self.hostname = None

        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None

        self.recv_queue = queue.Queue(maxsize=10000)
        self.send_queue_async = None 
        self.target_url = None

        # --- TELEMETRÍA ---
        self.count_sent = 0
        self.count_recv = 0
        self.last_log_time = time.time()

    def start(self, host, port, my_id, target_id):
        if self.thread and self.thread.is_alive():
            self.stop()

        protocol = "wss" if self.env != "local" else "ws"
        port_url = "" if self.env != "local" else f":{port}"
        base_url = f"{protocol}://{host}{port_url}/link"
        self.target_url = f"{base_url}?token={self.token}&id={my_id}&target={target_id}"
        
        print(f"[LinkClient] Intentando conectar a: {self.target_url}")
        
        self._stop_event.clear()
        self.count_sent = 0
        self.count_recv = 0
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except: pass
        self.thread = None
        print("[LinkClient] Detenido.")

    def send_byte(self, b: int):
        if self._stop_event.is_set() or self.loop is None or self.send_queue_async is None:
            return
        try:
            self.count_sent += 1
            self.loop.call_soon_threadsafe(
                self.send_queue_async.put_nowait, 
                bytes([b & 0xFF])
            )
        except Exception as e:
            print(f"[LinkClient] Error send_byte: {e}")

    def get_byte(self):
        try:
            b = self.recv_queue.get_nowait()
            self.count_recv += 1
            return b
        except queue.Empty:
            return 0xFF 

    def _run_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.send_queue_async = asyncio.Queue()
        
        # Hilo para printear estadísticas cada 2 segundos sin bloquear nada
        stats_thread = threading.Thread(target=self._stats_logger, daemon=True)
        stats_thread.start()
        
        self.loop.run_until_complete(self._main())

    def _stats_logger(self):
        """Printea el estado del tráfico para debuggear la pantalla azul"""
        while not self._stop_event.is_set():
            time.sleep(2)
            if self.count_sent > 0 or self.count_recv > 0:
                print(f"[Link-Stats] TX: {self.count_sent} bytes | RX: {self.count_recv} bytes | Queue: {self.recv_queue.qsize()}")

    async def _main(self):
        while not self._stop_event.is_set():
            if not self.target_url:
                await asyncio.sleep(0.5)
                continue
            try:
                async with websockets.connect(
                    self.target_url,
                    ssl=self.ssl_context,
                    server_hostname=self.hostname,
                    compression=None,
                    ping_interval=None 
                ) as ws:
                    print("[LinkClient] ✔ Conectado al Bridge")
                    
                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))
                    
                    await asyncio.wait({send_task, recv_task}, return_when=asyncio.FIRST_COMPLETED)
            except Exception as e:
                print(f"[LinkClient] Error de conexión: {e}")
                await asyncio.sleep(2)

    async def send_loop(self, ws):
        while not self._stop_event.is_set():
            try:
                byte_data = await self.send_queue_async.get()
                payload = bytearray(byte_data)
                
                # Agrupación para optimizar el túnel
                while not self.send_queue_async.empty() and len(payload) < 128:
                    payload.extend(self.send_queue_async.get_nowait())
                
                await ws.send(payload)
            except Exception as e:
                print(f"[LinkClient] Error en send_loop: {e}")
                return

    async def recv_loop(self, ws):
        while not self._stop_event.is_set():
            try:
                data = await ws.recv()
                if isinstance(data, (bytes, bytearray)):
                    for b in data:
                        try:
                            self.recv_queue.put_nowait(b)
                        except queue.Full:
                            self.recv_queue.get_nowait()
                            self.recv_queue.put_nowait(b)
            except Exception as e:
                print(f"[LinkClient] Error en recv_loop: {e}")
                return