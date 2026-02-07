
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.connection.link_cable.link_client import LinkClient

class TestLinkScenarios(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = LinkClient()
        self.client.env = "local"
        self.client.hostname = "localhost"
        self.client._stop_event.clear()
        self.client.target_url = "ws://mock"
        self.client.send_queue_async = asyncio.Queue()

    async def test_bridge_establishment(self):
        # T-UI-04 (Backend part): Verify receipt of "bridged" sets state
        
        ws_mock = AsyncMock()
        cm_mock = AsyncMock()
        cm_mock.__aenter__.return_value = ws_mock
        cm_mock.__aexit__.return_value = None
        
        # Async generator for websocket messages
        async def async_gen():
            yield "bridged"
            # Give time for processing then exit
            await asyncio.sleep(0.01)
            self.client._stop_event.set()
        
        ws_mock.__aiter__.side_effect = async_gen
        
        # Patch connect where it is used
        with patch('services.connection.link_cable.link_client.websockets.connect', return_value=cm_mock):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await self.client._main()
        
        # Assertions
        self.assertTrue(self.client.bridged, "Client should be in bridged state after receiving 'bridged' message")

if __name__ == "__main__":
    unittest.main()
