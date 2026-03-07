
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

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
        
        # We use an event because self.client.bridged is reset to False when the loop stops
        was_bridged_event = asyncio.Event()
        
        # Configure recv to return "bridged" once, then set stop event
        async def mock_recv():
            if not self.client.bridged:
                return "bridged"
            
            # If we reach here, it means the previous "bridged" message was processed
            # and self.client.bridged should be True
            if self.client.bridged:
                was_bridged_event.set()
            
            # Once bridged, we stop the loop
            self.client._stop_event.set()
            return b"" # dummy data to let loop finish
        
        ws_mock.recv.side_effect = mock_recv
        
        # Patch connect where it is used
        with patch('services.connection.link_cable.link_client.websockets.connect', return_value=cm_mock):
            # We don't want real sleeps during tests
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await self.client._main()
        
        # Assertions
        self.assertTrue(was_bridged_event.is_set(), "Client should have been in bridged state at some point after receiving 'bridged'")

if __name__ == "__main__":
    unittest.main()
