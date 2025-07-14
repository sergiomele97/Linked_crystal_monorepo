from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.properties import StringProperty
from kivy.utils import platform
from kivy.lang import Builder

from pyboy import PyBoy
import threading
import time
import os
from io import BytesIO
import numpy as np

from screens.emulator_screen.components.audio_manager import AudioManagerKivy
from screens.emulator_screen.components.environment_manager import solicitar_permisos
from screens.emulator_screen.components.controlpad import ControlPad

class ImageButton(ButtonBehavior, Image):
    pass

Builder.load_file("screens/emulator_screen/emulator_screen.kv")
Builder.load_file("screens/emulator_screen/components/controlpad.kv")


class EmulatorScreen(Screen):
    rom_path = StringProperty("")

    def on_enter(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.image_widget = self.ids.image_widget
        self.label = self.ids.label
        self.example_button = self.ids.example_button
        self.controlpad = self.ids.control_pad

        self.example_button.bind(on_press=self.on_example_button)

        self.controlpad.on_button_press = self.on_button_press
        self.controlpad.on_button_release = self.on_button_release

        self.audio_manager = AudioManagerKivy()

        threading.Thread(target=self._run_pyboy_thread, daemon=True).start()

    def on_example_button(self, instance):
        self.label.text = "Botón presionado"

    def on_button_press(self, button_name):
        if hasattr(self, 'pyboy'):
            #self.pyboy.send_input(button_name, True)
            print("boton presionado")
            pass

    def on_button_release(self, button_name):
        if hasattr(self, 'pyboy'):
            #self.pyboy.send_input(button_name, False)
            pass

    def update_label(self, ticks):
        self.label.text = f'PyBoy\nTicks ejecutados: {ticks}'

    def capture_image(self, pyboy):
        image = pyboy.screen.image
        with BytesIO() as byte_io:
            image.save(byte_io, format='PNG')
            byte_io.seek(0)
            kivy_image = CoreImage(byte_io, ext="png")
        self.image_widget.texture = kivy_image.texture

    def play_audio_buffer(self, audio_array, sample_rate):
        self.audio_manager.play_audio_buffer(audio_array, sample_rate)

    def _run_pyboy_thread(self):
        solicitar_permisos()
        rom_path = self.rom_path

        if not os.path.exists(rom_path):
            Clock.schedule_once(lambda dt: setattr(self.label, 'text', "ROM no encontrada"), 0)
            return

        try:
            self.pyboy = PyBoy(rom_path, window="null", sound_emulated=True, sound_volume=100)
            self.pyboy.set_emulation_speed(1)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.label, 'text', f"Error al cargar ROM: {e}"), 0)
            return

        ticks = 0
        last_time = time.time()

        def emular(dt):
            nonlocal ticks, last_time
            if self.pyboy.tick():
                ticks += 1
                Clock.schedule_once(lambda dt: self.capture_image(self.pyboy), 0)

                valid_length = self.pyboy.sound.raw_buffer_head
                if valid_length > 0:
                    audio_buffer = self.pyboy.sound.ndarray[:valid_length]
                    self.play_audio_buffer(audio_buffer, self.pyboy.sound.sample_rate)

                if time.time() - last_time >= 1:
                    Clock.schedule_once(lambda dt, t=ticks: self.update_label(t), 0)
                    last_time = time.time()
            else:
                self.pyboy.stop(save=False)
                Clock.schedule_once(lambda dt: setattr(self.label, 'text', "Emulación finalizada"), 0)

        Clock.schedule_interval(emular, 1 / 60)
