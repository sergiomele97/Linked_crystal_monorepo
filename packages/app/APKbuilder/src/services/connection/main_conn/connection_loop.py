import asyncio
import threading
import ssl
import os
import certifi
import websockets
from kivy.app import App
from kivy.clock import Clock

from env import STATIC_TOKEN, ENV, SSL_URL
from models.packet import Packet  # tu clase Packet

class ConnectionLoop:
    PACKET_SIZE = 24

    def __init__(self, get_url_callback):
        self.get_url_callback = get_url_callback
        self.token = STATIC_TOKEN
        self.env = ENV
        self.my_id = None

        # -----------------------------
        #   SSL + CERTIFICADOS ANDROID
        # -----------------------------
        self.ssl_context = None
        self.hostname = None

        if self.env != "local":
            # Fuerza ruta del bundle de certifi (Android necesita esto)
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
        #   ACCESO A DATOS DEL APP
        # -----------------------------
        app = App.get_running_app()
        self.localPacket = app.appData.packet
        self.serverPackets = app.appData.serverPackets

        # -----------------------------
        #   CALLBACKS VISUALES WIFI
        # -----------------------------
        self.on_connected = lambda: Clock.schedule_once(
            lambda dt: App.get_running_app().root.connection_status.show_ok()
        )

        self.on_disconnected = lambda err="": Clock.schedule_once(
            lambda dt: App.get_running_app().root.connection_status.show_nok()
        )

    # ====================================================================================
    #   START / STOP
    # ====================================================================================
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
        self.loop.run_until_complete(self._main())

    # ====================================================================================
    #   SEND
    # ====================================================================================
    async def send_loop(self, ws):
        while not self._stop_event.is_set():
            #print(self.localPacket)
            try:
                pkt_bytes = self.localPacket.to_bytes()
                await ws.send(pkt_bytes)
            except Exception as e:
                print("❌ Error en send_loop:", e)
                return

            await asyncio.sleep(0.1)

    # ====================================================================================
    #   RECV
    # ====================================================================================
    async def recv_loop(self, ws):

        while not self._stop_event.is_set():
            try:
                data = await ws.recv()

                # --- Mensaje de bienvenida (4 bytes) ---
                if isinstance(data, (bytes, bytearray)) and len(data) == 4 and self.my_id is None:
                    self.my_id = int.from_bytes(data, "little")
                    App.get_running_app().appData.userID = self.my_id
                    print("Mi ID recibido:", self.my_id)
                    continue

                if isinstance(data, (bytes, bytearray)):
                    n = len(data) // self.PACKET_SIZE

                    # Limpiamos la lista existente y agregamos solo paquetes válidos
                    self.serverPackets.clear()
                    for i in range(n):
                        chunk = data[i * self.PACKET_SIZE:(i + 1) * self.PACKET_SIZE]
                        if len(chunk) != self.PACKET_SIZE:
                            continue

                        try:
                            p = Packet.from_bytes(chunk)
                            # Ignorar mi propio paquete
                            if self.my_id is not None and p.player_id == self.my_id:
                                continue
                            self.serverPackets.append(p)
                        except Exception as e:
                            print("Error decodificando packet:", e)
                            continue

            except websockets.exceptions.ConnectionClosed:
                print("❌ Conexión cerrada en recv_loop")
                return
            except Exception as e:
                print("❌ Error en recv_loop:", e)
                return

    # ====================================================================================
    #   MAIN (conectividad + callbacks)
    # ====================================================================================
    async def _main(self):
        backoff = 1
        max_backoff = 30
        was_connected = False

        while not self._stop_event.is_set():
            base_url = self.get_url_callback()
            if not base_url:
                await asyncio.sleep(1)
                continue

            full_url = f"{base_url}?token={self.token}"
            print(f"Intentando conectar a: {full_url}")

            try:
                async with websockets.connect(
                    full_url,
                    ssl=self.ssl_context,
                    server_hostname=self.hostname,
                    ping_interval=10,
                    ping_timeout=5,
                    close_timeout=3,
                ) as ws:

                    print("✔ Conectado:", full_url)

                    # -----------------------------
                    #   CALLBACK WIFI OK
                    # -----------------------------
                    if not was_connected:
                        self.on_connected()
                    was_connected = True

                    # -----------------------------
                    #   SEND + RECV EN PARALELO
                    # -----------------------------
                    send_task = asyncio.create_task(self.send_loop(ws))
                    recv_task = asyncio.create_task(self.recv_loop(ws))

                    done, pending = await asyncio.wait(
                        {send_task, recv_task},
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    for t in pending:
                        t.cancel()

            except Exception as e:
                print(f"⚠ Error WebSocket: {e}")

                if was_connected:
                    self.on_disconnected(str(e))
                was_connected = False
            print(f"Reintentando en {backoff}s…")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
