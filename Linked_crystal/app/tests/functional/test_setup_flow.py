import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Configure Kivy 
os.environ['KIVY_NO_CONSOLELOG'] = '1'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import kivy.lang
with patch('kivy.lang.Builder.load_file'):
    from screens.menu_screen.menu_screen import MenuScreen

class TestSetupFlow(unittest.TestCase):
    def setUp(self):
        self.mock_app = MagicMock()
        self.mock_app.appData = MagicMock()
        self.mock_app.appData.romPath = ""
        self.mock_app.connection_manager = MagicMock()
        
        self.app_patcher = patch('kivy.app.App.get_running_app', return_value=self.mock_app)
        self.app_patcher.start()

        with patch('kivy.lang.Builder.load_file'):
            self.screen = MenuScreen()
            
        self.screen.ids = MagicMock()
        self.screen.ids.label_rom = MagicMock()
        self.screen.ids.label_rom.text = ""
        # Añadido para evitar AttributeError en iniciar_juego
        self.screen.ids.output_label = MagicMock()
        self.screen.ids.output_label.text = ""
        
        self.screen.on_pre_enter()

    def tearDown(self):
        self.app_patcher.stop()

    def test_rom_selection_flow(self):
        with patch('screens.menu_screen.menu_screen.select_rom') as mock_select_rom:
            self.screen.abrir_explorador()
            args, _ = mock_select_rom.call_args
            callback = args[1]
            callback("/path/game.gbc")
            
            self.assertEqual(self.mock_app.appData.romPath, "/path/game.gbc")
            self.assertTrue(self.screen.rom_cargado)
            self.assertEqual(self.screen.ids.label_rom.text, "ROM seleccionada:\ngame.gbc")

    def test_server_selection_flow(self):
        self.screen.elegir_servidor()
        self.mock_app.connection_manager.getServerListAndSelect.assert_called_with(self.screen)
        self.screen.servidor_elegido = True
        self.assertTrue(self.screen.servidor_elegido)

    def test_play_transition(self):
        self.screen.manager = MagicMock()
        self.screen.iniciar_juego()
        self.assertEqual(self.screen.manager.current, 'emulator')

if __name__ == "__main__":
    unittest.main()