from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.properties import StringProperty
from kivy.utils import platform

from pyboy import PyBoy
import threading
import time
import os
from io import BytesIO
import numpy as np

if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast

    def solicitar_permisos():
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])

    AudioTrack = autoclass("android.media.AudioTrack")
    AudioFormat = autoclass("android.media.AudioFormat")
    AudioManager = autoclass("android.media.AudioManager")
else:
    import sounddevice as sd

    def solicitar_permisos():
        pass


class EmuladorScreen(Screen):
    rom_path = StringProperty("")

    def on_enter(self):
        if hasattr(self, 'layout'):
            return

        self.layout = BoxLayout(orientation='vertical')
        self.image_widget = Image(size_hint=(1, 0.5), allow_stretch=True, keep_ratio=True)
        self.label = Label(text='Iniciando PyBoy…', size_hint=(1, 0.5))

        self.layout.add_widget(self.image_widget)
        self.layout.add_widget(self.label)
        self.add_widget(self.layout)

        self.audio_buffer = None
        self.audio_stream = None
        self.audio_track = None
        self.android_audio_initialized = False

        threading.Thread(target=self.run_pyboy, daemon=True).start()

    def update_label(self, ticks):
        self.label.text = f'PyBoy\nTicks ejecutados: {ticks}'

    def capture_image(self, pyboy):
        image = pyboy.screen.image
        with BytesIO() as byte_io:
            image.save(byte_io, format='PNG')
            byte_io.seek(0)
            kivy_image = CoreImage(byte_io, ext="png")
        self.image_widget.texture = kivy_image.texture

    def init_audio_stream(self, sample_rate, channels):
        if platform == 'android':
            channel_config = AudioFormat.CHANNEL_OUT_MONO if channels == 1 else AudioFormat.CHANNEL_OUT_STEREO
            encoding = AudioFormat.ENCODING_PCM_16BIT
            buffer_size = AudioTrack.getMinBufferSize(sample_rate, channel_config, encoding)

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
        else:
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
        if (platform == 'android' and not self.android_audio_initialized) or (platform != 'android' and self.audio_stream is None):
            self.init_audio_stream(sample_rate, channels)

        audio_float = audio_array.astype(np.float32)
        for ch in range(audio_float.shape[1]):
            center = (audio_float[:, ch].max() + audio_float[:, ch].min()) / 2
            audio_float[:, ch] -= center

        max_abs = np.max(np.abs(audio_float), axis=0)
        max_abs[max_abs == 0] = 1
        audio_norm = audio_float / max_abs
        audio_int16 = (audio_norm * 32767).astype(np.int16)

        if platform == 'android':
            if audio_int16.ndim == 2:
                audio_int16 = audio_int16.flatten()
            audio_bytes = audio_int16.tobytes()
            self.audio_track.write(audio_bytes, 0, len(audio_bytes))
        else:
            self.audio_buffer = np.concatenate((self.audio_buffer, audio_int16))

    def run_pyboy(self):
        solicitar_permisos()
        rom_path = self.rom_path

        if not os.path.exists(rom_path):
            print(f"[ERROR] ROM no encontrada: {rom_path}")
            Clock.schedule_once(lambda dt: setattr(self.label, 'text', "No se puede acceder al archivo ROM."), 0)
            return

        try:
            pyboy = PyBoy(rom_path, window="null", sound_emulated=True, sound_volume=100)
            pyboy.set_emulation_speed(1)
        except Exception as e:
            print(f"[ERROR] PyBoy no pudo cargar el ROM: {e}")
            Clock.schedule_once(lambda dt: setattr(self.label, 'text', "Error al cargar el ROM."), 0)
            return

        print(f"[INFO] ROM cargada desde: {rom_path}")

        ticks = 0
        last_time = time.time()

        def emular(dt):
            nonlocal ticks, last_time
            if pyboy.tick():
                ticks += 1
                Clock.schedule_once(lambda dt: self.capture_image(pyboy), 0)

                valid_length = pyboy.sound.raw_buffer_head
                if valid_length > 0:
                    audio_buffer = pyboy.sound.ndarray[:valid_length]
                    sample_rate = pyboy.sound.sample_rate
                    self.play_audio_buffer(audio_buffer, sample_rate)

                current_time = time.time()
                if current_time - last_time >= 1:
                    Clock.schedule_once(lambda dt, t=ticks: self.update_label(t), 0)
                    last_time = current_time
            else:
                pyboy.stop(save=False)
                print("[PyBoy] Emulación finalizada")
                Clock.schedule_once(lambda dt: setattr(self.label, 'text', "Emulación finalizada"), 0)

        Clock.schedule_interval(emular, 1 / 60)
        Clock.schedule_once(lambda dt: self.capture_image(pyboy), 5)
