import asyncio
import threading
import ssl
import os
import certifi
import websockets
import queue
import time
import struct # Para empaquetar IDs de secuencia

from env import STATIC_TOKEN, ENV, SSL_URL

class LinkClient:
    def __init__(self):
        # ... (Configuración inicial igual) ...
        self.token = STATIC_TOKEN
        self.env = ENV
        self.ssl_context = None
        self.hostname = None
        if self.env != "local":
            os.environ["SSL_CERT_FILE"] = certifi.where()
            self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.hostname = SSL_URL

        self._stop_event = threading.Event()
        self.thread = None
        self.loop = None
        self.recv_queue = queue.Queue(maxsize=100000)
        self.send_queue_async = None
        self.target_url = None

        # --- REGISTRO DE BYTES (Sincronización Inteligente) ---
        self.sent_log = []           # Lista de todos los bytes enviados: [byte, byte, ...]
        self.next_expected_id = 0    # El ID del byte que espero recibir del otro
        self.peer_last_received = -1 # El último ID que el otro me confirmó haber recibido
        
        self.count_sent = 0
        self.count_recv_network = 0
        self.is_connected = False

    def start(self, host, port, my_id, target_id):
        if self.thread and self.thread.is_alive(): self.stop()
        protocol = "wss" if self.env != "local" else "ws"
        port_url = "" if self.env != "local" else f":{port}"
        self.target_url = f"{protocol}://{host}{port_url}/link?token={self.token}&id={my_id}&target={target_id}"
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        if self.loop: self.loop.call_soon_threadsafe(self.loop.stop)

    def send_byte(self, b: int):
        """PyBoy entrega un byte. Le asignamos un ID y lo guardamos."""
        if self._stop_event.is_set() or self.loop is None: return
        
        byte_val = b & 0xFF
        current_id = len(self.sent_log)
        self.sent_log.append(byte_val)
        self.count_sent += 1

        # Enviamos paquete: [ID (4 bytes)][BYTE (1 byte)]
        payload = struct.pack("<IB", current_id, byte_val)
        
        if self.send_queue_async:
            try: self.loop.call_soon_threadsafe(self.send_queue_async.put_nowait, payload)
            except: pass

    def get_byte(self):
        """Extrae de la cola. Si está vacío, devuelve 0x00 para no bloquear."""
        try:
            b = self.recv_queue.get_nowait()
            return b
        except queue.Empty:
            return 0x00

    def _run_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.send_queue_async = asyncio.Queue()
        threading.Thread(target=self._stats_logger, daemon=True).start()
        try: self.loop.run_until_complete(self._main())
        except Exception as e: print(f"Loop fatal: {e}")

    def _stats_logger(self):
        while not self._stop_event.is_set():
            time.sleep(2)
            st = "OK" if self.is_connected else "RECONECT"
            print(f"[{st}] TX: {self.count_sent} | RX_Net: {self.count_recv_network} | Q: {self.recv_queue.qsize()} | PeerAck: {self.peer_last_received}")

    async def _main(self):
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(self.target_url, ssl=self.ssl_context) as ws:
                    self.is_connected = True
                    
                    # 1. Al conectar, informamos al otro en qué byte nos quedamos nosotros
                    # Enviamos un paquete especial: [0xFFFFFFFF][ID_QUE_ESPERO]
                    await ws.send(struct.pack("<II", 0xFFFFFFFF, self.next_expected_id))

                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))
                    
                    # Tarea de "Rescate": Cada 3 segundos, si no hay tráfico, re-enviamos el ACK
                    rescue_task = asyncio.create_task(self.rescue_loop(ws))
                    
                    await asyncio.wait({send_task, recv_task, rescue_task}, return_when=asyncio.FIRST_COMPLETED)
            except:
                self.is_connected = False
                await asyncio.sleep(1)

    async def rescue_loop(self, ws):
        """Si la conexión parece muerta, gritamos nuestra posición para despertar al otro."""
        while self.is_connected:
            await asyncio.sleep(3.0)
            # Enviamos nuestro estado actual (ACK)
            try:
                await ws.send(struct.pack("<II", 0xFFFFFFFF, self.next_expected_id))
            except: break

    async def send_loop(self, ws):
        while self.is_connected:
            payload = await self.send_queue_async.get()
            await ws.send(payload)

    async def recv_loop(self, ws):
        while self.is_connected:
            try:
                data = await ws.recv()
                if len(data) == 5: # Paquete de datos normal [ID][BYTE]
                    seq_id, val = struct.unpack("<IB", data)
                    if seq_id == self.next_expected_id:
                        self.recv_queue.put_nowait(val)
                        self.next_expected_id += 1
                        self.count_recv_network += 1
                    elif seq_id > self.next_expected_id:
                        # Nos hemos saltado bytes. No hacemos nada, 
                        # el rescue_loop del otro eventualmente retransmitirá.
                        pass
                elif len(data) == 8: # Paquete de Control (ACK) [0xFFFFFFFF][PEER_EXPECTS_ID]
                    header, peer_expects = struct.unpack("<II", data)
                    if header == 0xFFFFFFFF:
                        self.peer_last_received = peer_expects - 1
                        # RETRANSMISIÓN: El otro dice que le falta desde 'peer_expects'
                        if peer_expects < len(self.sent_log):
                            for i in range(peer_expects, len(self.sent_log)):
                                retransmit_payload = struct.pack("<IB", i, self.sent_log[i])
                                await ws.send(retransmit_payload)
            except: break