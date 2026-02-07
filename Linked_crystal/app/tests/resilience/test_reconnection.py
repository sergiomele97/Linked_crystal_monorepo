
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.connection.link_cable.link_client import LinkClient

class TestLinkClientReconnection(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch websockets before importing if needed, but since we are in venv, 
        # we can just patch it where used.
        self.client = LinkClient()
        self.client.env = "local"
        self.client.hostname = "localhost"
        self.client._stop_event.clear()
        self.client.target_url = "ws://localhost:8080/link"
        self.client.send_queue_async = asyncio.Queue()

    async def test_reconnection_logic(self):
        # T-RES-01: Reconnection Logic
        
        # We need to mock 'websockets.connect' inside 'services.connection.link_cable.link_client'
        
        # Success context manager mock
        ws_mock = AsyncMock()
        cm_mock = AsyncMock()
        cm_mock.__aenter__.return_value = ws_mock
        cm_mock.__aexit__.return_value = None
        
        # Configure ws_mock as an empty async iterator to exit recv_loop immediately
        ws_mock.__aiter__.side_effect = lambda: (None for _ in range(0)) # Empty async gen helper
        
        # Need a real async gen for __aiter__
        async def empty_gen():
            if False: yield None
        ws_mock.__aiter__.side_effect = empty_gen

        # Use a counter to fail the first time
        calls = [0]
        def connect_side_effect(*args, **kwargs):
            calls[0] += 1
            if calls[0] == 1:
                raise Exception("Connection Refused")
            else:
                # On second call, we stop the loop to finish the test
                self.client._stop_event.set()
                return cm_mock

        with patch('services.connection.link_cable.link_client.websockets.connect', side_effect=connect_side_effect) as mock_connect:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                await self.client._main()
                
                # Assertions
                self.assertGreaterEqual(calls[0], 2, "Should have attempted connection at least twice")
                mock_sleep.assert_called()

if __name__ == "__main__":
    unittest.main()
