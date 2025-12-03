from kivy.app import App

class RamScrapper:
    def __init__(self, pyboy, ramData):
        self.pyboy = pyboy
        self.ramData = ramData
        self.localPacket = App.get_running_app().appData.packet
    
    '''
    Function which will run every pyboy tick and updates
    all the information we need from the GBC RAM
    '''
    def update_ram_data(self):
        # Absolute player position
        # Doesn't update until moving cycle has completed.
        self.ramData.player_x_coord = self.pyboy.memory[0xDCB8]
        self.ramData.player_y_coord = self.pyboy.memory[0xDCB7]

        # In which map the player is right now
        self.ramData.map_number = self.pyboy.memory[0xDCB6]
        self.ramData.map_bank = self.pyboy.memory[0xDCB5]

        # More dinamical player position
        self.updateSpriteCoord()
        self.ramData.x_coord_sprite[0] = self.pyboy.memory[0xD14C]
        self.ramData.y_coord_sprite[0] = self.pyboy.memory[0xD14D]

        # Gives info about potential collision
        self.ramData.collision_down = self.pyboy.memory[0xC2FA]
        self.ramData.collision_up = self.pyboy.memory[0xC2FB]
        self.ramData.collision_left = self.pyboy.memory[0xC2FC]
        self.ramData.collision_right = self.pyboy.memory[0xC2FD]

        # Actualizar el paquete que se va a enviar
        self.updateOnlinePacket()
    
    '''
    In order to have a fluid animation, we need information from 
    4 ticks before
    '''
    def updateSpriteCoord(self):
        self.ramData.x_coord_sprite[4] = self.ramData.x_coord_sprite[3]
        self.ramData.x_coord_sprite[3] = self.ramData.x_coord_sprite[2]
        self.ramData.x_coord_sprite[2] = self.ramData.x_coord_sprite[1]
        self.ramData.x_coord_sprite[1] = self.ramData.x_coord_sprite[0]

        self.ramData.y_coord_sprite[4] = self.ramData.y_coord_sprite[3]
        self.ramData.y_coord_sprite[3] = self.ramData.y_coord_sprite[2]
        self.ramData.y_coord_sprite[2] = self.ramData.y_coord_sprite[1]
        self.ramData.y_coord_sprite[1] = self.ramData.y_coord_sprite[0]
    
    def updateOnlinePacket(self):
        self.localPacket.player_x_coord = self.ramData.player_x_coord
        self.localPacket.player_y_coord = self.ramData.player_y_coord

        self.localPacket.map_number = self.ramData.map_number
        self.localPacket.map_bank = self.ramData.map_bank

        self.localPacket.IsOverworld = True
