from kivy.clock import Clock
from kivy.app import App
import threading
import time

from models.ramData import RamData
from models.packet import Packet

from services.emulator.ram_scrapper import RamScrapper
from services.emulator.ram_hooks import RamHooks
from services.audio.audio_manager import AudioManagerKivy
from services.drawing.drawing_manager import DrawingManager


class EmulationLoop:
    """
    Clase que maneja el ciclo de emulación.
    Se encarga de ejecutar pasos de emulación y notificar
    a la interfaz de usuario mediante callbacks.
    """

    def __init__(self, pyboy, on_frame=None, on_text_output=None, on_save=None):
    #EmulatorInstance
        self.pyboy = pyboy
    #Callbacks
        self.on_frame = on_frame
        self.on_text_output = on_text_output
        self.on_save = on_save
    #Models
        self.ramData = App.get_running_app().appData.ramData
        self.packet = App.get_running_app().appData.packet
        self.serverPackets = App.get_running_app().appData.serverPackets
    #Services
        self.audioManager = AudioManagerKivy(self.pyboy)
        self.ramScrapper = RamScrapper(self.pyboy, self.ramData)
        self.ramHooks = RamHooks(self.ramData, self.on_save)
        self.drawingManager = DrawingManager(self.ramData, self.serverPackets, self.pyboy, self.on_frame)
    #Others
        self.running = False
        self._clock_event = None


    def start(self, fps=60):
        """Inicia el ciclo de emulación en un hilo independiente."""
        if not self.pyboy or self.running:
            return

        self.running = True
        self.fps = fps
        self.interval = 1.0 / fps
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Detiene el ciclo de emulación."""
        self.running = False
        self.thread = None

    def _run(self):
        """Bucle principal de ejecución en el hilo secundario."""
        while self.running and self.pyboy:
            t_start = time.perf_counter()
            
            # Ejecutamos un tick de PyBoy
            if self.pyboy.tick():
                self.ramScrapper.update_ram_data()
                self.drawingManager.update_frame()
                self.audioManager.update_audio()
                self.ramHooks.handle_hooks()
            else:
                self.running = False
                if self.on_text_output:
                    Clock.schedule_once(
                        lambda dt: self.on_text_output("Emulación finalizada"), 0
                    )
                break

            # Control de FPS inteligente:
            # Si un frame tarda más de lo normal (ej. por Link Cable), 
            # NO intentamos recuperar el tiempo. Simplemente esperamos al siguiente intervalo.
            t_end = time.perf_counter()
            elapsed = t_end - t_start
            
            # Si tardamos menos de 1/60s, dormimos el resto
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            else:
                # Si tardamos MÁS, no dormimos nada, pero tampoco intentamos "correr" en el siguiente frame.
                # Dejamos que el sistema respire.
                pass

    def _step(self, dt):
        """Obsoleto: El paso de emulación ahora se maneja en _run."""
        pass

