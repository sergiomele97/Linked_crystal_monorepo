
import unittest
import queue
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.connection.link_cable.link_client import LinkClient

class TestLinkClient(unittest.TestCase):
    def test_buffer_overflow_logic(self):
        # T-RES-02: Link Buffer Management logic
        client = LinkClient()
        client.active = True # Important for SmartLinkQueue to work
        
        # Fill to capacity (10000)
        for i in range(10000):
            client.recv_queue.put_nowait(i)
            
        self.assertTrue(client.recv_queue.full())
        
        # Simulation of recv_loop drop logic:
        new_byte = 255
        try:
            client.recv_queue.put_nowait(new_byte)
        except queue.Full:
            # We must use super().get_nowait() or ensure SmartLinkQueue doesn't intercept
            # actually SmartLinkQueue.get_nowait() calls SmartLinkQueue.get()
            # which returns 0xFF if empty/inactive, but here it's FULL and active.
            client.recv_queue.get(block=False) # Drops oldest (0)
            client.recv_queue.put_nowait(new_byte)
            
        self.assertEqual(client.recv_queue.qsize(), 10000)
        # Check that the first element is now 1, not 0
        client.active = True
        first = client.recv_queue.get(block=False)
        self.assertEqual(first, 1)

    def test_get_byte_timeout(self):
        # Verify get_byte returns 0xFF on timeout/empty
        client = LinkClient()
        client.active = False # Inactive means always 0xFF
        val = client.get_byte()
        self.assertEqual(val, 0xFF)

    def test_get_byte_success(self):
        client = LinkClient()
        client.active = True
        client.recv_queue.put_nowait(10)
        val = client.get_byte()
        self.assertEqual(val, 10)
        self.assertEqual(client.count_recv, 1)

if __name__ == "__main__":
    unittest.main()
