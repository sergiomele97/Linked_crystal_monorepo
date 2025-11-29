import asyncio
import struct
import ssl
import websockets
import certifi
from kivy.app import App

from env import STATIC_TOKEN, ENV, SSL_URL

class ConnectionWS:
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
            await self._mock_send_receive_loop(ws)

    async def _mock_send_receive_loop(self, ws):
        x = y = z = 0
        while True:  
            await ws.send(self._generate_mock_packet(x, y, z))
            try:
                await asyncio.wait_for(ws.recv(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
            x += 1
            y += 1
            z += 1
            await asyncio.sleep(0.1)

    def _generate_mock_packet(self, x, y, z):
        return struct.pack("<3i", x, y, z)
