import unittest
import queue
from services.connection.link_cable.link_client import LinkClient

class TestLinkClient(unittest.TestCase):
    def test_buffer_overflow_logic(self):
        # T-RES-02: Link Buffer Management logic
        # We simulate the recv_loop's logic for putting bytes into the queue
        client = LinkClient() # Default maxsize is 10000
        
        # To make the test faster/practical, we'll use a smaller queue for this test
        # but the logic is what matters. However, LinkClient hardcodes 10000.
        # Let's test with the real limit since it's just 10k integers.
        
        # Fill to capacity
        for i in range(10000):
            client.recv_queue.put_nowait(i)
            
        self.assertTrue(client.recv_queue.full())
        
        # Simulation of recv_loop drop logic:
        # data = [99999]
        new_byte = 255
        try:
            client.recv_queue.put_nowait(new_byte)
        except queue.Full:
            client.recv_queue.get_nowait() # Drops oldest (0)
            client.recv_queue.put_nowait(new_byte)
            
        self.assertEqual(client.recv_queue.qsize(), 10000)
        # Check that the first element is now 1, not 0
        first = client.recv_queue.get_nowait()
        self.assertEqual(first, 1)

    def test_get_byte_timeout(self):
        # Verify get_byte returns 0xFF on timeout
        client = LinkClient()
        # Queue is empty
        val = client.get_byte()
        self.assertEqual(val, 0xFF)

    def test_get_byte_success(self):
        client = LinkClient()
        client.recv_queue.put_nowait(10)
        val = client.get_byte()
        self.assertEqual(val, 10)
        self.assertEqual(client.count_recv, 1)

if __name__ == "__main__":
    unittest.main()
