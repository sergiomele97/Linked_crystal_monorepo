import asyncio
import ssl
import websockets
import struct
import certifi
from kivy.app import App
from env import STATIC_TOKEN, ENV, SSL_URL
from models.packet import Packet

class ConnectionWS:
    """
    WebSocket handler: envía el paquete local y recibe paquetes del servidor.
    """

    def __init__(self):
        self.token = STATIC_TOKEN
        self.env = ENV
        self.ssl_context = self._create_ssl_context()
        self.hostname = SSL_URL if self.env != "local" else None

    def _create_ssl_context(self):
        if self.env != "local":
            return ssl.create_default_context(cafile=certifi.where())
        return None

    async def connect(self, url):
        async with websockets.connect(
            url,
            ssl=self.ssl_context,
            server_hostname=self.hostname,
            ping_interval=10,
            ping_timeout=5,
            close_timeout=3
        ) as ws:
            await self._send_receive_loop(ws)

    async def _send_receive_loop(self, ws):
        """
        Loop principal para enviar el paquete local y recibir paquetes de otros jugadores.
        """
        app = App.get_running_app()
        local_packet = app.appData.packet
        server_packets = app.appData.serverPackets

        while True:  
            await ws.send(local_packet.to_bytes())

            try:
                data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                packet_received = Packet.from_bytes(data)
                server_packets.append(packet_received)
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.1)
