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
        Lógica de bloqueo estricto (Hardware Emulation):
        1. Si NO es bloqueante (cleanup de UI) -> Sacamos lo que haya o devolvemos 0xFF.
        2. Si SÍ es bloqueante (emulador):
           - Si 'active' es False -> Devolvemos 0xFF.
           - Si 'active' es True -> BLOQUEAMOS hasta que llegue algo del peer.
        """
        if not block:
            try: return super().get(block=False)
            except queue.Empty: return 0xFF

        # Mientras el usuario quiera esté 'active' (cable conectado físicamente), esperaremos.
        # Usamos un timeout largo (0.5s) para reducir el churn de hilos si hay lag extremo.
        while getattr(self.client, 'active', False) and not self.client._stop_event.is_set():
            if self.client.thread and not self.client.thread.is_alive():
                break
            try:
                # Si llega un byte, salimos del bucle y lo devolvemos
                # Bajamos el tiempo de espera por iteración para ser más reactivos a inputs
                return super().get(block=True, timeout=0.05)
            except queue.Empty:
                # Un pequeño sleep para que el hilo no sature el núcleo si el compañero no manda nada
                time.sleep(0.001)
                continue

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
        self.active = False
        self.bridged = False
        self.last_log_time = time.time()
        self._send_lock = threading.Lock()
        self._send_buffer = []

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
        # Limpiamos cola al empezar
        while not self.recv_queue.empty():
            try: self.recv_queue.get_nowait()
            except: break

        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        # 1. Marcamos el fin e invalidamos el estado active inmediatamente
        self._stop_event.set()
        self.active = False
        self.bridged = False
        
        # 2. Despertamos al emulador si estaba esperando datos (unblock get)
        try:
            while not self.recv_queue.empty():
                self.recv_queue.get_nowait()
            self.recv_queue.put_nowait(0xFF)
        except:
            pass

        # 3. Solicitamos parada del loop de red
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except: pass
            
        # 4. Esperamos a que el hilo termine para evitar "hilos fantasm" al reconectar rápido
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            
        self.thread = None
        self.loop = None
        print("[LinkClient] Detenido.")

    def send_byte(self, b: int):
        """
        PyBoy entrega un byte para el cable.
        Los agrupamos para minimizar el churn de hilos de asyncio.
        """
        if not self.active or self._stop_event.is_set() or self.loop is None:
            return
            
        with self._send_lock:
            self._send_buffer.append(b & 0xFF)
            
        # Programar el envío inmediato si es el primer byte del buffer
        if len(self._send_buffer) == 1:
            try:
                self.loop.call_soon_threadsafe(self._flush_send_buffer)
            except: pass

    def _flush_send_buffer(self):
        """Consume el buffer y lo mete en la cola de asyncio."""
        with self._send_lock:
            if not self._send_buffer:
                return
            payload = bytes(self._send_buffer)
            self._send_buffer.clear()
            
        if self.send_queue_async:
            try:
                self.send_queue_async.put_nowait(payload)
            except: pass

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
        finally:
            # Aseguramos que el estado 'active' caiga si el hilo muere
            self.active = False
            self.bridged = False

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
                # Obtenemos un paquete (que ya puede venir agrupado)
                payload = await self.send_queue_async.get()
                
                # Intentamos agrupar más si hay ráfaga pesada
                count = 0
                while not self.send_queue_async.empty() and len(payload) < 256 and count < 10:
                    payload += self.send_queue_async.get_nowait()
                    count += 1
                
                self.count_sent += len(payload)
                await ws.send(payload)
        except:
            return

    async def recv_loop(self, ws):
        try:
            async for message in ws:
                if self._stop_event.is_set(): break
                
                if isinstance(message, (bytes, bytearray)):
                    # Telemetría de bytes recibidos
                    self.count_recv += len(message)
                    # Entregamos los bytes a la cola del emulador siempre que estemos activos
                    # (Incluso antes del mensaje 'bridged' por si acaso hay race condition)
                    for b in message:
                        try:
                            self.recv_queue.put_nowait(b)
                        except queue.Full:
                            try: self.recv_queue.get_nowait()
                            except: pass
                            self.recv_queue.put_nowait(b)
                            
                elif isinstance(message, str):
                    if message == "bridged":
                        print("[LinkClient] !!! BRIDGE ESTABLECIDO !!!")
                        self.bridged = True
                        # NO limpiamos la cola aquí para no perder bytes iniciales del handshake
        except Exception as e:
            print(f"[LinkClient] Error en recv_loop: {e}")
            self.bridged = False