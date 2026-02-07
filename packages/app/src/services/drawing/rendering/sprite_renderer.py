import numpy as np
from PIL import Image


class SpriteRenderer:
    """
    Clase que maneja el renderizado de sprites RGBA sobre un framebuffer.
    Usa alpha binario (0 = transparente, 255 = opaco).
    """

    def draw(self, frame, sprite_array, x, y):
        """
        Dibuja un sprite RGBA sobre el framebuffer en (x, y).
        Maneja recortes si el sprite está fuera de pantalla.
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

    def load_sprite_sheet(self, path, frame_width=16, frame_height=16):
        """
        Carga una hoja de sprites (sprite sheet) PNG en formato RGBA.
        Devuelve un array numpy (H, W, 4) y una lista de frames (cada uno 16x16).
        """
        image = Image.open(path).convert("RGBA")
        sheet = np.array(image, dtype=np.uint8)

        sheet_h, sheet_w, _ = sheet.shape
        frames = []

        num_frames = sheet_w // frame_width
        for i in range(num_frames):
            x0 = i * frame_width
            x1 = x0 + frame_width
            frame = sheet[0:frame_height, x0:x1, :]
            frames.append(frame)

        self.sprite_sheet = sheet
        self.sprite_frames = frames
        return frames

    def draw_sprite(self, frame, x, y, current_sprite):
        """
        Dibuja el frame indicado por current_sprite.
        """
        if not hasattr(self, 'sprite_frames'):
            raise ValueError("No se han cargado sprites con load_sprite_sheet().")

        if current_sprite < 0 or current_sprite >= len(self.sprite_frames):
            raise IndexError(f"Frame inválido: {current_sprite}")

        sprite = self.sprite_frames[current_sprite]
        self.draw(frame, sprite, x, y)
