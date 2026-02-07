
# import unittest
# from unittest.mock import MagicMock, patch
# import sys
# import os

# # Configure Kivy for headless testing
# os.environ['KIVY_NO_CONSOLELOG'] = '1'
# os.environ['KIVY_NO_ARGS'] = '1'

# # Add src to path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# import kivy.lang
# # Global patch for Builder.load_file
# patch('kivy.lang.Builder.load_file').start()

# from kivy.config import Config
# Config.set('graphics', 'backend', 'headless')

# from screens.emulator_screen.emulator_screen import EmulatorScreen

# class TestEmulatorTools(unittest.TestCase):
#     def setUp(self):
#         self.patchers = [
#             patch('screens.emulator_screen.emulator_screen.ChatManager'),
#             patch('screens.emulator_screen.emulator_screen.DebugLogManager'),
#             patch('screens.emulator_screen.emulator_screen.EmulatorCoreInterface'),
#             patch('kivy.app.App.get_running_app'),
#             patch('screens.emulator_screen.emulator_screen.ChatInterface')
#         ]
        
#         self.mocks = [p.start() for p in self.patchers]
#         self.mock_chat_mgr = self.mocks[0]
#         self.mock_log_mgr = self.mocks[1]
#         self.mock_emu_core = self.mocks[2]
#         self.mock_get_app = self.mocks[3]
#         self.mock_chat_ui = self.mocks[4]
        
#         self.mock_app = MagicMock()
#         self.mock_get_app.return_value = self.mock_app
#         self.mock_app.connection_manager = MagicMock()
        
#         self.screen = EmulatorScreen()
#         self.screen.ids = MagicMock()
#         self.screen.ids.video_display = MagicMock()
#         self.screen.ids.control_pad = MagicMock()
#         self.screen.ids.link_stats_panel = MagicMock()
#         self.screen.ids.link_tx_label = MagicMock()
#         self.screen.ids.link_status_dot = MagicMock()

#     def tearDown(self):
#         for p in self.patchers:
#             p.stop()

#     def test_on_enter_initialization(self):
#         self.screen.on_enter()
#         self.mock_chat_mgr.assert_called()
#         self.mock_log_mgr.assert_called()
#         self.mock_emu_core.assert_called()
#         self.screen.emulator.start.assert_called()
#         self.mock_app.connection_manager.set_chat_manager.assert_called_with(self.screen.chat_manager)

#     def test_update_link_stats_waiting(self):
#         self.screen.on_enter()
#         self.screen.emulator.get_link_status.return_value = {
#             "connected": True, "tx": 5, "bridged": False
#         }
#         self.screen.update_link_stats(0)
#         self.assertEqual(self.screen.ids.link_stats_panel.opacity, 1)
#         self.assertEqual(self.screen.ids.link_status_dot.text, "Waiting...")
#         self.assertEqual(self.screen.ids.link_tx_label.text, "Packets: 5")

#     def test_update_link_stats_linked(self):
#         self.screen.on_enter()
#         self.screen.emulator.get_link_status.return_value = {
#             "connected": True, "tx": 10, "bridged": True
#         }
#         self.screen.update_link_stats(0)
#         self.assertEqual(self.screen.ids.link_status_dot.text, "Linked!")
#         self.assertEqual(self.screen.ids.link_status_dot.color, (0, 1, 0, 1))

#     def test_open_chat(self):
#         self.screen.onChatPressed()
#         self.mock_chat_ui.assert_called_with(father_screen=self.screen)
#         self.mock_chat_ui.return_value.mostrar_chat.assert_called()

# if __name__ == "__main__":
#     unittest.main()
