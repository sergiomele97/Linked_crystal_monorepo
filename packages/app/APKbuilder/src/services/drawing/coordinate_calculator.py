class CoordinateCalculator:

    def __init__(self, ramData):
        self.ramData = ramData

    def shouldFilter(self, packet):
        if (not packet.IsOverworld
            or packet.map_bank != self.ramData.map_bank
            or packet.map_number != self.ramData.map_number 
            ):
            return True
        return False

    def calculate_player_coords(self, x_packet_coord, y_packet_coord):
        return x_packet_coord, y_packet_coord
