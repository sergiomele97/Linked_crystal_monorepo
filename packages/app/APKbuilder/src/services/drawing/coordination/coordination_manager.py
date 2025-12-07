class CoordinationManager:  

    CENTER_SCREEN_CORRECTION = 64
    VERTICAL_SPRITE_CORRECTION = 4
    PIXEL_MOVEMENT_CORRECTION = [2,2,4,4,6,6,8,8,10,10,12,12,14,14]

    def __init__(self, ramData):
        self.ram = ramData
        self.x_fine_coord = self.ram.player_x_coord * 16
        self.y_fine_coord = self.ram.player_y_coord * 16

        self.local_direction = "none"
        self.local_moving_cycle = False
        self.local_moving_count = 0
        self.base_x_during_cycle = 0
        self.base_y_during_cycle = 0

    def get_local_direction(self):
        x0, x1 = self.ram.x_coord_sprite[1],self.ram.x_coord_sprite[2]
        y0, y1 = self.ram.y_coord_sprite[1],self.ram.y_coord_sprite[2]

        dx = (x0 - x1 + 128) % 256 - 128
        dy = (y0 - y1 + 128) % 256 - 128

        if dx == 0 and dy == 0:
            return "none"

        return (
            "right" if abs(dx) > abs(dy) and dx > 0 else
            "left"  if abs(dx) > abs(dy) else
            "down"  if dy > 0 else
            "up"
        )

    def updateLocalFineCoords(self):
        if not self.local_moving_cycle:
            direction = self.get_local_direction()
        else:
            direction = self.local_direction 
        print(f"Direction {direction}")

        if not self.local_moving_cycle and direction == "none":
            print(f"ESTA QUIETO ESTE TICK")
            self.local_moving_cycle = False
            self.local_moving_count = 0
            self.x_fine_coord = self.ram.player_x_coord * 16
            self.y_fine_coord = self.ram.player_y_coord * 16
            print(f"y fine {self.y_fine_coord}")
            return

        # Inicio de moving cycle
        if not self.local_moving_cycle:
            print("INICIO DE MOVING CYCLE")
            self.local_moving_cycle = True
            self.local_moving_count = 0
            self.local_direction = direction  
            self.base_x_during_cycle = self.ram.player_x_coord * 16
            self.base_y_during_cycle = self.ram.player_y_coord * 16

        correction = self.PIXEL_MOVEMENT_CORRECTION[min(self.local_moving_count, 14)]

        base_x = self.base_x_during_cycle
        base_y = self.base_y_during_cycle

        if self.local_direction == "left":
            self.x_fine_coord = base_x + correction
            self.y_fine_coord = base_y

        elif self.local_direction == "right":
            self.x_fine_coord = base_x - correction
            self.y_fine_coord = base_y

        elif self.local_direction == "up":
            self.x_fine_coord = base_x
            self.y_fine_coord = base_y + correction

        elif self.local_direction == "down":
            self.x_fine_coord = base_x
            self.y_fine_coord = base_y - correction

        self.local_moving_count += 1

        
        # Fin del ciclo
        if self.local_moving_count >= 14:
            print("FIN DE MOVING CYCLE")
            self.local_moving_cycle = False
            self.local_moving_count = 0
        
        print(f"base y {base_y} // correction: {correction} // y_fine: {self.y_fine_coord} // moving_cycle {self.local_moving_cycle} //moving count {self.local_moving_count}")



    def calculate_render_coords(self, other_fine_x, other_fine_y):
        """
        Devuelve las coordenadas de pantalla donde dibujar a otro jugador.
        """
        dx = other_fine_x - self.x_fine_coord
        dy = other_fine_y - self.y_fine_coord

        render_x = dx + self.CENTER_SCREEN_CORRECTION
        render_y = dy + self.CENTER_SCREEN_CORRECTION - self.VERTICAL_SPRITE_CORRECTION

        return render_x, render_y

