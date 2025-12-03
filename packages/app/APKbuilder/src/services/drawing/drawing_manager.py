from kivy.clock import Clock
import numpy as np

from services.drawing.coordinate_calculator import CoordinateCalculator
from services.drawing.sprite_renderer import SpriteRenderer

class DrawingManager:

    def __init__(self, ramData, serverPackets, pyboy, on_frame=None,):
        #Callbacks
        self.on_frame = on_frame
        #Emulator instance
        self.pyboy = pyboy
        #Models
        self.ramData = ramData
        self.serverPackets = serverPackets
        #Services
        self.coordinateCalculator = CoordinateCalculator(self.ramData)
        self.spriteRenderer = SpriteRenderer()
        self.spriteRenderer.load_sprite_sheet("resources/image/OW_default_sprite.png")


    def update_frame(self):
        if self.on_frame:
            # Gets current native frame
            frame_arr = self.pyboy.screen.ndarray

            # Draws foreign sprites
            for packet in self.serverPackets:

                # Filter outbounds players
                if(self.coordinateCalculator.shouldFilter(packet)):
                    continue

                # Calculate where to draw 
                x_render_coord, y_render_coord = self.coordinateCalculator.calculate_player_coords(
                    packet.player_x_coord,
                    packet.player_y_coord
                )

                # Render sprite
                self.spriteRenderer.draw_first_frame(
                    frame_arr,
                    x_render_coord,
                    y_render_coord
                )

            # Sends update to kivy
            Clock.schedule_once(lambda dt: self.on_frame(frame_arr), 0)
