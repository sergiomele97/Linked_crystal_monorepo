
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.connection.components.packet_dispatcher import PacketDispatcher
from models.packet import Packet

class TestMultiplayerSync(unittest.TestCase):
    def setUp(self):
        self.mock_app = MagicMock()
        self.mock_app.appData.serverPackets = []
        self.mock_app.appData.userID = 1
        
        with patch('kivy.app.App.get_running_app', return_value=self.mock_app):
            self.dispatcher = PacketDispatcher()
            self.dispatcher.my_id = 1

    def test_ignore_own_packets(self):
        # T-UI-03: Player A does NOT see a duplicate of itself rendered by the server
        
        # Scenario: Server sends a packet from ID 1 (me) and ID 2 (other)
        p1 = Packet(player_id=1, x=10, y=10).to_bytes()
        p2 = Packet(player_id=2, x=20, y=20).to_bytes()
        
        # Frame type 0x01 (Game Data)
        payload = bytes([0x01]) + p1 + p2
        
        self.dispatcher.handle_data(payload)
        
        # Verify appData.serverPackets only contains ID 2
        self.assertEqual(len(self.mock_app.appData.serverPackets), 1)
        self.assertEqual(self.mock_app.appData.serverPackets[0].player_id, 2)
        self.assertNotEqual(self.mock_app.appData.serverPackets[0].player_id, 1)

    def test_update_remote_player_state(self):
        # T-UI-03: Player B's screen renders Player A's sprite moving correctly
        
        # Initial position
        p2_v1 = Packet(player_id=2, x=20, y=20).to_bytes()
        self.dispatcher.handle_data(bytes([0x01]) + p2_v1)
        self.assertEqual(self.mock_app.appData.serverPackets[0].player_x_coord, 20)
        
        # Updated position
        p2_v2 = Packet(player_id=2, x=21, y=20).to_bytes()
        self.dispatcher.handle_data(bytes([0x01]) + p2_v2)
        
        # Verify update
        self.assertEqual(len(self.mock_app.appData.serverPackets), 1)
        self.assertEqual(self.mock_app.appData.serverPackets[0].player_x_coord, 21)

if __name__ == "__main__":
    unittest.main()
