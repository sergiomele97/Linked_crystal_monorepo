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
    Si la cola está vacía o el cliente no está activo, devuelve inmediatamente 0xFF.
    """
    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client

    def get(self, block=True, timeout=None):
        """
        Lógica de bloqueo selectivo (3 casos):
        1. Desconectado (active=False) -> 0xFF inmediato.
        2. Esperando (active=True, bridged=False) -> 0xFF inmediato.
        3. En Bridge (active=True, bridged=True) -> BLOQUEO estricto.
        """
        if not block:
            try: return super().get(block=False)
            except queue.Empty: return 0xFF

        # Caso 1 y 2: No activo o esperando compañero -> No bloqueamos
        if not getattr(self.client, 'active', False) or not getattr(self.client, 'bridged', False):
            return 0xFF

        # Caso 3: Bridge activo -> Bloqueamos el hilo hasta que llegue algo
        if hasattr(self.client, 'is_main_thread_waiting'):
            self.client.is_main_thread_waiting = True
            
        try:
            while getattr(self.client, 'active', False) and getattr(self.client, 'bridged', False) and not self.client._stop_event.is_set():
                try:
                    return super().get(block=True, timeout=0.05)
                except queue.Empty:
                    time.sleep(0.001)
                    continue
        finally:
            if hasattr(self.client, 'is_main_thread_waiting'):
                self.client.is_main_thread_waiting = False

        return 0xFF

    def get_nowait(self):
        return self.get(block=False)

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

        self.recv_queue = SmartLinkQueue(self, maxsize=10000)
        self.send_queue_async = None
        self.target_url = None

        # --- TELEMETRÍA ---
        self.count_sent = 0
        self.count_recv = 0
        self.active = False
        self.bridged = False
        self.is_main_thread_waiting = False
        self.timeout_reached = False
        self.last_log_time = time.time()
        self.last_recv_time = time.time()

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
        self.active = True
        self.bridged = False
        self.timeout_reached = False
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self.active = False
        self.bridged = False
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
        except Exception:
            pass

    def get_byte(self):
        """
        Lee un byte de la cola inteligente.
        Si active=True, esta llamada BLOQUEARÁ el hilo hasta recibir datos.
        """
        b = self.recv_queue.get(block=True)
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
        finally:
            self.active = False
            self.bridged = False

    def _stats_logger(self):
        while not self._stop_event.is_set():
            time.sleep(2)
            if self.count_sent > 0 or self.count_recv > 0:
                print(f"[Link-Stats] TX: {self.count_sent} | RX: {self.count_recv} | Queue: {self.recv_queue.qsize()}")

    async def _main(self):
        while not self._stop_event.is_set():
            if not self.target_url:
                await asyncio.sleep(0.5)
                continue
            try:
                # 1. Vaciar cola de RECEPCIÓN (hilos)
                for _ in range(10001):
                    if self.recv_queue.empty(): break
                    try: self.recv_queue.get_nowait()
                    except queue.Empty: break

                # 2. Vaciar cola de ENVÍO (asyncio)
                while not self.send_queue_async.empty():
                    try: self.send_queue_async.get_nowait()
                    except: break

                self.bridged = False
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
                    self.count_sent = 0
                    self.count_recv = 0
                    print(f"[LinkClient] ✔ Conectado y Sincronizado.")
                    
                    self.last_recv_time = time.time()
                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))
                    
                    # Iniciamos el watchdog fuera si no existe o lo manejamos aquí
                    watchdog_task = asyncio.create_task(self.watchdog_loop())
                    
                    done, pending = await asyncio.wait(
                        {send_task, recv_task, watchdog_task}, 
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

    async def watchdog_loop(self):
        """Tarea que monitoriza si la conexión se ha quedado colgada."""
        blocked_since = None
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(0.5)
                
                # Solo contamos si el hilo principal está bloqueado Y hay bridge
                if self.active and self.bridged and getattr(self, 'is_main_thread_waiting', False):
                    if blocked_since is None:
                        blocked_since = time.time()
                    
                    # El tiempo de timeout real es desde lo que haya ocurrido más tarde:
                    # empezar a esperar o recibir el último paquete.
                    recv_time = self.last_recv_time if self.last_recv_time is not None else 0.0
                    effective_wait_start = max(blocked_since, recv_time)
                    elapsed = time.time() - effective_wait_start
                    
                    if elapsed > 30.0:
                        print(f"[LinkClient] ⚠️ Timeout de 30s detectado (sin actividad y bloqueado). Cerrando.")
                        self.timeout_reached = True
                        self.stop()
                        break
                else:
                    # Si no está bloqueado o cambió el estado, reseteamos el contador
                    blocked_since = None
        except:
            pass

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
                    self.last_recv_time = time.time()
                    # Procesamiento masivo para ganar microsegundos
                    for b in data:
                        try:
                            self.recv_queue.put_nowait(b)
                        except queue.Full:
                            try: self.recv_queue.get_nowait()
                            except: pass
                            self.recv_queue.put_nowait(b)
                elif isinstance(data, str):
                    if data == "bridged":
                        self.bridged = True
                # Eliminado sleep(0) para máxima prioridad
        except:
            self.bridged = False
            return
        finally:
            self.bridged = False