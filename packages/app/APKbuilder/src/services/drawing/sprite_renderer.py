import numpy as np

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

    def create_black_sprite(self, size=16):
        """
        Crea un sprite negro RGBA de tamaño `size x size`.
        Con algunos píxeles transparentes en la diagonal.
        """
        sprite = np.zeros((size, size, 4), dtype=np.uint8)
        sprite[..., :3] = 0      # negro
        sprite[..., 3] = 255     # opaco

        # Hacer transparente la diagonal principal
        for i in range(size):
            sprite[i, i, 3] = 0  # alpha = 0 → transparente

        return sprite
