import numpy as np
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass
    AudioTrack = autoclass("android.media.AudioTrack")
    AudioFormat = autoclass("android.media.AudioFormat")
    AudioManager = autoclass("android.media.AudioManager")
else:
    import sounddevice as sd


class AudioManagerKivy:
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.platform = platform
        self.audio_buffer = None
        self.audio_stream = None
        self.audio_track = None
        self.android_audio_initialized = False
        self._channels = 2 
    
    def update_audio(self):
        audio_len = self.pyboy.sound.raw_buffer_head
        if audio_len > 0:
            audio_buffer = self.pyboy.sound.ndarray[:audio_len]
            sample_rate = self.pyboy.sound.sample_rate
            self.play_audio_buffer(audio_buffer, sample_rate)

    def init_audio_stream(self, sample_rate, channels):
        self._channels = channels
        if self.platform == 'android':
            self._init_android_audio(sample_rate, channels)
        else:
            self._init_desktop_audio(sample_rate, channels)

    def _init_android_audio(self, sample_rate, channels):
        channel_config = (
            AudioFormat.CHANNEL_OUT_MONO if channels == 1 else AudioFormat.CHANNEL_OUT_STEREO
        )
        encoding = AudioFormat.ENCODING_PCM_16BIT
        buffer_size = AudioTrack.getMinBufferSize(sample_rate, channel_config, encoding)

        if buffer_size <= 0:
            buffer_size = max(sample_rate * channels // 8, 4096)

        self.audio_track = AudioTrack(
            AudioManager.STREAM_MUSIC,
            sample_rate,
            channel_config,
            encoding,
            buffer_size,
            AudioTrack.MODE_STREAM
        )
        self.audio_track.play()
        self.android_audio_initialized = True

    def _init_desktop_audio(self, sample_rate, channels):
        self.audio_buffer = np.empty((0, channels), dtype=np.int16)
        self.audio_stream = sd.OutputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype='int16',
            callback=self.audio_callback,
            finished_callback=lambda: print("[Audio] Stream terminado")
        )
        self.audio_stream.start()

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print(f'[Audio Callback Status] {status}')

        if len(self.audio_buffer) >= frames:
            outdata[:] = self.audio_buffer[:frames]
            self.audio_buffer = self.audio_buffer[frames:]
        else:
            needed = frames - len(self.audio_buffer)
            outdata[:len(self.audio_buffer)] = self.audio_buffer
            outdata[len(self.audio_buffer):] = np.zeros((needed, outdata.shape[1]), dtype=np.int16)
            self.audio_buffer = np.empty((0, outdata.shape[1]), dtype=np.int16)

    def play_audio_buffer(self, audio_array, sample_rate):
        if audio_array is None or len(audio_array) == 0:
            return

        channels = 1 if audio_array.ndim == 1 else audio_array.shape[1]

        # Inicializar audio si no está listo
        if (self.platform == 'android' and not self.android_audio_initialized) or \
        (self.platform != 'android' and self.audio_stream is None):
            self.init_audio_stream(sample_rate, channels)

        # --- Normalization ---
        audio_float = audio_array.astype(np.float32)

        if audio_float.ndim == 1: 
            audio_float -= (audio_float.max() + audio_float.min()) / 2
        else: 
            for ch in range(audio_float.shape[1]):
                center = (audio_float[:, ch].max() + audio_float[:, ch].min()) / 2
                audio_float[:, ch] -= center

        max_abs = np.max(np.abs(audio_float))
        if max_abs == 0:
            max_abs = 1.0
        audio_norm = audio_float / max_abs
        audio_int16 = (audio_norm * 32767).astype(np.int16)

        # --- Android ---
        if self.platform == 'android':
            if audio_int16.ndim == 2:
                audio_int16 = audio_int16.flatten()
            audio_bytes = audio_int16.tobytes()
            self.audio_track.write(audio_bytes, 0, len(audio_bytes))

        # --- Desktop ---
        else:
            if audio_int16.ndim == 1:
                audio_int16 = audio_int16[:, np.newaxis]
            self.audio_buffer = np.concatenate((self.audio_buffer, audio_int16))
