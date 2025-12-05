class RemotePlayerEntity:
    """
    Entidad visual de un jugador remoto.
    Se encarga de interpolar posición hacia el último estado recibido,
    gestionar dirección/animación y reportar coordenadas de renderizado.
    """

    # --- CONFIGURACIÓN GLOBAL ---
    TILE_SIZE = 16

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

    # ---------------------------------------------------------
    #         Actualiza target y dirección 
    # ---------------------------------------------------------
    def update_from_network(self, packet):
        """
        network_state: instancia con tile_x y tile_y del jugador remoto.
        Solo se actualiza el objetivo, NUNCA la posicion de render.
        """
        if (packet.player_x_coord != self.target_x or 
            packet.player_y_coord != self.target_y):

            self.target_x = packet.player_x_coord
            self.target_y = packet.player_y_coord

            self.is_moving = True

            # Actualizamos dirección básica (opcional)
            dx = self.target_x - self.x_fine_coord / self.TILE_SIZE
            dy = self.target_y - self.y_fine_coord / self.TILE_SIZE
            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"

    # ---------------------------------------------------------------
    #        Actualiza posición fina relativa a mundo (render_x/y)
    # ---------------------------------------------------------------
    def updateFineCoords(self):
        """
        Actualiza la posición fina relativa a mundo
        """

        if not self.is_moving:
            return 

        return  # Por ahora no implementar
