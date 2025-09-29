from kivy.clock import Clock
import numpy as np

def draw_sprite(frame, sprite_array, x, y):
    """
    Dibuja un sprite RGBA sobre el framebuffer.
    Alpha binario: 0 (transparente) o 255 (opaco).
    Maneja correctamente cuando el sprite está fuera de pantalla.
    """
    H, W, _ = frame.shape
    h, w, _ = sprite_array.shape

    # Coordenadas destino en el framebuffer
    x0 = max(x, 0)
    y0 = max(y, 0)
    x1 = min(x + w, W)
    y1 = min(y + h, H)

    if x0 >= x1 or y0 >= y1:
        return  # completamente fuera de pantalla

    # Coordenadas origen en el sprite (recorte)
    sx0 = max(0, -x)
    sy0 = max(0, -y)
    sx1 = sx0 + (x1 - x0)
    sy1 = sy0 + (y1 - y0)

    frame_slice = frame[y0:y1, x0:x1]
    sprite_crop = sprite_array[sy0:sy1, sx0:sx1]

    # Máscara de píxeles opacos
    mask = sprite_crop[:, :, 3] == 255

    # Copiar solo donde el sprite es opaco
    frame_slice[mask] = sprite_crop[mask]



def create_black_sprite(size=16):
    """
    Crea un sprite negro RGBA de tamaño `size x size`.
    Con algunos píxeles transparentes para probar el blending binario.
    """
    sprite = np.zeros((size, size, 4), dtype=np.uint8)
    sprite[..., :3] = 0      # negro
    sprite[..., 3] = 255     # opaco

    # Hacer transparente la diagonal principal
    for i in range(size):
        sprite[i, i, 3] = 0  # alpha = 0 → transparente

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
        self.sprite_x = -8
        self.sprite_y = -8

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
                draw_sprite(frame_arr, self.black_sprite, 64, 64)
                draw_sprite(frame_arr, self.black_sprite, 155, 140)
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
