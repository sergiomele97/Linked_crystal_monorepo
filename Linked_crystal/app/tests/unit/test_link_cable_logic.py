
import unittest
import queue
import time
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.connection.link_cable.link_client import LinkClient

class TestLinkCableLogic(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = LinkClient()

    def test_get_byte_inactive(self):
        """Case 1: Desconectado (active=False) -> 0xFF inmediato."""
        self.client.active = False
        self.client.bridged = True
        self.client.recv_queue.put_nowait(10)
        
        start_time = time.time()
        val = self.client.get_byte()
        end_time = time.time()
        
        self.assertEqual(val, 0xFF)
        self.assertLess(end_time - start_time, 0.1)

    def test_get_byte_waiting(self):
        """Case 2: Esperando (active=True, bridged=False) -> 0xFF inmediato."""
        self.client.active = True
        self.client.bridged = False
        self.client.recv_queue.put_nowait(10)
        
        start_time = time.time()
        val = self.client.get_byte()
        end_time = time.time()
        
        self.assertEqual(val, 0xFF)
        self.assertLess(end_time - start_time, 0.1)

    def test_get_byte_bridged_with_data(self):
        """Case 3: En Bridge (active=True, bridged=True) -> Return data if available."""
        self.client.active = True
        self.client.bridged = True
        self.client.recv_queue.put_nowait(42)
        
        val = self.client.get_byte()
        self.assertEqual(val, 42)
        self.assertEqual(self.client.count_recv, 1)

    def test_get_byte_bridged_blocking(self):
        """Case 3: En Bridge (active=True, bridged=True) -> BLOCK until data."""
        self.client.active = True
        self.client.bridged = True
        
        def delayed_put():
            time.sleep(0.2)
            self.client.recv_queue.put_nowait(99)
            
        import threading
        t = threading.Thread(target=delayed_put)
        t.start()
        
        start_time = time.time()
        val = self.client.get_byte()
        end_time = time.time()
        
        self.assertEqual(val, 99)
        self.assertGreaterEqual(end_time - start_time, 0.15)
        t.join()

    def test_is_main_thread_waiting_toggle(self):
        """Verify is_main_thread_waiting is correctly toggled during blocking get."""
        self.client.active = True
        self.client.bridged = True
        
        self.assertFalse(self.client.is_main_thread_waiting)
        
        check_results = []
        def check_flag():
            time.sleep(0.1)
            check_results.append(self.client.is_main_thread_waiting)
            self.client.recv_queue.put_nowait(1)
            
        import threading
        t = threading.Thread(target=check_flag)
        t.start()
        
        self.client.get_byte()
        t.join()
        
        self.assertTrue(check_results[0])
        self.assertFalse(self.client.is_main_thread_waiting)

    @patch('time.time')
    async def test_watchdog_timeout_trigger(self, mock_time):
        """Verify watchdog triggers stop() after 30s of blocked inactivity."""
        self.client.active = True
        self.client.bridged = True
        self.client.is_main_thread_waiting = True
        self.client.stop = MagicMock()
        
        current_time = 1000.0
        mock_time.return_value = current_time
        self.client.last_recv_time = current_time
        
        # Start watchdog
        watchdog_task = asyncio.create_task(self.client.watchdog_loop())
        
        # IMPORTANT: Wait long enough for the loop to run at least once (it sleeps 0.5s)
        # and capture the current 'mock_time' into 'blocked_since'.
        await asyncio.sleep(0.6) 
        
        # Advancing 31 seconds in mock time
        mock_time.return_value = current_time + 31.0
        
        # Wait for watchdog to wake up again and detect the difference
        # We wait up to 2s of real time
        for _ in range(20):
            await asyncio.sleep(0.1)
            if self.client.timeout_reached:
                break
        
        self.client.stop.assert_called_once()
        self.assertTrue(self.client.timeout_reached)
        
        # Cleanup
        self.client._stop_event.set()
        await watchdog_task

    @patch('time.time')
    async def test_watchdog_reset_on_receipt(self, mock_time):
        """Verify watchdog resets timer when data is received."""
        self.client.active = True
        self.client.bridged = True
        self.client.is_main_thread_waiting = True
        self.client.stop = MagicMock()
        
        current_time = 1000.0
        mock_time.return_value = current_time
        self.client.last_recv_time = current_time
        
        watchdog_task = asyncio.create_task(self.client.watchdog_loop())
        await asyncio.sleep(0.6) # blocked_since = 1000.0
        
        # Advance mock time by 20 seconds
        mock_time.return_value = 1020.0
        await asyncio.sleep(0.6) # Let loop run
        self.client.stop.assert_not_called()
        
        # Receive data at 1025.0
        self.client.last_recv_time = 1025.0
        
        # Advance mock time to 1040.0 (40s total, but only 15s since last receipt)
        mock_time.return_value = 1040.0
        await asyncio.sleep(0.6)
        self.client.stop.assert_not_called()
        
        # Advance to 1056.0 (31s since last receipt)
        mock_time.return_value = 1056.0
        for _ in range(20):
            await asyncio.sleep(0.1)
            if self.client.timeout_reached:
                break
                
        self.client.stop.assert_called_once()
        
        # Cleanup
        self.client._stop_event.set()
        await watchdog_task

if __name__ == "__main__":
    unittest.main()
