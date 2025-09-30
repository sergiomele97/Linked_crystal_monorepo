from kivy.clock import Clock

from models.ramData import RamData
from models.connectionData import ConnectionData

from services.emulator.ram_scrapper import RamScrapper
from services.audio.audio_manager import AudioManagerKivy
from services.drawing.drawing_manager import DrawingManager
from services.connection.connection_manager import ConnectionManager


class EmulationLoop:
    """
    Clase que maneja el ciclo de emulación.
    Se encarga de ejecutar pasos de emulación y notificar
    a la interfaz de usuario mediante callbacks.
    """

    def __init__(self, pyboy, on_frame=None, on_text_output=None):
    #EmulatorInstance
        self.pyboy = pyboy
    #Callbacks
        self.on_frame = on_frame
        self.on_text_output = on_text_output
    #Models
        self.ramData = RamData()
        self.connectionData = ConnectionData()
    #Services
        self.audioManager = AudioManagerKivy(self.pyboy)
        self.ramScrapper = RamScrapper(self.ramData)
        self.connectionManager = ConnectionManager(self.connectionData)
        self.drawingManager = DrawingManager(self.ramData, self.connectionData, self.pyboy, self.on_frame)
    #Others
        self.running = False
        self._clock_event = None


    def start(self, fps=60):
        """Inicia el ciclo de emulación."""
        if not self.pyboy:
            return

        self.running = True
        interval = 1 / fps
        self._clock_event = Clock.schedule_interval(self._step, interval)

    def stop(self):
        """Detiene el ciclo de emulación."""
        self.running = False
        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None

    def _step(self, dt):
        """Ejecuta un paso de emulación."""
        if not self.running or not self.pyboy:
            return False

        if self.pyboy.tick():
            self.connectionManager.update_online_data()
            self.ramScrapper.update_ram_data()
            self.drawingManager.update_frame()
            self.audioManager.update_audio()
            
        else:
            self.stop()
            if self.on_text_output:
                Clock.schedule_once(
                    lambda dt: self.on_text_output("Emulación finalizada"), 0
                )
            return False

