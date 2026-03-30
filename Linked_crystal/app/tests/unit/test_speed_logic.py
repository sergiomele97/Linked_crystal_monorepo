import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.emulator.emulator_loop import EmulationLoop

class TestSpeedLogic(unittest.TestCase):
    def setUp(self):
        self.mock_pyboy = MagicMock()
        self.mock_app = MagicMock()
        self.mock_app.appData.ramData = MagicMock()
        self.mock_app.appData.packet = MagicMock()
        self.mock_app.appData.serverPackets = []
        
        # Patching AudioManagerKivy, RamScrapper, RamHooks, DrawingManager
        # because they are initialized in EmulationLoop.__init__
        self.patches = [
            patch('services.emulator.emulator_loop.AudioManagerKivy'),
            patch('services.emulator.emulator_loop.RamScrapper'),
            patch('services.emulator.emulator_loop.RamHooks'),
            patch('services.emulator.emulator_loop.DrawingManager'),
            patch('kivy.app.App.get_running_app', return_value=self.mock_app)
        ]
        for p in self.patches:
            p.start()
            
        self.loop = EmulationLoop(self.mock_pyboy)

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_set_speed(self):
        # Verify speed initialization and propagation
        self.assertEqual(self.loop.speed_multiplier, 1)
        self.assertEqual(self.loop.ramScrapper.speed, 1)
        
        self.loop.set_speed(2)
        self.assertEqual(self.loop.speed_multiplier, 2)
        self.assertEqual(self.loop.ramScrapper.speed, 2)

    def test_step_x1_speed(self):
        # When speed is x1:
        # - pyboy.tick() called once
        # - audioManager.update_audio() called once (no mute)
        # - drawingManager.update_frame(1) called once
        
        self.loop.speed_multiplier = 1
        self.loop.running = True
        self.mock_pyboy.tick.return_value = True
        
        self.loop._step(1/60)
        
        self.assertEqual(self.mock_pyboy.tick.call_count, 1)
        self.loop.audioManager.update_audio.assert_called_once_with()
        self.loop.drawingManager.update_frame.assert_called_once_with(1)

    def test_step_x2_speed(self):
        # When speed is x2:
        # - pyboy.tick() called twice
        # - audioManager.update_audio(mute=True) called once (first tick only)
        # - drawingManager.update_frame(2) called twice
        
        self.loop.speed_multiplier = 2
        self.loop.running = True
        self.mock_pyboy.tick.return_value = True
        
        self.loop._step(1/60)
        
        self.assertEqual(self.mock_pyboy.tick.call_count, 2)
        # Verify audio is updated with mute=True on the first tick (i=0)
        # and not called again on the second tick (i=1)
        self.loop.audioManager.update_audio.assert_called_once_with(mute=True)
        # Verify drawing manager is called twice with the correct speed
        self.assertEqual(self.loop.drawingManager.update_frame.call_count, 2)
        self.loop.drawingManager.update_frame.assert_called_with(2)

if __name__ == '__main__':
    unittest.main()
