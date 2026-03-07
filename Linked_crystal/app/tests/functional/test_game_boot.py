import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

print("DEBUG: Script started")
# Re-enable Kivy logging to see what's happening
# os.environ['KIVY_NO_CONSOLELOG'] = '1'
os.environ['KIVY_NO_ARGS'] = '1'

print("DEBUG: Setting up sys.path")
# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

print("DEBUG: Importing Kivy Config")
from kivy.config import Config
Config.set('graphics', 'backend', 'headless')

print("DEBUG: Importing local modules")
try:
    from services.emulator.emulator_core_interface import EmulatorCoreInterface
    from models.appData import appData
    print("DEBUG: Imports successful")
except Exception as e:
    print(f"DEBUG: Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class TestGameBoot(unittest.TestCase):
    def setUp(self):
        # Path to Pandora ROM relative to this test file
        self.rom_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/resources/rom/PandorasBlocks.GBC'))
        
        # Mocking App.get_running_app()
        self.mock_app = MagicMock()
        self.mock_app.appData = appData()
        self.mock_app.appData.romPath = self.rom_path
        
        self.patcher_app = patch('kivy.app.App.get_running_app', return_value=self.mock_app)
        self.patcher_app.start()
        
        # Mocking permissions to avoid Android-specific code
        self.patcher_perms = patch('services.emulator.emulator_core_interface.solicitar_permisos')
        self.patcher_perms.start()
        
        # Mocking SpriteRenderer to avoid FileNotFoundError: resources/image/OW_default_sprite.png
        self.patcher_sprite = patch('services.drawing.drawing_manager.SpriteRenderer')
        self.mock_sprite_class = self.patcher_sprite.start()
        self.mock_sprite_instance = MagicMock()
        self.mock_sprite_class.return_value = self.mock_sprite_instance

    def tearDown(self):
        patch.stopall()

    def test_emulator_initialization(self):
        """Test that EmulatorCoreInterface correctly initializes PyBoy and the loop."""
        print("DEBUG: Starting test_emulator_initialization")
        # Callbacks
        mock_on_frame = MagicMock()
        mock_on_text = MagicMock()
        
        # Create interface
        print("DEBUG: Creating EmulatorCoreInterface")
        interface = EmulatorCoreInterface(on_frame=mock_on_frame, on_text_output=mock_on_text)
        
        # Start initialization (it runs in a thread)
        print("DEBUG: Calling interface.start()")
        interface.start()
        
        # Wait for initialization (max 10 seconds)
        max_wait = 10
        start_time = time.time()
        success = False
        print("DEBUG: Waiting for initialization...")
        while time.time() - start_time < max_wait:
            if interface.pyboy is not None and interface.loop is not None and interface.loop.running:
                print(f"DEBUG: Initialization succeeded after {time.time() - start_time:.2f}s")
                success = True
                break
            time.sleep(0.5)
            
        if not success:
            print("DEBUG: Initialization timed out or failed")
            if interface.pyboy is None: print("DEBUG: interface.pyboy is None")
            if interface.loop is None: print("DEBUG: interface.loop is None")
            elif not interface.loop.running: print("DEBUG: interface.loop is not running")

        # Assertions
        self.assertTrue(success, "Initialization timed out")
        self.assertIsNotNone(interface.pyboy, "PyBoy should be initialized")
        self.assertIsNotNone(interface.loop, "EmulationLoop should be initialized")
        self.assertTrue(interface.loop.running, "EmulationLoop should be running")
        
        # Clean up
        if interface.loop:
            interface.loop.stop()

if __name__ == "__main__":
    print("DEBUG: Running unittest.main()")
    try:
        unittest.main()
    except Exception as e:
        print(f"DEBUG: unittest.main() failed: {e}")
        import traceback
        traceback.print_exc()
