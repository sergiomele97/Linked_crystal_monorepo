class RemotePlayerEntity:
    """
    Entidad visual de un jugador remoto.
    Se encarga de interpolar posición hacia el último estado recibido,
    gestionar dirección/animación y reportar coordenadas de renderizado.
    """

    # --- CONFIGURACIÓN GLOBAL ---
    TILE_SIZE = 16

    PIXEL_MOVEMENT_CORRECTION = [0,0,2,2,4,4,6,6,8,8,10,10,12,12,14,14]

    FRAME_MAP = {
        "down": {
            "idle": 1,
            "step_right": 0,
            "step_left": 2
        },
        "up": {
            "idle": 4,
            "step_right": 3,
            "step_left": 5
        },
        "left": {
            "idle": 6,
            "step_right": 7,
            "step_left": 6  
        },
        "right": {
            "idle": 8,
            "step_right": 9,
            "step_left": 8  
        }
    }

    def __init__(self, player_id, initial_x, initial_y):
        self.player_id = player_id

        # Target
        self.target_x = initial_x
        self.target_y = initial_y

        # Posición fina relativa a overworld
        self.x_fine_coord = initial_x * self.TILE_SIZE
        self.y_fine_coord = initial_y * self.TILE_SIZE

        self.direction = "down"
        self.is_moving = False
        self.current_sprite = 0
        self.move_tick = 0.0
        self.remote_speed = 1
        self.pending_target = None  # Buffer para el siguiente movimiento

    # ---------------------------------------------------------
    #         Actualiza target y dirección 
    # ---------------------------------------------------------
    def update_from_network(self, packet):
        self.remote_speed = getattr(packet, 'speed', 1)
        
        pk_x = packet.player_x_coord
        pk_y = packet.player_y_coord

        if not self.is_moving:
            # Si no nos estamos moviendo, evaluamos si el nuevo paquete
            # indica una posición distinta a la actual.
            if pk_x != self.target_x or pk_y != self.target_y:
                self._start_move(pk_x, pk_y)
        else:
            # Si ya estamos en movimiento, comprobamos si el paquete
            # trae un destino distinto al actual (un movimiento futuro).
            if pk_x != self.target_x or pk_y != self.target_y:
                self.pending_target = (pk_x, pk_y)

    def _start_move(self, tx, ty):
        """Inicializa un nuevo tramo de movimiento."""
        old_tx, old_ty = self.target_x, self.target_y
        self.target_x = tx
        self.target_y = ty
        self.is_moving = True
        self.move_tick = 0.0

        # Calcular dirección basada en el desplazamiento desde la posición teórica actual
        # (que debería ser el target anterior)
        dx = self.target_x - old_tx
        dy = self.target_y - old_ty
        
        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
        elif abs(dy) > 0:
            self.direction = "down" if dy > 0 else "up"

    # ---------------------------------------------------------------
    #        Actualiza posición fina relativa a mundo (render_x/y)
    # ---------------------------------------------------------------
    def updateFineCoords(self, local_speed=1):
        if not self.is_moving:
            return

        # Calcular cuánto avanzar en este tick
        advance = self.remote_speed / local_speed
        
        # Guardar tick previo para calcular incremento de delta
        prev_tick_int = int(self.move_tick)
        self.move_tick += advance
        curr_tick_int = int(self.move_tick)

        # Si no hemos cruzado un tick entero, no hay movimiento de píxeles nuevo hoy 
        # (a menos que advance sea >= 1)
        
        # En el sistema original de Crystal, cada tick de los 16 tiene un delta acumulado.
        # PIXEL_MOVEMENT_CORRECTION es el desplazamiento ACUMULADO en cada tick.
        
        target_idx = min(curr_tick_int, 15)
        prev_idx = min(prev_tick_int, 15)
        
        delta = self.PIXEL_MOVEMENT_CORRECTION[target_idx]
        prev_delta = self.PIXEL_MOVEMENT_CORRECTION[prev_idx]
        
        step_size = delta - prev_delta

        target_px_x = self.target_x * self.TILE_SIZE
        target_px_y = self.target_y * self.TILE_SIZE

        dx = target_px_x - self.x_fine_coord
        dy = target_px_y - self.y_fine_coord

        if dx != 0:
            direction = 1 if dx > 0 else -1
            self.x_fine_coord += direction * step_size

        if dy != 0:
            direction = 1 if dy > 0 else -1
            self.y_fine_coord += direction * step_size

        if curr_tick_int < 8:
            step_frame = "step_right"
        else:
            step_frame = "step_left"

        self.current_sprite = self.FRAME_MAP[self.direction][step_frame]

        if self.move_tick >= 16:
            self.x_fine_coord = target_px_x
            self.y_fine_coord = target_px_y

            self.is_moving = False
            self.move_tick = 0.0

            # Si teníamos un movimiento en cola, empezamos el siguiente tramo inmediatamente
            if self.pending_target:
                next_tx, next_ty = self.pending_target
                self.pending_target = None
                # Solo iniciamos si es realmente un cambio de posición
                if next_tx != self.target_x or next_ty != self.target_y:
                    self._start_move(next_tx, next_ty)
                else:
                    self.current_sprite = self.FRAME_MAP[self.direction]["idle"]
            else:
                self.current_sprite = self.FRAME_MAP[self.direction]["idle"]
