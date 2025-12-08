import threading
import numpy as np
import collections
import time
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass
    AudioTrack = autoclass("android.media.AudioTrack")
    AudioFormat = autoclass("android.media.AudioFormat")
    AudioManager = autoclass("android.media.AudioManager")
else:
    import sounddevice as sd


class AudioManagerKivy:
    """AudioManager seguro y eficiente para PyBoy + Kivy."""
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.platform = platform

        self._channels = 2
        self.sample_rate = None

        self._playback_buffer = collections.deque()
        self._buffer_lock = threading.Lock()

        # Desktop
        self.audio_stream = None

        # Android
        self.audio_track = None
        self.android_audio_initialized = False
        self._android_writer_thread = None

        self._running = True

    # -------------------------
    # API compatible
    # -------------------------
    def update_audio(self):
        """Lee audio de PyBoy y encola para reproducción."""
        try:
            audio_len = getattr(self.pyboy.sound, "raw_buffer_head", 0)
            if audio_len <= 0:
                return
            audio_buffer = self.pyboy.sound.ndarray[:audio_len]
            sample_rate = getattr(self.pyboy.sound, "sample_rate", None)
            if sample_rate:
                self.play_audio_buffer(audio_buffer, sample_rate)
        except Exception:
            pass  # nunca rompe el loop

    def play_audio_buffer(self, audio_array, sample_rate):
        """Encola audio; normaliza solo si no es int16."""
        if audio_array is None or len(audio_array) == 0:
            return

        arr = np.asarray(audio_array)
        channels = 1 if arr.ndim == 1 else arr.shape[1]

        # Init audio si es necesario o si cambian sample_rate / channels
        need_init = (self.platform != 'android' and self.audio_stream is None) or \
                    (self.platform == 'android' and (not self.android_audio_initialized or
                                                    self.sample_rate != sample_rate or
                                                    self._channels != channels))
        if need_init:
            self.init_audio_stream(sample_rate, channels)

        # Normalización solo si no es int16
        if arr.dtype != np.int16:
            arr = arr.astype(np.float32)
            if arr.ndim == 1:
                arr -= (arr.max() + arr.min()) / 2
            else:
                for ch in range(arr.shape[1]):
                    arr[:, ch] -= (arr[:, ch].max() + arr[:, ch].min()) / 2
            max_abs = np.max(np.abs(arr)) or 1.0
            arr = (arr / max_abs * 32767).astype(np.int16)

        # Desktop shape
        if self.platform != 'android' and arr.ndim == 1:
            arr = arr[:, np.newaxis]

        # Encolar
        with self._buffer_lock:
            self._playback_buffer.append(arr)

    # -------------------------
    # Inicialización de streams
    # -------------------------
    def init_audio_stream(self, sample_rate, channels):
        self.sample_rate = int(sample_rate)
        self._channels = channels
        if self.platform == 'android':
            self._init_android_audio(self.sample_rate, channels)
        else:
            self._init_desktop_audio(self.sample_rate, channels)

    # -------------------------
    # Desktop
    # -------------------------
    def _init_desktop_audio(self, sample_rate, channels=2):
        if self.audio_stream:
            try: self.audio_stream.stop(); self.audio_stream.close()
            except: pass
        self.audio_stream = sd.OutputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype='int16',
            callback=self._desktop_callback,
            latency='low'
        )
        self.audio_stream.start()

    def _desktop_callback(self, outdata, frames, time_info, status):
        out = np.zeros((frames, self._channels), dtype=np.int16)
        needed = frames
        with self._buffer_lock:
            dst = 0
            while needed > 0 and self._playback_buffer:
                chunk = self._playback_buffer[0]
                take = min(needed, chunk.shape[0])
                nch = chunk.shape[1]
                out[dst:dst+take, :nch] = chunk[:take]
                if take == chunk.shape[0]:
                    self._playback_buffer.popleft()
                else:
                    self._playback_buffer[0] = chunk[take:]
                dst += take
                needed -= take
        if out.shape[1] != self._channels:
            if out.shape[1] == 1: out = np.repeat(out, 2, axis=1)
            else:
                tmp = np.zeros((frames, self._channels), dtype=np.int16)
                tmp[:, :min(out.shape[1], self._channels)] = out[:, :min(out.shape[1], self._channels)]
                out = tmp
        try: outdata[:] = out
        except: pass

    # -------------------------
    # Android
    # -------------------------
    def _init_android_audio(self, sample_rate, channels):
        try:
            if self.android_audio_initialized and self.audio_track: return

            channel_config = AudioFormat.CHANNEL_OUT_MONO if channels == 1 else AudioFormat.CHANNEL_OUT_STEREO
            encoding = AudioFormat.ENCODING_PCM_16BIT
            try: min_buf = AudioTrack.getMinBufferSize(sample_rate, channel_config, encoding)
            except: min_buf = max(sample_rate * channels // 8, 4096)

            self.audio_track = AudioTrack(AudioManager.STREAM_MUSIC, sample_rate, channel_config,
                                          encoding, min_buf, AudioTrack.MODE_STREAM)
            self.audio_track.play()
            self.android_audio_initialized = True

            # Start writer thread
            if not self._android_writer_thread or not self._android_writer_thread.is_alive():
                self._android_writer_thread = threading.Thread(target=self._android_writer_loop, daemon=True)
                self._android_writer_thread.start()
        except Exception:
            self.audio_track = None
            self.android_audio_initialized = False

    def _android_writer_loop(self):
        while self.android_audio_initialized:
            chunk = None
            with self._buffer_lock:
                if self._playback_buffer:
                    chunk = self._playback_buffer.popleft()
            if chunk is None:
                time.sleep(0.005)
                continue
            try:
                self.audio_track.write(chunk.tobytes(), 0, len(chunk.tobytes()))
            except: time.sleep(0.01)

    # -------------------------
    # Cleanup
    # -------------------------
    def stop(self):
        self._running = False
        if self.audio_stream:
            try: self.audio_stream.stop(); self.audio_stream.close()
            except: pass
            self.audio_stream = None
        if self.audio_track:
            try: self.audio_track.stop(); self.audio_track.release()
            except: pass
            self.audio_track = None
            self.android_audio_initialized = False
