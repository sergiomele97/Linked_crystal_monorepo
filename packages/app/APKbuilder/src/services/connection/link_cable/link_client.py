import asyncio
import threading
import ssl
import os
import certifi
import websockets
import queue
import time

from env import STATIC_TOKEN, ENV, SSL_URL

class SmartLinkQueue(queue.Queue):
    """
    Cola especial que nunca bloquea el hilo de emulación.
    Si no hay puente o la cola está vacía, devuelve inmediatamente 0xFF (cable desconectado).
    """
    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client

    def get(self, block=True, timeout=None):
        """
        Lógica de bloqueo selectivo:
        1. Si NO hay bridge -> Devolvemos 0xFF al instante (No bloquea).
        2. Si HAY bridge -> Bloqueamos hasta que llegue un byte real.
        """
        if not getattr(self.client, 'bridged', False):
            return 0xFF
            
        try:
            # Bloqueamos esperando datos reales del peer.
            # Ponemos un timeout largo (5s) por si la conexión se muere sin avisar,
            # para que el emulador no se quede colgado para siempre.
            return super().get(block=True, timeout=5.0)
        except queue.Empty:
            # Si después de 5s no hay nada, devolvemos 0xFF para dejar respirar al motor,
            # aunque esto probablemente signifique lag o desincronización.
            return 0xFF

    def get_nowait(self):
        # El comportamiento de get ya es el correcto según el estado del bridge
        return self.get()

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

        # Usamos nuestra cola inteligente
        self.recv_queue = SmartLinkQueue(self, maxsize=10000)
        self.send_queue_async = None
        self.target_url = None

        # --- TELEMETRÍA ---
        self.count_sent = 0
        self.count_recv = 0
        self.bridged = False
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
        self.bridged = False
        # Limpiamos cola al empezar
        while not self.recv_queue.empty():
            try: self.recv_queue.get_nowait()
            except: break

        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except: pass
        self.thread = None
        self.bridged = False
        print("[LinkClient] Detenido.")

    def send_byte(self, b: int):
        """
        PyBoy entrega un byte para el cable.
        SOLO lo encolamos si el puente está activo para evitar saturar al peer.
        """
        if not self.bridged or self._stop_event.is_set() or self.loop is None or self.send_queue_async is None:
            return
        try:
            self.count_sent += 1
            self.loop.call_soon_threadsafe(
                self.send_queue_async.put_nowait,
                bytes([b & 0xFF])
            )
        except Exception:
            pass

    def get_byte(self):
        """
        Llamado por el GameBoy para leer un byte del cable.
        """
        b = self.recv_queue.get()
        if b != 0xFF:
            self.count_recv += 1
        return b

    def _run_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.send_queue_async = asyncio.Queue()
        
        stats_thread = threading.Thread(target=self._stats_logger, daemon=True)
        stats_thread.start()
        
        try:
            self.loop.run_until_complete(self._main())
        except Exception as e:
            print(f"[LinkClient] Loop asyncio colapsado: {e}")

    def _stats_logger(self):
        while not self._stop_event.is_set():
            time.sleep(2)
            if self.count_sent > 0 or self.count_recv > 0:
                print(f"[Link-Stats] BRIDGED: {self.bridged} | TX: {self.count_sent} | RX: {self.count_recv} | Q: {self.recv_queue.qsize()}")

    async def _main(self):
        while not self._stop_event.is_set():
            if not self.target_url:
                await asyncio.sleep(0.5)
                continue
            try:
                # 1. Vaciar colas
                while not self.recv_queue.empty():
                    try: self.recv_queue.get_nowait()
                    except: break

                while not self.send_queue_async.empty():
                    try: self.send_queue_async.get_nowait()
                    except: break

                async with websockets.connect(
                    self.target_url,
                    ssl=self.ssl_context,
                    server_hostname=self.hostname,
                    compression=None,
                    extensions=[],
                    ping_interval=10,
                    ping_timeout=5,
                    close_timeout=1
                ) as ws:
                    print(f"[LinkClient] ✔ Conectado al relay. Esperando bridge...")
                    
                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))
                    
                    done, pending = await asyncio.wait(
                        {send_task, recv_task}, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
                        try: await task
                        except: pass
                        
            except Exception as e:
                self.bridged = False
                print(f"[LinkClient] Error/Desconexión: {e}")
                await asyncio.sleep(2) 

    async def send_loop(self, ws):
        try:
            while not self._stop_event.is_set():
                byte_data = await self.send_queue_async.get()
                payload = bytearray(byte_data)
                
                count = 0
                while not self.send_queue_async.empty() and len(payload) < 128 and count < 64:
                    payload.extend(self.send_queue_async.get_nowait())
                    count += 1
                
                await ws.send(payload)
        except:
            return

    async def recv_loop(self, ws):
        try:
            while not self._stop_event.is_set():
                data = await ws.recv()
                if isinstance(data, (bytes, bytearray)):
                    # Solo procesamos datos si el puente está activo
                    if self.bridged:
                        for b in data:
                            try:
                                self.recv_queue.put_nowait(b)
                            except queue.Full:
                                try: self.recv_queue.get_nowait()
                                except: pass
                                self.recv_queue.put_nowait(b)
                elif isinstance(data, str):
                    if data == "bridged":
                        print("[LinkClient] !!! BRIDGE ESTABLECIDO !!!")
                        # 1. Marcar como activo
                        self.bridged = True
                        # 2. LIMPIEZA TOTAL DE BUFFERS para empezar sincronizados
                        while not self.recv_queue.empty():
                            try: self.recv_queue.get_nowait()
                            except: break
                        
                        # También limpiamos la cola de envío async
                        while not self.send_queue_async.empty():
                            try: self.send_queue_async.get_nowait()
                            except: break
        except:
            self.bridged = False
            return