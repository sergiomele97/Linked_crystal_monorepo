import asyncio
import threading
import ssl
import os
import certifi
import websockets
import queue  # Cola síncrona estándar
from kivy.clock import Clock

from env import STATIC_TOKEN, ENV, SSL_URL

class LinkClient:
    def __init__(self):
        self.token = STATIC_TOKEN
        self.env = ENV
        
        # -----------------------------
        #   SSL + CERTIFICADOS ANDROID
        # -----------------------------
        self.ssl_context = None
        self.hostname = None

        if self.env != "local":
            os.environ["SSL_CERT_FILE"] = certifi.where()
            self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.hostname = SSL_URL
        else:
            self.ssl_context = None
            self.hostname = None

        # -----------------------------
        #   THREAD / LOOP
        # -----------------------------
        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None

        # -----------------------------
        #   QUEUES (PUENTE ENTRE HILOS)
        # -----------------------------
        # Cola síncrona: AsyncIO (Red) -> PyBoy (Emulador)
        self.recv_queue = queue.Queue()
        
        # Cola asíncrona: PyBoy (Emulador) -> AsyncIO (Red)
        # Se inicializa dentro del loop porque pertenece a asyncio
        self.send_queue_async = None 

        # Datos de conexión dinámicos
        self.target_url = None

    # ====================================================================================
    #   PUBLIC API (Llamado desde Kivy / PyBoy)
    # ====================================================================================
    def start(self, host, port, my_id, target_id):
        """Inicia el hilo de conexión específico para el Link Cable"""
        if self.thread and self.thread.is_alive():
            self.stop() # Reiniciar si ya existía

        # Construir URL WS://host:port/link?token=...
        protocol = "wss" if self.env != "local" else "ws"
        base_url = f"{protocol}://{host}:{port}/link"
        self.target_url = f"{base_url}?token={self.token}&id={my_id}&target={target_id}"

        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[LinkClient] Iniciando hilo hacia: {target_id}")

    def stop(self):
        """Detiene la conexión y limpia recursos"""
        self._stop_event.set()
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except:
                pass
        self.thread = None

    def send_byte(self, b: int):
        """
        HOOK para PyBoy. 
        Se llama desde el hilo del emulador (Síncrono).
        Pasa el byte al hilo de Asyncio de forma segura.
        """
        if self._stop_event.is_set() or self.loop is None or self.send_queue_async is None:
            return

        try:
            # Programamos la inserción en la cola asíncrona desde este hilo externo
            self.loop.call_soon_threadsafe(
                self.send_queue_async.put_nowait, 
                bytes([b & 0xFF])
            )
        except Exception:
            pass # Evitar romper el emulador si la red cae

    # ====================================================================================
    #   INTERNAL LOOP (Asyncio)
    # ====================================================================================
    def _run_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        
        # Inicializamos la cola asíncrona dentro del contexto del loop
        self.send_queue_async = asyncio.Queue()
        
        self.loop.run_until_complete(self._main())

    async def _main(self):
        backoff = 1
        max_backoff = 10 

        while not self._stop_event.is_set():
            if not self.target_url:
                await asyncio.sleep(1)
                continue

            try:
                print(f"[LinkClient] Conectando WS...")
                async with websockets.connect(
                    self.target_url,
                    ssl=self.ssl_context,
                    server_hostname=self.hostname,
                    ping_interval=None, # Desactivar ping para latencia pura (opcional)
                    close_timeout=1,
                ) as ws:
                    print("[LinkClient] ✔ Conectado (Túnel listo)")
                    backoff = 1

                    # Corremos lectura y escritura en paralelo
                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))

                    done, pending = await asyncio.wait(
                        {send_task, recv_task},
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    for t in pending:
                        t.cancel()

            except Exception as e:
                print(f"[LinkClient] ⚠ Error: {e}")
            
            if self._stop_event.is_set():
                break

            print(f"[LinkClient] Reintentando en {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

    # ====================================================================================
    #   SEND LOOP (Asyncio)
    # ====================================================================================
    async def send_loop(self, ws):
        while not self._stop_event.is_set():
            try:
                # Esperamos a que PyBoy mande algo a la cola (bloqueante asíncrono)
                byte_data = await self.send_queue_async.get()
                
                # Enviamos inmediatamente (Binary frame)
                await ws.send(byte_data)
            except Exception as e:
                print("[LinkClient] Error send_loop:", e)
                return

    # ====================================================================================
    #   RECV LOOP (Asyncio)
    # ====================================================================================
    async def recv_loop(self, ws):
        while not self._stop_event.is_set():
            try:
                # Esperamos datos del servidor Go
                data = await ws.recv()
                
                # Metemos en la cola síncrona para que PyBoy lo lea en su .tick()
                if isinstance(data, (bytes, bytearray)):
                    for b in data:
                        self.recv_queue.put(b)
                elif isinstance(data, str):
                    # Fallback por si acaso
                    for b in data.encode('latin1'):
                        self.recv_queue.put(b)
                        
            except Exception as e:
                print("[LinkClient] Error recv_loop:", e)
                return