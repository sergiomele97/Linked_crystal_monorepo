import asyncio
import threading
import ssl
import os
import certifi
import websockets
import queue
import time
from collections import deque

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

        self.recv_queue = queue.Queue(maxsize=100000)
        self.send_queue_async = None
        
        # --- NUEVO: REGISTRO DE HISTORIAL ---
        # Guardamos los últimos 1000 bytes enviados para poder retransmitirlos
        self.sent_history = deque(maxlen=1000)
        
        self.count_sent = 0
        self.count_recv_network = 0
        self.count_recv_emulator = 0
        self.is_connected = False

    def start(self, host, port, my_id, target_id):
        if self.thread and self.thread.is_alive():
            self.stop()

        protocol = "wss" if self.env != "local" else "ws"
        port_url = "" if self.env != "local" else f":{port}"
        base_url = f"{protocol}://{host}{port_url}/link"
        self.target_url = f"{base_url}?token={self.token}&id={my_id}&target={target_id}"
        
        print(f"[DEBUG-INIT] URL: {self.target_url}")
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self.is_connected = False
        if self.loop:
            try: self.loop.call_soon_threadsafe(self.loop.stop)
            except: pass

    def send_byte(self, b: int):
        if self._stop_event.is_set() or self.loop is None:
            return
        try:
            val = b & 0xFF
            self.count_sent += 1
            # Guardamos en el registro histórico antes de enviar
            self.sent_history.append(val)
            
            self.loop.call_soon_threadsafe(
                self.send_queue_async.put_nowait,
                bytes([val])
            )
        except Exception as e:
            print(f"[DEBUG-TX-ERR] {e}")

    def get_byte(self):
        """
        Retorna el byte de la cola. Si no hay, retorna 0x00 para que 
        el emulador no se bloquee y pueda seguir llamando a send_byte().
        """
        try:
            b = self.recv_queue.get_nowait()
            self.count_recv_emulator += 1
            return b
        except queue.Empty:
            return 0x00

    def _run_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.send_queue_async = asyncio.Queue()
        
        threading.Thread(target=self._stats_logger, daemon=True).start()
        
        try:
            self.loop.run_until_complete(self._main())
        except Exception as e:
            print(f"[DEBUG-FATAL] {e}")

    def _stats_logger(self):
        while not self._stop_event.is_set():
            time.sleep(2)
            conn_status = "OK" if self.is_connected else "DISCONNECTED"
            print(f"[DEBUG-STATS] Conn: {conn_status} | TX: {self.count_sent} | "
                  f"RX_Net: {self.count_recv_network} | RX_Emu: {self.count_recv_emulator} | "
                  f"History: {len(self.sent_history)}")

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
                    ping_interval=5,
                    ping_timeout=5
                ) as ws:
                    self.is_connected = True
                    print(f"[DEBUG-NET] ✔ Conectado. Enviando ráfaga de sincronización...")

                    # --- EL "EMPUJÓN" DE SINCRONIZACIÓN ---
                    # Al conectar (o reconectar), enviamos los últimos 500 bytes 
                    # que tenemos registrados para asegurar que el otro lado despierte.
                    if len(self.sent_history) > 0:
                        burst_size = min(len(self.sent_history), 500)
                        burst = bytes(list(self.sent_history)[-burst_size:])
                        await ws.send(burst)

                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))
                    
                    await asyncio.wait({send_task, recv_task}, return_when=asyncio.FIRST_COMPLETED)
                    
            except Exception as e:
                self.is_connected = False
                print(f"[DEBUG-NET-ERR] {e}")
                await asyncio.sleep(1.5)

    async def send_loop(self, ws):
        try:
            while not self._stop_event.is_set():
                byte_data = await self.send_queue_async.get()
                payload = bytearray(byte_data)
                while not self.send_queue_async.empty() and len(payload) < 512:
                    payload.extend(self.send_queue_async.get_nowait())
                await ws.send(payload)
        except: pass

    async def recv_loop(self, ws):
        try:
            async for message in ws:
                if isinstance(message, (bytes, bytearray)):
                    self.count_recv_network += len(message)
                    for b in message:
                        try:
                            self.recv_queue.put_nowait(b)
                        except queue.Full:
                            self.recv_queue.get_nowait()
                            self.recv_queue.put_nowait(b)
        except: pass