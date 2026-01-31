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

    def __str__(self):
        return (
            f"--- RamData Status ---\n"
            f"📍 Position: ({self.player_x_coord}, {self.player_y_coord})\n"
            f"🗺️  Map: Bank {self.map_bank}, Number {self.map_number}\n"
            f"👾 Sprites X: {self.x_coord_sprite}\n"
            f"👾 Sprites Y: {self.y_coord_sprite}\n"
            f"🖥️  GUI Open: {'Yes' if self.is_gui_open else 'No'}\n"
            f"💾 Saving: {self.is_saving}\n"
            f"🏦 WRAM Bank: {self.wram_bank}\n"
            f"----------------------"
        )

    def __repr__(self):
        return f"<RamData pos=({self.player_x_coord},{self.player_y_coord}) map={self.map_bank}:{self.map_number}>"