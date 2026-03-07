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

try:
    from screens.emulator_screen.components.controlpad import ControlPad
    from services.emulator.emulator_core_interface import EmulatorCoreInterface
except Exception as e:
    print(f"FAILED TO IMPORT IN DISCOVERY: {e}")
    import traceback
    traceback.print_exc()
    raise

class TestGamepadInput(unittest.TestCase):
    def setUp(self):
        # Mocking App.get_running_app() for any potential calls
        self.mock_app = MagicMock()
        self.patcher_app = patch('kivy.app.App.get_running_app', return_value=self.mock_app)
        self.patcher_app.start()

    def tearDown(self):
        patch.stopall()

    def test_controlpad_callbacks(self):
        """Verify that ControlPad triggers the assigned callbacks when buttons are pressed/released."""
        cp = ControlPad()
        mock_press = MagicMock()
        mock_release = MagicMock()
        
        cp.on_button_press = mock_press
        cp.on_button_release = mock_release
        
        # Test press
        cp.press("up")
        mock_press.assert_called_once_with("up")
        self.assertIn("up", cp._pressed_buttons)
        
        # Test duplicate press (should not trigger again)
        cp.press("up")
        mock_press.assert_called_once()
        
        # Test release
        cp.release("up")
        mock_release.assert_called_once_with("up")
        self.assertNotIn("up", cp._pressed_buttons)
        
        # Test release of non-pressed button (should not trigger)
        cp.release("up")
        mock_release.assert_called_once()

    def test_emulator_interface_input(self):
        """Verify that EmulatorCoreInterface correctly forwards inputs to PyBoy."""
        interface = EmulatorCoreInterface()
        interface.pyboy = MagicMock()
        
        # Test press
        interface.send_input_press("a")
        interface.pyboy.button_press.assert_called_once_with("a")
        
        # Test release
        interface.send_input_release("a")
        interface.pyboy.button_release.assert_called_once_with("a")

    def test_integration_pad_to_interface(self):
        """Verify the flow from ControlPad to EmulatorCoreInterface as configured in EmulatorScreen."""
        interface = EmulatorCoreInterface()
        interface.pyboy = MagicMock()
        
        cp = ControlPad()
        # Simulate local mapping in EmulatorScreen
        cp.on_button_press = interface.send_input_press
        cp.on_button_release = interface.send_input_release
        
        # Press "start"
        cp.press("start")
        interface.pyboy.button_press.assert_called_once_with("start")
        
        # Release "start"
        cp.release("start")
        interface.pyboy.button_release.assert_called_once_with("start")

if __name__ == "__main__":
    unittest.main()
