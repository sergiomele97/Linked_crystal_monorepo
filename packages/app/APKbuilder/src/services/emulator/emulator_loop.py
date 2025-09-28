from kivy.clock import Clock
import numpy as np

def draw_sprite(frame, sprite_array, x, y):
    """
    Dibuja un sprite RGBA sobre el framebuffer usando blending.
    """
    h, w, _ = sprite_array.shape

    # Evitar salirse del framebuffer
    h = min(h, frame.shape[0] - y)
    w = min(w, frame.shape[1] - x)
    if h <= 0 or w <= 0:
        return

    frame_slice = frame[y:y+h, x:x+w]

    # Normalizar alpha
    alpha = sprite_array[:h, :w, 3:4] / 255.0

    # Blending de los 3 canales de color
    frame_slice[:, :, :3] = frame_slice[:, :, :3] * (1 - alpha) + sprite_array[:h, :w, :3] * alpha

    # Opcional: mantener alpha del framebuffer igual
    frame_slice[:, :, 3] = 255  # o dejar frame original si quieres



def create_black_sprite(size=16):
    """
    Crea un sprite negro RGBA de tamaño `size x size`.
    """
    sprite = np.zeros((size, size, 4), dtype=np.uint8)
    sprite[..., :3] = 0      # negro
    sprite[..., 3] = 255     # opaco
    return sprite


class EmulationLoop:
    """
    Clase que maneja el ciclo de emulación.
    Se encarga de ejecutar pasos de emulación y notificar
    a la interfaz de usuario mediante callbacks.
    """

    def __init__(self, pyboy, on_frame=None, on_audio=None, on_text_output=None):
        self.pyboy = pyboy
        self.on_frame = on_frame
        self.on_audio = on_audio
        self.on_text_output = on_text_output
        self.running = False
        self._clock_event = None

        # Sprite negro de personaje (16x16)
        self.black_sprite = create_black_sprite(16)
        # Coordenadas iniciales del sprite (puedes cambiar según overworld)
        self.sprite_x = 64
        self.sprite_y = 66

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
            # Enviar frame
            if self.on_frame:
                frame_arr = self.pyboy.screen.ndarray
                # Dibujar cuadrado negro del sprite
                draw_sprite(frame_arr, self.black_sprite, self.sprite_x, self.sprite_y)
                Clock.schedule_once(lambda dt: self.on_frame(frame_arr), 0)

            # Enviar audio
            audio_len = self.pyboy.sound.raw_buffer_head
            if audio_len > 0 and self.on_audio:
                audio_buffer = self.pyboy.sound.ndarray[:audio_len]
                sample_rate = self.pyboy.sound.sample_rate
                self.on_audio(audio_buffer, sample_rate)
        else:
            # Fin de emulación
            self.stop()
            if self.on_text_output:
                Clock.schedule_once(
                    lambda dt: self.on_text_output("Emulación finalizada"), 0
                )
            return False
