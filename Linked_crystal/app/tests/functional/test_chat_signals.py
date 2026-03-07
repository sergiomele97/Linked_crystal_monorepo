import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Configure Kivy for headless testing
# os.environ['KIVY_NO_CONSOLELOG'] = '1'
os.environ['KIVY_NO_ARGS'] = '1'

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from kivy.config import Config
Config.set('graphics', 'backend', 'headless')

from services.chat.chat_manager import ChatManager
from screens.emulator_screen.components.chat_interface import ChatInterface

class TestChatSignals(unittest.TestCase):
    def setUp(self):
        # Mocking App.get_running_app()
        self.mock_app = MagicMock()
        self.patcher_app = patch('kivy.app.App.get_running_app', return_value=self.mock_app)
        self.patcher_app.start()
        
        # Connection Manager Mock
        self.mock_conn_mgr = MagicMock()
        self.mock_app.connection_manager = self.mock_conn_mgr
        
        self.chat_mgr = ChatManager()

    def tearDown(self):
        patch.stopall()

    def test_receive_message_logic(self):
        """Verify that receiving a message updates the messages list."""
        self.chat_mgr.receive_message(sender_id=5, text="Hola mundo")
        
        self.assertEqual(len(self.chat_mgr.messages), 1)
        self.assertEqual(self.chat_mgr.messages[0]['sender'], "Jugador 5")
        self.assertEqual(self.chat_mgr.messages[0]['text'], "Hola mundo")

    def test_send_message_logic(self):
        """Verify that sending a message calls the connection manager."""
        self.chat_mgr.send_message("Mensaje de prueba")
        
        # Check internal state
        self.assertEqual(len(self.chat_mgr.messages), 1)
        self.assertEqual(self.chat_mgr.messages[0]['sender'], "Tú")
        
        # Check network call
        self.mock_conn_mgr.connectionLoop.send_chat.assert_called_once_with("Mensaje de prueba")

    def test_send_empty_message(self):
        """Verify that empty messages are not sent."""
        self.chat_mgr.send_message("   ")
        self.assertEqual(len(self.chat_mgr.messages), 0)
        self.mock_conn_mgr.connectionLoop.send_chat.assert_not_called()

    def test_chat_interface_display(self):
        """Verify that ChatInterface initializes and shows the ChatView."""
        mock_father = MagicMock()
        mock_father.chat_manager = self.chat_mgr
        
        interface = ChatInterface(father_screen=mock_father)
        
        with patch('screens.emulator_screen.components.chat_interface.ChatView') as mock_view_class:
            mock_view = MagicMock()
            mock_view_class.return_value = mock_view
            
            interface.mostrar_chat()
            
            mock_view_class.assert_called_once()
            mock_view.set_chat_manager.assert_called_once_with(self.chat_mgr)
            mock_view.open.assert_called_once()

if __name__ == "__main__":
    unittest.main()
