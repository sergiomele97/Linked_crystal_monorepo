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
        self.spriteRenderer.load_sprite_sheet("resources/image/OW_default_sprite.png")


    def update_frame(self):
        if self.on_frame:
            # Gets current native frame
            frame_arr = self.pyboy.screen.ndarray

            # Draws foreign sprites
            self.spriteRenderer.draw_first_frame(frame_arr, 0, 0)

            # Sends update to kivy
            Clock.schedule_once(lambda dt: self.on_frame(frame_arr), 0)
