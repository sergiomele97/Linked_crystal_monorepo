from pyboy import PyBoy
from kivy.clock import Clock
from kivy.utils import platform
import threading
import os

from screens.emulator_screen.components.environment_manager import solicitar_permisos


class EmulatorCoreInterface:
    def __init__(self, rom_path, on_frame=None, on_audio=None, on_text_output=None):
        self.rom_path = rom_path
        self.on_frame = on_frame
        self.on_text_output = on_text_output
        self.on_audio = on_audio
        self.pyboy = None

    def start(self):
        threading.Thread(target=self._initialize, daemon=True).start()

    def _initialize(self):
        solicitar_permisos()

        if not os.path.exists(self.rom_path):
            if self.on_text_output:
                Clock.schedule_once(lambda dt: self.on_text_output("ROM no encontrada"), 0)
            return

        try:
            self.pyboy = PyBoy(self.rom_path, window="null", sound_emulated=True, sound_volume=100)
            self.pyboy.set_emulation_speed(1)
        except Exception as e:
            if self.on_text_output:
                print(f"Error al cargar ROM: {e}")
            return

        Clock.schedule_interval(self._emulate, 1 / 60)

    def _emulate(self, dt):
        if not self.pyboy:
            return False

        if self.pyboy.tick():

            # Enviar frame
            if self.on_frame:
                Clock.schedule_once(lambda dt: self.on_frame(self.pyboy), 0)

            # Enviar audio
            audio_len = self.pyboy.sound.raw_buffer_head
            if audio_len > 0 and self.on_audio:
                audio_buffer = self.pyboy.sound.ndarray[:audio_len]
                sample_rate = self.pyboy.sound.sample_rate
                self.on_audio(audio_buffer, sample_rate)

        else:
            self.pyboy.stop()
            if self.on_text_output:
                Clock.schedule_once(lambda dt: self.on_text_output("Emulación finalizada"), 0)
            return False

    def send_input_press(self, button_name):
        if self.pyboy:
            self.pyboy.button_press(button_name)

    def send_input_release(self, button_name):
        if self.pyboy:
            self.pyboy.button_release(button_name)

    def save_RAM(self):
        try:
            rom_dir = os.path.dirname(self.rom_path)
            RAMfile = (
                os.path.join(rom_dir, "rom_seleccionada.gbc") if platform == "android" else self.rom_path
            ) + ".ram"

            with open(RAMfile, "wb") as f:
                self.pyboy.save_state(f, True)

            file_size = os.path.getsize(RAMfile)
            print(f"[DEBUG] Ram guardada: {RAMfile} ({file_size} bytes)")

        except Exception as e:
            if self.on_text_output:
                Clock.schedule_once(lambda dt, err=e: self.on_text_output(f"Error guardando RAM: {err}"), 0)

