class RamData:
    def __init__(self):
        self.player_x_coord = 0
        self.player_y_coord = 0

        self.map_number = 0
        self.map_bank = 0

        self.x_coord_sprite = [-1, -1, -1, -1, -1]
        self.y_coord_sprite = [-1, -1, -1, -1, -1]

        self.is_gui_open = False
        self.is_saving = 0
        self.wram_bank = 0