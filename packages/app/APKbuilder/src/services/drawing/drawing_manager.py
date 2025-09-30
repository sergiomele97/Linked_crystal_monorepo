from kivy.clock import Clock
import numpy as np

from services.drawing.sprite_renderer import SpriteRenderer

class DrawingManager:

    def __init__(self, ramData, connectionData, pyboy, on_frame=None,):
        #Callbacks
        self.on_frame = on_frame
        #Emulator instance
        self.pyboy = pyboy
        #Models
        self.ramData = ramData
        self.connectionData = connectionData
        #Services
        self.spriteRenderer = SpriteRenderer()
        # Sprite negro de personaje (16x16)
        self.black_sprite = self.spriteRenderer.create_black_sprite(16)
            # Coordenadas iniciales del sprite (puedes cambiar según overworld)
        self.sprite_x = -8
        self.sprite_y = -8


    def update_frame(self):
        if self.on_frame:
            frame_arr = self.pyboy.screen.ndarray
            # Dibujar cuadrado negro del sprite
            self.spriteRenderer.draw(frame_arr, self.black_sprite, self.sprite_x, self.sprite_y)
            self.spriteRenderer.draw(frame_arr, self.black_sprite, 64, 64)
            self.spriteRenderer.draw(frame_arr, self.black_sprite, 155, 140)

            Clock.schedule_once(lambda dt: self.on_frame(frame_arr), 0)
