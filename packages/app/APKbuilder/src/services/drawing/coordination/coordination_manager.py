class CoordinationManager:  

    CENTER_SCREEN_CORRECTION = 64
    VERTICAL_SPRITE_CORRECTION = 4

    def __init__(self, ramData):
        self.ram = ramData
        self.x_fine_coord = self.ram.player_x_coord * 16
        self.y_fine_coord = self.ram.player_y_coord * 16

    def updateLocalFineCoords(self):
        self.x_fine_coord = self.ram.player_x_coord * 16
        self.y_fine_coord = self.ram.player_y_coord * 16

    def calculate_render_coords(self, other_fine_x, other_fine_y):
        """
        Devuelve las coordenadas de pantalla donde dibujar a otro jugador.
        """

        dx = other_fine_x - self.x_fine_coord
        dy = other_fine_y - self.y_fine_coord

        render_x = dx + self.CENTER_SCREEN_CORRECTION
        render_y = dy + self.CENTER_SCREEN_CORRECTION - self.VERTICAL_SPRITE_CORRECTION

        return render_x, render_y

