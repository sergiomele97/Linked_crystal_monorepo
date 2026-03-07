import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import threading
import time

# Set up paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock Kivy platform
import kivy.utils
kivy.utils.platform = 'linux'

# Mock EVERYTHING that is not available
sys.modules['jnius'] = MagicMock()
sys.modules['sounddevice'] = MagicMock()
mock_np = MagicMock()
sys.modules['numpy'] = mock_np

# Custom mock for audio chunks to satisfy numpy-like access
class MockChunk:
    def __init__(self, data, channels=2):
        self.data = data
        self.ndim = 2 if channels > 1 else 1
        self.shape = (len(data) // channels, channels) if channels > 1 else (len(data),)
        self.dtype = "int16" # To skip normalization logic in test
    def __len__(self):
        return self.shape[0] if self.ndim == 2 else len(self.data)
    def tobytes(self):
        return bytes(self.data)
    def __getitem__(self, key):
        return self # Simple slice mock

# Mock ndarray as a list-like enough for popleft/append
mock_np.asarray = lambda x: x
mock_np.concatenate = lambda x: MockChunk(b"".join([i.tobytes() for i in x]))
mock_np.int16 = "int16"

from services.audio.audio_manager import AudioManagerKivy

class TestAudioManagerLogic(unittest.TestCase):
    def setUp(self):
        self.pyboy = MagicMock()
        # Ensure we don't accidentally call android init in constructor
        with patch('services.audio.audio_manager.platform', 'linux'):
            self.manager = AudioManagerKivy(self.pyboy)
        
        self.manager.sample_rate = 44100
        self.manager._channels = 2
        self.manager.platform = 'android'

    def test_condition_and_batching(self):
        # 1. Simulate enqueuing 3 small chunks
        chunk1 = MockChunk([0] * 200, channels=2) # 100 samples per channel
        chunk2 = MockChunk([1] * 200, channels=2)
        chunk3 = MockChunk([2] * 200, channels=2)
        
        self.manager.play_audio_buffer(chunk1, 44100)
        self.manager.play_audio_buffer(chunk2, 44100)
        self.manager.play_audio_buffer(chunk3, 44100)
        
        self.assertEqual(len(self.manager._playback_buffer), 3)

        # 2. Simulate the writer loop consumption (logic part)
        self.manager.android_audio_initialized = True
        
        chunks_to_write = []
        with self.manager._buffer_lock:
            # Should not wait
            max_samples = self.manager.sample_rate // 25
            current_samples = 0
            while self.manager._playback_buffer and current_samples < max_samples:
                c = self.manager._playback_buffer.popleft()
                chunks_to_write.append(c)
                current_samples += len(c)
        
        # All 3 chunks should be batched (total 300 samples < ~1764 max_samples)
        self.assertEqual(len(chunks_to_write), 3)
        self.assertEqual(len(self.manager._playback_buffer), 0)

    def test_stop_wakes_up_thread(self):
        self.manager.android_audio_initialized = True
        self.manager.audio_track = MagicMock()
        
        # Simulate a thread waiting
        reached_wait = threading.Event()
        def wait_func():
            with self.manager._buffer_lock:
                reached_wait.set()
                while not self.manager._playback_buffer and self.manager.android_audio_initialized:
                    self.manager._buffer_lock.wait(timeout=2)
        
        t = threading.Thread(target=wait_func)
        t.start()
        
        reached_wait.wait(timeout=1)
        time.sleep(0.1)
        self.assertTrue(t.is_alive())
        
        # Stop should notify and close the loop
        self.manager.stop()
        t.join(timeout=1)
        self.assertFalse(t.is_alive())

if __name__ == '__main__':
    unittest.main()
