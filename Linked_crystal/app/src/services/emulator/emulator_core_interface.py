from pyboy import PyBoy
from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
import threading
import os

from services.environment.environment_manager import solicitar_permisos
from services.emulator.emulator_loop import EmulationLoop
from services.connection.link_cable.link_client import LinkClient
from services.logger import log


class EmulatorCoreInterface:
    """
    Clase que crea y gestiona la instancia de Pyboy
    """
    def __init__(self, on_frame=None, on_text_output=None):
        self.on_frame = on_frame
        self.on_text_output = on_text_output
        self.pyboy = None
        self.loop = None
        self.link_client = LinkClient()

    def start(self):
        threading.Thread(target=self._initialize, daemon=True).start()
        
    def connect_link(self, my_id, target_id, host="127.0.0.1", port=8080):
        """
        Inicia la conexión WebSocket hacia el endpoint /link del servidor Go.
        """
        if self.link_client:
            # Usamos el método start adaptado a la lógica de ConnectionLoop (asyncio)
            self.link_client.start(host, port, my_id, target_id)
            if self.on_text_output:
                self.on_text_output(f"Conectando Link: {my_id} <-> {target_id}")

    def disconnect_link(self):
        """
        Cierra el túnel de datos sin detener la emulación.
        """
        if self.link_client:
            self.link_client.stop()
            if self.on_text_output:
                self.on_text_output("Link desconectado")

    def get_link_status(self):
        if not self.link_client:
            return {"connected": False, "tx": 0, "rx": 0}
        
        connected = (self.link_client.thread is not None and 
                     self.link_client.thread.is_alive() and 
                     not self.link_client._stop_event.is_set())
                     
        return {
            "connected": connected,
            "bridged": getattr(self.link_client, 'bridged', False),
            "tx": self.link_client.count_sent,
            "rx": self.link_client.count_recv
        }

    def _initialize(self):
        solicitar_permisos()

        if not os.path.exists(App.get_running_app().appData.romPath):
            if self.on_text_output:
                Clock.schedule_once(lambda dt: self.on_text_output("ROM no encontrada"), 0)
            return

        try:
            # Inyectamos los hooks de LinkClient en PyBoy. 
            # PyBoy enviará bytes a través de link_send (que usa call_soon_threadsafe)
            # y leerá de link_recv_queue (una Queue síncrona alimentada por la red).
            self.pyboy = PyBoy(
                App.get_running_app().appData.romPath,
                window="null",
                sound_emulated=True,
                sound_volume=100,
                link_send=self.link_client.send_byte,
                link_recv_queue=self.link_client.recv_queue
            )
            self.pyboy.set_emulation_speed(1)
        except Exception as e:
            if self.on_text_output:
                log(f"Error al cargar ROM: {e}")
            return

        # Crear y lanzar el loop de emulación
        self.loop = EmulationLoop(
            self.pyboy, self.on_frame, self.on_text_output, on_save=self.save_RAM
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
            rom_dir = os.path.dirname(App.get_running_app().appData.romPath)
            RAMfile = (
                os.path.join(rom_dir, "gamerom.gbc")
                if platform == "android"
                else App.get_running_app().appData.romPath
            ) + ".ram"

            with open(RAMfile, "wb") as f:
                self.pyboy.save_state(f, True)

            file_size = os.path.getsize(RAMfile)
            self.on_text_output(f"[DEBUG] Ram guardada: {RAMfile} ({file_size} bytes)")
            log(f"[DEBUG] Ram guardada: {RAMfile} ({file_size} bytes)")

        except Exception as e:
            if self.on_text_output:
                Clock.schedule_once(
                    lambda dt, err=e: self.on_text_output(f"Error guardando RAM: {err}"), 0
                )
                