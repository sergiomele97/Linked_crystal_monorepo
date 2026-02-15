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
        self.ramData.wram_bank = self.pyboy.memory[0xFF70] & 0x07

        wy = self.pyboy.memory[0xFF4A]
        menu_state = self.pyboy.memory[0xCF14]
        self.ramData.is_gui_open = (wy < 144) or (menu_state > 0)

        self.ramData.is_saving = self.pyboy.memory[0xD151]

        if self.ramData.wram_bank == 1:
            self.update_overworld_info()


    def update_overworld_info(self):

        self.ramData.player_x_coord = self.pyboy.memory[0xDCB8]
        self.ramData.player_y_coord = self.pyboy.memory[0xDCB7]

        self.ramData.map_number = self.pyboy.memory[0xDCB6]
        self.ramData.map_bank = self.pyboy.memory[0xDCB5]

        self.updateSpriteCoord()
        self.ramData.x_coord_sprite[0] = self.pyboy.memory[0xD14C]
        self.ramData.y_coord_sprite[0] = self.pyboy.memory[0xD14D]

        self.updateOnlinePacket()


    def updateSpriteCoord(self):
        # In order to have a fluid animation, we need information from 4 ticks before
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
