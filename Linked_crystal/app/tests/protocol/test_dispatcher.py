import unittest
from unittest.mock import MagicMock, patch
from services.connection.components.packet_dispatcher import PacketDispatcher
from models.packet import Packet

class TestPacketDispatcher(unittest.TestCase):
    def setUp(self):
        # Mocking App and its hierarchy to avoid Kivy dependency errors
        self.mock_app = MagicMock()
        self.mock_app.appData.serverPackets = []
        self.mock_app.appData.userID = None
        
        with patch('kivy.app.App.get_running_app', return_value=self.mock_app):
            self.dispatcher = PacketDispatcher()

    def test_id_assignment(self):
        # T-PRO-02: Link Cable ID Assignment
        # Sending raw 4 bytes (ID = 10)
        data = (10).to_bytes(4, "little")
        self.dispatcher.handle_data(data)
        
        self.assertEqual(self.dispatcher.my_id, 10)
        self.assertEqual(self.mock_app.appData.userID, 10)

    def test_chat_multiplexing(self):
        # T-PRO-03: Chat Multiplexing
        mock_chat_manager = MagicMock()
        self.dispatcher.set_chat_manager(mock_chat_manager)
        
        # Format: [0x02] [SenderID(4b)] [Message]
        sender_id = 5
        message = "Hello World"
        # Multiplexed frame: [Type 0x02] [ID(4b)] [Msg]
        payload = bytes([0x02]) + sender_id.to_bytes(4, "little") + message.encode('utf-8')
        
        self.dispatcher.handle_data(payload)
        
        mock_chat_manager.receive_message.assert_called_once_with(5, "Hello World")

    def test_game_data_multiplexing(self):
        # Verify game data (0x01) clears store and appends packets (excluding own ID)
        self.dispatcher.my_id = 1
        
        p1 = Packet(player_id=1, x=10, y=10).to_bytes()
        p2 = Packet(player_id=2, x=20, y=20).to_bytes()
        
        # Multiplexed frame: [Type 0x01] [Packets...]
        payload = bytes([0x01]) + p1 + p2
        
        self.dispatcher.handle_data(payload)
        
        # Should only contain p2 (ID 2)
        self.assertEqual(len(self.mock_app.appData.serverPackets), 1)
        self.assertEqual(self.mock_app.appData.serverPackets[0].player_id, 2)

    def test_reconnection_id_update(self):
        # 1. First connection (ID 5)
        self.dispatcher.handle_data((5).to_bytes(4, "little"))
        self.assertEqual(self.dispatcher.my_id, 5)
        
        # 2. Reconnection (ID 6)
        self.dispatcher.handle_data((6).to_bytes(4, "little"))
        self.assertEqual(self.dispatcher.my_id, 6)
        self.assertEqual(self.mock_app.appData.userID, 6)

        # 3. Verify filtering uses new ID
        p_old = Packet(player_id=5, x=10, y=10).to_bytes()
        p_new = Packet(player_id=6, x=20, y=20).to_bytes()
        
        payload = bytes([0x01]) + p_old + p_new
        self.dispatcher.handle_data(payload)
        
        # Should contain p_old (ID 5) because we are now ID 6
        # Should NOT contain p_new (ID 6)
        self.assertEqual(len(self.mock_app.appData.serverPackets), 1)
        self.assertEqual(self.mock_app.appData.serverPackets[0].player_id, 5)

    def test_reset(self):
        self.dispatcher.my_id = 10
        self.dispatcher.reset()
        self.assertIsNone(self.dispatcher.my_id)

if __name__ == "__main__":
    unittest.main()
