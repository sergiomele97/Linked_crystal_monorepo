from services.drawing.synchronization.movement_cycle import MovementCycle

class SynchronizationManager:

    CENTER_SCREEN_CORRECTION = 64
    VERTICAL_SPRITE_CORRECTION = 4

    def __init__(self, ramData):
        self.ram = ramData
        self.cycle = MovementCycle()

        self.x_fine_coord = self.ram.player_x_coord * 16
        self.y_fine_coord = self.ram.player_y_coord * 16

    def get_local_direction(self):
        x0, x1 = self.ram.x_coord_sprite[0], self.ram.x_coord_sprite[1]
        y0, y1 = self.ram.y_coord_sprite[0], self.ram.y_coord_sprite[1]

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

        if not self.cycle.active:
            direction = self.get_local_direction()
        else:
            direction = self.cycle.direction

        if not self.cycle.active and direction == "none":
            self.x_fine_coord = self.ram.player_x_coord * 16
            self.y_fine_coord = self.ram.player_y_coord * 16
            return

        if not self.cycle.active:
            self.cycle.start(direction, self.ram)

        self.x_fine_coord, self.y_fine_coord = self.cycle.step(self.ram)

    def calculate_render_coords(self, other_x, other_y):
        dx = other_x - self.x_fine_coord
        dy = other_y - self.y_fine_coord

        return (
            dx + self.CENTER_SCREEN_CORRECTION,
            dy + self.CENTER_SCREEN_CORRECTION - self.VERTICAL_SPRITE_CORRECTION
        )
