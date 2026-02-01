import asyncio
import ssl
import os
import certifi
import websockets
from env import SSL_URL, ENV, STATIC_TOKEN
from services.logger import log

class SocketClient:
    def __init__(self):
        self.token = STATIC_TOKEN
        self.env = ENV
        
        # SSL Setup
        self.ssl_context = None
        self.hostname = None
        if self.env != "local":
            os.environ["SSL_CERT_FILE"] = certifi.where()
            self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.hostname = SSL_URL

    async def connect(self, base_url):
        full_url = f"{base_url}?token={self.token}"
        log(f"Connecting to: {full_url}")
        
        return websockets.connect(
            full_url,
            ssl=self.ssl_context,
            server_hostname=self.hostname,
            ping_interval=10,
            ping_timeout=5,
            close_timeout=3,
        )
