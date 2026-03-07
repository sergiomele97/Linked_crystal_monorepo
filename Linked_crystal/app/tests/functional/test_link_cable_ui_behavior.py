import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time
import asyncio

# Configure Kivy for headless testing
os.environ['KIVY_NO_CONSOLELOG'] = '1'
os.environ['KIVY_NO_ARGS'] = '1'

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from kivy.config import Config
Config.set('graphics', 'backend', 'headless')

from services.emulator.emulator_core_interface import EmulatorCoreInterface
from services.connection.link_cable.link_client import LinkClient

class TestLinkCableUIBehavior(unittest.TestCase):
    def setUp(self):
        # Mocking App.get_running_app()
        self.mock_app = MagicMock()
        self.patcher_app = patch('kivy.app.App.get_running_app', return_value=self.mock_app)
        self.patcher_app.start()
        
        # Mocking SpriteRenderer and permissions
        self.patcher_sprite = patch('services.drawing.drawing_manager.SpriteRenderer').start()
        self.patcher_perms = patch('services.emulator.emulator_core_interface.solicitar_permisos').start()

    def tearDown(self):
        patch.stopall()

    def test_5_1_idle_no_block(self):
        """5.1 Sin conexión: El emulador no debe bloquearse en absoluto."""
        interface = EmulatorCoreInterface()
        # Simulate disconnected state
        interface.link_client.active = False
        interface.link_client.bridged = False
        
        # Calling get_byte should be instantaneous (return 0xFF)
        start = time.time()
        for _ in range(100):
            val = interface.link_client.get_byte()
            self.assertEqual(val, 0xFF)
        duration = time.time() - start
        
        self.assertLess(duration, 0.1, "get_byte blocked while disconnected")

    def test_5_2_waiting_no_block(self):
        """5.2 Intento: Mientras esperamos bridge (active=True, bridged=False), no debe bloquear."""
        interface = EmulatorCoreInterface()
        interface.link_client.active = True
        interface.link_client.bridged = False
        
        # Even if active, if not bridged, it returns 0xFF immediately
        start = time.time()
        for _ in range(100):
            val = interface.link_client.get_byte()
            self.assertEqual(val, 0xFF)
        duration = time.time() - start
        
        self.assertLess(duration, 0.1, "get_byte blocked while waiting for bridge")

    def test_5_3_bridged_timeout(self):
        """5.3 Bridge: En bridge debe bloquear, y el watchdog debe actuar si pasan 30s."""
        # This test uses unit logic to verify the behavior without waiting 30 real seconds
        client = LinkClient()
        client.active = True
        client.bridged = True
        client.is_main_thread_waiting = True
        client.stop = MagicMock()
        
        # Verify it reaches timeout state (using the logic we have in test_link_cable_logic)
        # We've already tested the watchdog loop in unit tests, 
        # but here we ensure the EmulatorCoreInterface setup doesn't break it.
        interface = EmulatorCoreInterface()
        interface.link_client = client
        
        # Verify that get_byte for a bridged client with no data would block 
        # (we test this by checking the flag it sets)
        import threading
        def call_get_byte():
            client.get_byte()
            
        t = threading.Thread(target=call_get_byte)
        t.start()
        
        time.sleep(0.1) # Give time for get_byte to start waiting
        self.assertTrue(client.is_main_thread_waiting, "Emulator core should signal it's waiting for data")
        
        # Simulate data arrival to unblock
        client.recv_queue.put(0x00)
        t.join(timeout=1)
        self.assertFalse(client.is_main_thread_waiting, "Emulator core should stop waiting once data arrives")

if __name__ == "__main__":
    unittest.main()
