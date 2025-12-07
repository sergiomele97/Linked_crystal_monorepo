class MovementCycle:

    PIXEL_MOVEMENT_CORRECTION = [0,0,2,2,4,4,6,6,8,8,10,10,12,12,14,14]

    def __init__(self):
        self.active = False
        self.count = 0
        self.direction = "none"
        self.base_x = 0
        self.base_y = 0

    def apply_frame_instability_correction(self, ram):
        dx = abs(ram.x_coord_sprite[0] - ram.x_coord_sprite[1])
        dy = abs(ram.y_coord_sprite[0] - ram.y_coord_sprite[1])

        if dx in (4, 252) or dy in (4, 252):
            self.count += 1

    def start(self, direction, ram):
        self.active = True
        self.count = 0
        self.direction = direction
        self.apply_frame_instability_correction(ram)

        self.base_x = ram.player_x_coord * 16
        self.base_y = ram.player_y_coord * 16

    def step(self, ram):
        correction = self.PIXEL_MOVEMENT_CORRECTION[min(self.count, 15)]

        bx, by = self.base_x, self.base_y

        if self.direction == "left":
            x = bx + correction
            y = by
        elif self.direction == "right":
            x = bx - correction
            y = by
        elif self.direction == "up":
            x = bx
            y = by + correction
        else:  # down
            x = bx
            y = by - correction

        self.count += 1

        if self.count > 15:
            self.active = False
            self.count = 0

        return x, y
