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

        self.recv_queue = queue.Queue(maxsize=100000)
        self.send_queue_async = None
        self.target_url = None

        # --- DEBUG METRICS ---
        self.count_sent = 0
        self.count_recv_network = 0 # Bytes que entran desde el socket
        self.count_recv_emulator = 0 # Bytes que el emulador saca de la cola
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
        """Llamado por PyBoy para enviar un byte"""
        if self._stop_event.is_set() or self.loop is None:
            return
        try:
            self.count_sent += 1
            self.loop.call_soon_threadsafe(
                self.send_queue_async.put_nowait,
                bytes([b & 0xFF])
            )
        except Exception as e:
            # Si esto falla, el emulador está intentando enviar pero el loop de asyncio ha muerto
            print(f"[DEBUG-TX-ERR] Error en send_byte: {e}")

    def get_byte(self):
        """Llamado por PyBoy para recibir un byte"""
        try:
            # NO BLOQUEANTE: get_nowait nunca congelará tu PC.
            # Si hay algo, lo devuelve; si no, lanza Empty.
            b = self.recv_queue.get_nowait()
            self.count_recv_emulator += 1
            return b
        except queue.Empty:
            # IMPORTANTE: Devolvemos 0x00 para que el emulador NO se pare.
            # Si devolvemos algo o esperamos, PyBoy se bloquea y deja de llamar a send_byte.
            return 0x00

    def _run_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.send_queue_async = asyncio.Queue()
        
        threading.Thread(target=self._stats_logger, daemon=True).start()
        
        try:
            self.loop.run_until_complete(self._main())
        except Exception as e:
            print(f"[DEBUG-FATAL] Loop asyncio colapsado: {e}")

    def _stats_logger(self):
        while not self._stop_event.is_set():
            time.sleep(2)
            conn_status = "OK" if self.is_connected else "DISCONNECTED"
            # Este print es vital para entender dónde está el atasco
            print(f"[DEBUG-STATS] Conn: {conn_status} | TX (Emu): {self.count_sent} | "
                  f"RX (Net): {self.count_recv_network} | RX (Emu): {self.count_recv_emulator} | "
                  f"Queue: {self.recv_queue.qsize()}")

    async def _main(self):
        while not self._stop_event.is_set():
            if not self.target_url:
                await asyncio.sleep(0.5)
                continue
            
            print(f"[DEBUG-NET] Intentando conectar...")
            try:
                async with websockets.connect(
                    self.target_url,
                    ssl=self.ssl_context,
                    server_hostname=self.hostname,
                    ping_interval=5,
                    ping_timeout=5
                ) as ws:
                    print(f"[DEBUG-NET] ✔ Conectado al servidor Go")
                    self.is_connected = True
                    
                    # Al reconectar, podríamos vaciar la cola para evitar basura vieja
                    # pero según tu petición, queremos que intente sincronizar.
                    
                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))
                    
                    done, pending = await asyncio.wait(
                        {send_task, recv_task}, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
                        
            except Exception as e:
                self.is_connected = False
                print(f"[DEBUG-NET-ERR] Error conexión: {e}")
                await asyncio.sleep(1.5)

    async def send_loop(self, ws):
        try:
            while not self._stop_event.is_set():
                byte_data = await self.send_queue_async.get()
                payload = bytearray(byte_data)
                
                # Agrupamos bytes pendientes para vaciar el buffer rápido
                while not self.send_queue_async.empty() and len(payload) < 512:
                    payload.extend(self.send_queue_async.get_nowait())
                
                try:
                    await ws.send(payload)
                except Exception as e:
                    print(f"[DEBUG-WS-SEND-ERR] Fallo al enviar payload: {e}")
                    raise e # Rompe para que el main reconecte
        except asyncio.CancelledError:
            pass

    async def recv_loop(self, ws):
        try:
            async for message in ws:
                if isinstance(message, (bytes, bytearray)):
                    self.count_recv_network += len(message)
                    for b in message:
                        try:
                            self.recv_queue.put_nowait(b)
                        except queue.Full:
                            # Si la cola está llena, el emulador no está consumiendo bytes
                            # Quitamos uno viejo para meter el nuevo
                            try: self.recv_queue.get_nowait()
                            except: pass
                            self.recv_queue.put_nowait(b)
        except Exception as e:
            print(f"[DEBUG-WS-RECV-ERR] Fallo al recibir: {e}")
            raise e