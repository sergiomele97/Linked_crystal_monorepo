from pyboy import PyBoy
from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
import threading
import os

from services.environment.environment_manager import solicitar_permisos
from services.emulator.emulator_loop import EmulationLoop


class EmulatorCoreInterface:
    """
    Clase que crea y gestiona la instancia de Pyboy
    """
    def __init__(self, on_frame=None, on_audio=None, on_text_output=None):
        self.on_frame = on_frame
        self.on_text_output = on_text_output
        self.on_audio = on_audio
        self.pyboy = None
        self.loop = None

    def start(self):
        threading.Thread(target=self._initialize, daemon=True).start()

    def _initialize(self):
        solicitar_permisos()

        if not os.path.exists(App.get_running_app().rom_path):
            if self.on_text_output:
                Clock.schedule_once(lambda dt: self.on_text_output("ROM no encontrada"), 0)
            return

        try:
            self.pyboy = PyBoy(
                App.get_running_app().rom_path,
                window="null",
                sound_emulated=True,
                sound_volume=100,
            )
            self.pyboy.set_emulation_speed(1)
        except Exception as e:
            if self.on_text_output:
                print(f"Error al cargar ROM: {e}")
            return

        # Crear y lanzar el loop de emulación
        self.loop = EmulationLoop(
            self.pyboy, self.on_frame, self.on_audio, self.on_text_output
        )
        self.loop.start(fps=60)

    def send_input_press(self, button_name):
        if self.pyboy:
            self.pyboy.button_press(button_name)

    def send_input_release(self, button_name):
        if self.pyboy:
            self.pyboy.button_release(button_name)

    def save_RAM(self):
        try:
            rom_dir = os.path.dirname(App.get_running_app().rom_path)
            RAMfile = (
                os.path.join(rom_dir, "rom_seleccionada.gbc")
                if platform == "android"
                else App.get_running_app().rom_path
            ) + ".ram"

            with open(RAMfile, "wb") as f:
                self.pyboy.save_state(f, True)

            file_size = os.path.getsize(RAMfile)
            self.on_text_output(f"[DEBUG] Ram guardada: {RAMfile} ({file_size} bytes)")
            print(f"[DEBUG] Ram guardada: {RAMfile} ({file_size} bytes)")

        except Exception as e:
            if self.on_text_output:
                Clock.schedule_once(
                    lambda dt, err=e: self.on_text_output(f"Error guardando RAM: {err}"), 0
                )
