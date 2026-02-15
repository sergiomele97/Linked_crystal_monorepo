from kivy.clock import Clock

from services.drawing.entities.remote_player_manager import RemotePlayerManager
from services.drawing.synchronization.synchro_manager import SynchronizationManager
from services.drawing.rendering.sprite_renderer import SpriteRenderer
from services.drawing.scenarios.scenario_manager import ScenarioManager

class DrawingManager:

    def __init__(self, ramData, serverPackets, pyboy, on_frame=None,):
        self.on_frame = on_frame
        self.pyboy = pyboy
        self.ramData = ramData
        self.serverPackets = serverPackets
        self.onScreenPlayers = {} 
        self.remotePlayerManager = RemotePlayerManager(
            self.ramData,
            self.serverPackets, 
            self.onScreenPlayers
            )
        self.synchronizationManager = SynchronizationManager(self.ramData)
        self.spriteRenderer = SpriteRenderer()
        self.spriteRenderer.load_sprite_sheet("resources/image/OW_default_sprite.png")
        self.scenarioManager = ScenarioManager(self.ramData)

    def update_frame(self):
        if self.on_frame:
            frame_array = self.pyboy.screen.ndarray.copy()

            self.remotePlayerManager.updateOnScreenPlayersFromNetwork()
            self.synchronizationManager.updateLocalFineCoords()
            self.scenarioManager.updateScenario()

            for player in self.onScreenPlayers.values():
                player.updateFineCoords()
                x_render_coord, y_render_coord = self.synchronizationManager.calculate_render_coords(
                    player.x_fine_coord, player.y_fine_coord
                )
                self.spriteRenderer.draw_sprite(
                    frame_array,
                    x_render_coord,
                    y_render_coord,
                    player.current_sprite
                )

            Clock.schedule_once(lambda dt: self.on_frame(frame_array), 0)
    