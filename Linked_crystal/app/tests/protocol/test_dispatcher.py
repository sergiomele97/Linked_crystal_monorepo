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

if __name__ == "__main__":
    unittest.main()
