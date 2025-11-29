class Packet:
    """
    Representa un paquete de datos del jugador.
    """

    def __init__(self, x=50, y=50, map_number=0, map_bank=0, is_playing=0):
        self.player_x_coord = x
        self.player_y_coord = y
        self.map_number = map_number
        self.map_bank = map_bank
        self.isPlaying = is_playing

    # ------------------------
    # Serialización para enviar
    # ------------------------
    def to_bytes(self):
        import struct
        # "<3i" es un ejemplo, ajusta según los campos que quieras enviar
        return struct.pack(
            "<2i2iI",  # 2 coords, 2 map info, isPlaying
            self.player_x_coord,
            self.player_y_coord,
            self.map_number,
            self.map_bank,
            self.isPlaying
        )

    # ------------------------
    # Deserialización de bytes recibidos
    # ------------------------
    @classmethod
    def from_bytes(cls, data):
        import struct
        x, y, map_number, map_bank, is_playing = struct.unpack("<2i2iI", data)
        return cls(x, y, map_number, map_bank, is_playing)
