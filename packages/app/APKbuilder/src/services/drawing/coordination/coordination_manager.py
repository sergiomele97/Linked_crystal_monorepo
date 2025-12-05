class CoordinationManager:  

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

        # --- 1. Diferencia en tiles ---
        dx = other_fine_x - self.x_fine_coord
        dy = other_fine_y - self.y_fine_coord

        # ... sin implementar

        return dx, dy




