class Packet:
    """
    Representa un paquete de datos del jugador.
    """

    def __init__(self, player_id=0, x=50, y=50, map_number=0, map_bank=0, IsOverworld=0):
        self.player_id = player_id
        self.player_x_coord = x
        self.player_y_coord = y
        self.map_number = map_number
        self.map_bank = map_bank
        self.IsOverworld = IsOverworld

    # ------------------------
    # Serialización para enviar
    # ------------------------
    def to_bytes(self):
        import struct
        return struct.pack(
            "<I2i2iI",
            self.player_id,
            self.player_x_coord,
            self.player_y_coord,
            self.map_number,
            self.map_bank,
            self.IsOverworld
        )

    # ------------------------
    # Deserialización de bytes recibidos
    # ------------------------
    @classmethod
    def from_bytes(cls, data):
        import struct
        player_id, x, y, map_number, map_bank, IsOverworld = struct.unpack("<I2i2iI", data)
        return cls(player_id, x, y, map_number, map_bank, IsOverworld)

    # ------------------------
    # Representación en string (humana)
    # ------------------------
    def __str__(self):
        return (
            f"Packet(id={self.player_id}, "
            f"x={self.player_x_coord}, "
            f"y={self.player_y_coord}, "
            f"map={self.map_number}, "
            f"bank={self.map_bank}, "
            f"IsOverworld={self.IsOverworld})"
        )

    # ------------------------
    # Representación en listas / consola
    # ------------------------
    def __repr__(self):
        return str(self)
