import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock sounddevice BEFORE importing audio_manager
sys.modules['sounddevice'] = MagicMock()

from services.audio.audio_manager import AudioManagerKivy

class TestAudioManager(unittest.TestCase):
    def setUp(self):
        self.mock_pyboy = MagicMock()
        # Mocking platform to be 'linux' for desktop testing
        with patch('services.audio.audio_manager.platform', 'linux'):
            self.manager = AudioManagerKivy(self.mock_pyboy)

    def tearDown(self):
        self.manager.stop()
        patch.stopall()

    def test_play_audio_buffer_int16_no_normalizing(self):
        """Verify that int16 buffers are stored without changes."""
        # Create a stereo int16 buffer
        data = np.array([[10, 10], [20, 20]], dtype=np.int16)
        
        with patch.object(self.manager, 'init_audio_stream') as mock_init:
            self.manager.play_audio_buffer(data, 44100)
            
            # Should have queued one chunk
            self.assertEqual(len(self.manager._playback_buffer), 1)
            queued = self.manager._playback_buffer[0]
            
            # Values should be exactly the same
            np.testing.assert_array_equal(queued, data)
            self.assertEqual(queued.dtype, np.int16)
            
            # Initialized once
            mock_init.assert_called_once_with(44100, 2)

    def test_play_audio_buffer_float_normalization(self):
        """Verify that float buffers are normalized and converted to int16."""
        # Float data between -1.0 and 1.0
        data = np.array([0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        
        with patch.object(self.manager, 'init_audio_stream'):
            self.manager.play_audio_buffer(data, 44100)
            
            queued = self.manager._playback_buffer[0]
            self.assertEqual(queued.dtype, np.int16)
            
            # 1.0 should be ~32767, -1.0 should be ~-32768
            # Taking into account the smoothed peak calculation
            self.assertGreater(queued.max(), 30000)
            self.assertLess(queued.min(), -30000)

    def test_desktop_callback_logic(self):
        """Verify that the callback correctly consumes data from the buffer."""
        # 4 frames of stereo data
        chunk = np.array([[1, 1], [2, 2], [3, 3], [4, 4]], dtype=np.int16)
        self.manager._playback_buffer.append(chunk)
        self.manager._channels = 2
        
        # Prepare output buffer (size 2 frames)
        outdata = np.zeros((2, 2), dtype=np.int16)
        
        # Call the callback
        self.manager._desktop_callback(outdata, frames=2, time_info=None, status=None)
        
        # Output should have first 2 frames
        np.testing.assert_array_equal(outdata, chunk[:2])
        
        # Next 2 frames should still be in playback_buffer[0]
        self.assertEqual(len(self.manager._playback_buffer), 1)
        np.testing.assert_array_equal(self.manager._playback_buffer[0], chunk[2:])

    def test_stop_cleanup(self):
        """Verify that stop cleans up streams."""
        mock_stream = MagicMock()
        self.manager.audio_stream = mock_stream
        self.manager.stop()
        
        mock_stream.stop.assert_called()
        mock_stream.close.assert_called()
        self.assertIsNone(self.manager.audio_stream)

if __name__ == "__main__":
    unittest.main()
